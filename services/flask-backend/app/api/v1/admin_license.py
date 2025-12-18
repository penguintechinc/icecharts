"""Admin License Management API Endpoints for v1.

Provides endpoints for viewing and configuring the license key through the
admin interface. Supports dynamic license key updates without server restart.
"""

import logging
import re
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from app.middleware import admin_required, auth_required, get_current_user
from app.services.system_settings_service import SystemSettingsService
from app.licensing import (
    get_client,
    check_feature,
    get_all_features,
    reinitialize_licensing,
    LicenseValidationError,
)
from app.licensing.client import PenguinTechLicenseClient

logger = logging.getLogger(__name__)

admin_license_v1_bp = Blueprint("admin_license_v1", __name__, url_prefix="/admin/license")

# License key format regex
LICENSE_KEY_PATTERN = re.compile(r"^PENG-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")


def _mask_license_key(key: Optional[str]) -> Optional[str]:
    """Mask license key for display, showing only first and last segments."""
    if not key or len(key) < 29:
        return None
    # Show: PENG-XXXX-****-****-****-ABCD
    parts = key.split("-")
    if len(parts) != 6:
        return None
    return f"{parts[0]}-{parts[1]}-****-****-****-{parts[5]}"


def _get_license_status() -> Dict[str, Any]:
    """Get comprehensive license status information."""
    client = get_client()

    # Get stored license key (masked)
    stored_key = SystemSettingsService.get_setting("license_key")

    status = {
        "configured": stored_key is not None and bool(stored_key),
        "license_key_masked": _mask_license_key(stored_key) if stored_key else None,
        "valid": False,
        "tier": None,
        "customer": None,
        "expires_at": None,
        "features": [],
        "limits": None,
        "grace_period": False,
        "error": None,
    }

    if client is None:
        if stored_key:
            status["error"] = "License client not initialized - key may be invalid"
        return status

    try:
        # Validate and get current status
        validation = client.validate()

        status["valid"] = validation.get("valid", False)
        status["tier"] = validation.get("tier")
        status["customer"] = validation.get("customer")
        status["expires_at"] = validation.get("expires_at")
        status["limits"] = validation.get("limits")
        status["grace_period"] = client.is_in_grace_period()

        # Get features with details
        features = validation.get("features", [])
        status["features"] = [
            {
                "name": f.get("name"),
                "entitled": f.get("entitled", False),
                "description": f.get("description"),
                "units": f.get("units"),
            }
            for f in features
        ]

    except LicenseValidationError as e:
        status["error"] = str(e)
        status["grace_period"] = client.is_in_grace_period() if client else False
    except Exception as e:
        logger.error(f"Error getting license status: {e}")
        status["error"] = "Failed to validate license"

    return status


@admin_license_v1_bp.route("", methods=["GET"], strict_slashes=False)
@auth_required
@admin_required
def get_license_status():
    """
    Get current license status and configuration.

    Returns comprehensive license information including:
    - configured: Whether a license key is set
    - license_key_masked: Partially masked license key
    - valid: Whether the license is currently valid
    - tier: License tier (community, professional, enterprise)
    - customer: Customer name
    - expires_at: License expiration date
    - features: List of available features with entitlement status
    - limits: License limits (max_users, max_servers, etc.)
    - grace_period: Whether operating in grace period
    - error: Any validation error message
    """
    try:
        status = _get_license_status()
        return jsonify({"license": status}), 200
    except Exception as e:
        logger.error(f"Failed to get license status: {e}")
        return jsonify({"error": "Failed to retrieve license status"}), 500


@admin_license_v1_bp.route("", methods=["PUT"], strict_slashes=False)
@auth_required
@admin_required
def update_license_key():
    """
    Update the license key.

    Expects JSON body:
    - license_key: str - The new license key (format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD)

    The license key is validated before being saved. On success, the licensing
    system is re-initialized with the new key.
    """
    try:
        current_user = get_current_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        license_key = data.get("license_key", "").strip().upper()

        if not license_key:
            return jsonify({"error": "License key is required"}), 400

        # Validate format
        if not LICENSE_KEY_PATTERN.match(license_key):
            return jsonify({
                "error": "Invalid license key format",
                "message": "License key must be in format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
            }), 400

        # Additional format validation
        if not PenguinTechLicenseClient.is_valid_license_key(license_key):
            return jsonify({
                "error": "Invalid license key",
                "message": "License key validation failed"
            }), 400

        # Store the license key
        SystemSettingsService.set_setting("license_key", license_key, current_user["id"])

        # Re-initialize the licensing system with the new key
        try:
            success = reinitialize_licensing()
            if not success:
                # Key saved but validation failed - still keep the key
                logger.warning(f"License key saved but validation failed for user {current_user['id']}")
        except Exception as e:
            logger.warning(f"License re-initialization warning: {e}")

        # Get updated status
        status = _get_license_status()

        logger.info(f"License key updated by user {current_user['id']}")

        return jsonify({
            "message": "License key updated successfully",
            "license": status
        }), 200

    except Exception as e:
        logger.error(f"Failed to update license key: {e}")
        return jsonify({"error": "Failed to update license key"}), 500


