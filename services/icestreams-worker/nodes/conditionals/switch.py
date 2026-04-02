"""
Switch Conditional Node for IceStreams Workflow System.

This module provides a switch/case branching node that routes data to different
outputs based on field value matching. Supports multiple cases with a default
fallback output. Common pattern for routing based on categorical values.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from ...executor.node_registry import register_node
from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


@register_node("conditional_switch", "conditionals", "Switch")
class SwitchConditional(BaseNode):
    """Switch/case conditional node that routes data based on field value matching."""

    node_type = "conditional_switch"
    name = "Switch"
    description = "Route data to different outputs based on field value matching"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the switch node."""
        return [
            NodeInput(
                name="in",
                description="Input data to evaluate against cases",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the switch node."""
        return [
            NodeOutput(
                name="case1",
                description="Output when value matches case 1",
                data_type="any",
            ),
            NodeOutput(
                name="case2",
                description="Output when value matches case 2",
                data_type="any",
            ),
            NodeOutput(
                name="case3",
                description="Output when value matches case 3",
                data_type="any",
            ),
            NodeOutput(
                name="case4",
                description="Output when value matches case 4",
                data_type="any",
            ),
            NodeOutput(
                name="default",
                description="Output when no cases match",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate switch conditional configuration.

        Checks that:
        - A field name is provided to check
        - Cases array is provided with value mappings
        - Each case has a value and case output mapping

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        field = config.get("field")
        if not field:
            errors.append("field is required (field to check for value matching)")

        cases = config.get("cases", [])
        if not cases:
            errors.append("cases array is required with at least one case")

        for i, case in enumerate(cases):
            if "value" not in case:
                errors.append(f"Case {i+1}: value is required")
            if "output" not in case:
                errors.append(f"Case {i+1}: output is required")
            output = case.get("output", "")
            if output not in ("case1", "case2", "case3", "case4", "default"):
                errors.append(
                    f"Case {i+1}: invalid output '{output}'. "
                    "Must be one of: case1, case2, case3, case4, default"
                )

        return errors

    def _get_field_value(self, data: Any, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "user.profile.type") and
        array indexing (e.g., "items.0.type"). Returns None for non-dict inputs.

        Args:
            data: Data to traverse (dict, list, or primitive)
            field: Field path using dot notation

        Returns:
            Field value or None if not found or inaccessible
        """
        if not isinstance(data, dict):
            return None

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

    def _find_matching_output(self, field_value: Any, cases: List[Dict]) -> str:
        """
        Find the first matching case output for a field value.

        Performs strict equality matching against case values.
        Returns "default" if no case matches.

        Args:
            field_value: Value extracted from the input data field
            cases: List of case dictionaries with 'value' and 'output' keys

        Returns:
            Output handle name (case1, case2, case3, case4, or default)
        """
        for case in cases:
            if field_value == case.get("value"):
                return case.get("output", "default")
        return "default"

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the switch conditional.

        Extracts the configured field value from input data, matches it against
        the cases array, and routes the input data to the matching output handle.
        If no cases match, routes to the default output.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with one output populated (case1/case2/case3/case4/default)
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
        field = context.config.get("field", "")
        cases = context.config.get("cases", [])

        try:
            # Extract field value from input data
            field_value = self._get_field_value(input_data, field)

            # Find matching case output
            matched_output = self._find_matching_output(field_value, cases)

            # Build outputs with only the matched case populated
            outputs = {
                "case1": None,
                "case2": None,
                "case3": None,
                "case4": None,
                "default": None,
            }
            outputs[matched_output] = input_data

            context.log_info(
                f"Field '{field}' with value {field_value!r} "
                f"routed to output '{matched_output}'"
            )

            return NodeResult.success_result(
                outputs=outputs,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"Switch evaluation failed: {e}")
            return NodeResult.failure_result(
                error=str(e),
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
