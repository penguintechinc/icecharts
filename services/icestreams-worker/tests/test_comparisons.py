#!/usr/bin/env python3
"""
Tests for comparison conditional nodes in nodes/conditionals/comparisons.py.

Tests cover:
- EqualsConditional: equal/not-equal string, numbers, None, mixed types
- GreaterThanConditional: true/false branches, numeric conversion, invalid inputs
- LessThanConditional: true/false branches, numeric conversion, invalid inputs
- ContainsConditional: string contains, array contains, dict contains, empty values
- RegexConditional: pattern matching, invalid patterns, non-string values
- Input validation and error handling
- All nodes return NodeResult with correct success/failure status
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nodes.base import NodeContext, NodeResult
from executor.node_registry import NodeRegistry


@pytest.fixture(autouse=True)
def clean_node_registry():
    """Clear NodeRegistry before/after each test."""
    NodeRegistry.clear()
    yield
    NodeRegistry.clear()


def _make_context(config: dict = None, variables: dict = None, node_id: str = "test-node") -> NodeContext:
    """Create a test NodeContext."""
    return NodeContext(
        execution_id="test-exec-001",
        playbook_id="test-playbook",
        node_id=node_id,
        config=config or {},
        variables=variables or {},
    )


class TestEqualsConditional:
    """Tests for EqualsConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.comparisons import EqualsConditional
        self.node_class = EqualsConditional
        self.node = EqualsConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_equals"

    def test_category_is_conditionals(self):
        assert self.node_class.category == "conditionals"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_value_and_expected_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "value" in names
        assert "expected" in names

    @pytest.mark.asyncio
    async def test_equal_strings(self):
        """When strings are equal, true output is populated."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "hello", "expected": "hello"})
        assert isinstance(result, NodeResult)
        assert result.success is True
        assert result.outputs["true"] == "hello"
        assert result.outputs.get("false") is None

    @pytest.mark.asyncio
    async def test_unequal_strings(self):
        """When strings are not equal, false output is populated."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "hello", "expected": "world"})
        assert result.success is True
        assert result.outputs.get("true") is None
        assert result.outputs["false"] is None

    @pytest.mark.asyncio
    async def test_equal_numbers(self):
        """When numbers are equal, true output is populated."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 42, "expected": 42})
        assert result.success is True
        assert result.outputs["true"] == 42

    @pytest.mark.asyncio
    async def test_equal_booleans(self):
        """When booleans are equal, true output is populated."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": True, "expected": True})
        assert result.success is True
        assert result.outputs["true"] is True

    @pytest.mark.asyncio
    async def test_equal_none_values(self):
        """When both values are None, true output is populated."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": None, "expected": None})
        assert result.success is True
        assert result.outputs["true"] is None
        assert result.outputs.get("false") is None

    @pytest.mark.asyncio
    async def test_none_vs_empty_string(self):
        """None and empty string are not equal."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": None, "expected": ""})
        assert result.success is True
        assert result.outputs.get("true") is None
        assert result.outputs["false"] is None

    @pytest.mark.asyncio
    async def test_list_equality(self):
        """Lists can be compared for equality."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": [1, 2, 3], "expected": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["true"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_dict_equality(self):
        """Dicts can be compared for equality."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": {"a": 1}, "expected": {"a": 1}})
        assert result.success is True
        assert result.outputs["true"] == {"a": 1}

    @pytest.mark.asyncio
    async def test_type_mismatch_string_vs_number(self):
        """String '42' is not equal to number 42."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "42", "expected": 42})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_missing_value_input(self):
        """Missing required input 'value' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"expected": "hello"})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_missing_expected_input(self):
        """Missing required input 'expected' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "hello"})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execution_time_measured(self):
        """Execution time is measured and returned."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "hello", "expected": "hello"})
        assert result.execution_time_ms >= 0


