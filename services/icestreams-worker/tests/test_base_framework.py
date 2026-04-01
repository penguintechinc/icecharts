#!/usr/bin/env python3
"""
Unit tests for IceStreams base node framework.

Tests cover:
- NodeInput and NodeOutput dataclass validation
- NodeContext functionality and logging
- NodeResult success and failure factory methods
- CloudAuth token expiration and refresh logic
- BaseNode abstract class and validation
- NodeRegistry registration and lookup
- @register_node decorator functionality
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from nodes.base import (
    BaseNode,
    CloudAuth,
    NodeContext,
    NodeInput,
    NodeOutput,
    NodeResult,
)
from executor.node_registry import (
    DuplicateNodeError,
    NodeInfo,
    NodeNotFoundError,
    NodeRegistry,
    register_node,
)


class TestNodeInput:
    """Test NodeInput dataclass validation and creation."""

    def test_valid_node_input_creation(self) -> None:
        """Test creating a valid NodeInput."""
        input_port = NodeInput(name="data", description="Input data stream")
        assert input_port.name == "data"
        assert input_port.description == "Input data stream"
        assert input_port.required is True
        assert input_port.data_type == "any"

    def test_node_input_with_all_fields(self) -> None:
        """Test creating NodeInput with all optional fields."""
        input_port = NodeInput(
            name="count",
            description="Number of items",
            required=False,
            data_type="number",
        )
        assert input_port.name == "count"
        assert input_port.required is False
        assert input_port.data_type == "number"

    def test_node_input_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            NodeInput(name="", description="Test")

    def test_node_input_empty_description_raises_error(self) -> None:
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            NodeInput(name="test", description="")

    def test_node_input_invalid_data_type_raises_error(self) -> None:
        """Test that invalid data_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid data_type"):
            NodeInput(name="test", description="Test", data_type="invalid")

    @pytest.mark.parametrize(
        "valid_type", ["any", "string", "number", "bool", "object", "array"]
    )
    def test_node_input_valid_data_types(self, valid_type: str) -> None:
        """Test all valid data types."""
        input_port = NodeInput(name="test", description="Test", data_type=valid_type)
        assert input_port.data_type == valid_type

    def test_node_input_is_frozen(self) -> None:
        """Test that NodeInput is immutable."""
        input_port = NodeInput(name="test", description="Test")
        with pytest.raises(AttributeError):
            input_port.name = "changed"


