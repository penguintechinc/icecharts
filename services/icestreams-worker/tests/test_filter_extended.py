#!/usr/bin/env python3
"""
Extended tests for FilterTransform node to increase coverage from 73%.

Covers:
- inputs()/outputs() class methods
- validate_config: empty conditions, invalid operator, invalid logic
- _get_field_value: nested dot notation, array indexing, out-of-bounds, non-dict
- _evaluate_condition: all operator types
- _matches: and/or logic, empty conditions
- execute: array input, single object, no match, all operators, non-dict items
"""

import pytest
from unittest.mock import MagicMock

from nodes.transforms.filter import FilterTransform, OPERATORS
from nodes.base import NodeContext


def _make_context(config: dict) -> NodeContext:
    ctx = MagicMock(spec=NodeContext)
    ctx.config = config
    ctx.get_config_value = lambda k, d=None: config.get(k, d)
    ctx.log_info = MagicMock()
    ctx.log_error = MagicMock()
    return ctx


class TestFilterInputsOutputs:
    """Test inputs/outputs class methods."""

    def test_inputs_defined(self) -> None:
        inputs = FilterTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_outputs_defined(self) -> None:
        outputs = FilterTransform.outputs()
        names = {o.name for o in outputs}
        assert "out" in names
        assert "rejected" in names


class TestFilterValidateConfig:
    """Test validate_config branches."""

    def test_no_conditions_error(self) -> None:
        errors = FilterTransform.validate_config({})
        assert any("condition" in e.lower() for e in errors)

    def test_valid_config(self) -> None:
        config = {
            "conditions": [{"field": "status", "operator": "eq", "value": "active"}],
            "logic": "and",
        }
        errors = FilterTransform.validate_config(config)
        assert errors == []

    def test_condition_missing_field(self) -> None:
        config = {"conditions": [{"operator": "eq", "value": "test"}]}
        errors = FilterTransform.validate_config(config)
        assert any("field" in e for e in errors)

    def test_condition_invalid_operator(self) -> None:
        config = {"conditions": [{"field": "x", "operator": "invalid_op", "value": 1}]}
        errors = FilterTransform.validate_config(config)
        assert any("invalid operator" in e.lower() for e in errors)

    def test_invalid_logic(self) -> None:
        config = {
            "conditions": [{"field": "x", "operator": "eq", "value": 1}],
            "logic": "xor",
        }
        errors = FilterTransform.validate_config(config)
        assert any("logic" in e.lower() for e in errors)

    def test_valid_or_logic(self) -> None:
        config = {
            "conditions": [{"field": "x", "operator": "eq", "value": 1}],
            "logic": "or",
        }
        errors = FilterTransform.validate_config(config)
        assert errors == []

    def test_all_operators_are_valid(self) -> None:
        """Every operator in OPERATORS passes validation."""
        for op in OPERATORS:
            config = {"conditions": [{"field": "x", "operator": op, "value": None}]}
            errors = FilterTransform.validate_config(config)
            assert not any(
                "invalid operator" in e.lower() for e in errors
            ), f"Operator '{op}' should be valid but got errors: {errors}"


class TestGetFieldValue:
    """Test _get_field_value helper."""

    def test_simple_field(self) -> None:
        node = FilterTransform()
        assert node._get_field_value({"a": 1}, "a") == 1

    def test_nested_field(self) -> None:
        node = FilterTransform()
        data = {"user": {"profile": {"name": "Alice"}}}
        assert node._get_field_value(data, "user.profile.name") == "Alice"

    def test_array_index(self) -> None:
        node = FilterTransform()
        data = {"items": [10, 20, 30]}
        assert node._get_field_value(data, "items.1") == 20

    def test_array_out_of_bounds(self) -> None:
        node = FilterTransform()
        data = {"items": [1]}
        assert node._get_field_value(data, "items.99") is None

    def test_missing_field(self) -> None:
        node = FilterTransform()
        assert node._get_field_value({"a": 1}, "b") is None

    def test_non_dict_non_array_stops(self) -> None:
        node = FilterTransform()
        # Traversing "a.b" where a is a string — should return None
        assert node._get_field_value({"a": "string"}, "a.b") is None

    def test_empty_field_path(self) -> None:
        node = FilterTransform()
        # Single-part path
        assert node._get_field_value({"": "empty_key"}, "") == "empty_key"


