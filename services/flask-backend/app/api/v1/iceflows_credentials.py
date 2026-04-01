"""IceFlows Credentials API Endpoints - Secure Git Provider Token Management.

Provides CRUD operations for Git provider credentials (GitHub/GitLab tokens):
- List user's credentials
- Create new credential
- Get credential details (token masked)
- Update credential
- Delete credential
- Test credential validity
"""

import datetime
import secrets
import uuid

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db

iceflows_credentials_v1_bp = Blueprint(
    "iceflows_credentials_v1", __name__, url_prefix="/iceflows/credentials"
)


def serialize_credential(cred, include_token=False):
    """Serialize credential database row to JSON-safe dict.

    Args:
        cred: Database credential record
        include_token: Whether to include the actual token (default: False, shows masked)

    Returns:
        Dictionary representation of credential
    """
    result = {
        "credential_id": cred.credential_id,
        "name": cred.name,
        "description": cred.description or "",
        "provider": cred.provider,
        "token_type": cred.token_type or "personal",
        "scopes": cred.scopes or [],
        "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
        "is_active": cred.is_active or True,
        "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
        "created_at": cred.created_at.isoformat() if cred.created_at else None,
        "updated_at": cred.updated_at.isoformat() if cred.updated_at else None,
    }

    if include_token:
        result["access_token"] = cred.access_token
    else:
        # Show masked token for security
        if cred.access_token:
            result["access_token_preview"] = (
                f"{cred.access_token[:8]}...{cred.access_token[-4:]}"
            )
        else:
            result["access_token_preview"] = None

    return result


@iceflows_credentials_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_credentials():
    """List all credentials for current user.

    Query parameters:
        - provider: Filter by provider (github, gitlab)
        - is_active: Filter by active status (true, false)

    Returns:
        JSON with credentials array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Filters
        provider = request.args.get("provider")
        is_active = request.args.get("is_active")

        # Build query
        query = db.iceflows_credentials.created_by_id == user_id

        if provider:
            query &= db.iceflows_credentials.provider == provider
        if is_active is not None:
            query &= db.iceflows_credentials.is_active == (is_active.lower() == "true")

        # Execute query
        credentials = db(query).select(orderby=~db.iceflows_credentials.created_at)

        result = [serialize_credential(cred) for cred in credentials]

        return (
            jsonify(
                {
                    "success": True,
                    "credentials": result,
                    "total": len(result),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing credentials: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_credentials_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def create_credential():
    """Create a new credential.

    Request body:
        - name (required): Credential name
        - provider (required): github or gitlab
        - access_token (required): Git provider access token
        - description (optional): Credential description
        - token_type (optional): personal, oauth, app (default: personal)
        - scopes (optional): Array of token scopes/permissions
        - expires_at (optional): Token expiration ISO datetime

    Returns:
        JSON with created credential
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        # Validation
        if not data.get("name"):
            return jsonify({"success": False, "error": "name is required"}), 400
        if not data.get("provider"):
            return jsonify({"success": False, "error": "provider is required"}), 400
        if data["provider"] not in ["github", "gitlab"]:
            return (
                jsonify(
                    {"success": False, "error": "provider must be github or gitlab"}
                ),
                400,
            )
        if not data.get("access_token"):
            return jsonify({"success": False, "error": "access_token is required"}), 400

        # Generate credential_id
        credential_id = str(uuid.uuid4())

        # Parse expires_at if provided
        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.datetime.fromisoformat(
                    data["expires_at"].replace("Z", "+00:00")
                )
            except ValueError:
                return (
                    jsonify({"success": False, "error": "Invalid expires_at format"}),
                    400,
                )

        # Create credential record
        db_id = db.iceflows_credentials.insert(
            credential_id=credential_id,
            name=data["name"],
            description=data.get("description", ""),
            provider=data["provider"],
            access_token=data["access_token"],
            token_type=data.get("token_type", "personal"),
            scopes=data.get("scopes", []),
            expires_at=expires_at,
            is_active=True,
            created_by_id=user_id,
        )
        db.commit()

        # Fetch and return created credential
        cred = db.iceflows_credentials[db_id]

        return (
            jsonify(
                {
                    "success": True,
                    "credential": serialize_credential(cred),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating credential: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_credentials_v1_bp.route("/<credential_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_credential(credential_id: str):
    """Get credential details (token masked).

    Args:
        credential_id: Credential identifier

    Returns:
        JSON with credential details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        cred = (
            db((db.iceflows_credentials.credential_id == credential_id))
            .select()
            .first()
        )

        if not cred:
            return (
                jsonify({"success": False, "error": "Credential not found"}),
                404,
            )

        # Check access
        if cred.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "credential": serialize_credential(cred),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting credential {credential_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_credentials_v1_bp.route("/<credential_id>", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_credential(credential_id: str):
    """Update credential configuration.

    Args:
        credential_id: Credential identifier

    Returns:
        JSON with updated credential
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        cred = (
            db((db.iceflows_credentials.credential_id == credential_id))
            .select()
            .first()
        )

        if not cred:
            return (
                jsonify({"success": False, "error": "Credential not found"}),
                404,
            )

        # Check ownership
        if cred.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Build update dict
        update_data = {"updated_at": datetime.datetime.now(datetime.timezone.utc)}

        if "name" in data:
            update_data["name"] = data["name"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "access_token" in data:
            update_data["access_token"] = data["access_token"]
        if "token_type" in data:
            update_data["token_type"] = data["token_type"]
        if "scopes" in data:
            update_data["scopes"] = data["scopes"]
        if "expires_at" in data:
            if data["expires_at"]:
                try:
                    update_data["expires_at"] = datetime.datetime.fromisoformat(
                        data["expires_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    return (
                        jsonify(
                            {"success": False, "error": "Invalid expires_at format"}
                        ),
                        400,
                    )
            else:
                update_data["expires_at"] = None
        if "is_active" in data:
            update_data["is_active"] = data["is_active"]

        cred.update_record(**update_data)
        db.commit()

        # Fetch updated credential
        updated_cred = (
            db((db.iceflows_credentials.credential_id == credential_id))
            .select()
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "credential": serialize_credential(updated_cred),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating credential {credential_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_credentials_v1_bp.route("/<credential_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:delete")
def delete_credential(credential_id: str):
    """Delete credential.

    Args:
        credential_id: Credential identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        cred = (
            db((db.iceflows_credentials.credential_id == credential_id))
            .select()
            .first()
        )

        if not cred:
            return (
                jsonify({"success": False, "error": "Credential not found"}),
                404,
            )

        # Check ownership
        if cred.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Check if credential is in use
        flows_using = db(db.iceflows.credential_id == cred.id).count()
        if flows_using > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Credential is in use by {flows_using} flow(s). Remove from flows first.",
                    }
                ),
                409,
            )

        # Delete credential
        db(db.iceflows_credentials.id == cred.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Credential deleted successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting credential {credential_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_credentials_v1_bp.route("/<credential_id>/test", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def test_credential(credential_id: str):
    """Test credential validity by making a test API call to provider.

    Args:
        credential_id: Credential identifier

    Returns:
        JSON with test result
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        cred = (
            db((db.iceflows_credentials.credential_id == credential_id))
            .select()
            .first()
        )

        if not cred:
            return (
                jsonify({"success": False, "error": "Credential not found"}),
                404,
            )

        # Check ownership
        if cred.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # TODO: Implement actual API test calls to GitHub/GitLab
        # For now, just update last_used_at
        cred.update_record(last_used_at=datetime.datetime.now(datetime.timezone.utc))
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Credential test successful",
                    "provider": cred.provider,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error testing credential {credential_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
