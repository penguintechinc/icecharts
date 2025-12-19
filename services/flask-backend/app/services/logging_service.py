"""Logging Service - Business logic for activity and audit logging."""

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional

from flask import g, request

from ..models import get_db

logger = logging.getLogger(__name__)


class LoggingService:
    """Service class for activity and audit logging operations."""

    @staticmethod
    def log_activity(
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        tenant_id: int = 1,
    ) -> Optional[int]:
        """
        Log a user activity.

        Args:
            user_id: ID of the user performing the action
            action: Action name (e.g., "login", "drawing_created", "drawing_shared")
            resource_type: Type of resource being acted upon (e.g., "drawing", "comment")
            resource_id: ID of the resource
            resource_name: Human-readable name of the resource
            details: Additional context-specific data
            tenant_id: Tenant ID (defaults to 1)

        Returns:
            ID of the created activity log record, or None if creation failed
        """
        try:
            db = get_db()

            log_id = db.activity_logs.insert(
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                details=details,
                ip_address=request.remote_addr if request else None,
                user_agent=(
                    request.user_agent.string
                    if request and request.user_agent
                    else None
                ),
                timestamp=datetime.now(timezone.utc),
            )
            db.commit()
            return log_id
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
            return None

    @staticmethod
    def log_audit(
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        user_id: Optional[int] = None,
        tenant_id: int = 1,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> Optional[int]:
        """
        Log an audit action (admin/sensitive operations).

        Args:
            action: Action name (e.g., "user_created", "user_updated", "user_deleted")
            resource_type: Type of resource being modified (e.g., "user", "group", "settings")
            resource_id: ID of the resource
            resource_name: Human-readable name of the resource
            changes: Detailed change data with old_value and new_value for each field
            reason: Reason for the action
            user_id: ID of the admin/user making the change (optional)
            tenant_id: Tenant ID (defaults to 1)
            status: "success" or "failed"
            error_message: Error message if status is "failed"

        Returns:
            ID of the created audit log record, or None if creation failed
        """
        try:
            db = get_db()

            # Get user_id from context if not provided
            if user_id is None:
                current_user = getattr(g, "current_user", None)
                if current_user:
                    user_id = current_user.get("id")

            log_id = db.audit_logs.insert(
                user_id=user_id,
                tenant_id=tenant_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                changes=changes,
                reason=reason,
                ip_address=request.remote_addr if request else None,
                user_agent=(
                    request.user_agent.string
                    if request and request.user_agent
                    else None
                ),
                status=status,
                error_message=error_message,
                timestamp=datetime.now(timezone.utc),
            )
            db.commit()
            return log_id
        except Exception as e:
            logger.error(f"Failed to log audit: {str(e)}")
            return None

    @staticmethod
    def get_activity_logs(
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: int = 1,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple:
        """
        Retrieve activity logs with filtering.

        Args:
            user_id: Filter by user ID
            action: Filter by action name
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date
            tenant_id: Tenant ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Tuple of (logs list, total count)
        """
        try:
            db = get_db()

            # Build query conditions
            conditions = [db.activity_logs.tenant_id == tenant_id]

            if user_id is not None:
                conditions.append(db.activity_logs.user_id == user_id)

            if action:
                conditions.append(db.activity_logs.action == action)

            if resource_type:
                conditions.append(db.activity_logs.resource_type == resource_type)

            if start_date:
                conditions.append(db.activity_logs.timestamp >= start_date)

            if end_date:
                conditions.append(db.activity_logs.timestamp <= end_date)

            # Combine conditions
            combined = conditions[0]
            for cond in conditions[1:]:
                combined = combined & cond

            # Query
            query = db(combined)
            total = query.count()

            logs = query.select(
                orderby=~db.activity_logs.timestamp,
                limitby=(offset, offset + limit),
            )

            # Convert to list of dicts
            result = []
            for log in logs:
                log_dict = log.as_dict()
                # Include user info
                if log.user_id:
                    user = db.identities(log.user_id)
                    if user:
                        log_dict["user"] = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "full_name": user.full_name,
                        }
                result.append(log_dict)

            return result, total

        except Exception as e:
            logger.error(f"Failed to retrieve activity logs: {str(e)}")
            return [], 0

    @staticmethod
    def get_audit_logs(
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: int = 1,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple:
        """
        Retrieve audit logs with filtering.

        Args:
            user_id: Filter by user ID
            action: Filter by action name
            resource_type: Filter by resource type
            start_date: Filter by start date
            end_date: Filter by end date
            tenant_id: Tenant ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Tuple of (logs list, total count)
        """
        try:
            db = get_db()

            # Build query conditions
            conditions = [db.audit_logs.tenant_id == tenant_id]

            if user_id is not None:
                conditions.append(db.audit_logs.user_id == user_id)

            if action:
                conditions.append(db.audit_logs.action == action)

            if resource_type:
                conditions.append(db.audit_logs.resource_type == resource_type)

            if start_date:
                conditions.append(db.audit_logs.timestamp >= start_date)

            if end_date:
                conditions.append(db.audit_logs.timestamp <= end_date)

            # Combine conditions
            combined = conditions[0]
            for cond in conditions[1:]:
                combined = combined & cond

            # Query
            query = db(combined)
            total = query.count()

            logs = query.select(
                orderby=~db.audit_logs.timestamp,
                limitby=(offset, offset + limit),
            )

            # Convert to list of dicts
            result = []
            for log in logs:
                log_dict = log.as_dict()
                # Include user info
                if log.user_id:
                    user = db.identities(log.user_id)
                    if user:
                        log_dict["user"] = {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "full_name": user.full_name,
                        }
                result.append(log_dict)

            return result, total

        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {str(e)}")
            return [], 0


def log_activity_decorator(
    action: str,
    resource_type: Optional[str] = None,
    include_args: Optional[list] = None,
):
    """
    Decorator to automatically log user activity on function execution.

    Args:
        action: Action name to log
        resource_type: Type of resource being acted upon
        include_args: List of argument names to include in resource details

    Usage:
        @log_activity_decorator("drawing_created", "drawing", include_args=["title"])
        def create_drawing(title, description):
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            current_user = getattr(g, "current_user", None)

            try:
                # Execute function
                result = f(*args, **kwargs)

                # Log activity if user is authenticated
                if current_user:
                    details = {}

                    # Extract specified arguments
                    if include_args:
                        # Try to extract from kwargs first
                        for arg_name in include_args:
                            if arg_name in kwargs:
                                details[arg_name] = kwargs[arg_name]

                    LoggingService.log_activity(
                        user_id=current_user.get("id"),
                        action=action,
                        resource_type=resource_type,
                        details=details if details else None,
                    )

                return result

            except Exception as e:
                logger.error(f"Error in log_activity_decorator: {str(e)}")
                # Still raise the original exception
                raise

        return wrapper

    return decorator


def log_audit_decorator(
    action: str,
    resource_type: str,
    include_args: Optional[list] = None,
):
    """
    Decorator to automatically log audit actions on function execution.

    Args:
        action: Action name to log
        resource_type: Type of resource being modified
        include_args: List of argument names to include in details

    Usage:
        @log_audit_decorator("user_created", "user", include_args=["email"])
        def create_user(email, full_name):
            ...
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            current_user = getattr(g, "current_user", None)

            try:
                # Execute function
                result = f(*args, **kwargs)

                # Log audit
                details = {}

                if include_args:
                    for arg_name in include_args:
                        if arg_name in kwargs:
                            details[arg_name] = kwargs[arg_name]

                LoggingService.log_audit(
                    action=action,
                    resource_type=resource_type,
                    user_id=current_user.get("id") if current_user else None,
                    changes=details if details else None,
                )

                return result

            except Exception as e:
                logger.error(f"Error in log_audit_decorator: {str(e)}")
                raise

        return wrapper

    return decorator
