"""Drawing content storage service for IceCharts.

This module provides S3-compatible storage for drawing content (nodes, edges).
Drawing content is stored as JSON files in object storage with versioning support.

Supports any S3-compatible storage provider:
- MinIO (development/testing)
- AWS S3 (production)
- Google Cloud Storage
- Azure Blob Storage (via S3 API)
"""

import asyncio
import json
import os
from typing import Any, Optional

from flask import current_app


class DrawingStorageService:
    """Service for storing and retrieving drawing content from S3-compatible storage."""

    _provider = None
    _initialized = False

    @classmethod
    def _get_provider(cls):
        """Get or initialize the storage provider based on configuration.

        Reads STORAGE_PROVIDER env var to determine which provider to use:
        - 'minio': MinIO (default for dev)
        - 's3': AWS S3
        - 'gcs': Google Cloud Storage

        Returns:
            StorageProvider instance

        Raises:
            RuntimeError: If storage is not configured
        """
        if cls._provider is None:
            try:
                from app.storage import get_storage_provider

                # Determine provider type from environment
                provider_type = os.getenv("STORAGE_PROVIDER", "minio").lower()

                # Build config based on provider type
                if provider_type in ("minio", "s3"):
                    config = {
                        "endpoint": os.getenv("MINIO_ENDPOINT") or os.getenv("STORAGE_ENDPOINT", "minio:9000"),
                        "access_key": os.getenv("MINIO_ACCESS_KEY") or os.getenv("STORAGE_ACCESS_KEY", "minioadmin"),
                        "secret_key": os.getenv("MINIO_SECRET_KEY") or os.getenv("STORAGE_SECRET_KEY", "minioadmin"),
                        "bucket": os.getenv("MINIO_BUCKET") or os.getenv("STORAGE_BUCKET", "icecharts"),
                        "secure": (os.getenv("MINIO_SECURE") or os.getenv("STORAGE_SECURE", "false")).lower() == "true",
                    }
                    if provider_type == "s3":
                        config["region"] = os.getenv("STORAGE_REGION", "us-east-1")
                else:
                    # Let the storage factory handle other providers from env
                    config = None

                cls._provider = get_storage_provider(provider_type, config)
                cls._initialized = True
                current_app.logger.info(f"Initialized storage provider: {provider_type}")

            except Exception as e:
                current_app.logger.error(f"Failed to initialize storage: {e}")
                raise RuntimeError(f"Object storage not available: {e}")

        return cls._provider

    @classmethod
    def _run_async(cls, coro):
        """Run an async coroutine in a sync context.

        Args:
            coro: Async coroutine to run

        Returns:
            Result of the coroutine
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    @classmethod
    def get_storage_key(cls, drawing_id: int, version: int = None) -> str:
        """Generate the object key for a drawing.

        Args:
            drawing_id: Drawing ID
            version: Version number (optional, uses 'latest' if not specified)

        Returns:
            Object key string (e.g., 'drawings/123/v1.json')
        """
        if version:
            return f"drawings/{drawing_id}/v{version}.json"
        return f"drawings/{drawing_id}/latest.json"

    @classmethod
    def save_content(
        cls,
        drawing_id: int,
        content: dict,
        version: int = None,
        user_id: int = None,
    ) -> str:
        """Save drawing content to object storage.

        Args:
            drawing_id: Drawing ID
            content: Drawing content dict with nodes, edges, etc.
            version: Version number (optional)
            user_id: User ID making the change (for metadata)

        Returns:
            Storage key where content was saved

        Raises:
            RuntimeError: If storage fails
        """
        try:
            provider = cls._get_provider()

            # Prepare content with metadata
            storage_content = {
                "drawing_id": drawing_id,
                "version": version,
                "content": content,
                "saved_by": user_id,
            }

            # Serialize to JSON bytes
            json_bytes = json.dumps(storage_content, indent=2).encode("utf-8")

            # Save to storage
            key = cls.get_storage_key(drawing_id, version)

            cls._run_async(
                provider.upload(
                    key=key,
                    data=json_bytes,
                    content_type="application/json",
                    metadata={
                        "drawing_id": str(drawing_id),
                        "version": str(version) if version else "latest",
                        "user_id": str(user_id) if user_id else "",
                    },
                )
            )

            # Also save as 'latest' if versioned
            if version:
                latest_key = cls.get_storage_key(drawing_id, None)
                cls._run_async(
                    provider.upload(
                        key=latest_key,
                        data=json_bytes,
                        content_type="application/json",
                        metadata={
                            "drawing_id": str(drawing_id),
                            "version": str(version),
                            "user_id": str(user_id) if user_id else "",
                        },
                    )
                )

            current_app.logger.info(
                f"Saved drawing {drawing_id} v{version} to storage: {key}"
            )
            return key

        except Exception as e:
            current_app.logger.error(f"Failed to save drawing to storage: {e}")
            raise RuntimeError(f"Failed to save drawing content: {e}")

    @classmethod
    def load_content(
        cls,
        drawing_id: int,
        version: int = None,
    ) -> Optional[dict]:
        """Load drawing content from object storage.

        Args:
            drawing_id: Drawing ID
            version: Version number (optional, loads latest if not specified)

        Returns:
            Drawing content dict or None if not found
        """
        try:
            provider = cls._get_provider()
            key = cls.get_storage_key(drawing_id, version)

            # Check if exists
            exists = cls._run_async(provider.exists(key))
            if not exists:
                current_app.logger.debug(f"Drawing content not found: {key}")
                return None

            # Download content
            data = cls._run_async(provider.download(key))
            storage_content = json.loads(data.decode("utf-8"))

            current_app.logger.debug(f"Loaded drawing {drawing_id} from storage: {key}")
            return storage_content.get("content", storage_content)

        except FileNotFoundError:
            return None
        except Exception as e:
            current_app.logger.error(f"Failed to load drawing from storage: {e}")
            return None

    @classmethod
    def delete_content(cls, drawing_id: int, version: int = None) -> bool:
        """Delete drawing content from object storage.

        Args:
            drawing_id: Drawing ID
            version: Version number (optional, deletes specific version)
                    If None, deletes all versions

        Returns:
            True if deleted successfully
        """
        try:
            provider = cls._get_provider()

            if version:
                # Delete specific version
                key = cls.get_storage_key(drawing_id, version)
                result = cls._run_async(provider.delete(key))
                return result
            else:
                # Delete all versions
                prefix = f"drawings/{drawing_id}/"
                files = cls._run_async(provider.list_files(prefix=prefix))

                for f in files:
                    cls._run_async(provider.delete(f.key))

                current_app.logger.info(
                    f"Deleted all content for drawing {drawing_id}"
                )
                return True

        except Exception as e:
            current_app.logger.error(f"Failed to delete drawing content: {e}")
            return False

    @classmethod
    def list_versions(cls, drawing_id: int) -> list[dict]:
        """List all versions of a drawing stored in object storage.

        Args:
            drawing_id: Drawing ID

        Returns:
            List of version info dicts with key, version, size, modified
        """
        try:
            provider = cls._get_provider()
            prefix = f"drawings/{drawing_id}/"

            files = cls._run_async(provider.list_files(prefix=prefix))

            versions = []
            for f in files:
                # Extract version number from key
                filename = f.key.split("/")[-1]
                if filename.startswith("v") and filename.endswith(".json"):
                    try:
                        version_num = int(filename[1:-5])  # Remove 'v' and '.json'
                        versions.append({
                            "key": f.key,
                            "version": version_num,
                            "size": f.size,
                            "modified": f.last_modified.isoformat() if f.last_modified else None,
                        })
                    except ValueError:
                        pass

            # Sort by version number
            versions.sort(key=lambda v: v["version"])
            return versions

        except Exception as e:
            current_app.logger.error(f"Failed to list drawing versions: {e}")
            return []

    @classmethod
    def get_presigned_url(
        cls,
        drawing_id: int,
        version: int = None,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """Get a presigned URL for direct content access.

        Args:
            drawing_id: Drawing ID
            version: Version number (optional)
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL or None if content doesn't exist
        """
        try:
            provider = cls._get_provider()
            key = cls.get_storage_key(drawing_id, version)

            # Check if exists
            exists = cls._run_async(provider.exists(key))
            if not exists:
                return None

            url = cls._run_async(provider.get_url(key, expires_in=expires_in))
            return url

        except Exception as e:
            current_app.logger.error(f"Failed to get presigned URL: {e}")
            return None

    @classmethod
    def is_available(cls) -> bool:
        """Check if object storage is available and configured.

        Returns:
            True if storage is available
        """
        try:
            cls._get_provider()
            return True
        except Exception:
            return False
