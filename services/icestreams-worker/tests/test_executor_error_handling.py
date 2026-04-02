#!/usr/bin/env python3
"""
Additional tests for ConnectorActionExecutor error handling and edge cases.

Tests cover:
- Missing connector error handling
- Request body building edge cases
- Empty config schema handling
- JSON parsing failures in request body templates
- Connector cleanup on errors
- Variable interpolation edge cases
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import (ActionDefinition, AuthMethod, AuthType,
                             ConfigField, ConnectorConfig, ConnectorManifest,
                             PortDefinition, TransformDefinition)
from connectors.executor import (ConnectorActionExecutor,
                                 ConnectorExecutionError)
from connectors.registry import ConnectorNotFoundError, ConnectorRegistry
from executor.node_registry import NodeRegistry


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear registries before/after each test."""
    ConnectorRegistry.clear()
    NodeRegistry.clear()
    yield
    ConnectorRegistry.clear()
    NodeRegistry.clear()


def _make_config(
    auth_type: AuthType = AuthType.NONE, api_key: str = None, oauth_token: str = None
):
    return ConnectorConfig(
        connector_id="testconn",
        base_url="http://localhost:9000",
        auth_type=auth_type,
        api_key=api_key,
        oauth_token=oauth_token,
    )


def _make_manifest_with_action(
    action_id: str = "do_thing",
    method: str = "POST",
    endpoint: str = "/api/action",
    config_fields: tuple = (),
    request_body_template: str = "",
) -> ConnectorManifest:
    return ConnectorManifest(
        id="testconn",
        name="Test Connector",
        description="Test",
        version="1.0.0",
        vendor="test",
        auth_methods=(
            AuthMethod(
                type=AuthType.API_KEY, header="X-API-Key", env_var="TEST_API_KEY"
            ),
        ),
        actions=(
            ActionDefinition(
                id=action_id,
                name="Do Thing",
                description="Does a thing",
                endpoint=endpoint,
                method=method,
                config_schema=config_fields,
                request_body_template=request_body_template,
            ),
        ),
        transforms=(
            TransformDefinition(
                id="lookup",
                name="Lookup",
                description="Data lookup",
                endpoint="/api/lookup",
                method="GET",
                config_schema=(),
            ),
            TransformDefinition(
                id="passthrough",
                name="Passthrough",
                description="Pass through",
                endpoint="",
                method="GET",
                config_schema=(),
            ),
        ),
    )


