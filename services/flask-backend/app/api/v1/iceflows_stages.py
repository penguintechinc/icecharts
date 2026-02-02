"""IceFlows Stage Configuration Endpoints for API v1.

Provides CRUD operations for stage configurations including:
- Approvers: Approval authority per stage
- Tests: Test execution configuration per stage
- Calls: IceStreams/IceRuns triggers per stage
- Reviews: Darwin code review configuration per stage
"""

import datetime
import uuid

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db

iceflows_stages_bp = Blueprint(
    "iceflows_stages", __name__, url_prefix="/iceflows/stages"
)


def serialize_approver(approver, user_data=None, group_data=None):
    """Serialize approver record to JSON-safe dict.

    Args:
        approver: Database approver record
        user_data: Optional user details
        group_data: Optional group details

    Returns:
        Dictionary representation of approver
    """
    result = {
        "approver_id": approver.approver_id,
        "stage_id": approver.stage_id,
        "identity_id": approver.identity_id,
        "group_id": approver.group_id,
        "role": approver.role or "approver",
        "can_override": approver.can_override or False,
        "created_at": approver.created_at.isoformat() if approver.created_at else None,
    }

    if user_data:
        result["user_name"] = user_data.get("full_name") or user_data.get("username")
        result["user_email"] = user_data.get("email")
    if group_data:
        result["group_name"] = group_data.get("name")
        result["group_description"] = group_data.get("description")

    return result


def serialize_test(test):
    """Serialize test record to JSON-safe dict.

    Args:
        test: Database test record

    Returns:
        Dictionary representation of test
    """
    return {
        "test_id": test.test_id,
        "stage_id": test.stage_id,
        "name": test.name,
        "test_type": test.test_type,
        "path_mode": test.path_mode or "repo_relative",
        "centralized_path": test.centralized_path or "",
        "repo_relative_path": test.repo_relative_path or "",
        "command": test.command or "",
        "timeout_seconds": test.timeout_seconds or 600,
        "is_blocking": test.is_blocking or True,
        "is_required": test.is_required or True,
        "execution_order": test.execution_order or 0,
        "env_vars": test.env_vars or {},
        "created_at": test.created_at.isoformat() if test.created_at else None,
    }


def serialize_call(call, target_name=None):
    """Serialize call record to JSON-safe dict.

    Args:
        call: Database call record
        target_name: Optional name of target (playbook or function)

    Returns:
        Dictionary representation of call
    """
    result = {
        "call_id": call.call_id,
        "stage_id": call.stage_id,
        "name": call.name,
        "call_type": call.call_type,
        "target_id": call.target_id,
        "trigger_on": call.trigger_on or "on_promotion",
        "input_template": call.input_template or {},
        "timeout_seconds": call.timeout_seconds or 300,
        "is_blocking": call.is_blocking or True,
        "retry_count": call.retry_count or 0,
        "execution_order": call.execution_order or 0,
        "created_at": call.created_at.isoformat() if call.created_at else None,
    }

    if target_name:
        result["target_name"] = target_name

    return result


def serialize_review(review):
    """Serialize review record to JSON-safe dict.

    Args:
        review: Database review record

    Returns:
        Dictionary representation of review
    """
    return {
        "review_id": review.review_id,
        "stage_id": review.stage_id,
        "is_required": review.is_required or True,
        "review_type": review.review_type or "inherit",
        "min_score": review.min_score or 70,
        "block_on_critical": review.block_on_critical or True,
        "allowed_issue_types": review.allowed_issue_types or [],
        "reviewers_notified": review.reviewers_notified or True,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }


def get_stage_or_404(stage_id: str, flow_id: str = None):
    """Get stage by ID or return None if not found.

    Args:
        stage_id: Stage identifier
        flow_id: Optional flow identifier for verification

    Returns:
        Stage record or None
    """
    db = get_db()
    query = db.iceflows_stages.stage_id == stage_id

    if flow_id:
        query &= db.iceflows_stages.flow_id == flow_id

    return db(query).select().first()


def verify_stage_access(stage, user_id):
    """Verify user has access to stage's flow.

    Args:
        stage: Stage record
        user_id: User identifier

    Returns:
        True if user has access, False otherwise
    """
    db = get_db()
    flow = db((db.iceflows.id == stage.flow_id)).select().first()
    return flow and flow.created_by_id == user_id


