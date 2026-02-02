"""
Unit tests for graph utilities.

Tests cover:
- Topological sorting with cycles and disconnected graphs
- Upstream/downstream node queries
- Input/output mapping
- Trigger node detection
- Graph validation
- Execution path analysis
- Graph statistics
"""

import pytest
from executor.graph_utils import (
    TopologicalSorter,
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


class TestTopologicalSorter:
    """Test TopologicalSorter class."""

    def test_simple_linear_graph(self):
        """Test sorting a simple linear graph."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]

        sorter = TopologicalSorter(nodes, edges)
        result = sorter.sort()

        assert result == ["n1", "n2", "n3"]

    def test_diamond_graph(self):
        """Test sorting a diamond-shaped graph."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"},
            {"source": "n2", "target": "n4"},
            {"source": "n3", "target": "n4"}
        ]

        sorter = TopologicalSorter(nodes, edges)
        result = sorter.sort()

        # n1 must be first, n4 must be last
        assert result[0] == "n1"
        assert result[3] == "n4"
        # n2 and n3 can be in any order
        assert set(result[1:3]) == {"n2", "n3"}

    def test_disconnected_graph(self):
        """Test sorting a graph with disconnected components."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n3", "target": "n4"}
        ]

        sorter = TopologicalSorter(nodes, edges)
        result = sorter.sort()

        # Should include all nodes
        assert len(result) == 4
        assert set(result) == {"n1", "n2", "n3", "n4"}

        # n1 before n2, n3 before n4
        assert result.index("n1") < result.index("n2")
        assert result.index("n3") < result.index("n4")

    def test_cycle_detection(self):
        """Test that cycles are detected and reported."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n1"}
        ]

        sorter = TopologicalSorter(nodes, edges)

        with pytest.raises(CycleDetectedError) as exc_info:
            sorter.sort()

        assert "Cycle detected" in str(exc_info.value)
        # Should report the cycle nodes
        assert len(exc_info.value.cycle_nodes) > 0

    def test_self_loop(self):
        """Test detection of self-loop (node pointing to itself)."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n2"}
        ]

        sorter = TopologicalSorter(nodes, edges)

        with pytest.raises(CycleDetectedError):
            sorter.sort()

    def test_empty_graph(self):
        """Test sorting an empty graph."""
        sorter = TopologicalSorter([], [])
        result = sorter.sort()
        assert result == []

    def test_single_node(self):
        """Test sorting a graph with single node."""
        nodes = [{"id": "n1"}]
        edges = []

        sorter = TopologicalSorter(nodes, edges)
        result = sorter.sort()

        assert result == ["n1"]

    def test_multiple_entry_points(self):
        """Test graph with multiple nodes having no incoming edges."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n3"},
            {"source": "n2", "target": "n4"}
        ]

        sorter = TopologicalSorter(nodes, edges)
        result = sorter.sort()

        assert len(result) == 4
        # n1 and n2 should come before n3 and n4
        assert result.index("n1") < result.index("n3")
        assert result.index("n2") < result.index("n4")


class TestGetUpstreamNodes:
    """Test get_upstream_nodes function."""

    def test_single_upstream(self):
        """Test node with single upstream connection."""
        edges = [{"source": "n1", "target": "n2"}]
        result = get_upstream_nodes("n2", edges)
        assert result == ["n1"]

    def test_multiple_upstream(self):
        """Test node with multiple upstream connections."""
        edges = [
            {"source": "n1", "target": "n3"},
            {"source": "n2", "target": "n3"}
        ]
        result = get_upstream_nodes("n3", edges)
        assert set(result) == {"n1", "n2"}

    def test_no_upstream(self):
        """Test node with no upstream connections."""
        edges = [{"source": "n1", "target": "n2"}]
        result = get_upstream_nodes("n1", edges)
        assert result == []

    def test_empty_edges(self):
        """Test with empty edge list."""
        result = get_upstream_nodes("n1", [])
        assert result == []


