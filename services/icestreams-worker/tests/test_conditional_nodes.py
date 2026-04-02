#!/usr/bin/env python3
"""
Tests for conditional nodes in nodes/conditionals/.

Tests cover:
- IfThenConditional: true/false branches, AND/OR logic, operators
- SwitchConditional: case matching, default fallback
- ForEachConditional: iterate/empty array
- WhileConditional: condition evaluation, max iterations safety
- AndConditional: all truthy -> true
- OrConditional: any truthy -> true
- NotConditional: invert boolean
- Missing required input handling
- All nodes return NodeResult
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor.node_registry import NodeRegistry
from nodes.base import NodeContext, NodeResult


@pytest.fixture(autouse=True)
def clean_node_registry():
    """Clear NodeRegistry before/after each test."""
    NodeRegistry.clear()
    yield
    NodeRegistry.clear()


def _make_context(
    config: dict = None, variables: dict = None, node_id: str = "test-node"
) -> NodeContext:
    """Create a test NodeContext."""
    return NodeContext(
        execution_id="test-exec-001",
        playbook_id="test-playbook",
        node_id=node_id,
        config=config or {},
        variables=variables or {},
    )


class TestIfThenConditional:
    """Tests for IfThenConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.if_then import IfThenConditional

        self.node_class = IfThenConditional
        self.node = IfThenConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_if_then"

    def test_category_is_conditionals(self):
        assert self.node_class.category == "conditionals"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_single_input_in(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "in" in names

    @pytest.mark.asyncio
    async def test_condition_true_routes_to_true_output(self):
        """When condition matches, data goes to 'true' output."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"status": "active"}})
        assert isinstance(result, NodeResult)
        assert result.success is True
        assert result.outputs["true"] is not None
        assert result.outputs["false"] is None

    @pytest.mark.asyncio
    async def test_condition_false_routes_to_false_output(self):
        """When condition doesn't match, data goes to 'false' output."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"status": "inactive"}})
        assert result.success is True
        assert result.outputs["true"] is None
        assert result.outputs["false"] is not None

    @pytest.mark.asyncio
    async def test_and_logic_all_conditions_must_match(self):
        """AND logic: all conditions must match for true branch."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "age", "operator": "gte", "value": 18},
                    {"field": "active", "operator": "eq", "value": True},
                ],
                "logic": "and",
            }
        )
        # Both match
        result = await self.node.execute(ctx, {"in": {"age": 25, "active": True}})
        assert result.outputs["true"] is not None

        # Only one matches - must go false
        result2 = await self.node.execute(ctx, {"in": {"age": 16, "active": True}})
        assert result2.outputs["false"] is not None

    @pytest.mark.asyncio
    async def test_or_logic_any_condition_matches(self):
        """OR logic: any single condition matching sends to true branch."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "role", "operator": "eq", "value": "admin"},
                    {"field": "role", "operator": "eq", "value": "superuser"},
                ],
                "logic": "or",
            }
        )
        result = await self.node.execute(ctx, {"in": {"role": "superuser"}})
        assert result.outputs["true"] is not None

    @pytest.mark.asyncio
    async def test_contains_operator(self):
        """contains operator must check substring membership."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "name", "operator": "contains", "value": "Alice"}
                ],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"name": "Alice Smith"}})
        assert result.outputs["true"] is not None

    @pytest.mark.asyncio
    async def test_gt_operator(self):
        """gt operator must route to true when field > value."""
        ctx = _make_context(
            config={
                "conditions": [{"field": "score", "operator": "gt", "value": 50}],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"score": 75}})
        assert result.outputs["true"] is not None

        result2 = await self.node.execute(ctx, {"in": {"score": 25}})
        assert result2.outputs["false"] is not None

    @pytest.mark.asyncio
    async def test_ne_operator(self):
        """ne (not equal) operator must work correctly."""
        ctx = _make_context(
            config={
                "conditions": [{"field": "type", "operator": "ne", "value": "deleted"}],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"type": "active"}})
        assert result.outputs["true"] is not None

    @pytest.mark.asyncio
    async def test_missing_in_input_returns_failure(self):
        """Missing required 'in' input must return failure."""
        ctx = _make_context(
            config={
                "conditions": [{"field": "x", "operator": "eq", "value": 1}],
            }
        )
        result = await self.node.execute(ctx, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_empty_conditions_default_to_true(self):
        """No conditions configured means data always routes to true."""
        ctx = _make_context(config={"conditions": [], "logic": "and"})
        result = await self.node.execute(ctx, {"in": {"any": "data"}})
        assert result.success is True
        assert result.outputs["true"] is not None

    def test_validate_config_valid(self):
        errors = self.node_class.validate_config(
            {
                "conditions": [{"field": "x", "operator": "eq", "value": 1}],
                "logic": "and",
            }
        )
        assert errors == []

    def test_validate_config_no_conditions(self):
        errors = self.node_class.validate_config({"conditions": [], "logic": "and"})
        assert any("condition" in e.lower() for e in errors)

    def test_validate_config_invalid_operator(self):
        errors = self.node_class.validate_config(
            {
                "conditions": [{"field": "x", "operator": "INVALID_OP", "value": 1}],
                "logic": "and",
            }
        )
        assert len(errors) > 0


class TestSwitchConditional:
    """Tests for SwitchConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.switch import SwitchConditional

        self.node_class = SwitchConditional
        self.node = SwitchConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_switch"

    def test_has_case_and_default_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "case1" in names
        assert "case2" in names
        assert "default" in names

    @pytest.mark.asyncio
    async def test_matching_case_receives_data(self):
        """Data must route to the matching case output."""
        ctx = _make_context(
            config={
                "field": "color",
                "cases": [
                    {"value": "red", "output": "case1"},
                    {"value": "blue", "output": "case2"},
                ],
            }
        )
        result = await self.node.execute(ctx, {"in": {"color": "red"}})
        assert result.success is True
        assert result.outputs["case1"] is not None
        assert result.outputs["case2"] is None

    @pytest.mark.asyncio
    async def test_no_match_routes_to_default(self):
        """Unmatched value must route to default output."""
        ctx = _make_context(
            config={
                "field": "color",
                "cases": [
                    {"value": "red", "output": "case1"},
                ],
            }
        )
        result = await self.node.execute(ctx, {"in": {"color": "green"}})
        assert result.success is True
        assert result.outputs["default"] is not None
        assert result.outputs["case1"] is None

    @pytest.mark.asyncio
    async def test_case2_routing(self):
        """Value matching case2 must route data there."""
        ctx = _make_context(
            config={
                "field": "priority",
                "cases": [
                    {"value": "low", "output": "case1"},
                    {"value": "medium", "output": "case2"},
                    {"value": "high", "output": "case3"},
                ],
            }
        )
        result = await self.node.execute(ctx, {"in": {"priority": "medium"}})
        assert result.outputs["case2"] is not None
        assert result.outputs["case1"] is None
        assert result.outputs["case3"] is None

    @pytest.mark.asyncio
    async def test_nested_field_routing(self):
        """Dot-notation field paths must resolve for case matching."""
        ctx = _make_context(
            config={
                "field": "user.role",
                "cases": [{"value": "admin", "output": "case1"}],
            }
        )
        result = await self.node.execute(ctx, {"in": {"user": {"role": "admin"}}})
        assert result.outputs["case1"] is not None

    @pytest.mark.asyncio
    async def test_missing_in_input_returns_failure(self):
        """Missing required 'in' input must return failure."""
        ctx = _make_context(
            config={
                "field": "x",
                "cases": [{"value": "y", "output": "case1"}],
            }
        )
        result = await self.node.execute(ctx, {})
        assert result.success is False

    def test_validate_config_valid(self):
        errors = self.node_class.validate_config(
            {
                "field": "status",
                "cases": [{"value": "ok", "output": "case1"}],
            }
        )
        assert errors == []

    def test_validate_config_missing_field(self):
        errors = self.node_class.validate_config(
            {
                "cases": [{"value": "ok", "output": "case1"}],
            }
        )
        assert len(errors) > 0

    def test_validate_config_missing_cases(self):
        errors = self.node_class.validate_config({"field": "status", "cases": []})
        assert len(errors) > 0


