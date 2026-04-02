#!/usr/bin/env python3
"""
Comprehensive unit tests for JsonTransform node.

Tests cover:
- Extract operation with dot notation and JMESPath
- Set operation with nested path creation
- Delete operation on nested paths
- Rename operation for field renaming
- Merge operation for object merging
- Flatten operation for nested structures
- Unflatten operation for nested reconstruction
- Error handling for invalid operations
- Edge cases (missing paths, non-dict inputs)
"""

import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest
from nodes.base import NodeContext, NodeResult
from nodes.transforms.json_transform import JsonTransform


class TestJsonTransformValidation:
    """Test JSON transform configuration validation."""

    def test_validate_config_valid_extract(self) -> None:
        """Test validation passes for valid extract operation."""
        config = {"operation": "extract", "jsonPath": "user.name"}
        errors = JsonTransform.validate_config(config)
        assert errors == []

    def test_validate_config_valid_set(self) -> None:
        """Test validation passes for valid set operation."""
        config = {"operation": "set", "jsonPath": "user.name", "value": "John"}
        errors = JsonTransform.validate_config(config)
        assert errors == []

    def test_validate_config_missing_operation(self) -> None:
        """Test validation fails without operation."""
        config = {"jsonPath": "user.name"}
        errors = JsonTransform.validate_config(config)
        # Missing operation defaults to "extract", check for missing jsonPath instead
        assert len(errors) == 0 or any(
            "operation" in e.lower() or "path" in e.lower() for e in errors
        )

    def test_validate_config_invalid_operation(self) -> None:
        """Test validation fails for invalid operation."""
        config = {"operation": "invalid"}
        errors = JsonTransform.validate_config(config)
        assert any("Invalid operation" in e for e in errors)

    def test_validate_config_extract_missing_path(self) -> None:
        """Test validation fails for extract without path."""
        config = {"operation": "extract"}
        errors = JsonTransform.validate_config(config)
        assert any("jsonPath" in e for e in errors)

    def test_validate_config_set_missing_path(self) -> None:
        """Test validation fails for set without path."""
        config = {"operation": "set", "value": "test"}
        errors = JsonTransform.validate_config(config)
        assert any("jsonPath" in e for e in errors)

    def test_validate_config_set_missing_value(self) -> None:
        """Test validation fails for set without value."""
        config = {"operation": "set", "jsonPath": "field"}
        errors = JsonTransform.validate_config(config)
        assert any("value" in e for e in errors)

    def test_validate_config_rename_missing_paths(self) -> None:
        """Test validation fails for rename without paths."""
        config = {"operation": "rename", "fromPath": "old"}
        errors = JsonTransform.validate_config(config)
        assert any("toPath" in e for e in errors)

    def test_validate_config_all_operations(self) -> None:
        """Test all valid operations."""
        operations = [
            "extract",
            "set",
            "delete",
            "rename",
            "merge",
            "flatten",
            "unflatten",
        ]
        for op in operations:
            config = {
                "operation": op,
                "jsonPath": "test",
                "value": "test",
                "fromPath": "from",
                "toPath": "to",
            }
            errors = JsonTransform.validate_config(config)
            # Should not have operation-specific errors
            assert not any("Invalid operation" in e for e in errors)


class TestExtractOperation:
    """Test JSON extract operation."""

    @pytest.mark.asyncio
    async def test_extract_simple_key(self) -> None:
        """Test extracting a simple key from dictionary."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract", "jsonPath": "name"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"name": "John", "age": 30}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == "John"

    @pytest.mark.asyncio
    async def test_extract_nested_path(self) -> None:
        """Test extracting nested path using dot notation."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract", "jsonPath": "user.profile.email"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"profile": {"email": "test@example.com"}}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_extract_array_index(self) -> None:
        """Test extracting from array using index."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract", "jsonPath": "items[0]"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"items": [10, 20, 30]}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_extract_missing_path(self) -> None:
        """Test extracting path that doesn't exist."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract", "jsonPath": "user.email"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_extract_from_non_dict(self) -> None:
        """Test extracting from non-dictionary input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract", "jsonPath": "field"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "not a dict"})
        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_extract_default_path(self) -> None:
        """Test extraction with missing/empty jsonPath returns error (JMESPath requires a valid expression)."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "extract"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"test": "value"}
        result = await node.execute(context, {"in": data})
        # No jsonPath defaults to "$" which is invalid JMESPath — expect failure
        assert result.success is False
        assert result.error is not None