class TestNodeOutput:
    """Test NodeOutput dataclass validation and creation."""

    def test_valid_node_output_creation(self) -> None:
        """Test creating a valid NodeOutput."""
        output_port = NodeOutput(name="result", description="Output result")
        assert output_port.name == "result"
        assert output_port.description == "Output result"
        assert output_port.data_type == "any"

    def test_node_output_with_data_type(self) -> None:
        """Test creating NodeOutput with specific data type."""
        output_port = NodeOutput(
            name="count", description="Result count", data_type="number"
        )
        assert output_port.data_type == "number"

    def test_node_output_empty_name_raises_error(self) -> None:
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            NodeOutput(name="", description="Test")

    def test_node_output_empty_description_raises_error(self) -> None:
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            NodeOutput(name="test", description="")

    def test_node_output_invalid_data_type_raises_error(self) -> None:
        """Test that invalid data_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid data_type"):
            NodeOutput(name="test", description="Test", data_type="invalid")

    @pytest.mark.parametrize(
        "valid_type", ["any", "string", "number", "bool", "object", "array"]
    )
    def test_node_output_valid_data_types(self, valid_type: str) -> None:
        """Test all valid data types."""
        output_port = NodeOutput(name="test", description="Test", data_type=valid_type)
        assert output_port.data_type == valid_type

    def test_node_output_is_frozen(self) -> None:
        """Test that NodeOutput is immutable."""
        output_port = NodeOutput(name="test", description="Test")
        with pytest.raises(AttributeError):
            output_port.name = "changed"


class TestNodeContext:
    """Test NodeContext execution context functionality."""

    @pytest.fixture
    def valid_context(self) -> NodeContext:
        """Create a valid NodeContext for testing."""
        return NodeContext(
            execution_id="exec-123", playbook_id="pb-456", node_id="node-789"
        )

    def test_node_context_creation(self, valid_context: NodeContext) -> None:
        """Test creating a NodeContext with required fields."""
        assert valid_context.execution_id == "exec-123"
        assert valid_context.playbook_id == "pb-456"
        assert valid_context.node_id == "node-789"
        assert valid_context.config == {}
        assert valid_context.variables == {}

    def test_node_context_with_config_and_variables(self) -> None:
        """Test NodeContext with config and variables."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1",
            config={"timeout": 30, "retries": 3},
            variables={"api_key": "secret", "endpoint": "https://api.test"},
        )
        assert context.config == {"timeout": 30, "retries": 3}
        assert context.variables == {
            "api_key": "secret",
            "endpoint": "https://api.test",
        }

    def test_node_context_empty_execution_id_raises_error(self) -> None:
        """Test that empty execution_id raises ValueError."""
        with pytest.raises(ValueError, match="execution_id cannot be empty"):
            NodeContext(execution_id="", playbook_id="pb-1", node_id="node-1")

    def test_node_context_empty_playbook_id_raises_error(self) -> None:
        """Test that empty playbook_id raises ValueError."""
        with pytest.raises(ValueError, match="playbook_id cannot be empty"):
            NodeContext(execution_id="exec-1", playbook_id="", node_id="node-1")

    def test_node_context_empty_node_id_raises_error(self) -> None:
        """Test that empty node_id raises ValueError."""
        with pytest.raises(ValueError, match="node_id cannot be empty"):
            NodeContext(execution_id="exec-1", playbook_id="pb-1", node_id="")

    def test_get_config_value_returns_existing_key(
        self, valid_context: NodeContext
    ) -> None:
        """Test get_config_value returns existing configuration."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1",
            config={"key": "value"},
        )
        assert context.get_config_value("key") == "value"

    def test_get_config_value_returns_default_for_missing_key(
        self, valid_context: NodeContext
    ) -> None:
        """Test get_config_value returns default for missing key."""
        assert valid_context.get_config_value("missing", "default") == "default"

    def test_get_variable_returns_existing_variable(
        self, valid_context: NodeContext
    ) -> None:
        """Test get_variable returns existing variable."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1",
            variables={"var": "val"},
        )
        assert context.get_variable("var") == "val"

    def test_get_variable_returns_default_for_missing(
        self, valid_context: NodeContext
    ) -> None:
        """Test get_variable returns default for missing variable."""
        assert valid_context.get_variable("missing", "default") == "default"

    def test_log_info_method(self, valid_context: NodeContext) -> None:
        """Test log_info method includes execution context."""
        with patch.object(valid_context.logger, "info") as mock_info:
            valid_context.log_info("Test message")
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            assert "exec-123" in call_args
            assert "node-789" in call_args
            assert "Test message" in call_args

    def test_log_warning_method(self, valid_context: NodeContext) -> None:
        """Test log_warning method."""
        with patch.object(valid_context.logger, "warning") as mock_warning:
            valid_context.log_warning("Warning message")
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            assert "Warning message" in call_args

    def test_log_error_method(self, valid_context: NodeContext) -> None:
        """Test log_error method."""
        with patch.object(valid_context.logger, "error") as mock_error:
            valid_context.log_error("Error message")
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            assert "Error message" in call_args

    def test_log_debug_method(self, valid_context: NodeContext) -> None:
        """Test log_debug method."""
        with patch.object(valid_context.logger, "debug") as mock_debug:
            valid_context.log_debug("Debug message")
            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[0][0]
            assert "Debug message" in call_args


