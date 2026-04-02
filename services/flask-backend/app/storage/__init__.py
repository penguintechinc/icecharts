"""Storage abstraction layer for IceCharts.

This module provides a unified interface for multiple storage providers
including MinIO, AWS S3, Google Cloud Storage, OneDrive, and Google Drive.

Usage:
    from app.storage import get_storage_provider

    # Initialize storage provider based on configuration
    storage = get_storage_provider()

    # Upload a file
    await storage.upload('path/to/file.txt', data, 'text/plain')

    # Download a file
    data = await storage.download('path/to/file.txt')

    # Get presigned URL
    url = await storage.get_url('path/to/file.txt', expires_in=3600)
"""

import os
from typing import Any, Dict, Optional

from .base import (StorageAuthenticationError, StorageConfigError,
                   StorageConnectionError, StorageError, StorageFile,
                   StorageProvider)

__all__ = [
    "get_storage_provider",
    "StorageProvider",
    "StorageFile",
    "StorageError",
    "StorageConfigError",
    "StorageConnectionError",
    "StorageAuthenticationError",
]


def get_storage_provider(
    provider_type: Optional[str] = None, config: Optional[Dict[str, Any]] = None
) -> StorageProvider:
    """Factory function to create storage provider instances.

    Args:
        provider_type: Type of storage provider (minio, s3, gcs, onedrive,
                      googledrive). If None, reads from STORAGE_PROVIDER env var
        config: Provider-specific configuration dictionary. If None, reads
               from environment variables

    Returns:
        Initialized storage provider instance

    Raises:
        StorageConfigError: If provider type is invalid or configuration
                           is missing
        ImportError: If required provider library is not installed

    Environment Variables:
        STORAGE_PROVIDER: Provider type (required if provider_type is None)

        MinIO/S3:
            STORAGE_ENDPOINT: MinIO/S3 endpoint URL
            STORAGE_ACCESS_KEY: Access key ID
            STORAGE_SECRET_KEY: Secret access key
            STORAGE_BUCKET: Bucket name
            STORAGE_REGION: AWS region (S3 only, optional)
            STORAGE_SECURE: Use HTTPS (true/false, default: true)

        GCS:
            STORAGE_BUCKET: GCS bucket name
            STORAGE_PROJECT_ID: GCP project ID
            GCS_CREDENTIALS_PATH: Path to service account JSON file

        OneDrive:
            ONEDRIVE_CLIENT_ID: Azure AD application client ID
            ONEDRIVE_CLIENT_SECRET: Azure AD application client secret
            ONEDRIVE_TENANT_ID: Azure AD tenant ID
            ONEDRIVE_FOLDER_PATH: Root folder path (optional)

        Google Drive:
            GDRIVE_CREDENTIALS_PATH: Path to OAuth2 credentials JSON
            GDRIVE_TOKEN_PATH: Path to store/read OAuth2 token
            GDRIVE_FOLDER_ID: Root folder ID (optional)
    """
    # Determine provider type
    if provider_type is None:
        provider_type = os.getenv("STORAGE_PROVIDER", "").lower()

    if not provider_type:
        raise StorageConfigError(
            "Storage provider type not specified. Set STORAGE_PROVIDER "
            "environment variable or pass provider_type parameter"
        )

    # Build configuration from environment if not provided
    if config is None:
        config = _build_config_from_env(provider_type)

    # Import and instantiate appropriate provider
    try:
        if provider_type == "minio":
            from .minio_provider import MinIOProvider

            return MinIOProvider(config)

        elif provider_type == "s3":
            from .s3_provider import S3Provider

            return S3Provider(config)

        elif provider_type == "gcs":
            from .gcs_provider import GCSProvider

            return GCSProvider(config)

        elif provider_type == "onedrive":
            from .onedrive_provider import OneDriveProvider

            return OneDriveProvider(config)

        elif provider_type == "googledrive":
            from .google_drive_provider import GoogleDriveProvider

            return GoogleDriveProvider(config)

        else:
            raise StorageConfigError(
                f"Unsupported storage provider: {provider_type}. "
                f"Supported providers: minio, s3, gcs, onedrive, googledrive"
            )

    except ImportError as e:
        raise ImportError(
            f"Failed to import {provider_type} provider. "
            f"Ensure required dependencies are installed: {e}"
        )


def _build_config_from_env(provider_type: str) -> Dict[str, Any]:
    """Build provider configuration from environment variables.

    Args:
        provider_type: Type of storage provider

    Returns:
        Configuration dictionary for the specified provider

    Raises:
        StorageConfigError: If required environment variables are missing
    """
    if provider_type in ("minio", "s3"):
        endpoint = os.getenv("STORAGE_ENDPOINT")
        access_key = os.getenv("STORAGE_ACCESS_KEY")
        secret_key = os.getenv("STORAGE_SECRET_KEY")
        bucket = os.getenv("STORAGE_BUCKET")

        if not all([access_key, secret_key, bucket]):
            raise StorageConfigError(
                f"{provider_type.upper()} configuration incomplete. Required: "
                "STORAGE_ACCESS_KEY, STORAGE_SECRET_KEY, STORAGE_BUCKET"
            )

        config = {
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key,
            "bucket": bucket,
            "secure": os.getenv("STORAGE_SECURE", "true").lower() == "true",
        }

        if provider_type == "s3":
            config["region"] = os.getenv("STORAGE_REGION", "us-east-1")

        return config

    elif provider_type == "gcs":
        bucket = os.getenv("STORAGE_BUCKET")
        project_id = os.getenv("STORAGE_PROJECT_ID")
        credentials_path = os.getenv("GCS_CREDENTIALS_PATH")

        if not all([bucket, project_id]):
            raise StorageConfigError(
                "GCS configuration incomplete. Required: "
                "STORAGE_BUCKET, STORAGE_PROJECT_ID"
            )

        return {
            "bucket": bucket,
            "project_id": project_id,
            "credentials_path": credentials_path,
        }

    elif provider_type == "onedrive":
        client_id = os.getenv("ONEDRIVE_CLIENT_ID")
        client_secret = os.getenv("ONEDRIVE_CLIENT_SECRET")
        tenant_id = os.getenv("ONEDRIVE_TENANT_ID")

        if not all([client_id, client_secret, tenant_id]):
            raise StorageConfigError(
                "OneDrive configuration incomplete. Required: "
                "ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID"
            )

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "folder_path": os.getenv("ONEDRIVE_FOLDER_PATH", "/"),
        }

    elif provider_type == "googledrive":
        credentials_path = os.getenv("GDRIVE_CREDENTIALS_PATH")
        token_path = os.getenv("GDRIVE_TOKEN_PATH", "token.json")

        if not credentials_path:
            raise StorageConfigError(
                "Google Drive configuration incomplete. Required: "
                "GDRIVE_CREDENTIALS_PATH"
            )

        return {
            "credentials_path": credentials_path,
            "token_path": token_path,
            "folder_id": os.getenv("GDRIVE_FOLDER_ID"),
        }

    else:
        raise StorageConfigError(f"Unknown provider type: {provider_type}")
