"""Tests for Admin Statistics API endpoints."""

import pytest


class TestAdminDashboardStats:
    """Tests for GET /admin/statistics/dashboard."""

    def test_get_dashboard_stats_requires_auth(self, client):
        """Getting admin stats requires authentication."""
        response = client.get("/api/v1/admin/statistics/dashboard")
        assert response.status_code == 401

    def test_get_dashboard_stats_requires_admin(self, client, auth_headers):
        """Getting admin stats requires admin role."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard", headers=auth_headers
        )
        assert response.status_code == 403

    def test_get_dashboard_stats_as_admin(self, client, admin_auth_headers):
        """Admin can get dashboard statistics."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard", headers=admin_auth_headers
        )
        assert response.status_code == 200

    def test_get_dashboard_stats_invalid_time_range(self, client, admin_auth_headers):
        """Invalid time_range query param returns 400."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=forever",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400


class TestTimeSeriesStats:
    """Tests for GET /admin/statistics/time-series/<metric>."""

    def test_time_series_requires_auth(self, client):
        """Getting time series requires authentication."""
        response = client.get("/api/v1/admin/statistics/time-series/users")
        assert response.status_code == 401

    def test_time_series_requires_admin(self, client, auth_headers):
        """Getting time series requires admin role."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_time_series_invalid_metric(self, client, admin_auth_headers):
        """Invalid metric returns 400."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/invalid_metric",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_time_series_valid_metric(self, client, admin_auth_headers):
        """Valid metric returns time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200


class TestLatencyStats:
    """Tests for GET /admin/statistics/latency."""

    def test_latency_requires_auth(self, client):
        """Getting latency metrics requires authentication."""
        response = client.get("/api/v1/admin/statistics/latency")
        assert response.status_code == 401

    def test_latency_requires_admin(self, client, auth_headers):
        """Getting latency metrics requires admin role."""
        response = client.get("/api/v1/admin/statistics/latency", headers=auth_headers)
        assert response.status_code == 403

    def test_latency_as_admin(self, client, admin_auth_headers):
        """Admin can get latency metrics."""
        response = client.get(
            "/api/v1/admin/statistics/latency", headers=admin_auth_headers
        )
        assert response.status_code == 200


class TestTopUsersStats:
    """Tests for GET /admin/statistics/top-users."""

    def test_top_users_requires_auth(self, client):
        """Getting top users requires authentication."""
        response = client.get("/api/v1/admin/statistics/top-users")
        assert response.status_code == 401

    def test_top_users_requires_admin(self, client, auth_headers):
        """Getting top users requires admin role."""
        response = client.get(
            "/api/v1/admin/statistics/top-users", headers=auth_headers
        )
        assert response.status_code == 403

    def test_top_users_invalid_limit(self, client, admin_auth_headers):
        """Limit outside 1-100 returns 400."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=0",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400


class TestTopDrawingsStats:
    """Tests for GET /admin/statistics/top-drawings."""

    def test_top_drawings_requires_auth(self, client):
        """Getting top drawings requires authentication."""
        response = client.get("/api/v1/admin/statistics/top-drawings")
        assert response.status_code == 401

    def test_top_drawings_requires_admin(self, client, auth_headers):
        """Getting top drawings requires admin role."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings", headers=auth_headers
        )
        assert response.status_code == 403

    def test_top_drawings_as_admin(self, client, admin_auth_headers):
        """Admin can get top drawings."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings", headers=admin_auth_headers
        )
        assert response.status_code == 200


class TestLoginsByCountryStats:
    """Tests for GET /admin/statistics/logins-by-country."""

    def test_logins_by_country_requires_auth(self, client):
        """Getting logins by country requires authentication."""
        response = client.get("/api/v1/admin/statistics/logins-by-country")
        assert response.status_code == 401

    def test_logins_by_country_requires_admin(self, client, auth_headers):
        """Getting logins by country requires admin role."""
        response = client.get(
            "/api/v1/admin/statistics/logins-by-country", headers=auth_headers
        )
        assert response.status_code == 403

    def test_logins_by_country_as_admin(self, client, admin_auth_headers):
        """Admin can get logins by country."""
        response = client.get(
            "/api/v1/admin/statistics/logins-by-country",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "countries" in data
