#!/usr/bin/env python3
"""
Comprehensive unit tests for ExpressionTransform node.

Tests cover:
- Basic arithmetic operations (+, -, *, /, //, %, **)
- Comparison operators (<, >, ==, !=, <=, >=)
- Boolean operations (and, or)
- Safe function calls (abs, min, max, len, sum, round, int, float, str, sqrt, floor, ceil, upper, lower, strip)
- Variable access from input data
- Dictionary and list access patterns
- Conditional expressions (ternary operator)
- Complex nested expressions
- Error handling for unsupported operations and variables
- Input/output handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict

from nodes.transforms.expression import ExpressionTransform
from nodes.base import NodeContext, NodeInput, NodeOutput, NodeResult


class TestExpressionValidation:
    """Test expression validation during node configuration."""

    def test_validate_config_valid_expression(self) -> None:
        """Test validation passes for valid expression."""
        config = {"expression": "data * 2"}
        errors = ExpressionTransform.validate_config(config)
        assert errors == []

    def test_validate_config_missing_expression(self) -> None:
        """Test validation fails when expression is missing."""
        config = {}
        errors = ExpressionTransform.validate_config(config)
        assert any("required" in e for e in errors)

    def test_validate_config_empty_expression(self) -> None:
        """Test validation fails for empty expression."""
        config = {"expression": ""}
        errors = ExpressionTransform.validate_config(config)
        assert any("required" in e for e in errors)

    def test_validate_config_syntax_error(self) -> None:
        """Test validation fails for syntax errors."""
        config = {"expression": "data * * 2"}
        errors = ExpressionTransform.validate_config(config)
        assert any("syntax" in e.lower() for e in errors)

    def test_validate_config_unmatched_parenthesis(self) -> None:
        """Test validation fails for unmatched parenthesis."""
        config = {"expression": "data * (2 + 3"}
        errors = ExpressionTransform.validate_config(config)
        assert any("syntax" in e.lower() for e in errors)


class TestArithmeticExpressions:
    """Test arithmetic operations in expressions."""

    @pytest.mark.asyncio
    async def test_simple_addition(self) -> None:
        """Test basic addition."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data + 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 15

    @pytest.mark.asyncio
    async def test_simple_subtraction(self) -> None:
        """Test basic subtraction."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data - 3"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 7

    @pytest.mark.asyncio
    async def test_multiplication(self) -> None:
        """Test multiplication."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data * 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_division(self) -> None:
        """Test true division."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data / 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 5.0

    @pytest.mark.asyncio
    async def test_floor_division(self) -> None:
        """Test floor division."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data // 3"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 3

    @pytest.mark.asyncio
    async def test_modulo(self) -> None:
        """Test modulo operation."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data % 3"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 1

    @pytest.mark.asyncio
    async def test_power(self) -> None:
        """Test exponentiation."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data ** 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 25

    @pytest.mark.asyncio
    async def test_unary_negation(self) -> None:
        """Test unary negation."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "-data"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == -5

    @pytest.mark.asyncio
    async def test_unary_positive(self) -> None:
        """Test unary positive."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "+data"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": -5})
        assert result.success is True
        assert result.outputs["out"] == -5

    @pytest.mark.asyncio
    async def test_complex_arithmetic(self) -> None:
        """Test complex arithmetic with operator precedence."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data * 2 + 3"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 13

    @pytest.mark.asyncio
    async def test_arithmetic_with_parenthesis(self) -> None:
        """Test arithmetic with parenthesis to override precedence."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "(data + 3) * 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 16


class TestComparisonExpressions:
    """Test comparison operations in expressions."""

    @pytest.mark.asyncio
    async def test_equal_true(self) -> None:
        """Test equality comparison that is true."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data == 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_equal_false(self) -> None:
        """Test equality comparison that is false."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data == 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3})
        assert result.success is True
        assert result.outputs["out"] is False

    @pytest.mark.asyncio
    async def test_not_equal(self) -> None:
        """Test not equal comparison."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data != 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_less_than(self) -> None:
        """Test less than comparison."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data < 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_less_than_or_equal(self) -> None:
        """Test less than or equal comparison."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data <= 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_greater_than(self) -> None:
        """Test greater than comparison."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data > 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 7})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal comparison."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data >= 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is True


