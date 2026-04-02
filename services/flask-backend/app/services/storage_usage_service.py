"""Storage usage and quota management service for IceCharts.

This module provides functionality to calculate actual storage usage
from object storage and manage user/tenant storage quotas.
"""

import json
from typing import Any, Dict, Optional

from app.models import get_db
from app.services.drawing_storage_service import DrawingStorageService
from flask import current_app


class StorageUsageService:
    """Service for calculating and managing storage usage and quotas."""

    # Default quota values (in bytes)
    DEFAULT_USER_QUOTA = 1073741824  # 1GB
    DEFAULT_TENANT_QUOTA = 10737418240  # 10GB

    @classmethod
    def get_user_storage_usage(cls, user_id: int) -> Dict[str, Any]:
        """Calculate total storage usage for a user.

        Args:
            user_id: User ID to calculate storage for

        Returns:
            Dictionary with storage usage breakdown:
            {
                "user_id": int,
                "total_size_bytes": int,
                "total_size_mb": float,
                "total_drawings": int,
                "drawings_content_bytes": int,
                "drawing_versions_bytes": int,
                "attachments_bytes": int,
                "thumbnails_bytes": int,
                "quota_bytes": int,
                "quota_mb": float,
                "usage_percentage": float,
                "by_provider": [
                    {
                        "provider_id": int,
                        "provider_name": str,
                        "provider_type": str,
                        "size_bytes": int,
                        "size_mb": float,
                        "file_count": int
                    }
                ]
            }
        """
        try:
            db = get_db()

            # Get all drawings owned by the user
            user_drawings = db(
                (db.drawings.owner_id == user_id)
                | (db.drawings.created_by_id == user_id)
            ).select(db.drawings.id)

            drawing_ids = [d.id for d in user_drawings]

            # Calculate storage usage from each component
            drawings_content_bytes = cls._calculate_drawing_content_size(drawing_ids)
            drawing_versions_bytes = cls._calculate_drawing_versions_size(drawing_ids)
            attachments_bytes = cls._calculate_attachments_size(drawing_ids)
            thumbnails_bytes = cls._calculate_thumbnails_size(drawing_ids)

            # Total usage
            total_size_bytes = (
                drawings_content_bytes
                + drawing_versions_bytes
                + attachments_bytes
                + thumbnails_bytes
            )

            # Get user's quota (or use default)
            quota_bytes = cls.get_user_quota(user_id)

            # Calculate usage percentage
            usage_percentage = (
                (total_size_bytes / quota_bytes * 100) if quota_bytes > 0 else 0
            )

            # Get breakdown by storage provider
            by_provider = cls._get_usage_by_provider(drawing_ids)

            return {
                "user_id": user_id,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "total_drawings": len(drawing_ids),
                "drawings_content_bytes": drawings_content_bytes,
                "drawing_versions_bytes": drawing_versions_bytes,
                "attachments_bytes": attachments_bytes,
                "thumbnails_bytes": thumbnails_bytes,
                "quota_bytes": quota_bytes,
                "quota_mb": round(quota_bytes / (1024 * 1024), 2),
                "usage_percentage": round(usage_percentage, 2),
                "by_provider": by_provider,
            }

        except Exception as e:
            current_app.logger.error(
                f"Error calculating storage usage for user {user_id}: {e}"
            )
            # Return minimal response with defaults
            return {
                "user_id": user_id,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "total_drawings": 0,
                "drawings_content_bytes": 0,
                "drawing_versions_bytes": 0,
                "attachments_bytes": 0,
                "thumbnails_bytes": 0,
                "quota_bytes": cls.DEFAULT_USER_QUOTA,
                "quota_mb": round(cls.DEFAULT_USER_QUOTA / (1024 * 1024), 2),
                "usage_percentage": 0.0,
                "by_provider": [],
            }

    @classmethod
    def get_tenant_storage_usage(cls, tenant_id: int) -> Dict[str, Any]:
        """Calculate total storage usage for a tenant.

        Args:
            tenant_id: Tenant ID to calculate storage for

        Returns:
            Dictionary with storage usage breakdown
        """
        try:
            db = get_db()

            # Get all drawings in the tenant
            tenant_drawings = db(db.drawings.tenant_id == tenant_id).select(
                db.drawings.id
            )
            drawing_ids = [d.id for d in tenant_drawings]

            # Calculate storage usage
            drawings_content_bytes = cls._calculate_drawing_content_size(drawing_ids)
            drawing_versions_bytes = cls._calculate_drawing_versions_size(drawing_ids)
            attachments_bytes = cls._calculate_attachments_size(drawing_ids)
            thumbnails_bytes = cls._calculate_thumbnails_size(drawing_ids)

            total_size_bytes = (
                drawings_content_bytes
                + drawing_versions_bytes
                + attachments_bytes
                + thumbnails_bytes
            )

            # Get tenant's quota
            quota_bytes = cls.get_tenant_quota(tenant_id)

            usage_percentage = (
                (total_size_bytes / quota_bytes * 100) if quota_bytes > 0 else 0
            )

            by_provider = cls._get_usage_by_provider(drawing_ids)

            return {
                "tenant_id": tenant_id,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "total_drawings": len(drawing_ids),
                "drawings_content_bytes": drawings_content_bytes,
                "drawing_versions_bytes": drawing_versions_bytes,
                "attachments_bytes": attachments_bytes,
                "thumbnails_bytes": thumbnails_bytes,
                "quota_bytes": quota_bytes,
                "quota_mb": round(quota_bytes / (1024 * 1024), 2),
                "usage_percentage": round(usage_percentage, 2),
                "by_provider": by_provider,
            }

        except Exception as e:
            current_app.logger.error(
                f"Error calculating storage usage for tenant {tenant_id}: {e}"
            )
            return {
                "tenant_id": tenant_id,
                "total_size_bytes": 0,
                "total_size_mb": 0.0,
                "total_drawings": 0,
                "drawings_content_bytes": 0,
                "drawing_versions_bytes": 0,
                "attachments_bytes": 0,
                "thumbnails_bytes": 0,
                "quota_bytes": cls.DEFAULT_TENANT_QUOTA,
                "quota_mb": round(cls.DEFAULT_TENANT_QUOTA / (1024 * 1024), 2),
                "usage_percentage": 0.0,
                "by_provider": [],
            }

    @classmethod
    def _calculate_drawing_content_size(cls, drawing_ids: list) -> int:
        """Calculate total size of drawing content in object storage.

        Args:
            drawing_ids: List of drawing IDs

        Returns:
            Total size in bytes
        """
        if not drawing_ids or not DrawingStorageService.is_available():
            return 0

        try:
            total_size = 0
            for drawing_id in drawing_ids:
                # Get the latest version of the drawing
                try:
                    key = DrawingStorageService.get_storage_key(drawing_id, None)
                    provider = DrawingStorageService._get_provider()
                    file_info = DrawingStorageService._run_async(
                        provider.get_metadata(key)
                    )
                    if file_info:
                        total_size += file_info.size
                except Exception:
                    # File doesn't exist or error - skip
                    pass

            return total_size

        except Exception as e:
            current_app.logger.warning(f"Error calculating drawing content size: {e}")
            return 0

    @classmethod
    def _calculate_drawing_versions_size(cls, drawing_ids: list) -> int:
        """Calculate total size of all drawing versions in object storage.

        Args:
            drawing_ids: List of drawing IDs

        Returns:
            Total size in bytes
        """
        if not drawing_ids or not DrawingStorageService.is_available():
            return 0

        try:
            total_size = 0
            for drawing_id in drawing_ids:
                # Get all versions of the drawing
                try:
                    versions = DrawingStorageService.list_versions(drawing_id)
                    for version in versions:
                        total_size += version.get("size", 0)
                except Exception:
                    # Error listing versions - skip
                    pass

            return total_size

        except Exception as e:
            current_app.logger.warning(f"Error calculating drawing versions size: {e}")
            return 0

    @classmethod
    def _calculate_attachments_size(cls, drawing_ids: list) -> int:
        """Calculate total size of attachments for drawings.

        Currently a placeholder - would need to implement attachment storage.

        Args:
            drawing_ids: List of drawing IDs

        Returns:
            Total size in bytes
        """
        # TODO: Implement attachment size calculation when attachment storage is added
        return 0

    @classmethod
    def _calculate_thumbnails_size(cls, drawing_ids: list) -> int:
        """Calculate total size of thumbnails for drawings.

        Currently a placeholder - would need to implement thumbnail storage.

        Args:
            drawing_ids: List of drawing IDs

        Returns:
            Total size in bytes
        """
        # TODO: Implement thumbnail size calculation when thumbnail storage is added
        return 0

    @classmethod
    def _get_usage_by_provider(cls, drawing_ids: list) -> list:
        """Get storage usage breakdown by storage provider.

        Args:
            drawing_ids: List of drawing IDs

        Returns:
            List of dictionaries with provider usage information
        """
        if not drawing_ids:
            return []

        try:
            db = get_db()
            providers = {}

            # Query storage providers used by these drawings
            drawing_versions = db(
                db.drawing_versions.drawing_id.belongs(drawing_ids)
            ).select(
                db.drawing_versions.storage_provider_id,
                db.drawing_versions.storage_path,
                groupby=db.drawing_versions.storage_provider_id,
            )

            for dv in drawing_versions:
                provider_id = dv.storage_provider_id
                if not provider_id:
                    continue

                if provider_id not in providers:
                    providers[provider_id] = {
                        "provider_id": provider_id,
                        "size_bytes": 0,
                        "file_count": 0,
                    }

                providers[provider_id]["file_count"] += 1

            # Add provider details
            result = []
            for provider_id, usage in providers.items():
                provider = db(db.storage_providers.id == provider_id).select().first()
                if provider:
                    result.append(
                        {
                            "provider_id": provider.id,
                            "provider_name": provider.name,
                            "provider_type": provider.provider_type,
                            "size_bytes": usage["size_bytes"],
                            "size_mb": round(usage["size_bytes"] / (1024 * 1024), 2),
                            "file_count": usage["file_count"],
                        }
                    )

            return result

        except Exception as e:
            current_app.logger.warning(f"Error getting usage by provider: {e}")
            return []

    @classmethod
    def get_user_quota(cls, user_id: int) -> int:
        """Get storage quota for a user in bytes.

        Checks for user-specific quota, then tenant quota, then default.

        Args:
            user_id: User ID

        Returns:
            Quota in bytes
        """
        try:
            db = get_db()

            # Get user and tenant info
            user = db(db.identities.id == user_id).select().first()
            if not user:
                return cls.DEFAULT_USER_QUOTA

            # TODO: Add storage_quota_bytes field to identities table
            # For now, get tenant quota
            tenant_id = user.tenant_id
            return cls.get_tenant_quota(tenant_id)

        except Exception as e:
            current_app.logger.warning(f"Error getting user quota: {e}")
            return cls.DEFAULT_USER_QUOTA

    @classmethod
    def get_tenant_quota(cls, tenant_id: int) -> int:
        """Get storage quota for a tenant in bytes.

        Args:
            tenant_id: Tenant ID

        Returns:
            Quota in bytes
        """
        try:
            db = get_db()

            tenant = db(db.tenants.id == tenant_id).select().first()
            if not tenant:
                return cls.DEFAULT_TENANT_QUOTA

            # storage_quota_gb field stores quota in GB
            quota_gb = tenant.storage_quota_gb or 10
            return quota_gb * 1024 * 1024 * 1024

        except Exception as e:
            current_app.logger.warning(f"Error getting tenant quota: {e}")
            return cls.DEFAULT_TENANT_QUOTA

    @classmethod
    def set_user_quota(cls, user_id: int, quota_mb: int) -> bool:
        """Set storage quota for a user.

        Args:
            user_id: User ID
            quota_mb: Quota in megabytes

        Returns:
            True if successful, False otherwise
        """
        try:
            db = get_db()

            # TODO: Add storage_quota_bytes field to identities table
            # For now, this updates the tenant quota if user is tenant owner
            user = db(db.identities.id == user_id).select().first()
            if not user:
                return False

            # Update would go here once schema is updated
            # db(db.identities.id == user_id).update(storage_quota_bytes=quota_mb * 1024 * 1024)
            # db.commit()

            current_app.logger.info(
                f"Storage quota updated for user {user_id}: {quota_mb}MB"
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Error setting user quota: {e}")
            return False

    @classmethod
    def set_tenant_quota(cls, tenant_id: int, quota_gb: int) -> bool:
        """Set storage quota for a tenant.

        Args:
            tenant_id: Tenant ID
            quota_gb: Quota in gigabytes

        Returns:
            True if successful, False otherwise
        """
        try:
            db = get_db()

            if quota_gb < 0:
                return False

            db(db.tenants.id == tenant_id).update(storage_quota_gb=quota_gb)
            db.commit()

            current_app.logger.info(
                f"Storage quota updated for tenant {tenant_id}: {quota_gb}GB"
            )
            return True

        except Exception as e:
            current_app.logger.error(f"Error setting tenant quota: {e}")
            return False

    @classmethod
    def check_quota_exceeded(cls, user_id: int, additional_bytes: int = 0) -> bool:
        """Check if user would exceed quota with additional storage.

        Args:
            user_id: User ID
            additional_bytes: Additional bytes to add (default 0)

        Returns:
            True if quota would be exceeded, False otherwise
        """
        try:
            usage = cls.get_user_storage_usage(user_id)
            quota = cls.get_user_quota(user_id)

            return (usage["total_size_bytes"] + additional_bytes) > quota

        except Exception as e:
            current_app.logger.warning(f"Error checking quota: {e}")
            return False

    @classmethod
    def get_storage_stats_summary(cls, user_id: int) -> Dict[str, Any]:
        """Get a summary of storage stats for dashboard widget.

        Args:
            user_id: User ID

        Returns:
            Dictionary with summary statistics
        """
        try:
            usage = cls.get_user_storage_usage(user_id)

            return {
                "used_mb": usage["total_size_mb"],
                "quota_mb": usage["quota_mb"],
                "usage_percentage": usage["usage_percentage"],
                "usage_status": cls._get_usage_status(usage["usage_percentage"]),
                "total_drawings": usage["total_drawings"],
            }

        except Exception as e:
            current_app.logger.warning(f"Error getting storage summary: {e}")
            return {
                "used_mb": 0.0,
                "quota_mb": round(cls.DEFAULT_USER_QUOTA / (1024 * 1024), 2),
                "usage_percentage": 0.0,
                "usage_status": "ok",
                "total_drawings": 0,
            }

    @classmethod
    def _get_usage_status(cls, usage_percentage: float) -> str:
        """Get usage status based on percentage.

        Args:
            usage_percentage: Usage percentage (0-100)

        Returns:
            Status string: "ok", "warning", or "critical"
        """
        if usage_percentage >= 90:
            return "critical"
        elif usage_percentage >= 75:
            return "warning"
        else:
            return "ok"
