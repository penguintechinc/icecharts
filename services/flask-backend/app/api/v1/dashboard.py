"""Dashboard Endpoints for API v1.

Provides dashboard statistics and activity feed for IceCharts users.
"""

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import get_db
from ...services.storage_usage_service import StorageUsageService

dashboard_v1_bp = Blueprint("dashboard_v1", __name__, url_prefix="/dashboard")


@dashboard_v1_bp.route("/stats", methods=["GET"])
@auth_required
def get_dashboard_stats():
    """Get dashboard statistics for current user.

    Returns:
        JSON object with user statistics:
        - totalDrawings: Number of drawings owned by user
        - totalTemplates: Number of templates owned by user
        - totalCollections: Number of collections owned by user
        - totalGroups: Number of groups user belongs to
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Count drawings owned or created by user
        total_drawings = db(
            (db.drawings.owner_id == user_id) | (db.drawings.created_by_id == user_id)
        ).count()

        # Count templates owned or created by user
        total_templates = db(
            (db.drawings.is_template == True)
            & (
                (db.drawings.owner_id == user_id)
                | (db.drawings.created_by_id == user_id)
            )
        ).count()

        # Count collections owned by user
        total_collections = db(db.collections.owner_id == user_id).count()

        # Count groups user belongs to (as a member)
        total_groups = db(db.group_members.user_id == user_id).count()

        stats = {
            "totalDrawings": total_drawings,
            "totalTemplates": total_templates,
            "totalCollections": total_collections,
            "totalGroups": total_groups,
        }

        return jsonify(stats), 200

    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({"error": str(e)}), 500


@dashboard_v1_bp.route("/activity", methods=["GET"])
@auth_required
def get_activity_feed():
    """Get recent activity feed for current user.

    Returns recent items from:
    - User's own drawings (created, updated)

    Query params:
        limit: Maximum items to return (default 20, max 50)
        offset: Pagination offset (default 0)

    Returns:
        JSON array of activity items with type, title, and timestamp
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        limit = min(int(request.args.get("limit", 20)), 50)
        offset = int(request.args.get("offset", 0))

        # Query recent drawings updated by or created by user, ordered by updated_at desc
        drawings = db(
            (db.drawings.owner_id == user_id) | (db.drawings.created_by_id == user_id)
        ).select(orderby=~db.drawings.updated_at, limitby=(offset, offset + limit))

        # Format as activity items
        activity = []
        for drawing in drawings:
            activity_item = {
                "id": str(drawing.id),
                "type": (
                    "drawing_updated" if drawing.updated_by_id else "drawing_created"
                ),
                "title": drawing.title or "Untitled Drawing",
                "timestamp": (
                    drawing.updated_at.isoformat()
                    if drawing.updated_at
                    else drawing.created_at.isoformat() if drawing.created_at else None
                ),
                "resource_id": str(drawing.id),
                "resource_type": "drawing",
            }
            activity.append(activity_item)

        # Get total count for pagination
        total_count = db(
            (db.drawings.owner_id == user_id) | (db.drawings.created_by_id == user_id)
        ).count()

        return (
            jsonify(
                {
                    "success": True,
                    "count": len(activity),
                    "items": activity,
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting activity feed: {e}")
        return jsonify({"error": str(e)}), 500


@dashboard_v1_bp.route("/storage", methods=["GET"])
@auth_required
def get_storage_widget():
    """Get storage usage statistics for dashboard widget.

    Returns:
        JSON object with storage stats for display in dashboard:
        {
            "storage": {
                "used_mb": float,
                "quota_mb": float,
                "usage_percentage": float,
                "usage_status": str ("ok", "warning", or "critical"),
                "total_drawings": int
            }
        }
    """
    try:
        user = get_current_user()
        user_id = user["id"]

        # Get storage statistics
        stats = StorageUsageService.get_storage_stats_summary(user_id)

        return jsonify({"storage": stats}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting storage widget: {e}")
        return jsonify({"error": str(e)}), 500
