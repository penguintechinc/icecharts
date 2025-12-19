"""
Schedule Trigger Node - Executes workflow on a cron schedule.

This trigger node fires workflow execution based on a cron expression and timezone.
It validates cron expressions using croniter and outputs scheduling metadata when
triggered, including next scheduled run time and timezone information.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import pytz

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult

try:
    from croniter import croniter

    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False


class ScheduleTrigger(BaseTrigger):
    """
    Schedule trigger node for cron-based workflow execution.

    This node fires a workflow based on a user-configured cron expression and
    timezone. It outputs scheduling metadata including execution timestamps,
    the configured cron expression, timezone, and the next scheduled run time.

    Configuration:
        cron_expression (str): Cron expression defining the schedule
                              (e.g., "0 9 * * MON-FRI" for 9 AM on weekdays).
        timezone (str): IANA timezone string (default: "UTC").
                       See pytz.all_timezones for valid values.

    Example Configuration:
        {
            "cron_expression": "0 9 * * MON-FRI",
            "timezone": "America/New_York"
        }
    """

    node_type = "trigger_schedule"
    name = "Schedule"
    description = "Trigger workflow on a cron schedule"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Schedule triggers have no inputs.

        Returns:
            Empty list - triggers are entry points with no upstream inputs.
        """
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for schedule metadata.

        Returns:
            List containing one output port for schedule metadata.
        """
        return [
            NodeOutput(
                name="out",
                description="Schedule execution metadata including timestamps and next run",
                data_type="object",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate schedule trigger configuration.

        Validates:
        - cron_expression is provided and syntactically valid
        - timezone is a recognized IANA timezone
        - croniter library is available (if validation needed)

        Args:
            config: Configuration dictionary containing cron_expression and timezone.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        # Validate cron_expression
        cron_expr = config.get("cron_expression")
        if not cron_expr:
            errors.append("cron_expression is required")
        elif isinstance(cron_expr, str):
            if CRONITER_AVAILABLE:
                try:
                    croniter(cron_expr)
                except (ValueError, KeyError) as e:
                    errors.append(f"Invalid cron expression: {str(e)}")
            else:
                errors.append("croniter library not available for validation")
        else:
            errors.append("cron_expression must be a string")

        # Validate timezone
        tz = config.get("timezone", "UTC")
        if not isinstance(tz, str):
            errors.append("timezone must be a string")
        else:
            try:
                pytz.timezone(tz)
            except pytz.UnknownTimeZoneError:
                errors.append(f"Unknown timezone: {tz}")

        return errors

    @classmethod
    def get_next_run(cls, cron_expression: str, tz_name: str = "UTC") -> datetime:
        """
        Calculate the next scheduled run time.

        Uses croniter to compute the next occurrence of the cron expression
        in the specified timezone.

        Args:
            cron_expression: Valid cron expression string.
            tz_name: IANA timezone name (default: "UTC").

        Returns:
            datetime object of the next scheduled run in the specified timezone.

        Raises:
            RuntimeError: If croniter library is not available.
            ValueError: If cron_expression is invalid.
            pytz.UnknownTimeZoneError: If timezone is invalid.
        """
        if not CRONITER_AVAILABLE:
            raise RuntimeError("croniter library not installed")

        tz = pytz.timezone(tz_name)
        now = datetime.now(tz)
        cron = croniter(cron_expression, now)
        return cron.get_next(datetime)

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """
        Fire the schedule trigger and produce schedule metadata.

        Generates schedule metadata containing current execution timestamp,
        configured cron expression, timezone, UTC timestamp, and next scheduled
        run time. This metadata is passed downstream to dependent nodes.

        Args:
            context: Execution context containing configuration and logger.
            trigger_data: Trigger-specific data (unused for schedule triggers).

        Returns:
            NodeResult with success status and schedule metadata in "out" port,
            or failure status with error message on validation failure.
        """
        # Extract configuration
        cron_expr = context.config.get("cron_expression", "* * * * *")
        tz_name = context.config.get("timezone", "UTC")

        # Validate timezone
        try:
            tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            error_msg = f"Unknown timezone: {tz_name}"
            context.log_error(error_msg)
            return NodeResult.failure_result(error=error_msg)

        # Get current time in configured timezone
        now = datetime.now(tz)

        # Build schedule metadata
        schedule_data: Dict[str, Any] = {
            "triggered_at": now.isoformat(),
            "cron_expression": cron_expr,
            "timezone": tz_name,
            "utc_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add next run time if croniter is available
        if CRONITER_AVAILABLE:
            try:
                next_run = self.get_next_run(cron_expr, tz_name)
                schedule_data["next_run"] = next_run.isoformat()
                context.log_debug(f"Schedule trigger next run: {next_run.isoformat()}")
            except (ValueError, KeyError) as e:
                # Log warning but don't fail - next_run is informational
                context.log_warning(f"Could not calculate next run time: {str(e)}")
        else:
            context.log_debug("croniter not available - next_run field omitted")

        context.log_info(f"Schedule trigger fired: {cron_expr} in {tz_name}")

        return NodeResult.success_result(outputs={"out": schedule_data})