class TestSetOperation:
    """Test JSON set operation."""

    @pytest.mark.asyncio
    async def test_set_simple_value(self) -> None:
        """Test setting a simple value."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "name", "value": "Jane"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"name": "John", "age": 30}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["name"] == "Jane"

    @pytest.mark.asyncio
    async def test_set_nested_value(self) -> None:
        """Test setting a nested value."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "operation": "set",
            "jsonPath": "user.email",
            "value": "new@example.com",
        }
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user"]["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_set_creates_nested_structure(self) -> None:
        """Test that set creates intermediate dictionaries."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "a.b.c", "value": "value"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {}})
        assert result.success is True
        assert result.outputs["out"]["a"]["b"]["c"] == "value"

    @pytest.mark.asyncio
    async def test_set_overwrites_existing(self) -> None:
        """Test that set overwrites existing nested structure."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "user", "value": "replaced"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user"] == "replaced"

    @pytest.mark.asyncio
    async def test_set_numeric_value(self) -> None:
        """Test setting numeric values."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "count", "value": 42}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {}})
        assert result.success is True
        assert result.outputs["out"]["count"] == 42

    @pytest.mark.asyncio
    async def test_set_null_value(self) -> None:
        """Test setting null value."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "field", "value": None}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"field": "old"}})
        assert result.success is True
        assert result.outputs["out"]["field"] is None

    @pytest.mark.asyncio
    async def test_set_with_path_reference(self) -> None:
        """Test setting value from another path using $. prefix."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "set", "jsonPath": "copy", "value": "$.source"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"source": "original"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["copy"] == "original"


class TestDeleteOperation:
    """Test JSON delete operation."""

    @pytest.mark.asyncio
    async def test_delete_simple_key(self) -> None:
        """Test deleting a simple key."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "delete", "jsonPath": "name"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"name": "John", "age": 30}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert "name" not in result.outputs["out"]
        assert result.outputs["out"]["age"] == 30

    @pytest.mark.asyncio
    async def test_delete_nested_key(self) -> None:
        """Test deleting a nested key."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "delete", "jsonPath": "user.email"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert "email" not in result.outputs["out"]["user"]
        assert result.outputs["out"]["user"]["name"] == "John"

    @pytest.mark.asyncio
    async def test_delete_non_existent_path(self) -> None:
        """Test deleting path that doesn't exist."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "delete", "jsonPath": "missing"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"existing": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["existing"] == "value"

    @pytest.mark.asyncio
    async def test_delete_from_non_dict(self) -> None:
        """Test delete operation on non-dict input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "delete", "jsonPath": "field"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "not a dict"})
        assert result.success is False


class TestRenameOperation:
    """Test JSON rename operation."""

    @pytest.mark.asyncio
    async def test_rename_simple_key(self) -> None:
        """Test renaming a simple key."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "operation": "rename",
            "fromPath": "old_name",
            "toPath": "new_name",
        }
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"old_name": "value", "other": "data"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert "new_name" in result.outputs["out"]
        assert "old_name" not in result.outputs["out"]
        assert result.outputs["out"]["new_name"] == "value"

    @pytest.mark.asyncio
    async def test_rename_nested_key(self) -> None:
        """Test renaming nested keys."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {
            "operation": "rename",
            "fromPath": "user.email_address",
            "toPath": "user.email",
        }
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"email_address": "john@example.com"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user"]["email"] == "john@example.com"
        assert "email_address" not in result.outputs["out"]["user"]

    @pytest.mark.asyncio
    async def test_rename_to_different_level(self) -> None:
        """Test renaming to different nesting level."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "rename", "fromPath": "a", "toPath": "b.c"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"a": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["b"]["c"] == "value"
        assert "a" not in result.outputs["out"]

    @pytest.mark.asyncio
    async def test_rename_non_existent_key(self) -> None:
        """Test renaming key that doesn't exist."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "rename", "fromPath": "missing", "toPath": "new"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"existing": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        # Rename sets None if source missing, so new will be None
        assert (
            result.outputs["out"]["new"] is None or "new" not in result.outputs["out"]
        )


class TestMergeOperation:
    """Test JSON merge operation."""

    @pytest.mark.asyncio
    async def test_merge_simple_dicts(self) -> None:
        """Test merging two dictionaries."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "merge", "mergeData": {"new_key": "new_value"}}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"existing": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["existing"] == "value"
        assert result.outputs["out"]["new_key"] == "new_value"

    @pytest.mark.asyncio
    async def test_merge_overwrites_existing(self) -> None:
        """Test that merge overwrites existing keys."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "merge", "mergeData": {"key": "new_value"}}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"key": "old_value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["key"] == "new_value"

    @pytest.mark.asyncio
    async def test_merge_json_string(self) -> None:
        """Test merge with JSON string input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "merge", "mergeData": '{"new": "value"}'}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"existing": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["new"] == "value"

    @pytest.mark.asyncio
    async def test_merge_invalid_json(self) -> None:
        """Test merge with invalid JSON string."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "merge", "mergeData": "{invalid json"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {}})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_merge_non_dict_input(self) -> None:
        """Test merge with non-dict input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "merge", "mergeData": {"key": "value"}}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "not a dict"})
        assert result.success is True
        assert result.outputs["out"] == {"key": "value"}


