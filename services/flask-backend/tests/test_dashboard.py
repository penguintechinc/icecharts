"""Tests for Dashboard API endpoints."""

import pytest


class TestDashboardStats:
    """Tests for GET /dashboard/stats."""

    def test_get_stats_requires_auth(self, client):
        """Getting dashboard stats requires authentication."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 401

    def test_get_stats_with_auth(self, client, auth_headers):
        """Authenticated user can get dashboard stats."""
        response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "totalDrawings" in data
        assert "totalCollections" in data
        assert "totalGroups" in data


class TestDashboardActivity:
    """Tests for GET /dashboard/activity."""

    def test_get_activity_requires_auth(self, client):
        """Getting activity feed requires authentication."""
        response = client.get("/api/v1/dashboard/activity")
        assert response.status_code == 401

    def test_get_activity_with_auth(self, client, auth_headers):
        """Authenticated user can get activity feed."""
        response = client.get("/api/v1/dashboard/activity", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "total" in data

    def test_get_activity_pagination(self, client, auth_headers):
        """Activity feed supports limit and offset query parameters."""
        response = client.get(
            "/api/v1/dashboard/activity?limit=5&offset=0",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDashboardStorage:
    """Tests for GET /dashboard/storage."""

    def test_get_storage_requires_auth(self, client):
        """Getting storage widget data requires authentication."""
        response = client.get("/api/v1/dashboard/storage")
        assert response.status_code == 401

    def test_get_storage_with_auth(self, client, auth_headers):
        """Authenticated user can get storage widget data."""
        response = client.get("/api/v1/dashboard/storage", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "storage" in data
