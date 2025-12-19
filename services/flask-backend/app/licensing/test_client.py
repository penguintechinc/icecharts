"""Unit tests for PenguinTech License Server client."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from .client import (
    FeatureNotAvailableError,
    LicenseValidationError,
    PenguinTechLicenseClient,
)


class TestLicenseKeyValidation(unittest.TestCase):
    """Test license key format validation."""

    def test_valid_license_key_format(self):
        """Test that valid license keys pass validation."""
        valid_keys = [
            "PENG-1234-5678-9012-3456-ABCD",
            "PENG-AAAA-BBBB-CCCC-DDDD-EEEE",
            "PENG-0000-0000-0000-0000-0000",
        ]
        for key in valid_keys:
            self.assertTrue(
                PenguinTechLicenseClient.is_valid_license_key(key),
                f"Expected {key} to be valid",
            )

    def test_invalid_license_key_format(self):
        """Test that invalid license keys fail validation."""
        invalid_keys = [
            "",  # Empty
            "PENG",  # Too short
            "PENG-1234-5678-9012-3456",  # Missing segment
            "PENG-1234-5678-9012-3456-ABCD-EXTRA",  # Too long
            "ACME-1234-5678-9012-3456-ABCD",  # Wrong prefix
            "peng-1234-5678-9012-3456-ABCD",  # Lowercase prefix
            "PENG1234567890123456789012345",  # No dashes
        ]
        for key in invalid_keys:
            self.assertFalse(
                PenguinTechLicenseClient.is_valid_license_key(key),
                f"Expected {key} to be invalid",
            )

    def test_none_license_key(self):
        """Test that None license key is invalid."""
        self.assertFalse(PenguinTechLicenseClient.is_valid_license_key(None))


class TestClientInitialization(unittest.TestCase):
    """Test client initialization."""

    def test_client_with_explicit_parameters(self):
        """Test creating client with explicit parameters."""
        client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD",
            product="test_product",
            base_url="https://custom.license.server",
            timeout=60,
        )

        self.assertEqual(client.license_key, "PENG-1234-5678-9012-3456-ABCD")
        self.assertEqual(client.product, "test_product")
        self.assertEqual(client.base_url, "https://custom.license.server")
        self.assertEqual(client.timeout, 60)

    def test_client_with_default_server_url(self):
        """Test that default server URL is used when not specified."""
        client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )

        self.assertEqual(client.base_url, "https://license.penguintech.io")

    @patch.dict(
        "os.environ",
        {
            "LICENSE_KEY": "PENG-1234-5678-9012-3456-ABCD",
            "PRODUCT_NAME": "test_product",
        },
    )
    def test_client_from_env_valid(self):
        """Test creating client from environment variables."""
        client = PenguinTechLicenseClient.from_env()

        self.assertIsNotNone(client)
        self.assertEqual(client.license_key, "PENG-1234-5678-9012-3456-ABCD")
        self.assertEqual(client.product, "test_product")

    @patch.dict("os.environ", {}, clear=True)
    def test_client_from_env_missing_key(self):
        """Test that client returns None when license key missing."""
        client = PenguinTechLicenseClient.from_env()
        self.assertIsNone(client)

    @patch.dict("os.environ", {"LICENSE_KEY": "INVALID"}, clear=True)
    def test_client_from_env_invalid_key_format(self):
        """Test that client returns None with invalid key format."""
        client = PenguinTechLicenseClient.from_env()
        self.assertIsNone(client)


class TestLicenseValidation(unittest.TestCase):
    """Test license validation."""

    def setUp(self):
        """Set up test client."""
        self.client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )

    def test_validate_success(self):
        """Test successful license validation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "valid": True,
            "customer": "Test Corp",
            "tier": "professional",
            "features": [
                {"name": "saml_sso", "entitled": True},
                {"name": "oidc_sso", "entitled": False},
            ],
            "metadata": {"server_id": "test_server_id"},
        }
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.validate()

            self.assertTrue(result["valid"])
            self.assertEqual(result["customer"], "Test Corp")
            self.assertEqual(self.client.server_id, "test_server_id")
            self.assertIn("saml_sso", self.client._feature_cache)
            self.assertTrue(self.client._feature_cache["saml_sso"])

    def test_validate_failure(self):
        """Test validation failure."""
        mock_response = Mock()
        mock_response.json.return_value = {"valid": False, "message": "License expired"}
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            with self.assertRaises(LicenseValidationError):
                self.client.validate()

    def test_validate_request_failure(self):
        """Test validation with request failure."""
        with patch.object(self.client.session, "post") as mock_post:
            mock_post.side_effect = Exception("Connection error")

            with self.assertRaises(LicenseValidationError):
                self.client.validate()

    def test_validate_invalid_response(self):
        """Test validation with invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            with self.assertRaises(LicenseValidationError):
                self.client.validate()


class TestFeatureChecking(unittest.TestCase):
    """Test feature checking."""

    def setUp(self):
        """Set up test client."""
        self.client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )

    def test_check_feature_enabled(self):
        """Test checking an enabled feature."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [{"name": "saml_sso", "entitled": True}]
        }
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.check_feature("saml_sso")
            self.assertTrue(result)

    def test_check_feature_disabled(self):
        """Test checking a disabled feature."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [{"name": "oidc_sso", "entitled": False}]
        }
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.check_feature("oidc_sso")
            self.assertFalse(result)

    def test_check_feature_not_found(self):
        """Test checking a non-existent feature."""
        mock_response = Mock()
        mock_response.json.return_value = {"features": []}
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.check_feature("nonexistent_feature")
            self.assertFalse(result)

    def test_check_feature_request_failure(self):
        """Test feature check with request failure."""
        with patch.object(self.client.session, "post") as mock_post:
            mock_post.side_effect = Exception("Connection error")

            result = self.client.check_feature("saml_sso")
            self.assertFalse(result)

    def test_check_feature_uses_cache(self):
        """Test that feature check uses cache when valid."""
        # Pre-populate cache
        self.client._feature_cache["saml_sso"] = True
        self.client._cache_timestamp = __import__("time").time()

        # Should return cached value without making request
        result = self.client.check_feature("saml_sso", use_cache=True)
        self.assertTrue(result)

    def test_check_feature_bypasses_cache(self):
        """Test that use_cache=False bypasses cache."""
        # Pre-populate cache
        self.client._feature_cache["saml_sso"] = False
        self.client._cache_timestamp = __import__("time").time()

        mock_response = Mock()
        mock_response.json.return_value = {
            "features": [{"name": "saml_sso", "entitled": True}]
        }
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.check_feature("saml_sso", use_cache=False)
            self.assertTrue(result)


class TestKeepalive(unittest.TestCase):
    """Test keepalive functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )
        self.client.server_id = "test_server_id"

    def test_keepalive_success(self):
        """Test successful keepalive."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post", return_value=mock_response):
            result = self.client.keepalive()
            self.assertEqual(result["status"], "ok")

    def test_keepalive_with_usage_data(self):
        """Test keepalive with usage statistics."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()

        with patch.object(
            self.client.session, "post", return_value=mock_response
        ) as mock_post:
            usage_data = {"active_users": 42}
            self.client.keepalive(usage_data)

            # Verify usage data was included in request
            call_args = mock_post.call_args
            json_data = call_args[1]["json"]
            self.assertEqual(json_data["active_users"], 42)

    def test_keepalive_without_server_id(self):
        """Test keepalive validates first if no server_id."""
        self.client.server_id = None

        mock_validate_response = Mock()
        mock_validate_response.json.return_value = {
            "valid": True,
            "metadata": {"server_id": "new_server_id"},
        }
        mock_validate_response.raise_for_status = Mock()

        mock_keepalive_response = Mock()
        mock_keepalive_response.json.return_value = {"status": "ok"}
        mock_keepalive_response.raise_for_status = Mock()

        with patch.object(self.client.session, "post") as mock_post:
            mock_post.side_effect = [mock_validate_response, mock_keepalive_response]
            result = self.client.keepalive()
            self.assertEqual(result["status"], "ok")
            self.assertEqual(self.client.server_id, "new_server_id")

    def test_keepalive_request_failure(self):
        """Test keepalive with request failure."""
        with patch.object(self.client.session, "post") as mock_post:
            mock_post.side_effect = Exception("Connection error")

            with self.assertRaises(LicenseValidationError):
                self.client.keepalive()


