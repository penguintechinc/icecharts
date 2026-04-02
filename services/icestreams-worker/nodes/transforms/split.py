"""
Split Transform Node for IceStreams Workflow System.

This module provides a configurable split node that divides arrays or strings
into separate output items. Supports multiple splitting modes including array
passthrough, string delimited splitting, chunk-based splitting, and field
extraction from nested objects.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from ...executor.node_registry import register_node
from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


@register_node("transform_split", "transforms", "Split")
class SplitTransform(BaseNode):
    """Split arrays or strings into separate outputs."""

    node_type = "transform_split"
    name = "Split"
    description = "Split arrays or strings into multiple items"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the split node."""
        return [
            NodeInput(
                name="in",
                description="Array or string to split",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the split node."""
        return [
            NodeOutput(
                name="out",
                description="Array of split items",
                data_type="array",
            ),
            NodeOutput(
                name="count",
                description="Number of items after split",
                data_type="number",
            ),
            NodeOutput(
                name="first",
                description="First item",
                data_type="any",
            ),
            NodeOutput(
                name="last",
                description="Last item",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate split node configuration.

        Checks that:
        - Mode is one of: array, string, chunks, field
        - String mode requires a delimiter
        - Chunks mode requires a positive integer chunkSize
        - Field mode requires a field path

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        mode = config.get("mode", "array")
        valid_modes = {"array", "string", "chunks", "field"}
        if mode not in valid_modes:
            errors.append(
                f"Invalid mode: {mode}. Valid modes: {', '.join(sorted(valid_modes))}"
            )

        if mode == "string":
            delimiter = config.get("delimiter")
            if delimiter is None:
                errors.append("delimiter is required for string mode")

        if mode == "chunks":
            chunk_size = config.get("chunkSize")
            if not isinstance(chunk_size, int) or chunk_size < 1:
                errors.append("chunkSize must be a positive integer for chunks mode")

        if mode == "field":
            field = config.get("field")
            if not field:
                errors.append("field is required for field mode")

        return errors

    def _get_field_value(self, data: Any, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "user.profile.name") and
        array indexing (e.g., "items.0.value").

        Args:
            data: Dictionary or object to traverse
            field: Field path using dot notation

        Returns:
            Field value or None if not found or inaccessible
        """
        parts = field.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                value = value[idx] if idx < len(value) else None
            else:
                return None
        return value

    def _chunk_list(self, lst: List, size: int) -> List[List]:
        """
        Split a list into chunks of given size.

        Args:
            lst: List to chunk
            size: Size of each chunk

        Returns:
            List of chunks (last chunk may be smaller)
        """
        return [lst[i : i + size] for i in range(0, len(lst), size)]

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the split transform.

        Processes input data according to configured mode:
        - array: Pass through as-is (or wrap single item in array)
        - string: Split by delimiter and optionally trim whitespace
        - chunks: Split arrays/strings into fixed-size chunks
        - field: Extract field from array items or nested objects

        Returns count, first, last items in addition to split output.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with 'out', 'count', 'first', 'last' outputs, or error
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

        input_data = inputs.get("in")
        mode = context.config.get("mode", "array")

        items: List[Any] = []

        try:
            if mode == "array":
                # Input is already an array, just pass through
                if isinstance(input_data, list):
                    items = input_data
                else:
                    items = [input_data]

            elif mode == "string":
                # Split string by delimiter
                delimiter = context.config.get("delimiter", ",")
                if isinstance(input_data, str):
                    items = input_data.split(delimiter)
                    # Optionally strip whitespace
                    if context.config.get("trim", True):
                        items = [item.strip() for item in items]
                else:
                    items = [str(input_data)]

            elif mode == "chunks":
                # Split into chunks of size N
                chunk_size = context.config.get("chunkSize", 10)
                if isinstance(input_data, list):
                    items = self._chunk_list(input_data, chunk_size)
                elif isinstance(input_data, str):
                    items = [
                        input_data[i : i + chunk_size]
                        for i in range(0, len(input_data), chunk_size)
                    ]
                else:
                    items = [input_data]

            elif mode == "field":
                # Extract field from each item in array
                field = context.config.get("field", "")
                if isinstance(input_data, list):
                    items = [
                        self._get_field_value(item, field)
                        for item in input_data
                        if isinstance(item, dict)
                    ]
                elif isinstance(input_data, dict):
                    value = self._get_field_value(input_data, field)
                    items = value if isinstance(value, list) else [value]
                else:
                    items = [input_data]

            # Remove None/empty values if configured
            if context.config.get("removeEmpty", False):
                items = [item for item in items if item is not None and item != ""]

            count = len(items)
            first = items[0] if items else None
            last = items[-1] if items else None

            context.log_info(f"Split into {count} items using mode '{mode}'")

            return NodeResult.success_result(
                outputs={
                    "out": items,
                    "count": count,
                    "first": first,
                    "last": last,
                },
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"Split failed: {e}")
            return NodeResult.failure_result(
                error=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