class TestGetDownstreamNodes:
    """Test get_downstream_nodes function."""

    def test_single_downstream(self):
        """Test node with single downstream connection."""
        edges = [{"source": "n1", "target": "n2"}]
        result = get_downstream_nodes("n1", edges)
        assert result == ["n2"]

    def test_multiple_downstream(self):
        """Test node with multiple downstream connections."""
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"}
        ]
        result = get_downstream_nodes("n1", edges)
        assert set(result) == {"n2", "n3"}

    def test_no_downstream(self):
        """Test node with no downstream connections."""
        edges = [{"source": "n1", "target": "n2"}]
        result = get_downstream_nodes("n2", edges)
        assert result == []

    def test_empty_edges(self):
        """Test with empty edge list."""
        result = get_downstream_nodes("n1", [])
        assert result == []


class TestGetNodeInputs:
    """Test get_node_inputs function."""

    def test_single_input(self):
        """Test node with single input."""
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n2", "targetHandle": "in"}
        ]
        result = get_node_inputs("n2", edges)
        assert result == {"in": ("n1", "out")}

    def test_multiple_inputs(self):
        """Test node with multiple inputs."""
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n3", "targetHandle": "in1"},
            {"source": "n2", "sourceHandle": "result", "target": "n3", "targetHandle": "in2"}
        ]
        result = get_node_inputs("n3", edges)
        assert result == {
            "in1": ("n1", "out"),
            "in2": ("n2", "result")
        }

    def test_default_handles(self):
        """Test that default handles are used when not specified."""
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        result = get_node_inputs("n2", edges)
        assert result == {"in": ("n1", "out")}

    def test_no_inputs(self):
        """Test node with no inputs."""
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        result = get_node_inputs("n1", edges)
        assert result == {}


class TestGetNodeOutputs:
    """Test get_node_outputs function."""

    def test_single_output(self):
        """Test node with single output."""
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n2", "targetHandle": "in"}
        ]
        result = get_node_outputs("n1", edges)
        assert result == {"out": [("n2", "in")]}

    def test_multiple_outputs_same_handle(self):
        """Test node with multiple connections from same handle."""
        edges = [
            {"source": "n1", "sourceHandle": "out", "target": "n2", "targetHandle": "in"},
            {"source": "n1", "sourceHandle": "out", "target": "n3", "targetHandle": "data"}
        ]
        result = get_node_outputs("n1", edges)
        assert "out" in result
        assert set(result["out"]) == {("n2", "in"), ("n3", "data")}

    def test_multiple_handles(self):
        """Test node with multiple output handles."""
        edges = [
            {"source": "n1", "sourceHandle": "true", "target": "n2", "targetHandle": "in"},
            {"source": "n1", "sourceHandle": "false", "target": "n3", "targetHandle": "in"}
        ]
        result = get_node_outputs("n1", edges)
        assert result == {
            "true": [("n2", "in")],
            "false": [("n3", "in")]
        }

    def test_no_outputs(self):
        """Test node with no outputs."""
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        result = get_node_outputs("n2", edges)
        assert result == {}


class TestFindTriggerNodes:
    """Test find_trigger_nodes function."""

    def test_single_trigger(self):
        """Test finding single trigger node."""
        nodes = [
            {"id": "n1", "category": "triggers"},
            {"id": "n2", "category": "actions"}
        ]
        result = find_trigger_nodes(nodes)
        assert result == ["n1"]

    def test_multiple_triggers(self):
        """Test finding multiple trigger nodes."""
        nodes = [
            {"id": "n1", "category": "triggers"},
            {"id": "n2", "category": "actions"},
            {"id": "n3", "category": "triggers"}
        ]
        result = find_trigger_nodes(nodes)
        assert set(result) == {"n1", "n3"}

    def test_no_triggers(self):
        """Test when no trigger nodes exist."""
        nodes = [
            {"id": "n1", "category": "actions"},
            {"id": "n2", "category": "logic"}
        ]
        result = find_trigger_nodes(nodes)
        assert result == []

    def test_empty_nodes(self):
        """Test with empty node list."""
        result = find_trigger_nodes([])
        assert result == []


