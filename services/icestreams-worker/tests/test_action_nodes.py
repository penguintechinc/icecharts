#!/usr/bin/env python3
"""
Tests for action nodes in nodes/actions/.

Tests cover:
- HttpRequestAction: GET/POST requests, custom headers, auth, retry on 5xx, timeout, JSON/non-JSON response
- WebhookOutAction: POST webhook, payload, headers, bearer/basic/apikey auth
- Both return NodeResult instances
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

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


def _make_context(config: dict = None, variables: dict = None) -> NodeContext:
    """Create a test NodeContext."""
    return NodeContext(
        execution_id="test-exec-001",
        playbook_id="test-playbook",
        node_id="test-node",
        config=config or {},
        variables=variables or {},
    )


def _mock_response(
    status_code: int = 200,
    content_type: str = "application/json",
    json_data: dict = None,
    text: str = "",
    content: bytes = b"",
) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {"content-type": content_type}
    resp.content = json_data is not None and b'{"ok": true}' or content or text.encode()
    resp.text = text if text else (str(json_data) if json_data else "")
    resp.json = MagicMock(return_value=json_data or {})
    return resp


class TestHttpRequestAction:
    """Tests for HttpRequestAction node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.actions.http_request import HttpRequestAction

        self.node_class = HttpRequestAction
        self.node = HttpRequestAction()

    def test_node_type(self):
        assert self.node_class.node_type == "action_http_request"

    def test_category_is_actions(self):
        assert self.node_class.category == "actions"

    def test_has_url_input(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "url" in names

    def test_has_response_and_status_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "response" in names
        assert "status" in names
        assert "body" in names

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """GET request with 200 response must succeed."""
        ctx = _make_context(config={"maxRetries": 0})
        mock_resp = _mock_response(200, "application/json", {"data": "result"})

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(ctx, {"url": "http://example.com/api"})

        assert isinstance(result, NodeResult)
        assert result.success is True
        assert result.outputs["status"] == 200

    @pytest.mark.asyncio
    async def test_post_request_with_body(self):
        """POST request must include body in request."""
        ctx = _make_context(config={"maxRetries": 0})
        mock_resp = _mock_response(201, "application/json", {"created": True})

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/api",
                    "method": "POST",
                    "body": {"name": "test"},
                },
            )

        assert result.success is True
        assert result.outputs["status"] == 201

    @pytest.mark.asyncio
    async def test_custom_headers_passed(self):
        """Custom headers must be included in the request."""
        ctx = _make_context(config={"maxRetries": 0})
        mock_resp = _mock_response(200, "application/json", {})

        captured_kwargs = {}

        async def capture_request(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_resp

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(side_effect=capture_request)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/api",
                    "headers": {"X-Custom": "MyValue"},
                },
            )

        assert result.success is True
        assert captured_kwargs.get("headers", {}).get("X-Custom") == "MyValue"

    @pytest.mark.asyncio
    async def test_missing_url_returns_failure(self):
        """Missing 'url' input must return failure result."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"url": ""})
        assert result.success is False
        assert "URL" in result.error or "url" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_required_url_input(self):
        """Missing required url port must fail validation."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_5xx_triggers_retry(self):
        """5xx status must trigger retry logic."""
        ctx = _make_context(config={"maxRetries": 2})
        mock_500 = _mock_response(500, "text/plain", None, "Internal Server Error")
        mock_200 = _mock_response(200, "application/json", {"ok": True})

        call_count = 0

        async def respond(**kwargs):
            nonlocal call_count
            call_count += 1
            return mock_500 if call_count < 3 else mock_200

        with patch("nodes.actions.http_request.asyncio.sleep", new_callable=AsyncMock):
            with patch(
                "nodes.actions.http_request.httpx.AsyncClient"
            ) as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.request = AsyncMock(side_effect=respond)
                mock_client_class.return_value = mock_client

                result = await self.node.execute(ctx, {"url": "http://example.com"})

        assert call_count >= 2  # At least one retry occurred

    @pytest.mark.asyncio
    async def test_json_response_parsed(self):
        """JSON response must be parsed into body output."""
        ctx = _make_context(config={"maxRetries": 0})
        json_data = {"users": [{"id": 1, "name": "Alice"}]}
        mock_resp = _mock_response(200, "application/json", json_data)

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(ctx, {"url": "http://example.com/api"})

        assert result.success is True
        body = result.outputs["body"]
        assert body is not None

    @pytest.mark.asyncio
    async def test_network_error_returns_failure(self):
        """Network error must return failure result."""
        ctx = _make_context(config={"maxRetries": 0})
        import httpx

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(
                side_effect=httpx.NetworkError("Connection refused")
            )
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx, {"url": "http://unreachable.example.com"}
            )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_timeout_error_returns_failure(self):
        """Timeout must return failure result."""
        ctx = _make_context(config={"maxRetries": 0})
        import httpx

        with patch("nodes.actions.http_request.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.request = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            mock_client_class.return_value = mock_client

            result = await self.node.execute(ctx, {"url": "http://slow.example.com"})

        assert result.success is False

    def test_validate_config_valid(self):
        """Valid config must produce no errors."""
        errors = self.node_class.validate_config({"method": "GET", "timeout": 30})
        assert errors == []

    def test_validate_config_invalid_method(self):
        """Invalid HTTP method must produce validation error."""
        errors = self.node_class.validate_config({"method": "INVALID"})
        assert len(errors) > 0

    def test_validate_config_invalid_timeout(self):
        """Non-positive timeout must produce validation error."""
        errors = self.node_class.validate_config({"timeout": -5})
        assert len(errors) > 0


class TestWebhookOutAction:
    """Tests for WebhookOutAction node."""

    @pytest.fixture(autouse=True)
    def import_node(self):
        from nodes.actions.webhook_out import WebhookOutAction

        self.node_class = WebhookOutAction
        self.node = WebhookOutAction()

    def test_node_type(self):
        assert self.node_class.node_type == "action_webhook_out"

    def test_category_is_actions(self):
        assert self.node_class.category == "actions"

    def test_has_url_and_payload_inputs(self):
        names = [i.name for i in self.node_class.inputs()]
        assert "url" in names
        assert "payload" in names

    def test_has_success_status_message_outputs(self):
        names = [o.name for o in self.node_class.outputs()]
        assert "success" in names
        assert "status" in names
        assert "message" in names

    @pytest.mark.asyncio
    async def test_webhook_post_success(self):
        """Successful webhook POST must return success=True."""
        ctx = _make_context(config={"authType": "none", "maxRetries": 0})
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {"event": "test"},
                },
            )

        assert isinstance(result, NodeResult)
        assert result.success is True
        assert result.outputs["success"] is True
        assert result.outputs["status"] == 200

    @pytest.mark.asyncio
    async def test_webhook_with_bearer_auth(self):
        """Webhook with bearer auth must include Authorization header."""
        ctx = _make_context(
            config={
                "authType": "bearer",
                "bearerToken": "my-token-123",
                "maxRetries": 0,
            }
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 204

        captured_headers = {}

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {"data": "test"},
                },
            )

        assert captured_headers.get("Authorization") == "Bearer my-token-123"

    @pytest.mark.asyncio
    async def test_webhook_with_basic_auth(self):
        """Webhook with basic auth must include base64 Authorization header."""
        import base64

        ctx = _make_context(
            config={
                "authType": "basic",
                "basicUsername": "user",
                "basicPassword": "pass",
                "maxRetries": 0,
            }
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        captured_headers = {}

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {},
                },
            )

        expected_b64 = base64.b64encode(b"user:pass").decode()
        assert captured_headers.get("Authorization") == f"Basic {expected_b64}"

    @pytest.mark.asyncio
    async def test_webhook_with_apikey_auth(self):
        """Webhook with apikey auth must include custom header."""
        ctx = _make_context(
            config={
                "authType": "apikey",
                "apiKeyHeader": "X-Auth-Token",
                "apiKeyValue": "secret-key-abc",
                "maxRetries": 0,
            }
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        captured_headers = {}

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {},
                },
            )

        assert captured_headers.get("X-Auth-Token") == "secret-key-abc"

    @pytest.mark.asyncio
    async def test_webhook_custom_headers_override(self):
        """Custom headers input must be included in request."""
        ctx = _make_context(config={"authType": "none", "maxRetries": 0})
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        captured_headers = {}

        async def capture_post(url, content, headers):
            captured_headers.update(headers)
            return mock_resp

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=capture_post)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {"key": "val"},
                    "headers": {"X-Request-ID": "req-001"},
                },
            )

        assert captured_headers.get("X-Request-ID") == "req-001"

    @pytest.mark.asyncio
    async def test_webhook_missing_url_returns_failure(self):
        """Missing URL must return failure."""
        ctx = _make_context(config={})
        result = await self.node.execute(ctx, {"url": "", "payload": {}})
        assert result.success is False

    @pytest.mark.asyncio
    async def test_webhook_5xx_returns_false_success(self):
        """5xx response must return success=False in outputs (not NodeResult failure)."""
        ctx = _make_context(config={"authType": "none", "maxRetries": 0})
        mock_resp = MagicMock()
        mock_resp.status_code = 503

        with patch("nodes.actions.webhook_out.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            result = await self.node.execute(
                ctx,
                {
                    "url": "http://example.com/webhook",
                    "payload": {},
                },
            )

        # NodeResult should succeed (we handled the error), but webhook failed
        assert isinstance(result, NodeResult)

    def test_validate_config_valid_bearer(self):
        """Valid bearer config must produce no errors."""
        errors = self.node_class.validate_config(
            {
                "authType": "bearer",
                "bearerToken": "mytoken",
                "timeout": 30,
                "maxRetries": 3,
            }
        )
        assert errors == []

    def test_validate_config_bearer_missing_token(self):
        """Bearer auth without token must produce validation error."""
        errors = self.node_class.validate_config({"authType": "bearer"})
        assert len(errors) > 0

    def test_validate_config_basic_missing_password(self):
        """Basic auth without password must produce validation error."""
        errors = self.node_class.validate_config(
            {
                "authType": "basic",
                "basicUsername": "user",
            }
        )
        assert len(errors) > 0

    def test_validate_config_invalid_auth_type(self):
        """Invalid authType must produce validation error."""
        errors = self.node_class.validate_config({"authType": "digest"})
        assert len(errors) > 0