class TestForEachConditional:
    """Tests for ForEachConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.for_each import ForEachConditional

        self.node_class = ForEachConditional
        self.node = ForEachConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_for_each"

    def test_has_item_index_done_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "item" in names
        assert "index" in names
        assert "done" in names

    @pytest.mark.asyncio
    async def test_iterate_list_returns_first_item(self):
        """ForEach with a list must return first item and index=0."""
        ctx = _make_context(config={})
        items = ["a", "b", "c"]
        result = await self.node.execute(ctx, {"array": items})
        assert result.success is True
        assert result.outputs["item"] == "a"
        assert result.outputs["index"] == 0
        assert result.outputs["done"] is False

    @pytest.mark.asyncio
    async def test_empty_array_returns_done_true(self):
        """Empty array must immediately set done=True."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"array": []})
        assert result.success is True
        assert result.outputs["done"] is True
        assert result.outputs["item"] is None

    @pytest.mark.asyncio
    async def test_iterations_stored_in_outputs(self):
        """All items must be stored in _iterations for executor use."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"array": [1, 2, 3]})
        assert "_iterations" in result.outputs
        assert result.outputs["_iterations"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_field_extraction_from_items(self):
        """When field is configured, must extract field from each item."""
        ctx = _make_context(config={"field": "name"})
        items = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = await self.node.execute(ctx, {"array": items})
        assert result.success is True
        assert result.outputs["_iterations"] == ["Alice", "Bob"]

    @pytest.mark.asyncio
    async def test_single_non_list_wrapped_in_array(self):
        """Non-list input should be wrapped in array."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"array": "single"})
        assert result.success is True
        assert result.outputs["item"] == "single"

    @pytest.mark.asyncio
    async def test_missing_required_array_input_returns_failure(self):
        """Missing required 'array' input must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {})
        assert result.success is False


class TestWhileConditional:
    """Tests for WhileConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.while_loop import WhileConditional

        self.node_class = WhileConditional
        self.node = WhileConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_while"

    def test_has_loop_and_done_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "loop" in names
        assert "done" in names

    @pytest.mark.asyncio
    async def test_condition_true_returns_loop_output(self):
        """When condition is true, data goes to 'loop' output."""
        ctx = _make_context(
            config={
                "condition": {"field": "count", "operator": "lt", "value": 10},
                "maxIterations": 100,
            }
        )
        result = await self.node.execute(ctx, {"in": {"count": 5}})
        assert result.success is True
        assert "loop" in result.outputs
        assert result.outputs["loop"] is not None

    @pytest.mark.asyncio
    async def test_condition_false_returns_done_output(self):
        """When condition is false, data goes to 'done' output."""
        ctx = _make_context(
            config={
                "condition": {"field": "count", "operator": "lt", "value": 10},
                "maxIterations": 100,
            }
        )
        result = await self.node.execute(ctx, {"in": {"count": 15}})
        assert result.success is True
        assert "done" in result.outputs
        assert result.outputs["done"] is not None

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded_returns_done(self):
        """When iteration count reaches max, must route to done."""
        iteration_key = "_while_iterations_test-node"
        ctx = _make_context(
            config={
                "condition": {"field": "x", "operator": "eq", "value": True},
                "maxIterations": 5,
            },
            variables={iteration_key: 5},  # At max
        )
        result = await self.node.execute(ctx, {"in": {"x": True}})
        assert result.success is True
        assert result.outputs.get("done") is not None

    @pytest.mark.asyncio
    async def test_non_dict_input_continues_looping(self):
        """Non-dict input always continues loop (condition meets True)."""
        ctx = _make_context(
            config={
                "condition": {"field": "x", "operator": "eq", "value": "y"},
                "maxIterations": 100,
            }
        )
        result = await self.node.execute(ctx, {"in": "simple_string"})
        assert result.success is True
        # Non-dict always continues
        assert result.outputs.get("loop") is not None

    @pytest.mark.asyncio
    async def test_missing_in_input_returns_failure(self):
        """Missing required 'in' input must return failure."""
        ctx = _make_context(
            config={
                "condition": {"field": "x", "operator": "eq", "value": 1},
            }
        )
        result = await self.node.execute(ctx, {})
        assert result.success is False

    def test_validate_config_valid(self):
        errors = self.node_class.validate_config(
            {
                "condition": {"field": "count", "operator": "lt", "value": 100},
                "maxIterations": 50,
            }
        )
        assert errors == []

    def test_validate_config_missing_condition_field(self):
        errors = self.node_class.validate_config(
            {
                "condition": {"operator": "eq", "value": 1},
            }
        )
        assert len(errors) > 0

    def test_validate_config_zero_max_iterations(self):
        errors = self.node_class.validate_config(
            {
                "condition": {"field": "x", "operator": "eq", "value": 1},
                "maxIterations": 0,
            }
        )
        assert len(errors) > 0


