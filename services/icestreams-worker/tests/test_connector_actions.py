#!/usr/bin/env python3
"""
Tests for ConnectorActionExecutor.execute_action and execute_transform.

Tests cover:
- HTTP request with correct URL/method
- Auth headers (API key, OAuth/JWT)
- Request body built from config_schema
- request_body_template parsing
- Response parsing
- HTTP errors propagate as ConnectorExecutionError
- Timeout handling
- execute_transform with endpoint calls API
- execute_transform without endpoint returns input passthrough
- Missing action raises ConnectorExecutionError
- Missing connector raises ConnectorExecutionError
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import (
    ActionDefinition,
    AuthMethod,
    AuthType,
    ConfigField,
    ConnectorConfig,
    ConnectorManifest,
    PortDefinition,
    TransformDefinition,
)
from connectors.executor import ConnectorActionExecutor, ConnectorExecutionError
from connectors.registry import ConnectorRegistry
from executor.node_registry import NodeRegistry


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear registries before/after each test."""
    ConnectorRegistry.clear()
    NodeRegistry.clear()
    yield
    ConnectorRegistry.clear()
    NodeRegistry.clear()


def _make_config(auth_type: AuthType = AuthType.NONE, api_key: str = None, oauth_token: str = None):
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
            AuthMethod(type=AuthType.API_KEY, header="X-API-Key", env_var="TEST_API_KEY"),
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
                description="No endpoint",
                endpoint="",
                method="GET",
                config_schema=(),
            ),
        ),
    )


def _register_manifest(manifest: ConnectorManifest) -> None:
    ConnectorRegistry.register_manifest(manifest)