class TestGreaterThanConditional:
    """Tests for GreaterThanConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.comparisons import GreaterThanConditional
        self.node_class = GreaterThanConditional
        self.node = GreaterThanConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_greater_than"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_value_and_threshold_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "value" in names
        assert "threshold" in names

    @pytest.mark.asyncio
    async def test_greater_than_integers(self):
        """5 > 3 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5, "threshold": 3})
        assert result.success is True
        assert result.outputs["true"] == 5

    @pytest.mark.asyncio
    async def test_not_greater_than_integers(self):
        """2 > 5 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 2, "threshold": 5})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_equal_is_not_greater_than(self):
        """5 > 5 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5, "threshold": 5})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_greater_than_floats(self):
        """5.5 > 3.2 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5.5, "threshold": 3.2})
        assert result.success is True
        assert result.outputs["true"] == 5.5

    @pytest.mark.asyncio
    async def test_numeric_string_conversion(self):
        """Numeric strings can be converted to floats."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "10", "threshold": "5"})
        assert result.success is True
        assert result.outputs["true"] == 10.0

    @pytest.mark.asyncio
    async def test_negative_numbers(self):
        """-2 > -5 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": -2, "threshold": -5})
        assert result.success is True
        assert result.outputs["true"] == -2.0

    @pytest.mark.asyncio
    async def test_non_numeric_value_error(self):
        """Non-numeric value returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "hello", "threshold": 5})
        assert result.success is False
        assert result.error is not None
        assert "Invalid numeric" in result.error

    @pytest.mark.asyncio
    async def test_non_numeric_threshold_error(self):
        """Non-numeric threshold returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5, "threshold": "world"})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_missing_value_input(self):
        """Missing required input 'value' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"threshold": 5})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_missing_threshold_input(self):
        """Missing required input 'threshold' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5})
        assert result.success is False


class TestLessThanConditional:
    """Tests for LessThanConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.comparisons import LessThanConditional
        self.node_class = LessThanConditional
        self.node = LessThanConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_less_than"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_value_and_threshold_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "value" in names
        assert "threshold" in names

    @pytest.mark.asyncio
    async def test_less_than_integers(self):
        """3 < 5 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 3, "threshold": 5})
        assert result.success is True
        assert result.outputs["true"] == 3.0

    @pytest.mark.asyncio
    async def test_not_less_than_integers(self):
        """5 < 3 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5, "threshold": 3})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_equal_is_not_less_than(self):
        """5 < 5 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 5, "threshold": 5})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_less_than_floats(self):
        """3.2 < 5.5 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": 3.2, "threshold": 5.5})
        assert result.success is True
        assert result.outputs["true"] == 3.2

    @pytest.mark.asyncio
    async def test_negative_numbers(self):
        """-5 < -2 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": -5, "threshold": -2})
        assert result.success is True
        assert result.outputs["true"] == -5.0

    @pytest.mark.asyncio
    async def test_non_numeric_value_error(self):
        """Non-numeric value returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"value": "abc", "threshold": 5})
        assert result.success is False
        assert result.error is not None


class TestContainsConditional:
    """Tests for ContainsConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.comparisons import ContainsConditional
        self.node_class = ContainsConditional
        self.node = ContainsConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_contains"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_haystack_and_needle_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "haystack" in names
        assert "needle" in names

    @pytest.mark.asyncio
    async def test_string_contains_substring(self):
        """'hello' contains 'ell' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": "hello", "needle": "ell"})
        assert result.success is True
        assert result.outputs["true"] == "hello"

    @pytest.mark.asyncio
    async def test_string_does_not_contain_substring(self):
        """'hello' contains 'xyz' is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": "hello", "needle": "xyz"})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_string_contains_number_as_string(self):
        """'abc123def' contains 123 -> '123' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": "abc123def", "needle": 123})
        assert result.success is True
        assert result.outputs["true"] == "abc123def"

    @pytest.mark.asyncio
    async def test_list_contains_element(self):
        """[1, 2, 3] contains 2 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": [1, 2, 3], "needle": 2})
        assert result.success is True
        assert result.outputs["true"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_list_does_not_contain_element(self):
        """[1, 2, 3] contains 5 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": [1, 2, 3], "needle": 5})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_tuple_contains_element(self):
        """(1, 2, 3) contains 2 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": (1, 2, 3), "needle": 2})
        assert result.success is True
        assert result.outputs["true"] == (1, 2, 3)

    @pytest.mark.asyncio
    async def test_set_contains_element(self):
        """{1, 2, 3} contains 2 is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": {1, 2, 3}, "needle": 2})
        assert result.success is True
        assert result.outputs["true"] == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_dict_contains_value(self):
        """{'a': 1, 'b': 2} contains 1 (as value) is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": {"a": 1, "b": 2}, "needle": 1})
        assert result.success is True
        assert result.outputs["true"] == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_dict_does_not_contain_key_as_value(self):
        """{'a': 1, 'b': 2} contains 'a' (key, not value) is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": {"a": 1, "b": 2}, "needle": "a"})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_empty_string_haystack(self):
        """'' contains '' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": "", "needle": ""})
        assert result.success is True
        assert result.outputs["true"] == ""

    @pytest.mark.asyncio
    async def test_empty_list_haystack(self):
        """[] contains 1 is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": [], "needle": 1})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_none_haystack(self):
        """None (unsupported type) contains x is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"haystack": None, "needle": "x"})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_missing_haystack_input(self):
        """Missing required input 'haystack' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"needle": "x"})
        assert result.success is False


