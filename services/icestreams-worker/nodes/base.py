"""
Base node framework for IceStreams workflow execution system.

This module provides the foundational classes and interfaces for building workflow
nodes that can be executed asynchronously in the IceStreams worker. All node
implementations must inherit from BaseNode and implement the execute method.

The framework uses slotted dataclasses throughout for memory efficiency and includes
comprehensive type hints for better IDE support and runtime validation.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True, frozen=True)
class NodeInput:
    """
    Defines an input port for a workflow node.

    Input ports represent data entry points for nodes. Each port has a name,
    description, and optionally a data type hint and required flag.

    Attributes:
        name: Port identifier (e.g., "in", "data", "condition").
        description: Human-readable description of what this input accepts.
        required: Whether this input must be provided for execution.
        data_type: Type hint for the expected data ("any", "string", "number", "bool", "object", "array").
    """

    name: str
    description: str
    required: bool = True
    data_type: str = "any"

    def __post_init__(self) -> None:
        """Validate input configuration after initialization."""
        if not self.name:
            raise ValueError("NodeInput name cannot be empty")
        if not self.description:
            raise ValueError("NodeInput description cannot be empty")
        if self.data_type not in {"any", "string", "number", "bool", "object", "array"}:
            raise ValueError(
                f"Invalid data_type '{self.data_type}'. "
                "Must be one of: any, string, number, bool, object, array"
            )


@dataclass(slots=True, frozen=True)
class NodeOutput:
    """
    Defines an output port for a workflow node.

    Output ports represent data exit points from nodes. Each port has a name,
    description, and optionally a data type hint.

    Attributes:
        name: Port identifier (e.g., "out", "true", "false", "result").
        description: Human-readable description of what this output provides.
        data_type: Type hint for the output data ("any", "string", "number", "bool", "object", "array").
    """

    name: str
    description: str
    data_type: str = "any"

    def __post_init__(self) -> None:
        """Validate output configuration after initialization."""
        if not self.name:
            raise ValueError("NodeOutput name cannot be empty")
        if not self.description:
            raise ValueError("NodeOutput description cannot be empty")
        if self.data_type not in {"any", "string", "number", "bool", "object", "array"}:
            raise ValueError(
                f"Invalid data_type '{self.data_type}'. "
                "Must be one of: any, string, number, bool, object, array"
            )


@dataclass(slots=True)
class NodeContext:
    """
    Execution context provided to a node during execution.

    Contains all necessary runtime information for node execution, including
    execution tracking IDs, node configuration, workflow variables, and logging.

    Attributes:
        execution_id: Unique identifier for this workflow execution instance.
        playbook_id: ID of the playbook/workflow being executed.
        node_id: ID of the specific node being executed.
        config: Node-specific configuration provided by the user.
        variables: Workflow-level variables accessible to all nodes.
        logger: Logger instance for this node's execution.
    """

    execution_id: str
    playbook_id: str
    node_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    def __post_init__(self) -> None:
        """Validate context after initialization."""
        if not self.execution_id:
            raise ValueError("NodeContext execution_id cannot be empty")
        if not self.playbook_id:
            raise ValueError("NodeContext playbook_id cannot be empty")
        if not self.node_id:
            raise ValueError("NodeContext node_id cannot be empty")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Safely retrieve a configuration value with an optional default.

        Args:
            key: Configuration key to retrieve.
            default: Default value if key is not found.

        Returns:
            Configuration value or default if not found.
        """
        return self.config.get(key, default)

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Safely retrieve a workflow variable with an optional default.

        Args:
            key: Variable key to retrieve.
            default: Default value if key is not found.

        Returns:
            Variable value or default if not found.
        """
        return self.variables.get(key, default)

    def log_info(self, message: str) -> None:
        """Log an info message with execution context."""
        self.logger.info(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_warning(self, message: str) -> None:
        """Log a warning message with execution context."""
        self.logger.warning(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_error(self, message: str) -> None:
        """Log an error message with execution context."""
        self.logger.error(f"[{self.execution_id}][{self.node_id}] {message}")

    def log_debug(self, message: str) -> None:
        """Log a debug message with execution context."""
        self.logger.debug(f"[{self.execution_id}][{self.node_id}] {message}")


@dataclass(slots=True)
class NodeResult:
    """
    Result of a node execution.

    Contains the success status, output data keyed by port name, optional error
    information, and execution timing metrics.

    Attributes:
        success: Whether the node executed successfully.
        outputs: Dictionary mapping output port names to their data values.
        error: Error message if execution failed (None if successful).
        execution_time_ms: Time taken to execute the node in milliseconds.
    """

    success: bool
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        if not self.success and self.error is None:
            raise ValueError("Failed NodeResult must include an error message")
        if self.execution_time_ms < 0:
            raise ValueError("execution_time_ms cannot be negative")

    @classmethod
    def success_result(
        cls, outputs: Dict[str, Any], execution_time_ms: float = 0.0
    ) -> NodeResult:
        """
        Create a successful node result.

        Args:
            outputs: Dictionary of output port names to data values.
            execution_time_ms: Execution time in milliseconds.

        Returns:
            NodeResult instance indicating success.
        """
        return cls(
            success=True,
            outputs=outputs,
            error=None,
            execution_time_ms=execution_time_ms,
        )

    @classmethod
    def failure_result(cls, error: str, execution_time_ms: float = 0.0) -> NodeResult:
        """
        Create a failed node result.

        Args:
            error: Error message describing the failure.
            execution_time_ms: Execution time in milliseconds.

        Returns:
            NodeResult instance indicating failure.
        """
        return cls(
            success=False, outputs={}, error=error, execution_time_ms=execution_time_ms
        )


@dataclass(slots=True)
class CloudAuth:
    """
    Cloud provider authentication credentials.

    Stores authentication information for cloud service providers like AWS,
    OpenWhisk, and GCP. Supports both static credentials and token-based
    authentication with expiration tracking.

    Attributes:
        provider: Cloud provider identifier ("aws", "openwhisk", "gcp").
        credentials: Provider-specific credential dictionary (e.g., access keys, API keys).
        token: Optional authentication token for token-based auth.
        expires_at: Optional token expiration timestamp.
    """

    provider: str
    credentials: Dict[str, Any] = field(default_factory=dict)
    token: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate cloud authentication configuration."""
        if not self.provider:
            raise ValueError("CloudAuth provider cannot be empty")
        if self.provider not in {"aws", "openwhisk", "gcp"}:
            raise ValueError(
                f"Invalid provider '{self.provider}'. "
                "Must be one of: aws, openwhisk, gcp"
            )

    def is_token_expired(self) -> bool:
        """
        Check if the authentication token has expired.

        Returns:
            True if token is expired or expires_at is not set, False otherwise.
        """
        if self.expires_at is None:
            return True
        return datetime.now(UTC) >= self.expires_at

    def needs_refresh(self, buffer_seconds: int = 300) -> bool:
        """
        Check if token needs refresh with a time buffer.

        Args:
            buffer_seconds: Number of seconds before expiration to consider refresh needed.

        Returns:
            True if token should be refreshed, False otherwise.
        """
        if self.expires_at is None:
            return True
        from datetime import timedelta

        refresh_time = self.expires_at - timedelta(seconds=buffer_seconds)
        return datetime.now(UTC) >= refresh_time