class TestAndGate:
    """Tests for AndConditional (AND Gate)."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.logic_gates import AndConditional

        self.node_class = AndConditional
        self.node = AndConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_and"

    def test_has_true_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    @pytest.mark.asyncio
    async def test_all_truthy_returns_true(self):
        """When all inputs are truthy, 'true' output must be True."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": True, "in2": True})
        assert result.success is True
        assert result.outputs["true"] is True
        assert result.outputs["false"] is False

    @pytest.mark.asyncio
    async def test_any_falsy_returns_false(self):
        """When any input is falsy, 'true' output must be False."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": True, "in2": False})
        assert result.success is True
        assert result.outputs["true"] is False
        assert result.outputs["false"] is True

    @pytest.mark.asyncio
    async def test_with_three_inputs(self):
        """AND gate works with three inputs."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": True, "in2": True, "in3": True})
        assert result.outputs["true"] is True

        result2 = await self.node.execute(ctx, {"in1": True, "in2": True, "in3": False})
        assert result2.outputs["true"] is False

    @pytest.mark.asyncio
    async def test_missing_required_in1_returns_failure(self):
        """Missing required in1 must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in2": True})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_truthy_values_coerced(self):
        """Non-zero/non-empty values should be treated as truthy."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": 1, "in2": "non-empty"})
        assert result.outputs["true"] is True


