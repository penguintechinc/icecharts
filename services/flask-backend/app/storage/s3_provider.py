"""AWS S3 storage provider implementation for IceCharts.

This module provides AWS S3 object storage support with async operations,
presigned URLs, and comprehensive error handling.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from .base import (
    StorageAuthenticationError,
    StorageConfigError,
    StorageConnectionError,
    StorageError,
    StorageFile,
    StorageProvider,
)


class S3Provider(StorageProvider):
    """AWS S3 storage provider implementation.

    Supports all standard S3 operations including upload, download,
    delete, presigned URLs, and file listing with async/await patterns.
    """

    def _validate_config(self) -> None:
        """Validate S3 configuration.

        Raises:
            StorageConfigError: If required configuration is missing
        """
        required = ["access_key", "secret_key", "bucket"]
        missing = [key for key in required if key not in self.config]

        if missing:
            raise StorageConfigError(
                f"S3 configuration missing required fields: {missing}"
            )

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize S3 provider.

        Args:
            config: Configuration dictionary with S3 settings
        """
        super().__init__(config)

        try:
            # Initialize S3 client
            session = boto3.Session(
                aws_access_key_id=self.config["access_key"],
                aws_secret_access_key=self.config["secret_key"],
                region_name=self.config.get("region", "us-east-1"),
            )

            self.client = session.client("s3")
            self.bucket = self.config["bucket"]

            # Verify credentials and bucket access
            self._verify_connection()

        except (NoCredentialsError, PartialCredentialsError) as e:
            raise StorageAuthenticationError(f"Invalid AWS credentials: {e}")
        except Exception as e:
            raise StorageConnectionError(f"Failed to initialize S3 client: {e}")

    def _verify_connection(self) -> None:
        """Verify connection to S3 and bucket access."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise StorageConfigError(f"Bucket does not exist: {self.bucket}")
            elif error_code == "403":
                raise StorageAuthenticationError(
                    f"Access denied to bucket: {self.bucket}"
                )
            raise StorageConnectionError(f"Failed to verify bucket access: {e}")

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload data to S3.

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
            extra_args = {"ContentType": content_type}

            if metadata:
                extra_args["Metadata"] = metadata

            # Run blocking S3 operation in executor
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.bucket, Key=key, Body=data, **extra_args
                ),
            )

            return key

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to upload to S3: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during upload: {e}")

    async def download(self, key: str) -> bytes:
        """Download data from S3.

        Args:
            key: Object key/path

        Returns:
            Binary data of the object

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If download fails
        """
        try:
            # Run blocking S3 operation in executor
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_object(Bucket=self.bucket, Key=key)
            )

            return response["Body"].read()

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {key}")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to download from S3: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during download: {e}")

    async def delete(self, key: str) -> bool:
        """Delete an object from S3.

        Args:
            key: Object key/path

        Returns:
            True if deletion was successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.delete_object(Bucket=self.bucket, Key=key)
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                return False
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to delete from S3: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during deletion: {e}")

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for object access.

        Args:
            key: Object key/path
            expires_in: URL expiration time in seconds

        Returns:
            Presigned URL for object access

        Raises:
            FileNotFoundError: If object does not exist
            StorageError: If URL generation fails
        """
        try:
            # Check if object exists first
            if not await self.exists(key):
                raise FileNotFoundError(f"Object not found: {key}")

            # Generate presigned URL
            url = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket, "Key": key},
                    ExpiresIn=expires_in,
                ),
            )

            return url

        except FileNotFoundError:
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to generate presigned URL: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during URL generation: {e}")

    async def list_files(self, prefix: Optional[str] = None) -> List[StorageFile]:
        """List objects in S3 bucket with optional prefix filter.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        try:
            storage_files = []
            continuation_token = None

            while True:
                # Build list_objects_v2 parameters
                params = {"Bucket": self.bucket, "MaxKeys": 1000}

                if prefix:
                    params["Prefix"] = prefix

                if continuation_token:
                    params["ContinuationToken"] = continuation_token

                # Run blocking S3 operation in executor
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.client.list_objects_v2(**params)
                )

                # Process objects in response
                for obj in response.get("Contents", []):
                    # Get metadata for content type
                    metadata = await self.get_metadata(obj["Key"])
                    storage_files.append(metadata)

                # Check if there are more objects to fetch
                if not response.get("IsTruncated", False):
                    break

                continuation_token = response.get("NextContinuationToken")

            return storage_files

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to list objects from S3: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during listing: {e}")

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Copy an object within S3 bucket.

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

            # Perform copy operation
            copy_source = {"Bucket": self.bucket, "Key": source_key}

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.copy_object(
                    Bucket=self.bucket, Key=dest_key, CopySource=copy_source
                ),
            )

            return True

        except FileNotFoundError:
            raise
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"Source object not found: {source_key}")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to copy object in S3: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during copy: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists in S3 bucket.

        Args:
            key: Object key/path

        Returns:
            True if object exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.head_object(Bucket=self.bucket, Key=key)
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                return False
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to check object existence: {e}")
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
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.head_object(Bucket=self.bucket, Key=key)
            )

            return StorageFile(
                key=key,
                size=response["ContentLength"],
                content_type=response.get("ContentType", "application/octet-stream"),
                last_modified=response["LastModified"],
                etag=response.get("ETag", "").strip('"'),
                metadata=response.get("Metadata"),
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"Object not found: {key}")
            if error_code == "AccessDenied":
                raise StorageAuthenticationError(f"Access denied: {e}")
            raise StorageError(f"Failed to get object metadata: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during metadata retrieval: {e}")
