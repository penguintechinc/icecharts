"""
OIDC authentication client for GCP Cloud Run and other OIDC-enabled services.

This module provides OpenID Connect (OIDC) authentication for services that
require ID tokens for authentication, such as GCP Cloud Run.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional

import aiohttp

from .base_auth import AuthCredentials, BaseAuthClient


class OIDCClient(BaseAuthClient):
    """
    OpenID Connect (OIDC) authentication client.

    Supports ID token generation for GCP Cloud Run and other OIDC-enabled
    services that require identity tokens for authentication.
    """

    def __init__(self, provider: str = "gcp") -> None:
        """
        Initialize OIDC client.

        Args:
            provider: Provider identifier (default: "gcp").
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
        Authenticate and obtain OIDC ID token.

        Args:
            config: Authentication configuration containing:
                - service_account_key: GCP service account JSON key (as dict)
                - target_audience: Target audience URL (e.g., Cloud Run service URL)
                - token_url: Optional custom token endpoint

        Returns:
            AuthCredentials with ID token.

        Raises:
            ValueError: If required config parameters are missing.
            aiohttp.ClientError: If HTTP request fails.
        """
        service_account = config.get("service_account_key")
        target_audience = config.get("target_audience")

        if not service_account:
            raise ValueError("OIDC authentication requires 'service_account_key'")
        if not target_audience:
            raise ValueError("OIDC authentication requires 'target_audience'")

        # Parse service account key
        if isinstance(service_account, str):
            service_account = json.loads(service_account)

        # Extract service account details
        client_email = service_account.get("client_email")
        private_key = service_account.get("private_key")
        token_uri = service_account.get("token_uri") or config.get(
            "token_url", "https://oauth2.googleapis.com/token"
        )

        if not client_email or not private_key:
            raise ValueError(
                "Service account key must contain 'client_email' and 'private_key'"
            )

        # Create JWT assertion for ID token request
        import jwt
        import time

        now = int(time.time())
        payload = {
            "iss": client_email,
            "sub": client_email,
            "aud": token_uri,
            "iat": now,
            "exp": now + 3600,
            "target_audience": target_audience,
        }

        assertion = jwt.encode(payload, private_key, algorithm="RS256")

        # Request ID token
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }

        session = await self._get_session()
        async with session.post(token_uri, data=data) as response:
            response.raise_for_status()
            token_data = await response.json()

        # Parse token response
        id_token = token_data.get("id_token")
        if not id_token:
            raise ValueError("OIDC response missing 'id_token'")

        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        # Store service account for refresh
        metadata = {
            "service_account_key": service_account,
            "target_audience": target_audience,
            "token_uri": token_uri,
            "client_email": client_email,
            "issued_at": datetime.now(UTC).isoformat(),
        }

        return AuthCredentials(
            provider=self.provider,
            access_token=id_token,
            refresh_token=None,  # OIDC ID tokens are refreshed by re-authentication
            expires_at=expires_at,
            metadata=metadata,
        )

    async def refresh_token(self, credentials: AuthCredentials) -> AuthCredentials:
        """
        Refresh ID token by re-authenticating.

        OIDC ID tokens cannot be refreshed; they must be re-obtained.

        Args:
            credentials: Current credentials containing service account info.

        Returns:
            New AuthCredentials with fresh ID token.

        Raises:
            ValueError: If service account metadata is missing.
        """
        # Extract service account from metadata
        service_account = credentials.metadata.get("service_account_key")
        target_audience = credentials.metadata.get("target_audience")

        if not service_account or not target_audience:
            raise ValueError(
                "Cannot refresh OIDC token: missing service account metadata"
            )

        # Re-authenticate to get new ID token
        config = {
            "service_account_key": service_account,
            "target_audience": target_audience,
        }

        return await self.authenticate(config)

    async def authenticate_gcp_cloudrun(
        self, config: Dict[str, Any]
    ) -> AuthCredentials:
        """
        Authenticate specifically for GCP Cloud Run.

        Args:
            config: GCP Cloud Run configuration containing:
                - service_account_key: GCP service account JSON key
                - service_url: Cloud Run service URL (used as target_audience)
                - project_id: Optional GCP project ID
                - region: Optional GCP region

        Returns:
            AuthCredentials with Cloud Run ID token.

        Raises:
            ValueError: If required config parameters are missing.
        """
        service_url = config.get("service_url")
        if not service_url:
            raise ValueError("GCP Cloud Run authentication requires 'service_url'")

        # Use service URL as target audience
        auth_config = {
            "service_account_key": config.get("service_account_key"),
            "target_audience": service_url,
        }

        # Add optional metadata
        credentials = await self.authenticate(auth_config)

        # Enhance metadata with GCP-specific info
        credentials.metadata["service_url"] = service_url
        credentials.metadata["project_id"] = config.get("project_id", "")
        credentials.metadata["region"] = config.get("region", "")

        return credentials

    async def authenticate_with_metadata_server(self) -> AuthCredentials:
        """
        Authenticate using GCP metadata server (for workload running on GCP).

        This method obtains an ID token from the GCP metadata server, which
        is available when running on GCP infrastructure (GCE, GKE, Cloud Run).

        Returns:
            AuthCredentials with ID token from metadata server.

        Raises:
            aiohttp.ClientError: If metadata server request fails.
        """
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity"

        session = await self._get_session()
        headers = {"Metadata-Flavor": "Google"}

        async with session.get(metadata_url, headers=headers) as response:
            response.raise_for_status()
            id_token = await response.text()

        # GCP metadata server tokens expire in 1 hour
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        metadata = {
            "source": "metadata_server",
            "issued_at": datetime.now(UTC).isoformat(),
        }

        return AuthCredentials(
            provider=self.provider,
            access_token=id_token,
            refresh_token=None,
            expires_at=expires_at,
            metadata=metadata,
        )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> OIDCClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
