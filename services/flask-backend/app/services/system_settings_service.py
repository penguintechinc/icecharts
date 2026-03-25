"""System settings service with in-memory caching for IceCharts."""

import json
import logging
from typing import Any, Optional

from app.models import get_db

logger = logging.getLogger(__name__)


class SystemSettingsService:
    """Service for managing system-wide settings with caching."""

    # In-memory cache for settings
    _cache = {}
    _cache_initialized = False

    @staticmethod
    def _initialize_cache() -> None:
        """Initialize the settings cache from database."""
        if SystemSettingsService._cache_initialized:
            return

        try:
            db = get_db()
            settings = db(db.system_settings).select()

            for setting in settings:
                key = setting.setting_key
                value = setting.setting_value
                setting_type = setting.setting_type

                # Convert value based on type
                if setting_type == "boolean":
                    value = value.lower() in ("true", "1", "yes")
                elif setting_type == "integer":
                    value = int(value)
                elif setting_type == "json":
                    value = json.loads(value)
                # else: keep as string

                SystemSettingsService._cache[key] = value

            SystemSettingsService._cache_initialized = True
            logger.info(
                f"Settings cache initialized with {len(SystemSettingsService._cache)} settings"
            )

        except Exception as e:
            logger.error(f"Failed to initialize settings cache: {str(e)}")
            SystemSettingsService._cache_initialized = (
                True  # Mark as initialized to prevent loops
            )

    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        """
        Get a setting value by key.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        # Initialize cache if needed
        if not SystemSettingsService._cache_initialized:
            SystemSettingsService._initialize_cache()

        # Return from cache
        return SystemSettingsService._cache.get(key, default)

    @staticmethod
    def set_setting(key: str, value: Any, user_id: Optional[int] = None) -> bool:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            user_id: ID of user making the change

        Returns:
            True if successful, False otherwise
        """
        try:
            db = get_db()

            # Determine setting type
            setting_type = "string"
            if isinstance(value, bool):
                setting_type = "boolean"
                value_str = "true" if value else "false"
            elif isinstance(value, int):
                setting_type = "integer"
                value_str = str(value)
            elif isinstance(value, (dict, list)):
                setting_type = "json"
                value_str = json.dumps(value)
            else:
                value_str = str(value)

            # Update or insert setting
            existing = db(db.system_settings.setting_key == key).select().first()

            if existing:
                db(db.system_settings.setting_key == key).update(
                    setting_value=value_str,
                    setting_type=setting_type,
                    updated_by_id=user_id,
                )
            else:
                db.system_settings.insert(
                    setting_key=key,
                    setting_value=value_str,
                    setting_type=setting_type,
                    updated_by_id=user_id,
                )

            db.commit()

            # Update cache
            SystemSettingsService._cache[key] = value

            logger.info(f"Setting '{key}' updated by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to set setting '{key}': {str(e)}")
            db.rollback()
            return False

    @staticmethod
    def get_signup_config() -> dict:
        """
        Get signup configuration.

        Returns:
            Dictionary with signup settings:
            - enabled: bool - Whether signup is enabled
            - mode: str - Signup mode (open, domain_restricted, sso_only, disabled)
            - allowed_domains: list - Allowed email domains (for domain_restricted mode)
            - email_verification_required: bool - Whether email verification is required
        """
        return {
            "enabled": SystemSettingsService.get_setting("signup_enabled", True),
            "mode": SystemSettingsService.get_setting("signup_mode", "open"),
            "allowed_domains": SystemSettingsService.get_setting(
                "signup_allowed_domains", []
            ),
            "email_verification_required": SystemSettingsService.get_setting(
                "email_verification_required", False
            ),
        }

    @staticmethod
    def get_email_config() -> dict:
        """
        Get email configuration.

        Returns:
            Dictionary with email settings:
            - provider: str - Email provider
            - from_email: str - From email address
            - from_name: str - From name
        """
        return {
            "provider": SystemSettingsService.get_setting("email_provider", "sendmail"),
            "from_email": SystemSettingsService.get_setting(
                "email_from", "noreply@icecharts.com"
            ),
            "from_name": SystemSettingsService.get_setting(
                "email_from_name", "IceCharts"
            ),
        }

    @staticmethod
    def update_signup_config(
        enabled: Optional[bool] = None,
        mode: Optional[str] = None,
        allowed_domains: Optional[list] = None,
        email_verification_required: Optional[bool] = None,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Update signup configuration.

        Args:
            enabled: Whether signup is enabled
            mode: Signup mode
            allowed_domains: Allowed email domains
            email_verification_required: Whether email verification is required
            user_id: ID of user making changes

        Returns:
            True if successful, False otherwise
        """
        try:
            if enabled is not None:
                SystemSettingsService.set_setting("signup_enabled", enabled, user_id)

            if mode is not None:
                if mode not in ("open", "domain_restricted", "sso_only", "disabled"):
                    logger.error(f"Invalid signup mode: {mode}")
                    return False
                SystemSettingsService.set_setting("signup_mode", mode, user_id)

            if allowed_domains is not None:
                SystemSettingsService.set_setting(
                    "signup_allowed_domains", allowed_domains, user_id
                )

            if email_verification_required is not None:
                SystemSettingsService.set_setting(
                    "email_verification_required", email_verification_required, user_id
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update signup config: {str(e)}")
            return False

    @staticmethod
    def update_email_config(
        provider: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> bool:
        """
        Update email configuration.

        Args:
            provider: Email provider
            from_email: From email address
            from_name: From name
            user_id: ID of user making changes

        Returns:
            True if successful, False otherwise
        """
        try:
            if provider is not None:
                valid_providers = (
                    "sendmail",
                    "smtp",
                    "sendgrid",
                    "aws_ses",
                    "mailgun",
                    "gmail",
                )
                if provider not in valid_providers:
                    logger.error(f"Invalid email provider: {provider}")
                    return False
                SystemSettingsService.set_setting("email_provider", provider, user_id)

            if from_email is not None:
                SystemSettingsService.set_setting("email_from", from_email, user_id)

            if from_name is not None:
                SystemSettingsService.set_setting("email_from_name", from_name, user_id)

            return True

        except Exception as e:
            logger.error(f"Failed to update email config: {str(e)}")
            return False

    @staticmethod
    def clear_cache() -> None:
        """Clear the settings cache. Used for testing or when settings are updated externally."""
        SystemSettingsService._cache = {}
        SystemSettingsService._cache_initialized = False
        logger.info("Settings cache cleared")

    @staticmethod
    def refresh_cache() -> None:
        """Refresh the settings cache from database."""
        SystemSettingsService.clear_cache()
        SystemSettingsService._initialize_cache()
        logger.info("Settings cache refreshed")
