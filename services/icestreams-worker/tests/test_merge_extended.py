#!/usr/bin/env python3
"""
Extended tests for MergeTransform node to increase coverage from 69%.

Covers:
- inputs()/outputs() class methods
- validate_config: mode validation, separator validation
- execute: object, array, concat (str, list, mixed), deep, fallback
- _deep_merge recursive logic
- error handling
- non-dict values in object mode
"""

import pytest
from unittest.mock import MagicMock

from nodes.transforms.merge import MergeTransform
from nodes.base import NodeContext


def _make_context(config: dict) -> NodeContext:
    ctx = MagicMock(spec=NodeContext)
    ctx.config = config
    ctx.get_config_value = lambda k, d=None: config.get(k, d)
    ctx.log_info = MagicMock()
    ctx.log_error = MagicMock()
    return ctx


class TestMergeInputsOutputs:
    """Test inputs/outputs class methods."""

    def test_inputs_defined(self) -> None:
        inputs = MergeTransform.inputs()
        names = {i.name for i in inputs}
        assert "in1" in names
        assert "in2" in names
        assert "in3" in names
        assert "in4" in names

    def test_in1_required(self) -> None:
        inputs = MergeTransform.inputs()
        in1 = next(i for i in inputs if i.name == "in1")
        assert in1.required is True

    def test_in2_optional(self) -> None:
        inputs = MergeTransform.inputs()
        in2 = next(i for i in inputs if i.name == "in2")
        assert in2.required is False

    def test_outputs_defined(self) -> None:
        outputs = MergeTransform.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"


class TestMergeValidateConfig:
    """Test validate_config for all branches."""

    def test_valid_default_mode(self) -> None:
        errors = MergeTransform.validate_config({})
        assert errors == []

    def test_valid_object_mode(self) -> None:
        errors = MergeTransform.validate_config({"mode": "object"})
        assert errors == []

    def test_valid_array_mode(self) -> None:
        errors = MergeTransform.validate_config({"mode": "array"})
        assert errors == []

    def test_valid_concat_mode(self) -> None:
        errors = MergeTransform.validate_config({"mode": "concat"})
        assert errors == []

    def test_valid_deep_mode(self) -> None:
        errors = MergeTransform.validate_config({"mode": "deep"})
        assert errors == []

    def test_invalid_mode(self) -> None:
        errors = MergeTransform.validate_config({"mode": "invalid_mode"})
        assert any("Invalid mode" in e for e in errors)

    def test_concat_mode_with_valid_separator(self) -> None:
        errors = MergeTransform.validate_config({"mode": "concat", "separator": ", "})
        assert errors == []

    def test_concat_mode_with_invalid_separator(self) -> None:
        errors = MergeTransform.validate_config({"mode": "concat", "separator": 123})
        assert any("separator" in e for e in errors)

    def test_concat_mode_empty_separator(self) -> None:
        errors = MergeTransform.validate_config({"mode": "concat", "separator": ""})
        assert errors == []


class TestMergeExecuteObjectMode:
    """Test object merge mode."""

    @pytest.mark.asyncio
    async def test_object_mode_two_dicts(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        result = await node.execute(ctx, {"in1": {"a": 1}, "in2": {"b": 2}})
        assert result.success is True
        assert result.outputs["out"] == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_object_mode_override(self) -> None:
        """Later inputs override earlier ones."""
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        result = await node.execute(ctx, {"in1": {"a": 1, "b": 0}, "in2": {"b": 2}})
        assert result.success is True
        assert result.outputs["out"]["b"] == 2

    @pytest.mark.asyncio
    async def test_object_mode_non_dict_wrapped(self) -> None:
        """Non-dict values are wrapped with indexed keys."""
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        result = await node.execute(ctx, {"in1": "string_value"})
        assert result.success is True
        out = result.outputs["out"]
        assert isinstance(out, dict)
        # Non-dict gets wrapped as value_0
        assert "value_0" in out

    @pytest.mark.asyncio
    async def test_object_mode_four_dicts(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        result = await node.execute(
            ctx, {"in1": {"a": 1}, "in2": {"b": 2}, "in3": {"c": 3}, "in4": {"d": 4}}
        )
        assert result.success is True
        assert result.outputs["out"] == {"a": 1, "b": 2, "c": 3, "d": 4}

    @pytest.mark.asyncio
    async def test_object_mode_default(self) -> None:
        """Default mode is 'object'."""
        node = MergeTransform()
        ctx = _make_context({})
        result = await node.execute(ctx, {"in1": {"x": 10}})
        assert result.success is True
        assert result.outputs["out"] == {"x": 10}


class TestMergeExecuteArrayMode:
    """Test array merge mode."""

    @pytest.mark.asyncio
    async def test_array_mode_two_lists(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "array"})
        result = await node.execute(ctx, {"in1": [1, 2], "in2": [3, 4]})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_array_mode_non_list_appended(self) -> None:
        """Non-list values are appended as single items."""
        node = MergeTransform()
        ctx = _make_context({"mode": "array"})
        result = await node.execute(ctx, {"in1": [1, 2], "in2": 3})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_array_mode_all_scalars(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "array"})
        result = await node.execute(ctx, {"in1": "a", "in2": "b"})
        assert result.success is True
        assert result.outputs["out"] == ["a", "b"]


