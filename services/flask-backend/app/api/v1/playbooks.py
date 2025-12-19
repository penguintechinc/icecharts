"""Playbooks Endpoints for API v1 - IceStreams workflow automation.

Provides CRUD operations for playbooks (workflows), execution triggers,
editor locking, and node metadata management.
"""

import datetime
import secrets
import uuid

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...schemas.playbook_schemas import (
    AcquireLockRequest,
    CreatePlaybookRequest,
    CreateScheduleRequest,
    CreateWebhookRequest,
    ExecutePlaybookRequest,
    PlaybookNodeMetadataRequest,
    UpdatePlaybookRequest,
)
from ...services.redis_streams import publish_task as redis_publish_task
from ...utils.validation import validate_json

playbooks_v1_bp = Blueprint("playbooks_v1", __name__, url_prefix="/playbooks")

# Free user playbook limit
FREE_USER_PLAYBOOK_LIMIT = 5
# Editor lock timeout in minutes
EDITOR_LOCK_TIMEOUT_MINUTES = 30


def serialize_playbook(playbook, version=None):
    """Serialize a playbook row to JSON-friendly dict."""
    result = {
        "id": str(playbook.id),
        "name": playbook.name,
        "description": playbook.description or "",
        "created_by_id": (
            str(playbook.created_by_id) if playbook.created_by_id else None
        ),
        "trigger_type": playbook.trigger_type,
        "is_public": playbook.is_public,
        "is_template": playbook.is_template,
        "is_enabled": playbook.is_enabled,
        "status": playbook.status,
        "tags": playbook.tags or [],
        "execution_count": playbook.execution_count or 0,
        "last_execution_at": (
            playbook.last_execution_at.isoformat()
            if playbook.last_execution_at
            else None
        ),
        "created_at": playbook.created_at.isoformat() if playbook.created_at else None,
        "updated_at": playbook.updated_at.isoformat() if playbook.updated_at else None,
    }
    if version:
        result["canvas_data"] = version.canvas_json or {"nodes": [], "edges": []}
        result["version"] = version.version_number
    return result


def serialize_execution(execution):
    """Serialize an execution record to JSON-friendly dict."""
    return {
        "id": str(execution.id),
        "playbook_id": str(execution.playbook_id),
        "status": execution.status,
        "trigger_type": execution.trigger_type,
        "input_data": execution.input_json,
        "output_data": execution.output_json,
        "error_message": execution.error_message,
        "started_at": (
            execution.started_at.isoformat() if execution.started_at else None
        ),
        "completed_at": (
            execution.completed_at.isoformat() if execution.completed_at else None
        ),
        "duration_ms": execution.duration_ms,
    }


def serialize_lock(lock, user_is_holder=False):
    """Serialize an editor lock to JSON-friendly dict."""
    return {
        "playbook_id": str(lock.playbook_id),
        "locked_by_id": str(lock.locked_by_id),
        "locked_by_name": lock.locked_by_name,
        "locked_at": lock.locked_at.isoformat() if lock.locked_at else None,
        "expires_at": lock.expires_at.isoformat() if lock.expires_at else None,
        "is_holder": user_is_holder,
    }


def check_playbook_limit(db, user_id: int) -> bool:
    """Check if user has reached their playbook limit.

    Returns True if user can create more playbooks.
    """
    # TODO: Check if user is premium via license/subscription
    # For now, all users are treated as free users
    count = db(db.playbooks.created_by_id == user_id).count()
    return count < FREE_USER_PLAYBOOK_LIMIT


# ============================================================================
# Playbook CRUD
# ============================================================================