class TestEvaluateCondition:
    """Test _evaluate_condition for all operators."""

    def _cond(self, field, op, value=None):
        return {"field": field, "operator": op, "value": value}

    def test_eq_true(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "eq", 5)) is True

    def test_eq_false(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "eq", 4)) is False

    def test_ne(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "ne", 4)) is True

    def test_gt(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "gt", 3)) is True

    def test_gte(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "gte", 5)) is True

    def test_lt(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 3}, self._cond("x", "lt", 5)) is True

    def test_lte(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": 5}, self._cond("x", "lte", 5)) is True

    def test_contains_string(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition(
                {"x": "hello world"}, self._cond("x", "contains", "world")
            )
            is True
        )

    def test_not_contains(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition(
                {"x": "hello"}, self._cond("x", "not_contains", "world")
            )
            is True
        )

    def test_starts_with(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition(
                {"x": "hello"}, self._cond("x", "starts_with", "hel")
            )
            is True
        )

    def test_ends_with(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition(
                {"x": "hello"}, self._cond("x", "ends_with", "llo")
            )
            is True
        )

    def test_regex(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": "abc123"}, self._cond("x", "regex", r"\d+"))
            is True
        )

    def test_is_null_true(self) -> None:
        node = FilterTransform()
        assert node._evaluate_condition({"x": None}, self._cond("x", "is_null")) is True

    def test_is_null_false(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": "val"}, self._cond("x", "is_null")) is False
        )

    def test_is_not_null(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": "val"}, self._cond("x", "is_not_null"))
            is True
        )

    def test_in_operator(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": "b"}, self._cond("x", "in", ["a", "b", "c"]))
            is True
        )

    def test_not_in_operator(self) -> None:
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": "z"}, self._cond("x", "not_in", ["a", "b"]))
            is True
        )

    def test_contains_no_contains_method(self) -> None:
        """contains on a number returns False."""
        node = FilterTransform()
        assert (
            node._evaluate_condition({"x": 42}, self._cond("x", "contains", "4"))
            is False
        )

    def test_condition_exception_returns_false(self) -> None:
        """Exception in operator returns False."""
        node = FilterTransform()
        # gt on incompatible types raises TypeError, should be caught
        assert (
            node._evaluate_condition({"x": "string"}, self._cond("x", "gt", 5)) is False
        )


class TestMatchesLogic:
    """Test _matches method."""

    def test_and_logic_all_match(self) -> None:
        node = FilterTransform()
        conditions = [
            {"field": "a", "operator": "eq", "value": 1},
            {"field": "b", "operator": "eq", "value": 2},
        ]
        assert node._matches({"a": 1, "b": 2}, conditions, "and") is True

    def test_and_logic_one_fails(self) -> None:
        node = FilterTransform()
        conditions = [
            {"field": "a", "operator": "eq", "value": 1},
            {"field": "b", "operator": "eq", "value": 99},
        ]
        assert node._matches({"a": 1, "b": 2}, conditions, "and") is False

    def test_or_logic_one_matches(self) -> None:
        node = FilterTransform()
        conditions = [
            {"field": "a", "operator": "eq", "value": 99},
            {"field": "b", "operator": "eq", "value": 2},
        ]
        assert node._matches({"a": 1, "b": 2}, conditions, "or") is True

    def test_or_logic_none_match(self) -> None:
        node = FilterTransform()
        conditions = [
            {"field": "a", "operator": "eq", "value": 99},
            {"field": "b", "operator": "eq", "value": 100},
        ]
        assert node._matches({"a": 1, "b": 2}, conditions, "or") is False

    def test_empty_conditions_returns_true(self) -> None:
        node = FilterTransform()
        assert node._matches({"a": 1}, [], "and") is True


