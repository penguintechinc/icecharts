"""Comments Endpoints for API v1."""

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import get_db

comments_v1_bp = Blueprint("comments_v1", __name__, url_prefix="/drawings")


def get_drawing_by_id(drawing_id: int) -> Optional[dict]:
    """Get drawing by ID."""
    db = get_db()
    drawing = db(db.drawings.id == drawing_id).select().first()
    return drawing.as_dict() if drawing else None


def user_can_access_drawing(user_id: int, drawing_id: int) -> bool:
    """Check if user can access a drawing."""
    db = get_db()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return False

    # Owner can always access
    if drawing["owner_id"] == user_id:
        return True

    # Check if shared with user
    share = (
        db(
            (db.drawing_shares.drawing_id == drawing_id)
            & (db.drawing_shares.user_id == user_id)
        )
        .select()
        .first()
    )

    if share:
        return True

    # Check if shared with user's group
    group_share = (
        db(
            (db.drawing_shares.drawing_id == drawing_id)
            & (
                db.drawing_shares.group_id.belongs(
                    db(db.group_members.user_id == user_id)._select(
                        db.group_members.group_id
                    )
                )
            )
        )
        .select()
        .first()
    )

    return group_share is not None


def get_comment_by_id(comment_id: int) -> Optional[dict]:
    """Get comment by ID."""
    db = get_db()
    comment = db(db.comments.id == comment_id).select().first()
    return comment.as_dict() if comment else None


@comments_v1_bp.route("/<int:drawing_id>/comments", methods=["GET"])
@auth_required
def list_comments(drawing_id: int):
    """List all comments for a drawing."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    db = get_db()

    # Get comments with user details
    comments = db(
        (db.comments.drawing_id == drawing_id) & (db.comments.user_id == db.users.id)
    ).select(
        db.comments.ALL,
        db.users.id,
        db.users.email,
        db.users.full_name,
        orderby=db.comments.created_at,
    )

    comment_list = []
    for c in comments:
        comment_list.append(
            {
                "id": c.comments.id,
                "content": c.comments.content,
                "x_position": c.comments.x_position,
                "y_position": c.comments.y_position,
                "is_resolved": c.comments.is_resolved,
                "resolved_by": c.comments.resolved_by,
                "resolved_at": (
                    c.comments.resolved_at.isoformat()
                    if c.comments.resolved_at
                    else None
                ),
                "created_at": (
                    c.comments.created_at.isoformat() if c.comments.created_at else None
                ),
                "updated_at": (
                    c.comments.updated_at.isoformat() if c.comments.updated_at else None
                ),
                "user": {
                    "id": c.users.id,
                    "email": c.users.email,
                    "full_name": c.users.full_name,
                },
            }
        )

    return (
        jsonify(
            {
                "comments": comment_list,
                "total": len(comment_list),
            }
        ),
        200,
    )


@comments_v1_bp.route("/<int:drawing_id>/comments", methods=["POST"])
@auth_required
def create_comment(drawing_id: int):
    """Create a new comment on a drawing."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    content = data.get("content", "").strip()
    x_position = data.get("x_position")
    y_position = data.get("y_position")

    # Validation
    if not content:
        return jsonify({"error": "Comment content is required"}), 400

    db = get_db()

    # Create comment
    comment_id = db.comments.insert(
        drawing_id=drawing_id,
        user_id=user["id"],
        content=content,
        x_position=x_position,
        y_position=y_position,
        is_resolved=False,
    )
    db.commit()

    comment = get_comment_by_id(comment_id)

    return (
        jsonify(
            {
                "message": "Comment created successfully",
                "comment": comment,
            }
        ),
        201,
    )


