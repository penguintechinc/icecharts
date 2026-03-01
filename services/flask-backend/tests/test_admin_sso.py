"""Tests for Admin SSO Configuration API endpoints."""
import pytest


class TestGetAvailableProviders:
    """Tests for GET /admin/sso/providers."""

    def test_get_providers_requires_auth(self, client):
        """Getting SSO providers requires authentication."""
        response = client.get("/api/v1/admin/sso/providers")
        assert response.status_code == 401

    def test_get_providers_requires_admin(self, client, auth_headers):
        """Getting SSO providers requires admin role."""
        response = client.get("/api/v1/admin/sso/providers", headers=auth_headers)
        assert response.status_code == 403

    def test_get_providers_as_admin(self, client, admin_auth_headers):
        """Admin can get available SSO providers."""
        response = client.get("/api/v1/admin/sso/providers", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "providers" in data
        # Google is always available
        provider_ids = [p["id"] for p in data["providers"]]
        assert "google" in provider_ids


class TestListSsoConfigs:
    """Tests for GET /admin/sso."""

    def test_list_sso_configs_requires_auth(self, client):
        """Listing SSO configs requires authentication."""
        response = client.get("/api/v1/admin/sso")
        assert response.status_code == 401

    def test_list_sso_configs_requires_admin(self, client, auth_headers):
        """Listing SSO configs requires admin role."""
        response = client.get("/api/v1/admin/sso", headers=auth_headers)
        assert response.status_code == 403

    def test_list_sso_configs_as_admin(self, client, admin_auth_headers):
        """Admin can list SSO configurations."""
        response = client.get("/api/v1/admin/sso", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data


class TestCreateSsoConfig:
    """Tests for POST /admin/sso."""

    def test_create_sso_config_requires_auth(self, client):
        """Creating SSO config requires authentication."""
        response = client.post(
            "/api/v1/admin/sso",
            json={"provider": "google", "client_id": "test", "client_secret": "secret"},
        )
        assert response.status_code == 401

    def test_create_sso_config_requires_admin(self, client, auth_headers):
        """Creating SSO config requires admin role."""
        response = client.post(
            "/api/v1/admin/sso",
            headers=auth_headers,
            json={"provider": "google", "client_id": "test", "client_secret": "secret"},
        )
        assert response.status_code == 403

    def test_create_sso_config_invalid_provider(self, client, admin_auth_headers):
        """Invalid provider type returns 400."""
        response = client.post(
            "/api/v1/admin/sso",
            headers=admin_auth_headers,
            json={"provider": "facebook"},
        )
        assert response.status_code == 400


class TestGetSsoConfig:
    """Tests for GET /admin/sso/<config_id>."""

    def test_get_sso_config_requires_auth(self, client):
        """Getting SSO config requires authentication."""
        response = client.get("/api/v1/admin/sso/1")
        assert response.status_code == 401

    def test_get_sso_config_requires_admin(self, client, auth_headers):
        """Getting SSO config requires admin role."""
        response = client.get("/api/v1/admin/sso/1", headers=auth_headers)
        assert response.status_code == 403

    def test_get_sso_config_not_found(self, client, admin_auth_headers):
        """Non-existent SSO config returns 404."""
        response = client.get("/api/v1/admin/sso/99999", headers=admin_auth_headers)
        assert response.status_code == 404


class TestUpdateSsoConfig:
    """Tests for PUT/PATCH/DELETE /admin/sso/<config_id>."""

    def test_update_sso_config_requires_auth(self, client):
        """Updating SSO config requires authentication."""
        response = client.put("/api/v1/admin/sso/1", json={"enabled": True})
        assert response.status_code == 401

    def test_patch_sso_config_requires_auth(self, client):
        """Patching SSO config requires authentication."""
        response = client.patch("/api/v1/admin/sso/1", json={"enabled": False})
        assert response.status_code == 401

    def test_delete_sso_config_requires_auth(self, client):
        """Deleting SSO config requires authentication."""
        response = client.delete("/api/v1/admin/sso/1")
        assert response.status_code == 401

    def test_delete_sso_config_not_found(self, client, admin_auth_headers):
        """Deleting non-existent SSO config returns 404."""
        response = client.delete("/api/v1/admin/sso/99999", headers=admin_auth_headers)
        assert response.status_code == 404
