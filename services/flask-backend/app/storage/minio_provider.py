"""MinIO storage provider implementation for IceCharts.

This module provides MinIO object storage support with async operations,
presigned URLs, and comprehensive error handling.
"""

import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from .base import (
    StorageProvider,
    StorageFile,
    StorageError,
    StorageConfigError,
    StorageConnectionError,
    StorageAuthenticationError
)


class MinIOProvider(StorageProvider):
    """MinIO storage provider implementation.

    Supports all standard MinIO operations including upload, download,
    delete, presigned URLs, and file listing with async/await patterns.
    """

    def _validate_config(self) -> None:
        """Validate MinIO configuration.

        Raises:
            StorageConfigError: If required configuration is missing
        """
        required = ['endpoint', 'access_key', 'secret_key', 'bucket']
        missing = [key for key in required if key not in self.config]

        if missing:
            raise StorageConfigError(
                f"MinIO configuration missing required fields: {missing}"
            )

        # Parse endpoint to extract host and port
        endpoint = self.config['endpoint']
        if not endpoint:
            raise StorageConfigError("MinIO endpoint cannot be empty")

        # Remove protocol if present
        if '://' in endpoint:
            parsed = urlparse(endpoint)
            self.config['endpoint'] = parsed.netloc
            if 'secure' not in self.config:
                self.config['secure'] = parsed.scheme == 'https'

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize MinIO provider.

        Args:
            config: Configuration dictionary with MinIO settings
        """
        super().__init__(config)

        try:
            self.client = Minio(
                endpoint=self.config['endpoint'],
                access_key=self.config['access_key'],
                secret_key=self.config['secret_key'],
                secure=self.config.get('secure', True)
            )
            self.bucket = self.config['bucket']

            # Ensure bucket exists
            self._ensure_bucket()

        except Exception as e:
            raise StorageConnectionError(
                f"Failed to initialize MinIO client: {e}"
            )

    def _ensure_bucket(self) -> None:
        """Ensure the configured bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(
                    f"Access denied when checking bucket: {e}"
                )
            raise StorageError(f"Failed to ensure bucket exists: {e}")

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload data to MinIO.

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
            data_stream = BytesIO(data)
            data_length = len(data)

            # Run blocking MinIO operation in executor
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.put_object(
                    bucket_name=self.bucket,
                    object_name=key,
                    data=data_stream,
                    length=data_length,
                    content_type=content_type,
                    metadata=metadata
                )
            )

            return key

        except S3Error as e:
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to upload to MinIO: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during upload: {e}")

    async def download(self, key: str) -> bytes:
        """Download data from MinIO.

        Args:
            key: Object key/path

        Returns:
            Binary data of the object

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If download fails
        """
        try:
            # Run blocking MinIO operation in executor
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_object(self.bucket, key)
            )

            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()

        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"Object not found: {key}")
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to download from MinIO: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during download: {e}")

    async def delete(self, key: str) -> bool:
        """Delete an object from MinIO.

        Args:
            key: Object key/path

        Returns:
            True if deletion was successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.remove_object(self.bucket, key)
            )
            return True

        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to delete from MinIO: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during deletion: {e}")

    async def get_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for object access.

        Args:
            key: Object key/path
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL for object access

        Raises:
            StorageError: If URL generation fails
        """
        try:
            # Check if object exists first
            if not await self.exists(key):
                raise FileNotFoundError(f"Object not found: {key}")

            # Generate presigned URL
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.presigned_get_object(
                    bucket_name=self.bucket,
                    object_name=key,
                    expires=timedelta(seconds=expires_in)
                )
            )

            return url

        except FileNotFoundError:
            raise
        except S3Error as e:
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to generate presigned URL: {e}")
        except Exception as e:
            raise StorageError(
                f"Unexpected error during URL generation: {e}"
            )

    async def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[StorageFile]:
        """List objects in MinIO bucket with optional prefix filter.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        try:
            objects = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: list(self.client.list_objects(
                    bucket_name=self.bucket,
                    prefix=prefix or '',
                    recursive=True
                ))
            )

            storage_files = []
            for obj in objects:
                storage_file = StorageFile(
                    key=obj.object_name,
                    size=obj.size,
                    content_type=obj.content_type or 'application/octet-stream',
                    last_modified=obj.last_modified,
                    etag=obj.etag,
                    metadata=obj.metadata
                )
                storage_files.append(storage_file)

            return storage_files

        except S3Error as e:
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to list objects from MinIO: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during listing: {e}")

    async def copy(
        self,
        source_key: str,
        dest_key: str
    ) -> bool:
        """Copy an object within MinIO bucket.

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
            from minio.commonconfig import CopySource

            # Check if source exists
            if not await self.exists(source_key):
                raise FileNotFoundError(f"Source object not found: {source_key}")

            # Perform copy operation
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.copy_object(
                    bucket_name=self.bucket,
                    object_name=dest_key,
                    source=CopySource(self.bucket, source_key)
                )
            )

            return True

        except FileNotFoundError:
            raise
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"Source object not found: {source_key}")
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to copy object in MinIO: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during copy: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists in MinIO bucket.

        Args:
            key: Object key/path

        Returns:
            True if object exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.stat_object(self.bucket, key)
            )
            return True

        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to check object existence: {e}")
        except Exception as e:
            raise StorageError(
                f"Unexpected error during existence check: {e}"
            )

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
            stat = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.stat_object(self.bucket, key)
            )

            return StorageFile(
                key=key,
                size=stat.size,
                content_type=stat.content_type or 'application/octet-stream',
                last_modified=stat.last_modified,
                etag=stat.etag,
                metadata=stat.metadata
            )

        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundError(f"Object not found: {key}")
            if e.code == 'AccessDenied':
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to get object metadata: {e}")
        except Exception as e:
            raise StorageError(
                f"Unexpected error during metadata retrieval: {e}"
            )
