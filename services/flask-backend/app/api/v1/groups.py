"""Group Management Endpoints for API v1."""

from datetime import datetime
from typing import Optional

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, maintainer_or_admin_required
from ...models import get_db, get_user_by_id

groups_v1_bp = Blueprint("groups_v1", __name__, url_prefix="/groups")


def get_group_by_id(group_id: int) -> Optional[dict]:
    """Get group by ID."""
    db = get_db()
    group = db(db.groups.id == group_id).select().first()
    return group.as_dict() if group else None


def user_is_group_member(user_id: int, group_id: int) -> bool:
    """Check if user is a member of group."""
    db = get_db()
    membership = (
        db(
            (db.group_members.user_id == user_id)
            & (db.group_members.group_id == group_id)
        )
        .select()
        .first()
    )
    return membership is not None


def user_is_group_admin(user_id: int, group_id: int) -> bool:
    """Check if user is an admin of group."""
    db = get_db()
    membership = (
        db(
            (db.group_members.user_id == user_id)
            & (db.group_members.group_id == group_id)
            & (db.group_members.role == "admin")
        )
        .select()
        .first()
    )
    return membership is not None


@groups_v1_bp.route("", methods=["GET"])
@auth_required
def list_groups():
    """List all groups (user's groups or all if admin)."""
    user = get_current_user()
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset = (page - 1) * per_page

    # Admin sees all groups, others see only their groups
    if user["role"] == "admin":
        query = db(db.groups)
    else:
        # Get groups where user is a member
        query = db(
            db.groups.id.belongs(
                db(db.group_members.user_id == user["id"])._select(
                    db.group_members.group_id
                )
            )
        )

    groups = query.select(
        orderby=db.groups.created_at,
        limitby=(offset, offset + per_page),
    )
    total = query.count()

    return (
        jsonify(
            {
                "groups": [g.as_dict() for g in groups],
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            }
        ),
        200,
    )


