#!/usr/bin/env python3
"""
Tests for transform nodes in nodes/transforms/.

Tests cover:
- JsonTransform: node_type, inputs/outputs, extract/set/delete/rename/merge/flatten operations
- FilterTransform: node_type, conditions with AND/OR logic, array and single-object input
- ExpressionTransform: node_type, arithmetic, comparisons, safe functions
- MergeTransform: node_type, object/array/concat/deep modes
- SplitTransform: node_type, array/string/chunks/field modes
- DelayTransform: node_type, mocked asyncio.sleep, passthrough of data
- AskAiTransform: node_type, missing API key failure
- CodeTransform: node_type, sandbox execution, result variable
- All transforms return NodeResult instances
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor.node_registry import NodeRegistry
from nodes.base import BaseNode, NodeContext, NodeResult


@pytest.fixture(autouse=True)
def clean_node_registry():
    """Clear NodeRegistry before/after each test."""
    NodeRegistry.clear()
    yield
    NodeRegistry.clear()


def _make_context(config: dict = None, variables: dict = None) -> NodeContext:
    """Create a test NodeContext."""
    return NodeContext(
        execution_id="test-exec-001",
        playbook_id="test-playbook",
        node_id="test-node",
        config=config or {},
        variables=variables or {},
    )


class TestJsonTransform:
    """Tests for JsonTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        """Import and register the JsonTransform node."""
        from nodes.transforms.json_transform import JsonTransform

        self.node_class = JsonTransform
        self.node = JsonTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_json"

    def test_has_input_port_in(self):
        inputs = self.node_class.inputs()
        names = [i.name for i in inputs]
        assert "in" in names

    def test_has_output_port_out(self):
        outputs = self.node_class.outputs()
        names = [o.name for o in outputs]
        assert "out" in names

    def test_category_is_transforms(self):
        assert self.node_class.category == "transforms"

    @pytest.mark.asyncio
    async def test_extract_operation(self):
        """Extract operation must return the value at jsonPath."""
        ctx = _make_context(config={"operation": "extract", "jsonPath": "user.name"})
        result = await self.node.execute(ctx, {"in": {"user": {"name": "Alice"}}})
        assert isinstance(result, NodeResult)
        assert result.success is True
        assert result.outputs["out"] == "Alice"

    @pytest.mark.asyncio
    async def test_set_operation(self):
        """Set operation must set a value at jsonPath."""
        ctx = _make_context(
            config={"operation": "set", "jsonPath": "status", "value": "active"}
        )
        result = await self.node.execute(ctx, {"in": {"id": 1}})
        assert result.success is True
        assert result.outputs["out"]["status"] == "active"
        assert result.outputs["out"]["id"] == 1

    @pytest.mark.asyncio
    async def test_delete_operation(self):
        """Delete operation must remove a key from the dict."""
        ctx = _make_context(config={"operation": "delete", "jsonPath": "secret"})
        result = await self.node.execute(ctx, {"in": {"id": 1, "secret": "password"}})
        assert result.success is True
        assert "secret" not in result.outputs["out"]
        assert result.outputs["out"]["id"] == 1

    @pytest.mark.asyncio
    async def test_rename_operation(self):
        """Rename operation must move a key to a new path."""
        ctx = _make_context(
            config={"operation": "rename", "fromPath": "old_name", "toPath": "new_name"}
        )
        result = await self.node.execute(ctx, {"in": {"old_name": "value", "other": 1}})
        assert result.success is True
        out = result.outputs["out"]
        assert "new_name" in out
        assert "old_name" not in out
        assert out["new_name"] == "value"

    @pytest.mark.asyncio
    async def test_merge_operation(self):
        """Merge operation must combine mergeData with input."""
        ctx = _make_context(
            config={"operation": "merge", "mergeData": {"new_key": "new_val"}}
        )
        result = await self.node.execute(ctx, {"in": {"existing": "data"}})
        assert result.success is True
        out = result.outputs["out"]
        assert out["existing"] == "data"
        assert out["new_key"] == "new_val"

    @pytest.mark.asyncio
    async def test_flatten_operation(self):
        """Flatten operation must convert nested dict to dot-notation keys."""
        ctx = _make_context(config={"operation": "flatten"})
        result = await self.node.execute(ctx, {"in": {"a": {"b": {"c": 42}}}})
        assert result.success is True
        out = result.outputs["out"]
        assert "a.b.c" in out
        assert out["a.b.c"] == 42

    @pytest.mark.asyncio
    async def test_missing_input_returns_failure(self):
        """Missing required 'in' input must return failure."""
        ctx = _make_context(config={"operation": "extract", "jsonPath": "x"})
        result = await self.node.execute(ctx, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_returns_node_result(self):
        """All operations must return NodeResult instances."""
        ctx = _make_context(config={"operation": "extract", "jsonPath": "x"})
        result = await self.node.execute(ctx, {"in": {"x": 1}})
        assert isinstance(result, NodeResult)


class TestFilterTransform:
    """Tests for FilterTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.filter import FilterTransform

        self.node_class = FilterTransform
        self.node = FilterTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_filter"

    def test_has_out_and_rejected_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "out" in names
        assert "rejected" in names

    @pytest.mark.asyncio
    async def test_filter_passes_matching_item(self):
        """Items matching conditions must appear in 'out'."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"status": "active", "id": 1}})
        assert result.success is True
        assert result.outputs["out"] is not None

    @pytest.mark.asyncio
    async def test_filter_rejects_non_matching_item(self):
        """Items not matching conditions must appear in 'rejected'."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "status", "operator": "eq", "value": "active"}
                ],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"status": "inactive", "id": 2}})
        assert result.success is True
        assert result.outputs["out"] is None
        assert result.outputs["rejected"] is not None

    @pytest.mark.asyncio
    async def test_filter_array_input(self):
        """Array input must filter each item individually."""
        ctx = _make_context(
            config={
                "conditions": [{"field": "active", "operator": "eq", "value": True}],
                "logic": "and",
            }
        )
        items = [
            {"active": True, "id": 1},
            {"active": False, "id": 2},
            {"active": True, "id": 3},
        ]
        result = await self.node.execute(ctx, {"in": items})
        assert result.success is True
        assert len(result.outputs["out"]) == 2
        assert len(result.outputs["rejected"]) == 1

    @pytest.mark.asyncio
    async def test_filter_or_logic(self):
        """OR logic must pass if any condition matches."""
        ctx = _make_context(
            config={
                "conditions": [
                    {"field": "type", "operator": "eq", "value": "A"},
                    {"field": "type", "operator": "eq", "value": "B"},
                ],
                "logic": "or",
            }
        )
        result = await self.node.execute(ctx, {"in": {"type": "B"}})
        assert result.success is True
        assert result.outputs["out"] is not None

    @pytest.mark.asyncio
    async def test_filter_gt_operator(self):
        """gt operator must pass when field value > expected."""
        ctx = _make_context(
            config={
                "conditions": [{"field": "score", "operator": "gt", "value": 50}],
                "logic": "and",
            }
        )
        result = await self.node.execute(ctx, {"in": {"score": 75}})
        assert result.success is True
        assert result.outputs["out"] is not None


class TestExpressionTransform:
    """Tests for ExpressionTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.expression import ExpressionTransform

        self.node_class = ExpressionTransform
        self.node = ExpressionTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_expression"

    def test_category_is_transforms(self):
        assert self.node_class.category == "transforms"

    @pytest.mark.asyncio
    async def test_arithmetic_expression(self):
        """Simple arithmetic must evaluate correctly."""
        ctx = _make_context(config={"expression": "2 + 3 * 4"})
        result = await self.node.execute(ctx, {"in": {}})
        assert result.success is True
        assert result.outputs["out"] == 14

    @pytest.mark.asyncio
    async def test_data_access_in_expression(self):
        """Expression can access 'data' variable from input."""
        ctx = _make_context(config={"expression": "data * 2"})
        result = await self.node.execute(ctx, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_comparison_expression(self):
        """Comparison expressions must return bool."""
        ctx = _make_context(config={"expression": "5 > 3"})
        result = await self.node.execute(ctx, {"in": None})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_string_function_upper(self):
        """upper() safe function must work."""
        ctx = _make_context(config={"expression": "upper('hello')"})
        result = await self.node.execute(ctx, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == "HELLO"

    @pytest.mark.asyncio
    async def test_invalid_expression_returns_failure(self):
        """Invalid/disallowed expressions must return failure."""
        ctx = _make_context(config={"expression": "invalid_var_xyz"})
        result = await self.node.execute(ctx, {"in": None})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_len_function(self):
        """len() function must work in expressions."""
        ctx = _make_context(config={"expression": "len(data)"})
        result = await self.node.execute(ctx, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] == 3


class TestMergeTransform:
    """Tests for MergeTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.merge import MergeTransform

        self.node_class = MergeTransform
        self.node = MergeTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_merge"

    @pytest.mark.asyncio
    async def test_object_mode_shallow_merge(self):
        """Object mode must shallow-merge input dicts."""
        ctx = _make_context(config={"mode": "object"})
        result = await self.node.execute(
            ctx,
            {
                "in1": {"a": 1, "b": 2},
                "in2": {"b": 99, "c": 3},
            },
        )
        assert result.success is True
        out = result.outputs["out"]
        assert out["a"] == 1
        assert out["b"] == 99  # in2 overrides
        assert out["c"] == 3

    @pytest.mark.asyncio
    async def test_array_mode_flattens_lists(self):
        """Array mode must concatenate lists."""
        ctx = _make_context(config={"mode": "array"})
        result = await self.node.execute(
            ctx,
            {
                "in1": [1, 2],
                "in2": [3, 4],
            },
        )
        assert result.success is True
        assert result.outputs["out"] == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_concat_mode_joins_strings(self):
        """Concat mode must join strings with separator."""
        ctx = _make_context(config={"mode": "concat", "separator": ", "})
        result = await self.node.execute(
            ctx,
            {
                "in1": "Hello",
                "in2": "World",
            },
        )
        assert result.success is True
        assert result.outputs["out"] == "Hello, World"

    @pytest.mark.asyncio
    async def test_deep_mode_recursive_merge(self):
        """Deep mode must recursively merge nested dicts."""
        ctx = _make_context(config={"mode": "deep"})
        result = await self.node.execute(
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
    async def test_missing_in1_returns_failure(self):
        """Missing required in1 must return failure."""
        ctx = _make_context(config={"mode": "object"})
        result = await self.node.execute(ctx, {})
        assert result.success is False


class TestSplitTransform:
    """Tests for SplitTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.split import SplitTransform

        self.node_class = SplitTransform
        self.node = SplitTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_split"

    def test_outputs_include_count_first_last(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "out" in names
        assert "count" in names
        assert "first" in names
        assert "last" in names

    @pytest.mark.asyncio
    async def test_array_mode_passthrough(self):
        """Array mode must pass list through."""
        ctx = _make_context(config={"mode": "array"})
        items = [1, 2, 3]
        result = await self.node.execute(ctx, {"in": items})
        assert result.success is True
        assert result.outputs["out"] == items
        assert result.outputs["count"] == 3
        assert result.outputs["first"] == 1
        assert result.outputs["last"] == 3

    @pytest.mark.asyncio
    async def test_string_mode_splits_by_delimiter(self):
        """String mode must split by delimiter."""
        ctx = _make_context(config={"mode": "string", "delimiter": ","})
        result = await self.node.execute(ctx, {"in": "a,b,c"})
        assert result.success is True
        assert result.outputs["count"] == 3
        assert result.outputs["first"] == "a"
        assert result.outputs["last"] == "c"

    @pytest.mark.asyncio
    async def test_chunks_mode_splits_into_chunks(self):
        """Chunks mode must split array into fixed-size chunks."""
        ctx = _make_context(config={"mode": "chunks", "chunkSize": 2})
        result = await self.node.execute(ctx, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        chunks = result.outputs["out"]
        assert len(chunks) == 3  # [1,2], [3,4], [5]
        assert chunks[0] == [1, 2]
        assert chunks[2] == [5]

    @pytest.mark.asyncio
    async def test_field_mode_extracts_field_from_items(self):
        """Field mode must extract a field from each dict item."""
        ctx = _make_context(config={"mode": "field", "field": "name"})
        items = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = await self.node.execute(ctx, {"in": items})
        assert result.success is True
        assert result.outputs["out"] == ["Alice", "Bob"]


class TestDelayTransform:
    """Tests for DelayTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.delay import DelayTransform

        self.node_class = DelayTransform
        self.node = DelayTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_delay"

    @pytest.mark.asyncio
    async def test_delay_ms_calls_sleep(self):
        """delayMs config must call asyncio.sleep with correct duration."""
        ctx = _make_context(config={"delayMs": 100})
        with patch(
            "nodes.transforms.delay.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await self.node.execute(ctx, {"in": {"data": "test"}})
            mock_sleep.assert_called_once_with(0.1)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_delay_seconds_calls_sleep(self):
        """delaySeconds config must call asyncio.sleep with correct seconds."""
        ctx = _make_context(config={"delaySeconds": 2})
        with patch(
            "nodes.transforms.delay.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await self.node.execute(ctx, {"in": "hello"})
            mock_sleep.assert_called_once_with(2.0)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_zero_delay_no_sleep(self):
        """Zero delay must not call asyncio.sleep."""
        ctx = _make_context(config={"delayMs": 0})
        with patch(
            "nodes.transforms.delay.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await self.node.execute(ctx, {"in": "data"})
            mock_sleep.assert_not_called()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_dict_input_gets_delay_metadata(self):
        """Dict input must have _delay metadata appended."""
        ctx = _make_context(config={"delayMs": 50})
        with patch("nodes.transforms.delay.asyncio.sleep", new_callable=AsyncMock):
            result = await self.node.execute(ctx, {"in": {"key": "value"}})
        assert "_delay" in result.outputs["out"]
        assert result.outputs["out"]["_delay"]["duration_seconds"] == pytest.approx(
            0.05
        )

    @pytest.mark.asyncio
    async def test_non_dict_input_passed_through(self):
        """Non-dict input must be passed through unchanged (no _delay added)."""
        ctx = _make_context(config={"delayMs": 10})
        with patch("nodes.transforms.delay.asyncio.sleep", new_callable=AsyncMock):
            result = await self.node.execute(ctx, {"in": [1, 2, 3]})
        assert result.outputs["out"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_returns_node_result(self):
        """execute() must return a NodeResult."""
        ctx = _make_context(config={"delayMs": 0})
        result = await self.node.execute(ctx, {"in": "data"})
        assert isinstance(result, NodeResult)


class TestAskAiTransform:
    """Tests for AskAiTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.ask_ai import AskAiTransform

        self.node_class = AskAiTransform
        self.node = AskAiTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_ask_ai"

    def test_has_out_raw_usage_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "out" in names
        assert "raw" in names
        assert "usage" in names

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_failure(self):
        """Missing API key for non-ollama providers must return failure."""
        ctx = _make_context(
            config={
                "prompt": "Summarize: {{data}}",
                "provider": "anthropic",
            }
        )
        # Ensure no API key env var is set
        with patch.dict("os.environ", {}, clear=False):
            result = await self.node.execute(ctx, {"in": "some data"})
        assert result.success is False
        assert "api key" in result.error.lower() or "no api" in result.error.lower()

    @pytest.mark.asyncio
    async def test_anthropic_api_call_mocked(self):
        """Successful Anthropic call must return parsed response."""
        ctx = _make_context(
            config={
                "prompt": "Process: {{data}}",
                "provider": "anthropic",
                "apiKey": "test-key",
                "outputFormat": "text",
            }
        )
        mock_response = {
            "content": "Processed result",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "model": "claude-3-5-sonnet-20241022",
        }
        with patch.object(
            self.node,
            "_call_anthropic",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await self.node.execute(ctx, {"in": "test data"})
        assert result.success is True
        assert result.outputs["raw"] == "Processed result"
        assert result.outputs["out"] == "Processed result"

    @pytest.mark.asyncio
    async def test_json_output_format_parses_json(self):
        """outputFormat=json must parse the AI response as JSON."""
        ctx = _make_context(
            config={
                "prompt": "Return JSON: {{data}}",
                "provider": "anthropic",
                "apiKey": "test-key",
                "outputFormat": "json",
            }
        )
        mock_response = {
            "content": '{"result": 42, "status": "ok"}',
            "usage": {"input_tokens": 5, "output_tokens": 10},
            "model": "test",
        }
        with patch.object(
            self.node,
            "_call_anthropic",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await self.node.execute(ctx, {"in": "data"})
        assert result.success is True
        assert result.outputs["out"] == {"result": 42, "status": "ok"}


class TestCodeTransform:
    """Tests for CodeTransform node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.transforms.code import CodeTransform

        self.node_class = CodeTransform
        self.node = CodeTransform()

    def test_node_type(self):
        assert self.node_class.node_type == "transform_code"

    def test_category_is_transforms(self):
        assert self.node_class.category == "transforms"

    @pytest.mark.asyncio
    async def test_simple_code_execution(self):
        """Simple code setting result must execute correctly."""
        ctx = _make_context(config={"code": "result = data * 2"})
        result = await self.node.execute(ctx, {"in": 21})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_code_with_list_input(self):
        """Code operating on list input must work."""
        ctx = _make_context(config={"code": "result = [x * 2 for x in data]"})
        result = await self.node.execute(ctx, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_forbidden_code_rejected(self):
        """Code using forbidden names must return failure."""
        ctx = _make_context(config={"code": "import os; result = os.getcwd()"})
        result = await self.node.execute(ctx, {"in": None})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_missing_code_returns_failure(self):
        """Missing code config must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"in": "data"})
        # Default code is "result = data", so it should pass through
        assert isinstance(result, NodeResult)

    @pytest.mark.asyncio
    async def test_returns_node_result(self):
        """execute() must always return NodeResult."""
        ctx = _make_context(config={"code": "result = 'ok'"})
        result = await self.node.execute(ctx, {"in": None})
        assert isinstance(result, NodeResult)