class TestNodeResult:
    """Test NodeResult success and failure creation."""

    def test_success_result_creation(self) -> None:
        """Test creating a successful NodeResult."""
        outputs = {"result": "data", "count": 42}
        result = NodeResult.success_result(outputs, execution_time_ms=100.5)
        assert result.success is True
        assert result.outputs == outputs
        assert result.error is None
        assert result.execution_time_ms == 100.5

    def test_failure_result_creation(self) -> None:
        """Test creating a failed NodeResult."""
        result = NodeResult.failure_result("Connection timeout", execution_time_ms=50.0)
        assert result.success is False
        assert result.outputs == {}
        assert result.error == "Connection timeout"
        assert result.execution_time_ms == 50.0

    def test_node_result_direct_creation_success(self) -> None:
        """Test direct NodeResult creation for success."""
        result = NodeResult(
            success=True, outputs={"data": "value"}, execution_time_ms=25.0
        )
        assert result.success is True
        assert result.outputs == {"data": "value"}

    def test_node_result_direct_creation_failure_requires_error(self) -> None:
        """Test that failed NodeResult requires error message."""
        with pytest.raises(
            ValueError, match="Failed NodeResult must include an error message"
        ):
            NodeResult(success=False, error=None)

    def test_node_result_negative_execution_time_raises_error(self) -> None:
        """Test that negative execution_time_ms raises ValueError."""
        with pytest.raises(ValueError, match="execution_time_ms cannot be negative"):
            NodeResult(success=True, outputs={}, execution_time_ms=-1.0)

    def test_node_result_with_empty_outputs(self) -> None:
        """Test NodeResult with empty outputs dict."""
        result = NodeResult.success_result({}, execution_time_ms=0.0)
        assert result.outputs == {}
        assert result.success is True

    def test_node_result_default_execution_time(self) -> None:
        """Test NodeResult defaults execution_time_ms to 0.0."""
        result = NodeResult.success_result({"key": "value"})
        assert result.execution_time_ms == 0.0


class TestCloudAuth:
    """Test CloudAuth credentials and token management."""

    def test_valid_cloud_auth_creation(self) -> None:
        """Test creating valid CloudAuth with AWS provider."""
        auth = CloudAuth(
            provider="aws",
            credentials={"access_key": "key123", "secret_key": "secret456"},
        )
        assert auth.provider == "aws"
        assert auth.credentials == {"access_key": "key123", "secret_key": "secret456"}
        assert auth.token is None
        assert auth.expires_at is None

    def test_cloud_auth_with_token(self) -> None:
        """Test CloudAuth with token-based authentication."""
        expires = datetime.now(UTC) + timedelta(hours=1)
        auth = CloudAuth(
            provider="gcp", credentials={}, token="token-abc123", expires_at=expires
        )
        assert auth.token == "token-abc123"
        assert auth.expires_at == expires

    def test_cloud_auth_empty_provider_raises_error(self) -> None:
        """Test that empty provider raises ValueError."""
        with pytest.raises(ValueError, match="provider cannot be empty"):
            CloudAuth(provider="", credentials={})

    def test_cloud_auth_invalid_provider_raises_error(self) -> None:
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Invalid provider"):
            CloudAuth(provider="azure", credentials={})

    @pytest.mark.parametrize("valid_provider", ["aws", "openwhisk", "gcp"])
    def test_cloud_auth_valid_providers(self, valid_provider: str) -> None:
        """Test all valid providers."""
        auth = CloudAuth(provider=valid_provider, credentials={})
        assert auth.provider == valid_provider

    def test_is_token_expired_with_no_expiration(self) -> None:
        """Test is_token_expired returns True when expires_at is None."""
        auth = CloudAuth(provider="aws", credentials={})
        assert auth.is_token_expired() is True

    def test_is_token_expired_with_future_expiration(self) -> None:
        """Test is_token_expired returns False for future expiration."""
        future = datetime.now(UTC) + timedelta(hours=1)
        auth = CloudAuth(
            provider="aws", credentials={}, token="token", expires_at=future
        )
        assert auth.is_token_expired() is False

    def test_is_token_expired_with_past_expiration(self) -> None:
        """Test is_token_expired returns True for past expiration."""
        past = datetime.now(UTC) - timedelta(hours=1)
        auth = CloudAuth(provider="aws", credentials={}, token="token", expires_at=past)
        assert auth.is_token_expired() is True

    def test_needs_refresh_with_no_expiration(self) -> None:
        """Test needs_refresh returns True when expires_at is None."""
        auth = CloudAuth(provider="aws", credentials={})
        assert auth.needs_refresh() is True

    def test_needs_refresh_with_buffer(self) -> None:
        """Test needs_refresh considers time buffer."""
        # Set expiration to 200 seconds in future (less than default 300s buffer)
        future = datetime.now(UTC) + timedelta(seconds=200)
        auth = CloudAuth(
            provider="aws", credentials={}, token="token", expires_at=future
        )
        assert auth.needs_refresh(buffer_seconds=300) is True

    def test_needs_refresh_sufficient_time_remaining(self) -> None:
        """Test needs_refresh returns False when enough time remains."""
        # Set expiration to 400 seconds in future (more than default 300s buffer)
        future = datetime.now(UTC) + timedelta(seconds=400)
        auth = CloudAuth(
            provider="aws", credentials={}, token="token", expires_at=future
        )
        assert auth.needs_refresh(buffer_seconds=300) is False


