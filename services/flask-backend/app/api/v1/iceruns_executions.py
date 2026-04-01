"""IceRuns Execution Management Endpoints for API v1.

Provides execution lifecycle management, logs, and real-time status updates.
"""

import datetime
import secrets

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...services.iceruns_storage_service import IceRunsStorageService
from ...services.redis_streams import RedisStreams

iceruns_executions_v1_bp = Blueprint(
    "iceruns_executions_v1", __name__, url_prefix="/iceruns"
)


def serialize_execution(execution):
    """Serialize execution to JSON."""
    return {
        "execution_id": execution.execution_id,
        "function_id": execution.function_id,
        "status": execution.status,
        "trigger_type": execution.trigger_type,
        "triggered_by": execution.triggered_by,
        "input_json": execution.input_json,
        "output_json": execution.output_json,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
        "exit_code": execution.exit_code,
        "error_message": execution.error_message,
        "worker_id": execution.worker_id,
        "container_id": execution.container_id,
        "started_at": (
            execution.started_at.isoformat() if execution.started_at else None
        ),
        "completed_at": (
            execution.completed_at.isoformat() if execution.completed_at else None
        ),
        "duration_ms": execution.duration_ms,
        "memory_used_mb": execution.memory_used_mb,
        "cpu_time_ms": execution.cpu_time_ms,
        "retry_count": execution.retry_count or 0,
        "created_at": (
            execution.created_at.isoformat() if execution.created_at else None
        ),
    }


@iceruns_executions_v1_bp.route("/executions", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def list_executions():
    """List all executions for current user."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query filters
        status = request.args.get("status")
        function_id = request.args.get("function_id")
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))

        # Build query
        query = db.iceruns.created_by_id == user_id
        if function_id:
            func = (
                db(
                    (db.iceruns.function_id == function_id)
                    & (db.iceruns.created_by_id == user_id)
                )
                .select()
                .first()
            )
            if not func:
                return jsonify({"error": "Function not found"}), 404
            query = db.iceruns_executions.function_id == func.id

        if status:
            query &= db.iceruns_executions.status == status

        executions = db(query).select(
            db.iceruns_executions.ALL,
            orderby=~db.iceruns_executions.created_at,
            limitby=(offset, offset + limit),
        )

        result = [serialize_execution(e) for e in executions]

        return jsonify({"success": True, "count": len(result), "items": result}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing executions: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/<function_id>/executions", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def list_function_executions(function_id: str):
    """List executions for specific function."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = (
            db(
                (db.iceruns.function_id == function_id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select()
            .first()
        )

        if not func:
            return jsonify({"error": "Function not found"}), 404

        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))

        executions = db(db.iceruns_executions.function_id == func.id).select(
            orderby=~db.iceruns_executions.created_at, limitby=(offset, offset + limit)
        )

        result = [serialize_execution(e) for e in executions]

        return jsonify({"success": True, "count": len(result), "items": result}), 200

    except Exception as e:
        current_app.logger.error(f"Error listing function executions: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/<function_id>/execute", methods=["POST"])
@auth_required
@scopes_required("iceruns:execute")
def execute_function(function_id: str):
    """Execute function via API."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json() or {}
        db = get_db()

        # Get function
        func = (
            db(
                (db.iceruns.function_id == function_id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select()
            .first()
        )

        if not func:
            return jsonify({"error": "Function not found"}), 404

        if func.status != "active":
            return (
                jsonify({"error": f"Function is not active (status: {func.status})"}),
                400,
            )

        if not func.package_key:
            return jsonify({"error": "Function has no package"}), 400

        # Create execution record
        execution_id = secrets.token_urlsafe(16)
        input_data = data.get("input", {})
        async_mode = data.get("async", True)
        timeout_override = data.get("timeout_override")

        exec_id = db.iceruns_executions.insert(
            execution_id=execution_id,
            function_id=func.id,
            status="queued",
            trigger_type="api",
            triggered_by=str(user_id),
            input_json=input_data,
            created_at=datetime.datetime.utcnow(),
        )

        db.commit()

        # Publish to Redis Streams
        redis = RedisStreams()
        config = {
            "runtime": func.runtime,
            "entrypoint": func.entrypoint,
            "handler": func.handler,
            "memory_limit_mb": func.memory_limit_mb,
            "timeout_seconds": timeout_override or func.timeout_seconds,
            "cpu_limit": func.cpu_limit,
            "env_vars": func.env_vars or {},
            "secrets": func.secrets or {},
            "package_key": func.package_key,
        }

        redis.publish_icerun_task(execution_id, function_id, input_data, config)

        # Update execution count
        db(db.iceruns.id == func.id).update(
            execution_count=(func.execution_count or 0) + 1,
            last_executed_at=datetime.datetime.utcnow(),
        )
        db.commit()

        # Return immediately (async) or wait for completion (sync)
        if async_mode:
            return (
                jsonify(
                    {
                        "success": True,
                        "execution_id": execution_id,
                        "status": "queued",
                        "function_id": function_id,
                        "created_at": datetime.datetime.utcnow().isoformat(),
                        "status_url": f"/api/v1/iceruns/executions/{execution_id}/status",
                    }
                ),
                202,
            )
        else:
            # Wait for completion (max 60s)
            import time

            for _ in range(120):  # Poll every 0.5s for 60s
                time.sleep(0.5)
                execution = db.iceruns_executions[exec_id]
                if execution.status in ["completed", "failed", "timeout", "cancelled"]:
                    return (
                        jsonify(
                            {
                                "success": True,
                                "execution": serialize_execution(execution),
                            }
                        ),
                        200,
                    )

            return jsonify({"error": "Execution timeout waiting for result"}), 504

    except Exception as e:
        current_app.logger.error(f"Error executing function: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def get_execution(execution_id: str):
    """Get execution details."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        return (
            jsonify({"success": True, "execution": serialize_execution(execution)}),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting execution: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceruns:execute")
