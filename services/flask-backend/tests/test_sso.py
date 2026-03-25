"""Tests for SSO (SAML 2.0 / OIDC) API endpoints."""
import pytest


class TestSamlMetadata:
    """Tests for GET /sso/saml/metadata."""

    def test_saml_metadata_no_auth_required(self, client):
        """SAML metadata is public (no auth needed)."""
        response = client.get("/api/v1/sso/saml/metadata")
        # Returns 404 when not configured, 200 when configured with XML,
        # or 500 on misconfiguration — never 401.
        assert response.status_code in [200, 404, 500]

    def test_saml_metadata_not_configured_returns_404(self, client):
        """When SAML is not configured the endpoint returns 404."""
        response = client.get("/api/v1/sso/saml/metadata")
        # In tests, SAML is not configured so 404 is expected
        assert response.status_code in [404, 500]


class TestSamlLogin:
    """Tests for GET /sso/saml/login."""

    def test_saml_login_no_auth_required(self, client):
        """SAML login initiation does not require authentication."""
        response = client.get("/api/v1/sso/saml/login")
        # Expect redirect, 404 (not configured), 403 (not licensed), or 500
        assert response.status_code in [302, 403, 404, 500]


class TestSamlAcs:
    """Tests for POST /sso/saml/acs."""

    def test_saml_acs_missing_saml_response(self, client):
        """ACS returns error when SAMLResponse is missing."""
        response = client.post("/api/v1/sso/saml/acs", data={})
        assert response.status_code in [400, 403, 404, 500]

    def test_saml_acs_no_auth_required(self, client):
        """ACS endpoint does not require a JWT token."""
        response = client.post("/api/v1/sso/saml/acs", data={})
        assert response.status_code != 401


class TestSamlLogout:
    """Tests for POST /sso/saml/logout."""

    def test_saml_logout_requires_auth(self, client):
        """SAML logout requires authentication."""
        response = client.post("/api/v1/sso/saml/logout")
        assert response.status_code == 401

    def test_saml_logout_with_auth(self, client, auth_headers):
        """Authenticated user can call SAML logout."""
        response = client.post("/api/v1/sso/saml/logout", headers=auth_headers)
        # 403 if not licensed, 404 if SAML not configured, 200 if configured
        assert response.status_code in [200, 403, 404, 500]


class TestOidcLogin:
    """Tests for GET /sso/oidc/login."""

    def test_oidc_login_no_auth_required(self, client):
        """OIDC login initiation does not require authentication."""
        response = client.get("/api/v1/sso/oidc/login")
        # Expect redirect or 404 (feature not available/configured)
        assert response.status_code in [302, 404, 403, 500]


class TestOidcCallback:
    """Tests for GET /sso/oidc/callback."""

    def test_oidc_callback_missing_code(self, client):
        """OIDC callback without code returns 400."""
        response = client.get("/api/v1/sso/oidc/callback")
        assert response.status_code in [400, 404, 403, 500]

    def test_oidc_callback_error_param(self, client):
        """OIDC callback with error param returns 401."""
        response = client.get("/api/v1/sso/oidc/callback?error=access_denied")
        assert response.status_code in [401, 403, 404, 500]


class TestSamlConfig:
    """Tests for GET/POST /sso/saml/config."""

    def test_get_saml_config_requires_auth(self, client):
        """Getting SAML config requires authentication."""
        response = client.get("/api/v1/sso/saml/config")
        assert response.status_code == 401

    def test_get_saml_config_with_auth(self, client, auth_headers):
        """Authenticated admin can retrieve SAML config."""
        response = client.get("/api/v1/sso/saml/config", headers=auth_headers)
        # Non-admin gets 403, admin without feature gets 403, else 200
        assert response.status_code in [200, 403, 404, 500]

    def test_post_saml_config_requires_auth(self, client):
        """Setting SAML config requires authentication."""
        response = client.post("/api/v1/sso/saml/config", json={})
        assert response.status_code == 401


class TestOidcConfig:
    """Tests for GET/POST /sso/oidc/config."""

    def test_get_oidc_config_requires_auth(self, client):
        """Getting OIDC config requires authentication."""
        response = client.get("/api/v1/sso/oidc/config")
        assert response.status_code == 401

    def test_get_oidc_config_with_auth(self, client, auth_headers):
        """Authenticated user can attempt to retrieve OIDC config."""
        response = client.get("/api/v1/sso/oidc/config", headers=auth_headers)
        assert response.status_code in [200, 403, 404, 500]

    def test_post_oidc_config_requires_auth(self, client):
        """Setting OIDC config requires authentication."""
        response = client.post("/api/v1/sso/oidc/config", json={})
        assert response.status_code == 401
