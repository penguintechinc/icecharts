"""Tests for Admin License Management API endpoints."""

import pytest


class TestGetLicenseStatus:
    """Tests for GET /admin/license."""

    def test_get_license_requires_auth(self, client):
        """License endpoint requires authentication."""
        response = client.get("/api/v1/admin/license")
        assert response.status_code == 401

    def test_get_license_requires_admin(self, client, auth_headers):
        """License endpoint requires admin role."""
        response = client.get("/api/v1/admin/license", headers=auth_headers)
        assert response.status_code == 403

    def test_get_license_as_admin(self, client, admin_auth_headers):
        """Admin can view license status."""
        response = client.get("/api/v1/admin/license", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "license" in data


class TestUpdateLicenseKey:
    """Tests for PUT /admin/license."""

    def test_update_license_requires_auth(self, client):
        """Updating license requires authentication."""
        response = client.put(
            "/api/v1/admin/license",
            json={"license_key": "PENG-AAAA-BBBB-CCCC-DDDD-EEEE"},
        )
        assert response.status_code == 401

    def test_update_license_requires_admin(self, client, auth_headers):
        """Updating license requires admin role."""
        response = client.put(
            "/api/v1/admin/license",
            headers=auth_headers,
            json={"license_key": "PENG-AAAA-BBBB-CCCC-DDDD-EEEE"},
        )
        assert response.status_code == 403

    def test_update_license_invalid_format(self, client, admin_auth_headers):
        """Invalid license key format returns 400."""
        response = client.put(
            "/api/v1/admin/license",
            headers=admin_auth_headers,
            json={"license_key": "INVALID-KEY"},
        )
        assert response.status_code == 400


class TestDeleteLicenseKey:
    """Tests for DELETE /admin/license."""

    def test_delete_license_requires_auth(self, client):
        """Deleting license requires authentication."""
        response = client.delete("/api/v1/admin/license")
        assert response.status_code == 401

    def test_delete_license_requires_admin(self, client, auth_headers):
        """Deleting license requires admin role."""
        response = client.delete("/api/v1/admin/license", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_license_as_admin(self, client, admin_auth_headers):
        """Admin can remove license key."""
        response = client.delete("/api/v1/admin/license", headers=admin_auth_headers)
        assert response.status_code == 200


class TestValidateLicenseKey:
    """Tests for POST /admin/license/validate."""

    def test_validate_requires_auth(self, client):
        """Validating license requires authentication."""
        response = client.post(
            "/api/v1/admin/license/validate",
            json={"license_key": "PENG-AAAA-BBBB-CCCC-DDDD-EEEE"},
        )
        assert response.status_code == 401

    def test_validate_requires_admin(self, client, auth_headers):
        """Validating license requires admin role."""
        response = client.post(
            "/api/v1/admin/license/validate",
            headers=auth_headers,
            json={"license_key": "PENG-AAAA-BBBB-CCCC-DDDD-EEEE"},
        )
        assert response.status_code == 403

    def test_validate_invalid_format(self, client, admin_auth_headers):
        """Validates format before contacting license server."""
        response = client.post(
            "/api/v1/admin/license/validate",
            headers=admin_auth_headers,
            json={"license_key": "NOT-A-VALID-KEY"},
        )
        assert response.status_code == 400


class TestGetLicenseFeatures:
    """Tests for GET /admin/license/features."""

    def test_get_features_requires_auth(self, client):
        """Getting features requires authentication."""
        response = client.get("/api/v1/admin/license/features")
        assert response.status_code == 401

    def test_get_features_requires_admin(self, client, auth_headers):
        """Getting features requires admin role."""
        response = client.get("/api/v1/admin/license/features", headers=auth_headers)
        assert response.status_code == 403

    def test_get_features_as_admin(self, client, admin_auth_headers):
        """Admin can get license features."""
        response = client.get(
            "/api/v1/admin/license/features", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "features" in data


class TestRefreshLicense:
    """Tests for POST /admin/license/refresh."""

    def test_refresh_requires_auth(self, client):
        """Refreshing license requires authentication."""
        response = client.post("/api/v1/admin/license/refresh")
        assert response.status_code == 401

    def test_refresh_requires_admin(self, client, auth_headers):
        """Refreshing license requires admin role."""
        response = client.post("/api/v1/admin/license/refresh", headers=auth_headers)
        assert response.status_code == 403

    def test_refresh_as_admin(self, client, admin_auth_headers):
        """Admin can refresh license."""
        response = client.post(
            "/api/v1/admin/license/refresh", headers=admin_auth_headers
        )
        assert response.status_code == 200
