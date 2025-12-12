"""Dashboard Endpoints for API v1.

Provides dashboard statistics and activity feed for IceCharts users.
"""

from flask import Blueprint, jsonify

from ...middleware import auth_required, get_current_user

dashboard_v1_bp = Blueprint("dashboard_v1", __name__, url_prefix="/dashboard")


@dashboard_v1_bp.route("/stats", methods=["GET"])
@auth_required
def get_dashboard_stats():
    """Get dashboard statistics for current user.

    Returns:
        JSON object with user statistics:
        - totalDrawings: Number of drawings owned by user
        - totalGroups: Number of groups user belongs to
        - sharedDrawings: Number of drawings shared with user
    """
    try:
        user = get_current_user()
        user_id = user["id"]

        # TODO: Query actual counts from database when models are implemented
        # For now, return placeholder stats
        stats = {
            "totalDrawings": 0,
            "totalGroups": 0,
            "sharedDrawings": 0,
        }

        return jsonify(stats), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dashboard_v1_bp.route("/activity", methods=["GET"])
@auth_required
def get_activity_feed():
    """Get recent activity feed for current user.

    Returns activity from:
    - User's own drawings (created, updated)
    - Groups user belongs to (new drawings, comments)
    - Drawings shared with user

    Query params:
        limit: Maximum items to return (default 20, max 50)
        offset: Pagination offset (default 0)

    Returns:
        JSON array of activity items
    """
    try:
        user = get_current_user()
        user_id = user["id"]

        limit = min(int(request.args.get("limit", 20)), 50)
        offset = int(request.args.get("offset", 0))

        # TODO: Query activity from database when models are implemented
        # Activity types: drawing_created, drawing_updated, comment_added,
        #                 group_joined, drawing_shared
        activity = []

        return jsonify({
            "success": True,
            "count": len(activity),
            "items": activity,
            "limit": limit,
            "offset": offset,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Import request for query params
from flask import request
