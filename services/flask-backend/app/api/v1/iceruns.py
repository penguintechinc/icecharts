"""IceRuns Function Management Endpoints for API v1.

Provides CRUD operations and configuration for serverless function execution.
"""

import datetime
import secrets
from typing import Optional

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...services.iceruns_storage_service import IceRunsStorageService
from ...utils.validation import validate_json

iceruns_v1_bp = Blueprint("iceruns_v1", __name__, url_prefix="/iceruns")

# Valid runtimes
VALID_RUNTIMES = ["python3.13", "nodejs", "go", "ruby", "bash", "powershell", "rust"]


def serialize_function(func):
    """Serialize IceRuns function to JSON."""
    return {
        "function_id": func.function_id,
        "name": func.name,
        "description": func.description or "",
        "runtime": func.runtime,
        "entrypoint": func.entrypoint,
        "handler": func.handler,
        "package_key": func.package_key,
        "package_size": func.package_size,
        "memory_limit_mb": func.memory_limit_mb,
        "timeout_seconds": func.timeout_seconds,
        "cpu_limit": func.cpu_limit,
        "status": func.status,
        "is_public": func.is_public,
        "tags": func.tags or [],
        "created_by_id": str(func.created_by_id) if func.created_by_id else None,
        "created_at": func.created_at.isoformat() if func.created_at else None,
        "updated_at": func.updated_at.isoformat() if func.updated_at else None,
        "last_executed_at": func.last_executed_at.isoformat() if func.last_executed_at else None,
        "execution_count": func.execution_count or 0,
        "webhook_url": f"/api/v1/iceruns/hook/{func.webhook_token}" if func.webhook_token else None,
    }


@iceruns_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("iceruns:read")
def list_functions():
    """List all functions for current user."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query filters
        status = request.args.get("status")
        runtime = request.args.get("runtime")
        tags = request.args.getlist("tags")
        search = request.args.get("q")

        query = db.iceruns.created_by_id == user_id

        if status:
            query &= db.iceruns.status == status
        if runtime:
            query &= db.iceruns.runtime == runtime
        if tags:
            for tag in tags:
                query &= db.iceruns.tags.contains(tag)
        if search:
            query &= (db.iceruns.name.contains(search) | db.iceruns.description.contains(search))

        functions = db(query).select(orderby=~db.iceruns.updated_at)
        result = [serialize_function(f) for f in functions]

        return jsonify({"success": True, "count": len(result), "items": result}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing functions: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("iceruns:write")
def create_function():
    """Create new IceRuns function."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json()

        # Validation
        if not data.get("name"):
            return jsonify({"error": "name is required"}), 400
        if not data.get("runtime") or data["runtime"] not in VALID_RUNTIMES:
            return jsonify({"error": f"runtime must be one of {VALID_RUNTIMES}"}), 400
        if not data.get("entrypoint"):
            return jsonify({"error": "entrypoint is required"}), 400
        if not data.get("handler"):
            return jsonify({"error": "handler is required"}), 400

        # Resource limits validation
        memory_limit = data.get("memory_limit_mb", 128)
        if not (128 <= memory_limit <= 4096):
            return jsonify({"error": "memory_limit_mb must be between 128 and 4096"}), 400

        timeout = data.get("timeout_seconds", 60)
        if not (1 <= timeout <= 900):
            return jsonify({"error": "timeout_seconds must be between 1 and 900"}), 400

        cpu_limit = data.get("cpu_limit", 0.5)
        if not (0.1 <= cpu_limit <= 4.0):
            return jsonify({"error": "cpu_limit must be between 0.1 and 4.0"}), 400

        db = get_db()

        # Generate tokens
        function_id = secrets.token_urlsafe(16)
        webhook_token = secrets.token_urlsafe(32)
        webhook_secret = secrets.token_urlsafe(64)

        # Create function
        func_id = db.iceruns.insert(
            function_id=function_id,
            name=data["name"],
            description=data.get("description"),
            runtime=data["runtime"],
            entrypoint=data["entrypoint"],
            handler=data["handler"],
            env_vars=data.get("env_vars", {}),
            secrets=data.get("secrets", {}),
            memory_limit_mb=memory_limit,
            timeout_seconds=timeout,
            cpu_limit=cpu_limit,
            status="draft",
            is_public=data.get("is_public", False),
            webhook_token=webhook_token,
            webhook_secret=webhook_secret,
            validate_signature=data.get("validate_signature", False),
            allowed_methods=data.get("allowed_methods", ["POST"]),
            ip_whitelist=data.get("ip_whitelist", []),
            rate_limit=data.get("rate_limit", 100),
            tags=data.get("tags", []),
            created_by_id=user_id,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )

        db.commit()

        func = db.iceruns[func_id]
        return jsonify({"success": True, "function": serialize_function(func)}), 201

    except Exception as e:
        current_app.logger.error(f"Error creating function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>", methods=["GET"])
