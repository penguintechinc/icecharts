"""Profile Endpoints for API v1."""

import os
from datetime import datetime
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from ...middleware import auth_required, get_current_user
from ...models import get_db, get_user_by_id, update_user

profile_v1_bp = Blueprint("profile_v1", __name__, url_prefix="/profile")

# Allowed avatar file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_v1_bp.route("/me", methods=["GET"])
@auth_required
def get_profile():
    """Get current user profile."""
    user = get_current_user()

    return (
        jsonify(
            {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "role": user["role"],
                "is_active": user["is_active"],
                "avatar_url": user.get("avatar_url"),
                "bio": user.get("bio", ""),
                "preferences": user.get("preferences", {}),
                "mfa_enabled": user.get("mfa_enabled", False),
                "created_at": (
                    user["created_at"].isoformat() if user.get("created_at") else None
                ),
                "updated_at": (
                    user["updated_at"].isoformat() if user.get("updated_at") else None
                ),
            }
        ),
        200,
    )


@profile_v1_bp.route("/me", methods=["PATCH"])
@auth_required
def update_profile():
    """Update current user profile (partial update)."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Fields that users can update themselves
    allowed_fields = {"full_name", "bio", "preferences"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    # Update user
    updated_user = update_user(user["id"], **update_data)

    if not updated_user:
        return jsonify({"error": "Failed to update profile"}), 500

    return (
        jsonify(
            {
                "message": "Profile updated successfully",
                "user": {
                    "id": updated_user["id"],
                    "email": updated_user["email"],
                    "full_name": updated_user.get("full_name", ""),
                    "bio": updated_user.get("bio", ""),
                    "preferences": updated_user.get("preferences", {}),
                },
            }
        ),
        200,
    )


@profile_v1_bp.route("/avatar", methods=["PUT"])
@auth_required
def upload_avatar():
    """Upload or update user avatar."""
    user = get_current_user()

    # Check if file is in request
    if "avatar" not in request.files:
        return jsonify({"error": "No avatar file provided"}), 400

    file = request.files["avatar"]

    # Check if file was selected
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # Validate file
    if not allowed_file(file.filename):
        return (
            jsonify(
                {
                    "error": "Invalid file type",
                    "allowed_types": list(ALLOWED_EXTENSIONS),
                }
            ),
            400,
        )

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_AVATAR_SIZE:
        return (
            jsonify(
                {
                    "error": "File too large",
                    "max_size_mb": MAX_AVATAR_SIZE / (1024 * 1024),
                }
            ),
            400,
        )

    # Generate secure filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    new_filename = f"avatar_{user['id']}_{timestamp}.{ext}"

    # Save file (adjust path based on storage configuration)
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "/tmp/uploads")
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)

    # Update user avatar URL
    avatar_url = f"/api/v1/profile/avatars/{new_filename}"
    update_user(user["id"], avatar_url=avatar_url)

    return (
        jsonify(
            {
                "message": "Avatar uploaded successfully",
                "avatar_url": avatar_url,
            }
        ),
        200,
    )


@profile_v1_bp.route("/avatar", methods=["DELETE"])
@auth_required
def delete_avatar():
    """Delete user avatar."""
    user = get_current_user()

    # Remove avatar URL from user
    update_user(user["id"], avatar_url=None)

    # TODO: Also delete physical file if stored locally

    return (
        jsonify(
            {
                "message": "Avatar deleted successfully",
            }
        ),
        200,
    )


@profile_v1_bp.route("/preferences", methods=["GET"])
@auth_required
def get_preferences():
    """Get user preferences."""
    user = get_current_user()

    return (
        jsonify(
            {
                "preferences": user.get("preferences", {}),
            }
        ),
        200,
    )


@profile_v1_bp.route("/preferences", methods=["PUT"])
@auth_required
def update_preferences():
    """Update user preferences (full replace)."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Validate preferences format (must be a dictionary)
    if not isinstance(data, dict):
        return jsonify({"error": "Preferences must be a JSON object"}), 400

    # Store preferences as JSON
    update_user(user["id"], preferences=data)

    return (
        jsonify(
            {
                "message": "Preferences updated successfully",
                "preferences": data,
            }
        ),
        200,
    )


@profile_v1_bp.route("/preferences", methods=["PATCH"])
@auth_required
def patch_preferences():
    """Update user preferences (partial update)."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Merge with existing preferences
    current_prefs = user.get("preferences", {})
    updated_prefs = {**current_prefs, **data}

    update_user(user["id"], preferences=updated_prefs)

    return (
        jsonify(
            {
                "message": "Preferences updated successfully",
                "preferences": updated_prefs,
            }
        ),
        200,
    )


@profile_v1_bp.route("/password", methods=["PUT"])
@auth_required
def change_password():
    """Change user password."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    # Validation
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400

    # Verify current password
    from .auth import hash_password, verify_password

    user_record = get_user_by_id(user["id"])
    if not verify_password(current_password, user_record["password_hash"]):
        return jsonify({"error": "Current password is incorrect"}), 400

    # Update password
    new_password_hash = hash_password(new_password)
    update_user(user["id"], password_hash=new_password_hash)

    return (
        jsonify(
            {
                "message": "Password changed successfully",
            }
        ),
        200,
    )
