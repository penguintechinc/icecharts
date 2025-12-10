"""Microsoft OneDrive storage provider implementation for IceCharts.

This module provides OneDrive storage support with async operations,
sharing links, and comprehensive error handling using Microsoft Graph API.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

import msal
import requests

from .base import (
    StorageProvider,
    StorageFile,
    StorageError,
    StorageConfigError,
    StorageConnectionError,
    StorageAuthenticationError
)


class OneDriveProvider(StorageProvider):
    """Microsoft OneDrive storage provider implementation.

    Uses Microsoft Graph API for OneDrive operations including upload,
    download, delete, sharing links, and file listing with async patterns.
    """

    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

    def _validate_config(self) -> None:
        """Validate OneDrive configuration.

        Raises:
            StorageConfigError: If required configuration is missing
        """
        required = ['client_id', 'client_secret', 'tenant_id']
        missing = [key for key in required if key not in self.config]

        if missing:
            raise StorageConfigError(
                f"OneDrive configuration missing required fields: {missing}"
            )

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize OneDrive provider.

        Args:
            config: Configuration dictionary with OneDrive settings
        """
        super().__init__(config)

        try:
            # Initialize MSAL confidential client for service authentication
            self.msal_app = msal.ConfidentialClientApplication(
                client_id=self.config['client_id'],
                client_credential=self.config['client_secret'],
                authority=f"https://login.microsoftonline.com/{self.config['tenant_id']}"
            )

            self.folder_path = self.config.get('folder_path', '/')
            self.access_token = None
            self.token_expires = None

            # Acquire initial access token
            self._acquire_token()

        except Exception as e:
            raise StorageConnectionError(
                f"Failed to initialize OneDrive client: {e}"
            )

    def _acquire_token(self) -> None:
        """Acquire or refresh access token for Microsoft Graph API.

        Raises:
            StorageAuthenticationError: If token acquisition fails
        """
        try:
            # Request token with required scopes
            result = self.msal_app.acquire_token_for_client(
                scopes=['https://graph.microsoft.com/.default']
            )

            if 'access_token' in result:
                self.access_token = result['access_token']
                # Token typically expires in 3600 seconds
                expires_in = result.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 60)
            else:
                error_desc = result.get('error_description', 'Unknown error')
                raise StorageAuthenticationError(
                    f"Failed to acquire access token: {error_desc}"
                )

        except Exception as e:
            raise StorageAuthenticationError(
                f"Token acquisition failed: {e}"
            )

    def _ensure_valid_token(self) -> None:
        """Ensure access token is valid, refresh if necessary."""
        if self.token_expires is None or datetime.now() >= self.token_expires:
            self._acquire_token()

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with valid access token.

        Returns:
            Dictionary of HTTP headers
        """
        self._ensure_valid_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def _build_path(self, key: str) -> str:
        """Build full OneDrive path from key.

        Args:
            key: File key/path

        Returns:
            Full OneDrive path
        """
        if self.folder_path == '/':
            return f'/me/drive/root:/{key}'
        return f'/me/drive/root:/{self.folder_path.strip("/")}/{key}'

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload data to OneDrive.

        Args:
            key: File key/path
            data: Binary data to upload
            content_type: MIME type of the data
            metadata: Optional metadata (not fully supported by OneDrive)

        Returns:
            The key of the uploaded file

        Raises:
            StorageError: If upload fails
        """
        try:
            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}:/content"

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': content_type
            }

            # Upload file (use simple upload for files < 4MB)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.put(url, headers=headers, data=data)
            )

            if response.status_code in (200, 201):
                return key
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to upload to OneDrive: {response.status_code} - {response.text}"
                )

        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during upload: {e}")

    async def download(self, key: str) -> bytes:
        """Download data from OneDrive.

        Args:
            key: File key/path

        Returns:
            Binary data of the file

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If download fails
        """
        try:
            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}:/content"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=self._get_headers())
            )

            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                raise FileNotFoundError(f"File not found: {key}")
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to download from OneDrive: {response.status_code}"
                )

        except FileNotFoundError:
            raise
        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during download: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a file from OneDrive.

        Args:
            key: File key/path

        Returns:
            True if deletion was successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.delete(url, headers=self._get_headers())
            )

            if response.status_code == 204:
                return True
            elif response.status_code == 404:
                return False
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to delete from OneDrive: {response.status_code}"
                )

        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during deletion: {e}")

    async def get_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate a sharing link for file access.

        Args:
            key: File key/path
            expires_in: URL expiration time in seconds (OneDrive has limited control)

        Returns:
            Sharing URL for file access

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If URL generation fails
        """
        try:
            # Check if file exists first
            if not await self.exists(key):
                raise FileNotFoundError(f"File not found: {key}")

            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}:/createLink"

            # Create anonymous view-only sharing link
            data = {
                'type': 'view',
                'scope': 'anonymous'
            }

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    headers=self._get_headers(),
                    json=data
                )
            )

            if response.status_code == 201:
                result = response.json()
                return result['link']['webUrl']
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to generate sharing link: {response.status_code}"
                )

        except FileNotFoundError:
            raise
        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during URL generation: {e}")

    async def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[StorageFile]:
        """List files in OneDrive with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        try:
            if prefix:
                path = self._build_path(prefix)
                url = f"{self.GRAPH_API_ENDPOINT}{path}:/children"
            else:
                folder = self.folder_path.strip('/')
                if folder:
                    url = f"{self.GRAPH_API_ENDPOINT}/me/drive/root:/{folder}:/children"
                else:
                    url = f"{self.GRAPH_API_ENDPOINT}/me/drive/root/children"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=self._get_headers())
            )

            if response.status_code == 200:
                result = response.json()
                storage_files = []

                for item in result.get('value', []):
                    # Skip folders
                    if 'folder' in item:
                        continue

                    # Parse last modified time
                    last_modified = datetime.fromisoformat(
                        item['lastModifiedDateTime'].replace('Z', '+00:00')
                    )

                    storage_file = StorageFile(
                        key=item['name'],
                        size=item.get('size', 0),
                        content_type=item.get('file', {}).get('mimeType', 'application/octet-stream'),
                        last_modified=last_modified,
                        etag=item.get('eTag'),
                        metadata={'id': item['id']}
                    )
                    storage_files.append(storage_file)

                return storage_files

            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to list files from OneDrive: {response.status_code}"
                )

        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during listing: {e}")

    async def copy(
        self,
        source_key: str,
        dest_key: str
    ) -> bool:
        """Copy a file within OneDrive.

        Args:
            source_key: Source file key/path
            dest_key: Destination file key/path

        Returns:
            True if copy was successful

        Raises:
            FileNotFoundError: If source file does not exist
            StorageError: If copy fails
        """
        try:
            # Check if source exists
            if not await self.exists(source_key):
                raise FileNotFoundError(f"Source file not found: {source_key}")

            source_path = self._build_path(source_key)
            url = f"{self.GRAPH_API_ENDPOINT}{source_path}:/copy"

            # Determine parent reference for destination
            dest_parts = dest_key.rsplit('/', 1)
            dest_name = dest_parts[-1]

            data = {
                'name': dest_name
            }

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    headers=self._get_headers(),
                    json=data
                )
            )

            # Copy operation is asynchronous, returns 202 Accepted
            if response.status_code == 202:
                return True
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to copy file in OneDrive: {response.status_code}"
                )

        except FileNotFoundError:
            raise
        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during copy: {e}")

    async def exists(self, key: str) -> bool:
        """Check if a file exists in OneDrive.

        Args:
            key: File key/path

        Returns:
            True if file exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        try:
            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=self._get_headers())
            )

            return response.status_code == 200

        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during existence check: {e}")

    async def get_metadata(self, key: str) -> StorageFile:
        """Get metadata for a file without downloading it.

        Args:
            key: File key/path

        Returns:
            StorageFile object with metadata

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If metadata retrieval fails
        """
        try:
            path = self._build_path(key)
            url = f"{self.GRAPH_API_ENDPOINT}{path}"

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(url, headers=self._get_headers())
            )

            if response.status_code == 200:
                item = response.json()

                # Parse last modified time
                last_modified = datetime.fromisoformat(
                    item['lastModifiedDateTime'].replace('Z', '+00:00')
                )

                return StorageFile(
                    key=key,
                    size=item.get('size', 0),
                    content_type=item.get('file', {}).get('mimeType', 'application/octet-stream'),
                    last_modified=last_modified,
                    etag=item.get('eTag'),
                    metadata={'id': item['id']}
                )

            elif response.status_code == 404:
                raise FileNotFoundError(f"File not found: {key}")
            elif response.status_code == 401:
                raise StorageAuthenticationError("Access token expired or invalid")
            else:
                raise StorageError(
                    f"Failed to get file metadata: {response.status_code}"
                )

        except FileNotFoundError:
            raise
        except StorageAuthenticationError:
            raise
        except Exception as e:
            raise StorageError(f"Unexpected error during metadata retrieval: {e}")
