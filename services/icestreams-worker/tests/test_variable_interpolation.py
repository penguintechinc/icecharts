#!/usr/bin/env python3
"""
Tests for variable interpolation in ConnectorActionExecutor._interpolate_value.

Tests cover:
- {{input.field}} syntax
- {{config.field}} syntax
- {{variable}} direct variable name
- Dotted paths ({{input.user.name}})
- Missing variable keeps placeholder
- Empty string resolves
- Nested dict in inputs
- List processing via _interpolate_dict
- Mixed text and variable
- SQL injection remains string
- None handling (returns empty string)
- Multiple variables in one string
- input.in nested access
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.executor import ConnectorActionExecutor


@pytest.fixture
def executor():
    """Create a fresh ConnectorActionExecutor."""
    return ConnectorActionExecutor()


class TestInputInterpolation:
    """{{input.field}} and direct input access."""

    def test_input_dot_field_access(self, executor):
        """{{input.field}} must resolve from inputs dict using 'field' key."""
        result = executor._interpolate_value(
            "Hello {{input.name}}",
            inputs={"name": "World"},
            variables={},
            config={},
        )
        assert result == "Hello World"

    def test_input_dot_nested_field(self, executor):
        """{{input.user.email}} must resolve nested input field."""
        result = executor._interpolate_value(
            "Email: {{input.user.email}}",
            inputs={"user": {"email": "test@example.com"}},
            variables={},
            config={},
        )
        assert result == "Email: test@example.com"

    def test_direct_input_key_access(self, executor):
        """{{field}} where field is a top-level inputs key should resolve."""
        result = executor._interpolate_value(
            "{{name}}",
            inputs={"name": "Alice"},
            variables={},
            config={},
        )
        assert result == "Alice"

    def test_in_nested_field_from_input(self, executor):
        """{{field}} where field exists in inputs['in'] dict."""
        result = executor._interpolate_value(
            "Value: {{user_id}}",
            inputs={"in": {"user_id": "abc123"}},
            variables={},
            config={},
        )
        assert result == "Value: abc123"


class TestConfigInterpolation:
    """{{config.field}} syntax."""

    def test_config_dot_field(self, executor):
        """{{config.table}} must resolve from config dict."""
        result = executor._interpolate_value(
            "SELECT * FROM {{config.table}}",
            inputs={},
            variables={},
            config={"table": "users"},
        )
        assert result == "SELECT * FROM users"

    def test_config_dot_nested_field(self, executor):
        """{{config.db.host}} must resolve nested config path."""
        result = executor._interpolate_value(
            "Host: {{config.db.host}}",
            inputs={},
            variables={},
            config={"db": {"host": "localhost"}},
        )
        assert result == "Host: localhost"

    def test_config_field_direct_access(self, executor):
        """{{key}} falling through to config lookup if in config."""
        result = executor._interpolate_value(
            "Endpoint: {{base_path}}",
            inputs={},
            variables={},
            config={"base_path": "/api/v1"},
        )
        assert result == "Endpoint: /api/v1"


class TestVariableInterpolation:
    """{{variable}} from workflow variables dict."""

    def test_variable_resolution(self, executor):
        """{{var}} must resolve from variables dict."""
        result = executor._interpolate_value(
            "Token: {{auth_token}}",
            inputs={},
            variables={"auth_token": "Bearer abc"},
            config={},
        )
        assert result == "Token: Bearer abc"

    def test_variable_takes_precedence_over_config_for_direct_key(self, executor):
        """If key is in both variables and config, variables wins for direct access."""
        result = executor._interpolate_value(
            "{{env}}",
            inputs={},
            variables={"env": "production"},
            config={"env": "staging"},
        )
        # inputs checked first, then variables — since "env" is in variables it resolves
        assert result == "production"


class TestMissingVariable:
    """Missing variables must keep the placeholder unchanged."""

    def test_missing_variable_keeps_placeholder(self, executor):
        """{{missing_var}} with no match should remain literally."""
        result = executor._interpolate_value(
            "Hello {{missing_var}}",
            inputs={},
            variables={},
            config={},
        )
        assert result == "Hello {{missing_var}}"

    def test_missing_nested_path_keeps_placeholder(self, executor):
        """{{input.nonexistent.deep}} with no match should remain."""
        result = executor._interpolate_value(
            "{{input.nonexistent.deep}}",
            inputs={},
            variables={},
            config={},
        )
        assert result == "{{input.nonexistent.deep}}"

    def test_partial_path_missing_keeps_placeholder(self, executor):
        """{{input.user.email}} when user exists but email doesn't."""
        result = executor._interpolate_value(
            "{{input.user.email}}",
            inputs={"user": {"name": "Alice"}},
            variables={},
            config={},
        )
        assert result == "{{input.user.email}}"