def cancel_execution(execution_id: str):
    """Cancel running execution."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        if execution.status not in ["queued", "running"]:
            return (
                jsonify(
                    {"error": f"Cannot cancel execution in status: {execution.status}"}
                ),
                400,
            )

        db(db.iceruns_executions.execution_id == execution_id).update(
            status="cancelled", completed_at=datetime.datetime.utcnow()
        )
        db.commit()

        return jsonify({"success": True, "message": "Execution cancelled"}), 200

    except Exception as e:
        current_app.logger.error(f"Error cancelling execution: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>/logs", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def get_execution_logs(execution_id: str):
    """Get execution logs."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        # Load full logs from S3 if available
        if execution.logs_key:
            logs = IceRunsStorageService.load_execution_logs(execution_id)
            return jsonify({"success": True, "logs": logs, "source": "s3"}), 200
        else:
            # Use inline logs
            logs = f"STDOUT:\n{execution.stdout or ''}\n\nSTDERR:\n{execution.stderr or ''}"
            return jsonify({"success": True, "logs": logs, "source": "inline"}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting execution logs: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>/output", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def get_execution_output(execution_id: str):
    """Get execution output JSON."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        return jsonify({"success": True, "output": execution.output_json}), 200

    except Exception as e:
        current_app.logger.error(f"Error getting execution output: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>/status", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def get_execution_status(execution_id: str):
    """Get execution status (for polling)."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        # Check Redis for real-time status
        redis = RedisStreams()
        status = redis.get_icerun_status(execution_id)

        if status:
            return jsonify({"success": True, "status": status}), 200
        else:
            # Fallback to database
            return (
                jsonify(
                    {
                        "success": True,
                        "status": execution.status,
                        "output": execution.output_json,
                        "exit_code": execution.exit_code,
                        "duration_ms": execution.duration_ms,
                    }
                ),
                200,
            )

    except Exception as e:
        current_app.logger.error(f"Error getting execution status: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>/retry", methods=["POST"])
@auth_required
@scopes_required("iceruns:execute")
def retry_execution(execution_id: str):
    """Retry failed execution."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        if execution.status not in ["failed", "timeout"]:
            return (
                jsonify({"error": "Can only retry failed or timeout executions"}),
                400,
            )

        # Get function
        func = db.iceruns[execution.function_id]

        # Create new execution
        new_execution_id = secrets.token_urlsafe(16)

        new_exec_id = db.iceruns_executions.insert(
            execution_id=new_execution_id,
            function_id=func.id,
            status="queued",
            trigger_type="retry",
            triggered_by=str(user_id),
            input_json=execution.input_json,
            parent_execution_id=execution_id,
            retry_count=(execution.retry_count or 0) + 1,
            created_at=datetime.datetime.utcnow(),
        )

        db.commit()

        # Publish to Redis Streams
        redis = RedisStreams()
        config = {
            "runtime": func.runtime,
            "entrypoint": func.entrypoint,
            "handler": func.handler,
            "memory_limit_mb": func.memory_limit_mb,
            "timeout_seconds": func.timeout_seconds,
            "cpu_limit": func.cpu_limit,
            "env_vars": func.env_vars or {},
            "secrets": func.secrets or {},
            "package_key": func.package_key,
        }

        redis.publish_icerun_task(
            new_execution_id, func.function_id, execution.input_json, config
        )

        return (
            jsonify(
                {
                    "success": True,
                    "execution_id": new_execution_id,
                    "parent_execution_id": execution_id,
                    "status": "queued",
                }
            ),
            202,
        )

    except Exception as e:
        current_app.logger.error(f"Error retrying execution: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/executions/<execution_id>/artifacts", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def list_artifacts(execution_id: str):
    """List execution artifacts."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        execution = (
            db(
                (db.iceruns_executions.execution_id == execution_id)
                & (db.iceruns_executions.function_id == db.iceruns.id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select(db.iceruns_executions.ALL)
            .first()
        )

        if not execution:
            return jsonify({"error": "Execution not found"}), 404

        if not execution.artifacts_key:
            return jsonify({"success": True, "artifacts": []}), 200

        # List artifacts from S3 (stub - implement in storage service)
        return (
            jsonify(
                {
                    "success": True,
                    "artifacts": [],
                    "artifacts_key": execution.artifacts_key,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing artifacts: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_executions_v1_bp.route("/<function_id>/stats", methods=["GET"])
@auth_required
@scopes_required("iceruns:logs")
def get_function_stats(function_id: str):
    """Get function execution statistics."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = (
            db(
                (db.iceruns.function_id == function_id)
                & (db.iceruns.created_by_id == user_id)
            )
            .select()
            .first()
        )

        if not func:
            return jsonify({"error": "Function not found"}), 404

        # Calculate stats
        total = db(db.iceruns_executions.function_id == func.id).count()
        completed = db(
            (db.iceruns_executions.function_id == func.id)
            & (db.iceruns_executions.status == "completed")
        ).count()
        failed = db(
            (db.iceruns_executions.function_id == func.id)
            & (db.iceruns_executions.status == "failed")
        ).count()
        avg_duration = (
            db(db.iceruns_executions.function_id == func.id)
            .select(db.iceruns_executions.duration_ms.avg().with_alias("avg_duration"))
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "stats": {
                        "total_executions": total,
                        "completed": completed,
                        "failed": failed,
                        "success_rate": (completed / total * 100) if total > 0 else 0,
                        "avg_duration_ms": (
                            avg_duration.avg_duration if avg_duration else 0
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting function stats: {e}")
        return jsonify({"error": str(e)}), 500
