"""
Mock Data Trigger node for IceCharts workflows.

The MockDataTrigger generates test data from user-provided JSON configuration,
enabling workflow testing without external dependencies. Supports repetition of
data for testing loop scenarios.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


class MockDataTrigger(BaseTrigger):
    """
    Generate mock data for testing workflows.

    This trigger node provides a convenient way to test workflows by generating
    configurable test data from JSON. Users can specify the data payload and
    optionally repeat it multiple times to simulate batch processing or loops.
    """

    node_type = "trigger_mock_data"
    name = "Mock Data"
    description = "Generate mock data for testing the workflow"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Define input ports for this node.

        Returns:
            Empty list as this trigger has no inputs (it's an entry point).
        """
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for this node.

        Returns:
            List containing a single output port for the mock data.
        """
        return [NodeOutput(name="out", description="Mock data output", data_type="any")]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate the node's configuration.

        Ensures that the mockData field contains valid JSON and that
        repeatCount is a positive integer.

        Args:
            config: Node configuration dictionary containing:
                - mockData: JSON string representing the mock data (optional)
                - repeatCount: Number of times to repeat the data (default: 1)

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate mockData JSON if provided
        mock_data = config.get("mockData", "")
        if mock_data:
            try:
                json.loads(mock_data)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in mockData: {str(e)}")

        # Validate repeatCount
        repeat_count = config.get("repeatCount")
        if repeat_count is not None:
            try:
                count = int(repeat_count)
                if count < 1:
                    errors.append("repeatCount must be at least 1")
                if count > 1000:
                    errors.append("repeatCount cannot exceed 1000")
            except (ValueError, TypeError):
                errors.append("repeatCount must be a valid integer")

        return errors

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the mock data trigger and produce test data.

        Parses the JSON configuration, optionally repeats the data, and outputs
        the result through the "out" port. If repeatCount > 1, outputs an array;
        otherwise outputs the single object.

        Args:
            context: Execution context with configuration and logging.
            trigger_data: Trigger-specific data (unused for this trigger).

        Returns:
            NodeResult with success status and output data, or failure with error message.
        """
        start_time = time.perf_counter()

        try:
            # Extract configuration values
            mock_data_str = context.get_config_value("mockData", "{}")
            repeat_count = int(context.get_config_value("repeatCount", 1))

            # Parse JSON data
            if not mock_data_str or not mock_data_str.strip():
                mock_data = {}
            else:
                try:
                    mock_data = json.loads(mock_data_str)
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse JSON in mockData: {str(e)}"
                    context.log_error(error_msg)
                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.failure_result(
                        error_msg, execution_time_ms=execution_time
                    )

            # Generate output data based on repeat count
            if repeat_count > 1:
                output_data = [mock_data for _ in range(repeat_count)]
                context.log_info(
                    f"Generated mock data array with {repeat_count} repetitions"
                )
            else:
                output_data = mock_data
                context.log_info("Generated single mock data object")

            # Create result payload
            result = {
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "trigger_type": "mock_data",
                "repeat_count": repeat_count,
                "data": output_data,
            }

            execution_time = (time.perf_counter() - start_time) * 1000

            # Return successful result
            return NodeResult.success_result(
                outputs={"out": result}, execution_time_ms=execution_time
            )

        except Exception as e:
            error_msg = f"Unexpected error in MockDataTrigger: {str(e)}"
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error_msg, execution_time_ms=execution_time
            )

    async def cleanup(self) -> None:
        """
        Perform cleanup after execution.

        This trigger node has no resources to clean up.
        """
        pass
