#!/usr/bin/env python3
"""
Integration tests for IceStreams playbook executor.

Tests cover:
- Complete playbook execution flow with simple node graph
- Topological sorting and execution order
- Data flow between nodes through edges
- Error handling during execution
- Execution results and status tracking
- Mock external dependencies (Redis, HTTP, gRPC)
- Node registry integration
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import redis.asyncio as aioredis

from executor.playbook_executor import (
    BaseNode,
    ExecutionResult,
    NodeContext,
    NodeData,
    NodeResult,
    NodeStatus,
    PlaybookExecutor,
    PassThroughNode,
)
from executor.node_registry import NodeRegistry, register_node
from nodes.base import (
    BaseNode as BaseNodeFramework,
    NodeContext as NodeContextFramework,
    NodeInput,
    NodeOutput,
    NodeResult as NodeResultFramework,
)


# Mock node implementations for testing
class DoubleTransformNode(BaseNode):
    """Test node that doubles numeric values."""

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Double the input value."""
        if "default" in inputs:
            input_data = inputs["default"]
            value = input_data.data.get("value", 0)
            doubled = value * 2

            result = NodeData(
                data={"value": doubled, "doubled": True},
                metadata={"operation": "double"},
                source_node_id=self.context.node_id
            )
            return {"default": result}

        return {}


class AddOneTransformNode(BaseNode):
    """Test node that adds one to numeric values."""

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Add one to the input value."""
        if "default" in inputs:
            input_data = inputs["default"]
            value = input_data.data.get("value", 0)
            incremented = value + 1

            result = NodeData(
                data={"value": incremented, "incremented": True},
                metadata={"operation": "add_one"},
                source_node_id=self.context.node_id
            )
            return {"default": result}

        return {}


class MockActionNode(BaseNode):
    """Test node that performs an action (mock HTTP request)."""

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Perform a mock action."""
        if "default" in inputs:
            input_data = inputs["default"]

            result = NodeData(
                data={
                    "status": "success",
                    "message": "Action completed",
                    "input": input_data.data
                },
                metadata={"action": "http_request"},
                source_node_id=self.context.node_id
            )
            return {"result": result}

        return {}