class TestConnectorExecutorErrorHandling:
    """Tests for error handling in ConnectorActionExecutor."""

    def test_missing_connector_raises_not_found_error(self):
        """Attempting to use non-existent connector raises ConnectorNotFoundError."""
        executor = ConnectorActionExecutor()

        with pytest.raises(ConnectorNotFoundError):
            executor._get_connector("nonexistent_connector")

    def test_interpolate_value_with_missing_nested_path_keeps_original(self):
        """Missing nested path in interpolation keeps original placeholder."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{user.profile.name}}",
            inputs={},
            variables={},
            config={},
        )

        # Should keep original when path not found
        assert result == "{{user.profile.name}}"

    def test_interpolate_value_with_non_dict_navigation_keeps_original(self):
        """Attempting to navigate through non-dict value keeps original."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{scalar.nested}}",
            inputs={"scalar": "string_value"},
            variables={},
            config={},
        )

        # Should keep original when can't navigate through non-dict
        assert result == "{{scalar.nested}}"

    def test_interpolate_dict_with_empty_dict_returns_empty_dict(self):
        """Interpolating empty dict returns empty dict."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_dict(
            {},
            inputs={},
            variables={},
            config={},
        )

        assert result == {}

    def test_interpolate_dict_with_mixed_types(self):
        """Dict interpolation preserves non-string types."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_dict(
            {
                "items": [
                    {"name": "item1"},
                    "plain_string",
                    42,
                    True,
                    None,
                ]
            },
            inputs={},
            variables={},
            config={},
        )

        assert result["items"][0]["name"] == "item1"
        assert result["items"][1] == "plain_string"
        assert result["items"][2] == 42
        assert result["items"][3] is True
        assert result["items"][4] is None

    def test_build_request_body_for_get_returns_none(self):
        """GET requests have no body."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "GET"

        result = executor._build_request_body(mock_action, {}, {}, {})
        assert result is None

    def test_build_request_body_for_head_returns_none(self):
        """HEAD requests have no body."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "HEAD"

        result = executor._build_request_body(mock_action, {}, {}, {})
        assert result is None

    def test_build_request_body_for_options_returns_none(self):
        """OPTIONS requests have no body."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "OPTIONS"

        result = executor._build_request_body(mock_action, {}, {}, {})
        assert result is None

    def test_build_request_body_with_invalid_json_template_logs_warning(self):
        """Invalid JSON in template logs warning and falls back to schema."""
        executor = ConnectorActionExecutor()

        mock_field = MagicMock(spec=ConfigField)
        mock_field.field = "message"
        mock_field.supports_variables = False

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "POST"
        mock_action.request_body_template = "{invalid json"
        mock_action.config_schema = (mock_field,)

        with patch("connectors.executor.logger") as mock_logger:
            result = executor._build_request_body(
                mock_action,
                config={"message": "hello"},
                inputs={},
                variables={},
            )

            mock_logger.warning.assert_called()
            assert result == {"message": "hello"}

    def test_build_request_body_with_empty_config_and_no_input_returns_none(self):
        """Empty config and no input data returns None."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "POST"
        mock_action.request_body_template = None
        mock_action.config_schema = ()

        result = executor._build_request_body(
            mock_action,
            config={},
            inputs={},
            variables={},
        )

        assert result is None

    def test_build_request_body_merges_input_data_into_body(self):
        """Input data is merged into request body."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "POST"
        mock_action.request_body_template = None
        mock_action.config_schema = ()

        result = executor._build_request_body(
            mock_action,
            config={},
            inputs={"in": {"key": "value"}},
            variables={},
        )

        assert result == {"key": "value"}

    def test_build_request_body_wraps_non_dict_input_data(self):
        """Non-dict input data is wrapped in 'data' key."""
        executor = ConnectorActionExecutor()

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "POST"
        mock_action.request_body_template = None
        mock_action.config_schema = ()

        result = executor._build_request_body(
            mock_action,
            config={},
            inputs={"in": "scalar_value"},
            variables={},
        )

        assert result == {"data": "scalar_value"}

    def test_build_request_body_doesnt_override_config_with_input(self):
        """Config values are not overridden by input data."""
        executor = ConnectorActionExecutor()

        mock_field = MagicMock(spec=ConfigField)
        mock_field.field = "id"
        mock_field.supports_variables = False

        mock_action = MagicMock(spec=ActionDefinition)
        mock_action.method = "POST"
        mock_action.request_body_template = None
        mock_action.config_schema = (mock_field,)

        result = executor._build_request_body(
            mock_action,
            config={"id": "config_value"},
            inputs={"in": {"id": "input_value"}},
            variables={},
        )

        # Config value takes precedence
        assert result["id"] == "config_value"

    @pytest.mark.asyncio
    async def test_cleanup_clears_cache(self):
        """Cleanup method clears connector cache."""
        executor = ConnectorActionExecutor()
        mock_connector = MagicMock()
        mock_connector.cleanup = AsyncMock()

        executor._connectors["test"] = mock_connector

        await executor.cleanup()

        assert len(executor._connectors) == 0
        mock_connector.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_is_idempotent(self):
        """Calling cleanup multiple times is safe."""
        executor = ConnectorActionExecutor()

        # Should not raise
        await executor.cleanup()
        await executor.cleanup()

    def test_interpolate_value_with_config_prefix(self):
        """{{config.field}} syntax accesses config dict."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{config.api_url}}",
            inputs={},
            variables={},
            config={"api_url": "https://api.example.com"},
        )

        assert result == "https://api.example.com"

    def test_interpolate_value_with_input_prefix(self):
        """{{input.field}} syntax accesses inputs dict."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{input.data}}",
            inputs={"data": "test_data"},
            variables={},
            config={},
        )

        assert result == "test_data"

    def test_interpolate_value_with_nested_config_field(self):
        """{{config.nested.field}} accesses nested config."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{config.auth.token}}",
            inputs={},
            variables={},
            config={"auth": {"token": "secret123"}},
        )

        assert result == "secret123"

    def test_interpolate_value_with_none_result_becomes_empty_string(self):
        """None values in interpolation become empty strings."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "Value: {{config.value}}",
            inputs={},
            variables={},
            config={"value": None},
        )

        assert result == "Value: "

    def test_interpolate_value_from_variables(self):
        """Variables are checked as fallback after inputs/config."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{myvar}}",
            inputs={},
            variables={"myvar": "from_variables"},
            config={},
        )

        assert result == "from_variables"

    def test_interpolate_value_with_multiple_placeholders(self):
        """Multiple placeholders in one string are all interpolated."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "Hello {{input.name}}, your ID is {{config.user_id}}",
            inputs={"name": "Alice"},
            variables={},
            config={"user_id": "123"},
        )

        assert result == "Hello Alice, your ID is 123"

    def test_interpolate_value_respects_input_over_variable(self):
        """Input keys take precedence over variable keys."""
        executor = ConnectorActionExecutor()

        result = executor._interpolate_value(
            "{{user}}",
            inputs={"user": "from_input"},
            variables={"user": "from_variables"},
            config={},
        )

        assert result == "from_input"

    def test_multiple_executor_instances_independent(self):
        """Multiple executor instances have independent caches."""
        executor1 = ConnectorActionExecutor()
        executor2 = ConnectorActionExecutor()

        mock_conn = MagicMock()
        executor1._connectors["test"] = mock_conn

        assert "test" in executor1._connectors
        assert "test" not in executor2._connectors