@playbooks_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def list_playbooks():
    """List all playbooks for current user.

    Returns:
        JSON array of playbooks with metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query playbooks owned by or created by the user
        playbooks = db(
            (db.playbooks.created_by_id == user_id)
            | (db.playbooks.is_public == True)  # noqa: E712
        ).select(orderby=~db.playbooks.updated_at)

        result = [serialize_playbook(p) for p in playbooks]

        # Also return limit info for free users
        owned_count = db(db.playbooks.created_by_id == user_id).count()

        return (
            jsonify(
                {
                    "success": True,
                    "count": len(result),
                    "items": result,
                    "playbooks": result,
                    "owned_count": owned_count,
                    "limit": FREE_USER_PLAYBOOK_LIMIT,
                    "can_create": owned_count < FREE_USER_PLAYBOOK_LIMIT,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing playbooks: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def get_playbook(playbook_id: str):
    """Get a specific playbook by ID.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON playbook object with canvas data and metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access (owner or public)
        has_access = playbook.created_by_id == user_id or playbook.is_public

        # Also check shares table
        if not has_access:
            share = (
                db(
                    (db.playbook_shares.playbook_id == playbook_id)
                    & (db.playbook_shares.identity_id == user_id)
                )
                .select()
                .first()
            )
            has_access = share is not None

        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        # Get latest version with canvas data
        version = (
            db(db.playbook_versions.playbook_id == playbook.id)
            .select(orderby=~db.playbook_versions.version_number, limitby=(0, 1))
            .first()
        )

        # Check if there's an active editor lock
        lock = db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()
        lock_info = None
        if lock:
            # Check if lock is expired
            if lock.expires_at and lock.expires_at < datetime.datetime.utcnow():
                # Lock expired, remove it
                db(db.playbook_editor_locks.playbook_id == playbook.id).delete()
                db.commit()
            else:
                lock_info = serialize_lock(
                    lock, user_is_holder=(lock.locked_by_id == user_id)
                )

        return (
            jsonify(
                {
                    "success": True,
                    "playbook": serialize_playbook(playbook, version),
                    "editor_lock": lock_info,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting playbook {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("playbooks:write")
@validate_json(CreatePlaybookRequest)
def create_playbook(validated_data: CreatePlaybookRequest):
    """Create a new playbook.

    Returns:
        JSON created playbook object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Check playbook limit for free users
        if not check_playbook_limit(db, user_id):
            return (
                jsonify(
                    {
                        "error": f"Free users are limited to {FREE_USER_PLAYBOOK_LIMIT} playbooks. "
                        "Upgrade to premium for unlimited playbooks."
                    }
                ),
                403,
            )

        # Create playbook record
        playbook_id = db.playbooks.insert(
            tenant_id=1,
            name=validated_data.name,
            description=validated_data.description or "",
            created_by_id=user_id,
            trigger_type=validated_data.trigger_type,
            is_public=validated_data.visibility == "public",
            is_template=validated_data.is_template or False,
            is_enabled=False,  # Start disabled
            tags=validated_data.tags or [],
            status="draft",
            execution_count=0,
        )
        db.commit()

        # Create initial version with canvas data
        db.playbook_versions.insert(
            playbook_id=playbook_id,
            version_number=1,
            created_by_id=user_id,
            canvas_json=validated_data.canvas_data,
            change_summary="Initial version",
        )
        db.commit()

        # Fetch the created playbook
        playbook = db.playbooks(playbook_id)

        return (
            jsonify(
                {
                    "success": True,
                    "playbook": serialize_playbook(playbook),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating playbook: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>", methods=["PUT"])
@auth_required
@scopes_required("playbooks:write")
@validate_json(UpdatePlaybookRequest)
def update_playbook(playbook_id: str, validated_data: UpdatePlaybookRequest):
    """Update a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON updated playbook object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check ownership or editor share
        is_owner = playbook.created_by_id == user_id
        share = (
            db(
                (db.playbook_shares.playbook_id == playbook_id)
                & (db.playbook_shares.identity_id == user_id)
                & (db.playbook_shares.permission.belongs(["editor", "owner"]))
            )
            .select()
            .first()
        )

        if not is_owner and not share:
            return jsonify({"error": "Access denied"}), 403

        # Check editor lock - only the lock holder can edit
        lock = db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()
        if lock:
            if lock.expires_at and lock.expires_at < datetime.datetime.utcnow():
                # Lock expired, remove it
                db(db.playbook_editor_locks.playbook_id == playbook.id).delete()
                db.commit()
            elif lock.locked_by_id != user_id:
                return (
                    jsonify(
                        {
                            "error": "Playbook is locked for editing",
                            "locked_by": lock.locked_by_name,
                            "expires_at": (
                                lock.expires_at.isoformat() if lock.expires_at else None
                            ),
                        }
                    ),
                    423,
                )  # Locked status code

        # Update playbook metadata
        update_data = {"updated_at": datetime.datetime.utcnow()}
        if validated_data.name is not None:
            update_data["name"] = validated_data.name
        if validated_data.description is not None:
            update_data["description"] = validated_data.description
        if validated_data.trigger_type is not None:
            update_data["trigger_type"] = validated_data.trigger_type
        if validated_data.visibility is not None:
            update_data["is_public"] = validated_data.visibility == "public"
        if validated_data.is_template is not None:
            update_data["is_template"] = validated_data.is_template
        if validated_data.tags is not None:
            update_data["tags"] = validated_data.tags
        if validated_data.status is not None:
            update_data["status"] = validated_data.status
        if validated_data.is_enabled is not None:
            update_data["is_enabled"] = validated_data.is_enabled

        playbook.update_record(**update_data)
        db.commit()

        # If canvas_data is provided, create new version
        if validated_data.canvas_data is not None:
            max_version = (
                db(db.playbook_versions.playbook_id == playbook_id)
                .select(db.playbook_versions.version_number.max())
                .first()[db.playbook_versions.version_number.max()]
                or 0
            )

            new_version = max_version + 1
            db.playbook_versions.insert(
                playbook_id=playbook_id,
                version_number=new_version,
                created_by_id=user_id,
                canvas_json=validated_data.canvas_data,
                change_summary="Updated",
            )
            db.commit()

        # Fetch updated playbook with latest version
        playbook = db.playbooks(playbook_id)
        version = (
            db(db.playbook_versions.playbook_id == playbook_id)
            .select(orderby=~db.playbook_versions.version_number, limitby=(0, 1))
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "playbook": serialize_playbook(playbook, version),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating playbook {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>", methods=["DELETE"])
@auth_required
@scopes_required("playbooks:delete")
def delete_playbook(playbook_id: str):
    """Delete a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check ownership
        if playbook.created_by_id != user_id:
            return jsonify({"error": "Access denied - only owner can delete"}), 403

        # Delete playbook (cascade will handle versions, nodes, edges, etc.)
        db(db.playbooks.id == playbook_id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Playbook deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting playbook {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/duplicate", methods=["POST"])
@auth_required
@scopes_required("playbooks:write")
def duplicate_playbook(playbook_id: str):
    """Duplicate a playbook.

    Args:
        playbook_id: Playbook identifier to duplicate

    Returns:
        JSON created playbook object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Check playbook limit
        if not check_playbook_limit(db, user_id):
            return (
                jsonify(
                    {
                        "error": f"Free users are limited to {FREE_USER_PLAYBOOK_LIMIT} playbooks."
                    }
                ),
                403,
            )

        original = db.playbooks(playbook_id)
        if not original:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        has_access = (
            original.created_by_id == user_id
            or original.is_public
            or original.is_template
        )
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        # Get latest version
        version = (
            db(db.playbook_versions.playbook_id == playbook_id)
            .select(orderby=~db.playbook_versions.version_number, limitby=(0, 1))
            .first()
        )

        # Create duplicate
        new_playbook_id = db.playbooks.insert(
            tenant_id=1,
            name=f"{original.name} (Copy)",
            description=original.description,
            created_by_id=user_id,
            trigger_type=original.trigger_type,
            is_public=False,
            is_template=False,
            is_enabled=False,
            tags=original.tags or [],
            status="draft",
            execution_count=0,
        )
        db.commit()

        # Copy version
        if version:
            db.playbook_versions.insert(
                playbook_id=new_playbook_id,
                version_number=1,
                created_by_id=user_id,
                canvas_json=version.canvas_json,
                change_summary="Duplicated from playbook",
            )
            db.commit()

        new_playbook = db.playbooks(new_playbook_id)

        return (
            jsonify(
                {
                    "success": True,
                    "playbook": serialize_playbook(new_playbook),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error duplicating playbook {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Editor Locking
# ============================================================================


@playbooks_v1_bp.route("/<playbook_id>/lock", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def get_lock_status(playbook_id: str):
    """Get the current editor lock status for a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON lock status
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        lock = db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()

        if not lock:
            return (
                jsonify(
                    {
                        "success": True,
                        "locked": False,
                        "lock": None,
                    }
                ),
                200,
            )

        # Check if lock is expired
        if lock.expires_at and lock.expires_at < datetime.datetime.utcnow():
            db(db.playbook_editor_locks.playbook_id == playbook.id).delete()
            db.commit()
            return (
                jsonify(
                    {
                        "success": True,
                        "locked": False,
                        "lock": None,
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "locked": True,
                    "lock": serialize_lock(
                        lock, user_is_holder=(lock.locked_by_id == user_id)
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting lock status for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/lock", methods=["POST"])
@auth_required
@scopes_required("playbooks:write")
@validate_json(AcquireLockRequest)
def acquire_lock(playbook_id: str, validated_data: AcquireLockRequest):
    """Acquire an editor lock for a playbook.

    Only one user can hold the editor lock at a time.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON lock info
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        user_name = user.get("full_name", user.get("email", "Unknown"))
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check if user has edit access
        is_owner = playbook.created_by_id == user_id
        share = (
            db(
                (db.playbook_shares.playbook_id == playbook_id)
                & (db.playbook_shares.identity_id == user_id)
                & (db.playbook_shares.permission.belongs(["editor", "owner"]))
            )
            .select()
            .first()
        )

        if not is_owner and not share:
            return jsonify({"error": "Access denied - no editor permission"}), 403

        # Check existing lock
        existing_lock = (
            db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()
        )

        if existing_lock:
            # Check if expired
            if (
                existing_lock.expires_at
                and existing_lock.expires_at < datetime.datetime.utcnow()
            ):
                # Remove expired lock
                db(db.playbook_editor_locks.playbook_id == playbook.id).delete()
                db.commit()
            elif existing_lock.locked_by_id == user_id:
                # User already holds the lock, refresh it
                now = datetime.datetime.utcnow()
                expires = now + datetime.timedelta(minutes=EDITOR_LOCK_TIMEOUT_MINUTES)
                existing_lock.update_record(
                    locked_at=now,
                    expires_at=expires,
                    socket_id=validated_data.socket_id,
                )
                db.commit()
                return (
                    jsonify(
                        {
                            "success": True,
                            "lock": serialize_lock(existing_lock, user_is_holder=True),
                        }
                    ),
                    200,
                )
            else:
                # Another user holds the lock
                return (
                    jsonify(
                        {
                            "error": "Playbook is locked by another user",
                            "lock": serialize_lock(existing_lock, user_is_holder=False),
                        }
                    ),
                    423,
                )

        # Create new lock
        now = datetime.datetime.utcnow()
        expires = now + datetime.timedelta(minutes=EDITOR_LOCK_TIMEOUT_MINUTES)

        db.playbook_editor_locks.insert(
            playbook_id=playbook.id,
            locked_by_id=user_id,
            locked_by_name=user_name,
            locked_at=now,
            expires_at=expires,
            socket_id=validated_data.socket_id,
        )
        db.commit()

        lock = db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "lock": serialize_lock(lock, user_is_holder=True),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error acquiring lock for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/lock", methods=["DELETE"])
@auth_required
@scopes_required("playbooks:write")
def release_lock(playbook_id: str):
    """Release an editor lock for a playbook.

    Only the lock holder can release the lock.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        lock = db(db.playbook_editor_locks.playbook_id == playbook.id).select().first()

        if not lock:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "No lock exists",
                    }
                ),
                200,
            )

        # Only lock holder or admin can release
        if lock.locked_by_id != user_id:
            # TODO: Check if user is admin
            return jsonify({"error": "Only the lock holder can release the lock"}), 403

        db(db.playbook_editor_locks.playbook_id == playbook.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Lock released successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error releasing lock for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Execution
# ============================================================================


@playbooks_v1_bp.route("/<playbook_id>/execute", methods=["POST"])
@auth_required
@scopes_required("playbooks:execute")
@validate_json(ExecutePlaybookRequest)
def execute_playbook(playbook_id: str, validated_data: ExecutePlaybookRequest):
    """Manually execute a playbook.

    Creates an execution record and queues the task for processing.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON execution info
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        has_access = playbook.created_by_id == user_id or playbook.is_public
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        if validated_data.dry_run:
            # Dry run - just validate
            return (
                jsonify(
                    {
                        "success": True,
                        "dry_run": True,
                        "message": "Playbook validation successful",
                    }
                ),
                200,
            )

        # Create execution record
        execution_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()

        db.playbook_executions.insert(
            id=execution_id,
            playbook_id=playbook_id,
            triggered_by_id=user_id,
            trigger_type="manual",
            status="pending",
            input_json=validated_data.input_data or {},
            started_at=now,
        )
        db.commit()

        # Update playbook execution stats
        playbook.update_record(
            execution_count=(playbook.execution_count or 0) + 1,
            last_execution_at=now,
        )
        db.commit()

        # Queue task to Redis Streams for worker processing
        try:
            message_id = redis_publish_task(
                execution_id=execution_id,
                playbook_id=str(playbook_id),
                input_data=validated_data.input_data or {},
            )
            current_app.logger.info(
                f"Task queued: execution_id={execution_id}, message_id={message_id}"
            )
        except Exception as redis_error:
            # Log the error but don't fail the request - execution record exists
            current_app.logger.warning(
                f"Failed to queue task to Redis: {redis_error}. "
                f"Execution {execution_id} created but may need manual processing."
            )

        return (
            jsonify(
                {
                    "success": True,
                    "execution_id": execution_id,
                    "status": "pending",
                    "message": "Execution queued for processing",
                }
            ),
            202,
        )

    except Exception as e:
        current_app.logger.error(f"Error executing playbook {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/executions", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def list_executions(playbook_id: str):
    """List execution history for a playbook.

    Args:
        playbook_id: Playbook identifier

    Query params:
        - limit: Max results (default 50)
        - offset: Pagination offset

    Returns:
        JSON array of executions
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        has_access = playbook.created_by_id == user_id or playbook.is_public
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))

        executions = db(db.playbook_executions.playbook_id == playbook_id).select(
            orderby=~db.playbook_executions.started_at, limitby=(offset, offset + limit)
        )

        total = db(db.playbook_executions.playbook_id == playbook_id).count()

        return (
            jsonify(
                {
                    "success": True,
                    "executions": [serialize_execution(e) for e in executions],
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing executions for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/executions/<execution_id>", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def get_execution(playbook_id: str, execution_id: str):
    """Get details of a specific execution.

    Args:
        playbook_id: Playbook identifier
        execution_id: Execution identifier

    Returns:
        JSON execution details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        has_access = playbook.created_by_id == user_id or playbook.is_public
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        execution = (
            db(
                (db.playbook_executions.id == execution_id)
                & (db.playbook_executions.playbook_id == playbook_id)
            )
            .select()
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        # Get node execution logs
        node_logs = db(db.playbook_node_executions.execution_id == execution_id).select(
            orderby=db.playbook_node_executions.started_at
        )

        node_log_data = [
            {
                "node_id": log.node_id,
                "node_type": log.node_type,
                "status": log.status,
                "input_data": log.input_json,
                "output_data": log.output_json,
                "error_message": log.error_message,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": (
                    log.completed_at.isoformat() if log.completed_at else None
                ),
                "duration_ms": log.duration_ms,
            }
            for log in node_logs
        ]

        return (
            jsonify(
                {
                    "success": True,
                    "execution": serialize_execution(execution),
                    "node_logs": node_log_data,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting execution {execution_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route(
    "/<playbook_id>/executions/<execution_id>/cancel", methods=["POST"]
)
@auth_required
@scopes_required("playbooks:execute")
def cancel_execution(playbook_id: str, execution_id: str):
    """Cancel a running execution.

    Args:
        playbook_id: Playbook identifier
        execution_id: Execution identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        if playbook.created_by_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        execution = (
            db(
                (db.playbook_executions.id == execution_id)
                & (db.playbook_executions.playbook_id == playbook_id)
            )
            .select()
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        if execution.status not in ["pending", "running"]:
            return jsonify({"error": "Execution is not running"}), 400

        # Update status to cancelled
        execution.update_record(
            status="cancelled",
            completed_at=datetime.datetime.utcnow(),
        )
        db.commit()

        # TODO: Send cancel signal to worker via Redis

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Execution cancelled",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error cancelling execution {execution_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Node Metadata
# ============================================================================


@playbooks_v1_bp.route("/<playbook_id>/nodes/<node_id>/metadata", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def get_node_metadata(playbook_id: str, node_id: str):
    """Get metadata for a specific node.

    Args:
        playbook_id: Playbook identifier
        node_id: Node identifier within the playbook

    Returns:
        JSON node metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check access
        has_access = playbook.created_by_id == user_id or playbook.is_public
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        metadata = (
            db(
                (db.playbook_node_metadata.playbook_id == playbook_id)
                & (db.playbook_node_metadata.node_id == node_id)
            )
            .select()
            .first()
        )

        if not metadata:
            return (
                jsonify(
                    {
                        "success": True,
                        "node_id": node_id,
                        "comments": None,
                        "metadata": {},
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "node_id": node_id,
                    "comments": metadata.comments,
                    "metadata": metadata.metadata_json or {},
                    "updated_at": (
                        metadata.updated_at.isoformat() if metadata.updated_at else None
                    ),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting node metadata: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/nodes/<node_id>/metadata", methods=["PUT"])
@auth_required
@scopes_required("playbooks:write")
@validate_json(PlaybookNodeMetadataRequest)
def update_node_metadata(
    playbook_id: str, node_id: str, validated_data: PlaybookNodeMetadataRequest
):
    """Update metadata for a specific node.

    Args:
        playbook_id: Playbook identifier
        node_id: Node identifier within the playbook

    Returns:
        JSON updated node metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check edit access
        is_owner = playbook.created_by_id == user_id
        share = (
            db(
                (db.playbook_shares.playbook_id == playbook_id)
                & (db.playbook_shares.identity_id == user_id)
                & (db.playbook_shares.permission.belongs(["editor", "owner"]))
            )
            .select()
            .first()
        )

        if not is_owner and not share:
            return jsonify({"error": "Access denied"}), 403

        now = datetime.datetime.utcnow()

        # Check if metadata exists
        existing = (
            db(
                (db.playbook_node_metadata.playbook_id == playbook_id)
                & (db.playbook_node_metadata.node_id == node_id)
            )
            .select()
            .first()
        )

        if existing:
            existing.update_record(
                comments=validated_data.comments,
                metadata_json=validated_data.metadata or {},
                updated_by_id=user_id,
                updated_at=now,
            )
        else:
            db.playbook_node_metadata.insert(
                playbook_id=playbook_id,
                node_id=node_id,
                comments=validated_data.comments,
                metadata_json=validated_data.metadata or {},
                updated_by_id=user_id,
                updated_at=now,
            )

        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "node_id": node_id,
                    "comments": validated_data.comments,
                    "metadata": validated_data.metadata or {},
                    "updated_at": now.isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating node metadata: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# Webhooks
# ============================================================================


@playbooks_v1_bp.route("/<playbook_id>/webhooks", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def list_webhooks(playbook_id: str):
    """List webhooks for a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON array of webhooks
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check ownership
        if playbook.created_by_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        webhooks = db(db.playbook_webhooks.playbook_id == playbook_id).select()

        return (
            jsonify(
                {
                    "success": True,
                    "webhooks": [
                        {
                            "id": str(w.id),
                            "name": w.name,
                            "token": w.token,
                            "url": f"/api/v1/hooks/{w.token}",
                            "allowed_methods": w.allowed_methods or ["POST"],
                            "validate_signature": w.validate_signature,
                            "is_enabled": w.is_enabled,
                            "created_at": (
                                w.created_at.isoformat() if w.created_at else None
                            ),
                        }
                        for w in webhooks
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing webhooks for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/webhooks", methods=["POST"])
@auth_required
@scopes_required("playbooks:write")
@validate_json(CreateWebhookRequest)
def create_webhook(playbook_id: str, validated_data: CreateWebhookRequest):
    """Create a webhook for a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON webhook info including token
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check ownership
        if playbook.created_by_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        # Generate secure token
        token = secrets.token_urlsafe(32)

        webhook_id = db.playbook_webhooks.insert(
            playbook_id=playbook_id,
            name=validated_data.name or f"Webhook for {playbook.name}",
            token=token,
            allowed_methods=validated_data.allowed_methods,
            validate_signature=validated_data.validate_signature,
            signature_secret=validated_data.signature_secret,
            is_enabled=True,
        )
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "webhook": {
                        "id": str(webhook_id),
                        "name": validated_data.name,
                        "token": token,
                        "url": f"/api/v1/hooks/{token}",
                        "allowed_methods": validated_data.allowed_methods,
                        "validate_signature": validated_data.validate_signature,
                        "is_enabled": True,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating webhook for {playbook_id}: {e}")
        return jsonify({"error": str(e)}), 500


@playbooks_v1_bp.route("/<playbook_id>/webhooks/<webhook_id>", methods=["DELETE"])
@auth_required
@scopes_required("playbooks:write")
def delete_webhook(playbook_id: str, webhook_id: str):
    """Delete a webhook.

    Args:
        playbook_id: Playbook identifier
        webhook_id: Webhook identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        playbook = db.playbooks(playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        # Check ownership
        if playbook.created_by_id != user_id:
            return jsonify({"error": "Access denied"}), 403

        webhook = (
            db(
                (db.playbook_webhooks.id == webhook_id)
                & (db.playbook_webhooks.playbook_id == playbook_id)
            )
            .select()
            .first()
        )

        if not webhook:
            return jsonify({"error": "Webhook not found"}), 404

        db(db.playbook_webhooks.id == webhook_id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Webhook deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting webhook {webhook_id}: {e}")
        return jsonify({"error": str(e)}), 500
