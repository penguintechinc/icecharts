"""
JSON Transform Node for IceStreams Workflow System.

This module provides a configurable JSON transformation node that processes
data using various operations including path extraction, value setting, deletion,
field renaming, merging, flattening, and unflattening.

Supports JMESPath queries with fallback to simple dot notation for maximum
compatibility.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("transform_json", "transforms", "JSON Transform")
class JsonTransform(BaseNode):
    """Transform JSON data using path queries and manipulation operations."""

    node_type = "transform_json"
    name = "JSON Transform"
    description = "Transform JSON data using path queries and operations"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the JSON transform node."""
        return [
            NodeInput(
                name="in",
                description="Input data to transform",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the JSON transform node."""
        return [
            NodeOutput(
                name="out",
                description="Transformed output",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate JSON transform configuration.

        Checks that:
        - Operation is one of the supported types
        - Required parameters are provided for each operation

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        operation = config.get("operation", "extract")
        valid_ops = {"extract", "set", "delete", "rename", "merge", "flatten", "unflatten"}
        if operation not in valid_ops:
            errors.append(
                f"Invalid operation: {operation}. Valid: {sorted(valid_ops)}"
            )

        if operation == "extract":
            path = config.get("jsonPath", "")
            if not path:
                errors.append("jsonPath is required for extract operation")

        if operation == "set":
            if not config.get("jsonPath"):
                errors.append("jsonPath is required for set operation")
            if "value" not in config:
                errors.append("value is required for set operation")

        if operation == "rename":
            if not config.get("fromPath"):
                errors.append("fromPath is required for rename operation")
            if not config.get("toPath"):
                errors.append("toPath is required for rename operation")

        return errors

    def _extract_path(self, data: Any, path: str) -> Any:
        """
        Extract value from data using JMESPath with fallback to dot notation.

        JMESPath provides powerful query capabilities. If JMESPath is not available,
        falls back to simple dot notation for basic path access.

        Args:
            data: Data to extract from (typically dict or list)
            path: JMESPath or dot-notation path (e.g., "user.profile.name" or "items[0].id")

        Returns:
            Extracted value or None if path not found
        """
        try:
            import jmespath
            return jmespath.search(path, data)
        except ImportError:
            # Fallback to simple dot notation
            return self._extract_dot_path(data, path)

    def _extract_dot_path(self, data: Any, path: str) -> Any:
        """
        Extract value using simple dot notation (no JMESPath).

        Supports basic paths like "user.name" and array indexing like "items.0.value".

        Args:
            data: Data to traverse
            path: Dot-notation path

        Returns:
            Value at path or None if not found
        """
        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                if idx < len(current):
                    current = current[idx]
                else:
                    return None
            else:
                return None

        return current

    def _set_path(self, data: Any, path: str, value: Any) -> Any:
        """
        Set value at specified path, creating nested structure as needed.

        Uses dot notation to navigate/create path structure. Creates intermediate
        dictionaries if they don't exist.

        Args:
            data: Data to modify (should be dict or will be converted)
            path: Dot-notation path (e.g., "user.profile.name")
            value: Value to set

        Returns:
            Modified data dictionary
        """
        if not isinstance(data, dict):
            data = {}

        parts = path.split(".")
        current = data

        # Navigate/create path to parent of target
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        # Set the final value
        current[parts[-1]] = value
        return data

    def _delete_path(self, data: Dict, path: str) -> Dict:
        """
        Delete value at specified path.

        Safely removes a key from nested structure. Returns data unchanged
        if path doesn't exist.

        Args:
            data: Dictionary to modify
            path: Dot-notation path to delete

        Returns:
            Modified data dictionary
        """
        parts = path.split(".")
        current = data

        # Navigate to parent of target
        for part in parts[:-1]:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # Path doesn't exist, return unchanged
                return data

        # Delete the final key
        if isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]

        return data

    def _rename_path(
        self, data: Dict, from_path: str, to_path: str
    ) -> Dict:
        """
        Rename a field by extracting from one path and setting at another.

        Args:
            data: Dictionary to modify
            from_path: Source path
            to_path: Destination path

        Returns:
            Modified data dictionary
        """
        value = self._extract_dot_path(data, from_path)
        data = self._delete_path(data, from_path)
        data = self._set_path(data, to_path, value)
        return data

    def _flatten(
        self, data: Dict, prefix: str = "", sep: str = "."
    ) -> Dict:
        """
        Flatten nested dictionary to single level with concatenated keys.

        Recursively flattens nested dicts and lists into single-level dict
        with keys like "user.profile.name" and "items.0.value".

        Args:
            data: Dictionary to flatten
            prefix: Current key prefix (used during recursion)
            sep: Separator for concatenating keys (default ".")

        Returns:
            Flattened dictionary
        """
        result = {}
        for key, value in data.items():
            new_key = f"{prefix}{sep}{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dicts
                result.update(self._flatten(value, new_key, sep))
            elif isinstance(value, list):
                # Handle lists by indexing
                for idx, item in enumerate(value):
                    list_key = f"{new_key}{sep}{idx}"
                    if isinstance(item, dict):
                        result.update(self._flatten(item, list_key, sep))
                    else:
                        result[list_key] = item
            else:
                result[new_key] = value

        return result

    def _unflatten(self, data: Dict, sep: str = ".") -> Dict:
        """
        Unflatten single-level dictionary back to nested structure.

        Converts keys with separators like "user.profile.name" back into
        nested dict structure.

        Args:
            data: Flattened dictionary
            sep: Separator used in keys (default ".")

        Returns:
            Nested dictionary structure
        """
        result = {}

        for key, value in data.items():
            parts = key.split(sep)
            current = result

            # Navigate/create nested structure
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[parts[-1]] = value

        return result

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the JSON transform operation.

        Processes input data through the configured operation and returns
        the transformed result.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with 'out' containing transformed data, or error
        """
        start_time = time.perf_counter()

        # Validate inputs
        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        input_data = inputs.get("in", {})
        operation = context.config.get("operation", "extract")

        try:
            result = self._perform_operation(operation, input_data, context.config)
            context.log_info(f"JSON transform '{operation}' completed")

            return NodeResult.success_result(
                outputs={"out": result},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"JSON transform failed: {e}")
            return NodeResult.failure_result(
                error=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _perform_operation(
        self, operation: str, input_data: Any, config: Dict[str, Any]
    ) -> Any:
        """
        Perform the specified JSON transformation operation.

        Args:
            operation: Operation type (extract, set, delete, rename, merge, flatten, unflatten)
            input_data: Data to transform
            config: Operation-specific configuration

        Returns:
            Transformed data

        Raises:
            ValueError: If operation is invalid or required parameters are missing
        """
        if operation == "extract":
            path = config.get("jsonPath", "$")
            return self._extract_path(input_data, path)

        elif operation == "set":
            path = config.get("jsonPath")
            value = config.get("value")

            # If value is a string starting with "$.", treat it as a path to extract
            if isinstance(value, str) and value.startswith("$."):
                value = self._extract_path(input_data, value[2:])

            # Ensure we have a dict to modify
            data = dict(input_data) if isinstance(input_data, dict) else {}
            return self._set_path(data, path, value)

        elif operation == "delete":
            path = config.get("jsonPath")
            if not isinstance(input_data, dict):
                raise ValueError("Cannot delete path from non-object data")
            return self._delete_path(dict(input_data), path)

        elif operation == "rename":
            from_path = config.get("fromPath")
            to_path = config.get("toPath")
            if not isinstance(input_data, dict):
                raise ValueError("Cannot rename paths in non-object data")
            return self._rename_path(dict(input_data), from_path, to_path)

        elif operation == "merge":
            merge_data = config.get("mergeData", {})

            # If merge_data is a JSON string, parse it
            if isinstance(merge_data, str):
                try:
                    merge_data = json.loads(merge_data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in mergeData: {e}")

            # Merge input and merge data
            if isinstance(input_data, dict):
                result = dict(input_data)
                result.update(merge_data)
                return result
            else:
                return merge_data

        elif operation == "flatten":
            sep = config.get("separator", ".")
            if not isinstance(input_data, dict):
                return input_data
            return self._flatten(input_data, sep=sep)

        elif operation == "unflatten":
            sep = config.get("separator", ".")
            if not isinstance(input_data, dict):
                return input_data
            return self._unflatten(input_data, sep=sep)

        else:
            raise ValueError(f"Unknown operation: {operation}")
