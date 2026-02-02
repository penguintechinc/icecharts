"""Drawing content and version management service for IceCharts."""

import datetime
import json
from dataclasses import dataclass
from typing import Optional

from app.models import get_db
from app.services.permission_service import PermissionService
from app.storage import StorageError, get_storage_provider


@dataclass(slots=True)
class VersionData:
    """Data class for version information."""

    id: int
    drawing_id: int
    version_number: int
    created_by_id: int
    change_summary: Optional[str]
    storage_path: str
    created_at: datetime.datetime


class ContentService:
    """Service for managing drawing content and versions."""

    @staticmethod
    def _get_storage_path(tenant_id: int, drawing_id: int, version: int) -> str:
        """
        Generate storage path for drawing content.

        Args:
            tenant_id: Tenant ID
            drawing_id: Drawing ID
            version: Version number

        Returns:
            Storage path string
        """
        return f"tenants/{tenant_id}/drawings/{drawing_id}/versions/v{version}.json"

    @staticmethod
    def save_content(
        drawing_id: int,
        content_json: dict,
        user_id: int,
        change_summary: Optional[str] = None,
    ) -> int:
        """
        Save drawing content and create a new version.

        Args:
            drawing_id: ID of the drawing
            content_json: Drawing content as JSON dictionary
            user_id: ID of the user saving the content
            change_summary: Optional description of changes

        Returns:
            New version number

        Raises:
            PermissionError: If user doesn't have edit permission
            ValueError: If save fails or drawing not found
            StorageError: If storage operation fails
        """
        db = get_db()

        # Check if drawing exists
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            raise ValueError("Drawing not found")

        # Check edit permission
        if not PermissionService.can_edit_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to edit this drawing")

        # Validate content
        if not content_json or not isinstance(content_json, dict):
            raise ValueError("Content must be a valid JSON dictionary")

        try:
            # Get next version number
            latest_version = (
                db(db.drawing_versions.drawing_id == drawing_id)
                .select(
                    db.drawing_versions.version_number,
                    orderby=~db.drawing_versions.version_number,
                    limitby=(0, 1),
                )
                .first()
            )

            next_version = (latest_version.version_number + 1) if latest_version else 1

            # Generate storage path
            storage_path = ContentService._get_storage_path(
                drawing.tenant_id, drawing_id, next_version
            )

            # Save content to storage
            try:
                storage = get_storage_provider()
                content_bytes = json.dumps(content_json, indent=2).encode("utf-8")
                storage.upload(storage_path, content_bytes, "application/json")
            except Exception as e:
                raise StorageError(f"Failed to upload content to storage: {str(e)}")

            # Create version record
            version_id = db.drawing_versions.insert(
                drawing_id=drawing_id,
                version_number=next_version,
                created_by_id=user_id,
                content_json=content_json,
                change_summary=change_summary,
                storage_path=storage_path,
            )

            # Update drawing's updated_by_id
            db(db.drawings.id == drawing_id).update(updated_by_id=user_id)

            db.commit()

            return next_version

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to save content: {str(e)}")

    @staticmethod
    def get_content(
        drawing_id: int, user_id: int, version: Optional[int] = None
    ) -> dict:
        """
        Get drawing content for a specific version or latest.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user requesting content
            version: Optional version number (defaults to latest)

        Returns:
            Dictionary containing drawing content

        Raises:
            PermissionError: If user doesn't have view permission
            ValueError: If drawing or version not found
            StorageError: If storage operation fails
        """
        db = get_db()

        # Check if drawing exists
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            raise ValueError("Drawing not found")

        # Check view permission
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to view this drawing")

        # Get version record
        if version is None:
            # Get latest version
            version_record = (
                db(db.drawing_versions.drawing_id == drawing_id)
                .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
                .first()
            )
        else:
            # Get specific version
            version_record = (
                db(
                    (db.drawing_versions.drawing_id == drawing_id)
                    & (db.drawing_versions.version_number == version)
                )
                .select()
                .first()
            )

        if not version_record:
            raise ValueError("Version not found")

        # Try to get content from JSON field first (newer approach)
        if version_record.content_json:
            return version_record.content_json

        # Fallback to storage if no JSON in database
        try:
            storage = get_storage_provider()
            content_bytes = storage.download(version_record.storage_path)
            content = json.loads(content_bytes.decode("utf-8"))
            return content
        except Exception as e:
            raise StorageError(f"Failed to retrieve content from storage: {str(e)}")

    @staticmethod
    def list_versions(
        drawing_id: int, user_id: int, page: int = 1, per_page: int = 20
    ) -> tuple[list[dict], int]:
        """
        List all versions for a drawing.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user requesting versions
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Tuple of (list of version dictionaries, total count)

        Raises:
            PermissionError: If user doesn't have view permission
            ValueError: If drawing not found
        """
        db = get_db()

        # Check if drawing exists
        if not db(db.drawings.id == drawing_id).select().first():
            raise ValueError("Drawing not found")

        # Check view permission
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError(
                "You don't have permission to view this drawing's versions"
            )

        offset = (page - 1) * per_page

        # Get versions with creator info
        versions = db(
            (db.drawing_versions.drawing_id == drawing_id)
            & (db.drawing_versions.created_by_id == db.identities.id)
        ).select(
            db.drawing_versions.ALL,
            db.identities.id,
            db.identities.username,
            db.identities.full_name,
            orderby=~db.drawing_versions.version_number,
            limitby=(offset, offset + per_page),
        )

        total = db(db.drawing_versions.drawing_id == drawing_id).count()

        result = []
        for v in versions:
            result.append(
                {
                    "id": v.drawing_versions.id,
                    "drawing_id": v.drawing_versions.drawing_id,
                    "version_number": v.drawing_versions.version_number,
                    "change_summary": v.drawing_versions.change_summary,
                    "storage_path": v.drawing_versions.storage_path,
                    "created_by": {
                        "id": v.identities.id,
                        "username": v.identities.username,
                        "full_name": v.identities.full_name,
                    },
                    "created_at": (
                        v.drawing_versions.created_at.isoformat()
                        if v.drawing_versions.created_at
                        else None
                    ),
                }
            )

        return result, total

    @staticmethod
    def restore_version(
        drawing_id: int,
        version: int,
        user_id: int,
        change_summary: Optional[str] = None,
    ) -> int:
        """
        Restore a previous version as a new version.

        Args:
            drawing_id: ID of the drawing
            version: Version number to restore
            user_id: ID of the user restoring the version
            change_summary: Optional description (defaults to restore message)

        Returns:
            New version number

        Raises:
            PermissionError: If user doesn't have edit permission
            ValueError: If restore fails or version not found
        """
        # Check edit permission
        if not PermissionService.can_edit_drawing(user_id, drawing_id):
            raise PermissionError(
                "You don't have permission to restore versions of this drawing"
            )

        # Get the content from the version to restore
        content = ContentService.get_content(drawing_id, user_id, version)

        # Create default change summary if not provided
        if not change_summary:
            change_summary = f"Restored from version {version}"

        # Save as new version
        return ContentService.save_content(drawing_id, content, user_id, change_summary)

    @staticmethod
    def delete_version(drawing_id: int, version: int, user_id: int) -> bool:
        """
        Delete a specific version (soft delete - mark as deleted).

        Args:
            drawing_id: ID of the drawing
            version: Version number to delete
            user_id: ID of the user deleting the version

        Returns:
            True if deleted, False if version not found

        Raises:
            PermissionError: If user doesn't have permission
            ValueError: If deletion fails
        """
        # Check permission (only owner or admin can delete versions)
        if not PermissionService.can_delete_drawing(user_id, drawing_id):
            raise PermissionError(
                "You don't have permission to delete versions of this drawing"
            )

        db = get_db()

        # Check if version exists
        version_record = (
            db(
                (db.drawing_versions.drawing_id == drawing_id)
                & (db.drawing_versions.version_number == version)
            )
            .select()
            .first()
        )

        if not version_record:
            return False

        # Prevent deletion of the only version
        version_count = db(db.drawing_versions.drawing_id == drawing_id).count()
        if version_count <= 1:
            raise ValueError("Cannot delete the only version of a drawing")

        try:
            # Delete version record
            deleted = db(
                (db.drawing_versions.drawing_id == drawing_id)
                & (db.drawing_versions.version_number == version)
            ).delete()

            # Optionally delete from storage
            try:
                storage = get_storage_provider()
                storage.delete(version_record.storage_path)
            except Exception:
                # Log but don't fail if storage deletion fails
                pass

            db.commit()
            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete version: {str(e)}")

    @staticmethod
    def compare_versions(
        drawing_id: int, version1: int, version2: int, user_id: int
    ) -> dict:
        """
        Compare two versions of a drawing.

        Args:
            drawing_id: ID of the drawing
            version1: First version number
            version2: Second version number
            user_id: ID of the user comparing versions

        Returns:
            Dictionary with comparison data

        Raises:
            PermissionError: If user doesn't have view permission
            ValueError: If versions not found
        """
        # Get both versions
        content1 = ContentService.get_content(drawing_id, user_id, version1)
        content2 = ContentService.get_content(drawing_id, user_id, version2)

        # Simple comparison - return both contents
        # Frontend can do detailed diff
        return {
            "drawing_id": drawing_id,
            "version1": {
                "version_number": version1,
                "content": content1,
            },
            "version2": {
                "version_number": version2,
                "content": content2,
            },
        }

    @staticmethod
    def get_latest_version_number(drawing_id: int) -> int:
        """
        Get the latest version number for a drawing.

        Args:
            drawing_id: ID of the drawing

        Returns:
            Latest version number or 0 if no versions
        """
        db = get_db()
        latest = (
            db(db.drawing_versions.drawing_id == drawing_id)
            .select(
                db.drawing_versions.version_number,
                orderby=~db.drawing_versions.version_number,
                limitby=(0, 1),
            )
            .first()
        )

        return latest.version_number if latest else 0
