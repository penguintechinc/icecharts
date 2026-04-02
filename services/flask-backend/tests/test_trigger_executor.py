"""Tests for Trigger Executor service.

Tests the trigger execution engine that orchestrates trigger nodes and publishes
jobs to Redis Stream for worker processing.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.trigger_executor import (BaseTrigger, NodeContext,
                                           NodeResult, TriggerExecutor,
                                           TriggerResult)


class TestNodeContext:
    """Test NodeContext data class."""

    def test_node_context_creation(self):
        """Test creating a NodeContext."""
        context = NodeContext(
            execution_id="exec-123",
            playbook_id="pb-456",
            node_id="node-789",
            config={"key": "value"},
            variables={"var": "val"},
        )

        assert context.execution_id == "exec-123"
        assert context.playbook_id == "pb-456"
        assert context.node_id == "node-789"
        assert context.config == {"key": "value"}
        assert context.variables == {"var": "val"}

    def test_node_context_defaults(self):
        """Test NodeContext with default values."""
        context = NodeContext(
            execution_id="exec-123",
            playbook_id="pb-456",
            node_id="node-789",
        )

        assert context.config == {}
        assert context.variables == {}
        assert context.logger is not None

    def test_node_context_get_config_value(self):
        """Test retrieving config values."""
        context = NodeContext(
            execution_id="exec-123",
            playbook_id="pb-456",
            node_id="node-789",
            config={"host": "localhost", "port": 5432},
        )

        assert context.get_config_value("host") == "localhost"
        assert context.get_config_value("port") == 5432
        assert context.get_config_value("missing") is None
        assert context.get_config_value("missing", "default") == "default"

    def test_node_context_get_variable(self):
        """Test retrieving variable values."""
        context = NodeContext(
            execution_id="exec-123",
            playbook_id="pb-456",
            node_id="node-789",
            variables={"user_id": 123, "action": "create"},
        )

        assert context.get_variable("user_id") == 123
        assert context.get_variable("action") == "create"
        assert context.get_variable("missing") is None
        assert context.get_variable("missing", "default") == "default"

    def test_node_context_logging_methods(self):
        """Test logging methods."""
        context = NodeContext(
            execution_id="exec-123",
            playbook_id="pb-456",
            node_id="node-789",
        )

        # These should not raise
        context.log_info("info message")
        context.log_error("error message")
        context.log_warning("warning message")
        context.log_debug("debug message")


class TestNodeResult:
    """Test NodeResult data class."""

    def test_node_result_success_factory(self):
        """Test creating a successful result."""
        outputs = {"result": "success", "count": 42}
        result = NodeResult.success_result(outputs, execution_time_ms=150.5)

        assert result.success is True
        assert result.outputs == outputs
        assert result.error is None
        assert result.execution_time_ms == 150.5

    def test_node_result_failure_factory(self):
        """Test creating a failure result."""
        result = NodeResult.failure_result(
            "Something went wrong", execution_time_ms=50.0
        )

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.outputs == {}
        assert result.execution_time_ms == 50.0

    def test_node_result_manual_creation_success(self):
        """Test manually creating a successful result."""
        result = NodeResult(
            success=True,
            outputs={"data": [1, 2, 3]},
            error=None,
            execution_time_ms=200.0,
        )

        assert result.success is True
        assert result.outputs == {"data": [1, 2, 3]}
        assert result.error is None

    def test_node_result_manual_creation_failure(self):
        """Test manually creating a failure result."""
        result = NodeResult(
            success=False,
            outputs={},
            error="Connection timeout",
            execution_time_ms=5000.0,
        )

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.execution_time_ms == 5000.0

    def test_node_result_default_execution_time(self):
        """Test NodeResult with default execution time."""
        result = NodeResult.success_result({"key": "val"})
        assert result.execution_time_ms == 0.0


class TestTriggerResult:
    """Test TriggerResult data class."""

    def test_trigger_result_success(self):
        """Test creating a successful trigger result."""
        result = TriggerResult(
            execution_id="exec-abc",
            success=True,
            trigger_output={"webhook_id": "wh-123"},
            error=None,
            published_to_queue=True,
        )

        assert result.execution_id == "exec-abc"
        assert result.success is True
        assert result.trigger_output == {"webhook_id": "wh-123"}
        assert result.error is None
        assert result.published_to_queue is True

    def test_trigger_result_failure(self):
        """Test creating a failed trigger result."""
        result = TriggerResult(
            execution_id="exec-def",
            success=False,
            trigger_output=None,
            error="Unknown trigger type",
            published_to_queue=False,
        )

        assert result.success is False
        assert result.error == "Unknown trigger type"
        assert result.published_to_queue is False


class TestTriggerExecutor:
    """Test TriggerExecutor service."""

    def test_executor_initialization(self):
        """Test creating a TriggerExecutor."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        assert executor.redis_client == mock_redis
        assert executor.stream_name == "icestreams:tasks"

    @pytest.mark.asyncio
    async def test_execute_trigger_missing_type_field(self):
        """Test execute_trigger with trigger node missing type."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={"id": "trigger-1", "data": {}},  # Missing 'type'
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is False
        assert "missing 'type' field" in result.error

    @pytest.mark.asyncio
    async def test_execute_trigger_unknown_trigger_type(self):
        """Test execute_trigger with unknown trigger type."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_unknown_type",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is False
        assert "Unknown trigger type" in result.error

    @pytest.mark.asyncio
    async def test_execute_trigger_success(self):
        """Test successful trigger execution."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        # Create a mock trigger class
        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"
            name = "Mock Trigger"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result({"trigger_data": "test_output"})

        # Register the mock trigger
        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is True
        assert result.trigger_output == {"trigger_data": "test_output"}
        assert result.error is None
        assert result.published_to_queue is True

    @pytest.mark.asyncio
    async def test_execute_trigger_config_validation_failure(self):
        """Test trigger execution with config validation failure."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return ["Missing required field: url", "Invalid format: timeout"]

            async def execute(self, context, inputs):
                return NodeResult.success_result({})

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is False
        assert "Config validation failed" in result.error
        assert "Missing required field: url" in result.error

    @pytest.mark.asyncio
    async def test_execute_trigger_execution_raises_exception(self):
        """Test trigger execution that raises exception."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                raise RuntimeError("Trigger execution failed")

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is False
        assert "Trigger execution failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_trigger_with_trigger_data(self):
        """Test execute_trigger passing trigger_data to trigger."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        received_config = {}

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                nonlocal received_config
                received_config = context.config.copy()
                return NodeResult.success_result({"received": True})

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {"url": "http://example.com"}},
            },
            remaining_graph={"nodes": [], "edges": []},
            trigger_data={"webhook_payload": {"id": 123}},
        )

        assert result.success is True
        assert "_trigger_data" in received_config
        assert received_config["_trigger_data"]["webhook_payload"]["id"] == 123

    @pytest.mark.asyncio
    async def test_execute_trigger_redis_publish_success(self):
        """Test that execute_trigger publishes job to Redis Stream."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result({"step": "completed"})

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [{"id": "n1"}], "edges": []},
        )

        assert result.published_to_queue is True
        mock_redis.xadd.assert_called_once()

        # Verify the published data
        call_args = mock_redis.xadd.call_args
        stream_name = call_args[0][0]
        job_data = call_args[0][1]

        assert stream_name == "icestreams:tasks"
        assert "type" in job_data
        assert job_data["type"] == "playbook_execute"
        assert "payload" in job_data

        # Verify payload structure
        payload = json.loads(job_data["payload"])
        assert payload["execution_id"] == result.execution_id
        assert payload["playbook_id"] == "pb-123"
        assert "trigger_output" in payload
        assert "nodes" in payload

    @pytest.mark.asyncio
    async def test_execute_trigger_redis_publish_failure(self):
        """Test that execute_trigger handles Redis publish failure gracefully."""
        mock_redis = MagicMock()
        mock_redis.xadd.side_effect = RuntimeError("Redis connection failed")
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result({"done": True})

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.success is True  # Trigger succeeded
        assert result.published_to_queue is False  # But publication failed

    @pytest.mark.asyncio
    async def test_execute_trigger_generates_unique_execution_ids(self):
        """Test that each trigger execution gets a unique ID."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result({})

        executor.register_trigger("trigger_mock", MockTrigger)

        result1 = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        result2 = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result1.execution_id != result2.execution_id

    @pytest.mark.asyncio
    async def test_execute_trigger_returns_trigger_output(self):
        """Test that execute_trigger returns trigger outputs."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        expected_output = {
            "webhook_id": "wh-123",
            "event_type": "order.created",
            "payload": {"order_id": 456},
        }

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result(expected_output)

        executor.register_trigger("trigger_mock", MockTrigger)

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph={"nodes": [], "edges": []},
        )

        assert result.trigger_output == expected_output

    @pytest.mark.asyncio
    async def test_execute_trigger_with_remaining_graph(self):
        """Test that execute_trigger includes remaining graph in published job."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class MockTrigger(BaseTrigger):
            node_type = "trigger_mock"

            @classmethod
            def validate_config(cls, config):
                return []

            async def execute(self, context, inputs):
                return NodeResult.success_result({})

        executor.register_trigger("trigger_mock", MockTrigger)

        remaining_graph = {
            "nodes": [
                {"id": "n1", "type": "action_type1"},
                {"id": "n2", "type": "action_type2"},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
            "config": {"timeout": 300},
        }

        result = await executor.execute_trigger(
            playbook_id="pb-123",
            trigger_node={
                "id": "trigger-1",
                "type": "trigger_mock",
                "data": {"config": {}},
            },
            remaining_graph=remaining_graph,
        )

        # Verify remaining graph was published
        call_args = mock_redis.xadd.call_args
        job_data = call_args[0][1]
        payload = json.loads(job_data["payload"])

        assert len(payload["nodes"]) == 2
        assert len(payload["edges"]) == 1
        assert payload["config"]["timeout"] == 300

    def test_register_trigger(self):
        """Test registering a trigger class."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class CustomTrigger(BaseTrigger):
            node_type = "trigger_custom"

        executor.register_trigger("trigger_custom", CustomTrigger)

        triggers = executor.get_registered_triggers()
        assert "trigger_custom" in triggers
        assert triggers["trigger_custom"] == CustomTrigger

    def test_register_trigger_overwrites_existing(self):
        """Test that registering a trigger overwrites existing registration."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class Trigger1(BaseTrigger):
            pass

        class Trigger2(BaseTrigger):
            pass

        executor.register_trigger("trigger_test", Trigger1)
        assert executor.get_registered_triggers()["trigger_test"] == Trigger1

        executor.register_trigger("trigger_test", Trigger2)
        assert executor.get_registered_triggers()["trigger_test"] == Trigger2

    def test_get_registered_triggers_returns_copy(self):
        """Test that get_registered_triggers returns a copy."""
        mock_redis = MagicMock()
        executor = TriggerExecutor(mock_redis)

        class TestTrigger(BaseTrigger):
            pass

        executor.register_trigger("trigger_test", TestTrigger)

        triggers1 = executor.get_registered_triggers()
        triggers1["trigger_new"] = TestTrigger  # Modify returned dict

        # Original registry should not be modified
        triggers2 = executor.get_registered_triggers()
        assert "trigger_new" not in triggers2
