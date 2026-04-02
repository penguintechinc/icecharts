"""
Base authentication client framework for cloud service integrations.

This module provides the abstract base class for all authentication clients used
by cloud action nodes. Authentication clients handle credential management, token
refresh, and provider-specific authentication flows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional


@dataclass(slots=True)
class AuthCredentials:
    """
    Authentication credentials for cloud services.

    Attributes:
        provider: Cloud provider identifier.
        access_token: Current access token.
        refresh_token: Optional refresh token for token renewal.
        expires_at: Token expiration timestamp.
        metadata: Additional provider-specific metadata.
    """

    provider: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) >= self.expires_at

    def needs_refresh(self, buffer_seconds: int = 300) -> bool:
        """
        Check if token needs refresh with a time buffer.

        Args:
            buffer_seconds: Seconds before expiration to trigger refresh.

        Returns:
            True if token should be refreshed.
        """
        if self.expires_at is None:
            return False
        refresh_time = self.expires_at - timedelta(seconds=buffer_seconds)
        return datetime.now(UTC) >= refresh_time


class BaseAuthClient(ABC):
    """
    Abstract base class for cloud service authentication clients.

    All authentication client implementations must inherit from this class
    and implement the abstract methods for authentication and token refresh.
    """

    def __init__(self, provider: str) -> None:
        """
        Initialize the authentication client.

        Args:
            provider: Cloud provider identifier (e.g., "aws", "gcp", "openwhisk").
        """
        self.provider = provider
        self._credentials: Optional[AuthCredentials] = None

    @abstractmethod
    async def authenticate(self, config: Dict[str, Any]) -> AuthCredentials:
        """
        Authenticate with the cloud provider and obtain credentials.

        Args:
            config: Provider-specific authentication configuration.

        Returns:
            AuthCredentials containing access token and metadata.

        Raises:
            Exception: If authentication fails.
        """
        pass

    @abstractmethod
    async def refresh_token(self, credentials: AuthCredentials) -> AuthCredentials:
        """
        Refresh an expired or expiring access token.

        Args:
            credentials: Current credentials with refresh token.

        Returns:
            New AuthCredentials with refreshed access token.

        Raises:
            Exception: If token refresh fails.
        """
        pass

    async def get_valid_credentials(self, config: Dict[str, Any]) -> AuthCredentials:
        """
        Get valid credentials, refreshing if necessary.

        Args:
            config: Authentication configuration.

        Returns:
            Valid AuthCredentials.

        Raises:
            Exception: If authentication or refresh fails.
        """
        # No cached credentials, authenticate
        if self._credentials is None:
            self._credentials = await self.authenticate(config)
            return self._credentials

        # Credentials need refresh
        if self._credentials.needs_refresh():
            try:
                self._credentials = await self.refresh_token(self._credentials)
            except Exception:
                # Refresh failed, re-authenticate
                self._credentials = await self.authenticate(config)

        return self._credentials

    def clear_credentials(self) -> None:
        """Clear cached credentials."""
        self._credentials = None