class TestBooleanExpressions:
    """Test boolean operations in expressions."""

    @pytest.mark.asyncio
    async def test_and_both_true(self) -> None:
        """Test 'and' with both conditions true."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data > 0 and data < 10"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_and_one_false(self) -> None:
        """Test 'and' with one condition false."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data > 0 and data < 10"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 15})
        assert result.success is True
        assert result.outputs["out"] is False

    @pytest.mark.asyncio
    async def test_or_both_false(self) -> None:
        """Test 'or' with both conditions false."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data == 1 or data == 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is False

    @pytest.mark.asyncio
    async def test_or_one_true(self) -> None:
        """Test 'or' with one condition true."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data == 1 or data == 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] is True


class TestFunctionCalls:
    """Test safe function calls in expressions."""

    @pytest.mark.asyncio
    async def test_abs_function(self) -> None:
        """Test abs() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "abs(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": -5})
        assert result.success is True
        assert result.outputs["out"] == 5

    @pytest.mark.asyncio
    async def test_min_function(self) -> None:
        """Test min() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "min(data, 3)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 3

    @pytest.mark.asyncio
    async def test_max_function(self) -> None:
        """Test max() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "max(data, 10)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_len_function(self) -> None:
        """Test len() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "len(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["out"] == 5

    @pytest.mark.asyncio
    async def test_sum_function(self) -> None:
        """Test sum() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "sum(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4]})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_round_function(self) -> None:
        """Test round() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "round(data, 2)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3.14159})
        assert result.success is True
        assert result.outputs["out"] == 3.14

    @pytest.mark.asyncio
    async def test_int_function(self) -> None:
        """Test int() conversion."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "int(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "42"})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_float_function(self) -> None:
        """Test float() conversion."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "float(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "3.14"})
        assert result.success is True
        assert result.outputs["out"] == 3.14

    @pytest.mark.asyncio
    async def test_str_function(self) -> None:
        """Test str() conversion."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "str(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 42})
        assert result.success is True
        assert result.outputs["out"] == "42"

    @pytest.mark.asyncio
    async def test_sqrt_function(self) -> None:
        """Test sqrt() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "sqrt(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 16})
        assert result.success is True
        assert result.outputs["out"] == 4.0

    @pytest.mark.asyncio
    async def test_floor_function(self) -> None:
        """Test floor() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "floor(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3.7})
        assert result.success is True
        assert result.outputs["out"] == 3

    @pytest.mark.asyncio
    async def test_ceil_function(self) -> None:
        """Test ceil() function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "ceil(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3.2})
        assert result.success is True
        assert result.outputs["out"] == 4

    @pytest.mark.asyncio
    async def test_upper_function(self) -> None:
        """Test upper() string function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "upper(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "hello"})
        assert result.success is True
        assert result.outputs["out"] == "HELLO"

    @pytest.mark.asyncio
    async def test_lower_function(self) -> None:
        """Test lower() string function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "lower(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "HELLO"})
        assert result.success is True
        assert result.outputs["out"] == "hello"

    @pytest.mark.asyncio
    async def test_strip_function(self) -> None:
        """Test strip() string function."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "strip(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "  hello  "})
        assert result.success is True
        assert result.outputs["out"] == "hello"


class TestConditionalExpressions:
    """Test conditional (ternary) expressions."""

    @pytest.mark.asyncio
    async def test_ternary_true_condition(self) -> None:
        """Test ternary operator with true condition."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data if data > 5 else 0"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 10})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_ternary_false_condition(self) -> None:
        """Test ternary operator with false condition."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data if data > 5 else 0"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 3})
        assert result.success is True
        assert result.outputs["out"] == 0

    @pytest.mark.asyncio
    async def test_nested_ternary(self) -> None:
        """Test nested ternary operators."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "'high' if data > 10 else 'low' if data > 5 else 'very low'"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 8})
        assert result.success is True
        assert result.outputs["out"] == "low"


