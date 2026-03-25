"""
Manual Trigger Node - Executes workflow when user clicks "Run" in the UI.

This trigger node is the simplest trigger type and serves as the entry point
for manual workflow execution. It passes through any data provided by the user
when triggering the workflow execution.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult


class ManualTrigger(BaseTrigger):
    """
    Manual trigger node for user-initiated workflow execution.

    This node fires a workflow when explicitly triggered by a user clicking the
    "Run" button in the UI. It is the simplest trigger type with no external
    dependencies or scheduling requirements. The trigger passes through any
    data provided in the trigger request to downstream nodes.

    Configuration:
        None required - manual triggers have no configuration.

    Example Trigger Data:
        {
            "user_id": "user-123",
            "data": {
                "project_id": "proj-456",
                "environment": "production"
            }
        }
    """

    node_type = "trigger_manual"
    name = "Manual Trigger"
    description = "Manually trigger workflow execution"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Manual triggers have no inputs.

        Returns:
            Empty list - triggers are entry points with no upstream inputs.
        """
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for trigger data.

        Returns:
            List containing one output port for trigger data.
        """
        return [
            NodeOutput(
                name="out",
                description="Trigger output with timestamp and user info",
                data_type="object",
            ),
        ]

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate manual trigger configuration.

        Manual triggers have no required configuration.

        Args:
            config: Node configuration to validate.

        Returns:
            Empty list (no validation errors).
        """
        return []

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the manual trigger.

        Extracts data from trigger_data and returns it with execution metadata
        including timestamp and user information. The trigger_data should contain
        user_id and optional data payload.

        Args:
            context: Execution context containing configuration and logger.
            trigger_data: Trigger activation data containing user info and data.

        Returns:
            NodeResult with trigger output containing timestamp, user, and data.
        """
        try:
            start_time = time.perf_counter()

            # Get optional data passed from UI
            user_id = trigger_data.get("user_id", "unknown")
            trigger_payload = trigger_data.get("data", {})

            # Build output with metadata
            output_data = {
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "triggered_by": user_id,
                "trigger_type": "manual",
                "data": trigger_payload,
            }

            context.log_info(f"Manual trigger fired by user {user_id}")

            execution_time = (time.perf_counter() - start_time) * 1000

            return NodeResult.success_result(
                outputs={"out": output_data}, execution_time_ms=execution_time
            )

        except Exception as e:
            error_msg = f"Manual trigger execution failed: {str(e)}"
            context.log_error(error_msg)
            return NodeResult.failure_result(error=error_msg)