# ============================================================================
# Approvers Endpoints
# ============================================================================


@iceflows_stages_bp.route("/<stage_id>/approvers", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_approvers(stage_id: str):
    """List all approvers for a stage.

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with approvers array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        approvers = db(
            db.iceflows_stage_approvers.stage_id == stage.id
        ).select(orderby=db.iceflows_stage_approvers.created_at)

        result = []
        for approver in approvers:
            user_data = None
            group_data = None

            if approver.identity_id:
                user_row = db.identities[approver.identity_id]
                if user_row:
                    user_data = {
                        "full_name": user_row.full_name,
                        "username": user_row.username,
                        "email": user_row.email,
                    }

            if approver.group_id:
                group_row = db.groups[approver.group_id]
                if group_row:
                    group_data = {
                        "name": group_row.name,
                        "description": group_row.description,
                    }

            result.append(serialize_approver(approver, user_data, group_data))

        return (
            jsonify(
                {
                    "success": True,
                    "approvers": result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing approvers for stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/approvers", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def add_approver(stage_id: str):
    """Add an approver to a stage.

    Request body:
        - identity_id or group_id (required): User or group identifier
        - role (optional): approver, admin, or reviewer (default: approver)
        - can_override (optional): Can override min approvers (default: false)

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with created approver
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        identity_id = data.get("identity_id")
        group_id = data.get("group_id")

        if not identity_id and not group_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "identity_id or group_id is required",
                    }
                ),
                400,
            )

        if identity_id and group_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Cannot specify both identity_id and group_id",
                    }
                ),
                400,
            )

        if identity_id:
            identity = db.identities[int(identity_id)]
            if not identity:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Identity not found",
                        }
                    ),
                    400,
                )

        if group_id:
            group = db.groups[int(group_id)]
            if not group:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Group not found",
                        }
                    ),
                    400,
                )

        existing = db(
            (db.iceflows_stage_approvers.stage_id == stage.id)
            & (
                (db.iceflows_stage_approvers.identity_id == identity_id)
                | (db.iceflows_stage_approvers.group_id == group_id)
            )
        ).select().first()

        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Approver already exists for this stage",
                    }
                ),
                409,
            )

        approver_id = str(uuid.uuid4())
        role = data.get("role", "approver")

        if role not in ["approver", "admin", "reviewer"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid role. Must be: approver, admin, or reviewer",
                    }
                ),
                400,
            )

        db.iceflows_stage_approvers.insert(
            approver_id=approver_id,
            stage_id=stage.id,
            identity_id=identity_id,
            group_id=group_id,
            role=role,
            can_override=data.get("can_override", False),
        )
        db.commit()

        approver = db(
            db.iceflows_stage_approvers.approver_id == approver_id
        ).select().first()

        user_data = None
        group_data = None

        if approver.identity_id:
            user_row = db.identities[approver.identity_id]
            if user_row:
                user_data = {
                    "full_name": user_row.full_name,
                    "username": user_row.username,
                    "email": user_row.email,
                }

        if approver.group_id:
            group_row = db.groups[approver.group_id]
            if group_row:
                group_data = {
                    "name": group_row.name,
                    "description": group_row.description,
                }

        return (
            jsonify(
                {
                    "success": True,
                    "approver": serialize_approver(approver, user_data, group_data),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error adding approver to stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/approvers/<approver_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:write")
def remove_approver(stage_id: str, approver_id: str):
    """Remove an approver from a stage.

    Args:
        stage_id: Stage identifier
        approver_id: Approver identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        approver = db(
            (db.iceflows_stage_approvers.approver_id == approver_id)
            & (db.iceflows_stage_approvers.stage_id == stage.id)
        ).select().first()

        if not approver:
            return (
                jsonify({"success": False, "error": "Approver not found"}),
                404,
            )

        db(db.iceflows_stage_approvers.id == approver.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Approver removed successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error removing approver {approver_id} from stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Tests Endpoints
# ============================================================================


@iceflows_stages_bp.route("/<stage_id>/tests", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_tests(stage_id: str):
    """List all tests for a stage.

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with tests array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        tests = db(db.iceflows_stage_tests.stage_id == stage.id).select(
            orderby=db.iceflows_stage_tests.execution_order
        )

        return (
            jsonify(
                {
                    "success": True,
                    "tests": [serialize_test(test) for test in tests],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing tests for stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/tests", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def add_test(stage_id: str):
    """Add a test to a stage.

    Request body:
        - name (required): Test name
        - test_type (required): unit, integration, e2e, or custom
        - path_mode (optional): centralized or repo_relative (default: repo_relative)
        - centralized_path (optional): Path for centralized mode
        - repo_relative_path (optional): Path for repo_relative mode
        - command (optional): Custom test command
        - timeout_seconds (optional): Timeout in seconds (default: 600)
        - is_blocking (optional): Block pipeline on failure (default: true)
        - is_required (optional): Test is required (default: true)
        - execution_order (optional): Execution order (auto-assigned if not provided)
        - env_vars (optional): Environment variables JSON

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with created test
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        if not data.get("name"):
            return (
                jsonify({"success": False, "error": "name is required"}),
                400,
            )

        if not data.get("test_type"):
            return (
                jsonify({"success": False, "error": "test_type is required"}),
                400,
            )

        test_type = data.get("test_type")
        if test_type not in ["unit", "integration", "e2e", "custom"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid test_type. Must be: unit, integration, e2e, or custom",
                    }
                ),
                400,
            )

        path_mode = data.get("path_mode", "repo_relative")
        if path_mode not in ["centralized", "repo_relative"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid path_mode. Must be: centralized or repo_relative",
                    }
                ),
                400,
            )

        max_order = db(
            db.iceflows_stage_tests.stage_id == stage.id
        ).select(db.iceflows_stage_tests.execution_order.max()).first()
        next_order = (
            (max_order[db.iceflows_stage_tests.execution_order.max()] or 0) + 1
        )

        test_id = str(uuid.uuid4())

        db.iceflows_stage_tests.insert(
            test_id=test_id,
            stage_id=stage.id,
            name=data["name"],
            test_type=test_type,
            path_mode=path_mode,
            centralized_path=data.get("centralized_path", ""),
            repo_relative_path=data.get("repo_relative_path", ""),
            command=data.get("command", ""),
            timeout_seconds=data.get("timeout_seconds", 600),
            is_blocking=data.get("is_blocking", True),
            is_required=data.get("is_required", True),
            execution_order=data.get("execution_order", next_order),
            env_vars=data.get("env_vars", {}),
        )
        db.commit()

        test = db(db.iceflows_stage_tests.test_id == test_id).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "test": serialize_test(test),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error adding test to stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/tests/<test_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_test(stage_id: str, test_id: str):
    """Get test details.

    Args:
        stage_id: Stage identifier
        test_id: Test identifier

    Returns:
        JSON with test details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        test = db(
            (db.iceflows_stage_tests.test_id == test_id)
            & (db.iceflows_stage_tests.stage_id == stage.id)
        ).select().first()

        if not test:
            return (
                jsonify({"success": False, "error": "Test not found"}),
                404,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "test": serialize_test(test),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error getting test {test_id} for stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/tests/<test_id>", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_test(stage_id: str, test_id: str):
    """Update a test configuration.

    Args:
        stage_id: Stage identifier
        test_id: Test identifier

    Returns:
        JSON with updated test
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        test = db(
            (db.iceflows_stage_tests.test_id == test_id)
            & (db.iceflows_stage_tests.stage_id == stage.id)
        ).select().first()

        if not test:
            return (
                jsonify({"success": False, "error": "Test not found"}),
                404,
            )

        update_data = {}

        if "name" in data:
            update_data["name"] = data["name"]
        if "test_type" in data:
            if data["test_type"] not in ["unit", "integration", "e2e", "custom"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Invalid test_type",
                        }
                    ),
                    400,
                )
            update_data["test_type"] = data["test_type"]
        if "path_mode" in data:
            if data["path_mode"] not in ["centralized", "repo_relative"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Invalid path_mode",
                        }
                    ),
                    400,
                )
            update_data["path_mode"] = data["path_mode"]
        if "centralized_path" in data:
            update_data["centralized_path"] = data["centralized_path"]
        if "repo_relative_path" in data:
            update_data["repo_relative_path"] = data["repo_relative_path"]
        if "command" in data:
            update_data["command"] = data["command"]
        if "timeout_seconds" in data:
            update_data["timeout_seconds"] = data["timeout_seconds"]
        if "is_blocking" in data:
            update_data["is_blocking"] = data["is_blocking"]
        if "is_required" in data:
            update_data["is_required"] = data["is_required"]
        if "execution_order" in data:
            update_data["execution_order"] = data["execution_order"]
        if "env_vars" in data:
            update_data["env_vars"] = data["env_vars"]

        db(db.iceflows_stage_tests.id == test.id).update(**update_data)
        db.commit()

        updated_test = db(
            (db.iceflows_stage_tests.test_id == test_id)
            & (db.iceflows_stage_tests.stage_id == stage.id)
        ).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "test": serialize_test(updated_test),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error updating test {test_id} for stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/tests/<test_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:write")
def delete_test(stage_id: str, test_id: str):
    """Delete a test from a stage.

    Args:
        stage_id: Stage identifier
        test_id: Test identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        test = db(
            (db.iceflows_stage_tests.test_id == test_id)
            & (db.iceflows_stage_tests.stage_id == stage.id)
        ).select().first()

        if not test:
            return (
                jsonify({"success": False, "error": "Test not found"}),
                404,
            )

        db(db.iceflows_stage_tests.id == test.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Test deleted successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error deleting test {test_id} from stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Calls Endpoints
# ============================================================================


@iceflows_stages_bp.route("/<stage_id>/calls", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_calls(stage_id: str):
    """List all calls for a stage.

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with calls array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        calls = db(db.iceflows_stage_calls.stage_id == stage.id).select(
            orderby=db.iceflows_stage_calls.execution_order
        )

        result = []
        for call in calls:
            target_name = None

            if call.call_type == "icestreams":
                playbook = db(
                    db.playbooks.id == int(call.target_id)
                    if call.target_id and call.target_id.isdigit()
                    else False
                ).select().first()
                if playbook:
                    target_name = playbook.name
            elif call.call_type == "iceruns":
                function = db(
                    db.iceruns.id == int(call.target_id)
                    if call.target_id and call.target_id.isdigit()
                    else False
                ).select().first()
                if function:
                    target_name = function.name

            result.append(serialize_call(call, target_name))

        return (
            jsonify(
                {
                    "success": True,
                    "calls": result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing calls for stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/calls", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def add_call(stage_id: str):
    """Add a call to a stage.

    Request body:
        - name (required): Call name
        - call_type (required): icestreams or iceruns
        - target_id (required): Target playbook or function ID
        - trigger_on (optional): pre_merge, post_merge, on_approval, on_promotion
        - input_template (optional): Input template JSON
        - timeout_seconds (optional): Timeout in seconds (default: 300)
        - is_blocking (optional): Block pipeline on failure (default: true)
        - retry_count (optional): Number of retries (default: 0)
        - execution_order (optional): Execution order (auto-assigned if not provided)

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with created call
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        if not data.get("name"):
            return (
                jsonify({"success": False, "error": "name is required"}),
                400,
            )

        if not data.get("call_type"):
            return (
                jsonify({"success": False, "error": "call_type is required"}),
                400,
            )

        if not data.get("target_id"):
            return (
                jsonify({"success": False, "error": "target_id is required"}),
                400,
            )

        call_type = data.get("call_type")
        if call_type not in ["icestreams", "iceruns"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid call_type. Must be: icestreams or iceruns",
                    }
                ),
                400,
            )

        target_id = str(data.get("target_id"))

        if call_type == "icestreams":
            target = db(db.playbooks.id == int(target_id) if target_id.isdigit() else False).select().first()
            if not target:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Playbook not found",
                        }
                    ),
                    400,
                )

        elif call_type == "iceruns":
            target = db(db.iceruns.id == int(target_id) if target_id.isdigit() else False).select().first()
            if not target:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Function not found",
                        }
                    ),
                    400,
                )

        trigger_on = data.get("trigger_on", "on_promotion")
        if trigger_on not in ["pre_merge", "post_merge", "on_approval", "on_promotion"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Invalid trigger_on. Must be: pre_merge, post_merge, on_approval, or on_promotion",
                    }
                ),
                400,
            )

        max_order = db(
            db.iceflows_stage_calls.stage_id == stage.id
        ).select(db.iceflows_stage_calls.execution_order.max()).first()
        next_order = (
            (max_order[db.iceflows_stage_calls.execution_order.max()] or 0) + 1
        )

        call_id = str(uuid.uuid4())

        db.iceflows_stage_calls.insert(
            call_id=call_id,
            stage_id=stage.id,
            name=data["name"],
            call_type=call_type,
            target_id=target_id,
            trigger_on=trigger_on,
            input_template=data.get("input_template", {}),
            timeout_seconds=data.get("timeout_seconds", 300),
            is_blocking=data.get("is_blocking", True),
            retry_count=data.get("retry_count", 0),
            execution_order=data.get("execution_order", next_order),
        )
        db.commit()

        call = db(db.iceflows_stage_calls.call_id == call_id).select().first()

        target_name = None
        if call_type == "icestreams":
            playbook = db(db.playbooks.id == int(target_id) if target_id.isdigit() else False).select().first()
            if playbook:
                target_name = playbook.name
        elif call_type == "iceruns":
            function = db(db.iceruns.id == int(target_id) if target_id.isdigit() else False).select().first()
            if function:
                target_name = function.name

        return (
            jsonify(
                {
                    "success": True,
                    "call": serialize_call(call, target_name),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error adding call to stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/calls/<call_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_call(stage_id: str, call_id: str):
    """Get call details.

    Args:
        stage_id: Stage identifier
        call_id: Call identifier

    Returns:
        JSON with call details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        call = db(
            (db.iceflows_stage_calls.call_id == call_id)
            & (db.iceflows_stage_calls.stage_id == stage.id)
        ).select().first()

        if not call:
            return (
                jsonify({"success": False, "error": "Call not found"}),
                404,
            )

        target_name = None
        if call.call_type == "icestreams":
            playbook = db(db.playbooks.id == int(call.target_id) if call.target_id and call.target_id.isdigit() else False).select().first()
            if playbook:
                target_name = playbook.name
        elif call.call_type == "iceruns":
            function = db(db.iceruns.id == int(call.target_id) if call.target_id and call.target_id.isdigit() else False).select().first()
            if function:
                target_name = function.name

        return (
            jsonify(
                {
                    "success": True,
                    "call": serialize_call(call, target_name),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error getting call {call_id} for stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/calls/<call_id>", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_call(stage_id: str, call_id: str):
    """Update a call configuration.

    Args:
        stage_id: Stage identifier
        call_id: Call identifier

    Returns:
        JSON with updated call
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        call = db(
            (db.iceflows_stage_calls.call_id == call_id)
            & (db.iceflows_stage_calls.stage_id == stage.id)
        ).select().first()

        if not call:
            return (
                jsonify({"success": False, "error": "Call not found"}),
                404,
            )

        update_data = {}

        if "name" in data:
            update_data["name"] = data["name"]
        if "call_type" in data:
            if data["call_type"] not in ["icestreams", "iceruns"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Invalid call_type",
                        }
                    ),
                    400,
                )
            update_data["call_type"] = data["call_type"]
        if "target_id" in data:
            update_data["target_id"] = str(data["target_id"])
        if "trigger_on" in data:
            if data["trigger_on"] not in [
                "pre_merge",
                "post_merge",
                "on_approval",
                "on_promotion",
            ]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Invalid trigger_on",
                        }
                    ),
                    400,
                )
            update_data["trigger_on"] = data["trigger_on"]
        if "input_template" in data:
            update_data["input_template"] = data["input_template"]
        if "timeout_seconds" in data:
            update_data["timeout_seconds"] = data["timeout_seconds"]
        if "is_blocking" in data:
            update_data["is_blocking"] = data["is_blocking"]
        if "retry_count" in data:
            update_data["retry_count"] = data["retry_count"]
        if "execution_order" in data:
            update_data["execution_order"] = data["execution_order"]

        db(db.iceflows_stage_calls.id == call.id).update(**update_data)
        db.commit()

        updated_call = db(
            (db.iceflows_stage_calls.call_id == call_id)
            & (db.iceflows_stage_calls.stage_id == stage.id)
        ).select().first()

        target_name = None
        if updated_call.call_type == "icestreams":
            playbook = db(db.playbooks.id == int(updated_call.target_id) if updated_call.target_id and updated_call.target_id.isdigit() else False).select().first()
            if playbook:
                target_name = playbook.name
        elif updated_call.call_type == "iceruns":
            function = db(db.iceruns.id == int(updated_call.target_id) if updated_call.target_id and updated_call.target_id.isdigit() else False).select().first()
            if function:
                target_name = function.name

        return (
            jsonify(
                {
                    "success": True,
                    "call": serialize_call(updated_call, target_name),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error updating call {call_id} for stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/calls/<call_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:write")
def delete_call(stage_id: str, call_id: str):
    """Delete a call from a stage.

    Args:
        stage_id: Stage identifier
        call_id: Call identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        call = db(
            (db.iceflows_stage_calls.call_id == call_id)
            & (db.iceflows_stage_calls.stage_id == stage.id)
        ).select().first()

        if not call:
            return (
                jsonify({"success": False, "error": "Call not found"}),
                404,
            )

        db(db.iceflows_stage_calls.id == call.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Call deleted successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error deleting call {call_id} from stage {stage_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Darwin Reviews Endpoints
# ============================================================================


@iceflows_stages_bp.route("/<stage_id>/reviews", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_review(stage_id: str):
    """Get Darwin review configuration for a stage.

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with review configuration
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        review = db(
            db.iceflows_stage_reviews.stage_id == stage.id
        ).select().first()

        if not review:
            review_id = str(uuid.uuid4())
            db.iceflows_stage_reviews.insert(
                review_id=review_id,
                stage_id=stage.id,
                is_required=True,
                review_type="inherit",
                min_score=70,
                block_on_critical=True,
                allowed_issue_types=[],
                reviewers_notified=True,
            )
            db.commit()
            review = db(
                db.iceflows_stage_reviews.review_id == review_id
            ).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "review": serialize_review(review),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting review for stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_stages_bp.route("/<stage_id>/reviews", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_review(stage_id: str):
    """Update Darwin review configuration for a stage.

    Request body:
        - is_required (optional): Review is required (default: true)
        - review_type (optional): inherit, standard, security, performance, full
        - min_score (optional): Minimum review score (default: 70)
        - block_on_critical (optional): Block on critical issues (default: true)
        - allowed_issue_types (optional): Allowed issue types array
        - reviewers_notified (optional): Notify reviewers (default: true)

    Args:
        stage_id: Stage identifier

    Returns:
        JSON with updated review configuration
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        stage = get_stage_or_404(stage_id)
        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        if not verify_stage_access(stage, user_id):
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        review = db(
            db.iceflows_stage_reviews.stage_id == stage.id
        ).select().first()

        if not review:
            review_id = str(uuid.uuid4())
            db.iceflows_stage_reviews.insert(
                review_id=review_id,
                stage_id=stage.id,
                is_required=data.get("is_required", True),
                review_type=data.get("review_type", "inherit"),
                min_score=data.get("min_score", 70),
                block_on_critical=data.get("block_on_critical", True),
                allowed_issue_types=data.get("allowed_issue_types", []),
                reviewers_notified=data.get("reviewers_notified", True),
            )
            db.commit()
            review = db(
                db.iceflows_stage_reviews.review_id == review_id
            ).select().first()
        else:
            update_data = {}

            if "is_required" in data:
                update_data["is_required"] = data["is_required"]
            if "review_type" in data:
                review_type = data["review_type"]
                if review_type not in [
                    "inherit",
                    "standard",
                    "security",
                    "performance",
                    "full",
                ]:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Invalid review_type",
                            }
                        ),
                        400,
                    )
                update_data["review_type"] = review_type
            if "min_score" in data:
                update_data["min_score"] = data["min_score"]
            if "block_on_critical" in data:
                update_data["block_on_critical"] = data["block_on_critical"]
            if "allowed_issue_types" in data:
                update_data["allowed_issue_types"] = data["allowed_issue_types"]
            if "reviewers_notified" in data:
                update_data["reviewers_notified"] = data["reviewers_notified"]

            db(db.iceflows_stage_reviews.id == review.id).update(**update_data)
            db.commit()
            review = db(
                db.iceflows_stage_reviews.stage_id == stage.id
            ).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "review": serialize_review(review),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating review for stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
