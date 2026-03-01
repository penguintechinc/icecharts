"""Tests for Storage Providers API endpoints."""
import pytest


class TestListStorageProviders:
    """Tests for GET /storage/providers."""

    def test_list_providers_requires_auth(self, client):
        """Listing providers requires authentication."""
        response = client.get("/api/v1/storage/providers")
        assert response.status_code == 401

    def test_list_providers_with_auth(self, client, auth_headers):
        """Authenticated user can list storage providers."""
        response = client.get("/api/v1/storage/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "providers" in data
        assert "total" in data


class TestCreateStorageProvider:
    """Tests for POST /storage/providers."""

    def test_create_provider_requires_auth(self, client):
        """Creating provider requires authentication."""
        response = client.post(
            "/api/v1/storage/providers",
            json={"provider_type": "local", "name": "Test", "config": {"path": "/tmp"}},
        )
        assert response.status_code == 401

    def test_create_provider_invalid_type(self, client, auth_headers):
        """Creating provider with invalid type returns 400."""
        response = client.post(
            "/api/v1/storage/providers",
            headers=auth_headers,
            json={"provider_type": "ftp", "name": "FTP Provider", "config": {}},
        )
        assert response.status_code == 400

    def test_create_provider_missing_name(self, client, auth_headers):
        """Creating provider without name returns 400."""
        response = client.post(
            "/api/v1/storage/providers",
            headers=auth_headers,
            json={"provider_type": "local", "config": {"path": "/tmp"}},
        )
        assert response.status_code == 400

    def test_create_local_provider(self, client, auth_headers):
        """Creating a local provider with valid data succeeds."""
        response = client.post(
            "/api/v1/storage/providers",
            headers=auth_headers,
            json={
                "provider_type": "local",
                "name": "Local Storage",
                "config": {"path": "/tmp/icecharts-test"},
            },
        )
        assert response.status_code == 201


class TestGetStorageProvider:
    """Tests for GET /storage/providers/<provider_id>."""

    def test_get_provider_requires_auth(self, client):
        """Getting provider requires authentication."""
        response = client.get("/api/v1/storage/providers/1")
        assert response.status_code == 401

    def test_get_provider_not_found(self, client, auth_headers):
        """Non-existent provider returns 404."""
        response = client.get("/api/v1/storage/providers/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateStorageProvider:
    """Tests for PUT /storage/providers/<provider_id>."""

    def test_update_provider_requires_auth(self, client):
        """Updating provider requires authentication."""
        response = client.put(
            "/api/v1/storage/providers/1",
            json={"name": "Updated"},
        )
        assert response.status_code == 401

    def test_update_provider_not_found(self, client, auth_headers):
        """Updating non-existent provider returns 404."""
        response = client.put(
            "/api/v1/storage/providers/99999",
            headers=auth_headers,
            json={"name": "Updated"},
        )
        assert response.status_code == 404


class TestDeleteStorageProvider:
    """Tests for DELETE /storage/providers/<provider_id>."""

    def test_delete_provider_requires_auth(self, client):
        """Deleting provider requires authentication."""
        response = client.delete("/api/v1/storage/providers/1")
        assert response.status_code == 401

    def test_delete_provider_not_found(self, client, auth_headers):
        """Deleting non-existent provider returns 404."""
        response = client.delete(
            "/api/v1/storage/providers/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestTestStorageProvider:
    """Tests for POST /storage/providers/<provider_id>/test."""

    def test_test_provider_requires_auth(self, client):
        """Testing provider requires authentication."""
        response = client.post("/api/v1/storage/providers/1/test")
        assert response.status_code == 401

    def test_test_provider_not_found(self, client, auth_headers):
        """Testing non-existent provider returns 404."""
        response = client.post(
            "/api/v1/storage/providers/99999/test",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestStorageUsage:
    """Tests for GET /storage/usage."""

    def test_get_usage_requires_auth(self, client):
        """Getting usage requires authentication."""
        response = client.get("/api/v1/storage/usage")
        assert response.status_code == 401

    def test_get_usage_with_auth(self, client, auth_headers):
        """Authenticated user can get storage usage."""
        response = client.get("/api/v1/storage/usage", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "usage" in data


class TestStorageQuota:
    """Tests for GET/PUT /storage/quota."""

    def test_get_quota_requires_auth(self, client):
        """Getting quota requires authentication."""
        response = client.get("/api/v1/storage/quota")
        assert response.status_code == 401

    def test_get_quota_with_auth(self, client, auth_headers):
        """Authenticated user can get storage quota."""
        response = client.get("/api/v1/storage/quota", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "quota" in data

    def test_update_quota_requires_admin(self, client, auth_headers):
        """Updating quota requires admin role."""
        response = client.put(
            "/api/v1/storage/quota",
            headers=auth_headers,
            json={"user_id": 1, "quota_mb": 2048},
        )
        # Regular user gets 403 (admin_required)
        assert response.status_code in [403, 400]


class TestStorageMigrate:
    """Tests for POST /storage/migrate."""

    def test_migrate_storage_requires_auth(self, client):
        """Migrating storage requires authentication."""
        response = client.post(
            "/api/v1/storage/migrate",
            json={"source_provider_id": 1, "target_provider_id": 2},
        )
        assert response.status_code == 401

    def test_migrate_storage_missing_fields(self, client, auth_headers):
        """Migration returns 400 when required fields are missing."""
        response = client.post(
            "/api/v1/storage/migrate",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400