class TestEdgeCases:
    """Edge cases and special inputs."""

    def test_non_string_value_passthrough(self, executor):
        """Non-string values must be returned as-is without interpolation."""
        result = executor._interpolate_value(
            42,
            inputs={},
            variables={},
            config={},
        )
        assert result == 42

    def test_none_value_passthrough(self, executor):
        """None values must be returned as-is."""
        result = executor._interpolate_value(
            None,
            inputs={},
            variables={},
            config={},
        )
        assert result is None

    def test_empty_string_interpolation(self, executor):
        """Empty string input should return empty string."""
        result = executor._interpolate_value(
            "",
            inputs={},
            variables={},
            config={},
        )
        assert result == ""

    def test_none_variable_value_resolves_to_empty_string(self, executor):
        """A variable with value None should resolve to empty string."""
        result = executor._interpolate_value(
            "Value: {{myvar}}",
            inputs={},
            variables={"myvar": None},
            config={},
        )
        assert result == "Value: "

    def test_integer_variable_converts_to_string(self, executor):
        """Integer variable values should convert to string."""
        result = executor._interpolate_value(
            "Count: {{count}}",
            inputs={},
            variables={"count": 42},
            config={},
        )
        assert result == "Count: 42"

    def test_multiple_vars_in_one_string(self, executor):
        """Multiple {{var}} placeholders in one string should all resolve."""
        result = executor._interpolate_value(
            "{{first}} and {{second}}",
            inputs={},
            variables={"first": "Alice", "second": "Bob"},
            config={},
        )
        assert result == "Alice and Bob"

    def test_mixed_text_and_variable(self, executor):
        """String with both literal text and variable should resolve correctly."""
        result = executor._interpolate_value(
            "Welcome to {{app_name}}, version {{version}}!",
            inputs={},
            variables={"app_name": "IceCharts", "version": "1.0"},
            config={},
        )
        assert result == "Welcome to IceCharts, version 1.0!"

    def test_sql_injection_remains_string(self, executor):
        """SQL injection attempts should remain as literal strings (no execution)."""
        malicious = "{{table_name}}"
        result = executor._interpolate_value(
            malicious,
            inputs={},
            variables={"table_name": "users; DROP TABLE users; --"},
            config={},
        )
        # The value is interpolated as a string - no execution occurs
        assert result == "users; DROP TABLE users; --"

    def test_no_double_brace_in_result(self, executor):
        """Resolved variables must not contain braces from template syntax."""
        result = executor._interpolate_value(
            "{{greeting}}",
            inputs={},
            variables={"greeting": "Hello World"},
            config={},
        )
        assert "{{" not in result
        assert "}}" not in result


class TestDictInterpolation:
    """_interpolate_dict must recursively interpolate all string values."""

    def test_flat_dict_interpolation(self, executor):
        """All string values in a flat dict should be interpolated."""
        data = {"key1": "{{var1}}", "key2": "{{var2}}"}
        result = executor._interpolate_dict(
            data,
            inputs={},
            variables={"var1": "value1", "var2": "value2"},
            config={},
        )
        assert result == {"key1": "value1", "key2": "value2"}

    def test_nested_dict_interpolation(self, executor):
        """Nested dict values should be recursively interpolated."""
        data = {"outer": {"inner": "{{myval}}"}}
        result = executor._interpolate_dict(
            data,
            inputs={},
            variables={"myval": "resolved"},
            config={},
        )
        assert result["outer"]["inner"] == "resolved"

    def test_list_values_in_dict_interpolated(self, executor):
        """List of string values in a dict should be interpolated."""
        data = {"items": ["{{item1}}", "{{item2}}"]}
        result = executor._interpolate_dict(
            data,
            inputs={},
            variables={"item1": "first", "item2": "second"},
            config={},
        )
        assert result["items"] == ["first", "second"]

    def test_non_string_values_preserved(self, executor):
        """Non-string values in dict should be preserved unchanged."""
        data = {"count": 42, "active": True, "ratio": 3.14}
        result = executor._interpolate_dict(
            data,
            inputs={},
            variables={},
            config={},
        )
        assert result["count"] == 42
        assert result["active"] is True
        assert result["ratio"] == 3.14
