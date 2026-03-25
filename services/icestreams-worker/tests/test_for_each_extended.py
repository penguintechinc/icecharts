#!/usr/bin/env python3
"""
Extended tests for ForEachConditional node to increase coverage from 77%.

Covers:
- inputs()/outputs() class methods
- validate_config: field type validation
- _get_field_value: dot notation, array indexing, out-of-bounds, non-dict
- execute: list, tuple, set, dict (values), single item wrap
- execute: field extraction with None filtering
- execute: empty input
- execute: missing required input
- execute: exception handling
"""

import pytest
from unittest.mock import MagicMock

from nodes.conditionals.for_each import ForEachConditional
from nodes.base import NodeContext


def _make_context(config: dict) -> NodeContext:
    ctx = MagicMock(spec=NodeContext)
    ctx.config = config
    ctx.get_config_value = lambda k, d=None: config.get(k, d)
    ctx.log_info = MagicMock()
    ctx.log_error = MagicMock()
    return ctx


class TestForEachInputsOutputs:
    """Test inputs/outputs class methods."""

    def test_inputs_defined(self) -> None:
        inputs = ForEachConditional.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "array"
        assert inputs[0].required is True

    def test_outputs_defined(self) -> None:
        outputs = ForEachConditional.outputs()
        names = {o.name for o in outputs}
        assert "item" in names
        assert "index" in names
        assert "done" in names


class TestForEachValidateConfig:
    """Test validate_config branches."""

    def test_valid_empty_config(self) -> None:
        errors = ForEachConditional.validate_config({})
        assert errors == []

    def test_valid_field_string(self) -> None:
        errors = ForEachConditional.validate_config({"field": "items.name"})
        assert errors == []

    def test_invalid_field_not_string(self) -> None:
        errors = ForEachConditional.validate_config({"field": 123})
        assert any("field" in e.lower() for e in errors)

    def test_field_none_is_valid(self) -> None:
        """field=None means no extraction — no error."""
        errors = ForEachConditional.validate_config({"field": None})
        assert errors == []


class TestGetFieldValue:
    """Test _get_field_value helper."""

    def test_simple_field(self) -> None:
        node = ForEachConditional()
        assert node._get_field_value({"name": "Alice"}, "name") == "Alice"

    def test_nested_field(self) -> None:
        node = ForEachConditional()
        data = {"a": {"b": {"c": 42}}}
        assert node._get_field_value(data, "a.b.c") == 42

    def test_array_index(self) -> None:
        node = ForEachConditional()
        data = {"items": ["x", "y", "z"]}
        assert node._get_field_value(data, "items.1") == "y"

    def test_array_out_of_bounds(self) -> None:
        node = ForEachConditional()
        data = {"items": [1]}
        assert node._get_field_value(data, "items.99") is None

    def test_non_dict_non_list_returns_none(self) -> None:
        node = ForEachConditional()
        assert node._get_field_value("a_string", "field") is None

    def test_missing_field(self) -> None:
        node = ForEachConditional()
        assert node._get_field_value({"a": 1}, "b") is None


class TestForEachExecute:
    """Test execute method all branches."""

    @pytest.mark.asyncio
    async def test_list_input(self) -> None:
        """Standard list input."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": [10, 20, 30]})
        assert result.success is True
        assert result.outputs["item"] == 10
        assert result.outputs["index"] == 0
        assert result.outputs["done"] is False
        assert result.outputs["_iterations"] == [10, 20, 30]

    @pytest.mark.asyncio
    async def test_tuple_input_converted_to_list(self) -> None:
        """Tuple input is converted to list."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": (1, 2, 3)})
        assert result.success is True
        assert result.outputs["_iterations"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_set_input_converted_to_list(self) -> None:
        """Set input is converted to list."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": {5, 6, 7}})
        assert result.success is True
        assert len(result.outputs["_iterations"]) == 3

    @pytest.mark.asyncio
    async def test_dict_input_iterates_values(self) -> None:
        """Dict input iterates over values."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": {"a": 1, "b": 2}})
        assert result.success is True
        assert set(result.outputs["_iterations"]) == {1, 2}

    @pytest.mark.asyncio
    async def test_single_value_wrapped_in_array(self) -> None:
        """Single non-iterable value is wrapped in a single-item list."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": "single_string"})
        assert result.success is True
        assert result.outputs["_iterations"] == ["single_string"]

    @pytest.mark.asyncio
    async def test_integer_wrapped_in_array(self) -> None:
        """Integer is wrapped in a list."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": 42})
        assert result.success is True
        assert result.outputs["_iterations"] == [42]

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        """Empty list returns done=True and item=None."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": []})
        assert result.success is True
        assert result.outputs["item"] is None
        assert result.outputs["done"] is True
        assert result.outputs["_iterations"] == []

    @pytest.mark.asyncio
    async def test_field_extraction(self) -> None:
        """Field extraction pulls nested values from each item."""
        node = ForEachConditional()
        ctx = _make_context({"field": "name"})
        data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Carol"}]
        result = await node.execute(ctx, {"array": data})
        assert result.success is True
        assert result.outputs["_iterations"] == ["Alice", "Bob", "Carol"]
        assert result.outputs["item"] == "Alice"

    @pytest.mark.asyncio
    async def test_field_extraction_filters_none(self) -> None:
        """Items without the field are filtered out (None removed)."""
        node = ForEachConditional()
        ctx = _make_context({"field": "value"})
        data = [
            {"value": 1},
            {"no_value": "x"},  # missing 'value' field → None → filtered
            {"value": 3},
        ]
        result = await node.execute(ctx, {"array": data})
        assert result.success is True
        assert result.outputs["_iterations"] == [1, 3]

    @pytest.mark.asyncio
    async def test_field_extraction_all_none_gives_empty(self) -> None:
        """All items missing field gives empty iterations and done=True."""
        node = ForEachConditional()
        ctx = _make_context({"field": "missing_key"})
        data = [{"a": 1}, {"b": 2}]
        result = await node.execute(ctx, {"array": data})
        assert result.success is True
        assert result.outputs["_iterations"] == []
        assert result.outputs["done"] is True

    @pytest.mark.asyncio
    async def test_missing_required_array_input(self) -> None:
        """Missing 'array' input returns failure."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_single_item_list_not_done(self) -> None:
        """Single-item list: done=False, item is the element."""
        node = ForEachConditional()
        ctx = _make_context({})
        result = await node.execute(ctx, {"array": ["only"]})
        assert result.success is True
        assert result.outputs["item"] == "only"
        assert result.outputs["done"] is False

    @pytest.mark.asyncio
    async def test_nested_field_extraction(self) -> None:
        """Nested field extraction using dot notation."""
        node = ForEachConditional()
        ctx = _make_context({"field": "user.id"})
        data = [
            {"user": {"id": 1}},
            {"user": {"id": 2}},
        ]
        result = await node.execute(ctx, {"array": data})
        assert result.success is True
        assert result.outputs["_iterations"] == [1, 2]
