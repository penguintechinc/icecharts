"""Tests for Admin Settings API endpoints."""
import pytest


class TestSignupSettings:
    """Tests for GET/PUT /admin/settings/signup."""

    def test_get_signup_settings_requires_auth(self, client):
        """Getting signup settings requires authentication."""
        response = client.get("/api/v1/admin/settings/signup")
        assert response.status_code == 401

    def test_get_signup_settings_requires_admin(self, client, auth_headers):
        """Getting signup settings requires admin role."""
        response = client.get("/api/v1/admin/settings/signup", headers=auth_headers)
        assert response.status_code == 403

    def test_get_signup_settings_as_admin(self, client, admin_auth_headers):
        """Admin can get signup settings."""
        response = client.get(
            "/api/v1/admin/settings/signup", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "signup" in data

    def test_update_signup_settings_requires_admin(self, client, auth_headers):
        """Updating signup settings requires admin role."""
        response = client.put(
            "/api/v1/admin/settings/signup",
            headers=auth_headers,
            json={"enabled": True},
        )
        assert response.status_code == 403

    def test_update_signup_settings_as_admin(self, client, admin_auth_headers):
        """Admin can update signup settings."""
        response = client.put(
            "/api/v1/admin/settings/signup",
            headers=admin_auth_headers,
            json={"enabled": True, "mode": "open"},
        )
        assert response.status_code == 200

    def test_update_signup_settings_invalid_mode(self, client, admin_auth_headers):
        """Invalid signup mode returns 400."""
        response = client.put(
            "/api/v1/admin/settings/signup",
            headers=admin_auth_headers,
            json={"mode": "invalid_mode"},
        )
        assert response.status_code == 400


class TestEmailSettings:
    """Tests for GET/PUT /admin/settings/email."""

    def test_get_email_settings_requires_auth(self, client):
        """Getting email settings requires authentication."""
        response = client.get("/api/v1/admin/settings/email")
        assert response.status_code == 401

    def test_get_email_settings_requires_admin(self, client, auth_headers):
        """Getting email settings requires admin role."""
        response = client.get("/api/v1/admin/settings/email", headers=auth_headers)
        assert response.status_code == 403

    def test_get_email_settings_as_admin(self, client, admin_auth_headers):
        """Admin can get email settings."""
        response = client.get(
            "/api/v1/admin/settings/email", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "email" in data

    def test_update_email_settings_requires_admin(self, client, auth_headers):
        """Updating email settings requires admin role."""
        response = client.put(
            "/api/v1/admin/settings/email",
            headers=auth_headers,
            json={"provider": "smtp"},
        )
        assert response.status_code == 403

    def test_update_email_settings_invalid_provider(self, client, admin_auth_headers):
        """Invalid email provider returns 400."""
        response = client.put(
            "/api/v1/admin/settings/email",
            headers=admin_auth_headers,
            json={"provider": "carrier_pigeon"},
        )
        assert response.status_code == 400


class TestTestEmail:
    """Tests for POST /admin/settings/email/test."""

    def test_send_test_email_requires_auth(self, client):
        """Sending test email requires authentication."""
        response = client.post(
            "/api/v1/admin/settings/email/test",
            json={"to": "test@example.com"},
        )
        assert response.status_code == 401

    def test_send_test_email_requires_admin(self, client, auth_headers):
        """Sending test email requires admin role."""
        response = client.post(
            "/api/v1/admin/settings/email/test",
            headers=auth_headers,
            json={"to": "test@example.com"},
        )
        assert response.status_code == 403


class TestSiteSettings:
    """Tests for GET/PUT /admin/settings/site."""

    def test_get_site_settings_requires_auth(self, client):
        """Getting site settings requires authentication."""
        response = client.get("/api/v1/admin/settings/site")
        assert response.status_code == 401

    def test_get_site_settings_requires_admin(self, client, auth_headers):
        """Getting site settings requires admin role."""
        response = client.get("/api/v1/admin/settings/site", headers=auth_headers)
        assert response.status_code == 403

    def test_get_site_settings_as_admin(self, client, admin_auth_headers):
        """Admin can get site settings."""
        response = client.get(
            "/api/v1/admin/settings/site", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "site" in data

    def test_update_site_settings_invalid_url(self, client, admin_auth_headers):
        """Site URL without http/https prefix returns 400."""
        response = client.put(
            "/api/v1/admin/settings/site",
            headers=admin_auth_headers,
            json={"site_url": "not-a-valid-url"},
        )
        assert response.status_code == 400

    def test_update_site_settings_as_admin(self, client, admin_auth_headers):
        """Admin can update site settings."""
        response = client.put(
            "/api/v1/admin/settings/site",
            headers=admin_auth_headers,
            json={"site_name": "IceCharts Test"},
        )
        assert response.status_code == 200
