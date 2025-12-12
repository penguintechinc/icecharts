"""Admin Endpoints for API v1."""

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request

from ...middleware import admin_required, auth_required, get_current_user
from ...models import (
    create_user,
    delete_user,
    get_db,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
)

admin_v1_bp = Blueprint("admin_v1", __name__, url_prefix="/admin")


@admin_v1_bp.route("/users", methods=["GET"])
@auth_required
@admin_required
def admin_list_users():
    """List all users with pagination (admin only)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    role = request.args.get("role", "").strip()
    active = request.args.get("active", "").strip()

    db = get_db()

    # Build query conditions
    conditions = []

    if search:
        conditions.append(
            (db.users.email.contains(search)) |
            (db.users.full_name.contains(search))
        )

    if role:
        conditions.append(db.users.role == role)

    if active:
        is_active = active.lower() == "true"
        conditions.append(db.users.is_active == is_active)

    # Combine conditions or use all users
    if conditions:
        combined = conditions[0]
        for cond in conditions[1:]:
            combined = combined & cond
        query = db(combined)
    else:
        query = db(db.users.id > 0)

    offset = (page - 1) * per_page

    users = query.select(
        orderby=db.users.created_at,
        limitby=(offset, offset + per_page),
    )
    total = query.count()

    # Remove sensitive fields and add group info
    user_list = []
    for u in users:
        user_dict = u.as_dict()
        user_dict.pop("password_hash", None)
        user_dict.pop("mfa_secret", None)

        # Get groups the user belongs to
        memberships = db(db.group_members.user_id == u.id).select(
            db.group_members.group_id,
            db.group_members.role,
        )
        groups = []
        for m in memberships:
            group = db.groups(m.group_id)
            if group:
                groups.append({
                    "id": group.id,
                    "name": group.name,
                    "role": m.role,
                })
        user_dict["groups"] = groups

        user_list.append(user_dict)

    return jsonify({
        "users": user_list,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@admin_v1_bp.route("/users/<int:user_id>", methods=["GET"])
@auth_required
@admin_required
def admin_get_user(user_id: int):
    """Get user details (admin only)."""
    user = get_user_by_id(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Remove sensitive fields
    user.pop("password_hash", None)
    user.pop("mfa_secret", None)

    return jsonify({"user": user}), 200


@admin_v1_bp.route("/users", methods=["POST"])
@auth_required
@admin_required
def admin_create_user():
    """Create a new user (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    full_name = data.get("full_name", "").strip()
    role = data.get("role", "viewer").strip()

    # Validation
    if not email:
        return jsonify({"error": "Email is required"}), 400

    if not password or len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    # Validate role
    valid_roles = ["admin", "maintainer", "viewer"]
    if role not in valid_roles:
        return jsonify({
            "error": "Invalid role",
            "valid_roles": valid_roles,
        }), 400

    # Check if user exists
    existing = get_user_by_email(email)
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    from .auth import hash_password

    password_hash = hash_password(password)
    user = create_user(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
    )

    # Remove sensitive fields
    user.pop("password_hash", None)
    user.pop("mfa_secret", None)

    return jsonify({
        "message": "User created successfully",
        "user": user,
    }), 201


@admin_v1_bp.route("/users/<int:user_id>", methods=["PUT"])
@auth_required
@admin_required
def admin_update_user(user_id: int):
    """Update user details (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Prepare update data
    update_data = {}

    if "email" in data:
        new_email = data["email"].strip().lower()
        # Check if email is already taken
        existing = get_user_by_email(new_email)
        if existing and existing["id"] != user_id:
            return jsonify({"error": "Email already in use"}), 409
        update_data["email"] = new_email

    if "full_name" in data:
        update_data["full_name"] = data["full_name"].strip()

    if "role" in data:
        role = data["role"].strip()
        valid_roles = ["admin", "maintainer", "viewer"]
        if role not in valid_roles:
            return jsonify({
                "error": "Invalid role",
                "valid_roles": valid_roles,
            }), 400
        update_data["role"] = role

    if "is_active" in data:
        update_data["is_active"] = data["is_active"]

    if "password" in data:
        password = data["password"]
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        from .auth import hash_password

        update_data["password_hash"] = hash_password(password)

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    # Update user
    updated_user = update_user(user_id, **update_data)

    # Remove sensitive fields
    updated_user.pop("password_hash", None)
    updated_user.pop("mfa_secret", None)

    return jsonify({
        "message": "User updated successfully",
        "user": updated_user,
    }), 200


@admin_v1_bp.route("/users/<int:user_id>", methods=["DELETE"])
@auth_required
@admin_required
def admin_delete_user(user_id: int):
    """Delete user (admin only)."""
    current_user = get_current_user()

    # Prevent self-deletion
    if current_user["id"] == user_id:
        return jsonify({"error": "Cannot delete your own account"}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Delete user
    success = delete_user(user_id)

    if not success:
        return jsonify({"error": "Failed to delete user"}), 500

    return jsonify({
        "message": "User deleted successfully",
    }), 200


@admin_v1_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@auth_required
@admin_required
def admin_activate_user(user_id: int):
    """Activate user account (admin only)."""
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Activate user
    update_user(user_id, is_active=True)

    return jsonify({
        "message": "User activated successfully",
    }), 200


@admin_v1_bp.route("/users/<int:user_id>/deactivate", methods=["POST"])
@auth_required
@admin_required
def admin_deactivate_user(user_id: int):
    """Deactivate user account (admin only)."""
    current_user = get_current_user()

    # Prevent self-deactivation
    if current_user["id"] == user_id:
        return jsonify({"error": "Cannot deactivate your own account"}), 400

    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Deactivate user
    update_user(user_id, is_active=False)

    return jsonify({
        "message": "User deactivated successfully",
    }), 200


@admin_v1_bp.route("/stats", methods=["GET"])
@auth_required
@admin_required
def admin_get_stats():
    """Get system statistics (admin only)."""
    db = get_db()

    stats = {
        "users": {
            "total": db(db.users).count(),
            "active": db(db.users.is_active == True).count(),
            "inactive": db(db.users.is_active == False).count(),
            "by_role": {
                "admin": db(db.users.role == "admin").count(),
                "maintainer": db(db.users.role == "maintainer").count(),
                "viewer": db(db.users.role == "viewer").count(),
            },
        },
        "drawings": {
            "total": db(db.drawings).count() if hasattr(db, "drawings") else 0,
        },
        "groups": {
            "total": db(db.groups).count() if hasattr(db, "groups") else 0,
        },
        "storage": {
            "providers": db(db.storage_providers).count() if hasattr(db, "storage_providers") else 0,
        },
    }

    return jsonify({"stats": stats}), 200


@admin_v1_bp.route("/activity", methods=["GET"])
@auth_required
@admin_required
def admin_get_activity():
    """Get recent system activity (admin only)."""
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # TODO: Implement activity logging and retrieval
    # For now, return placeholder

    activities = []

    return jsonify({
        "activities": activities,
        "total": len(activities),
        "page": page,
        "per_page": per_page,
    }), 200


@admin_v1_bp.route("/audit-log", methods=["GET"])
@auth_required
@admin_required
def admin_get_audit_log():
    """Get audit log entries (admin only)."""
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action", "").strip()

    # TODO: Implement audit logging and retrieval
    # For now, return placeholder

    audit_logs = []

    return jsonify({
        "audit_logs": audit_logs,
        "total": len(audit_logs),
        "page": page,
        "per_page": per_page,
    }), 200


@admin_v1_bp.route("/system/health", methods=["GET"])
@auth_required
@admin_required
def admin_get_system_health():
    """Get system health status (admin only)."""
    # Check various system components

    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": {
                "status": "healthy",
                "message": "Database connection OK",
            },
            "storage": {
                "status": "healthy",
                "message": "Storage accessible",
            },
            "cache": {
                "status": "healthy",
                "message": "Cache operational",
            },
        },
    }

    # TODO: Implement actual health checks for each component

    return jsonify({"health": health}), 200


@admin_v1_bp.route("/system/config", methods=["GET"])
@auth_required
@admin_required
def admin_get_system_config():
    """Get system configuration (admin only)."""
    from flask import current_app

    # Return non-sensitive configuration
    config = {
        "environment": current_app.config.get("ENV", "production"),
        "debug": current_app.config.get("DEBUG", False),
        "jwt_expiry_seconds": int(current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES").total_seconds()),
        "db_type": current_app.config.get("DB_TYPE", "postgres"),
    }

    return jsonify({"config": config}), 200


# ==========================================
# Storage Provider Configuration (Admin)
# ==========================================


@admin_v1_bp.route("/storage", methods=["GET"])
@auth_required
@admin_required
def admin_list_storage_configs():
    """List all organization storage configurations (admin only)."""
    db = get_db()

    # Get organization-level storage configs (where user_id is null or is_system_default is true)
    configs = db(
        (db.storage_providers.is_system_default == True) |
        (db.storage_providers.user_id == None)
    ).select(orderby=~db.storage_providers.updated_at)

    items = []
    for config in configs:
        item = config.as_dict()
        # Mask sensitive config fields
        if item.get("config_json"):
            masked = item["config_json"].copy()
            for key in ["client_secret", "secret_access_key", "account_key", "password"]:
                if key in masked:
                    masked[key] = "***"
            item["config_json"] = masked
        items.append(item)

    return jsonify({"items": items, "total": len(items)}), 200


@admin_v1_bp.route("/storage", methods=["POST"])
@auth_required
@admin_required
def admin_create_storage_config():
    """Create organization storage configuration (admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    provider = data.get("provider", "").strip()
    name = data.get("name", "").strip()
    enabled = data.get("enabled", True)

    # Validate provider type
    valid_providers = ["gdrive", "onedrive", "s3"]
    if provider not in valid_providers:
        return jsonify({"error": f"Invalid provider. Valid: {valid_providers}"}), 400

    if not name:
        name = {"gdrive": "Google Drive", "onedrive": "OneDrive", "s3": "External S3"}.get(provider, provider)

    # Build config based on provider type
    config_json = {}

    if provider in ("gdrive", "onedrive"):
        client_id = data.get("client_id", "").strip()
        client_secret = data.get("client_secret", "").strip()

        if not client_id:
            return jsonify({"error": "client_id is required"}), 400

        config_json = {
            "client_id": client_id,
            "client_secret": client_secret,
        }

        if provider == "onedrive":
            config_json["tenant_id"] = data.get("tenant_id", "common").strip()

    elif provider == "s3":
        bucket = data.get("bucket", "").strip()
        if not bucket:
            return jsonify({"error": "bucket is required for S3"}), 400

        config_json = {
            "bucket": bucket,
            "region": data.get("region", "us-east-1").strip(),
            "endpoint": data.get("endpoint", "").strip() or None,
        }

    db = get_db()

    # Check if provider already exists at org level
    existing = db(
        (db.storage_providers.provider_type == provider) &
        (db.storage_providers.is_system_default == True)
    ).select().first()

    if existing:
        return jsonify({"error": f"{name} is already configured. Edit it instead."}), 409

    # Create storage config
    config_id = db.storage_providers.insert(
        tenant_id=1,
        name=name,
        provider_type=provider,
        config_json=config_json,
        user_id=None,  # Organization-level, not user-specific
        is_active=enabled,
        is_system_default=True,
    )
    db.commit()

    config = db.storage_providers(config_id)

    return jsonify({
        "message": f"{name} configured successfully",
        "id": config_id,
    }), 201


@admin_v1_bp.route("/storage/<int:config_id>", methods=["PUT"])
@auth_required
@admin_required
def admin_update_storage_config(config_id: int):
    """Update organization storage configuration (admin only)."""
    db = get_db()
    config = db.storage_providers(config_id)

    if not config:
        return jsonify({"error": "Storage configuration not found"}), 404

    if not config.is_system_default:
        return jsonify({"error": "Can only update organization-level configs"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    update_data = {}

    if "name" in data:
        update_data["name"] = data["name"].strip()

    if "enabled" in data:
        update_data["is_active"] = data["enabled"]

    # Update config_json fields
    if config.config_json:
        new_config = config.config_json.copy()
    else:
        new_config = {}

    if "client_id" in data:
        new_config["client_id"] = data["client_id"].strip()

    if "client_secret" in data and data["client_secret"]:
        new_config["client_secret"] = data["client_secret"]

    if "tenant_id" in data:
        new_config["tenant_id"] = data["tenant_id"].strip()

    if "bucket" in data:
        new_config["bucket"] = data["bucket"].strip()

    if "region" in data:
        new_config["region"] = data["region"].strip()

    if "endpoint" in data:
        new_config["endpoint"] = data["endpoint"].strip() or None

    if new_config != config.config_json:
        update_data["config_json"] = new_config

    if update_data:
        config.update_record(**update_data)
        db.commit()

    return jsonify({"message": "Storage configuration updated"}), 200


@admin_v1_bp.route("/storage/<int:config_id>", methods=["PATCH"])
@auth_required
@admin_required
def admin_patch_storage_config(config_id: int):
    """Toggle storage configuration enabled status (admin only)."""
    db = get_db()
    config = db.storage_providers(config_id)

    if not config:
        return jsonify({"error": "Storage configuration not found"}), 404

    data = request.get_json()
    if "enabled" in data:
        config.update_record(is_active=data["enabled"])
        db.commit()

    return jsonify({"message": "Storage configuration updated"}), 200


@admin_v1_bp.route("/storage/<int:config_id>", methods=["DELETE"])
@auth_required
@admin_required
def admin_delete_storage_config(config_id: int):
    """Delete organization storage configuration (admin only)."""
    db = get_db()
    config = db.storage_providers(config_id)

    if not config:
        return jsonify({"error": "Storage configuration not found"}), 404

    if not config.is_system_default:
        return jsonify({"error": "Can only delete organization-level configs"}), 403

    # Delete the configuration
    db(db.storage_providers.id == config_id).delete()
    db.commit()

    return jsonify({"message": "Storage configuration deleted"}), 200


@admin_v1_bp.route("/users/bulk-import", methods=["POST"])
@auth_required
@admin_required
def admin_bulk_import_users():
    """Bulk import users from CSV (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    users_data = data.get("users", [])

    if not users_data or not isinstance(users_data, list):
        return jsonify({"error": "users array is required"}), 400

    from .auth import hash_password

    created = []
    errors = []

    for idx, user_data in enumerate(users_data):
        try:
            email = user_data.get("email", "").strip().lower()
            password = user_data.get("password", "")
            full_name = user_data.get("full_name", "").strip()
            role = user_data.get("role", "viewer").strip()

            # Validation
            if not email:
                errors.append({"index": idx, "error": "Email is required"})
                continue

            if not password or len(password) < 8:
                errors.append({"index": idx, "error": "Password must be at least 8 characters"})
                continue

            # Check if user exists
            existing = get_user_by_email(email)
            if existing:
                errors.append({"index": idx, "error": "Email already registered"})
                continue

            # Create user
            password_hash = hash_password(password)
            user = create_user(
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                role=role,
            )

            created.append(user["id"])

        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    return jsonify({
        "message": f"Bulk import completed: {len(created)} created, {len(errors)} errors",
        "created_count": len(created),
        "error_count": len(errors),
        "errors": errors,
    }), 201 if created else 400
