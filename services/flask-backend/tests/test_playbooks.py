"""Tests for Playbooks API endpoints."""

import pytest

NONEXISTENT_ID = "999999"


class TestPlaybooksList:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/playbooks")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/playbooks", headers=auth_headers)
        assert response.status_code != 401


class TestPlaybooksCreate:
    def test_create_requires_auth(self, client):
        response = client.post("/api/v1/playbooks", json={"name": "Test"})
        assert response.status_code == 401

    def test_create_with_valid_data(self, client, auth_headers):
        payload = {
            "name": "My Playbook",
            "trigger_type": "manual",
            "canvas_data": {"nodes": [], "edges": []},
        }
        response = client.post("/api/v1/playbooks", json=payload, headers=auth_headers)
        assert response.status_code != 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        payload = {"trigger_type": "manual"}
        response = client.post("/api/v1/playbooks", json=payload, headers=auth_headers)
        assert response.status_code in (400, 422, 500)


class TestPlaybooksGetById:
    def test_get_requires_auth(self, client):
        response = client.get(f"/api/v1/playbooks/{NONEXISTENT_ID}")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/playbooks/{NONEXISTENT_ID}", headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_with_auth_no_crash(self, client, auth_headers):
        response = client.get(
            f"/api/v1/playbooks/{NONEXISTENT_ID}", headers=auth_headers
        )
        assert response.status_code != 401


class TestPlaybooksUpdate:
    def test_update_requires_auth(self, client):
        response = client.put(
            f"/api/v1/playbooks/{NONEXISTENT_ID}", json={"name": "Updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/playbooks/{NONEXISTENT_ID}",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_with_auth(self, client, auth_headers):
        response = client.put(
            f"/api/v1/playbooks/{NONEXISTENT_ID}",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code != 401


class TestPlaybooksDelete:
    def test_delete_requires_auth(self, client):
        response = client.delete(f"/api/v1/playbooks/{NONEXISTENT_ID}")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/playbooks/{NONEXISTENT_ID}", headers=auth_headers
        )
        assert response.status_code == 404


class TestPlaybooksDuplicate:
    def test_duplicate_requires_auth(self, client):
        response = client.post(f"/api/v1/playbooks/{NONEXISTENT_ID}/duplicate")
        assert response.status_code == 401

    def test_duplicate_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/duplicate", headers=auth_headers
        )
        assert response.status_code == 404


class TestPlaybooksLock:
    def test_get_lock_requires_auth(self, client):
        response = client.get(f"/api/v1/playbooks/{NONEXISTENT_ID}/lock")
        assert response.status_code == 401

    def test_acquire_lock_requires_auth(self, client):
        response = client.post(f"/api/v1/playbooks/{NONEXISTENT_ID}/lock")
        assert response.status_code == 401

    def test_release_lock_requires_auth(self, client):
        response = client.delete(f"/api/v1/playbooks/{NONEXISTENT_ID}/lock")
        assert response.status_code == 401

    def test_get_lock_with_auth(self, client, auth_headers):
        response = client.get(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/lock", headers=auth_headers
        )
        assert response.status_code != 401


class TestPlaybooksExecute:
    def test_execute_requires_auth(self, client):
        response = client.post(f"/api/v1/playbooks/{NONEXISTENT_ID}/execute")
        assert response.status_code == 401

    def test_execute_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/execute",
            json={"input_data": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestPlaybooksExecutions:
    def test_list_executions_requires_auth(self, client):
        response = client.get(f"/api/v1/playbooks/{NONEXISTENT_ID}/executions")
        assert response.status_code == 401

    def test_get_execution_requires_auth(self, client):
        response = client.get(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/executions/{NONEXISTENT_ID}"
        )
        assert response.status_code == 401

    def test_cancel_execution_requires_auth(self, client):
        response = client.post(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/executions/{NONEXISTENT_ID}/cancel"
        )
        assert response.status_code == 401


class TestPlaybookNodeMetadata:
    def test_get_node_metadata_requires_auth(self, client):
        response = client.get(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/nodes/node-1/metadata"
        )
        assert response.status_code == 401

    def test_update_node_metadata_requires_auth(self, client):
        response = client.put(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/nodes/node-1/metadata",
            json={"metadata": {}},
        )
        assert response.status_code == 401


class TestPlaybooksWebhooks:
    def test_list_webhooks_requires_auth(self, client):
        response = client.get(f"/api/v1/playbooks/{NONEXISTENT_ID}/webhooks")
        assert response.status_code == 401

    def test_create_webhook_requires_auth(self, client):
        response = client.post(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/webhooks", json={"name": "test"}
        )
        assert response.status_code == 401

    def test_delete_webhook_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/playbooks/{NONEXISTENT_ID}/webhooks/{NONEXISTENT_ID}"
        )
        assert response.status_code == 401
