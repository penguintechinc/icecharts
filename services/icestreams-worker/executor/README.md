# IceStreams Worker Executor

Graph analysis and execution orchestration tools for IceStreams playbooks.

## Overview

The executor package provides comprehensive utilities for analyzing and executing IceStreams playbooks, which are stored as directed acyclic graphs (DAGs) of nodes and edges.

## Components

### Graph Utilities (`graph_utils.py`)

Core graph analysis functions for playbook execution ordering and validation.

#### TopologicalSorter

Determines execution order using Kahn's algorithm.

```python
from executor import TopologicalSorter

nodes = [
    {"id": "trigger", "category": "triggers"},
    {"id": "action", "category": "actions"}
]
edges = [
    {"source": "trigger", "target": "action"}
]

sorter = TopologicalSorter(nodes, edges)
execution_order = sorter.sort()  # ["trigger", "action"]
```

**Features:**
- Cycle detection with detailed error messages
- Handles disconnected subgraphs
- Multiple entry point support

#### Node Relationship Functions

**get_upstream_nodes(node_id, edges)**
Returns all nodes that feed into the specified node.

```python
upstream = get_upstream_nodes("my_node", edges)
# Returns: ["source1", "source2"]
```

**get_downstream_nodes(node_id, edges)**
Returns all nodes that this node feeds into.

```python
downstream = get_downstream_nodes("my_node", edges)
# Returns: ["target1", "target2"]
```

#### Input/Output Mapping

**get_node_inputs(node_id, edges)**
Returns mapping of target handles to their source information.

```python
inputs = get_node_inputs("my_node", edges)
# Returns: {"in": ("source_node", "out"), "param": ("param_node", "result")}
```

**get_node_outputs(node_id, edges)**
Returns mapping of source handles to their target destinations.

```python
outputs = get_node_outputs("my_node", edges)
# Returns: {"out": [("target1", "in"), ("target2", "data")]}
```

#### Graph Analysis

**find_trigger_nodes(nodes)**
Finds all trigger nodes (entry points) in the graph.

```python
triggers = find_trigger_nodes(nodes)
# Returns: ["trigger1", "trigger2"]
```

**validate_graph(nodes, edges)**
Validates graph structure and returns any errors found.

```python
errors = validate_graph(nodes, edges)
if errors:
    print(f"Validation failed: {errors}")
```

**Checks:**
- Missing node IDs
- Duplicate node IDs
- Invalid edge references
- Orphan nodes (excluding triggers)
- Cycles

**get_execution_paths(nodes, edges, from_node)**
Finds all possible execution paths from a starting node.

```python
paths = get_execution_paths(nodes, edges, "trigger")
# Returns: [["trigger", "branch1", "end"], ["trigger", "branch2", "end"]]
```

**get_graph_statistics(nodes, edges)**
Returns statistical information about the graph.

```python
stats = get_graph_statistics(nodes, edges)
# Returns: {
#     "node_count": 10,
#     "edge_count": 12,
#     "trigger_count": 2,
#     "avg_edges_per_node": 1.2,
#     "max_depth": 5,
#     "has_cycles": False,
#     "orphan_count": 0
# }
```

## Data Structures

### Node Format

```python
{
    "id": "unique_node_id",
    "category": "triggers|actions|logic",
    "type": "interval|webhook|http|condition|...",
    "data": {
        # Node-specific configuration
    }
}
```

### Edge Format

```python
{
    "source": "source_node_id",
    "sourceHandle": "out",  # Optional, defaults to "out"
    "target": "target_node_id",
    "targetHandle": "in"    # Optional, defaults to "in"
}
```

### Handle Types

Common handle identifiers:
- `"in"` - Default input
- `"out"` - Default output
- `"true"` - Condition true branch
- `"false"` - Condition false branch
- `"success"` - Success path
- `"error"` - Error path

## Usage Examples

### Simple Linear Playbook

```python
from executor import TopologicalSorter, validate_graph, find_trigger_nodes

nodes = [
    {"id": "trigger_1", "category": "triggers", "type": "interval"},
    {"id": "fetch_data", "category": "actions", "type": "http"},
    {"id": "log_result", "category": "actions", "type": "log"}
]

edges = [
    {"source": "trigger_1", "target": "fetch_data"},
    {"source": "fetch_data", "target": "log_result"}
]

# Validate
errors = validate_graph(nodes, edges)
if errors:
    raise ValueError(f"Invalid graph: {errors}")

# Get execution order
sorter = TopologicalSorter(nodes, edges)
order = sorter.sort()
print(order)  # ["trigger_1", "fetch_data", "log_result"]
```

### Conditional Branching

```python
nodes = [
    {"id": "trigger", "category": "triggers"},
    {"id": "check", "category": "logic", "type": "condition"},
    {"id": "handle_true", "category": "actions"},
    {"id": "handle_false", "category": "actions"}
]

edges = [
    {"source": "trigger", "target": "check"},
    {"source": "check", "sourceHandle": "true", "target": "handle_true"},
    {"source": "check", "sourceHandle": "false", "target": "handle_false"}
]

# Get possible execution paths
from executor import get_execution_paths

paths = get_execution_paths(nodes, edges, "trigger")
for path in paths:
    print(" -> ".join(path))

# Output:
# trigger -> check -> handle_true
# trigger -> check -> handle_false
```

