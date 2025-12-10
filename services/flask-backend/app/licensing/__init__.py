"""PenguinTech License Server Integration."""

import logging
import threading
from typing import Optional, Dict, Any

from .client import PenguinTechLicenseClient, LicenseValidationError


logger = logging.getLogger(__name__)


# Global license client instance
_license_client: Optional[PenguinTechLicenseClient] = None
_keepalive_thread: Optional[threading.Thread] = None


def initialize_licensing() -> bool:
    """
    Initialize licensing system from environment variables.

    Validates license on startup and starts keepalive background thread.

    Returns:
        True if licensing initialized successfully, False if license key not set
    """
    global _license_client, _keepalive_thread

    # Create client from environment variables
    _license_client = PenguinTechLicenseClient.from_env()

    if _license_client is None:
        logger.warning("License key not configured - licensing disabled")
        return False

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

    client = get_client()
    if client is None:
        return

    # Send keepalive every 5 minutes
    keepalive_interval = 300

    while True:
        try:
            time.sleep(keepalive_interval)
            client.keepalive()
            logger.debug("License keepalive sent successfully")
        except LicenseValidationError as e:
            logger.error(f"License keepalive failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in keepalive loop: {e}")


__all__ = [
    "initialize_licensing",
    "get_client",
    "check_feature",
    "get_all_features",
    "LicenseValidationError",
]
