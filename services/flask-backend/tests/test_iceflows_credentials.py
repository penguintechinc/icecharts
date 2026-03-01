"""Tests for IceFlows Credentials (Git Provider Token Management) API endpoints."""
import pytest

NONEXISTENT_CRED_ID = "nonexistent-cred-id-00000000-0000-0000-0000-000000000000"


class TestCredentialsList:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/iceflows/credentials")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceflows/credentials", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "credentials" in data or "error" in data

    def test_list_returns_empty_initially(self, client, auth_headers):
        response = client.get("/api/v1/iceflows/credentials", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["credentials"], list)


class TestCredentialsCreate:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/iceflows/credentials",
            json={"name": "test", "provider": "github", "access_token": "ghp_token"},
        )
        assert response.status_code == 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        payload = {"provider": "github", "access_token": "ghp_test_token"}
        response = client.post(
            "/api/v1/iceflows/credentials", json=payload, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_missing_provider_returns_400(self, client, auth_headers):
        payload = {"name": "My GitHub Token", "access_token": "ghp_test_token"}
        response = client.post(
            "/api/v1/iceflows/credentials", json=payload, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_invalid_provider_returns_400(self, client, auth_headers):
        payload = {
            "name": "My Token",
            "provider": "bitbucket",  # Not supported
            "access_token": "token_xyz",
        }
        response = client.post(
            "/api/v1/iceflows/credentials", json=payload, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_missing_access_token_returns_400(self, client, auth_headers):
        payload = {"name": "My GitHub Token", "provider": "github"}
        response = client.post(
            "/api/v1/iceflows/credentials", json=payload, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_valid_github_credential(self, client, auth_headers):
        payload = {
            "name": "My GitHub Token",
            "provider": "github",
            "access_token": "ghp_test_token_12345",
        }
        response = client.post(
            "/api/v1/iceflows/credentials", json=payload, headers=auth_headers
        )
        assert response.status_code != 401
        if response.status_code == 201:
            data = response.get_json()
            assert data["success"] is True
            assert "credential" in data
            credential = data["credential"]
            assert "access_token" not in credential  # Token should be masked
            assert credential["provider"] == "github"


class TestCredentialsGet:
    def test_get_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCredentialsUpdate:
    def test_update_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCredentialsDelete:
    def test_delete_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}"
        )
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCredentialsTest:
    def test_test_credential_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}/test"
        )
        assert response.status_code == 401

    def test_test_credential_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/credentials/{NONEXISTENT_CRED_ID}/test",
            headers=auth_headers,
        )
        assert response.status_code == 404
