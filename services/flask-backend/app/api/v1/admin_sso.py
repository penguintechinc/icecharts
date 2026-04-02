"""Admin SSO Configuration API endpoints."""

import logging

from app.licensing import check_feature, get_all_features
from app.middleware import admin_required, auth_required, get_current_user
from flask import Blueprint, jsonify, request

from ...models import get_db

logger = logging.getLogger(__name__)

admin_sso_v1_bp = Blueprint("admin_sso_v1", __name__, url_prefix="/admin/sso")


@admin_sso_v1_bp.route("/providers", methods=["GET"])
@auth_required
@admin_required
def get_available_providers():
    """
    Get available SSO providers based on license.

    Returns:
        JSON with available providers and their feature status:
        - google: Always available (free tier)
        - saml: Requires saml_sso feature (premium)
        - oidc: Requires oidc_sso feature (premium)
    """
    try:
        # Google OAuth is always available
        providers = [
            {
                "id": "google",
                "name": "Google OAuth 2.0",
                "description": "Sign in with Google accounts",
                "available": True,
                "premium": False,
            }
        ]

        # Check for SAML feature
        saml_available = check_feature("saml_sso")
        providers.append(
            {
                "id": "saml",
                "name": "SAML 2.0",
                "description": "Enterprise SAML single sign-on",
                "available": saml_available,
                "premium": True,
            }
        )

        # Check for OIDC feature
        oidc_available = check_feature("oidc_sso")
        providers.append(
            {
                "id": "oidc",
                "name": "OpenID Connect",
                "description": "Enterprise OIDC authentication",
                "available": oidc_available,
                "premium": True,
            }
        )

        return (
            jsonify(
                {
                    "providers": providers,
                    "has_premium": saml_available or oidc_available,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get SSO providers: {e}")
        return jsonify({"error": "Failed to retrieve SSO providers"}), 500


@admin_sso_v1_bp.route("", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def list_sso_configs():
    """
    List all SSO/IdP configurations.

    Returns:
        JSON with items array of SSO configurations
    """
    try:
        db = get_db()

        # Query all IdP configurations
        configs = db(db.idp_configurations.id > 0).select(
            orderby=~db.idp_configurations.created_at
        )

        items = []
        for config in configs:
            items.append(
                {
                    "id": config.id,
                    "provider": config.provider_type,  # 'saml' or 'oidc'
                    "name": config.name,
                    "enabled": config.is_active,
                    "client_id": config.oidc_client_id or config.entity_id or "",
                    "metadata_url": config.metadata_url or config.oidc_issuer_url or "",
                    "sso_url": config.sso_url or "",
                    "created_at": (
                        config.created_at.isoformat() if config.created_at else None
                    ),
                    "updated_at": (
                        config.updated_at.isoformat() if config.updated_at else None
                    ),
                }
            )

        return jsonify({"items": items}), 200

    except Exception as e:
        logger.error(f"Failed to list SSO configs: {e}")
        return jsonify({"error": "Failed to retrieve SSO configurations"}), 500


@admin_sso_v1_bp.route("", methods=["POST"], strict_slashes=False)
@auth_required
@admin_required
def create_sso_config():
    """
    Create a new SSO/IdP configuration.

    Expects JSON body:
        - provider: 'google', 'saml', or 'oauth2'
        - enabled: bool
        - client_id: str
        - client_secret: str
        - metadata_url: str (optional)
    """
    try:
        db = get_db()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        provider = data.get("provider")
        if provider not in ["google", "saml", "oauth2"]:
            return jsonify({"error": "Invalid provider type"}), 400

        # Map frontend provider to provider_type
        if provider == "google":
            provider_type = "oidc"
            name = "Google OAuth"
        elif provider == "saml":
            provider_type = "saml"
            name = data.get("name", "SAML Provider")
        else:
            provider_type = "oidc"
            name = data.get("name", "OAuth2 Provider")

        # Create the configuration
        config_id = db.idp_configurations.insert(
            tenant_id=1,  # Default tenant
            provider_type=provider_type,
            name=name,
            entity_id=data.get("client_id") if provider_type == "saml" else None,
            oidc_client_id=data.get("client_id") if provider_type == "oidc" else None,
            oidc_client_secret=(
                data.get("client_secret") if provider_type == "oidc" else None
            ),
            oidc_issuer_url=(
                data.get("metadata_url") if provider_type == "oidc" else None
            ),
            metadata_url=data.get("metadata_url") if provider_type == "saml" else None,
            sso_url=data.get("sso_url"),
            is_active=data.get("enabled", True),
        )
        db.commit()

        # Return the created config
        config = db.idp_configurations(config_id)

        current_user = get_current_user()
        logger.info(f"SSO config created by user {current_user['id']}: {name}")

        return (
            jsonify(
                {
                    "message": "SSO configuration created",
                    "config": {
                        "id": config.id,
                        "provider": provider,
                        "name": config.name,
                        "enabled": config.is_active,
                        "client_id": config.oidc_client_id or config.entity_id or "",
                        "metadata_url": config.metadata_url
                        or config.oidc_issuer_url
                        or "",
                    },
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Failed to create SSO config: {e}")
        return jsonify({"error": f"Failed to create SSO configuration: {str(e)}"}), 500


@admin_sso_v1_bp.route("/<int:config_id>", methods=["GET"])
@auth_required
@admin_required
def get_sso_config(config_id: int):
    """Get a single SSO configuration."""
    try:
        db = get_db()
        config = db.idp_configurations(config_id)

        if not config:
            return jsonify({"error": "SSO configuration not found"}), 404

        return (
            jsonify(
                {
                    "config": {
                        "id": config.id,
                        "provider": config.provider_type,
                        "name": config.name,
                        "enabled": config.is_active,
                        "client_id": config.oidc_client_id or config.entity_id or "",
                        "metadata_url": config.metadata_url
                        or config.oidc_issuer_url
                        or "",
                        "sso_url": config.sso_url or "",
                        "created_at": (
                            config.created_at.isoformat() if config.created_at else None
                        ),
                        "updated_at": (
                            config.updated_at.isoformat() if config.updated_at else None
                        ),
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to get SSO config {config_id}: {e}")
        return jsonify({"error": "Failed to retrieve SSO configuration"}), 500


@admin_sso_v1_bp.route("/<int:config_id>", methods=["PUT"])
@auth_required
@admin_required
def update_sso_config(config_id: int):
    """Update an SSO configuration."""
    try:
        db = get_db()
        config = db.idp_configurations(config_id)

        if not config:
            return jsonify({"error": "SSO configuration not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Build update dict
        update_data = {}

        if "enabled" in data:
            update_data["is_active"] = data["enabled"]

        if "client_id" in data:
            if config.provider_type == "oidc":
                update_data["oidc_client_id"] = data["client_id"]
            else:
                update_data["entity_id"] = data["client_id"]

        if "client_secret" in data and data["client_secret"]:
            update_data["oidc_client_secret"] = data["client_secret"]

        if "metadata_url" in data:
            if config.provider_type == "oidc":
                update_data["oidc_issuer_url"] = data["metadata_url"]
            else:
                update_data["metadata_url"] = data["metadata_url"]

        if "name" in data:
            update_data["name"] = data["name"]

        if update_data:
            config.update_record(**update_data)
            db.commit()

        current_user = get_current_user()
        logger.info(f"SSO config {config_id} updated by user {current_user['id']}")

        # Refresh config
        config = db.idp_configurations(config_id)

        return (
            jsonify(
                {
                    "message": "SSO configuration updated",
                    "config": {
                        "id": config.id,
                        "provider": config.provider_type,
                        "name": config.name,
                        "enabled": config.is_active,
                        "client_id": config.oidc_client_id or config.entity_id or "",
                        "metadata_url": config.metadata_url
                        or config.oidc_issuer_url
                        or "",
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to update SSO config {config_id}: {e}")
        return jsonify({"error": f"Failed to update SSO configuration: {str(e)}"}), 500


@admin_sso_v1_bp.route("/<int:config_id>", methods=["PATCH"])
@auth_required
@admin_required
def patch_sso_config(config_id: int):
    """Partial update an SSO configuration (e.g., toggle enabled)."""
    return update_sso_config(config_id)


@admin_sso_v1_bp.route("/<int:config_id>", methods=["DELETE"])
@auth_required
@admin_required
def delete_sso_config(config_id: int):
    """Delete an SSO configuration."""
    try:
        db = get_db()
        config = db.idp_configurations(config_id)

        if not config:
            return jsonify({"error": "SSO configuration not found"}), 404

        db(db.idp_configurations.id == config_id).delete()
        db.commit()

        current_user = get_current_user()
        logger.info(f"SSO config {config_id} deleted by user {current_user['id']}")

        return jsonify({"message": "SSO configuration deleted"}), 200

    except Exception as e:
        logger.error(f"Failed to delete SSO config {config_id}: {e}")
        return jsonify({"error": f"Failed to delete SSO configuration: {str(e)}"}), 500


__all__ = ["admin_sso_v1_bp"]