@groups_v1_bp.route("", methods=["POST"])
@auth_required
@maintainer_or_admin_required
def create_group():
    """Create a new group."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    # Validation
    if not name:
        return jsonify({"error": "Group name is required"}), 400

    db = get_db()

    # Create group
    group_id = db.groups.insert(
        name=name,
        description=description,
        owner_id=user["id"],
    )
    db.commit()

    # Add creator as admin member
    db.group_members.insert(
        group_id=group_id,
        user_id=user["id"],
        role="admin",
    )
    db.commit()

    group = get_group_by_id(group_id)

    return (
        jsonify(
            {
                "message": "Group created successfully",
                "group": group,
            }
        ),
        201,
    )


@groups_v1_bp.route("/<int:group_id>", methods=["GET"])
@auth_required
def get_group(group_id: int):
    """Get group details."""
    user = get_current_user()
    group = get_group_by_id(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group member
    if user["role"] != "admin" and not user_is_group_member(user["id"], group_id):
        return jsonify({"error": "Access denied"}), 403

    # Get member count
    db = get_db()
    member_count = db(db.group_members.group_id == group_id).count()

    group["member_count"] = member_count

    return jsonify({"group": group}), 200


@groups_v1_bp.route("/<int:group_id>", methods=["PUT"])
@auth_required
def update_group(group_id: int):
    """Update group details."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    group = get_group_by_id(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group admin
    if user["role"] != "admin" and not user_is_group_admin(user["id"], group_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    # Update fields
    db = get_db()
    update_data = {}

    if "name" in data:
        update_data["name"] = data["name"].strip()
    if "description" in data:
        update_data["description"] = data["description"].strip()

    if update_data:
        db(db.groups.id == group_id).update(**update_data)
        db.commit()

    updated_group = get_group_by_id(group_id)

    return (
        jsonify(
            {
                "message": "Group updated successfully",
                "group": updated_group,
            }
        ),
        200,
    )


@groups_v1_bp.route("/<int:group_id>", methods=["DELETE"])
@auth_required
def delete_group(group_id: int):
    """Delete group."""
    user = get_current_user()
    group = get_group_by_id(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group owner
    if user["role"] != "admin" and group["owner_id"] != user["id"]:
        return jsonify({"error": "Insufficient permissions"}), 403

    db = get_db()

    # Delete group members first
    db(db.group_members.group_id == group_id).delete()

    # Delete group
    db(db.groups.id == group_id).delete()
    db.commit()

    return (
        jsonify(
            {
                "message": "Group deleted successfully",
            }
        ),
        200,
    )


@groups_v1_bp.route("/<int:group_id>/members", methods=["GET"])
@auth_required
def list_group_members(group_id: int):
    """List group members."""
    user = get_current_user()
    group = get_group_by_id(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group member
    if user["role"] != "admin" and not user_is_group_member(user["id"], group_id):
        return jsonify({"error": "Access denied"}), 403

    db = get_db()

    # Get members with user details - using proper PyDAL join
    members = db(db.group_members.group_id == group_id).select(
        orderby=db.group_members.joined_at,
    )

    member_list = []
    for m in members:
        try:
            user = db.identities(m.user_id)
            if user:
                member_list.append(
                    {
                        "user_id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": m.role,
                        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                    }
                )
        except Exception as e:
            current_app.logger.warning(f"Error fetching user {m.user_id}: {e}")
            continue

    return (
        jsonify(
            {
                "members": member_list,
                "total": len(member_list),
            }
        ),
        200,
    )


@groups_v1_bp.route("/<int:group_id>/members", methods=["POST"])
@auth_required
def add_group_member(group_id: int):
    """Add member to group."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    group = get_group_by_id(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group admin
    if user["role"] != "admin" and not user_is_group_admin(user["id"], group_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    user_id = data.get("user_id")
    role = data.get("role", "member")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Validate role
    if role not in ["admin", "member"]:
        return jsonify({"error": "Invalid role"}), 400

    # Check if user exists
    target_user = get_user_by_id(user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    # Check if already a member
    if user_is_group_member(user_id, group_id):
        return jsonify({"error": "User is already a member"}), 409

    db = get_db()

    # Add member
    db.group_members.insert(
        group_id=group_id,
        user_id=user_id,
        role=role,
    )
    db.commit()

    return (
        jsonify(
            {
                "message": "Member added successfully",
                "user_id": user_id,
                "role": role,
            }
        ),
        201,
    )


@groups_v1_bp.route("/<int:group_id>/members/<int:member_id>", methods=["PUT"])
@auth_required
def update_group_member(group_id: int, member_id: int):
    """Update group member role."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    group = get_group_by_id(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin or group admin
    if user["role"] != "admin" and not user_is_group_admin(user["id"], group_id):
        return jsonify({"error": "Insufficient permissions"}), 403

    role = data.get("role")
    if not role or role not in ["admin", "member"]:
        return jsonify({"error": "Valid role is required"}), 400

    db = get_db()

    # Update member role
    updated = db(
        (db.group_members.group_id == group_id)
        & (db.group_members.user_id == member_id)
    ).update(role=role)

    if not updated:
        return jsonify({"error": "Member not found in group"}), 404

    db.commit()

    return (
        jsonify(
            {
                "message": "Member role updated successfully",
                "user_id": member_id,
                "role": role,
            }
        ),
        200,
    )


@groups_v1_bp.route("/<int:group_id>/members/<int:member_id>", methods=["DELETE"])
@auth_required
def remove_group_member(group_id: int, member_id: int):
    """Remove member from group."""
    user = get_current_user()
    group = get_group_by_id(group_id)

    if not group:
        return jsonify({"error": "Group not found"}), 404

    # Check access: admin, group admin, or removing self
    is_admin = user["role"] == "admin"
    is_group_admin = user_is_group_admin(user["id"], group_id)
    is_self = user["id"] == member_id

    if not (is_admin or is_group_admin or is_self):
        return jsonify({"error": "Insufficient permissions"}), 403

    db = get_db()

    # Prevent removing group owner
    if member_id == group["owner_id"]:
        return jsonify({"error": "Cannot remove group owner"}), 400

    # Remove member
    deleted = db(
        (db.group_members.group_id == group_id)
        & (db.group_members.user_id == member_id)
    ).delete()

    if not deleted:
        return jsonify({"error": "Member not found in group"}), 404

    db.commit()

    return (
        jsonify(
            {
                "message": "Member removed successfully",
            }
        ),
        200,
    )