class BaseNode(ABC):
    """
    Abstract base class for all IceStreams workflow nodes.

    All node implementations must inherit from this class and implement the
    execute method. The class provides node metadata (type, name, description,
    category) and defines the input/output port structure.

    Class Attributes:
        node_type: Unique identifier for this node type (e.g., "debug", "condition", "http_request").
        name: Display name for the node in the UI.
        description: Human-readable description of what this node does.
        category: Category for organizing nodes in the UI (e.g., "core", "logic", "cloud").

    Methods:
        inputs: Returns list of input port definitions.
        outputs: Returns list of output port definitions.
        execute: Async method that performs the node's operation.
        validate_config: Optional method to validate node configuration.
        cleanup: Optional async method for cleanup after execution.
    """

    # Subclasses must override these class attributes
    node_type: str = ""
    name: str = ""
    description: str = ""
    category: str = ""

    def __init__(self) -> None:
        """Initialize the base node."""
        if not self.node_type:
            raise ValueError(
                f"{self.__class__.__name__} must define node_type class attribute"
            )
        if not self.name:
            raise ValueError(
                f"{self.__class__.__name__} must define name class attribute"
            )
        if not self.description:
            raise ValueError(
                f"{self.__class__.__name__} must define description class attribute"
            )
        if not self.category:
            raise ValueError(
                f"{self.__class__.__name__} must define category class attribute"
            )

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Define the input ports for this node.

        Returns:
            List of NodeInput instances defining the node's input ports.
        """
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define the output ports for this node.

        Returns:
            List of NodeOutput instances defining the node's output ports.
        """
        return []

    @abstractmethod
    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the node's operation asynchronously.

        This is the main entry point for node execution. Implementations should:
        1. Validate inputs against expected ports
        2. Perform the node's operation
        3. Return a NodeResult with outputs or error

        Args:
            context: Execution context containing config, variables, and logger.
            inputs: Dictionary mapping input port names to their data values.

        Returns:
            NodeResult indicating success/failure and output data.

        Raises:
            Exception: Implementation-specific exceptions may be raised.
        """
        pass

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate the node's configuration.

        Override this method to implement custom configuration validation.
        Return a list of error messages; empty list indicates valid configuration.

        Args:
            config: Node configuration dictionary to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        return []

    async def cleanup(self) -> None:
        """
        Perform cleanup after node execution.

        Override this method to implement custom cleanup logic such as:
        - Closing file handles
        - Releasing network connections
        - Cleaning up temporary resources

        This method is called after execute completes, regardless of success/failure.
        """
        pass

    def _validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Validate that required inputs are provided.

        Internal helper method to check if all required input ports have data.

        Args:
            inputs: Dictionary of provided input data.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        for input_port in self.inputs():
            if input_port.required and input_port.name not in inputs:
                errors.append(f"Required input '{input_port.name}' is missing")
        return errors

    def _get_input_value(
        self, inputs: Dict[str, Any], port_name: str, default: Any = None
    ) -> Any:
        """
        Safely retrieve an input value with an optional default.

        Helper method for node implementations to safely access input data.

        Args:
            inputs: Dictionary of provided input data.
            port_name: Name of the input port.
            default: Default value if port is not provided.

        Returns:
            Input value or default if not found.
        """
        return inputs.get(port_name, default)

    def __repr__(self) -> str:
        """Return a string representation of the node."""
        return (
            f"{self.__class__.__name__}(node_type={self.node_type!r}, "
            f"name={self.name!r}, category={self.category!r})"
        )