class TestOrGate:
    """Tests for OrConditional (OR Gate)."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.logic_gates import OrConditional

        self.node_class = OrConditional
        self.node = OrConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_or"

    @pytest.mark.asyncio
    async def test_any_truthy_returns_true(self):
        """When any input is truthy, 'true' output must be True."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": False, "in2": True})
        assert result.success is True
        assert result.outputs["true"] is True
        assert result.outputs["false"] is False

    @pytest.mark.asyncio
    async def test_all_falsy_returns_false(self):
        """When all inputs are falsy, 'true' output must be False."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in1": False, "in2": False})
        assert result.success is True
        assert result.outputs["true"] is False
        assert result.outputs["false"] is True

    @pytest.mark.asyncio
    async def test_missing_required_in1_returns_failure(self):
        """Missing required in1 must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in2": True})
        assert result.success is False


class TestNotGate:
    """Tests for NotConditional (NOT Gate)."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.logic_gates import NotConditional

        self.node_class = NotConditional
        self.node = NotConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_not"

    def test_has_true_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    @pytest.mark.asyncio
    async def test_truthy_input_becomes_false(self):
        """Truthy input must produce 'true'=False output."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": True})
        assert result.success is True
        assert result.outputs["true"] is False
        assert result.outputs["false"] is True

    @pytest.mark.asyncio
    async def test_falsy_input_becomes_true(self):
        """Falsy input must produce 'true'=True output."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": False})
        assert result.success is True
        assert result.outputs["true"] is True
        assert result.outputs["false"] is False

    @pytest.mark.asyncio
    async def test_none_input_is_falsy(self):
        """None must be treated as falsy."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": None})
        assert result.success is True
        assert result.outputs["true"] is True

    @pytest.mark.asyncio
    async def test_zero_input_is_falsy(self):
        """Zero must be treated as falsy."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": 0})
        assert result.success is True
        assert result.outputs["true"] is True

    @pytest.mark.asyncio
    async def test_empty_string_is_falsy(self):
        """Empty string must be treated as falsy."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": ""})
        assert result.success is True
        assert result.outputs["true"] is True

    @pytest.mark.asyncio
    async def test_missing_in_input_returns_failure(self):
        """Missing required 'in' input must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_all_nodes_return_node_result(self):
        """execute() must always return NodeResult."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": "any"})
        assert isinstance(result, NodeResult)
