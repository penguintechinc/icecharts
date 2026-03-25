"""
Logic Gate Nodes for IceStreams Workflow System.

This module provides boolean logic gate nodes (AND, OR, NOT) that enable
conditional branching and logical operations in workflow execution.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node


@register_node("conditional_and", "conditionals", "AND Gate")
class AndConditional(BaseNode):
    """AND logic gate: outputs true only if ALL inputs are truthy."""

    node_type = "conditional_and"
    name = "AND Gate"
    description = "Outputs true only if ALL inputs are truthy"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the AND gate."""
        return [
            NodeInput(
                name="in1",
                description="First input condition",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="in2",
                description="Second input condition",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="in3",
                description="Third input condition",
                required=False,
                data_type="any",
            ),
            NodeInput(
                name="in4",
                description="Fourth input condition",
                required=False,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the AND gate."""
        return [
            NodeOutput(
                name="true",
                description="Output when all inputs are truthy",
                data_type="bool",
            ),
            NodeOutput(
                name="false",
                description="Output when any input is falsy",
                data_type="bool",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the AND gate logic.

        Evaluates all provided inputs and returns true only if ALL are truthy.
        Non-provided optional inputs are treated as True (neutral for AND).

        Args:
            context: Execution context
            inputs: Dictionary containing in1, in2, in3, in4 values

        Returns:
            NodeResult with 'true' or 'false' output based on AND logic
        """
        start_time = time.perf_counter()

        # Validate required inputs
        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Gather provided inputs
        values = []
        for key in ["in1", "in2", "in3", "in4"]:
            if key in inputs:
                values.append(bool(inputs[key]))

        # AND logic: all must be True
        result = all(values) if values else True

        context.log_info(f"AND Gate: {values} -> {result}")

        return NodeResult.success_result(
            outputs={"true": result, "false": not result},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_or", "conditionals", "OR Gate")
class OrConditional(BaseNode):
    """OR logic gate: outputs true if ANY input is truthy."""

    node_type = "conditional_or"
    name = "OR Gate"
    description = "Outputs true if ANY input is truthy"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the OR gate."""
        return [
            NodeInput(
                name="in1",
                description="First input condition",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="in2",
                description="Second input condition",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="in3",
                description="Third input condition",
                required=False,
                data_type="any",
            ),
            NodeInput(
                name="in4",
                description="Fourth input condition",
                required=False,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the OR gate."""
        return [
            NodeOutput(
                name="true",
                description="Output when any input is truthy",
                data_type="bool",
            ),
            NodeOutput(
                name="false",
                description="Output when all inputs are falsy",
                data_type="bool",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the OR gate logic.

        Evaluates all provided inputs and returns true if ANY is truthy.
        Non-provided optional inputs are treated as False (neutral for OR).

        Args:
            context: Execution context
            inputs: Dictionary containing in1, in2, in3, in4 values

        Returns:
            NodeResult with 'true' or 'false' output based on OR logic
        """
        start_time = time.perf_counter()

        # Validate required inputs
        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Gather provided inputs
        values = []
        for key in ["in1", "in2", "in3", "in4"]:
            if key in inputs:
                values.append(bool(inputs[key]))

        # OR logic: any must be True
        result = any(values) if values else False

        context.log_info(f"OR Gate: {values} -> {result}")

        return NodeResult.success_result(
            outputs={"true": result, "false": not result},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )


@register_node("conditional_not", "conditionals", "NOT Gate")
class NotConditional(BaseNode):
    """NOT logic gate: inverts the boolean value of input."""

    node_type = "conditional_not"
    name = "NOT Gate"
    description = "Inverts the boolean value of input"
    category = "conditionals"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the NOT gate."""
        return [
            NodeInput(
                name="in",
                description="Input condition to invert",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the NOT gate."""
        return [
            NodeOutput(
                name="true",
                description="Output when input is falsy",
                data_type="bool",
            ),
            NodeOutput(
                name="false",
                description="Output when input is truthy",
                data_type="bool",
            ),
        ]

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the NOT gate logic.

        Inverts the boolean value of the input: truthy values become False,
        falsy values become True.

        Args:
            context: Execution context
            inputs: Dictionary containing 'in' value

        Returns:
            NodeResult with 'true' or 'false' output based on NOT logic
        """
        start_time = time.perf_counter()

        # Validate required inputs
        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        input_value = inputs.get("in")
        result = not bool(input_value)

        context.log_info(f"NOT Gate: {bool(input_value)} -> {result}")

        return NodeResult.success_result(
            outputs={"true": result, "false": not result},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