class TestValidateGraph:
    """Test validate_graph function."""

    def test_valid_graph(self):
        """Test validation of a valid graph."""
        nodes = [
            {"id": "n1", "category": "triggers"},
            {"id": "n2", "category": "actions"}
        ]
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        errors = validate_graph(nodes, edges)
        assert errors == []

    def test_missing_node_id(self):
        """Test detection of missing node ID."""
        nodes = [
            {"category": "triggers"},
            {"id": "n2"}
        ]
        edges = []
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("missing 'id' field" in e for e in errors)

    def test_duplicate_node_ids(self):
        """Test detection of duplicate node IDs."""
        nodes = [
            {"id": "n1"},
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = []
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("Duplicate node ID" in e for e in errors)

    def test_invalid_edge_source(self):
        """Test detection of edge with non-existent source."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n99", "target": "n2"}
        ]
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("source node not found" in e for e in errors)

    def test_invalid_edge_target(self):
        """Test detection of edge with non-existent target."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n1", "target": "n99"}
        ]
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("target node not found" in e for e in errors)

    def test_orphan_node(self):
        """Test detection of orphan nodes."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("Orphan node" in e and "n3" in e for e in errors)

    def test_orphan_node_trigger_excluded(self):
        """Test that trigger nodes are not reported as orphans."""
        nodes = [
            {"id": "n1", "category": "triggers"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        errors = validate_graph(nodes, edges)
        # n1 is a trigger with outgoing edge, should be valid
        # n2 has incoming edge, should be valid
        assert errors == []

    def test_cycle_detection_in_validation(self):
        """Test that cycles are detected during validation."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n1"}
        ]
        errors = validate_graph(nodes, edges)
        assert len(errors) > 0
        assert any("Cycle detected" in e for e in errors)


class TestGetExecutionPaths:
    """Test get_execution_paths function."""

    def test_single_path(self):
        """Test finding single linear path."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
        paths = get_execution_paths(nodes, edges, "n1")
        assert paths == [["n1", "n2", "n3"]]

    def test_multiple_paths(self):
        """Test finding multiple paths from branch."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"}
        ]
        paths = get_execution_paths(nodes, edges, "n1")
        assert len(paths) == 2
        path_sets = [set(p) for p in paths]
        assert {"n1", "n2"} in path_sets
        assert {"n1", "n3"} in path_sets

    def test_diamond_paths(self):
        """Test paths in diamond-shaped graph."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n1", "target": "n3"},
            {"source": "n2", "target": "n4"},
            {"source": "n3", "target": "n4"}
        ]
        paths = get_execution_paths(nodes, edges, "n1")
        assert len(paths) == 2
        # Both paths should start with n1 and end with n4
        for path in paths:
            assert path[0] == "n1"
            assert path[-1] == "n4"

    def test_leaf_node_path(self):
        """Test path from leaf node (no outgoing edges)."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        paths = get_execution_paths(nodes, edges, "n2")
        assert paths == [["n2"]]

    def test_invalid_start_node(self):
        """Test with non-existent start node."""
        nodes = [{"id": "n1"}]
        edges = []
        paths = get_execution_paths(nodes, edges, "n99")
        assert paths == []


class TestGetGraphStatistics:
    """Test get_graph_statistics function."""

    def test_empty_graph_stats(self):
        """Test statistics for empty graph."""
        stats = get_graph_statistics([], [])
        assert stats["node_count"] == 0
        assert stats["edge_count"] == 0
        assert stats["trigger_count"] == 0

    def test_basic_stats(self):
        """Test basic statistics calculation."""
        nodes = [
            {"id": "n1", "category": "triggers"},
            {"id": "n2"},
            {"id": "n3"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
        stats = get_graph_statistics(nodes, edges)

        assert stats["node_count"] == 3
        assert stats["edge_count"] == 2
        assert stats["trigger_count"] == 1
        assert stats["avg_edges_per_node"] == pytest.approx(2/3)
        assert stats["has_cycles"] is False

    def test_max_depth_calculation(self):
        """Test maximum depth calculation."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"}
        ]
        stats = get_graph_statistics(nodes, edges)
        assert stats["max_depth"] == 4

    def test_cycle_detection_in_stats(self):
        """Test that cycles are detected in statistics."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"}
        ]
        edges = [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n1"}
        ]
        stats = get_graph_statistics(nodes, edges)
        assert stats["has_cycles"] is True

    def test_orphan_count(self):
        """Test orphan node counting."""
        nodes = [
            {"id": "n1"},
            {"id": "n2"},
            {"id": "n3"},
            {"id": "n4"}
        ]
        edges = [
            {"source": "n1", "target": "n2"}
        ]
        stats = get_graph_statistics(nodes, edges)
        # n3 and n4 are orphans
        assert stats["orphan_count"] == 2
