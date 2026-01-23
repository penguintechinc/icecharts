"""
Comparison Conditional Nodes for IceStreams Workflow System.

This module provides conditional nodes for comparing values and making workflow
decisions based on comparison results. Each node provides "true" and "false"
output ports for branching logic.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("conditional_equals", "conditionals", "Equals")
class EqualsConditional(BaseNode):
    """Conditional node that checks if two values are equal."""

    node_type = "conditional_equals"
    name = "Equals"
    description = "Check if two values are equal"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the equals node."""
        return [
            NodeInput(
                name="value",
                description="The value to compare",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="expected",
                description="The expected value to match",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the equals node."""
        return [
            NodeOutput(
                name="true",
                description="Output when values are equal",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when values are not equal",
                data_type="any",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the equals comparison.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'value' and 'expected'

        Returns:
            NodeResult with 'true' or 'false' output populated
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

        value = self._get_input_value(inputs, "value")
        expected = self._get_input_value(inputs, "expected")

        is_equal = value == expected

        context.log_info(f"Equals: {value!r} == {expected!r} -> {is_equal}")

        output_port = "true" if is_equal else "false"
        output_value = value if is_equal else None

        return NodeResult.success_result(
            outputs={output_port: output_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_greater_than", "conditionals", "Greater Than")
class GreaterThanConditional(BaseNode):
    """Conditional node that checks if value is greater than threshold."""

    node_type = "conditional_greater_than"
    name = "Greater Than"
    description = "Check if value is greater than threshold"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the greater than node."""
        return [
            NodeInput(
                name="value",
                description="The value to compare",
                required=True,
                data_type="number",
            ),
            NodeInput(
                name="threshold",
                description="The threshold to compare against",
                required=True,
                data_type="number",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the greater than node."""
        return [
            NodeOutput(
                name="true",
                description="Output when value > threshold",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when value <= threshold",
                data_type="any",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the greater than comparison.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'value' and 'threshold'

        Returns:
            NodeResult with 'true' or 'false' output populated
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

        try:
            value = float(self._get_input_value(inputs, "value"))
            threshold = float(self._get_input_value(inputs, "threshold"))
        except (TypeError, ValueError) as e:
            return NodeResult.failure_result(
                error=f"Invalid numeric values: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        is_greater = value > threshold

        context.log_info(f"Greater Than: {value} > {threshold} -> {is_greater}")

        output_port = "true" if is_greater else "false"
        output_value = value if is_greater else None

        return NodeResult.success_result(
            outputs={output_port: output_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_less_than", "conditionals", "Less Than")
class LessThanConditional(BaseNode):
    """Conditional node that checks if value is less than threshold."""

    node_type = "conditional_less_than"
    name = "Less Than"
    description = "Check if value is less than threshold"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the less than node."""
        return [
            NodeInput(
                name="value",
                description="The value to compare",
                required=True,
                data_type="number",
            ),
            NodeInput(
                name="threshold",
                description="The threshold to compare against",
                required=True,
                data_type="number",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the less than node."""
        return [
            NodeOutput(
                name="true",
                description="Output when value < threshold",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when value >= threshold",
                data_type="any",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the less than comparison.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'value' and 'threshold'

        Returns:
            NodeResult with 'true' or 'false' output populated
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

        try:
            value = float(self._get_input_value(inputs, "value"))
            threshold = float(self._get_input_value(inputs, "threshold"))
        except (TypeError, ValueError) as e:
            return NodeResult.failure_result(
                error=f"Invalid numeric values: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        is_less = value < threshold

        context.log_info(f"Less Than: {value} < {threshold} -> {is_less}")

        output_port = "true" if is_less else "false"
        output_value = value if is_less else None

        return NodeResult.success_result(
            outputs={output_port: output_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_contains", "conditionals", "Contains")
class ContainsConditional(BaseNode):
    """Conditional node that checks if string/array contains value."""

    node_type = "conditional_contains"
    name = "Contains"
    description = "Check if string or array contains a value"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the contains node."""
        return [
            NodeInput(
                name="haystack",
                description="The string or array to search in",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="needle",
                description="The value to search for",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the contains node."""
        return [
            NodeOutput(
                name="true",
                description="Output when haystack contains needle",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when haystack does not contain needle",
                data_type="any",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the contains comparison.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'haystack' and 'needle'

        Returns:
            NodeResult with 'true' or 'false' output populated
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

        haystack = self._get_input_value(inputs, "haystack")
        needle = self._get_input_value(inputs, "needle")

        try:
            # Support both string and array/list contains checks
            if isinstance(haystack, str):
                contains = needle in haystack if isinstance(needle, str) else str(needle) in haystack
            elif isinstance(haystack, (list, tuple, set)):
                contains = needle in haystack
            elif isinstance(haystack, dict):
                contains = needle in haystack.values()
            else:
                contains = False
        except Exception as e:
            return NodeResult.failure_result(
                error=f"Contains check failed: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        context.log_info(f"Contains: {needle!r} in {type(haystack).__name__} -> {contains}")

        output_port = "true" if contains else "false"
        output_value = haystack if contains else None

        return NodeResult.success_result(
            outputs={output_port: output_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_regex", "conditionals", "Regex Match")
class RegexConditional(BaseNode):
    """Conditional node that checks if string matches regex pattern."""

    node_type = "conditional_regex"
    name = "Regex Match"
    description = "Check if string matches a regex pattern"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the regex node."""
        return [
            NodeInput(
                name="text",
                description="The text to match against",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="pattern",
                description="The regex pattern to match",
                required=True,
                data_type="string",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the regex node."""
        return [
            NodeOutput(
                name="true",
                description="Output when text matches pattern",
                data_type="any",
            ),
            NodeOutput(
                name="false",
                description="Output when text does not match pattern",
                data_type="any",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the regex match comparison.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing 'text' and 'pattern'

        Returns:
            NodeResult with 'true' or 'false' output populated
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

        text = str(self._get_input_value(inputs, "text"))
        pattern = self._get_input_value(inputs, "pattern")

        try:
            matches = bool(re.search(pattern, text))
        except re.error as e:
            return NodeResult.failure_result(
                error=f"Invalid regex pattern: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as e:
            return NodeResult.failure_result(
                error=f"Regex match failed: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        context.log_info(f"Regex: '{pattern}' matches '{text}' -> {matches}")

        output_port = "true" if matches else "false"
        output_value = text if matches else None

        return NodeResult.success_result(
            outputs={output_port: output_value},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
