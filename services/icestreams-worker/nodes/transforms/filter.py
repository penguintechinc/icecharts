"""
Filter Transform Node for IceStreams Workflow System.

This module provides a configurable filter node that processes data based on
multiple conditions with AND/OR logic. It supports various comparison operators
including equality, relational, string matching, and pattern matching.
"""

from __future__ import annotations

import logging
import operator
import re
import time
from typing import Any, Callable, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)

# Operator mapping for filter conditions
OPERATORS: Dict[str, Callable] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
    "contains": lambda a, b: b in a if hasattr(a, "__contains__") else False,
    "not_contains": lambda a, b: b not in a if hasattr(a, "__contains__") else True,
    "starts_with": lambda a, b: str(a).startswith(str(b)),
    "ends_with": lambda a, b: str(a).endswith(str(b)),
    "regex": lambda a, b: bool(re.search(b, str(a))),
    "is_null": lambda a, b: a is None,
    "is_not_null": lambda a, b: a is not None,
    "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
    "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
}


@register_node("transform_filter", "transforms", "Filter")
class FilterTransform(BaseNode):
    """Filter data based on configurable conditions with AND/OR logic."""

    node_type = "transform_filter"
    name = "Filter"
    description = "Filter data based on configurable conditions"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the filter node."""
        return [
            NodeInput(
                name="in",
                description="Input data (object or array)",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the filter node."""
        return [
            NodeOutput(
                name="out",
                description="Filtered data (matching items)",
                data_type="any",
            ),
            NodeOutput(
                name="rejected",
                description="Rejected data (non-matching items)",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate filter node configuration.

        Checks that:
        - At least one condition is provided
        - Each condition has a field name and valid operator
        - Logic operator is either 'and' or 'or'

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        conditions = config.get("conditions", [])
        if not conditions:
            errors.append("At least one condition is required")

        for i, cond in enumerate(conditions):
            if not cond.get("field"):
                errors.append(f"Condition {i+1}: field is required")
            op = cond.get("operator", "eq")
            if op not in OPERATORS:
                valid_ops = ", ".join(sorted(OPERATORS.keys()))
                errors.append(
                    f"Condition {i+1}: invalid operator '{op}'. Valid: {valid_ops}"
                )

        logic = config.get("logic", "and")
        if logic not in ("and", "or"):
            errors.append(f"Invalid logic: {logic}. Must be 'and' or 'or'")

        return errors

    def _get_field_value(self, data: Dict, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "user.profile.name") and
        array indexing (e.g., "items.0.value").

        Args:
            data: Dictionary to traverse
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

    def _evaluate_condition(self, data: Dict, condition: Dict) -> bool:
        """
        Evaluate a single condition against data.

        Extracts the field value, applies the operator with the expected value,
        and returns the result. Exceptions during evaluation return False.

        Args:
            data: Dictionary containing the data to evaluate
            condition: Condition dict with 'field', 'operator', 'value' keys

        Returns:
            True if condition matches, False otherwise
        """
        field = condition.get("field", "")
        op_name = condition.get("operator", "eq")
        expected = condition.get("value")

        actual = self._get_field_value(data, field)
        op_func = OPERATORS.get(op_name, operator.eq)

        try:
            return op_func(actual, expected)
        except Exception:
            return False

    def _matches(
        self, data: Dict, conditions: List[Dict], logic: str
    ) -> bool:
        """
        Check if data matches all or any conditions based on logic.

        Args:
            data: Dictionary to evaluate
            conditions: List of condition dictionaries
            logic: Either "and" (all must match) or "or" (any can match)

        Returns:
            True if conditions are satisfied according to logic, False otherwise
        """
        if not conditions:
            return True

        results = [self._evaluate_condition(data, c) for c in conditions]

        if logic == "and":
            return all(results)
        else:  # or
            return any(results)

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the filter transform.

        Processes input data (single object or array) through configured conditions.
        Returns matching items in 'out' and non-matching items in 'rejected'.
        Preserves input type (single object returns single object or None).

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with 'out' and 'rejected' outputs, or error if validation fails
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
        conditions = context.config.get("conditions", [])
        logic = context.config.get("logic", "and")

        # Handle single object vs array
        is_array = isinstance(input_data, list)
        items = input_data if is_array else [input_data]

        matching = []
        rejected = []

        # Filter items
        for item in items:
            if isinstance(item, dict):
                if self._matches(item, conditions, logic):
                    matching.append(item)
                else:
                    rejected.append(item)
            else:
                # Non-dict items pass through to matching
                matching.append(item)

        # Return same type as input
        if is_array:
            result = matching
            rejected_result = rejected
        else:
            result = matching[0] if matching else None
            rejected_result = rejected[0] if rejected else None

        context.log_info(f"Filter: {len(matching)} matched, {len(rejected)} rejected")

        return NodeResult.success_result(
            outputs={"out": result, "rejected": rejected_result},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