class TestMergeExecuteConcatMode:
    """Test concat merge mode."""

    @pytest.mark.asyncio
    async def test_concat_strings_with_separator(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "concat", "separator": " | "})
        result = await node.execute(ctx, {"in1": "hello", "in2": "world"})
        assert result.success is True
        assert result.outputs["out"] == "hello | world"

    @pytest.mark.asyncio
    async def test_concat_strings_no_separator(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "concat"})
        result = await node.execute(ctx, {"in1": "foo", "in2": "bar"})
        assert result.success is True
        assert result.outputs["out"] == "foobar"

    @pytest.mark.asyncio
    async def test_concat_lists(self) -> None:
        """All-list inputs are extended (not joined as strings)."""
        node = MergeTransform()
        ctx = _make_context({"mode": "concat"})
        result = await node.execute(ctx, {"in1": [1, 2], "in2": [3, 4]})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_concat_mixed_types_uses_str(self) -> None:
        """Mixed-type inputs are converted to strings and joined."""
        node = MergeTransform()
        ctx = _make_context({"mode": "concat", "separator": "-"})
        result = await node.execute(ctx, {"in1": 42, "in2": "hello"})
        assert result.success is True
        assert result.outputs["out"] == "42-hello"


class TestMergeExecuteDeepMode:
    """Test deep merge mode."""

    @pytest.mark.asyncio
    async def test_deep_merge_nested(self) -> None:
        node = MergeTransform()
        ctx = _make_context({"mode": "deep"})
        result = await node.execute(
            ctx,
            {
                "in1": {"a": {"x": 1, "y": 2}},
                "in2": {"a": {"y": 99, "z": 3}},
            },
        )
        assert result.success is True
        out = result.outputs["out"]
        assert out["a"]["x"] == 1
        assert out["a"]["y"] == 99
        assert out["a"]["z"] == 3

    @pytest.mark.asyncio
    async def test_deep_merge_non_dict_values(self) -> None:
        """Non-dict values in deep mode get indexed keys."""
        node = MergeTransform()
        ctx = _make_context({"mode": "deep"})
        result = await node.execute(ctx, {"in1": "not_a_dict"})
        assert result.success is True
        out = result.outputs["out"]
        assert isinstance(out, dict)
        assert "value_0" in out

    @pytest.mark.asyncio
    async def test_deep_merge_recursive(self) -> None:
        """Deeply nested dicts are recursively merged."""
        node = MergeTransform()
        ctx = _make_context({"mode": "deep"})
        result = await node.execute(
            ctx,
            {
                "in1": {"level1": {"level2": {"a": 1}}},
                "in2": {"level1": {"level2": {"b": 2}}},
            },
        )
        assert result.success is True
        assert result.outputs["out"]["level1"]["level2"] == {"a": 1, "b": 2}


class TestMergeExecuteEdgeCases:
    """Test edge cases for execute."""

    @pytest.mark.asyncio
    async def test_no_inputs_returns_none(self) -> None:
        """No inputs (all None) returns None."""
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        # in1 is required, but if all collected values are None after filtering
        # we test the empty values path — simulate by providing None-like values
        # Note: _validate_inputs checks in1 is present, so we must provide it
        # To hit the empty branch, all inputs must be falsy-None
        # The code: values = [inputs.get(key) for key in input_keys if inputs.get(key) is not None]
        # If all values are None, values=[] and we return None
        result = await node.execute(ctx, {"in1": None})
        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_missing_required_input_fails(self) -> None:
        """Missing in1 returns failure."""
        node = MergeTransform()
        ctx = _make_context({"mode": "object"})
        result = await node.execute(ctx, {})
        assert result.success is False
        assert result.error is not None


class TestDeepMergeMethod:
    """Unit tests for _deep_merge helper."""

    def test_simple_merge(self) -> None:
        node = MergeTransform()
        result = node._deep_merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_override_value(self) -> None:
        node = MergeTransform()
        result = node._deep_merge({"a": 1}, {"a": 99})
        assert result == {"a": 99}

    def test_nested_merge(self) -> None:
        node = MergeTransform()
        result = node._deep_merge({"a": {"x": 1}}, {"a": {"y": 2}})
        assert result == {"a": {"x": 1, "y": 2}}

    def test_non_dict_override(self) -> None:
        """Non-dict value overrides dict value."""
        node = MergeTransform()
        result = node._deep_merge({"a": {"x": 1}}, {"a": "scalar"})
        assert result == {"a": "scalar"}
