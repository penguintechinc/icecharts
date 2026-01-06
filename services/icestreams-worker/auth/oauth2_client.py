"""
OAuth2 authentication client for AWS Lambda and Apache OpenWhisk.

This module provides OAuth2-based authentication for cloud services that use
OAuth2 flows for obtaining access tokens. Used by AWS Lambda (via STS) and
Apache OpenWhisk action nodes.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional

import aiohttp

from .base_auth import AuthCredentials, BaseAuthClient


class OAuth2Client(BaseAuthClient):
    """
    OAuth2 authentication client for cloud services.

    Supports client credentials flow and custom token endpoints for
    AWS STS and Apache OpenWhisk authentication.
    """

    def __init__(self, provider: str) -> None:
        """
        Initialize OAuth2 client.

        Args:
            provider: Provider identifier ("aws" or "openwhisk").
        """
        super().__init__(provider)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def authenticate(self, config: Dict[str, Any]) -> AuthCredentials:
        """
        Authenticate using OAuth2 client credentials flow.

        Args:
            config: Authentication configuration containing:
                - token_url: OAuth2 token endpoint URL
                - client_id: OAuth2 client identifier
                - client_secret: OAuth2 client secret
                - scope: Optional OAuth2 scopes (space-separated)
                - custom_params: Optional additional parameters

        Returns:
            AuthCredentials with access token.

        Raises:
            ValueError: If required config parameters are missing.
            aiohttp.ClientError: If HTTP request fails.
        """
        # Validate required parameters
        token_url = config.get("token_url")
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")

        if not token_url:
            raise ValueError("OAuth2 authentication requires 'token_url'")
        if not client_id:
            raise ValueError("OAuth2 authentication requires 'client_id'")
        if not client_secret:
            raise ValueError("OAuth2 authentication requires 'client_secret'")

        # Build token request
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        # Add optional scope
        scope = config.get("scope")
        if scope:
            data["scope"] = scope

        # Add custom parameters
        custom_params = config.get("custom_params", {})
        data.update(custom_params)

        # Request access token
        session = await self._get_session()
        async with session.post(token_url, data=data) as response:
            response.raise_for_status()
            token_data = await response.json()

        # Parse token response
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("OAuth2 response missing 'access_token'")

        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

        # Calculate expiration
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        # Extract additional metadata
        metadata = {
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope", ""),
            "issued_at": datetime.now(UTC).isoformat(),
        }

        return AuthCredentials(
            provider=self.provider,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            metadata=metadata,
        )

    async def refresh_token(self, credentials: AuthCredentials) -> AuthCredentials:
        """
        Refresh access token using refresh token.

        Args:
            credentials: Current credentials with refresh_token.

        Returns:
            New AuthCredentials with refreshed access token.

        Raises:
            ValueError: If refresh token is not available.
            aiohttp.ClientError: If HTTP request fails.
        """
        if not credentials.refresh_token:
            raise ValueError("Cannot refresh token: no refresh_token available")

        # Refresh tokens require the original token_url from metadata
        token_url = credentials.metadata.get("token_url")
        if not token_url:
            raise ValueError("Cannot refresh token: token_url not in metadata")

        # Build refresh request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": credentials.refresh_token,
        }

        # Add client credentials if available in metadata
        client_id = credentials.metadata.get("client_id")
        client_secret = credentials.metadata.get("client_secret")
        if client_id and client_secret:
            data["client_id"] = client_id
            data["client_secret"] = client_secret

        # Request new access token
        session = await self._get_session()
        async with session.post(token_url, data=data) as response:
            response.raise_for_status()
            token_data = await response.json()

        # Parse token response
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Refresh response missing 'access_token'")

        new_refresh_token = token_data.get("refresh_token", credentials.refresh_token)
        expires_in = token_data.get("expires_in", 3600)

        # Calculate expiration
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        # Update metadata
        metadata = credentials.metadata.copy()
        metadata["token_type"] = token_data.get("token_type", "Bearer")
        metadata["scope"] = token_data.get("scope", "")
        metadata["refreshed_at"] = datetime.now(UTC).isoformat()

        return AuthCredentials(
            provider=self.provider,
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_at=expires_at,
            metadata=metadata,
        )

    async def authenticate_aws_sts(self, config: Dict[str, Any]) -> AuthCredentials:
        """
        Authenticate with AWS using STS AssumeRole.

        Args:
            config: AWS authentication configuration containing:
                - aws_access_key_id: AWS access key ID
                - aws_secret_access_key: AWS secret access key
                - aws_region: AWS region (default: us-east-1)
                - role_arn: Optional IAM role ARN to assume
                - session_duration: Optional session duration in seconds

        Returns:
            AuthCredentials with AWS temporary credentials.

        Raises:
            ValueError: If required config parameters are missing.
        """
        access_key = config.get("aws_access_key_id")
        secret_key = config.get("aws_secret_access_key")
        region = config.get("aws_region", "us-east-1")

        if not access_key:
            raise ValueError("AWS authentication requires 'aws_access_key_id'")
        if not secret_key:
            raise ValueError("AWS authentication requires 'aws_secret_access_key'")

        # For basic credentials, return as-is
        # Token will be generated on-demand by AWS SDK
        expires_at = datetime.now(UTC) + timedelta(hours=12)  # AWS default

        metadata = {
            "aws_region": region,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "credential_type": "static",
        }

        # Add role ARN if provided
        role_arn = config.get("role_arn")
        if role_arn:
            metadata["role_arn"] = role_arn

        return AuthCredentials(
            provider="aws",
            access_token=access_key,  # Use as identifier
            refresh_token=None,
            expires_at=expires_at,
            metadata=metadata,
        )

    async def authenticate_openwhisk(self, config: Dict[str, Any]) -> AuthCredentials:
        """
        Authenticate with Apache OpenWhisk.

        Args:
            config: OpenWhisk authentication configuration containing:
                - api_host: OpenWhisk API host URL
                - auth_key: OpenWhisk authentication key (UUID:KEY format)
                - namespace: Optional namespace (default: _)

        Returns:
            AuthCredentials with OpenWhisk auth key.

        Raises:
            ValueError: If required config parameters are missing.
        """
        api_host = config.get("api_host")
        auth_key = config.get("auth_key")
        namespace = config.get("namespace", "_")

        if not api_host:
            raise ValueError("OpenWhisk authentication requires 'api_host'")
        if not auth_key:
            raise ValueError("OpenWhisk authentication requires 'auth_key'")

        # Validate auth_key format (UUID:KEY)
        if ":" not in auth_key:
            raise ValueError("OpenWhisk 'auth_key' must be in format 'UUID:KEY'")

        # OpenWhisk uses basic auth, no expiration
        metadata = {
            "api_host": api_host,
            "namespace": namespace,
            "auth_key": auth_key,
        }

        return AuthCredentials(
            provider="openwhisk",
            access_token=auth_key,
            refresh_token=None,
            expires_at=None,  # No expiration
            metadata=metadata,
        )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> OAuth2Client:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
