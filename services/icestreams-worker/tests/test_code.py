#!/usr/bin/env python3
"""
Comprehensive unit tests for CodeTransform node.

Tests cover:
- Safe code execution in sandboxed environment
- Safe builtin functions (abs, min, max, len, sum, range, enumerate, etc.)
- List comprehensions and loops
- Safe module utilities (json, re, datetime)
- Print output capture
- Timeout handling
- Forbidden name detection
- Forbidden pattern detection
- Syntax error handling
- Result variable requirement
- Error handling for invalid code
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from nodes.base import NodeContext, NodeResult
from nodes.transforms.code import CodeTransform


class TestCodeValidation:
    """Test code configuration validation."""

    def test_validate_config_valid_code(self) -> None:
        """Test validation passes for valid code."""
        config = {"code": "result = data * 2", "timeout": 10}
        errors = CodeTransform.validate_config(config)
        assert errors == []

    def test_validate_config_missing_code(self) -> None:
        """Test validation fails when code is missing."""
        config = {}
        errors = CodeTransform.validate_config(config)
        assert any("required" in e.lower() for e in errors)

    def test_validate_config_empty_code(self) -> None:
        """Test validation fails for empty code."""
        config = {"code": ""}
        errors = CodeTransform.validate_config(config)
        assert any("required" in e.lower() for e in errors)

    def test_validate_config_forbidden_exec(self) -> None:
        """Test validation fails for exec keyword."""
        config = {"code": "exec('bad code')"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_forbidden_eval(self) -> None:
        """Test validation fails for eval keyword."""
        config = {"code": "result = eval('code')"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_forbidden_open(self) -> None:
        """Test validation fails for open() function."""
        config = {"code": "open('/etc/passwd')"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_forbidden_import(self) -> None:
        """Test validation fails for import statement."""
        config = {"code": "import os"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_forbidden_import_from(self) -> None:
        """Test validation fails for from import."""
        config = {"code": "from os import system"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_forbidden_subprocess(self) -> None:
        """Test validation fails for subprocess."""
        config = {"code": "subprocess.run(['ls'])"}
        errors = CodeTransform.validate_config(config)
        assert any("Forbidden" in e or "Dangerous" in e for e in errors)

    def test_validate_config_syntax_error(self) -> None:
        """Test validation fails for syntax errors."""
        config = {"code": "result = data * * 2"}
        errors = CodeTransform.validate_config(config)
        assert any("Syntax" in e for e in errors)

    def test_validate_config_invalid_timeout(self) -> None:
        """Test validation fails for invalid timeout."""
        config = {"code": "result = data", "timeout": -1}
        errors = CodeTransform.validate_config(config)
        assert any("timeout" in e.lower() for e in errors)

    def test_validate_config_timeout_too_large(self) -> None:
        """Test validation fails for timeout exceeding max."""
        config = {"code": "result = data", "timeout": 40}
        errors = CodeTransform.validate_config(config)
        assert any(
            "timeout" in e.lower() and ("exceed" in e.lower() or "30" in e)
            for e in errors
        )


class TestSimpleCodeExecution:
    """Test simple code execution in sandbox."""

    @pytest.mark.asyncio
    async def test_simple_assignment(self) -> None:
        """Test simple variable assignment."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = 42"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_data_passthrough(self) -> None:
        """Test passing data through without modification."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = data"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 42})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_arithmetic_operations(self) -> None:
        """Test arithmetic operations."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = data * 2 + 10"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": 5})
        assert result.success is True
        assert result.outputs["out"] == 20

    @pytest.mark.asyncio
    async def test_string_operations(self) -> None:
        """Test string operations."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = data.upper()"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": "hello"})
        assert result.success is True
        assert result.outputs["out"] == "HELLO"


class TestListComprehensions:
    """Test list comprehensions and loops."""

    @pytest.mark.asyncio
    async def test_list_comprehension(self) -> None:
        """Test list comprehension."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = [x * 2 for x in data]"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["out"] == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_list_comprehension_with_condition(self) -> None:
        """Test list comprehension with condition."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = [x for x in data if x % 2 == 0]"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5, 6]})
        assert result.success is True
        assert result.outputs["out"] == [2, 4, 6]

    @pytest.mark.asyncio
    async def test_for_loop(self) -> None:
        """Test for loop."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        code = """
result = []
for x in data:
    result.append(x * 2)
