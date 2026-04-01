"""
IceRuns Playbook Nodes for executing serverless functions within workflows.

This module provides node types for integrating IceRuns function execution
into IceStreams playbooks. Includes nodes for executing functions synchronously
and asynchronously, with support for input mapping and timeout configuration.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from .base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


class IceRunExecuteNode(BaseNode):
    """
    Execute an IceRun function within a playbook.

    This node allows playbooks to execute serverless functions defined in IceRuns,
    passing data from previous nodes or static input. Supports both synchronous
    (wait for completion) and asynchronous (return immediately with activation ID)
    execution modes.

    Configuration:
        function_id (str): UUID of the IceRuns function to execute (required)
        input_mode (str): "static" for fixed input JSON or "from_previous" to use node input
        input_json (dict): Static input when input_mode="static"
        timeout_override (int): Override function's default timeout (1-900 seconds)
        async_mode (bool): If True, return immediately with activation ID; if False, wait for completion

    Input Ports:
        in (object): Data to pass as function input (optional, used when input_mode="from_previous")

    Output Ports:
        out (object): Execution result containing status, activation_id, output, and duration
    """

    node_type = "iceruns.execute"
    name = "Execute IceRun"
    description = "Execute a serverless function from IceRuns"
    category = "iceruns"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Define input ports for IceRun execution node.

        Returns:
            List containing one optional input port for passing data to the function.
        """
        return [
            NodeInput(
                name="in",
                description="Input data to pass to the IceRun function",
                required=False,
                data_type="object",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for IceRun execution node.

        Returns:
            List containing one output port with execution result.
        """
        return [
            NodeOutput(
                name="out",
                description="Execution result with status, output, and metadata",
                data_type="object",
            ),
        ]

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate IceRun execution node configuration.

        Args:
            config: Node configuration to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate required function_id
        if not config.get("function_id"):
            errors.append("function_id is required")

        # Validate input_mode
        input_mode = config.get("input_mode", "from_previous")
        if input_mode not in {"static", "from_previous"}:
            errors.append(
                f"Invalid input_mode '{input_mode}'. Must be 'static' or 'from_previous'"
            )

        # Validate static input if required
        if input_mode == "static":
            input_json = config.get("input_json")
            if input_json is None:
                errors.append("input_json is required when input_mode='static'")
            elif not isinstance(input_json, dict):
                errors.append("input_json must be a dictionary object")

        # Validate timeout_override if provided
        if "timeout_override" in config:
            timeout = config["timeout_override"]
            if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 900:
                errors.append("timeout_override must be between 1 and 900 seconds")

        # Validate async_mode
        if "async_mode" in config:
            async_mode = config["async_mode"]
            if not isinstance(async_mode, bool):
                errors.append("async_mode must be a boolean")

        return errors

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute an IceRun function from within a playbook.

        Handles both synchronous and asynchronous execution modes. In async mode,
        returns immediately with an activation ID for polling later. In sync mode,
        waits for the function to complete (up to timeout) and returns the result.

        Args:
            context: Execution context containing config, logger, and variables.
            inputs: Dictionary with input data (if using input_mode="from_previous").

        Returns:
            NodeResult with execution status, output, and metadata.
        """
        start_time = time.perf_counter()

        try:
            # Import here to avoid circular dependencies
            from ..models import get_db
            from ..services.redis_streams import RedisStreams
            import secrets
            import datetime

            config = context.config
            function_id = config.get("function_id")
            input_mode = config.get("input_mode", "from_previous")
            async_mode = config.get("async_mode", False)
            timeout_override = config.get("timeout_override")

            # Determine input data
            if input_mode == "static":
                function_input = config.get("input_json", {})
            else:
                # Use input from previous node
                function_input = inputs.get("in", {})

            if not isinstance(function_input, dict):
                function_input = {"data": function_input}

            context.log_info(
                f"Executing IceRun function '{function_id}' with input_mode='{input_mode}', "
                f"async_mode={async_mode}"
            )

            # Get database connection
            db = get_db()

            # Look up function
            func = db(db.iceruns.function_id == function_id).select().first()
            if not func:
                error_msg = f"IceRun function '{function_id}' not found"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

            if func.status != "active":
                error_msg = f"IceRun function is not active (status: {func.status})"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

            if not func.package_key:
                error_msg = "IceRun function has no package"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

            # Create execution record
            execution_id = secrets.token_urlsafe(16)
            exec_id = db.iceruns_executions.insert(
                execution_id=execution_id,
                function_id=func.id,
                status="queued",
                trigger_type="playbook",
                triggered_by=f"playbook:{context.playbook_id}",
                input_json=function_input,
                created_at=datetime.datetime.utcnow(),
            )

            db.commit()

            # Publish to Redis Streams for invoker
            redis = RedisStreams()
            config_data = {
                "runtime": func.runtime,
                "entrypoint": func.entrypoint,
                "handler": func.handler,
                "memory_limit_mb": func.memory_limit_mb,
                "timeout_seconds": timeout_override or func.timeout_seconds,
                "cpu_limit": func.cpu_limit,
                "env_vars": func.env_vars or {},
                "secrets": func.secrets or {},
                "package_key": func.package_key,
            }

            redis.publish_icerun_task(
                execution_id, function_id, function_input, config_data
            )
            context.log_info(
                f"IceRun task published to Redis Streams with execution_id={execution_id}"
            )

            # Update execution count
            db(db.iceruns.id == func.id).update(
                execution_count=(func.execution_count or 0) + 1,
                last_executed_at=datetime.datetime.utcnow(),
            )
            db.commit()

            # Return based on async mode
            if async_mode:
                # Async mode: return immediately with activation ID
                result_output = {
                    "activation_id": execution_id,
                    "status": "queued",
                    "function_id": function_id,
                    "execution_id": execution_id,
                }
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.success_result(
                    outputs={"out": result_output}, execution_time_ms=execution_time
                )
            else:
                # Sync mode: wait for completion (max 60 seconds)
                max_wait_seconds = timeout_override or func.timeout_seconds
                max_wait_seconds = min(
                    max_wait_seconds + 10, 300
                )  # Add buffer, max 5 minutes

                context.log_info(
                    f"Waiting for IceRun completion (max {max_wait_seconds}s)"
                )

                for attempt in range(max_wait_seconds * 2):  # Poll every 0.5s
                    await asyncio.sleep(0.5)

                    execution = db.iceruns_executions[exec_id]
                    if execution.status in [
                        "completed",
                        "failed",
                        "timeout",
                        "cancelled",
                    ]:
                        context.log_info(
                            f"IceRun completed with status={execution.status}"
                        )

                        result_output = {
                            "status": execution.status,
                            "execution_id": execution_id,
                            "output": execution.output_json,
                            "stdout": execution.stdout,
                            "stderr": execution.stderr,
                            "exit_code": execution.exit_code,
                            "duration_ms": execution.duration_ms,
                            "error": execution.error_message,
                        }

                        execution_time = (time.perf_counter() - start_time) * 1000
                        return NodeResult.success_result(
                            outputs={"out": result_output},
                            execution_time_ms=execution_time,
                        )

                # Timeout waiting for execution
                error_msg = f"IceRun execution timed out after {max_wait_seconds}s"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

        except Exception as e:
            error_msg = f"IceRun execute node failed: {str(e)}"
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )


class IceRunWaitNode(BaseNode):
    """
    Wait for an async IceRun execution to complete.

    This node polls an async execution (created with IceRunExecuteNode in async mode)
    until it completes or times out. Useful for workflows that need to wait for async
    function results at a later stage.

    Configuration:
        timeout_seconds (int): Maximum time to wait for completion (1-900 seconds, default: 300)
        poll_interval_ms (int): How often to poll status (default: 500ms)

    Input Ports:
        activation_id (string): Activation ID from a previous async IceRunExecuteNode execution

    Output Ports:
        out (object): Final execution result with status, output, logs, and metrics
    """

    node_type = "iceruns.wait_for_completion"
    name = "Wait for IceRun"
    description = "Wait for an async IceRun execution to complete"
    category = "iceruns"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Define input ports for IceRun wait node.

        Returns:
            List containing one required input port for activation ID.
        """
        return [
            NodeInput(
                name="activation_id",
                description="Activation ID from async IceRun execution",
                required=True,
                data_type="string",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for IceRun wait node.

        Returns:
            List containing one output port with final execution result.
        """
        return [
            NodeOutput(
                name="out",
                description="Final execution result with status, output, and metrics",
                data_type="object",
            ),
        ]

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate IceRun wait node configuration.

        Args:
            config: Node configuration to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate timeout_seconds if provided
        if "timeout_seconds" in config:
            timeout = config["timeout_seconds"]
            if not isinstance(timeout, (int, float)) or timeout < 1 or timeout > 900:
                errors.append("timeout_seconds must be between 1 and 900 seconds")

        # Validate poll_interval_ms if provided
        if "poll_interval_ms" in config:
            interval = config["poll_interval_ms"]
            if (
                not isinstance(interval, (int, float))
                or interval < 100
                or interval > 10000
            ):
                errors.append(
                    "poll_interval_ms must be between 100 and 10000 milliseconds"
                )

        return errors

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Wait for an async IceRun execution to complete.

        Polls the execution status at regular intervals until completion or timeout.
        Returns the final result with all execution details.

        Args:
            context: Execution context containing config and logger.
            inputs: Dictionary with activation_id from previous async execution.

        Returns:
            NodeResult with final execution status and output.
        """
        start_time = time.perf_counter()

        try:
            # Import here to avoid circular dependencies
            from ..models import get_db

            config = context.config
            activation_id = inputs.get("activation_id") or config.get("activation_id")
            timeout_seconds = config.get("timeout_seconds", 300)
            poll_interval_ms = config.get("poll_interval_ms", 500)

            if not activation_id:
                error_msg = "activation_id is required for wait node"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

            if not isinstance(activation_id, str):
                error_msg = f"activation_id must be a string, got {type(activation_id).__name__}"
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

            context.log_info(
                f"Waiting for IceRun completion (activation_id={activation_id}, "
                f"timeout={timeout_seconds}s, poll_interval={poll_interval_ms}ms)"
            )

            db = get_db()
            poll_interval_sec = poll_interval_ms / 1000.0
            max_polls = int(timeout_seconds / poll_interval_sec) + 1

            # Poll for completion
            for attempt in range(max_polls):
                execution = (
                    db(db.iceruns_executions.execution_id == activation_id)
                    .select()
                    .first()
                )

                if not execution:
                    error_msg = (
                        f"Execution with activation_id '{activation_id}' not found"
                    )
                    context.log_error(error_msg)
                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.failure_result(
                        error=error_msg, execution_time_ms=execution_time
                    )

                # Check if execution is complete
                if execution.status in ["completed", "failed", "timeout", "cancelled"]:
                    context.log_info(f"IceRun completed with status={execution.status}")

                    result_output = {
                        "status": execution.status,
                        "execution_id": activation_id,
                        "output": execution.output_json,
                        "stdout": execution.stdout,
                        "stderr": execution.stderr,
                        "exit_code": execution.exit_code,
                        "duration_ms": execution.duration_ms,
                        "memory_used_mb": execution.memory_used_mb,
                        "cpu_time_ms": execution.cpu_time_ms,
                        "error": execution.error_message,
                    }

                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.success_result(
                        outputs={"out": result_output}, execution_time_ms=execution_time
                    )

                # Not complete yet, wait before polling again
                if attempt < max_polls - 1:
                    context.log_debug(
                        f"IceRun still running (status={execution.status}), polling in {poll_interval_ms}ms"
                    )
                    await asyncio.sleep(poll_interval_sec)

            # Timeout waiting for execution
            error_msg = f"IceRun execution timed out after {timeout_seconds} seconds (activation_id={activation_id})"
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )

        except Exception as e:
            error_msg = f"IceRun wait node failed: {str(e)}"
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )
