"""Google OAuth2 Authentication Handler."""

import os
from dataclasses import dataclass
from typing import Optional

import requests
from flask import current_app


@dataclass(slots=True)
class GoogleUserInfo:
    """Google user profile information."""

    id: str
    email: str
    name: str
    picture: Optional[str]
    verified_email: bool


class GoogleOAuthHandler:
    """Handle Google OAuth2 authentication flow."""

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @classmethod
    def get_google_auth_url(cls, state: str) -> str:
        """Generate Google OAuth authorization URL with state parameter.

        Args:
            state: CSRF protection state token

        Returns:
            Google OAuth authorization URL
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        scope = "openid email profile"

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{cls.GOOGLE_AUTH_URL}?{query_string}"

    @classmethod
    def handle_google_callback(cls, code: str) -> tuple[str, dict]:
        """Exchange authorization code for access and ID tokens.

        Args:
            code: Authorization code from Google

        Returns:
            Tuple of (access_token, token_data)

        Raises:
            ValueError: If token exchange fails
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        payload = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        try:
            response = requests.post(cls.GOOGLE_TOKEN_URL, data=payload, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            if "access_token" not in token_data:
                raise ValueError("No access token in response")

            return token_data["access_token"], token_data

        except requests.RequestException as e:
            raise ValueError(f"Token exchange failed: {str(e)}") from e

    @classmethod
    def get_google_user_info(cls, access_token: str) -> GoogleUserInfo:
        """Fetch user profile information from Google using access token.

        Args:
            access_token: Google access token

        Returns:
            GoogleUserInfo with user profile data

        Raises:
            ValueError: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                cls.GOOGLE_USERINFO_URL, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return GoogleUserInfo(
                id=data.get("id"),
                email=data.get("email", "").lower(),
                name=data.get("name", ""),
                picture=data.get("picture"),
                verified_email=data.get("verified_email", False),
            )

        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch user info: {str(e)}") from e

    @classmethod
    def create_or_link_user(cls, google_user: GoogleUserInfo) -> tuple[dict, bool]:
        """Create new user or link Google identity to existing user.

        Handles account linking when email already exists.

        Args:
            google_user: GoogleUserInfo from Google

        Returns:
            Tuple of (user_dict, is_new_user)

        Raises:
            ValueError: If user creation/linking fails
        """
        from ..models import create_user, get_user_by_email, update_user

        # Check if user exists by email
        existing_user = get_user_by_email(google_user.email)

        if existing_user:
            # Link Google identity to existing account
            update_user(
                existing_user["id"],
                google_id=google_user.id,
            )
            return existing_user, False

        # Create new user
        if not google_user.email:
            raise ValueError("Google user email is required")

        # Generate a random password for OAuth users (they won't use it)
        import secrets

        random_password = secrets.token_urlsafe(32)

        from ..auth import hash_password

        password_hash = hash_password(random_password)

        try:
            new_user = create_user(
                email=google_user.email,
                password_hash=password_hash,
                full_name=google_user.name or "",
                role="viewer",  # Default role for OAuth users
                google_id=google_user.id,
                oauth_provider="google",
            )
            return new_user, True

        except Exception as e:
            raise ValueError(f"Failed to create user: {str(e)}") from e
