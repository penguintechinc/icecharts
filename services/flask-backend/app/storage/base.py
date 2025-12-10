"""Base storage provider abstract class for IceCharts.

This module defines the abstract base class for all storage providers,
including the StorageFile dataclass and common storage operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass(slots=True, frozen=True)
class StorageFile:
    """Represents a file in storage with metadata.

    Attributes:
        key: Unique identifier/path for the file
        size: File size in bytes
        content_type: MIME type of the file
        last_modified: Timestamp of last modification
        etag: Entity tag for cache validation
        metadata: Additional provider-specific metadata
    """
    key: str
    size: int
    content_type: str
    last_modified: datetime
    etag: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StorageProvider(ABC):
    """Abstract base class for storage providers.

    All storage provider implementations must inherit from this class
    and implement the required methods. Providers should support
    async/await patterns and handle errors gracefully.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize storage provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        pass

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload data to storage.

        Args:
            key: Unique identifier/path for the file
            data: Binary data to upload
            content_type: MIME type of the data
            metadata: Optional metadata key-value pairs

        Returns:
            The key/identifier of the uploaded file

        Raises:
            StorageError: If upload fails
        """
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download data from storage.

        Args:
            key: Unique identifier/path for the file

        Returns:
            Binary data of the file

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If download fails
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a file from storage.

        Args:
            key: Unique identifier/path for the file

        Returns:
            True if deletion was successful, False otherwise

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate a presigned URL for file access.

        Args:
            key: Unique identifier/path for the file
            expires_in: URL expiration time in seconds (default: 3600)

        Returns:
            Presigned URL for file access

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If URL generation fails
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[StorageFile]:
        """List files in storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    async def copy(
        self,
        source_key: str,
        dest_key: str
    ) -> bool:
        """Copy a file within storage.

        Args:
            source_key: Source file identifier/path
            dest_key: Destination file identifier/path

        Returns:
            True if copy was successful, False otherwise

        Raises:
            FileNotFoundError: If source file does not exist
            StorageError: If copy fails
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists in storage.

        Args:
            key: Unique identifier/path for the file

        Returns:
            True if file exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> StorageFile:
        """Get metadata for a file without downloading it.

        Args:
            key: Unique identifier/path for the file

        Returns:
            StorageFile object with metadata

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If metadata retrieval fails
        """
        pass


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class StorageConfigError(StorageError):
    """Exception for configuration-related errors."""
    pass


class StorageConnectionError(StorageError):
    """Exception for connection-related errors."""
    pass


class StorageAuthenticationError(StorageError):
    """Exception for authentication-related errors."""
    pass
