#!/usr/bin/env python3
"""
Comprehensive unit tests for SplitTransform node.

Tests cover:
- Array mode (pass-through existing arrays, wrap single items)
- String mode (delimiter-based splitting with optional trimming)
- Chunks mode (fixed-size grouping of arrays/strings)
- Field mode (extract field from array items)
- Output ports: out, count, first, last
- removeEmpty configuration option
- Error handling and validation
"""

import pytest
from unittest.mock import MagicMock
from typing import Any, Dict

from nodes.transforms.split import SplitTransform
from nodes.base import NodeContext, NodeResult


class TestSplitValidation:
    """Test split configuration validation."""

    def test_validate_config_valid_array_mode(self) -> None:
        """Test validation passes for array mode."""
        config = {"mode": "array"}
        errors = SplitTransform.validate_config(config)
        assert errors == []

    def test_validate_config_valid_string_mode(self) -> None:
        """Test validation passes for string mode with delimiter."""
        config = {"mode": "string", "delimiter": ","}
        errors = SplitTransform.validate_config(config)
        assert errors == []

    def test_validate_config_valid_chunks_mode(self) -> None:
        """Test validation passes for chunks mode with size."""
        config = {"mode": "chunks", "chunkSize": 10}
        errors = SplitTransform.validate_config(config)
        assert errors == []

    def test_validate_config_valid_field_mode(self) -> None:
        """Test validation passes for field mode with field."""
        config = {"mode": "field", "field": "id"}
        errors = SplitTransform.validate_config(config)
        assert errors == []

    def test_validate_config_invalid_mode(self) -> None:
        """Test validation fails for invalid mode."""
        config = {"mode": "invalid"}
        errors = SplitTransform.validate_config(config)
        assert any("Invalid mode" in e for e in errors)

    def test_validate_config_string_missing_delimiter(self) -> None:
        """Test validation fails for string mode without delimiter."""
        config = {"mode": "string"}
        errors = SplitTransform.validate_config(config)
        assert any("delimiter" in e for e in errors)

    def test_validate_config_chunks_missing_size(self) -> None:
        """Test validation fails for chunks mode without size."""
        config = {"mode": "chunks"}
        errors = SplitTransform.validate_config(config)
        assert any("chunkSize" in e for e in errors)

    def test_validate_config_chunks_invalid_size(self) -> None:
        """Test validation fails for invalid chunk size."""
        config = {"mode": "chunks", "chunkSize": 0}
        errors = SplitTransform.validate_config(config)
        assert any("chunkSize" in e for e in errors)

    def test_validate_config_field_missing_field(self) -> None:
        """Test validation fails for field mode without field."""
        config = {"mode": "field"}
        errors = SplitTransform.validate_config(config)
        assert any("field" in e for e in errors)


class TestArrayMode:
    """Test split in array mode."""

    @pytest.mark.asyncio
    async def test_array_mode_pass_through(self) -> None:
        """Test array mode passes through array as-is."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = [1, 2, 3, 4, 5]
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3, 4, 5]
        assert result.outputs["count"] == 5
        assert result.outputs["first"] == 1
        assert result.outputs["last"] == 5

    @pytest.mark.asyncio
    async def test_array_mode_wraps_single_item(self) -> None:
        """Test array mode wraps single non-array item."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "single"})
        assert result.success is True
        assert result.outputs["out"] == ["single"]
        assert result.outputs["count"] == 1
        assert result.outputs["first"] == "single"
        assert result.outputs["last"] == "single"

    @pytest.mark.asyncio
    async def test_array_mode_empty_array(self) -> None:
        """Test array mode with empty array."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": []})
        assert result.success is True
        assert result.outputs["out"] == []
        assert result.outputs["count"] == 0
        assert result.outputs["first"] is None
        assert result.outputs["last"] is None


class TestStringMode:
    """Test split in string mode."""

    @pytest.mark.asyncio
    async def test_string_split_by_comma(self) -> None:
        """Test splitting string by comma."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": ",", "trim": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "apple, banana, cherry"})
        assert result.success is True
        assert result.outputs["out"] == ["apple", "banana", "cherry"]
        assert result.outputs["count"] == 3

    @pytest.mark.asyncio
    async def test_string_split_by_pipe(self) -> None:
        """Test splitting string by custom delimiter."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": "|", "trim": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "one|two|three"})
        assert result.success is True
        assert result.outputs["out"] == ["one", "two", "three"]

    @pytest.mark.asyncio
    async def test_string_split_without_trim(self) -> None:
        """Test splitting string without trimming whitespace."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": ",", "trim": False}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "a, b, c"})
        assert result.success is True
        assert result.outputs["out"] == ["a", " b", " c"]

    @pytest.mark.asyncio
    async def test_string_split_default_trim(self) -> None:
        """Test splitting string with default trim (true)."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": ","}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "x, y, z"})
        assert result.success is True
        assert result.outputs["out"] == ["x", "y", "z"]

    @pytest.mark.asyncio
    async def test_string_split_no_delimiter_found(self) -> None:
        """Test splitting when delimiter is not found."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": "|", "trim": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "no delimiter here"})
        assert result.success is True
        assert result.outputs["out"] == ["no delimiter here"]
        assert result.outputs["count"] == 1

    @pytest.mark.asyncio
    async def test_string_split_on_non_string_converts(self) -> None:
        """Test splitting on non-string converts to string."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "string", "delimiter": ",", "trim": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 123})
        assert result.success is True
        assert result.outputs["out"] == ["123"]


class TestChunksMode:
    """Test split in chunks mode."""

    @pytest.mark.asyncio
    async def test_chunks_array_evenly(self) -> None:
        """Test chunking array into equal-sized chunks."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "chunks", "chunkSize": 2}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5, 6]})
        assert result.success is True
        assert result.outputs["out"] == [[1, 2], [3, 4], [5, 6]]
        assert result.outputs["count"] == 3

    @pytest.mark.asyncio
    async def test_chunks_array_uneven(self) -> None:
        """Test chunking array with remainder."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "chunks", "chunkSize": 3}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["out"] == [[1, 2, 3], [4, 5]]
        assert result.outputs["count"] == 2

    @pytest.mark.asyncio
    async def test_chunks_string(self) -> None:
        """Test chunking string into fixed-size chunks."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "chunks", "chunkSize": 3}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "abcdef"})
        assert result.success is True
        assert result.outputs["out"] == ["abc", "def"]

    @pytest.mark.asyncio
    async def test_chunks_single_item(self) -> None:
        """Test chunking with single item."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "chunks", "chunkSize": 5}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] == [[1, 2, 3]]

    @pytest.mark.asyncio
    async def test_chunks_non_array_wraps(self) -> None:
        """Test chunking non-array wraps it."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "chunks", "chunkSize": 5}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "data"})
        assert result.success is True
        assert result.outputs["out"] == ["data"]


