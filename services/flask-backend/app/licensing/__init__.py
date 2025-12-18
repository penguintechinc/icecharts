"""PenguinTech License Server Integration."""

import logging
import os
import threading
from typing import Optional, Dict, Any

from .client import PenguinTechLicenseClient, LicenseValidationError


logger = logging.getLogger(__name__)


# Global license client instance
_license_client: Optional[PenguinTechLicenseClient] = None
_keepalive_thread: Optional[threading.Thread] = None
_keepalive_stop_event: Optional[threading.Event] = None


def _get_license_key_from_db() -> Optional[str]:
    """Get license key from database settings if available."""
    try:
        # Import here to avoid circular imports
        from app.services.system_settings_service import SystemSettingsService
        key = SystemSettingsService.get_setting("license_key")
        if key and isinstance(key, str) and key.strip():
            return key.strip()
    except Exception as e:
        logger.debug(f"Could not get license key from database: {e}")
    return None


def initialize_licensing() -> bool:
    """
    Initialize licensing system from database or environment variables.

    Validates license on startup and starts keepalive background thread.
    Priority: Database setting > Environment variable

    Returns:
        True if licensing initialized successfully, False if license key not set
    """
    global _license_client, _keepalive_thread, _keepalive_stop_event

    # Stop any existing keepalive thread
    if _keepalive_stop_event:
        _keepalive_stop_event.set()

    # Try database first, then environment variable
    license_key = _get_license_key_from_db()
    product = os.getenv("PRODUCT_NAME", "icecharts")
    base_url = os.getenv("LICENSE_SERVER_URL")

    if not license_key:
        # Fall back to environment variable
        license_key = os.getenv("LICENSE_KEY")

    if not license_key:
        logger.warning("License key not configured - licensing disabled")
        _license_client = None
        return False

    # Validate key format
    if not PenguinTechLicenseClient.is_valid_license_key(license_key):
        logger.warning(f"Invalid license key format - licensing disabled")
        _license_client = None
        return False

    # Create client
    _license_client = PenguinTechLicenseClient(
        license_key=license_key,
        product=product,
        base_url=base_url,
    )

    try:
        # Validate license on startup
        validation = _license_client.validate()
        logger.info(
            f"License valid for {validation.get('customer', 'Unknown')} "
            f"({validation.get('tier', 'Unknown')} tier)"
        )

        # Log available features
        for feature in validation.get("features", []):
            if feature.get("entitled"):
                logger.info(f"Feature enabled: {feature.get('name')}")

        # Start keepalive background thread
        _keepalive_stop_event = threading.Event()
        _keepalive_thread = threading.Thread(
            target=_run_keepalive_loop,
            daemon=True,
            name="LicenseKeepaliveThread"
        )
        _keepalive_thread.start()
        logger.debug("License keepalive thread started")

        return True

    except LicenseValidationError as e:
        logger.error(f"License validation failed: {e}")
        return False


def reinitialize_licensing() -> bool:
    """
    Re-initialize the licensing system with updated configuration.

    Call this after updating the license key in the database to apply changes
    without restarting the server.

    Returns:
        True if licensing re-initialized successfully, False otherwise
    """
    global _keepalive_stop_event

    logger.info("Re-initializing licensing system...")

    # Signal the keepalive thread to stop
    if _keepalive_stop_event:
        _keepalive_stop_event.set()

    # Re-initialize
    return initialize_licensing()


def get_client() -> Optional[PenguinTechLicenseClient]:
    """Get the global license client instance."""
    global _license_client
    return _license_client


def check_feature(feature_name: str) -> bool:
    """
    Check if a specific feature is enabled.

    Args:
        feature_name: Name of the feature to check

    Returns:
        True if feature is available, False otherwise
    """
    client = get_client()
    if client is None:
        return False
    return client.check_feature(feature_name)


def get_all_features() -> Dict[str, bool]:
    """
    Get all available features.

    Returns:
        Dict mapping feature names to availability status
    """
    client = get_client()
    if client is None:
        return {}
    return client.get_all_features()


def _run_keepalive_loop() -> None:
    """Run keepalive loop in background thread."""
    import time

    global _keepalive_stop_event

    client = get_client()
    if client is None:
        return

    # Send keepalive every 5 minutes
    keepalive_interval = 300

    while True:
        # Check if we should stop
        if _keepalive_stop_event and _keepalive_stop_event.is_set():
            logger.debug("License keepalive thread stopping")
            return

        try:
            # Use wait with timeout instead of sleep for responsive shutdown
            if _keepalive_stop_event:
                stopped = _keepalive_stop_event.wait(timeout=keepalive_interval)
                if stopped:
                    logger.debug("License keepalive thread stopping")
                    return
            else:
                time.sleep(keepalive_interval)

            # Check if client still valid
            client = get_client()
            if client is None:
                logger.debug("License client no longer available, stopping keepalive")
                return

            client.keepalive()
            logger.debug("License keepalive sent successfully")
        except LicenseValidationError as e:
            logger.error(f"License keepalive failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in keepalive loop: {e}")


__all__ = [
    "initialize_licensing",
    "reinitialize_licensing",
    "get_client",
    "check_feature",
    "get_all_features",
    "LicenseValidationError",
]