@comments_v1_bp.route("/<int:drawing_id>/comments/<int:comment_id>", methods=["GET"])
@auth_required
def get_comment(drawing_id: int, comment_id: int):
    """Get a specific comment."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    return jsonify({"comment": comment}), 200


@comments_v1_bp.route("/<int:drawing_id>/comments/<int:comment_id>", methods=["PUT"])
@auth_required
def update_comment(drawing_id: int, comment_id: int):
    """Update a comment."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    # Only comment author can update
    if comment["user_id"] != user["id"]:
        return jsonify({"error": "You can only edit your own comments"}), 403

    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Comment content is required"}), 400

    db = get_db()

    # Update comment
    db(db.comments.id == comment_id).update(
        content=content,
        updated_at=datetime.utcnow(),
    )
    db.commit()

    updated_comment = get_comment_by_id(comment_id)

    return (
        jsonify(
            {
                "message": "Comment updated successfully",
                "comment": updated_comment,
            }
        ),
        200,
    )


@comments_v1_bp.route("/<int:drawing_id>/comments/<int:comment_id>", methods=["DELETE"])
@auth_required
def delete_comment(drawing_id: int, comment_id: int):
    """Delete a comment."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    # Only comment author or drawing owner can delete
    if comment["user_id"] != user["id"] and drawing["owner_id"] != user["id"]:
        return jsonify({"error": "Insufficient permissions"}), 403

    db = get_db()

    # Delete comment
    db(db.comments.id == comment_id).delete()
    db.commit()

    return (
        jsonify(
            {
                "message": "Comment deleted successfully",
            }
        ),
        200,
    )


@comments_v1_bp.route(
    "/<int:drawing_id>/comments/<int:comment_id>/resolve", methods=["POST"]
)
@auth_required
def resolve_comment(drawing_id: int, comment_id: int):
    """Mark a comment as resolved."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    db = get_db()

    # Toggle resolved status
    is_resolved = not comment.get("is_resolved", False)
    update_data = {
        "is_resolved": is_resolved,
    }

    if is_resolved:
        update_data["resolved_by"] = user["id"]
        update_data["resolved_at"] = datetime.utcnow()
    else:
        update_data["resolved_by"] = None
        update_data["resolved_at"] = None

    db(db.comments.id == comment_id).update(**update_data)
    db.commit()

    updated_comment = get_comment_by_id(comment_id)

    return (
        jsonify(
            {
                "message": f"Comment {'resolved' if is_resolved else 'unresolved'} successfully",
                "comment": updated_comment,
            }
        ),
        200,
    )


@comments_v1_bp.route(
    "/<int:drawing_id>/comments/<int:comment_id>/replies", methods=["GET"]
)
@auth_required
def list_comment_replies(drawing_id: int, comment_id: int):
    """List replies to a comment."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    db = get_db()

    # Get replies
    replies = db(
        (db.comment_replies.comment_id == comment_id)
        & (db.comment_replies.user_id == db.users.id)
    ).select(
        db.comment_replies.ALL,
        db.users.id,
        db.users.email,
        db.users.full_name,
        orderby=db.comment_replies.created_at,
    )

    reply_list = []
    for r in replies:
        reply_list.append(
            {
                "id": r.comment_replies.id,
                "content": r.comment_replies.content,
                "created_at": (
                    r.comment_replies.created_at.isoformat()
                    if r.comment_replies.created_at
                    else None
                ),
                "user": {
                    "id": r.users.id,
                    "email": r.users.email,
                    "full_name": r.users.full_name,
                },
            }
        )

    return (
        jsonify(
            {
                "replies": reply_list,
                "total": len(reply_list),
            }
        ),
        200,
    )


@comments_v1_bp.route(
    "/<int:drawing_id>/comments/<int:comment_id>/replies", methods=["POST"]
)
@auth_required
def create_comment_reply(drawing_id: int, comment_id: int):
    """Reply to a comment."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_access_drawing(user["id"], drawing_id):
        return jsonify({"error": "Access denied"}), 403

    comment = get_comment_by_id(comment_id)
    if not comment or comment["drawing_id"] != drawing_id:
        return jsonify({"error": "Comment not found"}), 404

    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Reply content is required"}), 400

    db = get_db()

    # Create reply
    reply_id = db.comment_replies.insert(
        comment_id=comment_id,
        user_id=user["id"],
        content=content,
    )
    db.commit()

    reply = db(db.comment_replies.id == reply_id).select().first()

    return (
        jsonify(
            {
                "message": "Reply created successfully",
                "reply": reply.as_dict() if reply else None,
            }
        ),
        201,
    )
