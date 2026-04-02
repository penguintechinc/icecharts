"""Admin Settings API Endpoints for v1."""

import logging

from app.config import Config
from app.middleware import admin_required, auth_required, get_current_user
from app.services.system_settings_service import SystemSettingsService
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

admin_settings_v1_bp = Blueprint(
    "admin_settings_v1", __name__, url_prefix="/admin/settings"
)


@admin_settings_v1_bp.route("/signup", methods=["GET"])
@auth_required
@admin_required
def get_signup_settings():
    """
    Get signup configuration settings.

    Returns signup settings including:
    - enabled: Whether signup is enabled
    - mode: Signup mode (open, domain_restricted, sso_only, disabled)
    - allowed_domains: List of allowed email domains
    - email_verification_required: Whether email verification is required
    """
    try:
        signup_config = SystemSettingsService.get_signup_config()

        return jsonify({"signup": signup_config}), 200

    except Exception as e:
        logger.error(f"Failed to get signup settings: {str(e)}")
        return jsonify({"error": "Failed to retrieve signup settings"}), 500


@admin_settings_v1_bp.route("/signup", methods=["PUT"])
@auth_required
@admin_required
def update_signup_settings():
    """
    Update signup configuration settings.

    Expects JSON body with optional fields:
    - enabled: bool - Enable/disable signup
    - mode: str - Signup mode (open, domain_restricted, sso_only, disabled)
    - allowed_domains: list - Allowed email domains (for domain_restricted mode)
    - email_verification_required: bool - Require email verification
    """
    try:
        current_user = get_current_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract fields
        enabled = data.get("enabled")
        mode = data.get("mode")
        allowed_domains = data.get("allowed_domains")
        email_verification_required = data.get("email_verification_required")

        # Validate mode if provided
        if mode is not None:
            valid_modes = ["open", "domain_restricted", "sso_only", "disabled"]
            if mode not in valid_modes:
                return (
                    jsonify(
                        {
                            "error": f"Invalid signup mode. Must be one of: {', '.join(valid_modes)}"
                        }
                    ),
                    400,
                )

        # Validate allowed_domains if provided
        if allowed_domains is not None:
            if not isinstance(allowed_domains, list):
                return jsonify({"error": "allowed_domains must be a list"}), 400

            # Validate each domain
            for domain in allowed_domains:
                if not isinstance(domain, str) or not domain.strip():
                    return jsonify({"error": "Invalid domain in allowed_domains"}), 400

        # Update settings
        success = SystemSettingsService.update_signup_config(
            enabled=enabled,
            mode=mode,
            allowed_domains=allowed_domains,
            email_verification_required=email_verification_required,
            user_id=current_user["id"],
        )

        if not success:
            return jsonify({"error": "Failed to update signup settings"}), 500

        # Return updated config
        signup_config = SystemSettingsService.get_signup_config()

        logger.info(f"Signup settings updated by user {current_user['id']}")

        return (
            jsonify(
                {
                    "message": "Signup settings updated successfully",
                    "signup": signup_config,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to update signup settings: {str(e)}")
        return jsonify({"error": "Failed to update signup settings"}), 500


@admin_settings_v1_bp.route("/email", methods=["GET"])
@auth_required
@admin_required
def get_email_settings():
    """
    Get email configuration settings.

    Returns email settings including:
    - provider: Email provider (sendmail, smtp, sendgrid, aws_ses, mailgun, gmail)
    - from_email: From email address
    - from_name: From name for emails
    - available_providers: List of available email providers
    """
    try:
        email_config = SystemSettingsService.get_email_config()

        # Add list of available providers
        email_config["available_providers"] = [
            {"value": "sendmail", "label": "Sendmail (Default)"},
            {"value": "smtp", "label": "SMTP (Generic)"},
            {"value": "sendgrid", "label": "SendGrid"},
            {"value": "aws_ses", "label": "AWS SES"},
            {"value": "mailgun", "label": "Mailgun"},
            {"value": "gmail", "label": "Gmail"},
        ]

        return jsonify({"email": email_config}), 200

    except Exception as e:
        logger.error(f"Failed to get email settings: {str(e)}")
        return jsonify({"error": "Failed to retrieve email settings"}), 500


@admin_settings_v1_bp.route("/email", methods=["PUT"])
@auth_required
@admin_required
def update_email_settings():
    """
    Update email configuration settings.

    Expects JSON body with optional fields:
    - provider: str - Email provider (sendmail, smtp, sendgrid, aws_ses, mailgun, gmail)
    - from_email: str - From email address
    - from_name: str - From name for emails

    Note: This endpoint only updates the provider selection and basic settings.
    Provider-specific credentials (API keys, SMTP passwords, etc.) should be
    configured via environment variables for security.
    """
    try:
        current_user = get_current_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract fields
        provider = data.get("provider")
        from_email = data.get("from_email")
        from_name = data.get("from_name")

        # Validate provider if provided
        if provider is not None:
            valid_providers = [
                "sendmail",
                "smtp",
                "sendgrid",
                "aws_ses",
                "mailgun",
                "gmail",
            ]
            if provider not in valid_providers:
                return (
                    jsonify(
                        {
                            "error": f"Invalid email provider. Must be one of: {', '.join(valid_providers)}"
                        }
                    ),
                    400,
                )

        # Validate from_email if provided
        if from_email is not None:
            if not isinstance(from_email, str) or not from_email.strip():
                return jsonify({"error": "from_email must be a non-empty string"}), 400
            # Basic email validation
            if "@" not in from_email:
                return jsonify({"error": "Invalid email address"}), 400

        # Update settings
        success = SystemSettingsService.update_email_config(
            provider=provider,
            from_email=from_email,
            from_name=from_name,
            user_id=current_user["id"],
        )

        if not success:
            return jsonify({"error": "Failed to update email settings"}), 500

        # Return updated config
        email_config = SystemSettingsService.get_email_config()

        logger.info(f"Email settings updated by user {current_user['id']}")

        return (
            jsonify(
                {
                    "message": "Email settings updated successfully",
                    "email": email_config,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to update email settings: {str(e)}")
        return jsonify({"error": "Failed to update email settings"}), 500


@admin_settings_v1_bp.route("/email/test", methods=["POST"])
@auth_required
@admin_required
def test_email():
    """
    Send a test email to verify email configuration.

    Expects JSON body with:
    - to: str - Recipient email address (defaults to current user's email)
    """
    try:
        from app.services.email_service import EmailService

        current_user = get_current_user()
        data = request.get_json() or {}

        # Get recipient email
        to_email = data.get("to", current_user.get("email"))

        if not to_email:
            return jsonify({"error": "No recipient email address provided"}), 400

        # Get site settings
        site_name = SystemSettingsService.get_setting("site_name", Config.APP_NAME)

        # Send test email
        subject = f"Test Email from {site_name}"
        body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9f9f9; padding: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{site_name}</h1>
                </div>
                <div class="content">
                    <h2>Test Email</h2>
                    <p>This is a test email from {site_name}.</p>
                    <p>If you received this email, your email configuration is working correctly!</p>
                    <p><strong>Sent by:</strong> {current_user.get('full_name', current_user.get('username'))}</p>
                </div>
            </div>
        </body>
        </html>
        """
        body_text = f"""
        Test Email from {site_name}

        This is a test email from {site_name}.

        If you received this email, your email configuration is working correctly!

        Sent by: {current_user.get('full_name', current_user.get('username'))}
        """

        success = EmailService.send_email(
            to=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )

        if success:
            logger.info(f"Test email sent to {to_email} by user {current_user['id']}")
            return (
                jsonify({"message": f"Test email sent successfully to {to_email}"}),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to send test email. Check server logs for details."
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return jsonify({"error": f"Failed to send test email: {str(e)}"}), 500


@admin_settings_v1_bp.route("/site", methods=["GET"])
@auth_required
@admin_required
def get_site_settings():
    """
    Get site configuration settings.

    Returns site settings including:
    - site_url: Base URL for the application
    - site_name: Application name
    """
    try:
        site_config = {
            "site_url": SystemSettingsService.get_setting("site_url", Config.SITE_URL),
            "site_name": SystemSettingsService.get_setting(
                "site_name", Config.APP_NAME
            ),
        }

        return jsonify({"site": site_config}), 200

    except Exception as e:
        logger.error(f"Failed to get site settings: {str(e)}")
        return jsonify({"error": "Failed to retrieve site settings"}), 500


@admin_settings_v1_bp.route("/site", methods=["PUT"])
@auth_required
@admin_required
def update_site_settings():
    """
    Update site configuration settings.

    Expects JSON body with optional fields:
    - site_url: str - Base URL for the application
    - site_name: str - Application name
    """
    try:
        current_user = get_current_user()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract fields
        site_url = data.get("site_url")
        site_name = data.get("site_name")

        # Validate and update site_url
        if site_url is not None:
            if not isinstance(site_url, str) or not site_url.strip():
                return jsonify({"error": "site_url must be a non-empty string"}), 400
            # Basic URL validation
            if not site_url.startswith(("http://", "https://")):
                return (
                    jsonify({"error": "site_url must start with http:// or https://"}),
                    400,
                )
            SystemSettingsService.set_setting(
                "site_url", site_url.rstrip("/"), current_user["id"]
            )

        # Validate and update site_name
        if site_name is not None:
            if not isinstance(site_name, str) or not site_name.strip():
                return jsonify({"error": "site_name must be a non-empty string"}), 400
            SystemSettingsService.set_setting(
                "site_name", site_name, current_user["id"]
            )

        # Return updated config
        site_config = {
            "site_url": SystemSettingsService.get_setting("site_url", Config.SITE_URL),
            "site_name": SystemSettingsService.get_setting(
                "site_name", Config.APP_NAME
            ),
        }

        logger.info(f"Site settings updated by user {current_user['id']}")

        return (
            jsonify(
                {"message": "Site settings updated successfully", "site": site_config}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Failed to update site settings: {str(e)}")
        return jsonify({"error": "Failed to update site settings"}), 500