class FailingNode(BaseNode):
    """Test node that always fails."""

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Always raise an error."""
        raise RuntimeError("Intentional test failure")


class SlowNode(BaseNode):
    """Test node that takes a long time to execute."""

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Sleep for a long time."""
        await asyncio.sleep(5.0)
        return {"default": NodeData(data={"result": "slow"}, source_node_id=self.context.node_id)}


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Create a mock Redis client."""
    return AsyncMock(spec=aioredis.Redis)


@pytest.fixture
def playbook_executor(mock_redis_client: AsyncMock) -> PlaybookExecutor:
    """Create a PlaybookExecutor instance for testing."""
    return PlaybookExecutor(
        redis_client=mock_redis_client,
        execution_id="test-exec-123",
        playbook_id="test-pb-456",
        node_timeout_seconds=10.0
    )


class TestPlaybookExecutorBasics:
    """Test basic PlaybookExecutor functionality."""

    def test_playbook_executor_initialization(self, mock_redis_client: AsyncMock) -> None:
        """Test PlaybookExecutor initialization."""
        executor = PlaybookExecutor(
            redis_client=mock_redis_client,
            execution_id="exec-1",
            playbook_id="pb-1",
            node_timeout_seconds=30.0
        )

        assert executor.execution_id == "exec-1"
        assert executor.playbook_id == "pb-1"
        assert executor.node_timeout_seconds == 30.0
        assert executor._node_outputs == {}
        assert executor._execution_order == []

    def test_playbook_executor_default_timeout(self, mock_redis_client: AsyncMock) -> None:
        """Test PlaybookExecutor uses default timeout."""
        executor = PlaybookExecutor(
            redis_client=mock_redis_client,
            execution_id="exec-1",
            playbook_id="pb-1"
        )

        assert executor.node_timeout_seconds == PlaybookExecutor.DEFAULT_NODE_TIMEOUT_SECONDS


class TestSimplePlaybookExecution:
    """Test execution of simple playbooks."""

    @pytest.mark.asyncio
    async def test_single_node_execution(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test executing a playbook with a single node."""
        playbook_data = {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "passthrough",
                    "data": {"label": "Start", "category": "trigger"}
                }
            ],
            "edges": [],
            "trigger_output": {"value": 10},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True
        assert len(result.completed_nodes) == 1
        assert result.completed_nodes[0] == "node-1"
        assert len(result.failed_nodes) == 0

    @pytest.mark.asyncio
    async def test_linear_three_node_chain(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test executing a linear chain of 3 nodes."""
        # Set up: trigger -> transform -> action
        playbook_data = {
            "nodes": [
                {
                    "id": "trigger",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "transform",
                    "type": "double_transform",
                    "data": {"label": "Double", "category": "transform"}
                },
                {
                    "id": "action",
                    "type": "mock_action",
                    "data": {"label": "Action", "category": "action"}
                }
            ],
            "edges": [
                {"source": "trigger", "target": "transform", "sourceHandle": "default", "targetHandle": "default"},
                {"source": "transform", "target": "action", "sourceHandle": "default", "targetHandle": "default"}
            ],
            "trigger_output": {"value": 5},
            "config": {}
        }

        # Mock node registry
        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.side_effect = lambda node_type: {
                "trigger": PassThroughNode,
                "double_transform": DoubleTransformNode,
                "mock_action": MockActionNode
            }.get(node_type, PassThroughNode)

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True
        assert len(result.completed_nodes) == 3

    @pytest.mark.asyncio
    async def test_no_nodes_in_playbook(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test execution fails when playbook has no nodes."""
        playbook_data = {
            "nodes": [],
            "edges": [],
            "trigger_output": {},
            "config": {}
        }

        result = await playbook_executor.execute(playbook_data)

        assert result.success is False
        assert result.error == "No nodes in playbook"

    @pytest.mark.asyncio
    async def test_execution_order_computation(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that execution order is computed correctly."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]

        execution_order = playbook_executor._get_execution_order(nodes, edges)

        assert execution_order == ["n1", "n2", "n3"]


class TestDataFlow:
    """Test data flow between nodes."""

    @pytest.mark.asyncio
    async def test_data_flows_through_nodes(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that data flows correctly through connected nodes."""
        playbook_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "double",
                    "type": "double_transform",
                    "data": {"label": "Double", "category": "transform"}
                }
            ],
            "edges": [
                {"source": "start", "target": "double", "sourceHandle": "default", "targetHandle": "default"}
            ],
            "trigger_output": {"value": 5},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.side_effect = lambda node_type: {
                "trigger": PassThroughNode,
                "double_transform": DoubleTransformNode
            }.get(node_type, PassThroughNode)

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True

    def test_gather_inputs_from_upstream(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test _gather_inputs collects data from upstream nodes."""
        node_outputs = {
            "upstream_1": {
                "output_a": NodeData(data={"value": 10}, source_node_id="upstream_1")
            },
            "upstream_2": {
                "output_b": NodeData(data={"value": 20}, source_node_id="upstream_2")
            }
        }

        edges = [
            {"source": "upstream_1", "target": "target", "sourceHandle": "output_a", "targetHandle": "input_a"},
            {"source": "upstream_2", "target": "target", "sourceHandle": "output_b", "targetHandle": "input_b"}
        ]

        inputs = playbook_executor._gather_inputs("target", edges, node_outputs)

        assert "input_a" in inputs
        assert "input_b" in inputs
        assert inputs["input_a"].data["value"] == 10
        assert inputs["input_b"].data["value"] == 20

    def test_route_outputs_to_downstream(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test _route_outputs stores outputs for downstream consumption."""
        outputs = {
            "output_1": NodeData(data={"result": "a"}, source_node_id="node_1"),
            "output_2": NodeData(data={"result": "b"}, source_node_id="node_1")
        }

        result = NodeResult(
            node_id="node_1",
            status=NodeStatus.SUCCESS,
            outputs=outputs
        )

        edges = [
            {"source": "node_1", "target": "node_2", "sourceHandle": "output_1"}
        ]

        playbook_executor._route_outputs("node_1", result, edges)

        assert playbook_executor._node_outputs["node_1"] == outputs


class TestErrorHandling:
    """Test error handling during playbook execution."""

    @pytest.mark.asyncio
    async def test_node_execution_failure_stops_playbook(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that node failure stops execution by default."""
        playbook_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "fail",
                    "type": "failing",
                    "data": {"label": "Fail", "category": "transform"}
                },
                {
                    "id": "unreachable",
                    "type": "passthrough",
                    "data": {"label": "Unreachable", "category": "action"}
                }
            ],
            "edges": [
                {"source": "start", "target": "fail"},
                {"source": "fail", "target": "unreachable"}
            ],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.side_effect = lambda node_type: {
                "trigger": PassThroughNode,
                "failing": FailingNode,
                "passthrough": PassThroughNode
            }.get(node_type, PassThroughNode)

            result = await playbook_executor.execute(playbook_data)

        assert result.success is False
        assert len(result.failed_nodes) >= 1
        # The unreachable node should not have been reached
        assert len(result.completed_nodes) < 3

    @pytest.mark.asyncio
    async def test_continue_on_error_configuration(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that continue_on_error config allows execution to continue."""
        playbook_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "fail",
                    "type": "failing",
                    "data": {"label": "Fail", "category": "transform"}
                },
                {
                    "id": "continue",
                    "type": "passthrough",
                    "data": {"label": "Continue", "category": "action"}
                }
            ],
            "edges": [
                {"source": "start", "target": "fail"},
                {"source": "start", "target": "continue"}
            ],
            "trigger_output": {},
            "config": {"continue_on_error": True}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.side_effect = lambda node_type: {
                "trigger": PassThroughNode,
                "failing": FailingNode,
                "passthrough": PassThroughNode
            }.get(node_type, PassThroughNode)

            result = await playbook_executor.execute(playbook_data)

        # With continue_on_error, execution should continue
        assert len(result.failed_nodes) >= 1
        assert len(result.completed_nodes) >= 1

    @pytest.mark.asyncio
    async def test_node_timeout_error(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that node timeout produces proper error."""
        # Set a very short timeout
        playbook_executor.node_timeout_seconds = 0.1

        playbook_data = {
            "nodes": [
                {
                    "id": "slow",
                    "type": "slow",
                    "data": {"label": "Slow", "category": "transform"}
                }
            ],
            "edges": [],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.side_effect = lambda node_type: {
                "slow": SlowNode
            }.get(node_type, PassThroughNode)

            result = await playbook_executor.execute(playbook_data)

        assert result.success is False
        assert len(result.failed_nodes) >= 1


class TestExecutionResults:
    """Test execution result tracking and reporting."""

    @pytest.mark.asyncio
    async def test_execution_result_contains_all_nodes(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that execution result includes all node results."""
        playbook_data = {
            "nodes": [
                {
                    "id": "node_1",
                    "type": "passthrough",
                    "data": {"label": "Node 1", "category": "trigger"}
                },
                {
                    "id": "node_2",
                    "type": "passthrough",
                    "data": {"label": "Node 2", "category": "transform"}
                }
            ],
            "edges": [
                {"source": "node_1", "target": "node_2"}
            ],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        assert len(result.node_results) == 2
        assert "node_1" in result.node_results
        assert "node_2" in result.node_results

    @pytest.mark.asyncio
    async def test_node_result_has_execution_time(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that node results include execution time."""
        playbook_data = {
            "nodes": [
                {
                    "id": "node_1",
                    "type": "passthrough",
                    "data": {"label": "Node 1", "category": "trigger"}
                }
            ],
            "edges": [],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        node_result = result.node_results["node_1"]
        assert node_result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execution_result_timestamps(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that node results have start and completion timestamps."""
        playbook_data = {
            "nodes": [
                {
                    "id": "node_1",
                    "type": "passthrough",
                    "data": {"label": "Node 1", "category": "trigger"}
                }
            ],
            "edges": [],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        node_result = result.node_results["node_1"]
        assert node_result.started_at is not None
        assert node_result.completed_at is not None
        assert node_result.started_at <= node_result.completed_at

    def test_execution_result_to_dict(self) -> None:
        """Test ExecutionResult serialization to dict."""
        node_result = NodeResult(
            node_id="node_1",
            status=NodeStatus.SUCCESS,
            outputs={"out": NodeData(data={"value": 42}, source_node_id="node_1")},
            execution_time_ms=100.5
        )

        result = ExecutionResult(
            success=True,
            node_results={"node_1": node_result},
            execution_time_ms=100.5,
            completed_nodes=["node_1"]
        )

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["execution_time_ms"] == 100.5
        assert "node_1" in result_dict["node_results"]
        assert result_dict["completed_nodes"] == ["node_1"]

    def test_node_result_to_dict(self) -> None:
        """Test NodeResult serialization to dict."""
        node_data = NodeData(
            data={"value": 42},
            metadata={"type": "number"},
            source_node_id="source",
            timestamp=datetime(2025, 1, 1, 12, 0, 0)
        )

        node_result = NodeResult(
            node_id="node_1",
            status=NodeStatus.SUCCESS,
            outputs={"output": node_data},
            execution_time_ms=50.0
        )

        result_dict = node_result.to_dict()

        assert result_dict["node_id"] == "node_1"
        assert result_dict["status"] == "success"
        assert "output" in result_dict["outputs"]
        assert result_dict["outputs"]["output"]["data"]["value"] == 42


class TestNodeContextCreation:
    """Test NodeContext creation during execution."""

    @pytest.mark.asyncio
    async def test_node_context_passed_to_node(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test that NodeContext is properly created and passed to nodes."""
        playbook_data = {
            "nodes": [
                {
                    "id": "test_node",
                    "type": "passthrough",
                    "config": {"timeout": 30},
                    "data": {"label": "Test", "category": "test"}
                }
            ],
            "edges": [],
            "trigger_output": {},
            "config": {"global_setting": "value"}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            # Create a mock node that captures its context
            captured_context = None

            class ContextCapturingNode(BaseNode):
                async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
                    nonlocal captured_context
                    captured_context = self.context
                    return {}

            mock_registry.get.return_value = ContextCapturingNode

            result = await playbook_executor.execute(playbook_data)

        assert captured_context is not None
        assert captured_context.execution_id == playbook_executor.execution_id
        assert captured_context.playbook_id == playbook_executor.playbook_id
        assert captured_context.node_id == "test_node"


class TestMultipleOutputHandles:
    """Test nodes with multiple output handles."""

    @pytest.mark.asyncio
    async def test_multiple_output_handles(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test executing nodes with multiple output handles."""
        class MultiOutputNode(BaseNode):
            async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
                """Return multiple outputs."""
                return {
                    "success": NodeData(data={"status": "ok"}, source_node_id=self.context.node_id),
                    "error": NodeData(data={"error": None}, source_node_id=self.context.node_id)
                }

        playbook_data = {
            "nodes": [
                {
                    "id": "multi",
                    "type": "multi_output",
                    "data": {"label": "Multi", "category": "transform"}
                }
            ],
            "edges": [],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = MultiOutputNode

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True
        assert len(result.node_results["multi"].outputs) == 2


class TestPassThroughNode:
    """Test PassThroughNode implementation."""

    @pytest.mark.asyncio
    async def test_passthrough_with_default_input(self) -> None:
        """Test PassThroughNode passes default input to output."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1"
        )

        node = PassThroughNode(context)
        inputs = {
            "default": NodeData(data={"value": 42}, source_node_id="upstream")
        }

        outputs = await node.execute(inputs)

        assert "default" in outputs
        assert outputs["default"].data["value"] == 42

    @pytest.mark.asyncio
    async def test_passthrough_with_no_default_returns_all_inputs(self) -> None:
        """Test PassThroughNode returns all inputs when no default."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1"
        )

        node = PassThroughNode(context)
        inputs = {
            "custom_1": NodeData(data={"a": 1}, source_node_id="upstream"),
            "custom_2": NodeData(data={"b": 2}, source_node_id="upstream")
        }

        outputs = await node.execute(inputs)

        assert "custom_1" in outputs
        assert "custom_2" in outputs

    @pytest.mark.asyncio
    async def test_passthrough_with_empty_inputs(self) -> None:
        """Test PassThroughNode handles empty inputs."""
        context = NodeContext(
            execution_id="exec-1",
            playbook_id="pb-1",
            node_id="node-1"
        )

        node = PassThroughNode(context)
        outputs = await node.execute({})

        assert outputs == {}


class TestComplexGraphs:
    """Test execution of complex playbook graphs."""

    @pytest.mark.asyncio
    async def test_diamond_graph_execution(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test execution of a diamond-shaped graph (splits and merges)."""
        playbook_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "left",
                    "type": "passthrough",
                    "data": {"label": "Left", "category": "transform"}
                },
                {
                    "id": "right",
                    "type": "passthrough",
                    "data": {"label": "Right", "category": "transform"}
                },
                {
                    "id": "end",
                    "type": "passthrough",
                    "data": {"label": "End", "category": "action"}
                }
            ],
            "edges": [
                {"source": "start", "target": "left"},
                {"source": "start", "target": "right"},
                {"source": "left", "target": "end"},
                {"source": "right", "target": "end"}
            ],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True
        assert len(result.completed_nodes) == 4

    @pytest.mark.asyncio
    async def test_multiple_execution_paths(
        self,
        playbook_executor: PlaybookExecutor
    ) -> None:
        """Test graph with multiple independent execution paths."""
        playbook_data = {
            "nodes": [
                {
                    "id": "start",
                    "type": "trigger",
                    "data": {"label": "Start", "category": "trigger"}
                },
                {
                    "id": "path1_node",
                    "type": "passthrough",
                    "data": {"label": "Path 1", "category": "transform"}
                },
                {
                    "id": "path2_node",
                    "type": "passthrough",
                    "data": {"label": "Path 2", "category": "transform"}
                }
            ],
            "edges": [
                {"source": "start", "target": "path1_node"},
                {"source": "start", "target": "path2_node"}
            ],
            "trigger_output": {},
            "config": {}
        }

        with patch('executor.playbook_executor.NodeRegistry') as mock_registry:
            mock_registry.get.return_value = PassThroughNode

            result = await playbook_executor.execute(playbook_data)

        assert result.success is True
        assert "path1_node" in result.completed_nodes
        assert "path2_node" in result.completed_nodes