class TestBaseNode:
    """Test BaseNode abstract class."""

    def test_base_node_instantiation_requires_node_type(self) -> None:
        """Test that BaseNode requires node_type class attribute."""
        with pytest.raises(ValueError, match="must define node_type"):

            class IncompleteNode(BaseNode):
                name = "Test"
                description = "Test node"
                category = "test"

                async def execute(
                    self, context: NodeContext, inputs: Dict[str, Any]
                ) -> NodeResult:
                    return NodeResult.success_result({})

            IncompleteNode()

    def test_base_node_instantiation_requires_name(self) -> None:
        """Test that BaseNode requires name class attribute."""
        with pytest.raises(ValueError, match="must define name"):

            class IncompleteNode(BaseNode):
                node_type = "test"
                description = "Test node"
                category = "test"

                async def execute(
                    self, context: NodeContext, inputs: Dict[str, Any]
                ) -> NodeResult:
                    return NodeResult.success_result({})

            IncompleteNode()

    def test_base_node_instantiation_requires_description(self) -> None:
        """Test that BaseNode requires description class attribute."""
        with pytest.raises(ValueError, match="must define description"):

            class IncompleteNode(BaseNode):
                node_type = "test"
                name = "Test"
                category = "test"

                async def execute(
                    self, context: NodeContext, inputs: Dict[str, Any]
                ) -> NodeResult:
                    return NodeResult.success_result({})

            IncompleteNode()

    def test_base_node_instantiation_requires_category(self) -> None:
        """Test that BaseNode requires category class attribute."""
        with pytest.raises(ValueError, match="must define category"):

            class IncompleteNode(BaseNode):
                node_type = "test"
                name = "Test"
                description = "Test node"

                async def execute(
                    self, context: NodeContext, inputs: Dict[str, Any]
                ) -> NodeResult:
                    return NodeResult.success_result({})

            IncompleteNode()

    def test_valid_base_node_instantiation(self) -> None:
        """Test creating a valid BaseNode subclass."""

        class ValidNode(BaseNode):
            node_type = "valid_node"
            name = "Valid Node"
            description = "A valid test node"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = ValidNode()
        assert node.node_type == "valid_node"
        assert node.name == "Valid Node"
        assert node.description == "A valid test node"
        assert node.category == "test"

    def test_base_node_inputs_returns_empty_list(self) -> None:
        """Test that default inputs() returns empty list."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        assert TestNode.inputs() == []

    def test_base_node_outputs_returns_empty_list(self) -> None:
        """Test that default outputs() returns empty list."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        assert TestNode.outputs() == []

    def test_base_node_with_inputs_and_outputs(self) -> None:
        """Test BaseNode with input and output port definitions."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            @classmethod
            def inputs(cls) -> list:
                return [
                    NodeInput("data", "Input data"),
                    NodeInput("config", "Configuration", required=False),
                ]

            @classmethod
            def outputs(cls) -> list:
                return [
                    NodeOutput("result", "Output result"),
                ]

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({"result": "data"})

        inputs = TestNode.inputs()
        outputs = TestNode.outputs()
        assert len(inputs) == 2
        assert len(outputs) == 1
        assert inputs[0].name == "data"
        assert outputs[0].name == "result"

    def test_base_node_validate_config_returns_empty_list(self) -> None:
        """Test that default validate_config returns empty list."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = TestNode()
        errors = node.validate_config({})
        assert errors == []

    def test_base_node_validate_inputs_helper(self) -> None:
        """Test _validate_inputs helper method."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            @classmethod
            def inputs(cls) -> list:
                return [
                    NodeInput("data", "Required input"),
                    NodeInput("optional", "Optional input", required=False),
                ]

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = TestNode()
        errors = node._validate_inputs({"data": "value"})
        assert errors == []

        errors = node._validate_inputs({"optional": "value"})
        assert len(errors) == 1
        assert "data" in errors[0]

    def test_base_node_get_input_value_helper(self) -> None:
        """Test _get_input_value helper method."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = TestNode()
        inputs = {"key": "value"}
        assert node._get_input_value(inputs, "key") == "value"
        assert node._get_input_value(inputs, "missing") is None
        assert node._get_input_value(inputs, "missing", "default") == "default"

    def test_base_node_repr(self) -> None:
        """Test BaseNode __repr__ method."""

        class TestNode(BaseNode):
            node_type = "test_type"
            name = "Test Node"
            description = "Test"
            category = "test_cat"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = TestNode()
        repr_str = repr(node)
        assert "TestNode" in repr_str
        assert "test_type" in repr_str
        assert "test_cat" in repr_str

    @pytest.mark.asyncio
    async def test_base_node_cleanup_is_async(self) -> None:
        """Test that cleanup is an async method."""

        class TestNode(BaseNode):
            node_type = "test"
            name = "Test"
            description = "Test"
            category = "test"

            async def execute(
                self, context: NodeContext, inputs: Dict[str, Any]
            ) -> NodeResult:
                return NodeResult.success_result({})

        node = TestNode()
        await node.cleanup()


