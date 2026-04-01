"""
OIDC authentication client for Google Cloud Platform.

This module provides thread-safe OIDC authentication with automatic token
refresh and caching for GCP Cloud Run and other GCP services.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock
import json
import logging

try:
    from google.auth import jwt
    from google.auth.transport import requests as google_requests
    from google.oauth2 import service_account

    HAS_GOOGLE_AUTH = True
except ImportError:
    HAS_GOOGLE_AUTH = False

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class OIDCConfig:
    """Configuration for OIDC authentication."""

    service_account_json: str  # Path to service account JSON file
    target_audience: Optional[str] = None  # Target audience for ID token
    timeout: int = 30


@dataclass(slots=True)
class CachedIDToken:
    """Cached OIDC ID token with expiry tracking."""

    id_token: str
    token_type: str
    expires_at: datetime

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired with optional buffer."""
        return datetime.now() >= (self.expires_at - timedelta(seconds=buffer_seconds))


class OIDCClient:
    """
    Thread-safe OIDC client for Google Cloud Platform.

    Supports:
    - Service account JSON key authentication
    - ID token generation for Cloud Run
    - Token caching with automatic refresh
    - Thread-safe token management
    """

    __slots__ = ("_config", "_credentials", "_token_cache", "_lock")

    def __init__(self, config: OIDCConfig):
        """
        Initialize OIDC client.

        Args:
            config: OIDC configuration

        Raises:
            RuntimeError: If google-auth is not available or credentials are invalid
        """
        if not HAS_GOOGLE_AUTH:
            raise RuntimeError(
                "google-auth is required for OIDC authentication. "
                "Install with: pip install google-auth"
            )

        self._config = config
        self._token_cache: Optional[CachedIDToken] = None
        self._lock = Lock()

        # Load service account credentials
        try:
            self._credentials = (
                service_account.IDTokenCredentials.from_service_account_file(
                    self._config.service_account_json,
                    target_audience=self._config.target_audience,
                )
            )
            logger.info(
                "Successfully loaded service account credentials from %s",
                self._config.service_account_json,
            )
        except FileNotFoundError as e:
            logger.error(
                "Service account file not found: %s", self._config.service_account_json
            )
            raise RuntimeError(
                f"Service account file not found: {self._config.service_account_json}"
            ) from e
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Invalid service account JSON: %s", str(e))
            raise RuntimeError(f"Invalid service account JSON: {e}") from e

    def get_id_token(
        self, target_audience: Optional[str] = None, force_refresh: bool = False
    ) -> str:
        """
        Get valid ID token, refreshing if necessary.

        Args:
            target_audience: Override target audience for this request
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            Valid ID token

        Raises:
            RuntimeError: If token acquisition fails
        """
        with self._lock:
            # Check if we need to refresh
            if (
                not force_refresh
                and self._token_cache
                and not self._token_cache.is_expired()
            ):
                # Verify target audience matches if provided
                if target_audience and target_audience != self._config.target_audience:
                    return self._fetch_new_token(target_audience)
                return self._token_cache.id_token

            return self._fetch_new_token(target_audience)

    def _fetch_new_token(self, target_audience: Optional[str] = None) -> str:
        """
        Fetch new ID token from Google.

        Args:
            target_audience: Override target audience

        Returns:
            New ID token

        Raises:
            RuntimeError: If token fetch fails
        """
        try:
            # Update target audience if provided
            audience = target_audience or self._config.target_audience
            if audience and audience != self._credentials.target_audience:
                self._credentials = (
                    service_account.IDTokenCredentials.from_service_account_file(
                        self._config.service_account_json, target_audience=audience
                    )
                )

            # Refresh credentials
            auth_request = google_requests.Request()
            self._credentials.refresh(auth_request)

            # Get the token and expiry
            id_token = self._credentials.token
            expiry = self._credentials.expiry

            if not id_token:
                raise RuntimeError("No ID token returned from credentials refresh")

            # Calculate expiry (default to 1 hour if not provided)
            if expiry:
                expires_at = expiry.replace(tzinfo=None)
            else:
                expires_at = datetime.now() + timedelta(hours=1)

            # Cache token
            self._token_cache = CachedIDToken(
                id_token=id_token, token_type="Bearer", expires_at=expires_at
            )

            logger.info(
                "Successfully fetched ID token for audience %s, expires at %s",
                audience or "default",
                expires_at.isoformat(),
            )

            return id_token

        except Exception as e:
            logger.error("Failed to fetch ID token: %s", str(e))
            raise RuntimeError(f"ID token fetch failed: {e}") from e

    def get_authorization_header(
        self, target_audience: Optional[str] = None, force_refresh: bool = False
    ) -> Dict[str, str]:
        """
        Get Authorization header with valid ID token.

        Args:
            target_audience: Override target audience
            force_refresh: Force token refresh

        Returns:
            Authorization header dict
        """
        token = self.get_id_token(
            target_audience=target_audience, force_refresh=force_refresh
        )
        return {"Authorization": f"Bearer {token}"}

    def verify_token(
        self, token: str, audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify and decode an ID token.

        Args:
            token: ID token to verify
            audience: Expected audience (uses config default if not provided)

        Returns:
            Decoded token payload

        Raises:
            RuntimeError: If token verification fails
        """
        try:
            target_audience = audience or self._config.target_audience
            if not target_audience:
                raise ValueError("Target audience required for token verification")

            # Verify and decode token
            request = google_requests.Request()
            payload = jwt.decode(token, request=request, audience=target_audience)

            logger.debug(
                "Successfully verified ID token for audience %s", target_audience
            )
            return payload

        except Exception as e:
            logger.error("Failed to verify ID token: %s", str(e))
            raise RuntimeError(f"ID token verification failed: {e}") from e

    def invalidate_cache(self) -> None:
        """Invalidate cached token, forcing refresh on next request."""
        with self._lock:
            self._token_cache = None
            logger.debug("OIDC token cache invalidated")

    @staticmethod
    def create_from_json_string(
        json_string: str, target_audience: Optional[str] = None, timeout: int = 30
    ) -> "OIDCClient":
        """
        Create OIDC client from service account JSON string.

        Args:
            json_string: Service account JSON as string
            target_audience: Target audience for ID token
            timeout: Request timeout in seconds

        Returns:
            Configured OIDC client

        Raises:
            RuntimeError: If credentials are invalid
        """
        if not HAS_GOOGLE_AUTH:
            raise RuntimeError(
                "google-auth is required for OIDC authentication. "
                "Install with: pip install google-auth"
            )

        try:
            # Parse and validate JSON
            credentials_info = json.loads(json_string)

            # Create credentials from dict
            credentials = service_account.IDTokenCredentials.from_service_account_info(
                credentials_info, target_audience=target_audience
            )

            # Create a temporary config (we'll override credentials)
            config = OIDCConfig(
                service_account_json="",  # Not used when creating from string
                target_audience=target_audience,
                timeout=timeout,
            )

            client = object.__new__(OIDCClient)
            object.__setattr__(client, "_config", config)
            object.__setattr__(client, "_credentials", credentials)
            object.__setattr__(client, "_token_cache", None)
            object.__setattr__(client, "_lock", Lock())

            logger.info("Successfully created OIDC client from JSON string")
            return client

        except json.JSONDecodeError as e:
            logger.error("Invalid service account JSON string: %s", str(e))
            raise RuntimeError(f"Invalid service account JSON: {e}") from e
        except Exception as e:
            logger.error("Failed to create OIDC client from JSON: %s", str(e))
            raise RuntimeError(f"Failed to create OIDC client: {e}") from e
