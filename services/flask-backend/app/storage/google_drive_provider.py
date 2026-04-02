"""Google Drive storage provider implementation for IceCharts.

This module provides Google Drive storage support with async operations,
sharing links, and comprehensive error handling using Google Drive API.
"""

import asyncio
import io
import os.path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .base import (StorageAuthenticationError, StorageConfigError,
                   StorageConnectionError, StorageError, StorageFile,
                   StorageProvider)


class GoogleDriveProvider(StorageProvider):
    """Google Drive storage provider implementation.

    Uses Google Drive API v3 for operations including upload, download,
    delete, sharing links, and file listing with async patterns.
    """

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def _validate_config(self) -> None:
        """Validate Google Drive configuration.

        Raises:
            StorageConfigError: If required configuration is missing
        """
        required = ["credentials_path", "token_path"]
        missing = [key for key in required if key not in self.config]

        if missing:
            raise StorageConfigError(
                f"Google Drive configuration missing required fields: {missing}"
            )

        if not os.path.exists(self.config["credentials_path"]):
            raise StorageConfigError(
                f"Credentials file not found: {self.config['credentials_path']}"
            )

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Google Drive provider.

        Args:
            config: Configuration dictionary with Google Drive settings
        """
        super().__init__(config)

        try:
            # Load or create credentials
            self.creds = self._get_credentials()

            # Build Drive API service
            self.service = build("drive", "v3", credentials=self.creds)

            # Optional root folder ID
            self.folder_id = self.config.get("folder_id")

            # Verify connection
            self._verify_connection()

        except Exception as e:
            raise StorageConnectionError(
                f"Failed to initialize Google Drive client: {e}"
            )

    def _get_credentials(self) -> Credentials:
        """Get or refresh OAuth2 credentials.

        Returns:
            Valid OAuth2 credentials

        Raises:
            StorageAuthenticationError: If authentication fails
        """
        creds = None
        token_path = self.config["token_path"]
        credentials_path = self.config["credentials_path"]

        # Load existing token if available
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            except Exception as e:
                raise StorageAuthenticationError(f"Failed to load credentials: {e}")

        # Refresh or obtain new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    raise StorageAuthenticationError(
                        f"Failed to refresh credentials: {e}"
                    )
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise StorageAuthenticationError(
                        f"Failed to obtain new credentials: {e}"
                    )

            # Save credentials for future use
            try:
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
            except Exception as e:
                # Non-fatal error, log but continue
                print(f"Warning: Failed to save token: {e}")

        return creds

    def _verify_connection(self) -> None:
        """Verify connection to Google Drive."""
        try:
            # Try to get user information
            about = self.service.about().get(fields="user").execute()
            if not about:
                raise StorageConnectionError("Failed to verify Drive connection")
        except HttpError as e:
            if e.resp.status == 401:
                raise StorageAuthenticationError(
                    "Authentication failed: Invalid credentials"
                )
            raise StorageConnectionError(f"Failed to verify Drive connection: {e}")

    def _get_parent_folder(self) -> Optional[str]:
        """Get parent folder ID for file operations.

        Returns:
            Folder ID or None for root
        """
        return self.folder_id

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload data to Google Drive.

        Args:
            key: File name/path
            data: Binary data to upload
            content_type: MIME type of the data
            metadata: Optional metadata (stored as properties)

        Returns:
            The key/file ID of the uploaded file

        Raises:
            StorageError: If upload fails
        """
        try:
            file_metadata = {"name": key}

            # Set parent folder if configured
            parent_folder = self._get_parent_folder()
            if parent_folder:
                file_metadata["parents"] = [parent_folder]

            # Add custom properties if metadata provided
            if metadata:
                file_metadata["properties"] = metadata

            # Create media upload
            media = MediaIoBaseUpload(
                io.BytesIO(data), mimetype=content_type, resumable=True
            )

            # Upload file
            file = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .create(body=file_metadata, media_body=media, fields="id,name")
                .execute(),
            )

            return file.get("name", key)

        except HttpError as e:
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to upload to Google Drive: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during upload: {e}")

    async def download(self, key: str) -> bytes:
        """Download data from Google Drive.

        Args:
            key: File name/path

        Returns:
            Binary data of the file

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If download fails
        """
        try:
            # Find file by name
            file_id = await self._get_file_id(key)
            if not file_id:
                raise FileNotFoundError(f"File not found: {key}")

            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_stream = io.BytesIO()
            downloader = MediaIoBaseDownload(file_stream, request)

            done = False
            while not done:
                _, done = await asyncio.get_event_loop().run_in_executor(
                    None, downloader.next_chunk
                )

            return file_stream.getvalue()

        except FileNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 404:
                raise FileNotFoundError(f"File not found: {key}")
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to download from Google Drive: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during download: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a file from Google Drive.

        Args:
            key: File name/path

        Returns:
            True if deletion was successful

        Raises:
            StorageError: If deletion fails
        """
        try:
            # Find file by name
            file_id = await self._get_file_id(key)
            if not file_id:
                return False

            # Delete file
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.service.files().delete(fileId=file_id).execute()
            )

            return True

        except HttpError as e:
            if e.resp.status == 404:
                return False
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to delete from Google Drive: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during deletion: {e}")

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a sharing link for file access.

        Args:
            key: File name/path
            expires_in: URL expiration time (not directly supported by Drive)

        Returns:
            Sharing URL for file access

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If URL generation fails
        """
        try:
            # Find file by name
            file_id = await self._get_file_id(key)
            if not file_id:
                raise FileNotFoundError(f"File not found: {key}")

            # Create permission for anyone with link
            permission = {"type": "anyone", "role": "reader"}

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.permissions()
                .create(fileId=file_id, body=permission)
                .execute(),
            )

            # Get shareable link
            file = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .get(fileId=file_id, fields="webViewLink")
                .execute(),
            )

            return file.get("webViewLink", "")

        except FileNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 404:
                raise FileNotFoundError(f"File not found: {key}")
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to generate sharing link: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during URL generation: {e}")

    async def list_files(self, prefix: Optional[str] = None) -> List[StorageFile]:
        """List files in Google Drive with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of StorageFile objects

        Raises:
            StorageError: If listing fails
        """
        try:
            # Build query
            query_parts = ["trashed=false"]

            parent_folder = self._get_parent_folder()
            if parent_folder:
                query_parts.append(f"'{parent_folder}' in parents")

            if prefix:
                query_parts.append(f"name contains '{prefix}'")

            query = " and ".join(query_parts)

            # List files
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .list(
                    q=query,
                    fields="files(id, name, size, mimeType, modifiedTime, md5Checksum, properties)",
                    pageSize=100,
                )
                .execute(),
            )

            files = results.get("files", [])
            storage_files = []

            for file in files:
                # Skip folders
                if file["mimeType"] == "application/vnd.google-apps.folder":
                    continue

                # Parse modified time
                modified_time = datetime.fromisoformat(
                    file["modifiedTime"].replace("Z", "+00:00")
                )

                storage_file = StorageFile(
                    key=file["name"],
                    size=int(file.get("size", 0)),
                    content_type=file.get("mimeType", "application/octet-stream"),
                    last_modified=modified_time,
                    etag=file.get("md5Checksum"),
                    metadata=file.get("properties"),
                )
                storage_files.append(storage_file)

            return storage_files

        except HttpError as e:
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to list files from Google Drive: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during listing: {e}")

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Copy a file within Google Drive.

        Args:
            source_key: Source file name/path
            dest_key: Destination file name/path

        Returns:
            True if copy was successful

        Raises:
            FileNotFoundError: If source file does not exist
            StorageError: If copy fails
        """
        try:
            # Find source file
            source_id = await self._get_file_id(source_key)
            if not source_id:
                raise FileNotFoundError(f"Source file not found: {source_key}")

            # Copy file
            file_metadata = {"name": dest_key}

            parent_folder = self._get_parent_folder()
            if parent_folder:
                file_metadata["parents"] = [parent_folder]

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .copy(fileId=source_id, body=file_metadata)
                .execute(),
            )

            return True

        except FileNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 404:
                raise FileNotFoundError(f"Source file not found: {source_key}")
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to copy file in Google Drive: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during copy: {e}")

    async def exists(self, key: str) -> bool:
        """Check if a file exists in Google Drive.

        Args:
            key: File name/path

        Returns:
            True if file exists, False otherwise

        Raises:
            StorageError: If existence check fails
        """
        try:
            file_id = await self._get_file_id(key)
            return file_id is not None

        except HttpError as e:
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Unexpected error during existence check: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during existence check: {e}")

    async def get_metadata(self, key: str) -> StorageFile:
        """Get metadata for a file without downloading it.

        Args:
            key: File name/path

        Returns:
            StorageFile object with metadata

        Raises:
            FileNotFoundError: If file does not exist
            StorageError: If metadata retrieval fails
        """
        try:
            # Find file by name
            file_id = await self._get_file_id(key)
            if not file_id:
                raise FileNotFoundError(f"File not found: {key}")

            # Get file metadata
            file = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .get(
                    fileId=file_id,
                    fields="name, size, mimeType, modifiedTime, md5Checksum, properties",
                )
                .execute(),
            )

            # Parse modified time
            modified_time = datetime.fromisoformat(
                file["modifiedTime"].replace("Z", "+00:00")
            )

            return StorageFile(
                key=file["name"],
                size=int(file.get("size", 0)),
                content_type=file.get("mimeType", "application/octet-stream"),
                last_modified=modified_time,
                etag=file.get("md5Checksum"),
                metadata=file.get("properties"),
            )

        except FileNotFoundError:
            raise
        except HttpError as e:
            if e.resp.status == 404:
                raise FileNotFoundError(f"File not found: {key}")
            if e.resp.status == 401:
                raise StorageAuthenticationError("Authentication failed")
            raise StorageError(f"Failed to get file metadata: {e}")
        except Exception as e:
            raise StorageError(f"Unexpected error during metadata retrieval: {e}")

    async def _get_file_id(self, key: str) -> Optional[str]:
        """Get file ID by name.

        Args:
            key: File name

        Returns:
            File ID or None if not found
        """
        try:
            # Build query to find file by name
            query_parts = [f"name = '{key}'", "trashed = false"]

            parent_folder = self._get_parent_folder()
            if parent_folder:
                query_parts.append(f"'{parent_folder}' in parents")

            query = " and ".join(query_parts)

            # Search for file
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.service.files()
                .list(q=query, fields="files(id)", pageSize=1)
                .execute(),
            )

            files = results.get("files", [])
            return files[0]["id"] if files else None

        except Exception:
            return None
