"""Celery tasks for background storage migration processing.

This module handles asynchronous storage migration operations for moving drawings
and files between storage providers with progress tracking and rollback support.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded

from ..config import Config
from ..models import get_db
from ..services.drawing_storage_service import DrawingStorageService

logger = logging.getLogger(__name__)

# Initialize Celery app (reuse from export tasks)
celery_app = Celery(
    "icecharts",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    timezone=Config.CELERY_TIMEZONE,
    task_track_started=Config.CELERY_TASK_TRACK_STARTED,
    task_time_limit=Config.CELERY_TASK_TIME_LIMIT,
    result_expires=86400,  # 24 hours
    task_acks_late=True,
)


class MigrationTask(Task):
    """Base task class for storage migration operations with custom error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure by updating migration status."""
        logger.error(f"Migration task {task_id} failed: {exc}")
        try:
            db = get_db()
            # Update migration job status to failed
            migration_id = kwargs.get("migration_id")
            if migration_id:
                db(db.migration_jobs.id == migration_id).update(
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.utcnow(),
                )
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update migration status: {e}")


def _get_storage_provider_instance(provider_id: int):
    """Get initialized storage provider instance from configuration.

    Args:
        provider_id: Storage provider ID

    Returns:
        Initialized storage provider instance

    Raises:
        ValueError: If provider not found
    """
    from app.storage import get_storage_provider

    db = get_db()
    provider = db(db.storage_providers.id == provider_id).select().first()

    if not provider:
        raise ValueError(f"Storage provider {provider_id} not found")

    config = provider.config_json or provider.storage_config or {}

    return get_storage_provider(provider.provider_type, config)


@celery_app.task(base=MigrationTask, bind=True, time_limit=3600)
def migrate_storage_task(
    self,
    migration_id: int,
    source_provider_id: int,
    target_provider_id: int,
    drawing_ids: List[int],
) -> Dict[str, Any]:
    """Migrate drawings from source to target storage provider asynchronously.

    Args:
        migration_id: Migration job ID for tracking
        source_provider_id: Source storage provider ID
        target_provider_id: Target storage provider ID
        drawing_ids: List of drawing IDs to migrate (empty = all)

    Returns:
        Dict with migration results and statistics

    Raises:
        ValueError: If migration or provider not found
        SoftTimeLimitExceeded: If task exceeds time limit
    """
    task_id = self.request.id
    logger.info(
        f"Starting migration task {task_id} for migration_id {migration_id} "
        f"from provider {source_provider_id} to {target_provider_id}"
    )

    db = get_db()
    migration_job = db(db.migration_jobs.id == migration_id).select().first()

    if not migration_job:
        raise ValueError(f"Migration job {migration_id} not found")

    try:
        # Update migration status to in_progress
        db(db.migration_jobs.id == migration_id).update(
            status="in_progress",
            celery_task_id=task_id,
            started_at=datetime.utcnow(),
        )
        db.commit()

        # Get storage provider instances
        source_provider = _get_storage_provider_instance(source_provider_id)
        target_provider = _get_storage_provider_instance(target_provider_id)

        # Get drawing IDs to migrate
        if not drawing_ids or len(drawing_ids) == 0:
            # Migrate all drawings
            rows = db(
                db.drawing_versions.storage_provider_id == source_provider_id
            ).select(db.drawing_versions.drawing_id, distinct=True)
            drawing_ids = [row.drawing_id for row in rows]

        total_drawings = len(drawing_ids)
        migrated_count = 0
        failed_count = 0
        skipped_count = 0
        failed_drawings = []
        backup_data = {}

        logger.info(f"Migrating {total_drawings} drawings")

        # Migrate each drawing
        for idx, drawing_id in enumerate(drawing_ids):
            try:
                progress = int((idx / total_drawings) * 100) if total_drawings > 0 else 0
                _set_migration_status(
                    migration_id,
                    "in_progress",
                    progress,
                    {
                        "migrated": migrated_count,
                        "failed": failed_count,
                        "skipped": skipped_count,
                        "current_drawing": drawing_id,
                    },
                )

                # Migrate this drawing
                result = _migrate_drawing(
                    db,
                    drawing_id,
                    source_provider,
                    target_provider,
                    source_provider_id,
                    target_provider_id,
                    backup_data,
                )

                if result["status"] == "success":
                    migrated_count += 1
                elif result["status"] == "failed":
                    failed_count += 1
                    failed_drawings.append({
                        "drawing_id": drawing_id,
                        "error": result.get("error", "Unknown error"),
                    })
                else:  # skipped
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error migrating drawing {drawing_id}: {e}", exc_info=True)
                failed_count += 1
                failed_drawings.append({
                    "drawing_id": drawing_id,
                    "error": str(e),
                })

        # Update final status
        migration_result = {
            "migration_id": migration_id,
            "total": total_drawings,
            "migrated": migrated_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "failed_drawings": failed_drawings,
            "backup_data": backup_data if failed_count > 0 else {},
        }

        status = "completed" if failed_count == 0 else "completed_with_errors"

        db(db.migration_jobs.id == migration_id).update(
            status=status,
            total_count=total_drawings,
            migrated_count=migrated_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            result_json=migration_result,
            completed_at=datetime.utcnow(),
        )
        db.commit()

        logger.info(
            f"Migration task {task_id} completed: "
            f"{migrated_count} migrated, {failed_count} failed, {skipped_count} skipped"
        )

        return migration_result

    except SoftTimeLimitExceeded:
        logger.error(f"Migration task {task_id} exceeded time limit")
        db(db.migration_jobs.id == migration_id).update(
            status="failed",
            error_message="Task exceeded time limit (1 hour)",
            completed_at=datetime.utcnow(),
        )
        db.commit()
        raise

    except Exception as e:
        logger.error(f"Migration task {task_id} failed: {str(e)}", exc_info=True)
        db(db.migration_jobs.id == migration_id).update(
            status="failed",
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )
        db.commit()
        raise


def _migrate_drawing(
    db,
    drawing_id: int,
    source_provider,
    target_provider,
    source_provider_id: int,
    target_provider_id: int,
    backup_data: Dict,
) -> Dict[str, str]:
    """Migrate a single drawing and its versions.

    Args:
        db: Database connection
        drawing_id: Drawing ID to migrate
        source_provider: Source storage provider instance
        target_provider: Target storage provider instance
        source_provider_id: Source provider ID
        target_provider_id: Target provider ID
        backup_data: Dictionary to store backup data for rollback

    Returns:
        Dict with status and optional error message
    """
    try:
        # Get all versions of this drawing stored in source provider
        versions = db(
            (db.drawing_versions.drawing_id == drawing_id) &
            (db.drawing_versions.storage_provider_id == source_provider_id)
        ).select()

        if not versions:
            # No versions to migrate
            return {"status": "skipped", "reason": "No versions found"}

        # Migrate each version
        for version in versions:
            try:
                # Get the drawing content key
                content_key = DrawingStorageService.get_storage_key(
                    drawing_id, version.version_number
                )

                # Check if source exists
                import asyncio

                async def check_exists():
                    return await source_provider.exists(content_key)

                exists = asyncio.run(check_exists())

                if not exists:
                    logger.debug(f"Content not found in source: {content_key}")
                    continue

                # Download from source
                async def download():
                    return await source_provider.download(content_key)

                content_data = asyncio.run(download())

                # Backup original location for rollback
                backup_key = f"migration_backup/{uuid4()}/{content_key}"
                backup_data[version.id] = {
                    "version_id": version.id,
                    "drawing_id": drawing_id,
                    "original_key": content_key,
                    "backup_key": backup_key,
                    "original_provider_id": source_provider_id,
                }

                # Upload to target
                async def upload():
                    return await target_provider.upload(
                        key=content_key,
                        data=content_data,
                        content_type="application/json",
                        metadata={
                            "drawing_id": str(drawing_id),
                            "version": str(version.version_number),
                        },
                    )

                asyncio.run(upload())

                # Update database to point to new provider
                db(db.drawing_versions.id == version.id).update(
                    storage_provider_id=target_provider_id,
                )
                db.commit()

                logger.debug(
                    f"Migrated drawing {drawing_id} v{version.version_number}"
                )

            except Exception as e:
                logger.error(
                    f"Error migrating version {version.id} of drawing {drawing_id}: {e}"
                )
                raise

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error migrating drawing {drawing_id}: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(base=MigrationTask, bind=True, time_limit=1800)
def rollback_migration_task(
    self,
    migration_id: int,
) -> Dict[str, Any]:
    """Rollback a failed migration to restore original storage provider references.

    Args:
        migration_id: Migration job ID to rollback

    Returns:
        Dict with rollback results
    """
    task_id = self.request.id
    logger.info(f"Starting rollback task {task_id} for migration_id {migration_id}")

    db = get_db()
    migration_job = db(db.migration_jobs.id == migration_id).select().first()

    if not migration_job:
        raise ValueError(f"Migration job {migration_id} not found")

    if migration_job.status not in ["failed", "completed_with_errors"]:
        return {
            "status": "skipped",
            "reason": f"Cannot rollback migration in {migration_job.status} status",
        }

    try:
        # Get backup data
        result_json = migration_job.result_json or {}
        backup_data = result_json.get("backup_data", {})

        if not backup_data:
            logger.warning(f"No backup data found for migration {migration_id}")
            return {"status": "skipped", "reason": "No backup data available"}

        # Restore original provider references
        rolled_back_count = 0
        failed_count = 0

        for version_id_str, backup_info in backup_data.items():
            try:
                version_id = int(version_id_str)
                original_provider_id = backup_info.get("original_provider_id")

                db(db.drawing_versions.id == version_id).update(
                    storage_provider_id=original_provider_id,
                )
                db.commit()

                rolled_back_count += 1

            except Exception as e:
                logger.error(f"Error rolling back version {version_id_str}: {e}")
                failed_count += 1

        db(db.migration_jobs.id == migration_id).update(
            status="rolled_back",
            result_json={
                "rollback_status": "completed",
                "rolled_back_count": rolled_back_count,
                "failed_count": failed_count,
            },
            completed_at=datetime.utcnow(),
        )
        db.commit()

        logger.info(
            f"Rollback completed: {rolled_back_count} restored, {failed_count} failed"
        )

        return {
            "status": "success",
            "rolled_back_count": rolled_back_count,
            "failed_count": failed_count,
        }

    except Exception as e:
        logger.error(f"Rollback task {task_id} failed: {str(e)}", exc_info=True)
        db(db.migration_jobs.id == migration_id).update(
            status="rollback_failed",
            error_message=str(e),
            completed_at=datetime.utcnow(),
        )
        db.commit()
        raise


def _set_migration_status(
    migration_id: int,
    status: str,
    progress: int,
    metadata: Optional[Dict] = None,
) -> None:
    """Store migration task status in database.

    Args:
        migration_id: Migration job ID
        status: Status string (pending, in_progress, completed, failed, etc.)
        progress: Progress percentage (0-100)
        metadata: Additional metadata to store
    """
    try:
        db = get_db()

        update_data = {
            "status": status,
            "progress": progress,
        }

        if metadata:
            # Merge with existing status_json metadata
            migration_job = db(db.migration_jobs.id == migration_id).select().first()
            existing_metadata = migration_job.status_json or {} if migration_job else {}
            existing_metadata.update(metadata)
            update_data["status_json"] = existing_metadata

        db(db.migration_jobs.id == migration_id).update(**update_data)
        db.commit()

        logger.debug(
            f"Updated migration {migration_id} status to {status} ({progress}%)"
        )

    except Exception as e:
        logger.error(f"Failed to set migration status: {e}")


def get_migration_status(migration_id: int) -> Optional[Dict]:
    """Retrieve migration job status from database.

    Args:
        migration_id: Migration job ID

    Returns:
        Migration status dict or None if not found
    """
    try:
        db = get_db()
        migration_job = db(db.migration_jobs.id == migration_id).select().first()

        if not migration_job:
            return None

        return {
            "id": migration_job.id,
            "status": migration_job.status,
            "progress": migration_job.progress,
            "total_count": migration_job.total_count,
            "migrated_count": migration_job.migrated_count,
            "failed_count": migration_job.failed_count,
            "skipped_count": migration_job.skipped_count,
            "error_message": migration_job.error_message,
            "started_at": migration_job.started_at,
            "completed_at": migration_job.completed_at,
            "result": migration_job.result_json,
            "status_json": migration_job.status_json,
            "celery_task_id": migration_job.celery_task_id,
        }

    except Exception as e:
        logger.error(f"Failed to retrieve migration status: {e}")
        return None