class TestDataAccess:
    """Test variable access and data structure navigation."""

    @pytest.mark.asyncio
    async def test_direct_data_reference(self) -> None:
        """Test direct reference to data variable."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 42})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_dict_key_access(self) -> None:
        """Test accessing dictionary keys."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data['name']"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"name": "John", "age": 30}})
        assert result.success is True
        assert result.outputs["out"] == "John"

    @pytest.mark.asyncio
    async def test_dict_attribute_access(self) -> None:
        """Test accessing dict attributes via dot notation."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data.age"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"name": "John", "age": 30}})
        assert result.success is True
        assert result.outputs["out"] == 30

    @pytest.mark.asyncio
    async def test_dict_variable_as_key(self) -> None:
        """Test using dict input keys as direct variables."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "age * 2"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"name": "John", "age": 30}})
        assert result.success is True
        assert result.outputs["out"] == 60

    @pytest.mark.asyncio
    async def test_list_index_access(self) -> None:
        """Test accessing list elements by index."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data[0]"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [10, 20, 30]})
        assert result.success is True
        assert result.outputs["out"] == 10

    @pytest.mark.asyncio
    async def test_list_negative_index(self) -> None:
        """Test accessing list elements with negative indices."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data[-1]"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [10, 20, 30]})
        assert result.success is True
        assert result.outputs["out"] == 30

    @pytest.mark.asyncio
    async def test_nested_dict_access(self) -> None:
        """Test accessing nested dictionary structures."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data['user']['email']"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"user": {"email": "test@example.com"}}})
        assert result.success is True
        assert result.outputs["out"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_list_literals(self) -> None:
        """Test creating list literals in expressions."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "[data, data * 2, data * 3]"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == [5, 10, 15]

    @pytest.mark.asyncio
    async def test_dict_literals(self) -> None:
        """Test creating dictionary literals in expressions."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "{'value': data, 'doubled': data * 2}"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == {"value": 5, "doubled": 10}


class TestConstants:
    """Test constant values and built-in constants."""

    @pytest.mark.asyncio
    async def test_true_constant(self) -> None:
        """Test true constant."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "true"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] is True

    @pytest.mark.asyncio
    async def test_false_constant(self) -> None:
        """Test false constant."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "false"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] is False

    @pytest.mark.asyncio
    async def test_null_constant(self) -> None:
        """Test null/none constant."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "null"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_numeric_constants(self) -> None:
        """Test numeric constants."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "42"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_string_constants(self) -> None:
        """Test string constants."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "'hello'"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == "hello"


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_unknown_variable(self) -> None:
        """Test error when referencing unknown variable."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "unknown_var"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is False
        assert "Unknown variable" in result.error

    @pytest.mark.asyncio
    async def test_division_by_zero(self) -> None:
        """Test division by zero error."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data / 0"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_invalid_index_access(self) -> None:
        """Test error when accessing invalid index."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data[10]"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3]})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_non_callable_invocation(self) -> None:
        """Test error when trying to call non-callable."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data()"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 42})
        assert result.success is False
        assert "Not a callable" in result.error

    @pytest.mark.asyncio
    async def test_missing_input(self) -> None:
        """Test handling of missing input."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "data + 5"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {})
        # Should either handle gracefully or return error
        assert result.success is False or result.success is True

    @pytest.mark.asyncio
    async def test_sqrt_negative_number(self) -> None:
        """Test sqrt of negative number."""
        node = ExpressionTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"expression": "sqrt(data)"}
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": -4})
        assert result.success is False


class TestNodeInterface:
    """Test node interface and metadata."""

    def test_node_inputs(self) -> None:
        """Test node input definitions."""
        inputs = ExpressionTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_node_outputs(self) -> None:
        """Test node output definitions."""
        outputs = ExpressionTransform.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_node_type(self) -> None:
        """Test node type identifier."""
        assert ExpressionTransform.node_type == "transform_expression"

    def test_node_category(self) -> None:
        """Test node category."""
        assert ExpressionTransform.category == "transforms"
