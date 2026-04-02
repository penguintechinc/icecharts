"""Google Cloud Storage provider implementation for IceCharts.

This module provides GCS object storage support with async operations,
signed URLs, and comprehensive error handling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.cloud import storage
from google.cloud.exceptions import Forbidden, NotFound
from google.oauth2 import service_account

from .base import (StorageAuthenticationError, StorageConfigError,
                   StorageConnectionError, StorageError, StorageFile,
                   StorageProvider)


class GCSProvider(StorageProvider):
    """Google Cloud Storage provider implementation.

    Supports all standard GCS operations including upload, download,
    delete, signed URLs, and file listing with async/await patterns.
    """

    def _validate_config(self) -> None:
        """Validate GCS configuration.

        Raises:
            StorageConfigError: If required configuration is missing
        """
        required = ["bucket", "project_id"]
        missing = [key for key in required if key not in self.config]

        if missing:
            raise StorageConfigError(
                f"GCS configuration missing required fields: {missing}"
            )

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize GCS provider.

        Args:
            config: Configuration dictionary with GCS settings
        """
        super().__init__(config)

        try:
            # Initialize GCS client
            credentials_path = self.config.get("credentials_path")

            if credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.client = storage.Client(
                    project=self.config["project_id"], credentials=credentials
                )
            else:
                # Use default credentials (Application Default Credentials)
                self.client = storage.Client(project=self.config["project_id"])

            self.bucket_name = self.config["bucket"]
            self.bucket = self.client.bucket(self.bucket_name)

            # Verify bucket access
            self._verify_connection()

        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize GCS client: {e}")

    def _verify_connection(self) -> None:
        """Verify connection to GCS and bucket access."""
        try:
            self.bucket.reload()
        except NotFound:
            raise StorageConfigError(f"Bucket does not exist: {self.bucket_name}")
        except Forbidden as e:
            raise StorageAuthenticationError(
                f"Access denied to bucket: {self.bucket_name}: {e}"
            )
        except Exception as e:
            raise StorageConnectionError(f"Failed to verify bucket access: {e}")

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload data to GCS.

        Args:
            key: Object key/path
            data: Binary data to upload
            content_type: MIME type of the data
            metadata: Optional metadata key-value pairs

        Returns:
            The key of the uploaded object

        Raises:
            StorageError: If upload fails
        """
        try:
            blob = self.bucket.blob(key)
            blob.content_type = content_type

            if metadata:
                blob.metadata = metadata

            # Run blocking GCS operation in executor
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: blob.upload_from_string(data)
            )

            return key

        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to upload to GCS: {e}")

    async def download(self, key: str) -> bytes:
        """Download data from GCS.

        Args:
            key: Object key/path

        Returns:
            Binary data of the object

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If download fails
        """
        try:
            blob = self.bucket.blob(key)

            # Run blocking GCS operation in executor
            data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: blob.download_as_bytes()
            )

            return data

        except NotFound:
            raise FileNotFoundError(f"Object not found: {key}")
        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to download from GCS: {e}")

    async def delete(self, key: str) -> bool:
        """Delete an object from GCS.

        Args:
            key: Object key/path

        Returns:
            True if deletion was successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            blob = self.bucket.blob(key)

            await asyncio.get_event_loop().run_in_executor(None, lambda: blob.delete())
            return True

        except NotFound:
            return False
        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to delete from GCS: {e}")

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a signed URL for object access.

        Args:
            key: Object key/path
            expires_in: URL expiration time in seconds

        Returns:
            Signed URL for object access

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If URL generation fails
        """
        try:
            # Check if object exists first
            if not await self.exists(key):
                raise FileNotFoundError(f"Object not found: {key}")

            blob = self.bucket.blob(key)

            # Generate signed URL
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: blob.generate_signed_url(
                    version="v4", expiration=timedelta(seconds=expires_in), method="GET"
                ),
            )

            return url

        except FileNotFoundError:
            raise
        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to generate signed URL: {e}")

    async def list_files(self, prefix: Optional[str] = None) -> List[StorageFile]:
        """List objects in GCS bucket with optional prefix filter.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        try:
            # Run blocking GCS operation in executor
            blobs = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(
                    self.client.list_blobs(
                        bucket_or_name=self.bucket_name, prefix=prefix
                    )
                ),
            )

            storage_files = []
            for blob in blobs:
                storage_file = StorageFile(
                    key=blob.name,
                    size=blob.size,
                    content_type=blob.content_type or "application/octet-stream",
                    last_modified=blob.updated,
                    etag=blob.etag,
                    metadata=blob.metadata,
                )
                storage_files.append(storage_file)

            return storage_files

        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to list objects from GCS: {e}")

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Copy an object within GCS bucket.

        Args:
            source_key: Source object key/path
            dest_key: Destination object key/path

        Returns:
            True if copy was successful

        Raises:
            FileNotFoundError: If source object does not exist
            StorageError: If copy fails
        """
        try:
            # Check if source exists
            if not await self.exists(source_key):
                raise FileNotFoundError(f"Source object not found: {source_key}")

            source_blob = self.bucket.blob(source_key)
            dest_blob = self.bucket.blob(dest_key)

            # Perform copy operation
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.bucket.copy_blob(
                    blob=source_blob, destination_bucket=self.bucket, new_name=dest_key
                ),
            )

            return True

        except FileNotFoundError:
            raise
        except NotFound:
            raise FileNotFoundError(f"Source object not found: {source_key}")
        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Failed to copy object in GCS: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists in GCS bucket.

        Args:
            key: Object key/path

        Returns:
            True if object exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        try:
            blob = self.bucket.blob(key)

            exists = await asyncio.get_event_loop().run_in_executor(
                None, lambda: blob.exists()
            )

            return exists

        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during existence check: {e}")

    async def get_metadata(self, key: str) -> StorageFile:
        """Get metadata for an object without downloading it.

        Args:
            key: Object key/path

        Returns:
            StorageFile object with metadata

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If metadata retrieval fails
        """
        try:
            blob = self.bucket.blob(key)

            await asyncio.get_event_loop().run_in_executor(None, lambda: blob.reload())

            return StorageFile(
                key=key,
                size=blob.size,
                content_type=blob.content_type or "application/octet-stream",
                last_modified=blob.updated,
                etag=blob.etag,
                metadata=blob.metadata,
            )

        except NotFound:
            raise FileNotFoundError(f"Object not found: {key}")
        except Forbidden as e:
            raise StorageAuthenticationError(f"Access denied: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during metadata retrieval: {e}")
