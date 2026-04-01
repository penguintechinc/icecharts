"""Tests for IceRuns Webhook/Hook API endpoints."""

import pytest

NONEXISTENT_FUNCTION_ID = "nonexistent-function-id-abc123"
NONEXISTENT_TOKEN = "nonexistent-webhook-token-xyz"


class TestIceRunsPublicWebhook:
    """Test the public webhook handler (no auth required)."""

    def test_webhook_invalid_token_returns_404(self, client):
        response = client.post(f"/api/v1/iceruns/hook/{NONEXISTENT_TOKEN}")
        # No auth needed - invalid token should return 404
        assert response.status_code == 404

    def test_webhook_get_invalid_token_returns_404(self, client):
        response = client.get(f"/api/v1/iceruns/hook/{NONEXISTENT_TOKEN}")
        assert response.status_code == 404

    def test_webhook_is_accessible_without_auth(self, client):
        # Public endpoint - should not return 401
        response = client.post(
            f"/api/v1/iceruns/hook/{NONEXISTENT_TOKEN}",
            json={"data": "test"},
        )
        assert response.status_code != 401


class TestIceRunsWebhookConfig:
    """Test authenticated webhook configuration endpoints."""

    def test_get_webhook_config_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook")
        assert response.status_code == 401

    def test_get_webhook_config_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_webhook_config_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/config",
            json={"rate_limit": 200},
        )
        assert response.status_code == 401

    def test_update_webhook_config_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/config",
            json={"rate_limit": 200},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_test_webhook_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/test"
        )
        assert response.status_code == 401

    def test_test_webhook_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/test",
            json={"payload": {"test": True}},
            headers=auth_headers,
        )
        assert response.status_code == 404
