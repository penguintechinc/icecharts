"""Admin statistics API endpoints."""

from app.middleware import admin_required, auth_required
from app.services.statistics_service import StatisticsService
from flask import Blueprint, jsonify, request

# Create admin statistics blueprint
admin_stats_v1_bp = Blueprint(
    "admin_stats_v1", __name__, url_prefix="/admin/statistics"
)


@admin_stats_v1_bp.route("/dashboard", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics.

    Query params:
        time_range: Time range for statistics (1h, 24h, 7d, 30d, 90d, all)
                   Default: 7d

    Returns:
        200: Dashboard statistics
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/dashboard?time_range=7d
    """
    time_range = request.args.get("time_range", "7d")

    # Validate time_range
    valid_ranges = ["1h", "24h", "7d", "30d", "90d", "all"]
    if time_range not in valid_ranges:
        return (
            jsonify({"error": "Invalid time_range", "valid_values": valid_ranges}),
            400,
        )

    try:
        stats = StatisticsService.get_dashboard_stats(time_range)
        return jsonify(stats), 200
    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to retrieve dashboard statistics", "message": str(e)}
            ),
            500,
        )


@admin_stats_v1_bp.route("/time-series/<metric>", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_time_series(metric: str):
    """
    Get time series data for a specific metric.

    Path params:
        metric: Metric to query (users, drawings, collections, shares, collaborations)

    Query params:
        time_range: Time range for data (1h, 24h, 7d, 30d, 90d)
                   Default: 7d
        interval: Data point interval (5m, 15m, 1h, 6h, 1d)
                 Default: 1h

    Returns:
        200: Time series data
        400: Invalid parameters
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/time-series/users?time_range=7d&interval=1h
    """
    time_range = request.args.get("time_range", "7d")
    interval = request.args.get("interval", "1h")

    # Validate metric
    valid_metrics = [
        "users",
        "drawings",
        "collections",
        "shares",
        "collaborations",
        "logins",
    ]
    if metric not in valid_metrics:
        return jsonify({"error": "Invalid metric", "valid_values": valid_metrics}), 400

    # Validate time_range
    valid_ranges = ["1h", "24h", "7d", "30d", "90d"]
    if time_range not in valid_ranges:
        return (
            jsonify({"error": "Invalid time_range", "valid_values": valid_ranges}),
            400,
        )

    # Validate interval
    valid_intervals = ["5m", "15m", "1h", "6h", "1d"]
    if interval not in valid_intervals:
        return (
            jsonify({"error": "Invalid interval", "valid_values": valid_intervals}),
            400,
        )

    try:
        data = StatisticsService.get_time_series_data(metric, time_range, interval)
        return (
            jsonify(
                {
                    "metric": metric,
                    "time_range": time_range,
                    "interval": interval,
                    "data": data,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to retrieve time series data", "message": str(e)}
            ),
            500,
        )


@admin_stats_v1_bp.route("/latency", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_latency_metrics():
    """
    Get API latency metrics.

    Returns:
        200: Latency metrics
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/latency
    """
    try:
        metrics = StatisticsService.get_latency_metrics()
        return jsonify(metrics), 200
    except Exception as e:
        return (
            jsonify({"error": "Failed to retrieve latency metrics", "message": str(e)}),
            500,
        )


@admin_stats_v1_bp.route("/top-users", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_top_users():
    """
    Get most active users by drawing count.

    Query params:
        limit: Maximum number of users to return (1-100)
              Default: 10

    Returns:
        200: List of top active users
        400: Invalid parameters
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/top-users?limit=10
    """
    limit = request.args.get("limit", 10, type=int)

    # Validate limit
    if limit < 1 or limit > 100:
        return (
            jsonify(
                {"error": "Invalid limit", "message": "Limit must be between 1 and 100"}
            ),
            400,
        )

    try:
        users = StatisticsService.get_top_active_users(limit)
        return jsonify({"users": users, "count": len(users)}), 200
    except Exception as e:
        return (
            jsonify({"error": "Failed to retrieve top users", "message": str(e)}),
            500,
        )


@admin_stats_v1_bp.route("/top-drawings", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_top_drawings():
    """
    Get most shared drawings.

    Query params:
        limit: Maximum number of drawings to return (1-100)
              Default: 10

    Returns:
        200: List of most shared drawings
        400: Invalid parameters
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/top-drawings?limit=10
    """
    limit = request.args.get("limit", 10, type=int)

    # Validate limit
    if limit < 1 or limit > 100:
        return (
            jsonify(
                {"error": "Invalid limit", "message": "Limit must be between 1 and 100"}
            ),
            400,
        )

    try:
        drawings = StatisticsService.get_most_shared_drawings(limit)
        return jsonify({"drawings": drawings, "count": len(drawings)}), 200
    except Exception as e:
        return (
            jsonify({"error": "Failed to retrieve top drawings", "message": str(e)}),
            500,
        )


@admin_stats_v1_bp.route("/logins-by-country", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_logins_by_country():
    """
    Get login counts grouped by country.

    Query params:
        time_range: Time range for statistics (1h, 24h, 7d, 30d, 90d, all)
                   Default: 7d
        limit: Maximum number of countries to return (1-100)
              Default: 20

    Returns:
        200: List of countries with login counts
        400: Invalid parameters
        401: Unauthorized (not authenticated)
        403: Forbidden (not admin)

    Example:
        GET /api/v1/admin/statistics/logins-by-country?time_range=7d&limit=20
    """
    time_range = request.args.get("time_range", "7d")
    limit = request.args.get("limit", 20, type=int)

    # Validate time_range
    valid_ranges = ["1h", "24h", "7d", "30d", "90d", "all"]
    if time_range not in valid_ranges:
        return (
            jsonify({"error": "Invalid time_range", "valid_values": valid_ranges}),
            400,
        )

    # Validate limit
    if limit < 1 or limit > 100:
        return (
            jsonify(
                {"error": "Invalid limit", "message": "Limit must be between 1 and 100"}
            ),
            400,
        )

    try:
        data = StatisticsService.get_logins_by_country(time_range, limit)
        return (
            jsonify({"countries": data, "count": len(data), "time_range": time_range}),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {"error": "Failed to retrieve logins by country", "message": str(e)}
            ),
            500,
        )
