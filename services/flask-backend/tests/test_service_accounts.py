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


class TestServiceAccountErrorPaths:
    """Tests for service account admin endpoint error handling."""

    @pytest.fixture
    def service_account(self, client, admin_auth_headers):
        """Create a service account for testing."""
        data = {
            "name": "Error Test Account",
            "scopes": ["drawings:read"],
        }
        response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        result = response.get_json()
        return result["service_account"]

    def test_update_service_account_invalid_scopes_returns_available(
        self, client, admin_auth_headers, service_account
    ):
        """Test that updating with invalid scopes returns available scopes."""
        data = {
            "name": "Updated Name",
            "scopes": ["invalid:scope", "also:invalid"],
        }
        response = client.put(
            f"/api/v1/admin/service-accounts/{service_account['id']}",
            headers=admin_auth_headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 400
        result = response.get_json()
        # Should include available scopes in error response
        assert "available_scopes" in result or "details" in result

    def test_delete_nonexistent_service_account_returns_404(
        self, client, admin_auth_headers
    ):
        """Test that deleting a non-existent service account returns 404."""
        # Use a very large ID that doesn't exist
        response = client.delete(
            "/api/v1/admin/service-accounts/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_generate_token_invalid_expires_days(
        self, client, admin_auth_headers, service_account
    ):
        """Test that invalid expires_days values are rejected."""
        invalid_values = [0, -1, 999999]

        for invalid_value in invalid_values:
            response = client.post(
                f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
                headers=admin_auth_headers,
                data=json.dumps({"expires_days": invalid_value}),
                content_type="application/json",
            )
            assert response.status_code == 400, f"Expected 400 for expires_days={invalid_value}"

    def test_get_nonexistent_service_account_returns_404(
        self, client, admin_auth_headers
    ):
        """Test that getting a non-existent service account returns 404."""
        response = client.get(
            "/api/v1/admin/service-accounts/999999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestTokenRevocationEffects:
    """Tests to verify token revocation behavior."""

    @pytest.fixture
    def service_account_with_token(self, client, admin_auth_headers):
        """Create a service account and generate a token."""
        # Create service account
        sa_data = {
            "name": "Revocation Test Account",
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
            data=json.dumps({"name": "Revocation Test Token"}),
            content_type="application/json",
        )
        token_data = token_response.get_json()

        return {
            "service_account": service_account,
            "token": token_data["token"],
            "token_info": token_data["token_info"],
        }

    def test_revoked_token_omitted_when_include_revoked_false(
        self, client, admin_auth_headers, service_account_with_token
    ):
        """Test that revoked tokens are omitted when include_revoked=false."""
        sa = service_account_with_token["service_account"]
        token_info = service_account_with_token["token_info"]

        # Revoke the token
        client.delete(
            f"/api/v1/admin/service-accounts/{sa['id']}/tokens/{token_info['token_jti']}",
            headers=admin_auth_headers,
        )

        # List tokens without revoked
        response = client.get(
            f"/api/v1/admin/service-accounts/{sa['id']}/tokens",
            headers=admin_auth_headers,
            query_string={"include_revoked": "false"},
        )
        assert response.status_code == 200
        result = response.get_json()
        tokens = result["tokens"]

        # Revoked token should not be in the list
        token_jtis = [t["token_jti"] for t in tokens]
        assert token_info["token_jti"] not in token_jtis

    def test_revoked_token_flagged_when_include_revoked_true(
        self, client, admin_auth_headers, service_account_with_token
    ):
        """Test that revoked tokens show revoked_at when include_revoked=true."""
        sa = service_account_with_token["service_account"]
        token_info = service_account_with_token["token_info"]

        # Revoke the token
        client.delete(
            f"/api/v1/admin/service-accounts/{sa['id']}/tokens/{token_info['token_jti']}",
            headers=admin_auth_headers,
        )

        # List tokens with revoked
        response = client.get(
            f"/api/v1/admin/service-accounts/{sa['id']}/tokens",
            headers=admin_auth_headers,
            query_string={"include_revoked": "true"},
        )
        assert response.status_code == 200
        result = response.get_json()
        tokens = result["tokens"]

        # Find our revoked token
        revoked_token = next(
            (t for t in tokens if t["token_jti"] == token_info["token_jti"]),
            None
        )
        assert revoked_token is not None
        assert revoked_token["revoked_at"] is not None

    def test_revoked_service_token_is_rejected(
        self, client, admin_auth_headers, service_account_with_token
    ):
        """Test that revoked service tokens cannot authenticate requests."""
        sa = service_account_with_token["service_account"]
        token = service_account_with_token["token"]
        token_info = service_account_with_token["token_info"]

        # First verify the token works
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/drawings", headers=headers)
        assert response.status_code == 200

        # Revoke the token
        client.delete(
            f"/api/v1/admin/service-accounts/{sa['id']}/tokens/{token_info['token_jti']}",
            headers=admin_auth_headers,
        )

        # Now the token should be rejected
        response = client.get("/api/v1/drawings", headers=headers)
        assert response.status_code == 401


class TestBroaderScopeEnforcement:
    """Tests for scope enforcement across different endpoints and scopes."""

    @pytest.fixture
    def templates_read_token(self, client, admin_auth_headers):
        """Create a service account with templates:read scope."""
        sa_data = {
            "name": "Templates Reader",
            "scopes": ["templates:read"],
        }
        sa_response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(sa_data),
            content_type="application/json",
        )
        service_account = sa_response.get_json()["service_account"]

        token_response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "Templates Read Token"}),
            content_type="application/json",
        )
        return token_response.get_json()["token"]

    @pytest.fixture
    def templates_write_token(self, client, admin_auth_headers):
        """Create a service account with templates:write scope."""
        sa_data = {
            "name": "Templates Writer",
            "scopes": ["templates:write"],
        }
        sa_response = client.post(
            "/api/v1/admin/service-accounts",
            headers=admin_auth_headers,
            data=json.dumps(sa_data),
            content_type="application/json",
        )
        service_account = sa_response.get_json()["service_account"]

        token_response = client.post(
            f"/api/v1/admin/service-accounts/{service_account['id']}/tokens",
            headers=admin_auth_headers,
            data=json.dumps({"name": "Templates Write Token"}),
            content_type="application/json",
        )
        return token_response.get_json()["token"]

    def test_templates_read_allows_list_but_denies_create(
        self, client, templates_read_token
    ):
        """Test that templates:read allows listing but denies creation."""
        headers = {"Authorization": f"Bearer {templates_read_token}"}

        # List should work
        response = client.get("/api/v1/templates", headers=headers)
        assert response.status_code == 200

        # Create should be denied
        data = {"name": "New Template", "content": {}}
        response = client.post(
            "/api/v1/templates",
            headers=headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_templates_write_allows_create(self, client, templates_write_token):
        """Test that templates:write allows creation."""
        headers = {"Authorization": f"Bearer {templates_write_token}"}

        data = {"name": "Created Template", "content": {}}
        response = client.post(
            "/api/v1/templates",
            headers=headers,
            data=json.dumps(data),
            content_type="application/json",
        )
        # Should succeed (or fail for reasons other than scopes)
        assert response.status_code in [200, 201, 400]  # Not 403
        if response.status_code == 403:
            result = response.get_json()
            # If it's 403, it shouldn't be a scope issue
            assert "scope" not in result.get("error", "").lower()