class TestFilterExecute:
    """Test execute for all paths."""

    @pytest.mark.asyncio
    async def test_filter_array_input(self) -> None:
        """Array input: matching items in out, rejected in rejected."""
        node = FilterTransform()
        ctx = _make_context(
            {
                "conditions": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "logic": "and",
            }
        )
        data = [
            {"status": "active", "name": "Alice"},
            {"status": "inactive", "name": "Bob"},
            {"status": "active", "name": "Carol"},
        ]
        result = await node.execute(ctx, {"in": data})
        assert result.success is True
        assert len(result.outputs["out"]) == 2
        assert len(result.outputs["rejected"]) == 1

    @pytest.mark.asyncio
    async def test_filter_single_object_match(self) -> None:
        """Single dict input that matches returns it in out, None in rejected."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "age", "operator": "gte", "value": 18}]}
        )
        result = await node.execute(ctx, {"in": {"age": 25}})
        assert result.success is True
        assert result.outputs["out"] == {"age": 25}
        assert result.outputs["rejected"] is None

    @pytest.mark.asyncio
    async def test_filter_single_object_no_match(self) -> None:
        """Single dict that doesn't match returns None in out, item in rejected."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "age", "operator": "gte", "value": 18}]}
        )
        result = await node.execute(ctx, {"in": {"age": 10}})
        assert result.success is True
        assert result.outputs["out"] is None
        assert result.outputs["rejected"] == {"age": 10}

    @pytest.mark.asyncio
    async def test_filter_non_dict_items_pass_through(self) -> None:
        """Non-dict items in array pass through to matching."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "x", "operator": "eq", "value": 1}]}
        )
        result = await node.execute(ctx, {"in": ["string", 42, None]})
        assert result.success is True
        # Non-dict items pass through to matching, not rejected
        assert result.outputs["out"] == ["string", 42, None]
        assert result.outputs["rejected"] == []

    @pytest.mark.asyncio
    async def test_filter_missing_required_input(self) -> None:
        """Missing 'in' input returns failure."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "x", "operator": "eq", "value": 1}]}
        )
        result = await node.execute(ctx, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_filter_or_logic_array(self) -> None:
        """OR logic: items matching any condition pass."""
        node = FilterTransform()
        ctx = _make_context(
            {
                "conditions": [
                    {"field": "type", "operator": "eq", "value": "A"},
                    {"field": "type", "operator": "eq", "value": "B"},
                ],
                "logic": "or",
            }
        )
        data = [{"type": "A"}, {"type": "B"}, {"type": "C"}]
        result = await node.execute(ctx, {"in": data})
        assert result.success is True
        assert len(result.outputs["out"]) == 2
        assert len(result.outputs["rejected"]) == 1

    @pytest.mark.asyncio
    async def test_filter_all_rejected(self) -> None:
        """All items rejected returns empty out list and all in rejected."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "x", "operator": "eq", "value": 999}]}
        )
        data = [{"x": 1}, {"x": 2}]
        result = await node.execute(ctx, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == []
        assert len(result.outputs["rejected"]) == 2

    @pytest.mark.asyncio
    async def test_filter_empty_array(self) -> None:
        """Empty array input returns empty out and rejected."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "x", "operator": "eq", "value": 1}]}
        )
        result = await node.execute(ctx, {"in": []})
        assert result.success is True
        assert result.outputs["out"] == []
        assert result.outputs["rejected"] == []

    @pytest.mark.asyncio
    async def test_filter_nested_field(self) -> None:
        """Filter on nested field using dot notation."""
        node = FilterTransform()
        ctx = _make_context(
            {"conditions": [{"field": "user.active", "operator": "eq", "value": True}]}
        )
        data = [
            {"user": {"active": True, "name": "Alice"}},
            {"user": {"active": False, "name": "Bob"}},
        ]
        result = await node.execute(ctx, {"in": data})
        assert result.success is True
        assert len(result.outputs["out"]) == 1
        assert result.outputs["out"][0]["user"]["name"] == "Alice"