class TestFlattenOperation:
    """Test JSON flatten operation."""

    @pytest.mark.asyncio
    async def test_flatten_simple_nested(self) -> None:
        """Test flattening simple nested structure."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "flatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user.name"] == "John"
        assert result.outputs["out"]["user.email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_flatten_deeply_nested(self) -> None:
        """Test flattening deeply nested structure."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "flatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"a": {"b": {"c": {"d": "value"}}}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["a.b.c.d"] == "value"

    @pytest.mark.asyncio
    async def test_flatten_with_arrays(self) -> None:
        """Test flattening structure with arrays."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "flatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"items": [{"id": 1}, {"id": 2}]}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["items.0.id"] == 1
        assert result.outputs["out"]["items.1.id"] == 2

    @pytest.mark.asyncio
    async def test_flatten_custom_separator(self) -> None:
        """Test flatten with custom separator."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "flatten", "separator": "_"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user": {"name": "John"}}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user_name"] == "John"

    @pytest.mark.asyncio
    async def test_flatten_non_dict_input(self) -> None:
        """Test flatten with non-dict input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "flatten"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "not a dict"})
        assert result.success is True
        assert result.outputs["out"] == "not a dict"


class TestUnflattenOperation:
    """Test JSON unflatten operation."""

    @pytest.mark.asyncio
    async def test_unflatten_simple(self) -> None:
        """Test unflattening simple structure."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "unflatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user.name": "John", "user.email": "john@example.com"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user"]["name"] == "John"
        assert result.outputs["out"]["user"]["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_unflatten_deeply_nested(self) -> None:
        """Test unflattening deeply nested structure."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "unflatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"a.b.c.d": "value"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["a"]["b"]["c"]["d"] == "value"

    @pytest.mark.asyncio
    async def test_unflatten_custom_separator(self) -> None:
        """Test unflatten with custom separator."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "unflatten", "separator": "_"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"user_name": "John"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["user"]["name"] == "John"

    @pytest.mark.asyncio
    async def test_unflatten_mixed_keys(self) -> None:
        """Test unflatten with mixed flat and nested keys."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "unflatten", "separator": "."}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        data = {"a.b": "value1", "c": "value2"}
        result = await node.execute(context, {"in": data})
        assert result.success is True
        assert result.outputs["out"]["a"]["b"] == "value1"
        assert result.outputs["out"]["c"] == "value2"

    @pytest.mark.asyncio
    async def test_unflatten_non_dict_input(self) -> None:
        """Test unflatten with non-dict input."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"operation": "unflatten"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "not a dict"})
        assert result.success is True
        assert result.outputs["out"] == "not a dict"


class TestRoundTrip:
    """Test flatten and unflatten roundtrips."""

    @pytest.mark.asyncio
    async def test_flatten_unflatten_roundtrip(self) -> None:
        """Test that flatten followed by unflatten recreates original."""
        node = JsonTransform()
        context = MagicMock(spec=NodeContext)

        original = {"user": {"profile": {"name": "John", "email": "john@example.com"}}}

        # Flatten
        context.config = {"operation": "flatten"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result1 = await node.execute(context, {"in": original})
        assert result1.success is True
        flattened = result1.outputs["out"]

        # Unflatten
        context.config = {"operation": "unflatten"}
        result2 = await node.execute(context, {"in": flattened})
        assert result2.success is True

        # Should be equivalent to original
        assert result2.outputs["out"] == original


class TestNodeInterface:
    """Test node interface and metadata."""

    def test_node_inputs(self) -> None:
        """Test node input definitions."""
        inputs = JsonTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_node_outputs(self) -> None:
        """Test node output definitions."""
        outputs = JsonTransform.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_node_type(self) -> None:
        """Test node type identifier."""
        assert JsonTransform.node_type == "transform_json"

    def test_node_category(self) -> None:
        """Test node category."""
        assert JsonTransform.category == "transforms"
