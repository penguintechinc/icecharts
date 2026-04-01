#!/usr/bin/env python3
"""
Playbook Executor - Executes IceStreams workflow playbooks on workers.

This module provides the core execution engine for running playbook node graphs,
handling topological sorting, data flow between nodes, conditional branching,
and comprehensive error handling with detailed execution results.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

import redis.asyncio as aioredis

from .graph_utils import TopologicalSorter, get_node_inputs
from .node_registry import NodeRegistry

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Execution status for individual nodes."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class NodeContext:
    """
    Execution context provided to nodes during execution.

    Attributes:
        execution_id: Unique identifier for this execution
        playbook_id: Identifier of the playbook being executed
        node_id: Identifier of the current node
        config: Node-specific configuration
        global_config: Playbook-level configuration
        metadata: Additional metadata for tracking
    """

    execution_id: str
    playbook_id: str
    node_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    global_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NodeData:
    """
    Standard data transfer object for workflow nodes.

    This is the data structure passed between nodes in the workflow.

    Attributes:
        data: The main data payload
        metadata: Additional metadata associated with the data
        source_node_id: ID of the source node that created this data
        timestamp: UTC timestamp of when this NodeData was created
    """

    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_node_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class NodeResult:
    """
    Result of a single node execution.

    Attributes:
        node_id: Identifier of the executed node
        status: Execution status
        outputs: Output data for each handle (keyed by handle name)
        error: Error message if execution failed
        execution_time_ms: Time taken to execute the node in milliseconds
        started_at: Timestamp when node execution started
        completed_at: Timestamp when node execution completed
    """

    node_id: str
    status: NodeStatus
    outputs: Dict[str, NodeData] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert NodeResult to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "outputs": {
                k: {
                    "data": v.data,
                    "metadata": v.metadata,
                    "source_node_id": v.source_node_id,
                    "timestamp": v.timestamp.isoformat(),
                }
                for k, v in self.outputs.items()
            },
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }


@dataclass(slots=True)
class ExecutionResult:
    """
    Overall result of playbook execution.

    Attributes:
        success: Whether the execution completed successfully
        node_results: Results for each executed node (keyed by node_id)
        error: Overall error message if execution failed
        execution_time_ms: Total execution time in milliseconds
        completed_nodes: List of node IDs that completed successfully
        failed_nodes: List of node IDs that failed
        skipped_nodes: List of node IDs that were skipped
    """

    success: bool
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    completed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    skipped_nodes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExecutionResult to dictionary for serialization."""
        return {
            "success": self.success,
            "node_results": {k: v.to_dict() for k, v in self.node_results.items()},
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "skipped_nodes": self.skipped_nodes,
        }


