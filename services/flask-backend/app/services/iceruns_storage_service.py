"""IceRuns storage service for function packages and artifacts.

This module provides S3-compatible storage for IceRuns function packages,
execution logs, and artifacts. Supports multi-language function packages and
version history.

Supports any S3-compatible storage provider:
- MinIO (development/testing)
- AWS S3 (production)
- Google Cloud Storage
- Azure Blob Storage (via S3 API)
"""

import asyncio
import hashlib
import os
from typing import Optional

from flask import current_app


class IceRunsStorageService:
    """Service for storing and retrieving IceRuns function packages and artifacts."""

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
                        "endpoint": os.getenv("MINIO_ENDPOINT")
                        or os.getenv("STORAGE_ENDPOINT", "minio:9000"),
                        "access_key": os.getenv("MINIO_ACCESS_KEY")
                        or os.getenv("STORAGE_ACCESS_KEY", "minioadmin"),
                        "secret_key": os.getenv("MINIO_SECRET_KEY")
                        or os.getenv("STORAGE_SECRET_KEY", "minioadmin"),
                        "bucket": os.getenv("MINIO_BUCKET")
                        or os.getenv("STORAGE_BUCKET", "icecharts"),
                        "secure": (
                            os.getenv("MINIO_SECURE")
                            or os.getenv("STORAGE_SECURE", "false")
                        ).lower()
                        == "true",
                    }
                    if provider_type == "s3":
                        config["region"] = os.getenv("STORAGE_REGION", "us-east-1")
                else:
                    # Let the storage factory handle other providers from env
                    config = None

                cls._provider = get_storage_provider(provider_type, config)
                cls._initialized = True
                current_app.logger.info(
                    f"Initialized storage provider for IceRuns: {provider_type}"
                )

            except Exception as e:
                current_app.logger.error(f"Failed to initialize IceRuns storage: {e}")
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

    @staticmethod
    def _calculate_sha256(data: bytes) -> str:
        """Calculate SHA256 hash of data.

        Args:
            data: Binary data to hash

        Returns:
            Hex string of SHA256 hash
        """
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def save_package(
        cls,
        function_id: str,
        file_stream,
        filename: str,
    ) -> dict:
        """Upload function package to S3.

        Supports various package formats:
        - .zip: Universal format for all runtimes
        - .tar.gz: Unix-based runtimes
        - Single files: .py, .js, .go, .rb, .sh, .ps1, .rs

        Args:
            function_id: Unique function identifier (UUID format)
            file_stream: File-like object with package data
            filename: Original filename (used for extension detection)

        Returns:
            Dict with:
            - package_key: S3 key where package is stored
            - size: Package size in bytes
            - hash: SHA256 hash of package
            - content_type: MIME type of package

        Raises:
            RuntimeError: If storage fails
            ValueError: If file format is not supported
        """
        try:
            provider = cls._get_provider()

            # Read file data
            if hasattr(file_stream, "read"):
                file_data = file_stream.read()
                if isinstance(file_data, str):
                    file_data = file_data.encode("utf-8")
            else:
                file_data = file_stream

            # Validate and detect format
            supported_extensions = {
                ".zip",
                ".tar.gz",
                ".tgz",
                ".py",
                ".js",
                ".go",
                ".rb",
                ".sh",
                ".ps1",
                ".rs",
            }
            file_ext = None
            for ext in supported_extensions:
                if filename.lower().endswith(ext):
                    file_ext = ext
                    break

            if not file_ext:
                raise ValueError(
                    f"Unsupported package format: {filename}. "
                    f"Supported: {', '.join(sorted(supported_extensions))}"
                )

            # Calculate hash before upload
            package_hash = cls._calculate_sha256(file_data)

            # Determine content type
            content_type_map = {
                ".zip": "application/zip",
                ".tar.gz": "application/gzip",
                ".tgz": "application/gzip",
                ".py": "text/x-python",
                ".js": "application/javascript",
                ".go": "text/x-go",
                ".rb": "text/x-ruby",
                ".sh": "application/x-sh",
                ".ps1": "application/x-powershell",
                ".rs": "text/x-rust",
            }
            content_type = content_type_map.get(file_ext, "application/octet-stream")

            # Generate S3 key
            package_key = f"iceruns/{function_id}/package{file_ext}"

            # Upload to storage
            cls._run_async(
                provider.upload(
                    key=package_key,
                    data=file_data,
                    content_type=content_type,
                    metadata={
                        "function_id": function_id,
                        "original_filename": filename,
                        "package_hash": package_hash,
                    },
                )
            )

            current_app.logger.info(
                f"Uploaded IceRuns package for function {function_id}: {package_key} "
                f"(size: {len(file_data)} bytes, hash: {package_hash})"
            )

            return {
                "package_key": package_key,
                "size": len(file_data),
                "hash": package_hash,
                "content_type": content_type,
            }

        except ValueError as e:
            current_app.logger.error(f"Invalid package format: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Failed to save IceRuns package: {e}")
            raise RuntimeError(f"Failed to save function package: {e}")

    @classmethod
    def load_package(cls, function_id: str) -> bytes:
        """Download function package from S3.

        Args:
            function_id: Unique function identifier

        Returns:
            Binary package data

        Raises:
            FileNotFoundError: If package not found
            RuntimeError: If download fails
        """
        try:
            provider = cls._get_provider()

            # List files to find the package (could be .zip, .tar.gz, or single file)
            prefix = f"iceruns/{function_id}/package"
            files = cls._run_async(provider.list_files(prefix=prefix))

            if not files:
                raise FileNotFoundError(
                    f"Package not found for function {function_id}"
                )

            # Get the package file (should be only one)
            package_key = files[0].key

            # Download
            data = cls._run_async(provider.download(package_key))

            current_app.logger.info(
                f"Downloaded IceRuns package for function {function_id}: {package_key}"
            )
            return data

        except FileNotFoundError:
            current_app.logger.warning(f"Package not found for function {function_id}")
            raise
        except Exception as e:
            current_app.logger.error(f"Failed to load IceRuns package: {e}")
            raise RuntimeError(f"Failed to load function package: {e}")

    @classmethod
    def delete_package(cls, function_id: str) -> bool:
        """Delete function package from S3.

        Args:
            function_id: Unique function identifier

        Returns:
            True if deleted successfully, False if not found

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            provider = cls._get_provider()

            # Find and delete the package file
            prefix = f"iceruns/{function_id}/package"
            files = cls._run_async(provider.list_files(prefix=prefix))

            if not files:
                current_app.logger.warning(f"Package not found for deletion: {function_id}")
                return False

            # Delete the package file
            package_key = files[0].key
            result = cls._run_async(provider.delete(package_key))

            current_app.logger.info(
                f"Deleted IceRuns package for function {function_id}: {package_key}"
            )
            return result

        except Exception as e:
            current_app.logger.error(f"Failed to delete IceRuns package: {e}")
            raise RuntimeError(f"Failed to delete function package: {e}")

    @classmethod
    def save_execution_logs(cls, execution_id: str, logs: str) -> str:
        """Upload full execution logs to S3.

        Logs are stored as plain text for readability and searchability.
        Format: iceruns/logs/{execution_id}.log

        Args:
            execution_id: Unique execution identifier (UUID format)
            logs: Combined stdout and stderr as string

        Returns:
            S3 key where logs were stored

        Raises:
            RuntimeError: If storage fails
        """
        try:
            provider = cls._get_provider()

            # Convert logs to bytes
            logs_bytes = logs.encode("utf-8")

            # Generate S3 key
            logs_key = f"iceruns/logs/{execution_id}.log"

            # Upload to storage
            cls._run_async(
                provider.upload(
                    key=logs_key,
                    data=logs_bytes,
                    content_type="text/plain",
                    metadata={
                        "execution_id": execution_id,
                        "size_bytes": str(len(logs_bytes)),
                    },
                )
            )

            current_app.logger.info(
                f"Saved execution logs for {execution_id}: {logs_key} "
                f"(size: {len(logs_bytes)} bytes)"
            )
            return logs_key

        except Exception as e:
            current_app.logger.error(f"Failed to save execution logs: {e}")
            raise RuntimeError(f"Failed to save execution logs: {e}")

    @classmethod
    def load_execution_logs(cls, execution_id: str) -> str:
        """Download execution logs from S3.

        Args:
            execution_id: Unique execution identifier

        Returns:
            Log content as string (stdout + stderr)

        Raises:
            FileNotFoundError: If logs not found
            RuntimeError: If download fails
        """
        try:
            provider = cls._get_provider()
            logs_key = f"iceruns/logs/{execution_id}.log"

            # Check if exists
            exists = cls._run_async(provider.exists(logs_key))
            if not exists:
                raise FileNotFoundError(f"Logs not found for execution {execution_id}")

            # Download
            data = cls._run_async(provider.download(logs_key))
            logs_content = data.decode("utf-8")

            current_app.logger.info(
                f"Loaded execution logs for {execution_id}: {logs_key}"
            )
            return logs_content

        except FileNotFoundError:
            current_app.logger.warning(f"Logs not found for execution {execution_id}")
            raise
        except Exception as e:
            current_app.logger.error(f"Failed to load execution logs: {e}")
            raise RuntimeError(f"Failed to load execution logs: {e}")

    @classmethod
    def save_artifacts(cls, execution_id: str, artifacts: dict) -> str:
        """Upload function output artifacts to S3.

        Artifacts are stored as individual files under a base path:
        iceruns/artifacts/{execution_id}/{filename}

        Supports multiple artifact files. Each artifact in the dict should be:
        - key: filename (string)
        - value: binary data (bytes) or string

        Args:
            execution_id: Unique execution identifier
            artifacts: Dict mapping filenames to binary data or strings

        Returns:
            Base S3 key path (iceruns/artifacts/{execution_id})

        Raises:
            RuntimeError: If storage fails
            TypeError: If artifacts value is invalid type
        """
        try:
            provider = cls._get_provider()

            if not artifacts or not isinstance(artifacts, dict):
                current_app.logger.debug(
                    f"No artifacts to save for execution {execution_id}"
                )
                return None

            base_path = f"iceruns/artifacts/{execution_id}"
            uploaded_count = 0

            for filename, data in artifacts.items():
                # Validate and convert data
                if isinstance(data, str):
                    file_data = data.encode("utf-8")
                    content_type = "text/plain"
                elif isinstance(data, bytes):
                    file_data = data
                    content_type = "application/octet-stream"
                else:
                    raise TypeError(
                        f"Artifact {filename} has invalid type: {type(data)}. "
                        f"Expected bytes or str."
                    )

                # Sanitize filename
                safe_filename = filename.replace("/", "_").replace("\\", "_")

                # Generate artifact key
                artifact_key = f"{base_path}/{safe_filename}"

                # Upload
                cls._run_async(
                    provider.upload(
                        key=artifact_key,
                        data=file_data,
                        content_type=content_type,
                        metadata={
                            "execution_id": execution_id,
                            "original_filename": filename,
                        },
                    )
                )

                uploaded_count += 1

            current_app.logger.info(
                f"Saved {uploaded_count} artifacts for execution {execution_id}: {base_path}"
            )
            return base_path

        except TypeError as e:
            current_app.logger.error(f"Invalid artifact data type: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Failed to save execution artifacts: {e}")
            raise RuntimeError(f"Failed to save execution artifacts: {e}")

    @classmethod
    def get_package_url(cls, function_id: str, expires_in: int = 3600) -> Optional[str]:
        """Generate presigned URL for function package download.

        URL is valid for the specified duration (default 1 hour).
        Use for direct downloads or sharing with external systems.

        Args:
            function_id: Unique function identifier
            expires_in: URL expiration time in seconds (default: 3600 = 1 hour)

        Returns:
            Presigned URL or None if package not found

        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            provider = cls._get_provider()

            # Find the package file
            prefix = f"iceruns/{function_id}/package"
            files = cls._run_async(provider.list_files(prefix=prefix))

            if not files:
                current_app.logger.debug(f"Package not found for function {function_id}")
                return None

            package_key = files[0].key

            # Generate presigned URL
            url = cls._run_async(provider.get_url(package_key, expires_in=expires_in))

            current_app.logger.debug(
                f"Generated presigned URL for package {function_id}: expires in {expires_in}s"
            )
            return url

        except Exception as e:
            current_app.logger.error(f"Failed to get package presigned URL: {e}")
            raise RuntimeError(f"Failed to generate package URL: {e}")

    @classmethod
    def get_artifact_url(
        cls, execution_id: str, artifact_path: str, expires_in: int = 3600
    ) -> Optional[str]:
        """Generate presigned URL for artifact download.

        URL is valid for the specified duration (default 1 hour).

        Args:
            execution_id: Unique execution identifier
            artifact_path: Relative path within artifacts directory
                          (e.g., "output.json", "results/report.pdf")
            expires_in: URL expiration time in seconds (default: 3600 = 1 hour)

        Returns:
            Presigned URL or None if artifact not found

        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            provider = cls._get_provider()

            # Sanitize artifact path
            safe_path = artifact_path.replace("\\", "/")

            # Build full artifact key
            artifact_key = f"iceruns/artifacts/{execution_id}/{safe_path}"

            # Check if exists
            exists = cls._run_async(provider.exists(artifact_key))
            if not exists:
                current_app.logger.debug(
                    f"Artifact not found: {artifact_key}"
                )
                return None

            # Generate presigned URL
            url = cls._run_async(provider.get_url(artifact_key, expires_in=expires_in))

            current_app.logger.debug(
                f"Generated presigned URL for artifact {artifact_key}: expires in {expires_in}s"
            )
            return url

        except Exception as e:
            current_app.logger.error(f"Failed to get artifact presigned URL: {e}")
            raise RuntimeError(f"Failed to generate artifact URL: {e}")

    @classmethod
    def list_artifacts(cls, execution_id: str) -> list[dict]:
        """List all artifacts for an execution.

        Args:
            execution_id: Unique execution identifier

        Returns:
            List of artifact info dicts with:
            - key: Full S3 key
            - filename: Artifact filename
            - size: File size in bytes
            - modified: Last modification timestamp

        Raises:
            RuntimeError: If listing fails
        """
        try:
            provider = cls._get_provider()
            prefix = f"iceruns/artifacts/{execution_id}/"

            files = cls._run_async(provider.list_files(prefix=prefix))

            artifacts = []
            for f in files:
                # Extract filename from key
                filename = f.key.split("/")[-1]
                artifacts.append(
                    {
                        "key": f.key,
                        "filename": filename,
                        "size": f.size,
                        "modified": f.last_modified.isoformat() if f.last_modified else None,
                    }
                )

            current_app.logger.debug(
                f"Listed {len(artifacts)} artifacts for execution {execution_id}"
            )
            return artifacts

        except Exception as e:
            current_app.logger.error(f"Failed to list execution artifacts: {e}")
            raise RuntimeError(f"Failed to list execution artifacts: {e}")

    @classmethod
    def delete_execution_artifacts(cls, execution_id: str) -> bool:
        """Delete all artifacts for an execution.

        Args:
            execution_id: Unique execution identifier

        Returns:
            True if deletion successful or no artifacts found

        Raises:
            RuntimeError: If deletion fails
        """
        try:
            provider = cls._get_provider()
            prefix = f"iceruns/artifacts/{execution_id}/"

            files = cls._run_async(provider.list_files(prefix=prefix))

            if not files:
                current_app.logger.debug(f"No artifacts to delete for execution {execution_id}")
                return True

            # Delete all artifact files
            for f in files:
                cls._run_async(provider.delete(f.key))

            current_app.logger.info(
                f"Deleted {len(files)} artifacts for execution {execution_id}"
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to delete execution artifacts: {e}")
            raise RuntimeError(f"Failed to delete execution artifacts: {e}")

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