class TestNodeRegistry:
    """Test NodeRegistry registration and lookup."""

    @pytest.fixture(autouse=True)
    def cleanup_registry(self) -> None:
        """Clean up registry before and after each test."""
        NodeRegistry.clear()
        yield
        NodeRegistry.clear()

    def test_register_node_basic(self) -> None:
        """Test registering a basic node."""

        class TestNode:
            pass

        NodeRegistry.register(
            node_type="test_node", node_class=TestNode, category="test"
        )

        assert NodeRegistry.is_registered("test_node")
        assert NodeRegistry.get("test_node") == TestNode

    def test_register_node_with_display_name_and_description(self) -> None:
        """Test registering node with custom display name and description."""

        class TestNode:
            """Original docstring."""

            pass

        NodeRegistry.register(
            node_type="test_node",
            node_class=TestNode,
            category="test",
            display_name="Custom Display Name",
            description="Custom description",
        )

        info = NodeRegistry.get_info("test_node")
        assert info.display_name == "Custom Display Name"
        assert info.description == "Custom description"

    def test_register_node_defaults_display_name(self) -> None:
        """Test that display_name is auto-generated from node_type."""

        class TestNode:
            pass

        NodeRegistry.register(
            node_type="my_test_node", node_class=TestNode, category="test"
        )

        info = NodeRegistry.get_info("my_test_node")
        assert info.display_name == "My Test Node"

    def test_register_node_uses_docstring_as_description(self) -> None:
        """Test that description defaults to first line of docstring."""

        class TestNode:
            """This is the first line.
            This is the second line."""

            pass

        NodeRegistry.register(
            node_type="test_node", node_class=TestNode, category="test"
        )

        info = NodeRegistry.get_info("test_node")
        assert "This is the first line" in info.description

    def test_register_duplicate_node_raises_error(self) -> None:
        """Test that registering duplicate node raises DuplicateNodeError."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("dup", Node1, "test")

        with pytest.raises(DuplicateNodeError):
            NodeRegistry.register("dup", Node2, "test")

    def test_register_duplicate_node_with_override(self) -> None:
        """Test that allow_override permits re-registration."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("dup", Node1, "test")
        NodeRegistry.register("dup", Node2, "test", allow_override=True)

        assert NodeRegistry.get("dup") == Node2

    def test_register_invalid_node_type_raises_error(self) -> None:
        """Test that invalid node_type raises ValueError."""

        class TestNode:
            pass

        with pytest.raises(ValueError, match="Invalid node_type"):
            NodeRegistry.register("", TestNode, "test")

    def test_register_invalid_node_class_raises_error(self) -> None:
        """Test that invalid node_class raises ValueError."""
        with pytest.raises(ValueError, match="Invalid node_class"):
            NodeRegistry.register("test", None, "test")

    def test_register_invalid_category_raises_error(self) -> None:
        """Test that invalid category raises ValueError."""

        class TestNode:
            pass

        with pytest.raises(ValueError, match="Invalid category"):
            NodeRegistry.register("test", TestNode, "")

    def test_get_node_class_returns_class(self) -> None:
        """Test get returns the node class."""

        class TestNode:
            pass

        NodeRegistry.register("test", TestNode, "test")
        result = NodeRegistry.get("test")
        assert result is TestNode

    def test_get_nonexistent_node_raises_error(self) -> None:
        """Test get raises NodeNotFoundError for missing node."""
        with pytest.raises(NodeNotFoundError):
            NodeRegistry.get("nonexistent")

    def test_get_nonexistent_node_returns_none_when_raise_false(self) -> None:
        """Test get returns None when raise_on_missing is False."""
        result = NodeRegistry.get("nonexistent", raise_on_missing=False)
        assert result is None

    def test_get_info_returns_node_info(self) -> None:
        """Test get_info returns NodeInfo object."""

        class TestNode:
            pass

        NodeRegistry.register(
            "test", TestNode, "test_cat", display_name="Test", description="Test node"
        )

        info = NodeRegistry.get_info("test")
        assert isinstance(info, NodeInfo)
        assert info.node_type == "test"
        assert info.node_class is TestNode
        assert info.category == "test_cat"

    def test_get_all_returns_all_registered_nodes(self) -> None:
        """Test get_all returns all registered nodes."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("node1", Node1, "test")
        NodeRegistry.register("node2", Node2, "test")

        all_nodes = NodeRegistry.get_all()
        assert len(all_nodes) == 2
        assert all_nodes["node1"] is Node1
        assert all_nodes["node2"] is Node2

    def test_get_by_category_filters_nodes(self) -> None:
        """Test get_by_category returns only nodes in specified category."""

        class Node1:
            pass

        class Node2:
            pass

        class Node3:
            pass

        NodeRegistry.register("node1", Node1, "transform")
        NodeRegistry.register("node2", Node2, "transform")
        NodeRegistry.register("node3", Node3, "action")

        transform_nodes = NodeRegistry.get_by_category("transform")
        assert len(transform_nodes) == 2

        action_nodes = NodeRegistry.get_by_category("action")
        assert len(action_nodes) == 1

    def test_get_categories_returns_unique_categories(self) -> None:
        """Test get_categories returns sorted unique categories."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("node1", Node1, "transform")
        NodeRegistry.register("node2", Node2, "action")
        NodeRegistry.register("node3", Node1, "transform")

        categories = NodeRegistry.get_categories()
        assert categories == ["action", "transform"]

    def test_is_registered_returns_true_for_registered(self) -> None:
        """Test is_registered returns True for registered nodes."""

        class TestNode:
            pass

        NodeRegistry.register("test", TestNode, "test")
        assert NodeRegistry.is_registered("test") is True

    def test_is_registered_returns_false_for_unregistered(self) -> None:
        """Test is_registered returns False for unregistered nodes."""
        assert NodeRegistry.is_registered("nonexistent") is False

    def test_unregister_removes_node(self) -> None:
        """Test unregister removes a node from registry."""

        class TestNode:
            pass

        NodeRegistry.register("test", TestNode, "test")
        assert NodeRegistry.is_registered("test")

        result = NodeRegistry.unregister("test")
        assert result is True
        assert NodeRegistry.is_registered("test") is False

    def test_unregister_nonexistent_returns_false(self) -> None:
        """Test unregister returns False for nonexistent node."""
        result = NodeRegistry.unregister("nonexistent")
        assert result is False

    def test_clear_removes_all_nodes(self) -> None:
        """Test clear removes all registered nodes."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("node1", Node1, "test")
        NodeRegistry.register("node2", Node2, "test")

        count = NodeRegistry.clear()
        assert count == 2
        assert NodeRegistry.count() == 0

    def test_count_returns_total_nodes(self) -> None:
        """Test count returns total number of registered nodes."""

        class Node1:
            pass

        class Node2:
            pass

        NodeRegistry.register("node1", Node1, "test")
        NodeRegistry.register("node2", Node2, "test")

        assert NodeRegistry.count() == 2

    def test_is_initialized_tracking(self) -> None:
        """Test is_initialized tracking."""
        assert NodeRegistry.is_initialized() is False

        NodeRegistry.mark_initialized()
        assert NodeRegistry.is_initialized() is True

        NodeRegistry.clear()
        assert NodeRegistry.is_initialized() is False


class TestRegisterNodeDecorator:
    """Test @register_node decorator."""

    @pytest.fixture(autouse=True)
    def cleanup_registry(self) -> None:
        """Clean up registry before and after each test."""
        NodeRegistry.clear()
        yield
        NodeRegistry.clear()

    def test_register_node_decorator_registers_class(self) -> None:
        """Test that @register_node decorator registers the class."""

        @register_node(
            "decorated_node",
            "test",
            display_name="Decorated Node",
            description="A decorated test node",
        )
        class DecoratedNode:
            pass

        assert NodeRegistry.is_registered("decorated_node")
        assert NodeRegistry.get("decorated_node") is DecoratedNode

    def test_register_node_decorator_returns_class_unchanged(self) -> None:
        """Test that decorator returns class unchanged."""

        class OriginalNode:
            def method(self) -> str:
                return "test"

        decorated = register_node("test", "test")(OriginalNode)
        assert decorated is OriginalNode

        instance = decorated()
        assert instance.method() == "test"

    def test_register_node_decorator_with_duplicate_raises_error(self) -> None:
        """Test that duplicate registration via decorator raises error."""

        @register_node("dup", "test")
        class Node1:
            pass

        with pytest.raises(DuplicateNodeError):

            @register_node("dup", "test")
            class Node2:
                pass

    def test_register_node_decorator_minimal_parameters(self) -> None:
        """Test decorator with only required parameters."""

        @register_node("minimal", "test")
        class MinimalNode:
            pass

        info = NodeRegistry.get_info("minimal")
        assert info.node_type == "minimal"
        assert info.category == "test"

    def test_register_node_decorator_all_parameters(self) -> None:
        """Test decorator with all parameters."""

        @register_node(
            "full", "test", display_name="Full Node", description="Complete node"
        )
        class FullNode:
            pass

        info = NodeRegistry.get_info("full")
        assert info.display_name == "Full Node"
        assert info.description == "Complete node"
