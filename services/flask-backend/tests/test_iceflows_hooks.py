"""Tests for IceFlows Webhook Hooks (GitHub/GitLab) API endpoints."""

import pytest

NONEXISTENT_WEBHOOK_ID = "nonexistent-webhook-id-00000000-0000-0000-0000-000000000000"


class TestGitHubWebhook:
    """Test GitHub webhook endpoint - public, no auth required."""

    def test_github_webhook_no_auth_required(self, client):
        """Public endpoint should not return 401."""
        response = client.post(
            f"/api/v1/iceflows/hooks/github/{NONEXISTENT_WEBHOOK_ID}",
            json={"action": "push"},
            headers={"X-GitHub-Event": "ping"},
        )
        assert response.status_code != 401

    def test_github_webhook_invalid_id_returns_404(self, client):
        """Invalid webhook ID should return 404."""
        response = client.post(
            f"/api/v1/iceflows/hooks/github/{NONEXISTENT_WEBHOOK_ID}",
            data=b'{"action": "push"}',
            content_type="application/json",
            headers={
                "X-GitHub-Event": "ping",
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )
        assert response.status_code == 404

    def test_github_webhook_ping_event_nonexistent(self, client):
        """Ping event should still check webhook existence."""
        response = client.post(
            f"/api/v1/iceflows/hooks/github/{NONEXISTENT_WEBHOOK_ID}",
            data=b"{}",
            content_type="application/json",
            headers={"X-GitHub-Event": "ping"},
        )
        assert response.status_code == 404


class TestGitLabWebhook:
    """Test GitLab webhook endpoint - public, no auth required."""

    def test_gitlab_webhook_no_auth_required(self, client):
        """Public endpoint should not return 401."""
        response = client.post(
            f"/api/v1/iceflows/hooks/gitlab/{NONEXISTENT_WEBHOOK_ID}",
            json={"object_kind": "push"},
            headers={"X-Gitlab-Event": "Push Hook"},
        )
        assert response.status_code != 401

    def test_gitlab_webhook_invalid_id_returns_404(self, client):
        """Invalid webhook ID should return 404."""
        response = client.post(
            f"/api/v1/iceflows/hooks/gitlab/{NONEXISTENT_WEBHOOK_ID}",
            data=b'{"object_kind": "push"}',
            content_type="application/json",
            headers={
                "X-Gitlab-Event": "Push Hook",
                "X-Gitlab-Token": "invalid-token",
            },
        )
        assert response.status_code == 404

    def test_gitlab_webhook_system_hook_nonexistent(self, client):
        """System Hook should still check webhook existence."""
        response = client.post(
            f"/api/v1/iceflows/hooks/gitlab/{NONEXISTENT_WEBHOOK_ID}",
            data=b"{}",
            content_type="application/json",
            headers={"X-Gitlab-Event": "System Hook"},
        )
        assert response.status_code == 404
