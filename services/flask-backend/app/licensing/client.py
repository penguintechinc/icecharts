"""PenguinTech License Server Client."""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class LicenseValidationError(Exception):
    """Raised when license validation fails."""

    pass


class FeatureNotAvailableError(Exception):
    """Raised when a required feature is not available."""

    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(f"Feature '{feature}' requires license upgrade")


class PenguinTechLicenseClient:
    """Client for PenguinTech License Server integration."""

    def __init__(
        self,
        license_key: str,
        product: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the license client.

        Args:
            license_key: The license key (format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD)
            product: The product identifier (e.g., 'icecharts')
            base_url: License server URL (default: https://license.penguintech.io)
            timeout: Request timeout in seconds (default: 30)
        """
        self.license_key = license_key
        self.product = product
        self.base_url = base_url or "https://license.penguintech.io"
        self.timeout = timeout
        self.server_id: Optional[str] = None

        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {license_key}",
                "Content-Type": "application/json",
            }
        )

        # Feature cache (5-minute TTL)
        self._feature_cache: Dict[str, bool] = {}
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300  # 5 minutes

        # Grace period tracking
        self._validation_timestamp: Optional[float] = None
        self._grace_period_days = 7

    @classmethod
    def from_env(cls, timeout: int = 30) -> Optional["PenguinTechLicenseClient"]:
        """
        Create client from environment variables.

        Requires LICENSE_KEY and PRODUCT_NAME environment variables.
        Optional LICENSE_SERVER_URL for custom server.

        Args:
            timeout: Request timeout in seconds

        Returns:
            PenguinTechLicenseClient instance or None if env vars missing
        """
        license_key = os.getenv("LICENSE_KEY")
        product = os.getenv("PRODUCT_NAME")
        base_url = os.getenv("LICENSE_SERVER_URL")

        if not license_key or not product:
            logger.warning(
                "LICENSE_KEY and PRODUCT_NAME environment variables required "
                "for license integration"
            )
            return None

        # Validate license key format
        if not cls.is_valid_license_key(license_key):
            logger.warning(f"Invalid license key format: {license_key}")
            return None

        return cls(license_key, product, base_url, timeout)

    def validate(self) -> Dict[str, Any]:
        """
        Validate license and get entitlements.

        Returns:
            Dict containing validation response with features, tier, customer, etc.

        Raises:
            LicenseValidationError: If validation fails
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/validate",
                json={"product": self.product},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("valid"):
                raise LicenseValidationError(
                    f"License validation failed: {data.get('message', 'Unknown error')}"
                )

            # Store server ID for keepalives
            if "metadata" in data and "server_id" in data["metadata"]:
                self.server_id = data["metadata"]["server_id"]

            # Update feature cache
            self._update_feature_cache(data.get("features", []))
            self._validation_timestamp = time.time()

            return data

        except requests.RequestException as e:
            raise LicenseValidationError(f"License validation request failed: {e}")
        except ValueError as e:
            raise LicenseValidationError(f"Invalid response from license server: {e}")

    def check_feature(self, feature: str, use_cache: bool = True) -> bool:
        """
        Check if a specific feature is enabled.

        Args:
            feature: Feature name to check
            use_cache: Whether to use cached results

        Returns:
            True if feature is enabled, False otherwise
        """
        # Check cache first if enabled and valid
        if use_cache and self._is_cache_valid():
            cached_result = self._feature_cache.get(feature)
            if cached_result is not None:
                return cached_result

        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/features",
                json={"product": self.product, "feature": feature},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            features = data.get("features", [])

            if features:
                entitled = features[0].get("entitled", False)
                # Cache the result
                self._feature_cache[feature] = entitled
                self._cache_timestamp = time.time()
                return entitled

            return False

        except requests.RequestException as e:
            logger.error(f"Feature check failed for '{feature}': {e}")
            return False
        except ValueError as e:
            logger.error(f"Invalid response from license server: {e}")
            return False

    def keepalive(self, usage_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send keepalive with optional usage statistics.

        Used to maintain license validity and report usage metrics.

        Args:
            usage_data: Optional usage statistics to send

        Returns:
            Dict containing keepalive response

        Raises:
            LicenseValidationError: If keepalive fails
        """
        if not self.server_id:
            # Validate first to get server ID
            validation = self.validate()
            if not validation.get("valid"):
                raise LicenseValidationError("Failed to validate license for keepalive")

        payload = {
            "product": self.product,
            "server_id": self.server_id,
        }

        if usage_data:
            payload.update(usage_data)

        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/keepalive",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            raise LicenseValidationError(f"Keepalive request failed: {e}")
        except ValueError as e:
            raise LicenseValidationError(f"Invalid response from license server: {e}")

    def get_all_features(self) -> Dict[str, bool]:
        """
        Get all available features from cache or validation.

        Returns:
            Dict mapping feature names to enabled status
        """
        if not self._is_cache_valid():
            try:
                self.validate()
            except LicenseValidationError as e:
                logger.error(f"Failed to refresh feature cache: {e}")

        return self._feature_cache.copy()

    def is_in_grace_period(self) -> bool:
        """
        Check if license is still in grace period.

        Returns:
            True if last successful validation was within grace period
        """
        if self._validation_timestamp is None:
            return False

        elapsed_seconds = time.time() - self._validation_timestamp
        grace_period_seconds = self._grace_period_days * 24 * 3600

        return elapsed_seconds < grace_period_seconds

    def _update_feature_cache(self, features: List[Dict[str, Any]]) -> None:
        """Update the feature cache with new feature data."""
        self._feature_cache = {}
        for feature in features:
            name = feature.get("name")
            entitled = feature.get("entitled", False)
            if name:
                self._feature_cache[name] = entitled

        self._cache_timestamp = time.time()

    def _is_cache_valid(self) -> bool:
        """Check if the feature cache is still valid."""
        if self._cache_timestamp is None:
            return False

        return (time.time() - self._cache_timestamp) < self._cache_ttl

    @staticmethod
    def is_valid_license_key(key: str) -> bool:
        """
        Validate license key format.

        Args:
            key: License key to validate

        Returns:
            True if format is valid (PENG-XXXX-XXXX-XXXX-XXXX-ABCD)
        """
        if not key or len(key) != 29:
            return False

        if not key.startswith("PENG-"):
            return False

        # Count dashes - should be 5 total
        if key.count("-") != 5:
            return False

        # Validate segment lengths
        segments = key.split("-")
        if len(segments) != 6:
            return False

        # Validate format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD
        expected_lengths = [4, 4, 4, 4, 4, 4]  # PENG + 5 segments
        for i, segment in enumerate(segments):
            if i == 0:  # PENG prefix
                if segment != "PENG":
                    return False
            else:
                if len(segment) != expected_lengths[i]:
                    return False

        return True


__all__ = [
    "PenguinTechLicenseClient",
    "LicenseValidationError",
    "FeatureNotAvailableError",
]
