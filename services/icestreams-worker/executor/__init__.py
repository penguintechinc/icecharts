"""
Executor package for IceStreams playbook execution.

This package provides graph analysis, node registry, and execution orchestration tools.
"""

from .graph_utils import (
    TopologicalSorter,
    GraphError,
    CycleDetectedError,
    get_upstream_nodes,
    get_downstream_nodes,
    get_node_inputs,
    get_node_outputs,
    find_trigger_nodes,
    validate_graph,
    get_execution_paths,
    get_graph_statistics,
)

from .node_registry import (
    NodeRegistry,
    NodeInfo,
    NodeRegistryError,
    NodeNotFoundError,
    DuplicateNodeError,
    register_node,
    discover_nodes,
    get_registry_stats,
)

from .playbook_executor import (
    PlaybookExecutor,
    ExecutionResult,
    NodeResult,
    NodeContext,
    NodeData,
    NodeStatus,
    BaseNode,
    PassThroughNode,
)

__all__ = [
    # Graph utilities
    "TopologicalSorter",
    "GraphError",
    "CycleDetectedError",
    "get_upstream_nodes",
    "get_downstream_nodes",
    "get_node_inputs",
    "get_node_outputs",
    "find_trigger_nodes",
    "validate_graph",
    "get_execution_paths",
    "get_graph_statistics",
    # Node registry
    "NodeRegistry",
    "NodeInfo",
    "NodeRegistryError",
    "NodeNotFoundError",
    "DuplicateNodeError",
    "register_node",
    "discover_nodes",
    "get_registry_stats",
    # Playbook executor
    "PlaybookExecutor",
    "ExecutionResult",
    "NodeResult",
    "NodeContext",
    "NodeData",
    "NodeStatus",
    "BaseNode",
    "PassThroughNode",
]