class TestGracePeriod(unittest.TestCase):
    """Test grace period functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )

    def test_in_grace_period_recently_validated(self):
        """Test that recently validated license is in grace period."""
        import time

        self.client._validation_timestamp = time.time()
        self.assertTrue(self.client.is_in_grace_period())

    def test_outside_grace_period(self):
        """Test that old validation is outside grace period."""
        import time

        # Set validation timestamp to 8 days ago
        self.client._validation_timestamp = time.time() - (8 * 24 * 3600)
        self.assertFalse(self.client.is_in_grace_period())

    def test_no_validation_not_in_grace_period(self):
        """Test that no validation means not in grace period."""
        self.client._validation_timestamp = None
        self.assertFalse(self.client.is_in_grace_period())


class TestCaching(unittest.TestCase):
    """Test feature cache functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = PenguinTechLicenseClient(
            license_key="PENG-1234-5678-9012-3456-ABCD", product="test_product"
        )

    def test_cache_validity(self):
        """Test cache validity checking."""
        import time

        # Cache is invalid when timestamp is None
        self.assertFalse(self.client._is_cache_valid())

        # Cache is valid when timestamp is recent
        self.client._cache_timestamp = time.time()
        self.assertTrue(self.client._is_cache_valid())

        # Cache is invalid when older than TTL
        self.client._cache_timestamp = time.time() - (self.client._cache_ttl + 1)
        self.assertFalse(self.client._is_cache_valid())

    def test_update_feature_cache(self):
        """Test feature cache update."""
        features = [
            {"name": "saml_sso", "entitled": True},
            {"name": "oidc_sso", "entitled": False},
            {"name": "advanced_analytics", "entitled": True},
        ]

        self.client._update_feature_cache(features)

        self.assertEqual(len(self.client._feature_cache), 3)
        self.assertTrue(self.client._feature_cache["saml_sso"])
        self.assertFalse(self.client._feature_cache["oidc_sso"])
        self.assertTrue(self.client._feature_cache["advanced_analytics"])

    def test_get_all_features(self):
        """Test getting all features from cache."""
        # Pre-populate cache
        self.client._feature_cache = {
            "feature1": True,
            "feature2": False,
            "feature3": True,
        }
        self.client._cache_timestamp = __import__("time").time()

        features = self.client.get_all_features()
        self.assertEqual(len(features), 3)
        self.assertTrue(features["feature1"])
        self.assertFalse(features["feature2"])


class TestExceptionHandling(unittest.TestCase):
    """Test exception classes."""

    def test_license_validation_error(self):
        """Test LicenseValidationError."""
        with self.assertRaises(LicenseValidationError):
            raise LicenseValidationError("Test error")

    def test_feature_not_available_error(self):
        """Test FeatureNotAvailableError."""
        error = FeatureNotAvailableError("saml_sso")
        self.assertEqual(error.feature, "saml_sso")
        self.assertIn("saml_sso", str(error))


if __name__ == "__main__":
    unittest.main()
