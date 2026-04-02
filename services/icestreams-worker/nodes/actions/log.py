"""
Log Action Node for IceStreams Workflow System.

Provides structured logging action with multiple log levels (DEBUG, INFO, WARNING, ERROR).
Logs to stdout in structured JSON format including execution context and metadata.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from ...executor.node_registry import register_node
from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


@register_node("action_log", "actions", "Log")
class LogAction(BaseNode):
    """Log messages with structured format including context and metadata."""

    node_type = "action_log"
    name = "Log"
    description = "Log messages with configurable level and structured format"
    category = "actions"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the log node."""
        return [
            NodeInput(
                name="message",
                description="Message to log",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="data",
                description="Additional data to include in log",
                required=False,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the log node."""
        return [
            NodeOutput(
                name="logged",
                description="Whether message was logged successfully",
                data_type="bool",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate log configuration."""
        errors = []

        level = config.get("level", "INFO").upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if level not in valid_levels:
            errors.append(f"Invalid log level: {level}. Valid: {sorted(valid_levels)}")

        return errors

    def _format_log_entry(
        self,
        level: str,
        message: str,
        data: Optional[Any],
        context: NodeContext,
    ) -> str:
        """Format log entry as JSON with context."""
        entry = {
            "timestamp": time.isoformat(),
            "level": level,
            "message": message,
            "execution_id": context.execution_id,
            "playbook_id": context.playbook_id,
            "node_id": context.node_id,
        }

        if data is not None:
            entry["data"] = data

        return json.dumps(entry)

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute log action."""
        start_time = time.perf_counter()

        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        message = inputs.get("message", "")
        data = inputs.get("data")

        level = context.get_config_value("level", "INFO").upper()
        include_data = context.get_config_value("includeData", True)

        try:
            if not include_data:
                data = None

            log_entry = self._format_log_entry(level, message, data, context)

            if level == "DEBUG":
                logger.debug(log_entry)
            elif level == "INFO":
                logger.info(log_entry)
            elif level == "WARNING":
                logger.warning(log_entry)
            elif level == "ERROR":
                logger.error(log_entry)
            else:
                logger.info(log_entry)

            print(log_entry, flush=True)

            return NodeResult.success_result(
                outputs={"logged": True},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"Log action failed: {e}")
            return NodeResult.failure_result(
                error=f"Log action failed: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
