"""User Search and Lookup Endpoints for API v1."""

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import get_db

users_v1_bp = Blueprint("users_v1", __name__, url_prefix="/users")


@users_v1_bp.route("/search", methods=["GET"])
@auth_required
def search_users():
    """Search users by email or name.

    Query parameters:
        - q: Search query (email or name)
        - limit: Maximum results (default 10, max 50)
        - exclude_group: Optional group ID to exclude members from results

    Returns:
        JSON array of matching users with id, email, full_name
    """
    try:
        user = get_current_user()
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 10)), 50)
        exclude_group = request.args.get("exclude_group", type=int)

        if not query:
            return jsonify({"users": []}), 200

        # Search must be at least 2 characters
        if len(query) < 2:
            return jsonify({"users": []}), 200

        db = get_db()

        # Search by email or full name
        search_query = db(
            (db.identities.email.contains(query))
            | (db.identities.full_name.contains(query))
        )

        # Exclude current user
        search_query = db(search_query._query & (db.identities.id != user["id"]))

        # Get users
        users = search_query.select(orderby=db.identities.email, limitby=(0, limit))

        results = []
        for u in users:
            # If exclude_group is provided, skip users already in that group
            if exclude_group:
                is_member = (
                    db(
                        (db.group_members.user_id == u.id)
                        & (db.group_members.group_id == exclude_group)
                    ).count()
                    > 0
                )

                if is_member:
                    continue

            results.append(
                {
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                }
            )

        return jsonify({"users": results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@users_v1_bp.route("/<int:user_id>", methods=["GET"])
@auth_required
def get_user(user_id: int):
    """Get basic user information by ID.

    Args:
        user_id: User identifier

    Returns:
        JSON user object with id, email, full_name
    """
    try:
        db = get_db()
        user = db.identities(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return (
            jsonify(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
