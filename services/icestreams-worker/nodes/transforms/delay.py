"""
Delay Transform Node for IceStreams Workflow System.

This module provides a configurable delay/pause node that adds a specified
duration to workflow execution using non-blocking async sleep. Useful for
rate limiting, staged rollouts, and time-based workflow control.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("transform_delay", "transforms", "Delay")
class DelayTransform(BaseNode):
    """Add a delay/pause to the workflow execution."""

    node_type = "transform_delay"
    name = "Delay"
    description = "Pause workflow execution for a specified duration"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the delay node."""
        return [
            NodeInput(
                name="in",
                description="Input data (passed through after delay)",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the delay node."""
        return [
            NodeOutput(
                name="out", description="Input data passed through", data_type="any"
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate delay node configuration.

        Checks that:
        - Either delayMs or delaySeconds is provided
        - Values are non-negative
        - Values do not exceed 5 minutes (safety limit)

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        delay_ms = config.get("delayMs")
        delay_seconds = config.get("delaySeconds")

        if delay_ms is None and delay_seconds is None:
            errors.append("Either delayMs or delaySeconds is required")

        if delay_ms is not None:
            try:
                ms = int(delay_ms)
                if ms < 0:
                    errors.append("delayMs must be non-negative")
                if ms > 300000:  # 5 minutes max
                    errors.append("delayMs cannot exceed 300000 (5 minutes)")
            except (ValueError, TypeError):
                errors.append("delayMs must be a valid integer")

        if delay_seconds is not None:
            try:
                secs = float(delay_seconds)
                if secs < 0:
                    errors.append("delaySeconds must be non-negative")
                if secs > 300:  # 5 minutes max
                    errors.append("delaySeconds cannot exceed 300 (5 minutes)")
            except (ValueError, TypeError):
                errors.append("delaySeconds must be a valid number")

        return errors

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the delay transform.

        Retrieves the configured delay duration, performs non-blocking async sleep,
        and passes through the input data with timing metadata appended.

        Args:
            context: Execution context with configuration and logging
            inputs: Dictionary containing the input data

        Returns:
            NodeResult with success status, output data, and execution timing
        """
        start_time = time.perf_counter()

        input_data = inputs.get("in")

        # Get delay duration from config
        delay_ms = context.config.get("delayMs")
        delay_seconds = context.config.get("delaySeconds")

        # Convert to seconds
        if delay_ms is not None:
            delay = float(delay_ms) / 1000.0
        elif delay_seconds is not None:
            delay = float(delay_seconds)
        else:
            delay = 0.0

        # Cap at 5 minutes for safety
        delay = min(delay, 300.0)

        if delay > 0:
            context.log_info(f"Delaying for {delay:.2f} seconds")
            started_at = datetime.now(timezone.utc).isoformat()

            await asyncio.sleep(delay)

            finished_at = datetime.now(timezone.utc).isoformat()
            context.log_info(f"Delay completed")
        else:
            started_at = finished_at = datetime.now(timezone.utc).isoformat()

        # Pass through input data with timing metadata
        if isinstance(input_data, dict):
            result = {
                **input_data,
                "_delay": {
                    "duration_seconds": delay,
                    "started_at": started_at,
                    "finished_at": finished_at,
                },
            }
        else:
            result = input_data

        return NodeResult.success_result(
            outputs={"out": result},
            execution_time_ms=(time.perf_counter() - start_time) * 1000,
        )
