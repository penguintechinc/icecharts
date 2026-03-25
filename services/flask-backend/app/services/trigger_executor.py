"""Trigger Executor service for IceStreams workflow orchestration.

This module orchestrates trigger execution on the Flask API node. When a trigger fires:
1. Executes the trigger node locally
2. Publishes the job to Redis Stream for workers
3. Returns execution_id to the caller

Uses existing redis_streams.py for publishing job data to the task queue.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


# Placeholder for trigger registry
# These will be imported from actual trigger implementations when available
class BaseTrigger:
    """Base trigger class that all triggers inherit from."""

    node_type: str = ""
    name: str = ""
    description: str = ""
    category: str = "trigger"

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> list[str]:
        """Validate trigger configuration.

        Args:
            config: Configuration dictionary for the trigger.

        Returns:
            List of validation error messages (empty if valid).
        """
        return []

    async def execute(
        self, context: "NodeContext", inputs: Dict[str, Any]
    ) -> "NodeResult":
        """Execute the trigger node.

        Args:
            context: Execution context containing config, variables, and logger.
            inputs: Dictionary of input data.

        Returns:
            NodeResult with trigger outputs or error.
        """
        raise NotImplementedError


class NodeContext:
    """Execution context for node execution."""

    def __init__(
        self,
        execution_id: str,
        playbook_id: str,
        node_id: str,
        config: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize node context.

        Args:
            execution_id: Unique identifier for execution.
            playbook_id: ID of the playbook being executed.
            node_id: ID of the specific node.
            config: Node-specific configuration.
            variables: Workflow-level variables.
            logger: Logger instance for this context.
        """
        self.execution_id = execution_id
        self.playbook_id = playbook_id
        self.node_id = node_id
        self.config = config or {}
        self.variables = variables or {}
        self.logger = logger or logging.getLogger(__name__)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self.config.get(key, default)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a workflow variable.

        Args:
            key: Variable key.
            default: Default value if key not found.

        Returns:
            Variable value or default.
        """
        return self.variables.get(key, default)

    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(f"[{self.execution_id}][{self.node_id}] {message}")


class NodeResult:
    """Result of a node execution."""

    def __init__(
        self,
        success: bool,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0.0,
    ):
        """Initialize node result.

        Args:
            success: Whether execution was successful.
            outputs: Dictionary of output port names to values.
            error: Error message if execution failed.
            execution_time_ms: Execution time in milliseconds.
        """
        self.success = success
        self.outputs = outputs or {}
        self.error = error
        self.execution_time_ms = execution_time_ms

    @classmethod
    def success_result(
        cls, outputs: Dict[str, Any], execution_time_ms: float = 0.0
    ) -> "NodeResult":
        """Create a successful result.

        Args:
            outputs: Dictionary of outputs.
            execution_time_ms: Execution time in milliseconds.

        Returns:
            Successful NodeResult instance.
        """
        return cls(success=True, outputs=outputs, execution_time_ms=execution_time_ms)

    @classmethod
    def failure_result(cls, error: str, execution_time_ms: float = 0.0) -> "NodeResult":
        """Create a failure result.

        Args:
            error: Error message.
            execution_time_ms: Execution time in milliseconds.

        Returns:
            Failed NodeResult instance.
        """
        return cls(success=False, error=error, execution_time_ms=execution_time_ms)


# Trigger registry (populated when trigger implementations are available)
TRIGGER_REGISTRY: Dict[str, Type[BaseTrigger]] = {
    # Triggers to be registered as they are implemented:
    # "trigger_manual": ManualTrigger,
    # "trigger_mock_data": MockDataTrigger,
    # "trigger_webhook": WebhookTrigger,
    # "trigger_schedule": ScheduleTrigger,
    # "trigger_grpc": GrpcTrigger,
    # "trigger_mcp": McpServerTrigger,
}


@dataclass(slots=True)
class TriggerResult:
    """Result from executing a trigger.

    Attributes:
        execution_id: Unique execution identifier.
        success: Whether trigger execution succeeded.
        trigger_output: Outputs from the trigger (if successful).
        error: Error message (if failed).
        published_to_queue: Whether job was published to Redis Stream.
    """

    execution_id: str
    success: bool
    trigger_output: Optional[Dict[str, Any]]
    error: Optional[str]
    published_to_queue: bool


class TriggerExecutor:
    """Orchestrates trigger execution and job publishing for IceStreams.

    When a trigger fires:
    1. Executes the trigger node locally
    2. Publishes the job to Redis Stream for workers
    3. Returns execution_id to the caller
    """

    def __init__(self, redis_client: Any):
        """Initialize trigger executor.

        Args:
            redis_client: Redis client instance for publishing jobs.
        """
        self.redis_client = redis_client
        self.stream_name = "icestreams:tasks"

    async def execute_trigger(
        self,
        playbook_id: str,
        trigger_node: Dict[str, Any],
        remaining_graph: Dict[str, Any],
        trigger_data: Optional[Dict[str, Any]] = None,
    ) -> TriggerResult:
        """Execute a trigger and publish the job for workers.

        Args:
            playbook_id: ID of the playbook being executed.
            trigger_node: Trigger node configuration from the graph.
            remaining_graph: Remaining nodes and edges to execute after trigger.
            trigger_data: Optional data passed to the trigger (e.g., from webhook).

        Returns:
            TriggerResult with execution details and status.
        """
        execution_id = str(uuid.uuid4())

        # Get trigger type and class
        trigger_type = trigger_node.get("type")
        if not trigger_type:
            return TriggerResult(
                execution_id=execution_id,
                success=False,
                trigger_output=None,
                error="Trigger node missing 'type' field",
                published_to_queue=False,
            )

        trigger_class = TRIGGER_REGISTRY.get(trigger_type)
        if not trigger_class:
            return TriggerResult(
                execution_id=execution_id,
                success=False,
                trigger_output=None,
                error=f"Unknown trigger type: {trigger_type}",
                published_to_queue=False,
            )

        # Build trigger configuration
        config = trigger_node.get("data", {}).get("config", {})
        if trigger_data:
            config["_trigger_data"] = trigger_data

        # Create execution context
        context = NodeContext(
            execution_id=execution_id,
            playbook_id=playbook_id,
            node_id=trigger_node.get("id", "trigger"),
            config=config,
            variables={},
            logger=logger,
        )

        # Validate trigger configuration
        validation_errors = trigger_class.validate_config(config)
        if validation_errors:
            error_message = f"Config validation failed: {'; '.join(validation_errors)}"
            return TriggerResult(
                execution_id=execution_id,
                success=False,
                trigger_output=None,
                error=error_message,
                published_to_queue=False,
            )

        # Execute trigger
        trigger_instance = trigger_class()
        try:
            result = await trigger_instance.execute(context, {})
        except Exception as e:
            error_message = f"Trigger execution failed: {str(e)}"
            logger.exception(error_message)
            return TriggerResult(
                execution_id=execution_id,
                success=False,
                trigger_output=None,
                error=error_message,
                published_to_queue=False,
            )

        # Check trigger execution result
        if not result.success:
            return TriggerResult(
                execution_id=execution_id,
                success=False,
                trigger_output=None,
                error=result.error or "Trigger execution failed",
                published_to_queue=False,
            )

        # Prepare job payload for workers
        job_data = {
            "type": "playbook_execute",
            "payload": json.dumps(
                {
                    "execution_id": execution_id,
                    "playbook_id": playbook_id,
                    "trigger_output": result.outputs,
                    "nodes": remaining_graph.get("nodes", []),
                    "edges": remaining_graph.get("edges", []),
                    "config": remaining_graph.get("config", {}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
        }

        # Publish job to Redis Stream
        published = False
        try:
            self.redis_client.xadd(self.stream_name, job_data)
            published = True
            logger.info(
                f"Job published to queue: execution_id={execution_id}, "
                f"playbook_id={playbook_id}"
            )
        except Exception as e:
            logger.error(f"Failed to publish job to Redis Stream: {str(e)}")
            published = False

        return TriggerResult(
            execution_id=execution_id,
            success=True,
            trigger_output=result.outputs,
            error=None,
            published_to_queue=published,
        )

    def register_trigger(
        self, trigger_type: str, trigger_class: Type[BaseTrigger]
    ) -> None:
        """Register a trigger class in the registry.

        Args:
            trigger_type: Trigger type identifier (e.g., "trigger_manual").
            trigger_class: Trigger class to register.
        """
        if trigger_type in TRIGGER_REGISTRY:
            logger.warning(f"Overwriting existing trigger registration: {trigger_type}")
        TRIGGER_REGISTRY[trigger_type] = trigger_class
        logger.debug(f"Registered trigger: {trigger_type}")

    def get_registered_triggers(self) -> Dict[str, Type[BaseTrigger]]:
        """Get all registered triggers.

        Returns:
            Dictionary of trigger type to trigger class.
        """
        return TRIGGER_REGISTRY.copy()


# Global trigger executor instance
_trigger_executor: Optional[TriggerExecutor] = None


def get_trigger_executor(redis_client: Optional[Any] = None) -> TriggerExecutor:
    """Get or create the global trigger executor instance.

    Args:
        redis_client: Redis client instance (uses app config if not provided).

    Returns:
        TriggerExecutor instance.
    """
    global _trigger_executor

    if _trigger_executor is None:
        if redis_client is None:
            try:
                import redis
                from flask import current_app

                redis_url = current_app.config.get(
                    "REDIS_URL", "redis://localhost:6379/0"
                )
                redis_client = redis.from_url(redis_url, decode_responses=True)
            except (RuntimeError, ImportError):
                raise RuntimeError(
                    "Redis client required. Provide redis_client parameter or "
                    "ensure REDIS_URL is configured in Flask app"
                )

        _trigger_executor = TriggerExecutor(redis_client)

    return _trigger_executor
