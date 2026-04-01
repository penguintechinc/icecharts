"""Tests for IceRuns (serverless function management) API endpoints."""

import pytest

NONEXISTENT_FUNCTION_ID = "nonexistent-function-id-abc123"


class TestIceRunsList:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/iceruns")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceruns", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "items" in data or "error" in data


class TestIceRunsCreate:
    def test_create_requires_auth(self, client):
        response = client.post("/api/v1/iceruns", json={"name": "test"})
        assert response.status_code == 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        payload = {
            "runtime": "python3.13",
            "entrypoint": "main.py",
            "handler": "handler",
        }
        response = client.post("/api/v1/iceruns", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_invalid_runtime_returns_400(self, client, auth_headers):
        payload = {
            "name": "test-func",
            "runtime": "invalid-runtime",
            "entrypoint": "main.py",
            "handler": "handler",
        }
        response = client.post("/api/v1/iceruns", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_with_valid_data(self, client, auth_headers):
        payload = {
            "name": "test-func",
            "runtime": "python3.13",
            "entrypoint": "main.py",
            "handler": "handler",
        }
        response = client.post("/api/v1/iceruns", json=payload, headers=auth_headers)
        assert response.status_code != 401

    def test_create_memory_limit_validation(self, client, auth_headers):
        payload = {
            "name": "test-func",
            "runtime": "python3.13",
            "entrypoint": "main.py",
            "handler": "handler",
            "memory_limit_mb": 99,  # Below minimum of 128
        }
        response = client.post("/api/v1/iceruns", json=payload, headers=auth_headers)
        assert response.status_code == 400


class TestIceRunsGetById:
    def test_get_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceRunsUpdate:
    def test_update_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}", json={"name": "updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsDelete:
    def test_delete_requires_auth(self, client):
        response = client.delete(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceRunsPackage:
    def test_upload_package_requires_auth(self, client):
        response = client.post(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/package")
        assert response.status_code == 401

    def test_download_package_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/package")
        assert response.status_code == 401

    def test_delete_package_requires_auth(self, client):
        response = client.delete(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/package")
        assert response.status_code == 401

    def test_upload_package_no_file_returns_error(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/package",
            headers=auth_headers,
        )
        # Should be 404 (function not found) or 400 (no file)
        assert response.status_code in (400, 404)


class TestIceRunsStatusOperations:
    def test_activate_requires_auth(self, client):
        response = client.put(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/activate")
        assert response.status_code == 401

    def test_pause_requires_auth(self, client):
        response = client.put(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/pause")
        assert response.status_code == 401

    def test_archive_requires_auth(self, client):
        response = client.put(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/archive")
        assert response.status_code == 401

    def test_activate_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/activate", headers=auth_headers
        )
        assert response.status_code == 404

    def test_pause_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/pause", headers=auth_headers
        )
        assert response.status_code == 404

    def test_archive_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/archive", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceRunsWebhookRegenerate:
    def test_regenerate_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/regenerate"
        )
        assert response.status_code == 401

    def test_regenerate_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/webhook/regenerate",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsVersions:
    def test_list_versions_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/versions")
        assert response.status_code == 401

    def test_list_versions_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/versions", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceRunsConfig:
    def test_update_config_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/config",
            json={"memory_limit_mb": 256},
        )
        assert response.status_code == 401

    def test_update_config_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/config",
            json={"memory_limit_mb": 256},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_secrets_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/secrets",
            json={"secrets": {"KEY": "value"}},
        )
        assert response.status_code == 401

    def test_update_secrets_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/secrets",
            json={"secrets": {"KEY": "value"}},
            headers=auth_headers,
        )
        assert response.status_code == 404