class TestFieldMode:
    """Test split in field mode."""

    @pytest.mark.asyncio
    async def test_field_extract_from_array_of_dicts(self) -> None:
        """Test extracting field from array of dictionaries."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "field", "field": "id"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3]
        assert result.outputs["count"] == 3

    @pytest.mark.asyncio
    async def test_field_extract_nested_path(self) -> None:
        """Test extracting nested field from array items."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "field", "field": "user.email"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = [
            {"user": {"email": "alice@example.com"}},
            {"user": {"email": "bob@example.com"}},
        ]
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == ["alice@example.com", "bob@example.com"]

    @pytest.mark.asyncio
    async def test_field_extract_from_single_dict(self) -> None:
        """Test extracting field that is itself an array."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "field", "field": "items"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"items": [1, 2, 3, 4]}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_field_missing_field(self) -> None:
        """Test field mode with missing field."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "field", "field": "missing"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = [{"id": 1}, {"id": 2}]
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == [None, None]

    @pytest.mark.asyncio
    async def test_field_from_non_dict_items(self) -> None:
        """Test field mode skips non-dict items in array."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "field", "field": "id"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = [{"id": 1}, "string", {"id": 2}]
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == [1, 2]


class TestRemoveEmpty:
    """Test removeEmpty configuration option."""

    @pytest.mark.asyncio
    async def test_remove_empty_removes_none(self) -> None:
        """Test that removeEmpty removes None values."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array", "removeEmpty": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, None, 2, None, 3]})
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3]
        assert result.outputs["count"] == 3

    @pytest.mark.asyncio
    async def test_remove_empty_removes_empty_strings(self) -> None:
        """Test that removeEmpty removes empty strings."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array", "removeEmpty": True}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": ["a", "", "b", "", "c"]})
        assert result.success is True
        assert result.outputs["out"] == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_keep_empty_by_default(self) -> None:
        """Test that empty values are kept by default."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, None, 2]})
        assert result.success is True
        assert result.outputs["out"] == [1, None, 2]


class TestOutputPorts:
    """Test split output ports (count, first, last)."""

    @pytest.mark.asyncio
    async def test_output_count(self) -> None:
        """Test count output."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["count"] == 5

    @pytest.mark.asyncio
    async def test_output_first(self) -> None:
        """Test first item output."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": ["apple", "banana", "cherry"]})
        assert result.success is True
        assert result.outputs["first"] == "apple"

    @pytest.mark.asyncio
    async def test_output_last(self) -> None:
        """Test last item output."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": ["apple", "banana", "cherry"]})
        assert result.success is True
        assert result.outputs["last"] == "cherry"

    @pytest.mark.asyncio
    async def test_empty_array_outputs(self) -> None:
        """Test outputs for empty array."""
        node = SplitTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"mode": "array"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": []})
        assert result.success is True
        assert result.outputs["count"] == 0
        assert result.outputs["first"] is None
        assert result.outputs["last"] is None


class TestNodeInterface:
    """Test node interface and metadata."""

    def test_node_inputs(self) -> None:
        """Test node input definitions."""
        inputs = SplitTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_node_outputs(self) -> None:
        """Test node output definitions."""
        outputs = SplitTransform.outputs()
        assert len(outputs) == 4
        output_names = {o.name for o in outputs}
        assert output_names == {"out", "count", "first", "last"}

    def test_node_type(self) -> None:
        """Test node type identifier."""
        assert SplitTransform.node_type == "transform_split"

    def test_node_category(self) -> None:
        """Test node category."""
        assert SplitTransform.category == "transforms"
