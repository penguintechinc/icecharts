"""Tests for Service Accounts API.

Tests cover:
- Service account CRUD operations
- Token generation and management
- Scope enforcement
- Authentication with service tokens
"""

import json
from datetime import datetime, timedelta

import pytest


class TestServiceAccountScopes:
    """Tests for the scopes module."""

    def test_is_valid_scope(self):
        """Test scope validation."""
        from app.auth.scopes import is_valid_scope

        assert is_valid_scope("drawings:read") is True
        assert is_valid_scope("drawings:write") is True
        assert is_valid_scope("invalid:scope") is False
        assert is_valid_scope("") is False

    def test_validate_scopes(self):
        """Test batch scope validation."""
        from app.auth.scopes import validate_scopes

        # Valid scopes
        is_valid, invalid = validate_scopes(["drawings:read", "exports:create"])
        assert is_valid is True
        assert invalid == []

        # Mixed valid/invalid
        is_valid, invalid = validate_scopes(["drawings:read", "invalid:scope"])
        assert is_valid is False
        assert "invalid:scope" in invalid

    def test_has_scope(self):
        """Test single scope checking."""
        from app.auth.scopes import has_scope

        token_scopes = ["drawings:read", "drawings:write"]
        assert has_scope(token_scopes, "drawings:read") is True
        assert has_scope(token_scopes, "drawings:delete") is False

    def test_has_all_scopes(self):
        """Test checking for all required scopes."""
        from app.auth.scopes import has_all_scopes

        token_scopes = ["drawings:read", "drawings:write", "exports:create"]
        assert has_all_scopes(token_scopes, ["drawings:read", "drawings:write"]) is True
        assert has_all_scopes(token_scopes, ["drawings:read", "templates:read"]) is False

    def test_get_missing_scopes(self):
        """Test getting missing scopes."""
        from app.auth.scopes import get_missing_scopes

        token_scopes = ["drawings:read"]
        required = ["drawings:read", "drawings:write", "exports:create"]
        missing = get_missing_scopes(token_scopes, required)
        assert "drawings:write" in missing
        assert "exports:create" in missing
        assert "drawings:read" not in missing


class TestServiceAccountManagement:
    """Tests for service account admin endpoints."""

    def test_list_service_accounts_requires_auth(self, client):
        """Test that listing service accounts requires authentication."""
        response = client.get("/api/v1/admin/service-accounts")
        assert response.status_code == 401

    def test_list_service_accounts_requires_admin(self, client, auth_headers):
        """Test that listing service accounts requires admin role."""
        response = client.get(
            "/api/v1/admin/service-accounts",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_service_account(self, client, admin_auth_headers):
        """Test creating a service account."""
        data = {
            "name": "Test Integration",
            "description": "Test service account",
            "scopes": ["drawings:read", "drawings:write"],
            "rate_limit": 500,
        }
        response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.get_json()
        assert result["success"] is True
        assert result["service_account"]["name"] == "Test Integration"
        assert "client_id" in result["service_account"]
        assert result["service_account"]["client_id"].startswith("sa_")

    def test_create_service_account_invalid_scopes(self, client, admin_auth_headers):
        """Test creating a service account with invalid scopes."""
        data = {
            "name": "Invalid Service Account",
            "scopes": ["invalid:scope"],
        }
        response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.get_json()
        assert "invalid" in result["error"].lower()

    def test_create_service_account_no_scopes(self, client, admin_auth_headers):
        """Test creating a service account without scopes."""
        data = {
            "name": "No Scopes Account",
        }
        response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_available_scopes(self, client, admin_auth_headers):
        """Test getting list of available scopes."""
        response = client.get(
            "/api/v1/admin/service-accounts/scopes",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        result = response.get_json()
        assert "scopes" in result
        assert "drawings:read" in result["scopes"]
        assert "scope_groups" in result


class TestServiceAccountTokens:
    """Tests for service account token management."""

    @pytest.fixture
    def service_account(self, client, admin_auth_headers):
        """Create a service account for testing."""
        data = {
            "name": "Token Test Account",
            "scopes": ["drawings:read", "drawings:write"],
        }
        response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        result = response.get_json()
        return result["service_account"]

    def test_generate_token(self, client, admin_auth_headers, service_account):
        """Test generating a service account token."""
        data = {
            "name": "Test Token",
            "expires_days": 30,
        }
        response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.get_json()
        assert "token" in result
        assert "token_info" in result
        assert result["token_info"]["name"] == "Test Token"

    def test_list_tokens(self, client, admin_auth_headers, service_account):
        """Test listing service account tokens."""
        # Generate a token first
        client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "Token 1"}),
            content_type="application/json",
        )

        response = client.get(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        result = response.get_json()
        assert "tokens" in result
        assert len(result["tokens"]) >= 1

    def test_revoke_token(self, client, admin_auth_headers, service_account):
        """Test revoking a service account token."""
        # Generate a token
        gen_response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "To Revoke"}),
            content_type="application/json",
        )
        token_info = gen_response.get_json()["token_info"]

        # Revoke it
        response = client.delete(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens/{token_info['token_jti']}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200


class TestServiceTokenAuthentication:
    """Tests for authenticating with service tokens."""

    @pytest.fixture
    def service_token(self, client, admin_auth_headers):
        """Create a service account and generate a token."""
        # Create service account
        sa_data = {
            "name": "Auth Test Account",
            "scopes": ["drawings:read", "drawings:write"],
        }
        sa_response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(sa_data),
            content_type="application/json",
        )
        service_account = sa_response.get_json()["service_account"]

        # Generate token
        token_response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "Auth Test Token"}),
            content_type="application/json",
        )
        return token_response.get_json()["token"]

    def test_service_token_access_drawings(self, client, service_token):
        """Test accessing drawings with service token."""
        headers = {"Authorization": f"Bearer {service_token}"}
        response = client.get("/api/v1/drawings", headers=headers)
        assert response.status_code == 200

    def test_service_token_create_drawing(self, client, service_token):
        """Test creating a drawing with service token."""
        headers = {"Authorization": f"Bearer {service_token}"}
        data = {
            "name": "Service Account Drawing",
            "content": {"nodes": [], "edges": []},
            "visibility": "private",
        }
        response = client.post(
            "/api/v1/drawings",
            headers=headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 201


class TestScopeEnforcement:
    """Tests for scope-based access control."""

    @pytest.fixture
    def readonly_service_token(self, client, admin_auth_headers):
        """Create a service account with only read scope."""
        # Create service account with only read scope
        sa_data = {
            "name": "Readonly Account",
            "scopes": ["drawings:read"],  # Only read scope
        }
        sa_response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(sa_data),
            content_type="application/json",
        )
        service_account = sa_response.get_json()["service_account"]

        # Generate token
        token_response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "Readonly Token"}),
            content_type="application/json",
        )
        return token_response.get_json()["token"]

    def test_scope_blocks_write_without_scope(self, client, readonly_service_token):
        """Test that write operations are blocked without drawings:write scope."""
        headers = {"Authorization": f"Bearer {readonly_service_token}"}
        data = {
            "name": "Should Fail",
            "content": {"nodes": [], "edges": []},
        }
        response = client.post(
            "/api/v1/drawings",
            headers=headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403
        result = response.get_json()
        assert "scope" in result["error"].lower()
        assert "drawings:write" in result.get("missing_scopes", [])

    def test_scope_allows_read_with_scope(self, client, readonly_service_token):
        """Test that read operations work with drawings:read scope."""
        headers = {"Authorization": f"Bearer {readonly_service_token}"}
        response = client.get("/api/v1/drawings", headers=headers)
        assert response.status_code == 200
