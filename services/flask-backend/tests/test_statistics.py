"""Admin Statistics and Dashboard Tests."""

import json

import pytest


class TestAdminStatisticsDashboard:
    """Test admin statistics dashboard endpoints."""

    def test_get_dashboard_stats_as_admin(self, client, admin_auth_headers):
        """Test admin can access dashboard statistics."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should contain various metrics
        assert isinstance(data, dict)

    def test_get_dashboard_stats_without_auth(self, client):
        """Test dashboard stats requires authentication."""
        response = client.get("/api/v1/admin/statistics/dashboard")
        assert response.status_code == 401

    def test_get_dashboard_stats_non_admin_forbidden(self, client, auth_headers):
        """Test non-admin user gets 403 forbidden."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_dashboard_stats_with_time_range_1h(self, client, admin_auth_headers):
        """Test dashboard stats with 1 hour time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_dashboard_stats_with_time_range_24h(self, client, admin_auth_headers):
        """Test dashboard stats with 24 hour time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=24h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_stats_with_time_range_7d(self, client, admin_auth_headers):
        """Test dashboard stats with 7 day time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=7d",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_stats_with_time_range_30d(self, client, admin_auth_headers):
        """Test dashboard stats with 30 day time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=30d",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_stats_with_time_range_90d(self, client, admin_auth_headers):
        """Test dashboard stats with 90 day time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=90d",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_stats_with_time_range_all(self, client, admin_auth_headers):
        """Test dashboard stats with all-time time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=all",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_dashboard_stats_invalid_time_range(self, client, admin_auth_headers):
        """Test dashboard stats with invalid time range."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard?time_range=invalid",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestAdminStatisticsTimeSeries:
    """Test admin time series statistics endpoints."""

    def test_get_users_time_series(self, client, admin_auth_headers):
        """Test getting users time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metric"] == "users"
        assert "data" in data

    def test_get_drawings_time_series(self, client, admin_auth_headers):
        """Test getting drawings time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/drawings?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metric"] == "drawings"
        assert "data" in data

    def test_get_collections_time_series(self, client, admin_auth_headers):
        """Test getting collections time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/collections?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metric"] == "collections"
        assert "data" in data

    def test_get_shares_time_series(self, client, admin_auth_headers):
        """Test getting shares time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/shares?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metric"] == "shares"
        assert "data" in data

    def test_get_collaborations_time_series(self, client, admin_auth_headers):
        """Test getting collaborations time series data."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/collaborations?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["metric"] == "collaborations"
        assert "data" in data

    def test_time_series_invalid_metric(self, client, admin_auth_headers):
        """Test time series with invalid metric."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/invalid_metric?time_range=7d&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_time_series_invalid_time_range(self, client, admin_auth_headers):
        """Test time series with invalid time range."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users?time_range=invalid&interval=1h",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_time_series_invalid_interval(self, client, admin_auth_headers):
        """Test time series with invalid interval."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=invalid",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_time_series_various_intervals(self, client, admin_auth_headers):
        """Test time series with various valid intervals."""
        intervals = ["5m", "15m", "1h", "6h", "1d"]
        for interval in intervals:
            response = client.get(
                f"/api/v1/admin/statistics/time-series/users?time_range=7d&interval={interval}",
                headers=admin_auth_headers,
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["interval"] == interval

    def test_time_series_non_admin_forbidden(self, client, auth_headers):
        """Test non-admin user cannot access time series."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=1h",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminStatisticsLatency:
    """Test admin latency metrics endpoints."""

    def test_get_latency_metrics_as_admin(self, client, admin_auth_headers):
        """Test admin can access latency metrics."""
        response = client.get(
            "/api/v1/admin/statistics/latency",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_get_latency_metrics_without_auth(self, client):
        """Test latency metrics requires authentication."""
        response = client.get("/api/v1/admin/statistics/latency")
        assert response.status_code == 401

    def test_get_latency_metrics_non_admin_forbidden(self, client, auth_headers):
        """Test non-admin user cannot access latency metrics."""
        response = client.get(
            "/api/v1/admin/statistics/latency",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminStatisticsTopUsers:
    """Test admin top users statistics endpoints."""

    def test_get_top_users_default_limit(self, client, admin_auth_headers):
        """Test getting top users with default limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-users",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data
        assert "count" in data
        assert isinstance(data["users"], list)

    def test_get_top_users_custom_limit(self, client, admin_auth_headers):
        """Test getting top users with custom limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=5",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) <= 5

    def test_get_top_users_limit_1(self, client, admin_auth_headers):
        """Test getting top 1 user."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=1",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) <= 1

    def test_get_top_users_limit_100(self, client, admin_auth_headers):
        """Test getting top 100 users (max limit)."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=100",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "users" in data

    def test_get_top_users_invalid_limit_zero(self, client, admin_auth_headers):
        """Test top users with invalid limit (0)."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=0",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_get_top_users_invalid_limit_negative(self, client, admin_auth_headers):
        """Test top users with negative limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=-5",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_get_top_users_invalid_limit_exceeds_max(self, client, admin_auth_headers):
        """Test top users with limit exceeding maximum."""
        response = client.get(
            "/api/v1/admin/statistics/top-users?limit=101",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_get_top_users_without_auth(self, client):
        """Test top users requires authentication."""
        response = client.get("/api/v1/admin/statistics/top-users")
        assert response.status_code == 401

    def test_get_top_users_non_admin_forbidden(self, client, auth_headers):
        """Test non-admin user cannot access top users."""
        response = client.get(
            "/api/v1/admin/statistics/top-users",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminStatisticsTopDrawings:
    """Test admin top drawings statistics endpoints."""

    def test_get_top_drawings_default_limit(self, client, admin_auth_headers):
        """Test getting top drawings with default limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "drawings" in data
        assert "count" in data
        assert isinstance(data["drawings"], list)

    def test_get_top_drawings_custom_limit(self, client, admin_auth_headers):
        """Test getting top drawings with custom limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=5",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "drawings" in data
        assert len(data["drawings"]) <= 5

    def test_get_top_drawings_limit_1(self, client, admin_auth_headers):
        """Test getting top 1 drawing."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=1",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "drawings" in data
        assert len(data["drawings"]) <= 1

    def test_get_top_drawings_limit_100(self, client, admin_auth_headers):
        """Test getting top 100 drawings (max limit)."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=100",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "drawings" in data

    def test_get_top_drawings_invalid_limit_zero(self, client, admin_auth_headers):
        """Test top drawings with invalid limit (0)."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=0",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_get_top_drawings_invalid_limit_negative(self, client, admin_auth_headers):
        """Test top drawings with negative limit."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=-5",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_get_top_drawings_invalid_limit_exceeds_max(
        self, client, admin_auth_headers
    ):
        """Test top drawings with limit exceeding maximum."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings?limit=101",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_get_top_drawings_without_auth(self, client):
        """Test top drawings requires authentication."""
        response = client.get("/api/v1/admin/statistics/top-drawings")
        assert response.status_code == 401

    def test_get_top_drawings_non_admin_forbidden(self, client, auth_headers):
        """Test non-admin user cannot access top drawings."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestAdminAccessControl:
    """Test admin-only access control for statistics endpoints."""

    def test_viewer_cannot_access_dashboard_stats(self, client, auth_headers):
        """Test viewer role cannot access dashboard stats."""
        response = client.get(
            "/api/v1/admin/statistics/dashboard",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_top_users(self, client, auth_headers):
        """Test viewer role cannot access top users."""
        response = client.get(
            "/api/v1/admin/statistics/top-users",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_top_drawings(self, client, auth_headers):
        """Test viewer role cannot access top drawings."""
        response = client.get(
            "/api/v1/admin/statistics/top-drawings",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_latency_metrics(self, client, auth_headers):
        """Test viewer role cannot access latency metrics."""
        response = client.get(
            "/api/v1/admin/statistics/latency",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_time_series(self, client, auth_headers):
        """Test viewer role cannot access time series."""
        response = client.get(
            "/api/v1/admin/statistics/time-series/users",
            headers=auth_headers,
        )
        assert response.status_code == 403
