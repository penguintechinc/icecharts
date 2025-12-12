"""Celery tasks for background export processing.

This module handles asynchronous export operations for large diagrams (>2000x2000px)
and stores results in Redis for retrieval via polling.
"""

import json
import logging
from datetime import timedelta
from typing import Optional

from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded

from ..config import Config
from ..services.export_service import ExportOptions, ExportService

# Configure logger
logger = logging.getLogger(__name__)

# Initialize Celery app
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


class ExportTask(Task):
    """Base task class for export operations with custom error handling."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Export task {task_id} failed: {exc}")
        # Store error in Redis for status endpoint
        try:
            from redis import Redis

            redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)
            redis_client.setex(
                f"export:task:{task_id}:error",
                86400,  # 24 hour expiration
                json.dumps({"error": str(exc), "status": "failed"}),
            )
        except Exception as e:
            logger.error(f"Failed to store error in Redis: {e}")


@celery_app.task(base=ExportTask, bind=True)
def export_drawing_task(
    self,
    drawing_id: int,
    format: str,
    options: Optional[dict] = None,
    drawing_data: Optional[dict] = None,
) -> dict:
    """Export drawing in background using Celery.

    Args:
        drawing_id: ID of the drawing to export
        format: Export format (png, jpg, svg, pdf, json)
        options: Export options (width, height, quality, etc.)
        drawing_data: Drawing content data (dict or SVG string)

    Returns:
        Dict with export metadata and Redis key for retrieval

    Raises:
        ValueError: If format is invalid or options are invalid
        SoftTimeLimitExceeded: If task exceeds time limit
    """
    task_id = self.request.id
    logger.info(f"Starting export task {task_id} for drawing {drawing_id} as {format}")

    try:
        # Set initial status
        _set_export_status(task_id, "processing", 0)

        # Validate options
        if options is None:
            options = {}
        export_format = options.get("format", format)
        width = options.get("width", 800)
        height = options.get("height", 600)
        quality = options.get("quality", 95 if export_format == "png" else 85)
        include_background = options.get("include_background", True)
        page_size = options.get("page_size", "A4")

        # Validate drawing data is provided
        if drawing_data is None:
            raise ValueError("Drawing data is required for export")

        # Update status - preparing
        _set_export_status(task_id, "preparing", 10)

        # Create export options
        export_options = ExportOptions(
            format=export_format,
            width=width,
            height=height,
            quality=quality,
            page_size=page_size,
            include_background=include_background,
        )

        # Update status - exporting
        _set_export_status(task_id, "exporting", 30)

        # Perform export
        exported_content = ExportService.export(export_options, drawing_data)

        # Update status - storing
        _set_export_status(task_id, "storing", 70)

        # Store result in Redis
        redis_key = _store_export_result(
            task_id, drawing_id, export_format, exported_content
        )

        # Update status - complete
        _set_export_status(
            task_id,
            "completed",
            100,
            {"redis_key": redis_key, "size": len(exported_content)},
        )

        logger.info(f"Export task {task_id} completed successfully")

        return {
            "task_id": task_id,
            "drawing_id": drawing_id,
            "format": export_format,
            "status": "completed",
            "redis_key": redis_key,
            "size": len(exported_content),
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Export task {task_id} exceeded time limit")
        _set_export_status(
            task_id, "failed", 0, {"error": "Task exceeded time limit (30 minutes)"}
        )
        raise

    except Exception as e:
        logger.error(f"Export task {task_id} failed: {str(e)}", exc_info=True)
        _set_export_status(task_id, "failed", 0, {"error": str(e)})
        raise


def _set_export_status(
    task_id: str,
    status: str,
    progress: int,
    metadata: Optional[dict] = None,
) -> None:
    """Store export task status in Redis.

    Args:
        task_id: Celery task ID
        status: Status string (processing, completed, failed, etc.)
        progress: Progress percentage (0-100)
        metadata: Additional metadata to store
    """
    try:
        from redis import Redis

        redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)

        status_data = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
        }
        if metadata:
            status_data.update(metadata)

        # Store status with 24-hour expiration
        redis_client.setex(
            f"export:task:{task_id}",
            86400,  # 24 hours
            json.dumps(status_data),
        )

        logger.debug(f"Updated export task {task_id} status to {status} ({progress}%)")

    except Exception as e:
        logger.error(f"Failed to set export status in Redis: {e}")


def _store_export_result(
    task_id: str,
    drawing_id: int,
    format: str,
    content: any,
) -> str:
    """Store exported content in Redis for later retrieval.

    Args:
        task_id: Celery task ID
        drawing_id: Drawing ID
        format: Export format
        content: Exported content (bytes or string)

    Returns:
        Redis key for retrieving the export

    Raises:
        Exception: If storage fails
    """
    try:
        from redis import Redis

        redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)

        # Create redis key
        redis_key = f"export:result:{task_id}"

        # Store metadata
        metadata = {
            "task_id": task_id,
            "drawing_id": drawing_id,
            "format": format,
            "stored_at": str(__import__("datetime").datetime.utcnow()),
        }
        redis_client.setex(
            f"{redis_key}:metadata",
            86400,  # 24 hours
            json.dumps(metadata),
        )

        # Store binary content
        if isinstance(content, bytes):
            redis_client.setex(
                f"{redis_key}:data",
                86400,  # 24 hours
                content,
            )
        else:
            # Text content (JSON, SVG)
            redis_client.setex(
                f"{redis_key}:data",
                86400,  # 24 hours
                content.encode("utf-8") if isinstance(content, str) else content,
            )

        logger.info(f"Stored export result {redis_key} in Redis")
        return redis_key

    except Exception as e:
        logger.error(f"Failed to store export result in Redis: {e}")
        raise


def get_export_status(task_id: str) -> Optional[dict]:
    """Retrieve export task status from Redis.

    Args:
        task_id: Celery task ID

    Returns:
        Status dict or None if not found

    Raises:
        Exception: If Redis access fails
    """
    try:
        from redis import Redis

        redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)

        status_json = redis_client.get(f"export:task:{task_id}")
        if status_json:
            return json.loads(status_json)
        return None

    except Exception as e:
        logger.error(f"Failed to retrieve export status from Redis: {e}")
        raise


def get_export_result(task_id: str) -> Optional[bytes]:
    """Retrieve exported content from Redis.

    Args:
        task_id: Celery task ID

    Returns:
        Exported content as bytes or None if not found

    Raises:
        Exception: If Redis access fails
    """
    try:
        from redis import Redis

        redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)

        data = redis_client.get(f"export:result:{task_id}:data")
        if data:
            return data
        return None

    except Exception as e:
        logger.error(f"Failed to retrieve export result from Redis: {e}")
        raise


def get_export_metadata(task_id: str) -> Optional[dict]:
    """Retrieve export metadata from Redis.

    Args:
        task_id: Celery task ID

    Returns:
        Metadata dict or None if not found

    Raises:
        Exception: If Redis access fails
    """
    try:
        from redis import Redis

        redis_client = Redis.from_url(Config.CELERY_RESULT_BACKEND)

        metadata_json = redis_client.get(f"export:result:{task_id}:metadata")
        if metadata_json:
            return json.loads(metadata_json)
        return None

    except Exception as e:
        logger.error(f"Failed to retrieve export metadata from Redis: {e}")
        raise