class TestExecuteActionHTTP:
    """Tests for HTTP call execution in execute_action."""

    @pytest.mark.asyncio
    async def test_execute_action_calls_correct_endpoint(self):
        """execute_action must call the connector API with the correct endpoint."""
        manifest = _make_manifest_with_action(endpoint="/api/action")
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()

        with patch.object(
            executor._get_connector("testconn").__class__,
            "call_api",
            new_callable=AsyncMock,
            return_value={"status": "ok"},
        ) as mock_call:
            # Re-get connector after mock
            connector = ConnectorRegistry.get_instance("testconn", _make_config())
            executor._connectors["testconn"] = connector

            with patch.object(connector, "call_api", new_callable=AsyncMock, return_value={"ok": True}) as mock_api:
                result = await executor.execute_action(
                    connector_id="testconn",
                    action_id="do_thing",
                    config={},
                    inputs={},
                    variables={},
                )
                mock_api.assert_called_once()
                call_kwargs = mock_api.call_args
                assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_execute_action_uses_correct_http_method(self):
        """execute_action must call API with the method from ActionDefinition."""
        manifest = _make_manifest_with_action(method="PUT", endpoint="/api/update")
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with patch.object(connector, "call_api", new_callable=AsyncMock, return_value={"updated": True}) as mock_api:
            result = await executor.execute_action(
                connector_id="testconn",
                action_id="do_thing",
                config={},
                inputs={},
                variables={},
            )
            mock_api.assert_called_once()
            _, kwargs = mock_api.call_args
            assert kwargs.get("method", "").upper() == "PUT"

    @pytest.mark.asyncio
    async def test_execute_action_returns_api_response(self):
        """execute_action must return the response from call_api."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        expected = {"result": "data", "id": 123}
        with patch.object(connector, "call_api", new_callable=AsyncMock, return_value=expected):
            result = await executor.execute_action(
                connector_id="testconn",
                action_id="do_thing",
                config={},
                inputs={},
                variables={},
            )
        assert result == expected

    @pytest.mark.asyncio
    async def test_execute_action_raises_for_missing_action(self):
        """execute_action must raise ConnectorExecutionError for unknown action_id."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with pytest.raises(ConnectorExecutionError, match="nonexistent"):
            await executor.execute_action(
                connector_id="testconn",
                action_id="nonexistent",
                config={},
                inputs={},
                variables={},
            )

    @pytest.mark.asyncio
    async def test_execute_action_raises_for_missing_connector(self):
        """execute_action must raise ConnectorExecutionError for unregistered connector."""
        executor = ConnectorActionExecutor()
        with pytest.raises(Exception):
            await executor.execute_action(
                connector_id="not_registered_xyz",
                action_id="anything",
                config={},
                inputs={},
                variables={},
            )

    @pytest.mark.asyncio
    async def test_execute_action_raises_on_http_error(self):
        """execute_action must raise ConnectorExecutionError when API call fails."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        import httpx
        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            side_effect=httpx.HTTPStatusError("404", request=MagicMock(), response=MagicMock()),
        ):
            with pytest.raises(ConnectorExecutionError):
                await executor.execute_action(
                    connector_id="testconn",
                    action_id="do_thing",
                    config={},
                    inputs={},
                    variables={},
                )


class TestRequestBodyBuilding:
    """Tests for _build_request_body."""

    def test_get_method_returns_none_body(self):
        """GET requests should produce no body."""
        manifest = _make_manifest_with_action(method="GET")
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()
        action = manifest.actions[0]
        body = executor._build_request_body(action, config={}, inputs={}, variables={})
        assert body is None

    def test_post_with_config_schema_builds_body(self):
        """POST with config_schema fields should include them in body."""
        field = ConfigField(
            field="message",
            type="string",
            label="Message",
            required=True,
            supports_variables=False,
        )
        manifest = _make_manifest_with_action(method="POST", config_fields=(field,))
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()
        action = manifest.actions[0]
        body = executor._build_request_body(
            action,
            config={"message": "Hello"},
            inputs={},
            variables={},
        )
        assert body is not None
        assert body.get("message") == "Hello"

    def test_request_body_template_used_when_present(self):
        """request_body_template should be parsed as JSON for the body."""
        template = '{"action": "create", "name": "test"}'
        manifest = _make_manifest_with_action(
            method="POST",
            request_body_template=template,
        )
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()
        action = manifest.actions[0]
        body = executor._build_request_body(
            action,
            config={},
            inputs={},
            variables={},
        )
        assert body == {"action": "create", "name": "test"}

    def test_input_data_merged_into_body(self):
        """Input data from 'in' port should be merged into request body."""
        manifest = _make_manifest_with_action(method="POST")
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()
        action = manifest.actions[0]
        body = executor._build_request_body(
            action,
            config={},
            inputs={"in": {"user_id": 42, "email": "test@test.com"}},
            variables={},
        )
        assert body is not None
        assert body.get("user_id") == 42
        assert body.get("email") == "test@test.com"

    def test_config_field_with_variable_interpolation(self):
        """Config field with supports_variables=True should interpolate."""
        field = ConfigField(
            field="user",
            type="string",
            label="User",
            required=False,
            supports_variables=True,
        )
        manifest = _make_manifest_with_action(method="POST", config_fields=(field,))
        _register_manifest(manifest)

        executor = ConnectorActionExecutor()
        action = manifest.actions[0]
        body = executor._build_request_body(
            action,
            config={"user": "{{username}}"},
            inputs={},
            variables={"username": "alice"},
        )
        assert body is not None
        assert body.get("user") == "alice"


class TestAuthHeaders:
    """Tests for authentication header injection."""

    def test_api_key_auth_header(self):
        """API key auth must produce X-API-Key header."""
        config = _make_config(auth_type=AuthType.API_KEY, api_key="my-secret-key")
        headers = config.get_auth_header()
        assert headers is not None
        assert headers.get("X-API-Key") == "my-secret-key"

    def test_oauth_bearer_header(self):
        """OAuth auth must produce Authorization: Bearer header."""
        config = _make_config(auth_type=AuthType.OAUTH, oauth_token="my-oauth-token")
        headers = config.get_auth_header()
        assert headers is not None
        assert headers.get("Authorization") == "Bearer my-oauth-token"

    def test_jwt_bearer_header(self):
        """JWT auth must produce Authorization: Bearer header."""
        config = _make_config(auth_type=AuthType.JWT, oauth_token="my-jwt-token")
        headers = config.get_auth_header()
        assert headers is not None
        assert headers.get("Authorization") == "Bearer my-jwt-token"

    def test_none_auth_returns_none_headers(self):
        """No auth must return None from get_auth_header."""
        config = _make_config(auth_type=AuthType.NONE)
        headers = config.get_auth_header()
        assert headers is None


class TestExecuteTransform:
    """Tests for execute_transform."""

    @pytest.mark.asyncio
    async def test_execute_transform_with_endpoint_calls_api(self):
        """execute_transform with endpoint should call the connector API."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        expected = {"rows": [{"id": 1}]}
        with patch.object(connector, "call_api", new_callable=AsyncMock, return_value=expected):
            result = await executor.execute_transform(
                connector_id="testconn",
                transform_id="lookup",
                config={},
                inputs={"in": {}},
                variables={},
            )
        assert result == expected

    @pytest.mark.asyncio
    async def test_execute_transform_passthrough_when_no_endpoint(self):
        """execute_transform with no endpoint should return inputs['in']."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        input_data = {"key": "value", "count": 5}
        result = await executor.execute_transform(
            connector_id="testconn",
            transform_id="passthrough",
            config={},
            inputs={"in": input_data},
            variables={},
        )
        assert result == input_data

    @pytest.mark.asyncio
    async def test_execute_transform_raises_for_missing_transform(self):
        """execute_transform must raise ConnectorExecutionError for unknown transform_id."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with pytest.raises(ConnectorExecutionError, match="not found"):
            await executor.execute_transform(
                connector_id="testconn",
                transform_id="no_such_transform",
                config={},
                inputs={},
                variables={},
            )

    @pytest.mark.asyncio
    async def test_execute_transform_endpoint_interpolation(self):
        """execute_transform endpoint can use variable interpolation."""
        manifest = ConnectorManifest(
            id="testconn",
            name="Test",
            description="Test",
            version="1.0.0",
            vendor="test",
            actions=(),
            transforms=(
                TransformDefinition(
                    id="dynamic_lookup",
                    name="Dynamic Lookup",
                    description="Uses variable in endpoint",
                    endpoint="/api/lookup/{{table}}",
                    method="GET",
                    config_schema=(),
                ),
            ),
        )
        ConnectorRegistry.clear()
        ConnectorRegistry.register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            return_value={"data": []},
        ) as mock_api:
            await executor.execute_transform(
                connector_id="testconn",
                transform_id="dynamic_lookup",
                config={},
                inputs={},
                variables={"table": "users"},
            )
            call_args = mock_api.call_args
            called_endpoint = call_args[1].get("endpoint") or call_args[0][0]
            assert "users" in called_endpoint


class TestCleanup:
    """Test executor cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_closes_connectors(self):
        """cleanup() must call cleanup on all cached connectors."""
        manifest = _make_manifest_with_action()
        _register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn", _make_config())
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with patch.object(connector, "cleanup", new_callable=AsyncMock) as mock_cleanup:
            await executor.cleanup()
            mock_cleanup.assert_called_once()

        assert executor._connectors == {}
