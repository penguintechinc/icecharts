#!/usr/bin/env python3
"""
Tests for BaseConnector.call_api retry logic and ConnectorActionExecutor integration.

Tests cover:
- call_api succeeds on first attempt
- call_api retries on 429 rate-limited response and succeeds on second attempt
- call_api retries on 500 server error and succeeds on second attempt
- call_api retries on httpx.RequestError and succeeds on second attempt
- call_api raises after max_retries exhausted (429)
- call_api raises after max_retries exhausted (5xx)
- call_api raises immediately on 4xx client errors (no retry)
- call_api builds auth headers for API key auth
- call_api builds auth headers for OAuth/JWT auth
- call_api passes query params on GET requests
- call_api passes JSON body on POST requests
- validate_connection returns True on successful health check
- validate_connection returns False on exception
- _create_config_from_env reads credentials from environment
- get_trigger, get_action, get_transform return correct definition or None
- ConnectorActionExecutor caches connector instances
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.base import (ActionDefinition, AuthMethod, AuthType,
                             ConfigField, ConnectorConfig, ConnectorManifest,
                             PortDefinition, TransformDefinition,
                             TriggerDefinition)
from connectors.executor import (ConnectorActionExecutor,
                                 ConnectorExecutionError)
from connectors.registry import ConnectorRegistry
from executor.node_registry import NodeRegistry

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_registries():
    """Clear registries before/after each test."""
    ConnectorRegistry.clear()
    NodeRegistry.clear()
    yield
    ConnectorRegistry.clear()
    NodeRegistry.clear()


def _make_manifest(
    connector_id: str = "testconn",
    max_retries: int = 3,
    auth_type: AuthType = AuthType.API_KEY,
) -> ConnectorManifest:
    """Return a minimal manifest for a connector."""
    return ConnectorManifest(
        id=connector_id,
        name="Test Connector",
        description="Test",
        version="1.0.0",
        vendor="test",
        default_url="http://localhost:9000",
        auth_methods=(
            AuthMethod(
                type=auth_type,
                header=(
                    "X-API-Key" if auth_type == AuthType.API_KEY else "Authorization"
                ),
                env_var="TEST_CRED",
            ),
        ),
        actions=(
            ActionDefinition(
                id="do_thing",
                name="Do Thing",
                description="Does a thing",
                endpoint="/api/action",
                method="POST",
            ),
        ),
        transforms=(
            TransformDefinition(
                id="lookup",
                name="Lookup",
                description="Data lookup",
                endpoint="/api/lookup",
                method="GET",
            ),
        ),
        triggers=(
            TriggerDefinition(
                id="on_event",
                name="On Event",
                description="Webhook trigger",
                webhook_path="/webhooks/event",
            ),
        ),
    )


def _make_connector_with_retries(max_retries: int = 3):
    """Register manifest and return a connector instance with custom retry count."""
    manifest = _make_manifest()
    ConnectorRegistry.register_manifest(manifest)
    connector = ConnectorRegistry.get_instance("testconn")
    connector.config.max_retries = max_retries
    return connector


def _make_http_status_error(status_code: int) -> httpx.HTTPStatusError:
    """Create an httpx.HTTPStatusError with the given status code."""
    mock_request = MagicMock(spec=httpx.Request)
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    return httpx.HTTPStatusError(
        f"HTTP {status_code}",
        request=mock_request,
        response=mock_response,
    )


# ---------------------------------------------------------------------------
# TestCallApiSuccess
# ---------------------------------------------------------------------------


class TestCallApiSuccess:
    """Tests for successful call_api execution."""

    @pytest.mark.asyncio
    async def test_call_api_returns_json_response(self):
        """call_api returns parsed JSON on success."""
        connector = _make_connector_with_retries()
        expected = {"status": "ok", "id": 42}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=expected)

        with patch.object(
            connector,
            "_get_client",
            new_callable=AsyncMock,
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await connector.call_api(
                "/api/action", method="POST", body={"x": 1}
            )

        assert result == expected
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_api_sends_auth_header_for_api_key(self):
        """call_api includes X-API-Key header when auth_type is API_KEY."""
        connector = _make_connector_with_retries()
        connector.config.auth_type = AuthType.API_KEY
        connector.config.api_key = "my-secret"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={})

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await connector.call_api("/api/test", method="GET")

        _, kwargs = mock_client.request.call_args
        headers = kwargs.get("headers", {})
        assert headers.get("X-API-Key") == "my-secret"

    @pytest.mark.asyncio
    async def test_call_api_sends_bearer_header_for_oauth(self):
        """call_api includes Authorization: Bearer header when auth_type is OAUTH."""
        connector = _make_connector_with_retries()
        connector.config.auth_type = AuthType.OAUTH
        connector.config.oauth_token = "my-token"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={})

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await connector.call_api("/api/test", method="GET")

        _, kwargs = mock_client.request.call_args
        headers = kwargs.get("headers", {})
        assert headers.get("Authorization") == "Bearer my-token"

    @pytest.mark.asyncio
    async def test_call_api_passes_query_params(self):
        """call_api forwards query params to HTTP client."""
        connector = _make_connector_with_retries()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=[])

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await connector.call_api(
                "/api/search", method="GET", params={"q": "test", "limit": 10}
            )

        _, kwargs = mock_client.request.call_args
        assert kwargs.get("params") == {"q": "test", "limit": 10}

    @pytest.mark.asyncio
    async def test_call_api_passes_json_body(self):
        """call_api forwards request body as JSON."""
        connector = _make_connector_with_retries()
        body = {"name": "Alice", "role": "admin"}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"created": True})

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await connector.call_api("/api/users", method="POST", body=body)

        _, kwargs = mock_client.request.call_args
        assert kwargs.get("json") == body

    @pytest.mark.asyncio
    async def test_call_api_merges_extra_headers(self):
        """call_api merges caller-supplied headers with auth headers."""
        connector = _make_connector_with_retries()
        connector.config.auth_type = AuthType.API_KEY
        connector.config.api_key = "sec"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={})

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            await connector.call_api(
                "/api/test",
                method="GET",
                headers={"X-Custom": "value"},
            )

        _, kwargs = mock_client.request.call_args
        headers = kwargs.get("headers", {})
        assert headers.get("X-API-Key") == "sec"
        assert headers.get("X-Custom") == "value"


# ---------------------------------------------------------------------------
# TestCallApiRetries
# ---------------------------------------------------------------------------


class TestCallApiRetries:
    """Tests for call_api retry logic on rate-limits, server errors, and network errors."""

    @pytest.mark.asyncio
    async def test_call_api_retries_on_429_and_succeeds(self):
        """call_api retries when the server returns 429 and succeeds on second attempt."""
        connector = _make_connector_with_retries(max_retries=3)

        ok_response = MagicMock()
        ok_response.raise_for_status = MagicMock()
        ok_response.json = MagicMock(return_value={"ok": True})

        rate_limited_error = _make_http_status_error(429)
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise rate_limited_error
            return ok_response

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock_get_client.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await connector.call_api("/api/action", method="POST")

        assert result == {"ok": True}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_call_api_retries_on_500_and_succeeds(self):
        """call_api retries when the server returns 500 and succeeds on second attempt."""
        connector = _make_connector_with_retries(max_retries=3)

        ok_response = MagicMock()
        ok_response.raise_for_status = MagicMock()
        ok_response.json = MagicMock(return_value={"data": "value"})

        server_error = _make_http_status_error(500)
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise server_error
            return ok_response

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock_get_client.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await connector.call_api("/api/action", method="GET")

        assert result == {"data": "value"}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_call_api_retries_on_request_error_and_succeeds(self):
        """call_api retries on httpx.RequestError (network failure) and succeeds."""
        connector = _make_connector_with_retries(max_retries=3)

        ok_response = MagicMock()
        ok_response.raise_for_status = MagicMock()
        ok_response.json = MagicMock(return_value={"reconnected": True})

        network_error = httpx.ConnectError("Connection refused")
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise network_error
            return ok_response

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock_get_client.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await connector.call_api("/api/action", method="POST")

        assert result == {"reconnected": True}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_call_api_raises_after_max_retries_429(self):
        """call_api raises after all retries are exhausted on persistent 429."""
        connector = _make_connector_with_retries(max_retries=2)
        rate_limited_error = _make_http_status_error(429)

        async def always_rate_limited(*args, **kwargs):
            raise rate_limited_error

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = always_rate_limited
            mock_get_client.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(httpx.HTTPStatusError):
                    await connector.call_api("/api/action", method="POST")

    @pytest.mark.asyncio
    async def test_call_api_raises_after_max_retries_500(self):
        """call_api raises after all retries are exhausted on persistent 500."""
        connector = _make_connector_with_retries(max_retries=2)
        server_error = _make_http_status_error(500)

        async def always_server_error(*args, **kwargs):
            raise server_error

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = always_server_error
            mock_get_client.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(httpx.HTTPStatusError):
                    await connector.call_api("/api/action", method="GET")

    @pytest.mark.asyncio
    async def test_call_api_raises_immediately_on_4xx_client_error(self):
        """call_api does NOT retry on 4xx client errors (except 429)."""
        connector = _make_connector_with_retries(max_retries=3)
        not_found_error = _make_http_status_error(404)
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise not_found_error

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock_get_client.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await connector.call_api("/api/missing", method="GET")

        # Should have only been called once — no retry on client errors
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_call_api_raises_immediately_on_401_unauthorized(self):
        """call_api does NOT retry on 401 Unauthorized."""
        connector = _make_connector_with_retries(max_retries=3)
        auth_error = _make_http_status_error(401)
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise auth_error

        with patch.object(
            connector, "_get_client", new_callable=AsyncMock
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock_get_client.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError):
                await connector.call_api("/api/secret", method="GET")

        assert call_count == 1


# ---------------------------------------------------------------------------
# TestValidateConnection
# ---------------------------------------------------------------------------


class TestValidateConnection:
    """Tests for BaseConnector.validate_connection."""

    @pytest.mark.asyncio
    async def test_validate_connection_returns_true_on_success(self):
        """validate_connection returns True when health endpoint responds."""
        connector = _make_connector_with_retries()

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            return_value={"status": "ok"},
        ):
            result = await connector.validate_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_returns_false_on_exception(self):
        """validate_connection returns False when the call raises."""
        connector = _make_connector_with_retries()

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await connector.validate_connection()

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_connection_uses_health_endpoint(self):
        """validate_connection calls the manifest health_endpoint."""
        manifest = ConnectorManifest(
            id="hc_conn",
            name="HC Connector",
            description="Test",
            version="1.0.0",
            vendor="test",
            default_url="http://localhost:9000",
            health_endpoint="/custom/health",
        )
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("hc_conn")

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ) as mock_call:
            await connector.validate_connection()

        mock_call.assert_called_once_with("/custom/health", method="GET")


# ---------------------------------------------------------------------------
# TestGetDefinitionHelpers
# ---------------------------------------------------------------------------


class TestGetDefinitionHelpers:
    """Tests for get_trigger, get_action, get_transform helpers."""

    def test_get_trigger_returns_definition_by_id(self):
        """get_trigger returns the TriggerDefinition matching the given id."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        trigger = connector.get_trigger("on_event")
        assert trigger is not None
        assert trigger.id == "on_event"

    def test_get_trigger_returns_none_for_unknown_id(self):
        """get_trigger returns None when trigger_id is not found."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        result = connector.get_trigger("no_such_trigger")
        assert result is None

    def test_get_action_returns_definition_by_id(self):
        """get_action returns the ActionDefinition matching the given id."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        action = connector.get_action("do_thing")
        assert action is not None
        assert action.id == "do_thing"

    def test_get_action_returns_none_for_unknown_id(self):
        """get_action returns None when action_id is not found."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        result = connector.get_action("no_such_action")
        assert result is None

    def test_get_transform_returns_definition_by_id(self):
        """get_transform returns the TransformDefinition matching the given id."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        transform = connector.get_transform("lookup")
        assert transform is not None
        assert transform.id == "lookup"

    def test_get_transform_returns_none_for_unknown_id(self):
        """get_transform returns None when transform_id is not found."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)
        connector = ConnectorRegistry.get_instance("testconn")

        result = connector.get_transform("no_such_transform")
        assert result is None


# ---------------------------------------------------------------------------
# TestCreateConfigFromEnv
# ---------------------------------------------------------------------------


class TestCreateConfigFromEnv:
    """Tests for BaseConnector._create_config_from_env."""

    def test_creates_config_with_api_key_from_env(self):
        """Config is built with API key from environment variable."""
        manifest = ConnectorManifest(
            id="env_conn",
            name="Env Connector",
            description="Test",
            version="1.0.0",
            vendor="test",
            default_url="http://env-service:8080",
            auth_methods=(
                AuthMethod(
                    type=AuthType.API_KEY, header="X-API-Key", env_var="MY_API_KEY"
                ),
            ),
        )
        ConnectorRegistry.register_manifest(manifest)

        with patch.dict(os.environ, {"MY_API_KEY": "env-key-123"}):
            connector = ConnectorRegistry.get_instance("env_conn", config=None)

        # New instance won't use cache since config was built from env
        assert connector.config.api_key == "env-key-123"
        assert connector.config.auth_type == AuthType.API_KEY

    def test_creates_config_with_no_auth_when_env_var_missing(self):
        """Config defaults to AuthType.NONE when env var not set."""
        manifest = ConnectorManifest(
            id="no_auth_conn",
            name="No Auth Connector",
            description="Test",
            version="1.0.0",
            vendor="test",
            default_url="http://no-auth:8080",
            auth_methods=(
                AuthMethod(
                    type=AuthType.API_KEY, header="X-API-Key", env_var="MISSING_KEY"
                ),
            ),
        )
        ConnectorRegistry.register_manifest(manifest)

        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if present
            env_without_key = {
                k: v for k, v in os.environ.items() if k != "MISSING_KEY"
            }
            with patch.dict(os.environ, env_without_key, clear=True):
                connector = ConnectorRegistry.get_instance("no_auth_conn", config=None)

        assert connector.config.auth_type == AuthType.NONE

    def test_creates_config_with_default_url_when_env_var_not_set(self):
        """Config uses default_url when base_url_env var is not set."""
        manifest = ConnectorManifest(
            id="url_conn",
            name="URL Connector",
            description="Test",
            version="1.0.0",
            vendor="test",
            base_url_env="MY_SERVICE_URL",
            default_url="http://default-service:9090",
        )
        ConnectorRegistry.register_manifest(manifest)

        with patch.dict(os.environ, {}, clear=True):
            env = {k: v for k, v in os.environ.items() if k != "MY_SERVICE_URL"}
            with patch.dict(os.environ, env, clear=True):
                connector = ConnectorRegistry.get_instance("url_conn", config=None)

        assert connector.config.base_url == "http://default-service:9090"


# ---------------------------------------------------------------------------
# TestConnectorExecutorCaching
# ---------------------------------------------------------------------------


class TestConnectorExecutorCaching:
    """Tests for ConnectorActionExecutor connector instance caching."""

    @pytest.mark.asyncio
    async def test_executor_caches_connector_instance(self):
        """Second call to execute_action uses cached connector instance."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)

        executor = ConnectorActionExecutor()
        connector = ConnectorRegistry.get_instance("testconn")
        executor._connectors["testconn"] = connector

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            return_value={"ok": True},
        ):
            result1 = await executor.execute_action(
                connector_id="testconn",
                action_id="do_thing",
                config={},
                inputs={},
                variables={},
            )
            result2 = await executor.execute_action(
                connector_id="testconn",
                action_id="do_thing",
                config={},
                inputs={},
                variables={},
            )

        assert result1 == {"ok": True}
        assert result2 == {"ok": True}
        # Should still be exactly one connector in cache
        assert len(executor._connectors) == 1

    @pytest.mark.asyncio
    async def test_executor_wraps_api_error_in_connector_execution_error(self):
        """execute_action wraps unexpected exceptions in ConnectorExecutionError."""
        manifest = _make_manifest()
        ConnectorRegistry.register_manifest(manifest)

        connector = ConnectorRegistry.get_instance("testconn")
        executor = ConnectorActionExecutor()
        executor._connectors["testconn"] = connector

        with patch.object(
            connector,
            "call_api",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ):
            with pytest.raises(ConnectorExecutionError, match="Unexpected error"):
                await executor.execute_action(
                    connector_id="testconn",
                    action_id="do_thing",
                    config={},
                    inputs={},
                    variables={},
                )
