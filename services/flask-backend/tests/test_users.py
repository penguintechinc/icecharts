"""Tests for Users API endpoints."""
import pytest


class TestUserSearch:
    """Tests for GET /users/search."""

    def test_search_users_requires_auth(self, client):
        """Searching users requires authentication."""
        response = client.get("/api/v1/users/search?q=test")
        assert response.status_code == 401

    def test_search_users_empty_query(self, client, auth_headers):
        """Empty search query returns empty list."""
        response = client.get("/api/v1/users/search?q=", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["users"] == []

    def test_search_users_short_query(self, client, auth_headers):
        """Query shorter than 2 chars returns empty list."""
        response = client.get("/api/v1/users/search?q=a", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["users"] == []

    def test_search_users_with_query(self, client, auth_headers):
        """Valid search query returns users list."""
        response = client.get("/api/v1/users/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert isinstance(data["users"], list)


class TestGetUser:
    """Tests for GET /users/<user_id>."""

    def test_get_user_requires_auth(self, client):
        """Getting a user requires authentication."""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 401

    def test_get_user_not_found(self, client, auth_headers):
        """Non-existent user returns 404."""
        response = client.get("/api/v1/users/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_user_found(self, client, auth_headers, test_user):
        """Existing user returns user data."""
        response = client.get(
            f"/api/v1/users/{test_user['id']}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data
        assert data["user"]["id"] == test_user["id"]
