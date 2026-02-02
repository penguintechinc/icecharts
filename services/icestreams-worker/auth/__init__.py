"""
Authentication clients for cloud function integrations.

This package provides thread-safe authentication clients for:
- AWS STS (boto3)
- OpenWhisk OAuth2
- GCP OIDC (google-auth)

All clients support token caching and automatic refresh.
"""

from .oauth2 import (
    OAuth2Client,
    OAuth2Config,
    AWSSTSClient,
    AWSSTSConfig,
    CachedToken,
)
from .oidc import (
    OIDCClient,
    OIDCConfig,
    CachedIDToken,
)

__all__ = [
    # OAuth2
    'OAuth2Client',
    'OAuth2Config',
    'AWSSTSClient',
    'AWSSTSConfig',
    'CachedToken',
    # OIDC
    'OIDCClient',
    'OIDCConfig',
    'CachedIDToken',
]
