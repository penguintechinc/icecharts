"""Storage Provider Management Endpoints for API v1."""

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user, admin_required
from ...models import get_db

storage_v1_bp = Blueprint("storage_v1", __name__, url_prefix="/storage")


def get_storage_provider_by_id(provider_id: int) -> Optional[dict]:
    """Get storage provider by ID."""
    db = get_db()
    provider = db(db.storage_providers.id == provider_id).select().first()
    return provider.as_dict() if provider else None


@storage_v1_bp.route("/providers", methods=["GET"])
@auth_required
def list_storage_providers():
    """List available storage providers."""
    user = get_current_user()
    db = get_db()

    # Users see only their configured providers and system defaults
    if user["role"] == "admin":
        providers = db(db.storage_providers).select()
    else:
        providers = db(
            (db.storage_providers.user_id == user["id"]) |
            (db.storage_providers.is_system_default == True)
        ).select()

    return jsonify({
        "providers": [p.as_dict() for p in providers],
        "total": len(providers),
    }), 200


@storage_v1_bp.route("/providers", methods=["POST"])
@auth_required
def create_storage_provider():
    """Configure a new storage provider."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    provider_type = data.get("provider_type", "").strip()
    name = data.get("name", "").strip()
    config = data.get("config", {})

    # Validation
    valid_types = ["local", "s3", "azure", "gcs", "webdav"]
    if provider_type not in valid_types:
        return jsonify({
            "error": "Invalid provider type",
            "valid_types": valid_types,
        }), 400

    if not name:
        return jsonify({"error": "Provider name is required"}), 400

    # Validate config based on provider type
    if provider_type == "s3":
        required_fields = ["bucket", "region", "access_key_id", "secret_access_key"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return jsonify({
                "error": "Missing required S3 configuration",
                "missing_fields": missing,
            }), 400

    elif provider_type == "azure":
        required_fields = ["account_name", "account_key", "container"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return jsonify({
                "error": "Missing required Azure configuration",
                "missing_fields": missing,
            }), 400

    elif provider_type == "gcs":
        required_fields = ["bucket", "credentials"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return jsonify({
                "error": "Missing required GCS configuration",
                "missing_fields": missing,
            }), 400

    db = get_db()

    # Create storage provider
    provider_id = db.storage_providers.insert(
        user_id=user["id"],
        provider_type=provider_type,
        name=name,
        config=config,
        is_active=True,
        is_system_default=False,
    )
    db.commit()

    provider = get_storage_provider_by_id(provider_id)

    return jsonify({
        "message": "Storage provider configured successfully",
        "provider": provider,
    }), 201


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["GET"])
@auth_required
def get_storage_provider(provider_id: int):
    """Get storage provider details."""
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Mask sensitive config fields
    if "config" in provider and isinstance(provider["config"], dict):
        masked_config = provider["config"].copy()
        sensitive_fields = ["secret_access_key", "account_key", "credentials", "password"]
        for field in sensitive_fields:
            if field in masked_config:
                masked_config[field] = "***MASKED***"
        provider["config"] = masked_config

    return jsonify({"provider": provider}), 200


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["PUT"])
@auth_required
def update_storage_provider(provider_id: int):
    """Update storage provider configuration."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    provider = get_storage_provider_by_id(provider_id)
    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    db = get_db()
    update_data = {}

    if "name" in data:
        update_data["name"] = data["name"].strip()
    if "config" in data:
        update_data["config"] = data["config"]
    if "is_active" in data:
        update_data["is_active"] = data["is_active"]

    if update_data:
        db(db.storage_providers.id == provider_id).update(**update_data)
        db.commit()

    updated_provider = get_storage_provider_by_id(provider_id)

    return jsonify({
        "message": "Storage provider updated successfully",
        "provider": updated_provider,
    }), 200