@admin_license_v1_bp.route("", methods=["DELETE"], strict_slashes=False)
@auth_required
@admin_required
def remove_license_key():
    """
    Remove the license key.

    This will disable license-gated features until a new key is configured.
    """
    try:
        current_user = get_current_user()

        # Clear the license key
        SystemSettingsService.set_setting("license_key", "", current_user["id"])

        # Re-initialize licensing (will result in no client)
        reinitialize_licensing()

        logger.info(f"License key removed by user {current_user['id']}")

        return jsonify({
            "message": "License key removed",
            "license": _get_license_status()
        }), 200

    except Exception as e:
        logger.error(f"Failed to remove license key: {e}")
        return jsonify({"error": "Failed to remove license key"}), 500


@admin_license_v1_bp.route("/validate", methods=["POST"])
@auth_required
@admin_required
def validate_license_key():
    """
    Validate a license key without saving it.

    Use this to test a license key before committing to it.

    Expects JSON body:
    - license_key: str - The license key to validate

    Returns validation result including tier and features.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        license_key = data.get("license_key", "").strip().upper()

        if not license_key:
            return jsonify({"error": "License key is required"}), 400

        # Validate format
        if not LICENSE_KEY_PATTERN.match(license_key):
            return jsonify({
                "valid": False,
                "error": "Invalid license key format",
                "message": "License key must be in format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
            }), 400

        # Create a temporary client to validate
        import os
        product = os.getenv("PRODUCT_NAME", "icecharts")
        base_url = os.getenv("LICENSE_SERVER_URL")

        temp_client = PenguinTechLicenseClient(
            license_key=license_key,
            product=product,
            base_url=base_url,
        )

        try:
            validation = temp_client.validate()

            return jsonify({
                "valid": validation.get("valid", False),
                "tier": validation.get("tier"),
                "customer": validation.get("customer"),
                "expires_at": validation.get("expires_at"),
                "features": [
                    {
                        "name": f.get("name"),
                        "entitled": f.get("entitled", False),
                        "description": f.get("description"),
                    }
                    for f in validation.get("features", [])
                ],
                "limits": validation.get("limits"),
            }), 200

        except LicenseValidationError as e:
            return jsonify({
                "valid": False,
                "error": str(e)
            }), 200

    except Exception as e:
        logger.error(f"Failed to validate license key: {e}")
        return jsonify({"error": "Failed to validate license key"}), 500


@admin_license_v1_bp.route("/features", methods=["GET"])
@auth_required
@admin_required
def get_features():
    """
    Get all licensed features and their availability.

    Returns a list of all known features with their current entitlement status.
    """
    try:
        # Get current features from client
        features = get_all_features()

        # Include known IceCharts features even if not in response
        known_features = [
            {
                "name": "saml_sso",
                "display_name": "SAML 2.0 SSO",
                "description": "Enterprise SAML single sign-on authentication",
                "tier": "professional",
            },
            {
                "name": "oidc_sso",
                "display_name": "OpenID Connect SSO",
                "description": "Enterprise OIDC authentication",
                "tier": "professional",
            },
            {
                "name": "advanced_analytics",
                "display_name": "Advanced Analytics",
                "description": "Advanced reporting and analytics features",
                "tier": "professional",
            },
            {
                "name": "audit_logging",
                "display_name": "Audit Logging",
                "description": "Comprehensive audit log tracking",
                "tier": "enterprise",
            },
            {
                "name": "custom_branding",
                "display_name": "Custom Branding",
                "description": "Custom logo, colors, and branding",
                "tier": "enterprise",
            },
            {
                "name": "api_access",
                "display_name": "API Access",
                "description": "Full API access for integrations",
                "tier": "professional",
            },
        ]

        result = []
        for kf in known_features:
            feature_name = kf["name"]
            entitled = features.get(feature_name, False) if features else False

            result.append({
                "name": feature_name,
                "display_name": kf["display_name"],
                "description": kf["description"],
                "required_tier": kf["tier"],
                "entitled": entitled,
            })

        return jsonify({"features": result}), 200

    except Exception as e:
        logger.error(f"Failed to get features: {e}")
        return jsonify({"error": "Failed to retrieve features"}), 500


@admin_license_v1_bp.route("/refresh", methods=["POST"])
@auth_required
@admin_required
def refresh_license():
    """
    Force refresh the license validation.

    Re-validates the current license key with the license server and
    updates the cached feature entitlements.
    """
    try:
        current_user = get_current_user()

        success = reinitialize_licensing()

        if success:
            logger.info(f"License refreshed by user {current_user['id']}")
            return jsonify({
                "message": "License refreshed successfully",
                "license": _get_license_status()
            }), 200
        else:
            return jsonify({
                "message": "License refresh completed with warnings",
                "license": _get_license_status()
            }), 200

    except Exception as e:
        logger.error(f"Failed to refresh license: {e}")
        return jsonify({"error": "Failed to refresh license"}), 500


__all__ = ["admin_license_v1_bp"]
