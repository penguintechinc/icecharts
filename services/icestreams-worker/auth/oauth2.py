"""
OAuth2 authentication client for AWS STS and OpenWhisk.

This module provides thread-safe OAuth2 authentication with automatic token
refresh and caching for cloud function integrations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock
import logging

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class OAuth2Config:
    """Configuration for OAuth2 authentication."""
    client_id: str
    client_secret: str
    token_url: str
    scope: Optional[str] = None
    timeout: int = 30


@dataclass(slots=True, frozen=True)
class AWSSTSConfig:
    """Configuration for AWS STS authentication."""
    access_key_id: str
    secret_access_key: str
    region: str
    session_token: Optional[str] = None
    role_arn: Optional[str] = None
    session_duration: int = 3600
    timeout: int = 30


@dataclass(slots=True)
class CachedToken:
    """Cached OAuth2 token with expiry tracking."""
    access_token: str
    token_type: str
    expires_at: datetime
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        """Check if token is expired with optional buffer."""
        return datetime.now() >= (self.expires_at - timedelta(seconds=buffer_seconds))


class OAuth2Client:
    """
    Thread-safe OAuth2 client with token caching and automatic refresh.

    Supports:
    - Client credentials flow
    - Token caching with automatic refresh
    - OpenWhisk OAuth2 authentication
    - Thread-safe token management
    """

    __slots__ = ('_config', '_token_cache', '_lock')

    def __init__(self, config: OAuth2Config):
        """
        Initialize OAuth2 client.

        Args:
            config: OAuth2 configuration
        """
        self._config = config
        self._token_cache: Optional[CachedToken] = None
        self._lock = Lock()

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get valid access token, refreshing if necessary.

        Args:
            force_refresh: Force token refresh even if cached token is valid

        Returns:
            Valid access token

        Raises:
            RuntimeError: If token acquisition fails
        """
        with self._lock:
            if not force_refresh and self._token_cache and not self._token_cache.is_expired():
                return self._token_cache.access_token

            return self._fetch_new_token()

    def _fetch_new_token(self) -> str:
        """
        Fetch new access token using client credentials flow.

        Returns:
            New access token

        Raises:
            RuntimeError: If token fetch fails
        """
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self._config.client_id,
                'client_secret': self._config.client_secret,
            }

            if self._config.scope:
                data['scope'] = self._config.scope

            response = requests.post(
                self._config.token_url,
                data=data,
                timeout=self._config.timeout,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()

            token_data = response.json()

            # Calculate expiry time
            expires_in = token_data.get('expires_in', 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)

            # Cache token
            self._token_cache = CachedToken(
                access_token=token_data['access_token'],
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at,
                refresh_token=token_data.get('refresh_token'),
                scope=token_data.get('scope')
            )

            logger.info(
                "Successfully fetched OAuth2 token, expires at %s",
                expires_at.isoformat()
            )

            return self._token_cache.access_token

        except RequestException as e:
            logger.error("Failed to fetch OAuth2 token: %s", str(e))
            raise RuntimeError(f"OAuth2 token fetch failed: {e}") from e
        except (KeyError, ValueError) as e:
            logger.error("Invalid OAuth2 token response: %s", str(e))
            raise RuntimeError(f"Invalid OAuth2 token response: {e}") from e

    def get_authorization_header(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get Authorization header with valid token.

        Args:
            force_refresh: Force token refresh

        Returns:
            Authorization header dict
        """
        token = self.get_access_token(force_refresh=force_refresh)
        token_type = self._token_cache.token_type if self._token_cache else 'Bearer'
        return {'Authorization': f'{token_type} {token}'}

    def invalidate_cache(self) -> None:
        """Invalidate cached token, forcing refresh on next request."""
        with self._lock:
            self._token_cache = None
            logger.debug("OAuth2 token cache invalidated")


class AWSSTSClient:
    """
    Thread-safe AWS STS client for credential management.

    Supports:
    - Temporary credential fetching
    - Role assumption
    - Credential caching with automatic refresh
    - Thread-safe credential management
    """

    __slots__ = ('_config', '_credentials_cache', '_lock')

    def __init__(self, config: AWSSTSConfig):
        """
        Initialize AWS STS client.

        Args:
            config: AWS STS configuration

        Raises:
            RuntimeError: If boto3 is not available
        """
        if not HAS_BOTO3:
            raise RuntimeError(
                "boto3 is required for AWS STS authentication. "
                "Install with: pip install boto3"
            )

        self._config = config
        self._credentials_cache: Optional[Dict[str, Any]] = None
        self._lock = Lock()

    def get_credentials(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get valid AWS credentials, refreshing if necessary.

        Args:
            force_refresh: Force credential refresh

        Returns:
            Dict with access_key_id, secret_access_key, session_token

        Raises:
            RuntimeError: If credential fetch fails
        """
        with self._lock:
            if not force_refresh and self._credentials_cache:
                expiry = self._credentials_cache.get('expiry')
                if expiry and datetime.now() < (expiry - timedelta(minutes=5)):
                    return {
                        'access_key_id': self._credentials_cache['access_key_id'],
                        'secret_access_key': self._credentials_cache['secret_access_key'],
                        'session_token': self._credentials_cache.get('session_token'),
                    }

            return self._fetch_new_credentials()

    def _fetch_new_credentials(self) -> Dict[str, str]:
        """
        Fetch new AWS credentials via STS.

        Returns:
            New credentials dict

        Raises:
            RuntimeError: If credential fetch fails
        """
        try:
            # Create STS client
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=self._config.access_key_id,
                aws_secret_access_key=self._config.secret_access_key,
                aws_session_token=self._config.session_token,
                region_name=self._config.region
            )

            if self._config.role_arn:
                # Assume role
                response = sts_client.assume_role(
                    RoleArn=self._config.role_arn,
                    RoleSessionName=f'icestreams-{datetime.now().timestamp()}',
                    DurationSeconds=self._config.session_duration
                )
                credentials = response['Credentials']

                self._credentials_cache = {
                    'access_key_id': credentials['AccessKeyId'],
                    'secret_access_key': credentials['SecretAccessKey'],
                    'session_token': credentials['SessionToken'],
                    'expiry': credentials['Expiration'].replace(tzinfo=None)
                }

                logger.info(
                    "Successfully assumed role %s, expires at %s",
                    self._config.role_arn,
                    credentials['Expiration'].isoformat()
                )
            else:
                # Get session token
                response = sts_client.get_session_token(
                    DurationSeconds=self._config.session_duration
                )
                credentials = response['Credentials']

                self._credentials_cache = {
                    'access_key_id': credentials['AccessKeyId'],
                    'secret_access_key': credentials['SecretAccessKey'],
                    'session_token': credentials['SessionToken'],
                    'expiry': credentials['Expiration'].replace(tzinfo=None)
                }

                logger.info(
                    "Successfully fetched session token, expires at %s",
                    credentials['Expiration'].isoformat()
                )

            return {
                'access_key_id': self._credentials_cache['access_key_id'],
                'secret_access_key': self._credentials_cache['secret_access_key'],
                'session_token': self._credentials_cache.get('session_token'),
            }

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to fetch AWS STS credentials: %s", str(e))
            raise RuntimeError(f"AWS STS credential fetch failed: {e}") from e

    def invalidate_cache(self) -> None:
        """Invalidate cached credentials, forcing refresh on next request."""
        with self._lock:
            self._credentials_cache = None
            logger.debug("AWS STS credentials cache invalidated")
