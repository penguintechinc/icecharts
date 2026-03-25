"""
ForEach Conditional Node for IceStreams Workflow System.

This module provides a for-each node that iterates over array input,
outputting each item individually along with its index. Emits a "done"
signal upon completion.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("conditional_for_each", "conditionals", "ForEach")
class ForEachConditional(BaseNode):
    """Iterate over array input, outputting each item individually."""

    node_type = "conditional_for_each"
    name = "ForEach"
    description = "Iterate over array, output each item with index"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the for-each node."""
        return [
            NodeInput(
                name="array",
                description="Array or iterable to iterate over",
                required=True,
                data_type="array",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the for-each node."""
        return [
            NodeOutput(
                name="item",
                description="Current item in iteration",
                data_type="any",
            ),
            NodeOutput(
                name="index",
                description="Current iteration index (0-based)",
                data_type="number",
            ),
            NodeOutput(
                name="done",
                description="Fires when iteration completes",
                data_type="bool",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate for-each node configuration.

        Checks that optional field extraction path is valid if provided.

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        field = config.get("field")
        if field is not None and not isinstance(field, str):
            errors.append("field configuration must be a string path")
        return errors

    def _get_field_value(self, data: Any, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "user.profile.items") and
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

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the for-each iteration.

        Iterates over the input array and outputs each item with its index.
        If a field is configured, extracts that field from nested objects.
        Emits outputs for each iteration with item, index, and done signal.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'array' with the input data

        Returns:
            NodeResult with outputs for the first iteration (or done signal)
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

        input_array = inputs.get("array")
        field = context.config.get("field")

        try:
            # Ensure input is iterable
            if not isinstance(input_array, list):
                if isinstance(input_array, (tuple, set)):
                    items = list(input_array)
                elif isinstance(input_array, dict):
                    # Iterate over dict values
                    items = list(input_array.values())
                else:
                    # Wrap single item in array
                    items = [input_array]
            else:
                items = input_array

            # Extract field from each item if configured
            if field:
                items = [
                    self._get_field_value(item, field)
                    for item in items
                ]
                # Filter out None values from failed extractions
                items = [item for item in items if item is not None]

            count = len(items)
            context.log_info(
                f"ForEach iterating over {count} items"
                + (f" extracting field '{field}'" if field else "")
            )

            # Return result with all items for downstream processing
            # The executor will handle iteration
            return NodeResult.success_result(
                outputs={
                    "item": items[0] if items else None,
                    "index": 0,
                    "done": count == 0,
                    "_iterations": items,  # Internal: all items for executor
                },
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"ForEach failed: {e}")
            return NodeResult.failure_result(
                error=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
