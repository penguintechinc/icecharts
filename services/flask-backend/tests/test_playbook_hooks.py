"""Tests for Playbook Webhook Hooks API endpoints."""
import pytest


class TestTriggerWebhook:
    """Tests for ANY /hooks/<token>."""

    def test_webhook_no_auth_required_post(self, client):
        """Webhook trigger does not require JWT authentication."""
        response = client.post("/api/v1/hooks/nonexistent-token-xyz", json={})
        # 404 = token not found, not 401 = no auth required
        assert response.status_code != 401
        assert response.status_code == 404

    def test_webhook_no_auth_required_get(self, client):
        """Webhook trigger via GET does not require authentication."""
        response = client.get("/api/v1/hooks/nonexistent-token-xyz")
        assert response.status_code != 401
        assert response.status_code == 404

    def test_webhook_invalid_token_returns_404(self, client):
        """An invalid/unknown token returns 404."""
        response = client.post(
            "/api/v1/hooks/completely-invalid-token-that-does-not-exist",
            json={"event": "test"},
        )
        assert response.status_code == 404


class TestTestWebhook:
    """Tests for GET/POST /hooks/<token>/test."""

    def test_webhook_test_no_auth_required(self, client):
        """Webhook test endpoint does not require JWT authentication."""
        response = client.get("/api/v1/hooks/nonexistent-token-xyz/test")
        # 404 = token not found, not 401
        assert response.status_code != 401
        assert response.status_code == 404

    def test_webhook_test_post_no_auth_required(self, client):
        """Webhook test POST does not require JWT authentication."""
        response = client.post(
            "/api/v1/hooks/nonexistent-token-xyz/test",
            json={},
        )
        assert response.status_code != 401
        assert response.status_code == 404
