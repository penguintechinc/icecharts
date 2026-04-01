"""
If-Then Conditional Node for IceStreams Workflow System.

This module provides a conditional branching node that evaluates conditions
and routes execution through "true" or "false" output handles based on
the evaluation result. Supports multiple conditions with AND/OR logic.
"""

from __future__ import annotations

import logging
import operator
import re
import time
from typing import Any, Callable, Dict, List

try:
    # Try relative imports first (when run as a package)
    from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
    from ...executor.node_registry import register_node
except ImportError:
    # Fallback for direct execution or alternative import paths
    from nodes.base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
    from executor.node_registry import register_node

logger = logging.getLogger(__name__)

# Operator mapping for conditional evaluation
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


@register_node("conditional_if_then", "conditionals", "If-Then")
class IfThenConditional(BaseNode):
    """Conditional branching node that routes to true or false outputs based on condition evaluation."""

    node_type = "conditional_if_then"
    name = "If-Then"
    description = "Evaluate conditions and route execution to true or false outputs"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the conditional node."""
        return [
            NodeInput(
                name="in",
                description="Input data to evaluate against conditions",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the conditional node."""
        return [
            NodeOutput(
                name="true",
                description="Output when condition evaluates to true",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when condition evaluates to false",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate if-then conditional configuration.

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

    def _get_field_value(self, data: Any, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "user.profile.name") and
        array indexing (e.g., "items.0.value"). Handles non-dict inputs
        gracefully by returning None.

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

    def _evaluate_condition(self, data: Any, condition: Dict) -> bool:
        """
        Evaluate a single condition against data.

        Extracts the field value, applies the operator with the expected value,
        and returns the result. Exceptions during evaluation return False.

        Args:
            data: Data to evaluate
            condition: Condition dict with 'field', 'operator', 'value' keys

        Returns:
            True if condition matches, False otherwise
        """
        field = condition.get("field", "")
        op_name = condition.get("operator", "eq")
        expected = condition.get("value")

        actual = self._get_field_value(data, field) if isinstance(data, dict) else None
        op_func = OPERATORS.get(op_name, operator.eq)

        try:
            return op_func(actual, expected)
        except Exception:
            return False

    def _matches(self, data: Any, conditions: List[Dict], logic: str) -> bool:
        """
        Check if data matches all or any conditions based on logic.

        Args:
            data: Data to evaluate
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

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the if-then conditional.

        Evaluates input data against configured conditions and routes execution
        to either the "true" or "false" output handle. The input data is passed
        through unchanged to whichever output matches the condition result.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with either 'true' or 'false' output populated
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

        # Evaluate conditions
        result = self._matches(input_data, conditions, logic)

        # Route to appropriate output
        if result:
            outputs = {"true": input_data, "false": None}
            context.log_info("Condition evaluated to true")
        else:
            outputs = {"true": None, "false": input_data}
            context.log_info("Condition evaluated to false")

        return NodeResult.success_result(
            outputs=outputs,
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
