"""Enterprise SSO (SAML 2.0 and OIDC) API endpoints."""

import json
import logging
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, jsonify, redirect, request, session
from flask_cors import cross_origin

from ...auth import (JITConfig, JITProvisioner, OIDCConfig, OIDCHandler,
                     SAMLConfig, SAMLHandler)
from ...licensing.decorators import feature_required
from ...middleware import auth_required, get_current_user

sso_v1_bp = Blueprint("sso", __name__, url_prefix="/sso")
logger = logging.getLogger(__name__)

# Check if SSO modules are available (may be None if dependencies are missing)
SSO_AVAILABLE = all(
    [SAMLConfig, SAMLHandler, OIDCConfig, OIDCHandler, JITConfig, JITProvisioner]
)


# ============================================================================
# SAML 2.0 Endpoints
# ============================================================================


@sso_v1_bp.route("/saml/metadata", methods=["GET"])
@cross_origin()
def saml_metadata():
    """Return SAML Service Provider metadata XML.

    This endpoint provides the SP metadata that should be registered with IdPs.
    No authentication required for metadata endpoint.
    """
    try:
        # Get SAML configuration from session or database
        saml_config = _get_active_saml_config()

        if not saml_config:
            return (
                jsonify(
                    {
                        "error": "SAML not configured",
                        "message": "No SAML IdP configuration found",
                    }
                ),
                404,
            )

        handler = SAMLHandler(saml_config)
        metadata = handler.get_metadata()

        return metadata, 200, {"Content-Type": "application/xml"}

    except Exception as e:
        logger.error(f"Error generating SAML metadata: {e}")
        return jsonify({"error": "Metadata generation failed", "message": str(e)}), 500


@sso_v1_bp.route("/saml/login", methods=["GET"])
@feature_required("saml_sso")
@cross_origin()
def saml_login():
    """Initiate SAML authentication flow.

    Redirects user to Identity Provider for authentication.
    """
    try:
        saml_config = _get_active_saml_config()

        if not saml_config:
            return (
                jsonify(
                    {
                        "error": "SAML not configured",
                        "message": "No SAML IdP configuration found",
                    }
                ),
                404,
            )

        handler = SAMLHandler(saml_config)
        login_url = handler.create_saml_request()

        return redirect(login_url)

    except Exception as e:
        logger.error(f"SAML login initiation failed: {e}")
        return jsonify({"error": "SAML login failed", "message": str(e)}), 500


@sso_v1_bp.route("/saml/acs", methods=["POST"])
@feature_required("saml_sso")
@cross_origin()
def saml_acs():
    """SAML Assertion Consumer Service endpoint.

    Processes SAML responses from Identity Provider.
    """
    try:
        saml_response = request.form.get("SAMLResponse")
        relay_state = request.form.get("RelayState")

        if not saml_response:
            return (
                jsonify(
                    {
                        "error": "Missing SAML response",
                        "message": "SAMLResponse parameter is required",
                    }
                ),
                400,
            )

        # Get SAML configuration
        saml_config = _get_active_saml_config()
        if not saml_config:
            return (
                jsonify(
                    {
                        "error": "SAML not configured",
                        "message": "No SAML IdP configuration found",
                    }
                ),
                404,
            )

        # Validate SAML response
        handler = SAMLHandler(saml_config)
        handler.parse_saml_response(saml_response, relay_state)

        # Extract user information
        user_data = handler.get_saml_user(saml_response)

        # JIT provisioning
        jit_config = _get_jit_config()
        provisioner = JITProvisioner(jit_config)

        user = provisioner.get_or_create_saml_user(user_data["attributes"], saml_config)

        # Generate JWT tokens
        tokens = _generate_user_tokens(user)

        # Return tokens - in production, would redirect to frontend with tokens
        return (
            jsonify(
                {
                    "message": "SAML authentication successful",
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                        "is_new": user["is_new"],
                    },
                    "tokens": tokens,
                }
            ),
            200,
        )

    except ValueError as e:
        logger.warning(f"SAML validation failed: {e}")
        return jsonify({"error": "SAML validation failed", "message": str(e)}), 401
    except Exception as e:
        logger.error(f"SAML ACS error: {e}")
        return jsonify({"error": "SAML processing failed", "message": str(e)}), 500