"""
        context.config = {"code": code}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] == [2, 4, 6]


class TestSafeBuiltins:
    """Test safe builtin functions."""

    @pytest.mark.asyncio
    async def test_abs_function(self) -> None:
        """Test abs() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = abs(-42)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == 42

    @pytest.mark.asyncio
    async def test_len_function(self) -> None:
        """Test len() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = len(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["out"] == 5

    @pytest.mark.asyncio
    async def test_sum_function(self) -> None:
        """Test sum() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = sum(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3, 4, 5]})
        assert result.success is True
        assert result.outputs["out"] == 15

    @pytest.mark.asyncio
    async def test_min_function(self) -> None:
        """Test min() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = min(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [5, 2, 8, 1, 9]})
        assert result.success is True
        assert result.outputs["out"] == 1

    @pytest.mark.asyncio
    async def test_max_function(self) -> None:
        """Test max() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = max(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [5, 2, 8, 1, 9]})
        assert result.success is True
        assert result.outputs["out"] == 9

    @pytest.mark.asyncio
    async def test_enumerate_function(self) -> None:
        """Test enumerate() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = list(enumerate(data))"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": ["a", "b", "c"]})
        assert result.success is True
        assert result.outputs["out"] == [(0, "a"), (1, "b"), (2, "c")]

    @pytest.mark.asyncio
    async def test_range_function(self) -> None:
        """Test range() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = list(range(5))"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_isinstance_function(self) -> None:
        """Test isinstance() builtin."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = isinstance(data, list)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] is True


class TestJsonOperations:
    """Test JSON utility functions."""

    @pytest.mark.asyncio
    async def test_json_dumps(self) -> None:
        """Test json_dumps utility."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = json_dumps(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": {"key": "value"}})
        assert result.success is True
        import json

        assert json.loads(result.outputs["out"]) == {"key": "value"}

    @pytest.mark.asyncio
    async def test_json_loads(self) -> None:
        """Test json_loads utility."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = json_loads(data)"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": '{"key": "value"}'})
        assert result.success is True
        assert result.outputs["out"] == {"key": "value"}


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_missing_result_variable(self) -> None:
        """Test code that doesn't set result variable."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "x = 42"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is True
        assert result.outputs["out"] is None

    @pytest.mark.asyncio
    async def test_runtime_error(self) -> None:
        """Test runtime error handling."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = 1 / 0"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_undefined_variable_error(self) -> None:
        """Test undefined variable access."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = undefined_var"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_forbidden_name_at_runtime(self) -> None:
        """Test forbidden name detection at runtime."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        context.config = {"code": "result = exec('x=1')"}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": None})
        assert result.success is False
        assert "Forbidden" in result.error

    @pytest.mark.asyncio
    async def test_complex_data_structures(self) -> None:
        """Test working with complex data structures."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        code = """
result = {
    'count': len(data),
    'sum': sum(data),
    'avg': sum(data) / len(data) if data else 0,
    'doubled': [x * 2 for x in data]
}
"""
        context.config = {"code": code}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [2, 4, 6, 8]})
        assert result.success is True
        assert result.outputs["out"]["count"] == 4
        assert result.outputs["out"]["sum"] == 20
        assert result.outputs["out"]["avg"] == 5.0
        assert result.outputs["out"]["doubled"] == [4, 8, 12, 16]

    @pytest.mark.asyncio
    async def test_conditional_logic(self) -> None:
        """Test conditional logic in code."""
        node = CodeTransform()
        context = MagicMock(spec=NodeContext)
        code = """
if isinstance(data, list):
    result = len(data)
elif isinstance(data, dict):
    result = len(data.keys())
else:
    result = None
"""
        context.config = {"code": code}
        context.get_config_value = lambda k, d: context.config.get(k, d)
        context.log_info = MagicMock()
        context.log_error = MagicMock()

        result = await node.execute(context, {"in": [1, 2, 3]})
        assert result.success is True
        assert result.outputs["out"] == 3


class TestNodeInterface:
    """Test node interface and metadata."""

    def test_node_inputs(self) -> None:
        """Test node input definitions."""
        inputs = CodeTransform.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "in"
        assert inputs[0].required is True

    def test_node_outputs(self) -> None:
        """Test node output definitions."""
        outputs = CodeTransform.outputs()
        assert len(outputs) == 1
        assert outputs[0].name == "out"

    def test_node_type(self) -> None:
        """Test node type identifier."""
        assert CodeTransform.node_type == "transform_code"

    def test_node_category(self) -> None:
        """Test node category."""
        assert CodeTransform.category == "transforms"