class BaseNode:
    """
    Base class for all node implementations.

    All node types should inherit from this class and implement the execute method.
    """

    def __init__(self, context: NodeContext):
        """Initialize the node with execution context."""
        self.context = context

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """
        Execute the node with given inputs.

        Args:
            inputs: Input data from upstream nodes (keyed by handle name)

        Returns:
            Output data for downstream nodes (keyed by handle name)
        """
        raise NotImplementedError("Node must implement execute method")

    def validate_config(self) -> None:
        """
        Validate node configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class PlaybookExecutor:
    """
    Main executor for running playbook node graphs on workers.

    This executor:
    - Receives playbook data from Redis Stream
    - Executes nodes in topological order
    - Manages data flow between nodes
    - Handles conditional branching
    - Publishes execution status updates
    """

    DEFAULT_NODE_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        redis_client: aioredis.Redis,
        execution_id: str,
        playbook_id: str,
        node_timeout_seconds: float = DEFAULT_NODE_TIMEOUT_SECONDS,
    ):
        """
        Initialize the playbook executor.

        Args:
            redis_client: Redis client for status updates
            execution_id: Unique identifier for this execution
            playbook_id: Identifier of the playbook being executed
            node_timeout_seconds: Timeout for individual node execution
        """
        self.redis_client = redis_client
        self.execution_id = execution_id
        self.playbook_id = playbook_id
        self.node_timeout_seconds = node_timeout_seconds

        self._node_outputs: Dict[str, Dict[str, NodeData]] = {}
        self._execution_order: List[str] = []

        logger.info(
            f"PlaybookExecutor initialized: execution_id={execution_id}, "
            f"playbook_id={playbook_id}, timeout={node_timeout_seconds}s"
        )

    async def execute(self, playbook_data: Dict[str, Any]) -> ExecutionResult:
        """
        Execute the playbook with given data.

        Args:
            playbook_data: Dictionary containing:
                - nodes: List of node definitions
                - edges: List of edge connections
                - trigger_output: Initial data from trigger
                - config: Playbook-level configuration

        Returns:
            ExecutionResult with detailed execution information
        """
        start_time = time.time()
        logger.info(
            f"Starting playbook execution: execution_id={self.execution_id}, "
            f"playbook_id={self.playbook_id}"
        )

        try:
            # Extract playbook components
            nodes = playbook_data.get("nodes", [])
            edges = playbook_data.get("edges", [])
            trigger_output = playbook_data.get("trigger_output", {})
            global_config = playbook_data.get("config", {})

            if not nodes:
                return ExecutionResult(
                    success=False,
                    error="No nodes in playbook",
                    execution_time_ms=0.0,
                )

            # Build execution order using topological sort
            execution_order = self._get_execution_order(nodes, edges)
            self._execution_order = execution_order

            logger.info(f"Execution order: {execution_order}")

            # Initialize node outputs storage
            self._node_outputs = {}

            # Track results
            node_results: Dict[str, NodeResult] = {}
            completed_nodes: List[str] = []
            failed_nodes: List[str] = []
            skipped_nodes: List[str] = []

            # Create a mapping of nodes by ID for easy lookup
            nodes_by_id = {node["id"]: node for node in nodes}

            # Execute nodes in topological order
            for node_id in execution_order:
                node_data = nodes_by_id.get(node_id)
                if not node_data:
                    logger.error(f"Node {node_id} not found in nodes list")
                    continue

                # Gather inputs from upstream nodes
                inputs = self._gather_inputs(node_id, edges, self._node_outputs)

                # Execute the node
                result = await self._execute_node(
                    node_id, node_data, inputs, global_config
                )
                node_results[node_id] = result

                # Handle execution result
                if result.status == NodeStatus.SUCCESS:
                    completed_nodes.append(node_id)
                    # Store outputs for downstream nodes
                    self._route_outputs(node_id, result, edges)
                elif result.status == NodeStatus.FAILED:
                    failed_nodes.append(node_id)
                    # Stop execution on failure unless configured otherwise
                    if not global_config.get("continue_on_error", False):
                        logger.error(
                            f"Node {node_id} failed, stopping execution: {result.error}"
                        )
                        break
                elif result.status == NodeStatus.SKIPPED:
                    skipped_nodes.append(node_id)

            # Calculate overall execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Determine overall success
            success = len(failed_nodes) == 0 and len(completed_nodes) > 0

            result = ExecutionResult(
                success=success,
                node_results=node_results,
                error=(f"{len(failed_nodes)} node(s) failed" if failed_nodes else None),
                execution_time_ms=execution_time_ms,
                completed_nodes=completed_nodes,
                failed_nodes=failed_nodes,
                skipped_nodes=skipped_nodes,
            )

            logger.info(
                f"Playbook execution completed: success={success}, "
                f"completed={len(completed_nodes)}, failed={len(failed_nodes)}, "
                f"skipped={len(skipped_nodes)}, time={execution_time_ms:.2f}ms"
            )

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Playbook execution failed with exception: {e}", exc_info=True
            )
            return ExecutionResult(
                success=False,
                error=f"Execution failed: {str(e)}",
                execution_time_ms=execution_time_ms,
            )

    def _get_execution_order(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Compute topological execution order for nodes.

        Args:
            nodes: List of node definitions
            edges: List of edge connections

        Returns:
            List of node IDs in execution order

        Raises:
            ValueError: If graph has cycles
        """
        try:
            # Use TopologicalSorter from graph_utils for cycle detection
            sorter = TopologicalSorter(nodes, edges)
            execution_order = sorter.sort()
            logger.debug(f"Computed execution order: {execution_order}")
            return execution_order
        except Exception as e:
            logger.error(f"Error computing execution order: {e}")
            raise ValueError(f"Failed to compute execution order: {str(e)}")

    async def _execute_node(
        self,
        node_id: str,
        node_data: Dict[str, Any],
        inputs: Dict[str, NodeData],
        global_config: Dict[str, Any],
    ) -> NodeResult:
        """
        Execute a single node with timeout and error handling.

        Args:
            node_id: Node identifier
            node_data: Node definition data
            inputs: Input data from upstream nodes
            global_config: Playbook-level configuration

        Returns:
            NodeResult with execution details
        """
        started_at = datetime.now(UTC)
        start_time = time.time()

        logger.info(f"Executing node: {node_id} ({node_data.get('type', 'unknown')})")

        try:
            # Extract node configuration
            node_type = node_data.get("type") or node_data.get("data", {}).get(
                "nodeType", "unknown"
            )
            node_config = node_data.get("config", {})

            # Create node context
            context = NodeContext(
                execution_id=self.execution_id,
                playbook_id=self.playbook_id,
                node_id=node_id,
                config=node_config,
                global_config=global_config,
                metadata={
                    "label": node_data.get("data", {}).get("label", ""),
                    "category": node_data.get("data", {}).get("category", ""),
                },
            )

            # Get node implementation from registry
            node_class = NodeRegistry.get(node_type)
            if not node_class:
                logger.warning(
                    f"Node type '{node_type}' not registered, using PassThrough"
                )
                node_class = PassThroughNode

            # Instantiate node
            node_instance = node_class(context)

            # Validate configuration if available
            if hasattr(node_instance, "validate_config"):
                node_instance.validate_config()

            # Execute node with timeout
            try:
                outputs = await asyncio.wait_for(
                    node_instance.execute(inputs), timeout=self.node_timeout_seconds
                )
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Node execution exceeded timeout of {self.node_timeout_seconds}s"
                )

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(UTC)

            logger.info(
                f"Node {node_id} completed successfully in {execution_time_ms:.2f}ms"
            )

            return NodeResult(
                node_id=node_id,
                status=NodeStatus.SUCCESS,
                outputs=outputs,
                execution_time_ms=execution_time_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            completed_at = datetime.now(UTC)

            error_msg = f"Node execution failed: {str(e)}"
            logger.error(f"Node {node_id} failed: {error_msg}", exc_info=True)

            return NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=error_msg,
                execution_time_ms=execution_time_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

    def _gather_inputs(
        self,
        node_id: str,
        edges: List[Dict[str, Any]],
        node_outputs: Dict[str, Dict[str, NodeData]],
    ) -> Dict[str, NodeData]:
        """
        Gather input data for a node from upstream outputs.

        Args:
            node_id: Target node identifier
            edges: List of edge connections
            node_outputs: Stored outputs from executed nodes

        Returns:
            Dictionary of input data keyed by handle name
        """
        inputs: Dict[str, NodeData] = {}

        # Find all edges that connect to this node
        incoming_edges = [edge for edge in edges if edge.get("target") == node_id]

        for edge in incoming_edges:
            source_node_id = edge.get("source")
            source_handle = edge.get("sourceHandle", "default")
            target_handle = edge.get("targetHandle", "default")

            # Get output from source node
            if source_node_id in node_outputs:
                source_outputs = node_outputs[source_node_id]
                if source_handle in source_outputs:
                    inputs[target_handle] = source_outputs[source_handle]
                    logger.debug(
                        f"Gathered input for {node_id}[{target_handle}] "
                        f"from {source_node_id}[{source_handle}]"
                    )

        return inputs

    def _route_outputs(
        self,
        node_id: str,
        result: NodeResult,
        edges: List[Dict[str, Any]],
    ) -> None:
        """
        Store node outputs for downstream consumption.

        For conditional nodes, only outputs that have data are routed.

        Args:
            node_id: Source node identifier
            result: Node execution result containing outputs
            edges: List of edge connections
        """
        # Store all outputs from this node
        self._node_outputs[node_id] = result.outputs

        logger.debug(
            f"Routed {len(result.outputs)} output(s) from node {node_id}: "
            f"{list(result.outputs.keys())}"
        )


class PassThroughNode(BaseNode):
    """
    Default node implementation that passes input to output.

    This is used when a node type is not registered in the NodeRegistry.
    """

    async def execute(self, inputs: Dict[str, NodeData]) -> Dict[str, NodeData]:
        """Pass through inputs to outputs."""
        logger.debug(
            f"PassThrough node {self.context.node_id} executing with {len(inputs)} input(s)"
        )

        # If there's a default input, pass it to default output
        if "default" in inputs:
            return {"default": inputs["default"]}

        # Otherwise, return all inputs as outputs
        return inputs
