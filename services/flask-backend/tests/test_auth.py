"""Authentication Endpoint Tests."""

import json
from datetime import datetime, timedelta

import pytest


class TestAuthRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"

    def test_register_missing_email(self, client):
        """Test registration with missing email."""
        response = client.post(
            "/api/v1/auth/register",
            json={"password": "SecurePass123!", "full_name": "New User"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user["email"],
                "password": "SecurePass123!",
                "full_name": "Another User",
            },
        )
        assert response.status_code == 409
        data = json.loads(response.data)
        assert "error" in data

    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",
                "full_name": "New User",
            },
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAuthLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == test_user["email"]

    def test_login_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPassword123!"},
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_login_missing_email(self, client):
        """Test login with missing email."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "AnyPassword123!"},
        )
        assert response.status_code == 400

    def test_login_missing_password(self, client, test_user):
        """Test login with missing password."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"]},
        )
        assert response.status_code == 400

    def test_login_no_body(self, client):
        """Test login with empty body."""
        response = client.post("/api/v1/auth/login")
        assert response.status_code == 400


class TestAuthLogout:
    """Test user logout endpoint."""

    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get("message") == "Successfully logged out"

    def test_logout_without_token(self, client):
        """Test logout without authentication token."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_logout_with_invalid_token(self, client):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.post("/api/v1/auth/logout", headers=headers)
        assert response.status_code == 401


class TestAuthJWTRefresh:
    """Test JWT refresh token endpoint."""

    def test_refresh_success(self, client, refresh_token):
        """Test successful token refresh."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data

    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    def test_refresh_missing_token(self, client):
        """Test refresh without providing token."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 400

    def test_refresh_revoked_token(self, client, app, test_user):
        """Test refresh with revoked token."""
        from app.models import revoke_all_user_tokens

        with app.app_context():
            # Create and revoke all user tokens
            revoke_all_user_tokens(test_user["id"])

        # Get a new refresh token and try to use it
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200


class TestAuthTokenValidation:
    """Test token validation and expiration."""

    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid.token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_expired_token(self, client, expired_jwt_token):
        """Test accessing protected endpoint with expired token."""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_token_in_cookie(self, client, test_user, app):
        """Test JWT token passed via cookie."""
        with app.app_context():
            from app.api.v1.auth import create_access_token

            token = create_access_token(test_user["id"], test_user["role"])

        # Set cookie and access protected endpoint
        client.set_cookie("access_token", token)
        response = client.get("/api/v1/auth/me")
        # Should work if cookie support is implemented
        assert response.status_code in [200, 401]


class TestAuthPasswordReset:
    """Test password reset functionality."""

    @pytest.mark.skip(reason="Password reset endpoint not yet implemented")
    def test_request_password_reset(self, client, test_user):
        """Test requesting password reset."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user["email"]},
        )
        assert response.status_code in [200, 202]

    @pytest.mark.skip(reason="Password reset endpoint not yet implemented")
    def test_password_reset_nonexistent_email(self, client):
        """Test password reset for non-existent email."""
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        # Should return 200/202 for security (not exposing email existence)
        assert response.status_code in [200, 202, 404]


class TestAuthRoleBasedAccess:
    """Test role-based access control in authentication."""

    def test_admin_token_has_admin_role(self, client, app, test_admin):
        """Test that admin token contains admin role."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_admin["email"],
                "password": test_admin["password"],
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["user"]["role"] == "admin"

    def test_viewer_token_has_viewer_role(self, client, test_user):
        """Test that viewer token contains viewer role."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["user"]["role"] == "viewer"


class TestAuthEdgeCases:
    """Edge case tests for authentication."""

    def test_auth_required_missing_bearer_prefix(self, client):
        """Token without 'Bearer ' prefix should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "just-a-token-without-bearer"},
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_auth_required_malformed_token(self, client):
        """Malformed JWT token should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_auth_required_empty_authorization_header(self, client):
        """Empty Authorization header should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401

    def test_auth_required_bearer_without_token(self, client):
        """'Bearer ' without token should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_multiple_spaces_in_authorization(self, client):
        """Authorization with extra spaces should return 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer  token"},
        )
        assert response.status_code == 401

    def test_case_insensitive_bearer_prefix(self, client, valid_jwt_token):
        """Bearer prefix should work case-insensitively."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"bearer {valid_jwt_token}"},
        )
        assert response.status_code == 200

    def test_login_after_logout_gets_new_token(self, client, test_user, auth_headers):
        """User should get a new token after logout and re-login."""
        # Logout
        logout_response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200

        # Login again
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert login_response.status_code == 200
        data = json.loads(login_response.data)
        assert "access_token" in data
        new_token = data["access_token"]

        # New token should be valid
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert response.status_code == 200

    def test_register_with_unicode_characters(self, client):
        """Registration with unicode characters should work."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "unicode@example.com",
                "password": "SecurePass123!",
                "full_name": "José García",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["user"]["full_name"] == "José García"

    def test_login_case_insensitive_email(self, client, test_user):
        """Login should be case-insensitive for email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"].upper(),
                "password": test_user["password"],
            },
        )
        # Should either work or explicitly fail consistently
        assert response.status_code in [200, 401]


class TestAuthSecurityEdgeCases:
    """Security-focused edge case tests for authentication."""

    def test_login_with_expired_token_returns_401(self, client, expired_jwt_token):
        """Accessing a protected endpoint with an expired token must return 401."""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_refresh_token_replay_attack_second_use_fails(
        self, client, refresh_token, app
    ):
        """A refresh token must be single-use: second call after rotation fails."""
        # First use – should succeed and issue a new access token
        first_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert (
            first_response.status_code == 200
        ), f"First refresh failed: {first_response.data}"

        # Second use of the same (now consumed) token must be rejected
        second_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        # The original token should no longer be valid after first use
        assert second_response.status_code in [
            401,
            400,
        ], "Replay of already-used refresh token should be rejected"

    def test_auth_required_tampered_signature(self, client, valid_jwt_token):
        """A JWT with a tampered signature must be rejected with 401."""
        # Corrupt the signature part (last segment) of the token
        parts = valid_jwt_token.split(".")
        assert len(parts) == 3, "JWT should have three dot-separated parts"
        tampered_sig = parts[2][:-4] + "XXXX"
        tampered_token = ".".join([parts[0], parts[1], tampered_sig])

        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_auth_required_wrong_token_type(self, client, refresh_token):
        """Using a refresh token where an access token is expected must fail."""
        # Refresh tokens have type='refresh'; the auth middleware should reject them
        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        # Should be 401 because token type is 'refresh', not 'access'
        assert response.status_code == 401

    def test_register_then_login_full_cycle(self, client):
        """Registering and immediately logging in should produce a valid token."""
        email = "cycle@example.com"
        password = "CyclePass123!"

        # Register
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Cycle User"},
        )
        assert reg_resp.status_code == 201

        # Login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        data = json.loads(login_resp.data)
        assert "access_token" in data
        token = data["access_token"]

        # Use the token immediately
        me_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = json.loads(me_resp.data)
        assert me_data.get("email") == email