@auth_required
@scopes_required("iceruns:read")
def get_function(function_id: str):
    """Get function details."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        return jsonify({"success": True, "function": serialize_function(func)}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def update_function(function_id: str):
    """Update function configuration."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json()
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        # Update fields
        update_fields = {}
        if "name" in data:
            update_fields["name"] = data["name"]
        if "description" in data:
            update_fields["description"] = data["description"]
        if "runtime" in data and data["runtime"] in VALID_RUNTIMES:
            update_fields["runtime"] = data["runtime"]
        if "entrypoint" in data:
            update_fields["entrypoint"] = data["entrypoint"]
        if "handler" in data:
            update_fields["handler"] = data["handler"]
        if "env_vars" in data:
            update_fields["env_vars"] = data["env_vars"]
        if "secrets" in data:
            update_fields["secrets"] = data["secrets"]
        if "memory_limit_mb" in data:
            if not (128 <= data["memory_limit_mb"] <= 4096):
                return jsonify({"error": "memory_limit_mb must be between 128 and 4096"}), 400
            update_fields["memory_limit_mb"] = data["memory_limit_mb"]
        if "timeout_seconds" in data:
            if not (1 <= data["timeout_seconds"] <= 900):
                return jsonify({"error": "timeout_seconds must be between 1 and 900"}), 400
            update_fields["timeout_seconds"] = data["timeout_seconds"]
        if "cpu_limit" in data:
            if not (0.1 <= data["cpu_limit"] <= 4.0):
                return jsonify({"error": "cpu_limit must be between 0.1 and 4.0"}), 400
            update_fields["cpu_limit"] = data["cpu_limit"]
        if "tags" in data:
            update_fields["tags"] = data["tags"]
        if "is_public" in data:
            update_fields["is_public"] = data["is_public"]

        update_fields["updated_at"] = datetime.datetime.utcnow()

        db(db.iceruns.id == func.id).update(**update_fields)
        db.commit()

        updated_func = db.iceruns[func.id]
        return jsonify({"success": True, "function": serialize_function(updated_func)}), 200

    except Exception as e:
        current_app.logger.error(f"Error updating function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceruns:delete")