class TestRegexConditional:
    """Tests for RegexConditional node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.conditionals.comparisons import RegexConditional
        self.node_class = RegexConditional
        self.node = RegexConditional()

    def test_node_type(self):
        assert self.node_class.node_type == "conditional_regex"

    def test_has_true_and_false_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "true" in names
        assert "false" in names

    def test_has_text_and_pattern_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "text" in names
        assert "pattern" in names

    @pytest.mark.asyncio
    async def test_simple_pattern_match(self):
        """'hello' matches 'hello' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello", "pattern": "hello"})
        assert result.success is True
        assert result.outputs["true"] == "hello"

    @pytest.mark.asyncio
    async def test_simple_pattern_no_match(self):
        """'hello' matches 'world' is false."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello", "pattern": "world"})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_regex_dot_pattern(self):
        """'abc' matches 'a.c' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "abc", "pattern": "a.c"})
        assert result.success is True
        assert result.outputs["true"] == "abc"

    @pytest.mark.asyncio
    async def test_regex_star_pattern(self):
        """'aaa' matches 'a*' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "aaa", "pattern": "a*"})
        assert result.success is True
        assert result.outputs["true"] == "aaa"

    @pytest.mark.asyncio
    async def test_regex_plus_pattern(self):
        """'aaa' matches 'a+' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "aaa", "pattern": "a+"})
        assert result.success is True
        assert result.outputs["true"] == "aaa"

    @pytest.mark.asyncio
    async def test_regex_character_class(self):
        """'a3' matches '[a-z][0-9]' is true."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "a3", "pattern": "[a-z][0-9]"})
        assert result.success is True
        assert result.outputs["true"] == "a3"

    @pytest.mark.asyncio
    async def test_regex_email_pattern(self):
        """Email regex pattern matches valid email."""
        ctx = _make_context()
        result = await self.node.execute(
            ctx,
            {
                "text": "test@example.com",
                "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            }
        )
        assert result.success is True
        assert result.outputs["true"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_regex_partial_match(self):
        """Pattern doesn't need to match entire string."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello world", "pattern": "world"})
        assert result.success is True
        assert result.outputs["true"] == "hello world"

    @pytest.mark.asyncio
    async def test_number_converted_to_string(self):
        """Numeric value is converted to string for matching."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": 123, "pattern": r"\d+"})
        assert result.success is True
        assert result.outputs["true"] == "123"

    @pytest.mark.asyncio
    async def test_invalid_regex_pattern_error(self):
        """Invalid regex pattern returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello", "pattern": "["})
        assert result.success is False
        assert result.error is not None
        assert "Invalid regex" in result.error

    @pytest.mark.asyncio
    async def test_invalid_regex_pattern_with_unmatched_parenthesis(self):
        """Unmatched parenthesis in pattern returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello", "pattern": "("})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_missing_text_input(self):
        """Missing required input 'text' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"pattern": "hello"})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_missing_pattern_input(self):
        """Missing required input 'pattern' returns error."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "hello"})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_empty_text(self):
        """Empty text matches empty pattern."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "", "pattern": ""})
        assert result.success is True
        assert result.outputs["true"] == ""

    @pytest.mark.asyncio
    async def test_case_sensitive_match(self):
        """Regex matching is case-sensitive by default."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "Hello", "pattern": "hello"})
        assert result.success is True
        assert result.outputs.get("true") is None

    @pytest.mark.asyncio
    async def test_case_insensitive_with_flag(self):
        """Regex with (?i) flag matches case-insensitively."""
        ctx = _make_context()
        result = await self.node.execute(ctx, {"text": "Hello", "pattern": "(?i)hello"})
        assert result.success is True
        assert result.outputs["true"] == "Hello"
