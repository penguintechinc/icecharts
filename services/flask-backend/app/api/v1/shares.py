"""Sharing Management Endpoints for API v1."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import get_db, get_user_by_id

shares_v1_bp = Blueprint("shares_v1", __name__, url_prefix="/drawings")


def get_drawing_by_id(drawing_id: int) -> Optional[dict]:
    """Get drawing by ID."""
    db = get_db()
    drawing = db(db.drawings.id == drawing_id).select().first()
    return drawing.as_dict() if drawing else None


def user_can_admin_drawing(user_id: int, drawing_id: int) -> bool:
    """Check if user can manage sharing for a drawing."""
    db = get_db()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return False

    # Owner can always manage
    if drawing["owner_id"] == user_id:
        return True

    # Check if has admin permission
    share = db(
        (db.drawing_shares.drawing_id == drawing_id) &
        (db.drawing_shares.user_id == user_id) &
        (db.drawing_shares.permission == "admin")
    ).select().first()

    return share is not None


@shares_v1_bp.route("/<int:drawing_id>/shares", methods=["GET"])
@auth_required
def list_shares(drawing_id: int):
    """List all shares for a drawing."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_admin_drawing(user["id"], drawing_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    db = get_db()

    # Get user shares
    user_shares = db(
        (db.drawing_shares.drawing_id == drawing_id) &
        (db.drawing_shares.user_id == db.users.id)
    ).select(
        db.drawing_shares.ALL,
        db.users.id,
        db.users.email,
        db.users.full_name,
    )

    # Get group shares
    group_shares = db(
        (db.drawing_shares.drawing_id == drawing_id) &
        (db.drawing_shares.group_id == db.groups.id)
    ).select(
        db.drawing_shares.ALL,
        db.groups.id,
        db.groups.name,
    )

    # Get public shares
    public_shares = db(
        (db.drawing_shares.drawing_id == drawing_id) &
        (db.drawing_shares.is_public == True)
    ).select()

    shares = {
        "user_shares": [],
        "group_shares": [],
        "public_shares": [],
    }

    for s in user_shares:
        shares["user_shares"].append({
            "id": s.drawing_shares.id,
            "user_id": s.users.id,
            "email": s.users.email,
            "full_name": s.users.full_name,
            "permission": s.drawing_shares.permission,
            "created_at": s.drawing_shares.created_at.isoformat() if s.drawing_shares.created_at else None,
        })

    for s in group_shares:
        shares["group_shares"].append({
            "id": s.drawing_shares.id,
            "group_id": s.groups.id,
            "group_name": s.groups.name,
            "permission": s.drawing_shares.permission,
            "created_at": s.drawing_shares.created_at.isoformat() if s.drawing_shares.created_at else None,
        })

    for s in public_shares:
        shares["public_shares"].append({
            "id": s.id,
            "token": s.share_token,
            "permission": s.permission,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return jsonify({"shares": shares}), 200


@shares_v1_bp.route("/<int:drawing_id>/shares", methods=["POST"])
@auth_required
def create_share(drawing_id: int):
    """Create a new share for a drawing."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_admin_drawing(user["id"], drawing_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    share_type = data.get("type")  # "user", "group", or "public"
    permission = data.get("permission", "view")

    # Validate permission
    if permission not in ["view", "edit", "admin"]:
        return jsonify({"error": "Invalid permission"}), 400

    db = get_db()

    if share_type == "user":
        target_user_id = data.get("user_id")
        if not target_user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Check if user exists
        target_user = get_user_by_id(target_user_id)
        if not target_user:
            return jsonify({"error": "User not found"}), 404

        # Check if already shared
        existing = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.user_id == target_user_id)
        ).select().first()

        if existing:
            return jsonify({"error": "Drawing already shared with this user"}), 409

        # Create share
        share_id = db.drawing_shares.insert(
            drawing_id=drawing_id,
            user_id=target_user_id,
            permission=permission,
            shared_by=user["id"],
        )
        db.commit()

        return jsonify({
            "message": "Drawing shared successfully",
            "share_id": share_id,
            "type": "user",
        }), 201

    elif share_type == "group":
        target_group_id = data.get("group_id")
        if not target_group_id:
            return jsonify({"error": "group_id is required"}), 400

        # Check if group exists
        group = db(db.groups.id == target_group_id).select().first()
        if not group:
            return jsonify({"error": "Group not found"}), 404

        # Check if already shared
        existing = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.group_id == target_group_id)
        ).select().first()

        if existing:
            return jsonify({"error": "Drawing already shared with this group"}), 409

        # Create share
        share_id = db.drawing_shares.insert(
            drawing_id=drawing_id,
            group_id=target_group_id,
            permission=permission,
            shared_by=user["id"],
        )
        db.commit()

        return jsonify({
            "message": "Drawing shared with group successfully",
            "share_id": share_id,
            "type": "group",
        }), 201

    elif share_type == "public":
        # Generate share token
        share_token = secrets.token_urlsafe(32)

        # Get expiration (optional)
        expires_in_days = data.get("expires_in_days")
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create public share
        share_id = db.drawing_shares.insert(
            drawing_id=drawing_id,
            is_public=True,
            share_token=share_token,
            permission=permission,
            expires_at=expires_at,
            shared_by=user["id"],
        )
        db.commit()

        return jsonify({
            "message": "Public share created successfully",
            "share_id": share_id,
            "type": "public",
            "token": share_token,
            "share_url": f"/api/v1/share/{share_token}",
            "expires_at": expires_at.isoformat() if expires_at else None,
        }), 201

    else:
        return jsonify({"error": "Invalid share type"}), 400


@shares_v1_bp.route("/<int:drawing_id>/shares/<int:share_id>", methods=["DELETE"])
@auth_required
def delete_share(drawing_id: int, share_id: int):
    """Delete a share."""
    user = get_current_user()
    drawing = get_drawing_by_id(drawing_id)

    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_admin_drawing(user["id"], drawing_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    db = get_db()

    # Delete share
    deleted = db(
        (db.drawing_shares.id == share_id) &
        (db.drawing_shares.drawing_id == drawing_id)
    ).delete()

    if not deleted:
        return jsonify({"error": "Share not found"}), 404

    db.commit()

    return jsonify({
        "message": "Share removed successfully",
    }), 200


@shares_v1_bp.route("/<int:drawing_id>/shares/<int:share_id>", methods=["PUT"])
@auth_required
def update_share(drawing_id: int, share_id: int):
    """Update share permissions."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    drawing = get_drawing_by_id(drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Check access
    if not user_can_admin_drawing(user["id"], drawing_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    permission = data.get("permission")
    if not permission or permission not in ["view", "edit", "admin"]:
        return jsonify({"error": "Valid permission is required"}), 400

    db = get_db()

    # Update share
    updated = db(
        (db.drawing_shares.id == share_id) &
        (db.drawing_shares.drawing_id == drawing_id)
    ).update(permission=permission)

    if not updated:
        return jsonify({"error": "Share not found"}), 404

    db.commit()

    return jsonify({
        "message": "Share permission updated successfully",
        "permission": permission,
    }), 200


# Public share access endpoint (no auth required)
@shares_v1_bp.route("/share/<string:token>", methods=["GET"])
def access_shared_drawing(token: str):
    """Access a drawing via public share token."""
    db = get_db()

    # Find share by token
    share = db(
        (db.drawing_shares.share_token == token) &
        (db.drawing_shares.is_public == True)
    ).select().first()

    if not share:
        return jsonify({"error": "Invalid or expired share link"}), 404

    # Check if expired
    if share.expires_at and share.expires_at < datetime.utcnow():
        return jsonify({"error": "Share link has expired"}), 410

    # Get drawing
    drawing = get_drawing_by_id(share.drawing_id)
    if not drawing:
        return jsonify({"error": "Drawing not found"}), 404

    # Return drawing with limited info
    return jsonify({
        "drawing": {
            "id": drawing["id"],
            "title": drawing["title"],
            "content": drawing.get("content"),
            "permission": share.permission,
        },
    }), 200