def delete_function(function_id: str):
    """Delete function and associated resources."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        # Delete package from storage
        if func.package_key:
            IceRunsStorageService.delete_package(function_id)

        # Delete database record
        db(db.iceruns.id == func.id).delete()
        db.commit()

        return jsonify({"success": True, "message": "Function deleted"}), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/package", methods=["POST"])
@auth_required
@scopes_required("iceruns:write")
def upload_package(function_id: str):
    """Upload function package to S3."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        if "package" not in request.files:
            return jsonify({"error": "No package file provided"}), 400

        file = request.files["package"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400

        # Upload to S3
        result = IceRunsStorageService.save_package(function_id, file.stream, file.filename)

        # Update database
        db(db.iceruns.id == func.id).update(
            package_key=result["package_key"],
            package_size=result["size"],
            package_hash=result["hash"],
            updated_at=datetime.datetime.utcnow(),
        )
        db.commit()

        return jsonify({"success": True, "package": result}), 200

    except Exception as e:
        current_app.logger.error(f"Error uploading package: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/package", methods=["GET"])
@auth_required
@scopes_required("iceruns:read")
def download_package(function_id: str):
    """Get presigned URL for package download."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func or not func.package_key:
            return jsonify({"error": "Package not found"}), 404

        url = IceRunsStorageService.get_package_url(function_id, expires_in=3600)

        return jsonify({"success": True, "url": url, "expires_in": 3600}), 200

    except Exception as e:
        current_app.logger.error(f"Error downloading package: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/package", methods=["DELETE"])
@auth_required
@scopes_required("iceruns:delete")
def delete_package(function_id: str):
    """Delete function package."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        if func.package_key:
            IceRunsStorageService.delete_package(function_id)

        db(db.iceruns.id == func.id).update(
            package_key=None, package_size=None, package_hash=None, updated_at=datetime.datetime.utcnow()
        )
        db.commit()

        return jsonify({"success": True, "message": "Package deleted"}), 200

    except Exception as e:
        current_app.logger.error(f"Error deleting package: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/activate", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def activate_function(function_id: str):
    """Activate function (set status to active)."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        if not func.package_key:
            return jsonify({"error": "Cannot activate function without package"}), 400

        db(db.iceruns.id == func.id).update(status="active", updated_at=datetime.datetime.utcnow())
        db.commit()

        return jsonify({"success": True, "status": "active"}), 200

    except Exception as e:
        current_app.logger.error(f"Error activating function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/pause", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def pause_function(function_id: str):
    """Pause function (set status to paused)."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        db(db.iceruns.id == func.id).update(status="paused", updated_at=datetime.datetime.utcnow())
        db.commit()

        return jsonify({"success": True, "status": "paused"}), 200

    except Exception as e:
        current_app.logger.error(f"Error pausing function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/archive", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def archive_function(function_id: str):
    """Archive function (set status to archived)."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        db(db.iceruns.id == func.id).update(status="archived", updated_at=datetime.datetime.utcnow())
        db.commit()

        return jsonify({"success": True, "status": "archived"}), 200

    except Exception as e:
        current_app.logger.error(f"Error archiving function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/webhook/regenerate", methods=["POST"])
@auth_required
@scopes_required("iceruns:write")
def regenerate_webhook_token(function_id: str):
    """Regenerate webhook token and secret."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        new_token = secrets.token_urlsafe(32)
        new_secret = secrets.token_urlsafe(64)

        db(db.iceruns.id == func.id).update(
            webhook_token=new_token, webhook_secret=new_secret, updated_at=datetime.datetime.utcnow()
        )
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "webhook_token": new_token,
                    "webhook_secret": new_secret,
                    "webhook_url": f"/api/v1/iceruns/hook/{new_token}",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error regenerating webhook token: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/versions", methods=["GET"])
@auth_required
@scopes_required("iceruns:read")
def list_versions(function_id: str):
    """List function versions."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        versions = db(db.iceruns_versions.function_id == func.id).select(
            orderby=~db.iceruns_versions.version_number
        )

        result = [
            {
                "version_id": v.version_id,
                "version_number": v.version_number,
                "package_key": v.package_key,
                "package_hash": v.package_hash,
                "entrypoint": v.entrypoint,
                "handler": v.handler,
                "change_summary": v.change_summary,
                "is_active": v.is_active,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]

        return jsonify({"success": True, "count": len(result), "versions": result}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing versions: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/config", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def update_config(function_id: str):
    """Update runtime configuration."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json()
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        update_fields = {}
        if "memory_limit_mb" in data:
            if not (128 <= data["memory_limit_mb"] <= 4096):
                return jsonify({"error": "memory_limit_mb must be between 128 and 4096"}), 400
            update_fields["memory_limit_mb"] = data["memory_limit_mb"]
        if "timeout_seconds" in data:
            if not (1 <= data["timeout_seconds"] <= 900):
                return jsonify({"error": "timeout_seconds must be between 1 and 900"}), 400
            update_fields["timeout_seconds"] = data["timeout_seconds"]
        if "cpu_limit" in data:
            if not (0.1 <= data["cpu_limit"] <= 4.0):
                return jsonify({"error": "cpu_limit must be between 0.1 and 4.0"}), 400
            update_fields["cpu_limit"] = data["cpu_limit"]

        update_fields["updated_at"] = datetime.datetime.utcnow()

        db(db.iceruns.id == func.id).update(**update_fields)
        db.commit()

        return jsonify({"success": True, "message": "Configuration updated"}), 200

    except Exception as e:
        current_app.logger.error(f"Error updating config: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_v1_bp.route("/<function_id>/secrets", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def update_secrets(function_id: str):
    """Update encrypted secrets."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json()
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        if "secrets" not in data or not isinstance(data["secrets"], dict):
            return jsonify({"error": "secrets must be a dictionary"}), 400

        db(db.iceruns.id == func.id).update(secrets=data["secrets"], updated_at=datetime.datetime.utcnow())
        db.commit()

        return jsonify({"success": True, "message": "Secrets updated"}), 200

    except Exception as e:
        current_app.logger.error(f"Error updating secrets: {e}")
        return jsonify({"error": str(e)}), 500
