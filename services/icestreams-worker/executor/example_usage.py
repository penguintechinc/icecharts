"""
Example usage of graph utilities for playbook execution.

This demonstrates how to use the graph utilities to analyze and execute
IceStreams playbooks.
"""

from executor.graph_utils import (
    TopologicalSorter,
    get_node_inputs,
    get_node_outputs,
    find_trigger_nodes,
    validate_graph,
    get_execution_paths,
    get_graph_statistics,
)


def example_simple_playbook():
    """Example: Simple playbook with trigger -> action -> output."""
    print("\n=== Simple Playbook Example ===")

    nodes = [
        {"id": "trigger_1", "category": "triggers", "type": "interval"},
        {"id": "fetch_data", "category": "actions", "type": "http"},
        {"id": "log_result", "category": "actions", "type": "log"},
    ]

    edges = [
        {
            "source": "trigger_1",
            "sourceHandle": "out",
            "target": "fetch_data",
            "targetHandle": "in",
        },
        {
            "source": "fetch_data",
            "sourceHandle": "out",
            "target": "log_result",
            "targetHandle": "in",
        },
    ]

    # Validate graph
    errors = validate_graph(nodes, edges)
    if errors:
        print(f"Validation errors: {errors}")
        return

    print("Graph is valid!")

    # Find trigger nodes (entry points)
    triggers = find_trigger_nodes(nodes)
    print(f"Trigger nodes: {triggers}")

    # Get execution order
    sorter = TopologicalSorter(nodes, edges)
    execution_order = sorter.sort()
    print(f"Execution order: {execution_order}")

    # Get statistics
    stats = get_graph_statistics(nodes, edges)
    print(f"Graph stats: {stats}")


def example_conditional_playbook():
    """Example: Playbook with conditional branching."""
    print("\n=== Conditional Playbook Example ===")

    nodes = [
        {"id": "trigger_1", "category": "triggers", "type": "webhook"},
        {"id": "check_auth", "category": "logic", "type": "condition"},
        {"id": "process_request", "category": "actions", "type": "process"},
        {"id": "reject_request", "category": "actions", "type": "reject"},
        {"id": "log_success", "category": "actions", "type": "log"},
        {"id": "log_failure", "category": "actions", "type": "log"},
    ]

    edges = [
        # Trigger to auth check
        {
            "source": "trigger_1",
            "sourceHandle": "out",
            "target": "check_auth",
            "targetHandle": "in",
        },
        # Auth success path
        {
            "source": "check_auth",
            "sourceHandle": "true",
            "target": "process_request",
            "targetHandle": "in",
        },
        {
            "source": "process_request",
            "sourceHandle": "out",
            "target": "log_success",
            "targetHandle": "in",
        },
        # Auth failure path
        {
            "source": "check_auth",
            "sourceHandle": "false",
            "target": "reject_request",
            "targetHandle": "in",
        },
        {
            "source": "reject_request",
            "sourceHandle": "out",
            "target": "log_failure",
            "targetHandle": "in",
        },
    ]

    # Validate
    errors = validate_graph(nodes, edges)
    if errors:
        print(f"Validation errors: {errors}")
        return

    print("Graph is valid!")

    # Get execution order
    sorter = TopologicalSorter(nodes, edges)
    execution_order = sorter.sort()
    print(f"Execution order: {execution_order}")

    # Analyze node connections
    print(f"\nNode 'check_auth' inputs: {get_node_inputs('check_auth', edges)}")
    print(f"Node 'check_auth' outputs: {get_node_outputs('check_auth', edges)}")

    # Get all possible execution paths
    paths = get_execution_paths(nodes, edges, "trigger_1")
    print(f"\nPossible execution paths from trigger:")
    for i, path in enumerate(paths, 1):
        print(f"  Path {i}: {' -> '.join(path)}")


def example_invalid_playbook():
    """Example: Playbook with errors (cycle)."""
    print("\n=== Invalid Playbook Example (Cycle) ===")

    nodes = [
        {"id": "node_1", "category": "actions"},
        {"id": "node_2", "category": "actions"},
        {"id": "node_3", "category": "actions"},
    ]

    edges = [
        {"source": "node_1", "target": "node_2"},
        {"source": "node_2", "target": "node_3"},
        {"source": "node_3", "target": "node_1"},  # Creates cycle
    ]

    # Validate - should detect cycle
    errors = validate_graph(nodes, edges)
    if errors:
        print(f"Validation errors detected:")
        for error in errors:
            print(f"  - {error}")
        return

    print("Unexpected: Graph should have been invalid!")


def example_complex_playbook():
    """Example: Complex playbook with multiple paths and joins."""
    print("\n=== Complex Playbook Example ===")

    nodes = [
        {"id": "trigger_1", "category": "triggers", "type": "schedule"},
        {"id": "fetch_users", "category": "actions", "type": "database"},
        {"id": "fetch_orders", "category": "actions", "type": "database"},
        {"id": "join_data", "category": "logic", "type": "merge"},
        {"id": "transform", "category": "actions", "type": "transform"},
        {"id": "save_report", "category": "actions", "type": "database"},
    ]

    edges = [
        # Trigger starts two parallel fetches
        {
            "source": "trigger_1",
            "sourceHandle": "out",
            "target": "fetch_users",
            "targetHandle": "in",
        },
        {
            "source": "trigger_1",
            "sourceHandle": "out",
            "target": "fetch_orders",
            "targetHandle": "in",
        },
        # Both fetches feed into join
        {
            "source": "fetch_users",
            "sourceHandle": "out",
            "target": "join_data",
            "targetHandle": "users",
        },
        {
            "source": "fetch_orders",
            "sourceHandle": "out",
            "target": "join_data",
            "targetHandle": "orders",
        },
        # Join feeds into transform
        {
            "source": "join_data",
            "sourceHandle": "out",
            "target": "transform",
            "targetHandle": "in",
        },
        # Transform saves result
        {
            "source": "transform",
            "sourceHandle": "out",
            "target": "save_report",
            "targetHandle": "in",
        },
    ]

    # Validate
    errors = validate_graph(nodes, edges)
    if errors:
        print(f"Validation errors: {errors}")
        return

    print("Graph is valid!")

    # Get execution order
    sorter = TopologicalSorter(nodes, edges)
    execution_order = sorter.sort()
    print(f"Execution order: {execution_order}")

    # Note: fetch_users and fetch_orders can execute in parallel
    fetch_users_idx = execution_order.index("fetch_users")
    fetch_orders_idx = execution_order.index("fetch_orders")
    join_idx = execution_order.index("join_data")

    print(f"\nParallelization opportunity:")
    print(
        f"  'fetch_users' (position {fetch_users_idx}) and 'fetch_orders' (position {fetch_orders_idx})"
    )
    print(f"  can execute in parallel before 'join_data' (position {join_idx})")

    # Analyze join node inputs
    join_inputs = get_node_inputs("join_data", edges)
    print(f"\nJoin node inputs: {join_inputs}")

    # Get statistics
    stats = get_graph_statistics(nodes, edges)
    print(f"\nGraph statistics:")
    print(f"  Nodes: {stats['node_count']}")
    print(f"  Edges: {stats['edge_count']}")
    print(f"  Max depth: {stats['max_depth']}")
    print(f"  Avg edges/node: {stats['avg_edges_per_node']:.2f}")


if __name__ == "__main__":
    """Run all examples."""
    example_simple_playbook()
    example_conditional_playbook()
    example_invalid_playbook()
    example_complex_playbook()

    print("\n=== Examples Complete ===")
