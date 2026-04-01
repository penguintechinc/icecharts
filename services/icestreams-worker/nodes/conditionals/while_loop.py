"""
While Loop Conditional Node for IceStreams Workflow System.

This module provides a loop node that continues executing while a condition
is true, with configurable max iterations safety limit to prevent infinite loops.
"""

from __future__ import annotations

import logging
import operator
import time
from typing import Any, Callable, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)

# Operator mapping for loop conditions
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
    "is_null": lambda a, b: a is None,
    "is_not_null": lambda a, b: a is not None,
    "in": lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
    "not_in": lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
}


@register_node("conditional_while", "conditionals", "While Loop")
class WhileConditional(BaseNode):
    """Loop node that continues while condition is true with max iterations safety."""

    node_type = "conditional_while"
    name = "While Loop"
    description = "Continue looping while condition is true with max iterations safety"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the while loop node."""
        return [
            NodeInput(
                name="in",
                description="Input data to evaluate in loop condition",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the while loop node."""
        return [
            NodeOutput(
                name="loop",
                description="Continue looping (condition is true)",
                data_type="any",
            ),
            NodeOutput(
                name="done",
                description="Exit loop (condition is false or max iterations reached)",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate while loop configuration.

        Checks that:
        - Condition has field name and valid operator
        - maxIterations is a positive integer if provided
        - Default maxIterations is 100 if not specified

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        condition = config.get("condition", {})
        if not condition.get("field"):
            errors.append("Condition field is required")

        op = condition.get("operator", "eq")
        if op not in OPERATORS:
            valid_ops = ", ".join(sorted(OPERATORS.keys()))
            errors.append(f"Invalid operator '{op}'. Valid: {valid_ops}")

        max_iterations = config.get("maxIterations", 100)
        if not isinstance(max_iterations, int) or max_iterations <= 0:
            errors.append("maxIterations must be a positive integer")

        return errors

    def _get_field_value(self, data: Dict, field: str) -> Any:
        """
        Get nested field value using dot notation.

        Supports nested object access (e.g., "count.value") and
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
        Evaluate the loop condition against data.

        Extracts the field value, applies the operator with the expected value,
        and returns the result. Exceptions during evaluation return False.

        Args:
            data: Dictionary containing the data to evaluate
            condition: Condition dict with 'field', 'operator', 'value' keys

        Returns:
            True if condition matches (continue loop), False otherwise
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

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the while loop conditional.

        Evaluates the condition against input data. Returns "loop" output if
        condition is true and iterations haven't been exceeded, otherwise
        returns "done" output. Tracks iteration count in context variables.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'in' with the input data

        Returns:
            NodeResult with 'loop' or 'done' output based on condition evaluation
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
        condition = context.config.get("condition", {})
        max_iterations = context.config.get("maxIterations", 100)

        # Get current iteration count from variables (0 if first iteration)
        iteration_key = f"_while_iterations_{context.node_id}"
        current_iteration = context.variables.get(iteration_key, 0)

        # Check if max iterations exceeded
        if current_iteration >= max_iterations:
            context.log_info(f"While loop: max iterations ({max_iterations}) reached")
            return NodeResult.success_result(
                outputs={"done": input_data},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Evaluate condition - support both dict and non-dict data
        condition_met = False
        if isinstance(input_data, dict):
            condition_met = self._evaluate_condition(input_data, condition)
        else:
            # For non-dict data, always continue looping (caller defines condition)
            condition_met = True

        if condition_met:
            context.log_debug(
                f"While loop: condition true, iteration {current_iteration + 1}/{max_iterations}"
            )
            return NodeResult.success_result(
                outputs={"loop": input_data},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        else:
            context.log_info(
                f"While loop: condition false, exiting after {current_iteration} iterations"
            )
            return NodeResult.success_result(
                outputs={"done": input_data},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
