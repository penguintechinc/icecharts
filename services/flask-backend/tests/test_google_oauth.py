"""Comprehensive tests for Google OAuth2 authentication handler.

Tests cover the complete OAuth2 flow including authorization URL generation,
token exchange, user info retrieval, and user creation/linking.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.oauth.google_oauth import GoogleOAuthHandler, GoogleUserInfo


class TestGoogleUserInfo:
    """Test GoogleUserInfo dataclass."""

    def test_google_user_info_creation(self):
        """Test GoogleUserInfo creation with all fields."""
        user_info = GoogleUserInfo(
            id="123456",
            email="user@example.com",
            name="Test User",
            picture="https://example.com/pic.jpg",
            verified_email=True,
        )
        assert user_info.id == "123456"
        assert user_info.email == "user@example.com"
        assert user_info.name == "Test User"
        assert user_info.picture == "https://example.com/pic.jpg"
        assert user_info.verified_email is True

    def test_google_user_info_optional_picture(self):
        """Test GoogleUserInfo with optional picture field."""
        user_info = GoogleUserInfo(
            id="123456",
            email="user@example.com",
            name="Test User",
            picture=None,
            verified_email=True,
        )
        assert user_info.picture is None


class TestGetGoogleAuthUrl:
    """Test Google OAuth authorization URL generation."""

    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_build_auth_url_contains_required_params(self):
        """Test that auth URL contains all required OAuth2 parameters."""
        state = "test-state-token"
        auth_url = GoogleOAuthHandler.get_google_auth_url(state)

        assert isinstance(auth_url, str)
        assert "client_id=test-client-id" in auth_url
        assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in auth_url
        assert "response_type=code" in auth_url
        assert "scope=openid+email+profile" in auth_url

    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_build_auth_url_state_parameter(self):
        """Test that auth URL includes state parameter for CSRF protection."""
        state = "csrf-protection-token-xyz"
        auth_url = GoogleOAuthHandler.get_google_auth_url(state)

        assert "state=csrf-protection-token-xyz" in auth_url

    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_build_auth_url_contains_scope(self):
        """Test that auth URL requests openid, email, and profile scopes."""
        state = "test-state"
        auth_url = GoogleOAuthHandler.get_google_auth_url(state)

        assert "openid" in auth_url
        assert "email" in auth_url
        assert "profile" in auth_url

    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_build_auth_url_offline_access(self):
        """Test that auth URL requests offline access for refresh tokens."""
        state = "test-state"
        auth_url = GoogleOAuthHandler.get_google_auth_url(state)

        assert "access_type=offline" in auth_url

    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_build_auth_url_consent_prompt(self):
        """Test that auth URL includes consent prompt."""
        state = "test-state"
        auth_url = GoogleOAuthHandler.get_google_auth_url(state)

        assert "prompt=consent" in auth_url


class TestExchangeCodeForToken:
    """Test Google OAuth token exchange."""

    @patch('app.oauth.google_oauth.requests.post')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_exchange_code_for_token_success(self, mock_post):
        """Test successful token exchange with valid authorization code."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "ya29.a0AfH6SMBx...",
            "expires_in": 3599,
            "refresh_token": "1//0gX...",
            "scope": "openid email profile",
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        access_token, token_data = GoogleOAuthHandler.handle_google_callback("auth-code-123")

        assert access_token == "ya29.a0AfH6SMBx..."
        assert token_data["access_token"] == "ya29.a0AfH6SMBx..."
        assert "refresh_token" in token_data
        mock_post.assert_called_once()

    @patch('app.oauth.google_oauth.requests.post')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_exchange_code_includes_client_credentials(self, mock_post):
        """Test token exchange includes client credentials."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "token"}
        mock_post.return_value = mock_response

        GoogleOAuthHandler.handle_google_callback("auth-code")

        # Verify the request included required parameters
        call_args = mock_post.call_args
        payload = call_args[1]["data"]
        assert payload["client_id"] == "test-client-id"
        assert payload["client_secret"] == "test-secret"
        assert payload["code"] == "auth-code"
        assert payload["grant_type"] == "authorization_code"

    @patch('app.oauth.google_oauth.requests.post')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_exchange_code_missing_access_token_raises(self, mock_post):
        """Test token exchange without access_token in response raises ValueError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "expires_in": 3599,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="No access token"):
            GoogleOAuthHandler.handle_google_callback("auth-code")

    @patch('app.oauth.google_oauth.requests.post')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_exchange_code_http_error_raises(self, mock_post):
        """Test token exchange with HTTP error raises ValueError."""
        mock_post.side_effect = requests.RequestException("Connection timeout")

        with pytest.raises(ValueError, match="Token exchange failed"):
            GoogleOAuthHandler.handle_google_callback("invalid-code")

    @patch('app.oauth.google_oauth.requests.post')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_exchange_code_invalid_code_raises(self, mock_post):
        """Test token exchange with invalid code raises error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response

        with pytest.raises(ValueError, match="Token exchange failed"):
            GoogleOAuthHandler.handle_google_callback("invalid-code")


class TestGetGoogleUserInfo:
    """Test Google OAuth user info retrieval."""

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_success(self, mock_get):
        """Test successful user info retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123456789",
            "email": "user@example.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg",
            "verified_email": True,
        }
        mock_get.return_value = mock_response

        user_info = GoogleOAuthHandler.get_google_user_info("test-access-token")

        assert isinstance(user_info, GoogleUserInfo)
        assert user_info.id == "123456789"
        assert user_info.email == "user@example.com"
        assert user_info.name == "John Doe"
        assert user_info.verified_email is True
        mock_get.assert_called_once()

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_includes_bearer_token(self, mock_get):
        """Test user info request includes Bearer token in Authorization header."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "email": "user@example.com",
            "name": "User",
            "picture": None,
            "verified_email": True,
        }
        mock_get.return_value = mock_response

        GoogleOAuthHandler.get_google_user_info("my-access-token")

        call_args = mock_get.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer my-access-token"

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_email_lowercased(self, mock_get):
        """Test that email is lowercased in user info."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "email": "User@Example.COM",
            "name": "User",
            "picture": None,
            "verified_email": True,
        }
        mock_get.return_value = mock_response

        user_info = GoogleOAuthHandler.get_google_user_info("token")

        assert user_info.email == "user@example.com"

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_unverified_email(self, mock_get):
        """Test user info with unverified email."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "email": "user@example.com",
            "name": "User",
            "picture": None,
            "verified_email": False,
        }
        mock_get.return_value = mock_response

        user_info = GoogleOAuthHandler.get_google_user_info("token")

        assert user_info.verified_email is False

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_missing_optional_fields(self, mock_get):
        """Test user info handles missing optional fields gracefully."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "email": "user@example.com",
            "verified_email": True,
        }
        mock_get.return_value = mock_response

        user_info = GoogleOAuthHandler.get_google_user_info("token")

        assert user_info.name == ""
        assert user_info.picture is None

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_http_error_raises(self, mock_get):
        """Test user info retrieval with HTTP error raises ValueError."""
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ValueError, match="Failed to fetch user info"):
            GoogleOAuthHandler.get_google_user_info("invalid-token")

    @patch('app.oauth.google_oauth.requests.get')
    def test_get_user_info_unauthorized_raises(self, mock_get):
        """Test user info retrieval with 401 Unauthorized raises ValueError."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to fetch user info"):
            GoogleOAuthHandler.get_google_user_info("expired-token")


class TestCreateOrLinkUser:
    """Test user creation and linking during OAuth."""

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_new_user(self, mock_hash, mock_get_user, mock_create):
        """Test creating a new user from Google OAuth."""
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"
        mock_create.return_value = {
            "id": 1,
            "email": "newuser@example.com",
            "full_name": "New User",
            "role": "viewer",
            "google_id": "123456",
        }

        google_user = GoogleUserInfo(
            id="123456",
            email="newuser@example.com",
            name="New User",
            picture=None,
            verified_email=True,
        )

        user, is_new = GoogleOAuthHandler.create_or_link_user(google_user)

        assert is_new is True
        assert user["email"] == "newuser@example.com"
        assert user["google_id"] == "123456"
        mock_create.assert_called_once()

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_existing_user(self, mock_hash, mock_get_user, mock_create):
        """Test linking Google OAuth to existing user."""
        existing_user = {
            "id": 2,
            "email": "existing@example.com",
            "full_name": "Existing User",
            "role": "viewer",
        }
        mock_get_user.return_value = existing_user

        google_user = GoogleUserInfo(
            id="google-123",
            email="existing@example.com",
            name="Existing User",
            picture=None,
            verified_email=True,
        )

        with patch('app.oauth.google_oauth.update_user') as mock_update:
            user, is_new = GoogleOAuthHandler.create_or_link_user(google_user)

            assert is_new is False
            assert user["id"] == 2
            mock_update.assert_called_once_with(2, google_id="google-123")

    @patch('app.oauth.google_oauth.get_user_by_email')
    def test_create_or_link_user_no_email_raises(self, mock_get_user):
        """Test creating user without email raises ValueError."""
        mock_get_user.return_value = None

        google_user = GoogleUserInfo(
            id="123456",
            email="",
            name="No Email User",
            picture=None,
            verified_email=False,
        )

        with pytest.raises(ValueError, match="Google user email is required"):
            GoogleOAuthHandler.create_or_link_user(google_user)

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_default_role_viewer(self, mock_hash, mock_get_user, mock_create):
        """Test new OAuth users receive 'viewer' role by default."""
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"
        mock_create.return_value = {
            "id": 1,
            "email": "user@example.com",
            "full_name": "User",
            "role": "viewer",
        }

        google_user = GoogleUserInfo(
            id="123",
            email="user@example.com",
            name="User",
            picture=None,
            verified_email=True,
        )

        GoogleOAuthHandler.create_or_link_user(google_user)

        call_args = mock_create.call_args
        assert call_args[1]["role"] == "viewer"

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_includes_google_id(self, mock_hash, mock_get_user, mock_create):
        """Test new user creation includes Google ID."""
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"
        mock_create.return_value = {"id": 1, "google_id": "goog-123"}

        google_user = GoogleUserInfo(
            id="goog-123",
            email="user@example.com",
            name="User",
            picture=None,
            verified_email=True,
        )

        GoogleOAuthHandler.create_or_link_user(google_user)

        call_args = mock_create.call_args
        assert call_args[1]["google_id"] == "goog-123"

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_includes_oauth_provider(self, mock_hash, mock_get_user, mock_create):
        """Test new user creation marks oauth_provider as 'google'."""
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"
        mock_create.return_value = {"id": 1, "oauth_provider": "google"}

        google_user = GoogleUserInfo(
            id="123",
            email="user@example.com",
            name="User",
            picture=None,
            verified_email=True,
        )

        GoogleOAuthHandler.create_or_link_user(google_user)

        call_args = mock_create.call_args
        assert call_args[1]["oauth_provider"] == "google"

    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    def test_create_or_link_user_creation_failure_raises(self, mock_hash, mock_get_user, mock_create):
        """Test user creation failure raises ValueError."""
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_password"
        mock_create.side_effect = Exception("Database error")

        google_user = GoogleUserInfo(
            id="123",
            email="user@example.com",
            name="User",
            picture=None,
            verified_email=True,
        )

        with pytest.raises(ValueError, match="Failed to create user"):
            GoogleOAuthHandler.create_or_link_user(google_user)


class TestGoogleOAuthEndToEnd:
    """End-to-end OAuth flow tests."""

    @patch('app.oauth.google_oauth.requests.post')
    @patch('app.oauth.google_oauth.requests.get')
    @patch('app.oauth.google_oauth.create_user')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.hash_password')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_full_oauth_flow_new_user(self, mock_hash, mock_get_user, mock_create,
                                      mock_userinfo, mock_token):
        """Test complete OAuth flow from code to new user creation."""
        # Mock token exchange
        token_response = MagicMock()
        token_response.json.return_value = {
            "access_token": "ya29.access",
            "refresh_token": "refresh",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_token.return_value = token_response

        # Mock user info
        userinfo_response = MagicMock()
        userinfo_response.json.return_value = {
            "id": "google-user-id",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/photo.jpg",
            "verified_email": True,
        }
        mock_userinfo.return_value = userinfo_response

        # Mock user creation
        mock_get_user.return_value = None
        mock_hash.return_value = "hashed_pwd"
        mock_create.return_value = {
            "id": 1,
            "email": "newuser@example.com",
            "google_id": "google-user-id",
        }

        # Execute flow
        access_token, token_data = GoogleOAuthHandler.handle_google_callback("auth-code")
        user_info = GoogleOAuthHandler.get_google_user_info(access_token)
        user, is_new = GoogleOAuthHandler.create_or_link_user(user_info)

        # Verify results
        assert access_token == "ya29.access"
        assert user_info.email == "newuser@example.com"
        assert is_new is True
        assert user["id"] == 1

    @patch('app.oauth.google_oauth.requests.post')
    @patch('app.oauth.google_oauth.requests.get')
    @patch('app.oauth.google_oauth.get_user_by_email')
    @patch('app.oauth.google_oauth.update_user')
    @patch.dict(os.environ, {
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-secret",
        "GOOGLE_REDIRECT_URI": "https://example.com/callback",
    })
    def test_full_oauth_flow_existing_user(self, mock_update, mock_get_user,
                                           mock_userinfo, mock_token):
        """Test complete OAuth flow linking to existing user."""
        # Mock token exchange
        token_response = MagicMock()
        token_response.json.return_value = {"access_token": "ya29.access", "expires_in": 3600}
        mock_token.return_value = token_response

        # Mock user info
        userinfo_response = MagicMock()
        userinfo_response.json.return_value = {
            "id": "google-id",
            "email": "existing@example.com",
            "name": "Existing User",
            "picture": None,
            "verified_email": True,
        }
        mock_userinfo.return_value = userinfo_response

        # Mock existing user
        existing = {
            "id": 5,
            "email": "existing@example.com",
        }
        mock_get_user.return_value = existing

        # Execute flow
        access_token, _ = GoogleOAuthHandler.handle_google_callback("auth-code")
        user_info = GoogleOAuthHandler.get_google_user_info(access_token)
        user, is_new = GoogleOAuthHandler.create_or_link_user(user_info)

        # Verify results
        assert is_new is False
        assert user["id"] == 5
        mock_update.assert_called_once_with(5, google_id="google-id")


class TestGoogleOAuthConstants:
    """Test OAuth constant URLs."""

    def test_google_auth_url_constant(self):
        """Test Google OAuth authorization URL constant."""
        assert GoogleOAuthHandler.GOOGLE_AUTH_URL == "https://accounts.google.com/o/oauth2/v2/auth"

    def test_google_token_url_constant(self):
        """Test Google OAuth token endpoint URL constant."""
        assert GoogleOAuthHandler.GOOGLE_TOKEN_URL == "https://oauth2.googleapis.com/token"

    def test_google_userinfo_url_constant(self):
        """Test Google OAuth user info endpoint URL constant."""
        assert GoogleOAuthHandler.GOOGLE_USERINFO_URL == "https://www.googleapis.com/oauth2/v2/userinfo"