@sso_v1_bp.route("/saml/logout", methods=["POST"])
@auth_required
@feature_required("saml_sso")
def saml_logout():
    """Initiate SAML logout (Single Logout).

    Current user must be authenticated.
    """
    try:
        user = get_current_user()

        saml_config = _get_active_saml_config()
        if not saml_config:
            return (
                jsonify(
                    {
                        "error": "SAML not configured",
                        "message": "No SAML IdP configuration found",
                    }
                ),
                404,
            )

        handler = SAMLHandler(saml_config)

        # Optionally generate SLO request if SLO URL available
        if saml_config.slo_url:
            logger.info(f"User {user['email']} initiated SAML logout")

        return (
            jsonify(
                {
                    "message": "Logout initiated",
                    "logout_url": saml_config.slo_url,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"SAML logout error: {e}")
        return jsonify({"error": "SAML logout failed", "message": str(e)}), 500


# ============================================================================
# OpenID Connect Endpoints
# ============================================================================


@sso_v1_bp.route("/oidc/login", methods=["GET"])
@feature_required("oidc_sso")
@cross_origin()
def oidc_login():
    """Initiate OpenID Connect authentication flow.

    Query Parameters:
        provider_id: Optional provider configuration ID
    """
    try:
        oidc_config = _get_active_oidc_config()

        if not oidc_config:
            return (
                jsonify(
                    {
                        "error": "OIDC not configured",
                        "message": "No OIDC provider configuration found",
                    }
                ),
                404,
            )

        handler = OIDCHandler(oidc_config)

        # Generate PKCE pair
        code_verifier, code_challenge = handler.generate_pkce_pair()

        # Store code_verifier in session for later use
        session["oidc_code_verifier"] = code_verifier

        # Build authorization URL
        auth_url = handler.build_authorization_url(code_challenge=code_challenge)

        return redirect(auth_url)

    except Exception as e:
        logger.error(f"OIDC login initiation failed: {e}")
        return jsonify({"error": "OIDC login failed", "message": str(e)}), 500


@sso_v1_bp.route("/oidc/callback", methods=["GET"])
@feature_required("oidc_sso")
@cross_origin()
def oidc_callback():
    """OpenID Connect callback endpoint.

    Processes authorization code from provider.

    Query Parameters:
        code: Authorization code
        state: State parameter for CSRF protection
        error: Error code if authentication failed
    """
    try:
        # Check for errors
        error = request.args.get("error")
        if error:
            error_description = request.args.get("error_description", error)
            logger.warning(f"OIDC callback error: {error_description}")
            return jsonify({"error": error, "message": error_description}), 401

        # Get authorization code
        code = request.args.get("code")
        state = request.args.get("state")

        if not code:
            return (
                jsonify(
                    {
                        "error": "Missing authorization code",
                        "message": "code parameter is required",
                    }
                ),
                400,
            )

        # Get OIDC configuration
        oidc_config = _get_active_oidc_config()
        if not oidc_config:
            return (
                jsonify(
                    {
                        "error": "OIDC not configured",
                        "message": "No OIDC provider configuration found",
                    }
                ),
                404,
            )

        # Exchange code for tokens
        handler = OIDCHandler(oidc_config)
        code_verifier = session.get("oidc_code_verifier")

        token_response = handler.exchange_code_for_token(code, code_verifier)

        # Validate ID token if present
        id_token = token_response.get("id_token")
        access_token = token_response.get("access_token")

        if id_token:
            id_token_payload = handler.validate_id_token(id_token)
            userinfo = id_token_payload
        elif access_token:
            # Fetch userinfo using access token
            userinfo = handler.get_userinfo(access_token)
        else:
            raise ValueError("No ID token or access token in response")

        # JIT provisioning
        jit_config = _get_jit_config()
        provisioner = JITProvisioner(jit_config)

        user = provisioner.get_or_create_oidc_user(userinfo, oidc_config)

        # Generate JWT tokens
        tokens = _generate_user_tokens(user)

        # Clean up session
        if "oidc_code_verifier" in session:
            del session["oidc_code_verifier"]

        return (
            jsonify(
                {
                    "message": "OIDC authentication successful",
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                        "is_new": user["is_new"],
                    },
                    "tokens": tokens,
                }
            ),
            200,
        )

    except ValueError as e:
        logger.warning(f"OIDC validation failed: {e}")
        return jsonify({"error": "OIDC validation failed", "message": str(e)}), 401
    except Exception as e:
        logger.error(f"OIDC callback error: {e}")
        return jsonify({"error": "OIDC processing failed", "message": str(e)}), 500


# ============================================================================
# Admin Configuration Endpoints (License-Gated)
# ============================================================================


@sso_v1_bp.route("/saml/config", methods=["GET"])
@auth_required
@feature_required("saml_sso")
def get_saml_config():
    """Get current SAML configuration (admin only)."""
    user = get_current_user()
    if user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        saml_config = _get_active_saml_config()

        if not saml_config:
            return jsonify({"message": "No SAML configuration", "config": None}), 200

        return (
            jsonify(
                {
                    "config": {
                        "idp_name": saml_config.idp_name,
                        "idp_entity_id": saml_config.idp_entity_id,
                        "sso_url": saml_config.sso_url,
                        "slo_url": saml_config.slo_url,
                        "name_id_format": saml_config.name_id_format,
                        "metadata_url": saml_config.metadata_url,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrieving SAML config: {e}")
        return (
            jsonify({"error": "Configuration retrieval failed", "message": str(e)}),
            500,
        )


@sso_v1_bp.route("/saml/config", methods=["POST"])
@auth_required
@feature_required("saml_sso")
def set_saml_config():
    """Configure SAML IdP (admin only)."""
    user = get_current_user()
    if user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Load SAML config from metadata URL or manual config
        metadata_url = data.get("metadata_url")

        if metadata_url:
            saml_config = SAMLConfig.from_metadata_url(metadata_url)
        else:
            # Manual configuration
            required_fields = ["idp_name", "idp_entity_id", "sso_url", "x509_cert"]
            for field in required_fields:
                if not data.get(field):
                    return (
                        jsonify({"error": "Missing required field", "field": field}),
                        400,
                    )

            saml_config = SAMLConfig(
                idp_name=data["idp_name"],
                idp_entity_id=data["idp_entity_id"],
                sso_url=data["sso_url"],
                slo_url=data.get("slo_url"),
                x509_cert=data["x509_cert"],
            )

        # Store configuration
        _store_saml_config(saml_config)

        # Configure JIT if specified
        if data.get("jit_enabled"):
            jit_config = JITConfig(
                enabled=True,
                auto_assign_role=data.get("auto_assign_role", "viewer"),
            )
            _store_jit_config(jit_config)

        logger.info(f"SAML configuration updated by {user['email']}")

        return (
            jsonify(
                {
                    "message": "SAML configuration saved",
                    "config": {
                        "idp_name": saml_config.idp_name,
                        "idp_entity_id": saml_config.idp_entity_id,
                        "sso_url": saml_config.sso_url,
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        logger.warning(f"SAML config validation failed: {e}")
        return jsonify({"error": "Invalid configuration", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting SAML config: {e}")
        return jsonify({"error": "Configuration failed", "message": str(e)}), 500


@sso_v1_bp.route("/oidc/config", methods=["GET"])
@auth_required
@feature_required("oidc_sso")
def get_oidc_config():
    """Get current OIDC configuration (admin only)."""
    user = get_current_user()
    if user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        oidc_config = _get_active_oidc_config()

        if not oidc_config:
            return jsonify({"message": "No OIDC configuration", "config": None}), 200

        return (
            jsonify(
                {
                    "config": {
                        "issuer": oidc_config.issuer,
                        "client_id": oidc_config.client_id,
                        "authorization_endpoint": oidc_config.authorization_endpoint,
                        "token_endpoint": oidc_config.token_endpoint,
                        "userinfo_endpoint": oidc_config.userinfo_endpoint,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrieving OIDC config: {e}")
        return (
            jsonify({"error": "Configuration retrieval failed", "message": str(e)}),
            500,
        )


@sso_v1_bp.route("/oidc/config", methods=["POST"])
@auth_required
@feature_required("oidc_sso")
def set_oidc_config():
    """Configure OIDC provider (admin only)."""
    user = get_current_user()
    if user["role"] != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body required"}), 400

        # Validate required fields
        required_fields = ["issuer", "client_id", "client_secret"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": "Missing required field", "field": field}), 400

        # Discover OIDC configuration
        oidc_config = OIDCConfig.from_discovery(
            issuer=data["issuer"],
            client_id=data["client_id"],
            client_secret=data["client_secret"],
        )

        # Store configuration
        _store_oidc_config(oidc_config)

        # Configure JIT if specified
        if data.get("jit_enabled"):
            jit_config = JITConfig(
                enabled=True,
                auto_assign_role=data.get("auto_assign_role", "viewer"),
            )
            _store_jit_config(jit_config)

        logger.info(f"OIDC configuration updated by {user['email']}")

        return (
            jsonify(
                {
                    "message": "OIDC configuration saved",
                    "config": {
                        "issuer": oidc_config.issuer,
                        "client_id": oidc_config.client_id,
                    },
                }
            ),
            200,
        )

    except ValueError as e:
        logger.warning(f"OIDC config validation failed: {e}")
        return jsonify({"error": "Invalid configuration", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Error setting OIDC config: {e}")
        return jsonify({"error": "Configuration failed", "message": str(e)}), 500


# ============================================================================
# Helper Functions
# ============================================================================


def _get_active_saml_config() -> Optional[SAMLConfig]:
    """Get active SAML configuration."""
    from flask import g

    if "saml_config" not in g:
        g.saml_config = None
    return g.saml_config


def _store_saml_config(config: SAMLConfig) -> None:
    """Store SAML configuration."""
    from flask import g

    g.saml_config = config


def _get_active_oidc_config() -> Optional[OIDCConfig]:
    """Get active OIDC configuration."""
    from flask import g

    if "oidc_config" not in g:
        g.oidc_config = None
    return g.oidc_config


def _store_oidc_config(config: OIDCConfig) -> None:
    """Store OIDC configuration."""
    from flask import g

    g.oidc_config = config


def _get_jit_config() -> JITConfig:
    """Get JIT provisioning configuration."""
    from flask import g

    if "jit_config" not in g:
        g.jit_config = JITConfig(enabled=True)
    return g.jit_config


def _store_jit_config(config: JITConfig) -> None:
    """Store JIT configuration."""
    from flask import g

    g.jit_config = config


def _generate_user_tokens(user: Dict[str, Any]) -> Dict[str, str]:
    """Generate JWT tokens for user."""
    import hashlib
    from datetime import datetime

    import bcrypt
    import jwt

    expires = datetime.utcnow() + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {
        "sub": str(user["id"]),
        "role": user["role"],
        "type": "access",
        "exp": expires,
        "iat": datetime.utcnow(),
    }
    access_token = jwt.encode(
        payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )

    # Refresh token
    refresh_expires = (
        datetime.utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    )
    refresh_payload = {
        "sub": str(user["id"]),
        "type": "refresh",
        "exp": refresh_expires,
        "iat": datetime.utcnow(),
    }
    refresh_token = jwt.encode(
        refresh_payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256"
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(
            current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()
        ),
    }


__all__ = ["sso_v1_bp"]
