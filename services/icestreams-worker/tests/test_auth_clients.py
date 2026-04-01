"""
Unit tests for authentication clients.

Tests OAuth2Client, AWSSTSClient, and OIDCClient with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

from auth import (
    OAuth2Client,
    OAuth2Config,
    AWSSTSClient,
    AWSSTSConfig,
    OIDCClient,
    OIDCConfig,
    CachedToken,
    CachedIDToken,
)

# Check if optional dependencies are available
try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import google.auth
    import google.oauth2.service_account

    HAS_GOOGLE_AUTH = True
except ImportError:
    HAS_GOOGLE_AUTH = False


class TestOAuth2Client:
    """Test OAuth2Client functionality."""

    def test_oauth2_config_creation(self):
        """Test OAuth2Config creation with required fields."""
        config = OAuth2Config(
            client_id="test-client-id",
            client_secret="test-client-secret",
            token_url="https://auth.example.com/token",
            scope="read write",
            timeout=30,
        )
        assert config.client_id == "test-client-id"
        assert config.scope == "read write"

    @patch("auth.oauth2.requests.post")
    def test_get_access_token_success(self, mock_post):
        """Test successful token fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = OAuth2Config(
            client_id="test-client",
            client_secret="test-secret",
            token_url="https://auth.example.com/token",
        )
        client = OAuth2Client(config)

        token = client.get_access_token()
        assert token == "test-token-123"

        # Verify cached token is used on second call
        token2 = client.get_access_token()
        assert token2 == "test-token-123"
        assert mock_post.call_count == 1  # Only called once

    @patch("auth.oauth2.requests.post")
    def test_get_access_token_force_refresh(self, mock_post):
        """Test forced token refresh."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test-token-456",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = OAuth2Config(
            client_id="test-client",
            client_secret="test-secret",
            token_url="https://auth.example.com/token",
        )
        client = OAuth2Client(config)

        token1 = client.get_access_token()
        token2 = client.get_access_token(force_refresh=True)

        assert mock_post.call_count == 2  # Called twice

    def test_get_authorization_header(self):
        """Test authorization header generation."""
        with patch("auth.oauth2.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test-token-789",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            config = OAuth2Config(
                client_id="test-client",
                client_secret="test-secret",
                token_url="https://auth.example.com/token",
            )
            client = OAuth2Client(config)

            header = client.get_authorization_header()
            assert header == {"Authorization": "Bearer test-token-789"}

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        with patch("auth.oauth2.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "test-token-abc",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            config = OAuth2Config(
                client_id="test-client",
                client_secret="test-secret",
                token_url="https://auth.example.com/token",
            )
            client = OAuth2Client(config)

            client.get_access_token()
            assert mock_post.call_count == 1

            client.invalidate_cache()
            client.get_access_token()
            assert mock_post.call_count == 2  # Fetched again after invalidation


class TestCachedToken:
    """Test CachedToken functionality."""

    def test_is_expired_false(self):
        """Test token not expired."""
        token = CachedToken(
            access_token="test-token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not token.is_expired()

    def test_is_expired_true(self):
        """Test token expired."""
        token = CachedToken(
            access_token="test-token",
            token_type="Bearer",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert token.is_expired()

    def test_is_expired_with_buffer(self):
        """Test token expiry with buffer."""
        token = CachedToken(
            access_token="test-token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(seconds=30),
        )
        # Should be expired with 60-second buffer
        assert token.is_expired(buffer_seconds=60)
        # Should not be expired with 10-second buffer
        assert not token.is_expired(buffer_seconds=10)


class TestAWSSTSClient:
    """Test AWSSTSClient functionality."""

    def test_aws_sts_config_creation(self):
        """Test AWSSTSConfig creation."""
        config = AWSSTSConfig(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
            session_duration=3600,
        )
        assert config.access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert config.region == "us-east-1"

    @pytest.mark.skipif(not HAS_BOTO3, reason="boto3 not installed")
    @patch("auth.oauth2.boto3.client")
    def test_get_credentials_with_session_token(self, mock_boto_client):
        """Test credential fetch with session token."""
        mock_sts = Mock()
        mock_sts.get_session_token.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIATESTACCESSKEY",
                "SecretAccessKey": "TestSecretKey",
                "SessionToken": "TestSessionToken",
                "Expiration": datetime.now() + timedelta(hours=1),
            }
        }
        mock_boto_client.return_value = mock_sts

        config = AWSSTSConfig(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
        )
        client = AWSSTSClient(config)

        credentials = client.get_credentials()
        assert credentials["access_key_id"] == "ASIATESTACCESSKEY"
        assert credentials["session_token"] == "TestSessionToken"

    @pytest.mark.skipif(not HAS_BOTO3, reason="boto3 not installed")
    @patch("auth.oauth2.boto3.client")
    def test_get_credentials_with_role_assumption(self, mock_boto_client):
        """Test credential fetch with role assumption."""
        mock_sts = Mock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIATESTACCESSKEY",
                "SecretAccessKey": "TestSecretKey",
                "SessionToken": "TestSessionToken",
                "Expiration": datetime.now() + timedelta(hours=1),
            }
        }
        mock_boto_client.return_value = mock_sts

        config = AWSSTSConfig(
            access_key_id="AKIAIOSFODNN7EXAMPLE",
            secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            region="us-east-1",
            role_arn="arn:aws:iam::123456789012:role/TestRole",
        )
        client = AWSSTSClient(config)

        credentials = client.get_credentials()
        assert credentials["access_key_id"] == "ASIATESTACCESSKEY"


class TestOIDCClient:
    """Test OIDCClient functionality."""

    def test_oidc_config_creation(self):
        """Test OIDCConfig creation."""
        config = OIDCConfig(
            service_account_json="/path/to/service-account.json",
            target_audience="https://example.com",
            timeout=30,
        )
        assert config.service_account_json == "/path/to/service-account.json"
        assert config.target_audience == "https://example.com"

    @pytest.mark.skipif(not HAS_GOOGLE_AUTH, reason="google-auth not installed")
    @patch("google.oauth2.service_account.IDTokenCredentials.from_service_account_file")
    @patch("google.auth.transport.requests.Request")
    def test_get_id_token_success(self, mock_request, mock_from_file):
        """Test successful ID token fetch."""
        mock_credentials = Mock()
        mock_credentials.token = "test-id-token-123"
        mock_credentials.expiry = datetime.now() + timedelta(hours=1)
        mock_credentials.target_audience = "https://example.com"
        mock_credentials.refresh = Mock()
        mock_from_file.return_value = mock_credentials

        config = OIDCConfig(
            service_account_json="/tmp/test-service-account.json",
            target_audience="https://example.com",
        )

        # Create mock service account file
        with patch("builtins.open", create=True):
            client = OIDCClient(config)

        token = client.get_id_token()
        assert token == "test-id-token-123"

    @pytest.mark.skipif(not HAS_GOOGLE_AUTH, reason="google-auth not installed")
    @patch("google.oauth2.service_account.IDTokenCredentials.from_service_account_info")
    def test_create_from_json_string(self, mock_from_info):
        """Test creating client from JSON string."""
        mock_credentials = Mock()
        mock_credentials.token = "test-id-token-456"
        mock_credentials.expiry = datetime.now() + timedelta(hours=1)
        mock_credentials.target_audience = "https://example.com"
        mock_from_info.return_value = mock_credentials

        service_account_json = json.dumps(
            {
                "type": "service_account",
                "project_id": "test-project",
                "private_key_id": "key123",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test-project.iam.gserviceaccount.com",
                "client_id": "123456789",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )

        client = OIDCClient.create_from_json_string(
            service_account_json, target_audience="https://example.com"
        )

        assert client is not None


class TestCachedIDToken:
    """Test CachedIDToken functionality."""

    def test_is_expired_false(self):
        """Test ID token not expired."""
        token = CachedIDToken(
            id_token="test-id-token",
            token_type="Bearer",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not token.is_expired()

    def test_is_expired_true(self):
        """Test ID token expired."""
        token = CachedIDToken(
            id_token="test-id-token",
            token_type="Bearer",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert token.is_expired()
