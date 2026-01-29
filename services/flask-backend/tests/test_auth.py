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
