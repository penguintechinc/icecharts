"""Service Accounts Endpoints for API v1.

Admin endpoints for managing service accounts and their tokens
for external application integration.
"""

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from ...auth.scopes import AVAILABLE_SCOPES, SCOPE_GROUPS
from ...middleware import auth_required, get_current_user, admin_required
from ...schemas.service_account_schemas import (
    CreateServiceAccountRequest,
    UpdateServiceAccountRequest,
    GenerateTokenRequest,
)
from ...services.service_account_service import ServiceAccountService

service_accounts_v1_bp = Blueprint(
    "service_accounts_v1",
    __name__,
    url_prefix="/admin/service-accounts",
)


def validate_json(schema_class):
    """
    Helper to validate JSON request body using Pydantic schema.

    Returns:
        Tuple of (validated_data, error_response)
        If validation succeeds, error_response is None
        If validation fails, validated_data is None
    """
    data = request.get_json()
    if not data:
        return None, (jsonify({"error": "Request body required"}), 400)

    try:
        validated = schema_class(**data)
        return validated, None
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")

        return None, (
            jsonify({
                "error": "Validation failed",
                "details": errors,
                "available_scopes": list(AVAILABLE_SCOPES.keys()) if "scopes" in str(e) else None,
            }),
            400,
        )


@service_accounts_v1_bp.route("", methods=["GET"])
@auth_required
@admin_required
def list_service_accounts():
    """
    List all service accounts.

    Query parameters:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 20, max: 100)
        - include_inactive: Include inactive accounts (default: false)
    """
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        include_inactive = request.args.get("include_inactive", "false").lower() == "true"

        result = ServiceAccountService.list_service_accounts(
            tenant_id=tenant_id,
            page=page,
            per_page=per_page,
            include_inactive=include_inactive,
        )

        return jsonify({
            "success": True,
            **result,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing service accounts: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("", methods=["POST"])
@auth_required
@admin_required
def create_service_account():
    """
    Create a new service account.

    Request body:
        - name: Name of the service account (required)
        - description: Description (optional)
        - scopes: List of permission scopes (required)
        - rate_limit: Requests per hour (optional, default: 1000)
    """
    try:
        user = get_current_user()

        # Validate request body with Pydantic schema
        validated_data, error = validate_json(CreateServiceAccountRequest)
        if error:
            return error

        account = ServiceAccountService.create_service_account(
            name=validated_data.name,
            scopes=validated_data.scopes,
            created_by_id=user["id"],
            description=validated_data.description,
            rate_limit=validated_data.rate_limit,
            tenant_id=user.get("tenant_id", 1),
        )

        return jsonify({
            "success": True,
            "message": "Service account created successfully",
            "service_account": account,
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating service account: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>", methods=["GET"])
@auth_required
@admin_required
def get_service_account(account_id: int):
    """Get a service account by ID."""
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        account = ServiceAccountService.get_service_account_by_id(account_id)

        if not account:
            return jsonify({"error": "Service account not found"}), 404

        # Verify tenant ownership
        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        return jsonify({
            "success": True,
            "service_account": account,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting service account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>", methods=["PUT"])
@auth_required
@admin_required
def update_service_account(account_id: int):
    """
    Update a service account.

    Request body (all optional):
        - name: New name
        - description: New description
        - scopes: New list of scopes
        - rate_limit: New rate limit
        - is_active: Active status
    """
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify the service account exists and belongs to the current tenant
        existing_account = ServiceAccountService.get_service_account_by_id(account_id)
        if not existing_account:
            return jsonify({"error": "Service account not found"}), 404

        if existing_account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        # Validate request body with Pydantic schema
        validated_data, error = validate_json(UpdateServiceAccountRequest)
        if error:
            return error

        account = ServiceAccountService.update_service_account(
            account_id=account_id,
            name=validated_data.name,
            description=validated_data.description,
            scopes=validated_data.scopes,
            rate_limit=validated_data.rate_limit,
            is_active=validated_data.is_active,
        )

        if not account:
            return jsonify({"error": "Service account not found"}), 404

        return jsonify({
            "success": True,
            "service_account": account,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating service account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>", methods=["DELETE"])
@auth_required
@admin_required
def delete_service_account(account_id: int):
    """Delete a service account and all its tokens."""
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify the service account exists and belongs to the current tenant
        account = ServiceAccountService.get_service_account_by_id(account_id)
        if not account:
            return jsonify({"error": "Service account not found"}), 404

        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        deleted = ServiceAccountService.delete_service_account(account_id)

        if not deleted:
            return jsonify({"error": "Service account not found"}), 404

        return jsonify({
            "success": True,
            "message": "Service account deleted successfully",
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error deleting service account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


# Token management endpoints

@service_accounts_v1_bp.route("/<int:account_id>/tokens", methods=["GET"])
@auth_required
@admin_required
def list_tokens(account_id: int):
    """
    List all tokens for a service account.

    Query parameters:
        - include_revoked: Include revoked tokens (default: false)
    """
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify account exists and belongs to current tenant
        account = ServiceAccountService.get_service_account_by_id(account_id)
        if not account:
            return jsonify({"error": "Service account not found"}), 404

        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        include_revoked = request.args.get("include_revoked", "false").lower() == "true"

        tokens = ServiceAccountService.list_tokens(
            account_id=account_id,
            include_revoked=include_revoked,
        )

        return jsonify({
            "success": True,
            "count": len(tokens),
            "tokens": tokens,
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error listing tokens for account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>/tokens", methods=["POST"])
@auth_required
@admin_required
def generate_token(account_id: int):
    """
    Generate a new token for a service account.

    Request body (optional):
        - name: Label for the token
        - expires_days: Days until expiration (1-365, default: 365)

    Returns the token string - store it securely as it cannot be retrieved again.
    """
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify the service account exists and belongs to the current tenant
        account = ServiceAccountService.get_service_account_by_id(account_id)
        if not account:
            return jsonify({"error": "Service account not found"}), 404

        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        # Validate request body with Pydantic schema (allow empty body for defaults)
        data = request.get_json() or {}
        try:
            validated_data = GenerateTokenRequest(**data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                errors.append(f"{field}: {error['msg']}")

            max_days = current_app.config.get("SERVICE_ACCOUNT_TOKEN_MAX_DAYS", 365)
            return jsonify({
                "error": "Validation failed",
                "details": errors,
                "max_expires_days": max_days,
            }), 400

        result = ServiceAccountService.generate_token(
            account_id=account_id,
            name=validated_data.name,
            expires_days=validated_data.expires_days,
        )

        return jsonify({
            "success": True,
            "message": "Token generated successfully. Store it securely - it cannot be retrieved again.",
            "token": result["token"],
            "token_info": result["token_info"],
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error generating token for account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>/tokens/<token_jti>", methods=["DELETE"])
@auth_required
@admin_required
def revoke_token(account_id: int, token_jti: str):
    """Revoke a specific token."""
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify the service account exists and belongs to the current tenant
        account = ServiceAccountService.get_service_account_by_id(account_id)
        if not account:
            return jsonify({"error": "Service account not found"}), 404

        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        # Get the token to verify it belongs to this service account
        from app.models import get_db
        db = get_db()
        token = db(db.service_account_tokens.token_jti == token_jti).select().first()

        if not token:
            return jsonify({"error": "Token not found"}), 404

        if token.service_account_id != account_id:
            return jsonify({"error": "Token not found"}), 404

        revoked = ServiceAccountService.revoke_token(
            token_jti=token_jti,
            revoked_by_id=user["id"],
        )

        if not revoked:
            return jsonify({"error": "Token not found"}), 404

        return jsonify({
            "success": True,
            "message": "Token revoked successfully",
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error revoking token {token_jti}: {e}")
        return jsonify({"error": str(e)}), 500


@service_accounts_v1_bp.route("/<int:account_id>/tokens/revoke-all", methods=["POST"])
@auth_required
@admin_required
def revoke_all_tokens(account_id: int):
    """Revoke all tokens for a service account."""
    try:
        user = get_current_user()
        tenant_id = user.get("tenant_id", 1)

        # Verify account exists and belongs to current tenant
        account = ServiceAccountService.get_service_account_by_id(account_id)
        if not account:
            return jsonify({"error": "Service account not found"}), 404

        if account.get("tenant_id") != tenant_id:
            return jsonify({"error": "Service account not found"}), 404

        revoked_count = ServiceAccountService.revoke_all_tokens(
            account_id=account_id,
            revoked_by_id=user["id"],
        )

        return jsonify({
            "success": True,
            "message": f"Revoked {revoked_count} token(s)",
            "revoked_count": revoked_count,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error revoking all tokens for account {account_id}: {e}")
        return jsonify({"error": str(e)}), 500


# Scope reference endpoint

@service_accounts_v1_bp.route("/scopes", methods=["GET"])
@auth_required
@admin_required
def list_available_scopes():
    """Get list of available scopes and scope groups."""
    return jsonify({
        "success": True,
        "scopes": AVAILABLE_SCOPES,
        "scope_groups": SCOPE_GROUPS,
    }), 200