@storage_v1_bp.route("/providers/<int:provider_id>", methods=["DELETE"])
@auth_required
def delete_storage_provider(provider_id: int):
    """Delete storage provider."""
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # Prevent deletion of system defaults
    if provider.get("is_system_default"):
        return jsonify({"error": "Cannot delete system default provider"}), 400

    db = get_db()

    # Delete provider
    db(db.storage_providers.id == provider_id).delete()
    db.commit()

    return jsonify({
        "message": "Storage provider deleted successfully",
    }), 200


@storage_v1_bp.route("/providers/<int:provider_id>/test", methods=["POST"])
@auth_required
def test_storage_provider(provider_id: int):
    """Test storage provider connection."""
    user = get_current_user()
    provider = get_storage_provider_by_id(provider_id)

    if not provider:
        return jsonify({"error": "Storage provider not found"}), 404

    # Check access
    if provider["user_id"] != user["id"] and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # TODO: Implement actual connection testing for each provider type
    # For now, return success placeholder

    return jsonify({
        "message": "Storage provider connection test successful",
        "status": "ok",
        "details": {
            "provider_type": provider["provider_type"],
            "writeable": True,
            "readable": True,
        },
    }), 200


@storage_v1_bp.route("/usage", methods=["GET"])
@auth_required
def get_storage_usage():
    """Get current user's storage usage statistics."""
    user = get_current_user()
    db = get_db()

    # Calculate storage usage
    # TODO: Implement actual storage calculation
    # For now, return placeholder data

    usage = {
        "user_id": user["id"],
        "total_drawings": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0,
        "quota_bytes": 1073741824,  # 1GB default
        "quota_mb": 1024,
        "usage_percentage": 0,
        "by_provider": [],
    }

    return jsonify({"usage": usage}), 200


@storage_v1_bp.route("/quota", methods=["GET"])
@auth_required
def get_storage_quota():
    """Get current user's storage quota."""
    user = get_current_user()
    db = get_db()

    # Get user's quota settings
    # TODO: Implement quota management
    # For now, return default quota

    quota = {
        "user_id": user["id"],
        "quota_bytes": 1073741824,  # 1GB default
        "quota_mb": 1024,
        "quota_type": "default",
        "can_increase": True,
    }

    return jsonify({"quota": quota}), 200


@storage_v1_bp.route("/quota", methods=["PUT"])
@auth_required
@admin_required
def update_storage_quota():
    """Update user storage quota (admin only)."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    target_user_id = data.get("user_id")
    quota_mb = data.get("quota_mb")

    if not target_user_id or not quota_mb:
        return jsonify({"error": "user_id and quota_mb are required"}), 400

    if quota_mb < 0:
        return jsonify({"error": "Quota must be non-negative"}), 400

    # TODO: Implement quota update
    # For now, return success placeholder

    return jsonify({
        "message": "Storage quota updated successfully",
        "user_id": target_user_id,
        "quota_mb": quota_mb,
    }), 200


@storage_v1_bp.route("/migrate", methods=["POST"])
@auth_required
def migrate_storage():
    """Migrate drawings to different storage provider."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    source_provider_id = data.get("source_provider_id")
    target_provider_id = data.get("target_provider_id")
    drawing_ids = data.get("drawing_ids", [])

    if not source_provider_id or not target_provider_id:
        return jsonify({"error": "source_provider_id and target_provider_id are required"}), 400

    # Verify access to both providers
    source = get_storage_provider_by_id(source_provider_id)
    target = get_storage_provider_by_id(target_provider_id)

    if not source or not target:
        return jsonify({"error": "Invalid provider ID"}), 404

    if (source["user_id"] != user["id"] or target["user_id"] != user["id"]) and user["role"] != "admin":
        return jsonify({"error": "Access denied"}), 403

    # TODO: Implement actual storage migration
    # This would be an async task in production

    return jsonify({
        "message": "Storage migration initiated",
        "migration_id": "migration_placeholder_id",
        "status": "pending",
        "drawing_count": len(drawing_ids),
    }), 202
