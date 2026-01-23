"""
Graph utilities for playbook execution ordering and analysis.

This module provides comprehensive graph analysis tools for IceStreams playbooks:
- Topological sorting for execution order determination
- Node relationship queries (upstream/downstream)
- Input/output mapping for data flow
- Graph validation and error detection

All functions are pure (no side effects) and thread-safe.
"""

from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GraphError(Exception):
    """Base exception for graph-related errors."""
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass(slots=True, frozen=True)
class CycleDetectedError(GraphError):
    """Raised when a cycle is detected in the graph."""
    cycle_nodes: Tuple[str, ...]

    def __str__(self) -> str:
        cycle_str = " -> ".join(self.cycle_nodes)
        return f"{self.message}: {cycle_str}"


class TopologicalSorter:
    """
    Topological sorting implementation using Kahn's algorithm.

    Handles:
    - Cycle detection with detailed error messages
    - Disconnected subgraphs
    - Multiple entry points (trigger nodes)

    Example:
        nodes = [{"id": "n1", "category": "triggers"}, {"id": "n2"}]
        edges = [{"source": "n1", "target": "n2"}]
        sorter = TopologicalSorter(nodes, edges)
        order = sorter.sort()  # Returns ["n1", "n2"]
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """
        Initialize the topological sorter.

        Args:
            nodes: List of node dictionaries with at least "id" field
            edges: List of edge dictionaries with "source" and "target" fields
        """
        self.nodes = nodes
        self.edges = edges
        self._node_ids = {node["id"] for node in nodes}
        self._adjacency_list = self._build_adjacency_list()
        self._in_degree = self._calculate_in_degree()

    def _build_adjacency_list(self) -> Dict[str, Set[str]]:
        """
        Build adjacency list representation of the graph.

        Returns:
            Dictionary mapping node_id to set of target node_ids
        """
        adj_list = defaultdict(set)

        # Initialize all nodes
        for node_id in self._node_ids:
            adj_list[node_id] = set()

        # Add edges
        for edge in self.edges:
            source = edge.get("source")
            target = edge.get("target")

            if source and target and source in self._node_ids and target in self._node_ids:
                adj_list[source].add(target)

        return dict(adj_list)

    def _calculate_in_degree(self) -> Dict[str, int]:
        """
        Calculate in-degree (number of incoming edges) for each node.

        Returns:
            Dictionary mapping node_id to in-degree count
        """
        in_degree = {node_id: 0 for node_id in self._node_ids}

        for edge in self.edges:
            target = edge.get("target")
            if target and target in self._node_ids:
                in_degree[target] += 1

        return in_degree

    def sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.

        Returns:
            List of node_ids in execution order

        Raises:
            CycleDetectedError: If graph contains cycles
        """
        # Create working copies
        in_degree = self._in_degree.copy()
        result = []

        # Queue starts with all nodes having in-degree 0
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])

        # Process nodes
        while queue:
            # Get node with no incoming edges
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for all neighbors
            for neighbor in self._adjacency_list.get(current, set()):
                in_degree[neighbor] -= 1

                # If neighbor now has no incoming edges, add to queue
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed
        if len(result) != len(self._node_ids):
            # Cycle detected - find remaining nodes
            remaining = [node_id for node_id in self._node_ids if node_id not in result]
            cycle = self._find_cycle(remaining)

            raise CycleDetectedError(
                message="Cycle detected in playbook graph",
                cycle_nodes=tuple(cycle)
            )

        return result

    def _find_cycle(self, remaining_nodes: List[str]) -> List[str]:
        """
        Find a cycle in the remaining nodes using DFS.

        Args:
            remaining_nodes: Nodes that couldn't be topologically sorted

        Returns:
            List of node_ids forming a cycle
        """
        visited = set()
        rec_stack = set()
        parent = {}

        def dfs(node: str) -> Optional[str]:
            """DFS to find cycle. Returns cycle start node if found."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._adjacency_list.get(node, set()):
                if neighbor not in remaining_nodes:
                    continue

                if neighbor not in visited:
                    parent[neighbor] = node
                    cycle_start = dfs(neighbor)
                    if cycle_start:
                        return cycle_start
                elif neighbor in rec_stack:
                    # Found cycle
                    parent[neighbor] = node
                    return neighbor

            rec_stack.remove(node)
            return None

        # Try DFS from each remaining node
        for node in remaining_nodes:
            if node not in visited:
                cycle_start = dfs(node)
                if cycle_start:
                    # Reconstruct cycle
                    cycle = [cycle_start]
                    current = parent[cycle_start]
                    while current != cycle_start:
                        cycle.append(current)
                        current = parent[current]
                    cycle.reverse()
                    return cycle

        # Shouldn't reach here, but return remaining nodes if we do
        return remaining_nodes


def get_upstream_nodes(node_id: str, edges: List[Dict]) -> List[str]:
    """
    Get all nodes that feed into the specified node.

    Args:
        node_id: Target node ID
        edges: List of edge dictionaries

    Returns:
        List of source node IDs that connect to this node

    Example:
        edges = [
            {"source": "n1", "target": "n3"},
            {"source": "n2", "target": "n3"}
        ]
        get_upstream_nodes("n3", edges)  # Returns ["n1", "n2"]
    """
    upstream = []

    for edge in edges:
        if edge.get("target") == node_id:
            source = edge.get("source")
            if source and source not in upstream:
                upstream.append(source)

    return upstream


def get_downstream_nodes(node_id: str, edges: List[Dict]) -> List[str]:
    """
    Get all nodes that this node feeds into.

    Args:
        node_id: Source node ID
        edges: List of edge dictionaries

    Returns:
        List of target node IDs that this node connects to

    Example:
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"}
        ]
        get_downstream_nodes("n1", edges)  # Returns ["n2", "n3"]
    """
    downstream = []

    for edge in edges:
        if edge.get("source") == node_id:
            target = edge.get("target")
            if target and target not in downstream:
                downstream.append(target)

    return downstream


def get_node_inputs(node_id: str, edges: List[Dict]) -> Dict[str, Tuple[str, str]]:
    """
    Get input mapping for a node.

    Returns mapping of target handles to their source information.
    Used to gather inputs from upstream node outputs.

    Args:
        node_id: Target node ID
        edges: List of edge dictionaries

    Returns:
        Dictionary mapping targetHandle to (source_node_id, sourceHandle)

    Example:
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n2", "targetHandle": "in"},
            {"source": "n3", "sourceHandle": "result", "target": "n2", "targetHandle": "param"}
        ]
        get_node_inputs("n2", edges)
        # Returns {"in": ("n1", "out"), "param": ("n3", "result")}
    """
    inputs = {}

    for edge in edges:
        if edge.get("target") == node_id:
            source = edge.get("source")
            source_handle = edge.get("sourceHandle", "out")
            target_handle = edge.get("targetHandle", "in")

            if source:
                inputs[target_handle] = (source, source_handle)

    return inputs


def get_node_outputs(node_id: str, edges: List[Dict]) -> Dict[str, List[Tuple[str, str]]]:
    """
    Get output routing for a node.

    Returns mapping of source handles to their target destinations.
    Used to route node outputs to downstream node inputs.

    Args:
        node_id: Source node ID
        edges: List of edge dictionaries

    Returns:
        Dictionary mapping sourceHandle to list of (target_node_id, targetHandle)

    Example:
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n2", "targetHandle": "in"},
            {"source": "n1", "sourceHandle": "out", "target": "n3", "targetHandle": "data"}
        ]
        get_node_outputs("n1", edges)
        # Returns {"out": [("n2", "in"), ("n3", "data")]}
    """
    outputs = defaultdict(list)

    for edge in edges:
        if edge.get("source") == node_id:
            target = edge.get("target")
            source_handle = edge.get("sourceHandle", "out")
            target_handle = edge.get("targetHandle", "in")

            if target:
                outputs[source_handle].append((target, target_handle))

    return dict(outputs)


def find_trigger_nodes(nodes: List[Dict]) -> List[str]:
    """
    Find all trigger nodes in the graph.

    Trigger nodes are entry points for playbook execution.
    They have category="triggers".

    Args:
        nodes: List of node dictionaries

    Returns:
        List of node IDs with category "triggers"

    Example:
        nodes = [
            {"id": "n1", "category": "triggers", "type": "interval"},
            {"id": "n2", "category": "actions"},
            {"id": "n3", "category": "triggers", "type": "webhook"}
        ]
        find_trigger_nodes(nodes)  # Returns ["n1", "n3"]
    """
    triggers = []

    for node in nodes:
        if node.get("category") == "triggers":
            node_id = node.get("id")
            if node_id:
                triggers.append(node_id)

    return triggers


def validate_graph(nodes: List[Dict], edges: List[Dict]) -> List[str]:
    """
    Validate graph structure and return any errors found.

    Checks for:
    - Orphan nodes (no incoming or outgoing edges)
    - Invalid edges (referencing non-existent nodes)
    - Missing node IDs
    - Cycles
    - Nodes without required fields

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        List of error messages (empty list if valid)

    Example:
        nodes = [{"id": "n1"}, {"id": "n2"}]
        edges = [{"source": "n1", "target": "n99"}]
        errors = validate_graph(nodes, edges)
        # Returns ["Invalid edge: source 'n1' -> target 'n99' (target node not found)"]
    """
    errors = []

    # Check for missing node IDs
    node_ids = set()
    for i, node in enumerate(nodes):
        node_id = node.get("id")
        if not node_id:
            errors.append(f"Node at index {i} is missing 'id' field")
        else:
            node_ids.add(node_id)

    # Check for duplicate node IDs
    if len(node_ids) != len(nodes):
        id_counts = defaultdict(int)
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                id_counts[node_id] += 1

        duplicates = [node_id for node_id, count in id_counts.items() if count > 1]
        for dup in duplicates:
            errors.append(f"Duplicate node ID found: '{dup}'")

    # Check for invalid edges
    edge_connections = set()
    for i, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")

        if not source:
            errors.append(f"Edge at index {i} is missing 'source' field")
            continue

        if not target:
            errors.append(f"Edge at index {i} is missing 'target' field")
            continue

        if source not in node_ids:
            errors.append(
                f"Invalid edge: source '{source}' -> target '{target}' "
                f"(source node not found)"
            )
            continue

        if target not in node_ids:
            errors.append(
                f"Invalid edge: source '{source}' -> target '{target}' "
                f"(target node not found)"
            )
            continue

        edge_connections.add(source)
        edge_connections.add(target)

    # Check for orphan nodes (excluding trigger nodes)
    trigger_ids = set(find_trigger_nodes(nodes))
    for node_id in node_ids:
        if node_id not in edge_connections and node_id not in trigger_ids:
            errors.append(
                f"Orphan node detected: '{node_id}' has no incoming or outgoing edges "
                f"and is not a trigger"
            )

    # Check for cycles (only if no other errors to avoid confusing messages)
    if not errors and node_ids:
        try:
            sorter = TopologicalSorter(nodes, edges)
            sorter.sort()
        except CycleDetectedError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Graph validation error: {str(e)}")

    return errors


def get_execution_paths(
    nodes: List[Dict],
    edges: List[Dict],
    from_node: str
) -> List[List[str]]:
    """
    Get all possible execution paths starting from a given node.

    Uses DFS to find all paths from the starting node to leaf nodes.
    Useful for understanding execution flow and debugging.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries
        from_node: Starting node ID

    Returns:
        List of paths, where each path is a list of node IDs

    Example:
        nodes = [{"id": "n1"}, {"id": "n2"}, {"id": "n3"}]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"}
        ]
        paths = get_execution_paths(nodes, edges, "n1")
        # Returns [["n1", "n2"], ["n1", "n3"]]
    """
    node_ids = {node["id"] for node in nodes}

    if from_node not in node_ids:
        return []

    adjacency = defaultdict(list)
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target:
            adjacency[source].append(target)

    all_paths = []

    def dfs(current: str, path: List[str], visited: Set[str]) -> None:
        """DFS to find all paths."""
        path.append(current)
        visited.add(current)

        neighbors = adjacency.get(current, [])

        if not neighbors:
            # Leaf node - save path
            all_paths.append(path.copy())
        else:
            # Continue exploration
            for neighbor in neighbors:
                if neighbor not in visited:
                    dfs(neighbor, path, visited.copy())

        path.pop()

    dfs(from_node, [], set())
    return all_paths


def get_graph_statistics(nodes: List[Dict], edges: List[Dict]) -> Dict[str, any]:
    """
    Get statistical information about the graph.

    Useful for monitoring, debugging, and optimization.

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        Dictionary containing graph statistics

    Example:
        stats = get_graph_statistics(nodes, edges)
        # Returns {
        #     "node_count": 10,
        #     "edge_count": 15,
        #     "trigger_count": 2,
        #     "avg_edges_per_node": 1.5,
        #     "max_depth": 5,
        #     "has_cycles": False
        # }
    """
    stats = {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "trigger_count": len(find_trigger_nodes(nodes)),
        "avg_edges_per_node": 0.0,
        "max_depth": 0,
        "has_cycles": False,
        "orphan_count": 0
    }

    if not nodes:
        return stats

    # Calculate average edges per node
    if len(nodes) > 0:
        stats["avg_edges_per_node"] = len(edges) / len(nodes)

    # Check for cycles
    try:
        sorter = TopologicalSorter(nodes, edges)
        sorted_nodes = sorter.sort()
        stats["has_cycles"] = False

        # Calculate max depth
        if sorted_nodes:
            node_depth = {}
            for node_id in sorted_nodes:
                upstream = get_upstream_nodes(node_id, edges)
                if not upstream:
                    node_depth[node_id] = 1
                else:
                    max_upstream_depth = max(node_depth.get(u, 0) for u in upstream)
                    node_depth[node_id] = max_upstream_depth + 1

            stats["max_depth"] = max(node_depth.values()) if node_depth else 0
    except CycleDetectedError:
        stats["has_cycles"] = True

    # Count orphan nodes
    validation_errors = validate_graph(nodes, edges)
    orphan_errors = [e for e in validation_errors if "Orphan node" in e]
    stats["orphan_count"] = len(orphan_errors)

    return stats