### Parallel Execution

```python
nodes = [
    {"id": "trigger", "category": "triggers"},
    {"id": "task1", "category": "actions"},
    {"id": "task2", "category": "actions"},
    {"id": "join", "category": "logic", "type": "merge"}
]

edges = [
    {"source": "trigger", "target": "task1"},
    {"source": "trigger", "target": "task2"},
    {"source": "task1", "target": "join", "targetHandle": "input1"},
    {"source": "task2", "target": "join", "targetHandle": "input2"}
]

# Get execution order
sorter = TopologicalSorter(nodes, edges)
order = sorter.sort()

# task1 and task2 can execute in parallel
# They both come after trigger but before join
task1_idx = order.index("task1")
task2_idx = order.index("task2")
join_idx = order.index("join")

print(f"Parallel tasks at positions {task1_idx} and {task2_idx}")
```

## Error Handling

### Cycle Detection

```python
from executor import CycleDetectedError

try:
    sorter = TopologicalSorter(nodes, edges)
    order = sorter.sort()
except CycleDetectedError as e:
    print(f"Cycle detected: {e.cycle_nodes}")
    # Handle cycle error
```

### Graph Validation

```python
errors = validate_graph(nodes, edges)

for error in errors:
    if "Cycle detected" in error:
        # Handle cycle
        pass
    elif "Orphan node" in error:
        # Handle orphan node
        pass
    elif "Invalid edge" in error:
        # Handle invalid edge reference
        pass
```

## Performance Considerations

### Complexity

- **TopologicalSorter.sort()**: O(V + E) where V = nodes, E = edges
- **get_upstream_nodes()**: O(E)
- **get_downstream_nodes()**: O(E)
- **get_node_inputs()**: O(E)
- **get_node_outputs()**: O(E)
- **validate_graph()**: O(V + E)
- **get_execution_paths()**: O(V + E) per path (exponential for highly branched graphs)

### Optimization Tips

1. **Cache results**: If analyzing the same graph multiple times, cache results
2. **Validate once**: Run validation before execution, not during
3. **Limit path finding**: Use path finding for debugging only, not runtime
4. **Batch operations**: Group multiple node analyses together

## Testing

Comprehensive test suite available in `tests/test_graph_utils.py`.

Run tests:
```bash
cd /home/penguin/code/IceCharts/services/icestreams-worker
python3 -m pytest tests/test_graph_utils.py -v
```

Test coverage includes:
- Linear graphs
- Diamond-shaped graphs
- Disconnected components
- Cycle detection
- Self-loops
- Empty graphs
- Multiple entry points
- Invalid edges
- Orphan nodes
- Complex branching

## Examples

See `executor/example_usage.py` for complete working examples:

```bash
cd /home/penguin/code/IceCharts/services/icestreams-worker
PYTHONPATH=. python3 executor/example_usage.py
```

## Thread Safety

All functions are **pure** (no side effects) and **thread-safe**. The TopologicalSorter class creates working copies of data structures and does not modify the original nodes or edges.

## API Reference

### Classes

**TopologicalSorter(nodes, edges)**
- `sort() -> List[str]`: Returns node IDs in execution order

**GraphError(message)**
- Base exception for graph errors

**CycleDetectedError(message, cycle_nodes)**
- Raised when cycle is detected
- `cycle_nodes`: Tuple of node IDs forming the cycle

### Functions

**get_upstream_nodes(node_id: str, edges: List[Dict]) -> List[str]**
- Returns source node IDs feeding into this node

**get_downstream_nodes(node_id: str, edges: List[Dict]) -> List[str]**
- Returns target node IDs this node feeds into

**get_node_inputs(node_id: str, edges: List[Dict]) -> Dict[str, Tuple[str, str]]**
- Returns mapping: {targetHandle: (source_node_id, sourceHandle)}

**get_node_outputs(node_id: str, edges: List[Dict]) -> Dict[str, List[Tuple[str, str]]]**
- Returns mapping: {sourceHandle: [(target_node_id, targetHandle), ...]}

**find_trigger_nodes(nodes: List[Dict]) -> List[str]**
- Returns node IDs with category="triggers"

**validate_graph(nodes: List[Dict], edges: List[Dict]) -> List[str]**
- Returns list of validation error messages (empty if valid)

**get_execution_paths(nodes: List[Dict], edges: List[Dict], from_node: str) -> List[List[str]]**
- Returns all possible execution paths from starting node

**get_graph_statistics(nodes: List[Dict], edges: List[Dict]) -> Dict[str, any]**
- Returns statistical information about the graph

## Integration

The graph utilities are designed to integrate with:
- Worker execution engine
- Playbook validation service
- Frontend visualization
- Debugging and monitoring tools

## License

Part of IceCharts by Penguin Tech Inc.
