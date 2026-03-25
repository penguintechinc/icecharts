"""IceFlows API Endpoints for API v1 - CI/CD Pipeline Orchestration.

Provides CRUD operations for flows and stages, including:
- Flow management (create, read, update, delete, enable/disable, duplicate)
- Stage management (create, read, update, delete, reorder)
- Full cascade deletion handling
"""

import datetime
import secrets
import uuid

import yaml
from flask import Blueprint, current_app, jsonify, request, Response

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db

iceflows_v1_bp = Blueprint("iceflows_v1", __name__, url_prefix="/iceflows")


def serialize_flow(flow, include_stages=False):
    """Serialize flow database row to JSON-safe dict.

    Args:
        flow: Database flow record
        include_stages: Whether to include nested stages

    Returns:
        Dictionary representation of flow
    """
    db = get_db()

    # Get credential info if exists
    credential_info = None
    if flow.credential_id:
        cred = db.iceflows_credentials[flow.credential_id]
        if cred:
            credential_info = {
                "credential_id": cred.credential_id,
                "name": cred.name,
                "provider": cred.provider,
            }

    result = {
        "flow_id": flow.flow_id,
        "name": flow.name,
        "description": flow.description or "",
        "repository_url": flow.repository_url,
        "repository_provider": flow.repository_provider,
        "repository_name": flow.repository_name or "",
        "default_branch": flow.default_branch or "main",
        "credential": credential_info,
        "gitops_enabled": flow.gitops_enabled or False,
        "gitops_repo_url": flow.gitops_repo_url or "",
        "gitops_branch": flow.gitops_branch or "main",
        "gitops_path": flow.gitops_path or "",
        "webhook_secret": flow.webhook_secret or "",
        "status": flow.status or "draft",
        "is_enabled": flow.is_enabled or True,
        "created_by_id": str(flow.created_by_id) if flow.created_by_id else None,
        "tags": flow.tags or [],
        "created_at": flow.created_at.isoformat() if flow.created_at else None,
        "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
    }

    if include_stages:
        db = get_db()
        stages = db(db.iceflows_stages.flow_id == flow.id).select(
            orderby=db.iceflows_stages.stage_order
        )
        result["stages"] = [serialize_stage(stage, include_details=True) for stage in stages]
        result["stage_count"] = len(stages)

    return result


def serialize_stage(stage, include_details=False):
    """Serialize stage database row to JSON-safe dict.

    Args:
        stage: Database stage record
        include_details: Whether to include approvers, tests, calls

    Returns:
        Dictionary representation of stage
    """
    result = {
        "stage_id": stage.stage_id,
        "flow_id": stage.flow_id,
        "stage_order": stage.stage_order,
        "branch_name": stage.branch_name,
        "display_name": stage.display_name or stage.branch_name,
        "description": stage.description or "",
        "is_production": stage.is_production or False,
        "auto_promote": stage.auto_promote or False,
        "require_approval": stage.require_approval or True,
        "min_approvers": stage.min_approvers or 1,
        "override_min_approvers": stage.override_min_approvers or 2,
        "day_restrictions": stage.day_restrictions or {},
        "time_restrictions": stage.time_restrictions or {},
        "notification_config": stage.notification_config or {},
        "is_enabled": stage.is_enabled or True,
        "created_at": stage.created_at.isoformat() if stage.created_at else None,
        "updated_at": stage.updated_at.isoformat() if stage.updated_at else None,
    }

    if include_details:
        db = get_db()
        approvers = db(db.iceflows_stage_approvers.stage_id == stage.id).count()
        tests = db(db.iceflows_stage_tests.stage_id == stage.id).count()
        calls = db(db.iceflows_stage_calls.stage_id == stage.id).count()
        result["approver_count"] = approvers
        result["test_count"] = tests
        result["call_count"] = calls

    return result


# ============================================================================
# Flow CRUD
# ============================================================================


@iceflows_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_flows():
    """List all flows for current user with pagination and filtering.

    Query parameters:
        - page: Page number (default 1)
        - per_page: Items per page (default 20, max 100)
        - status: Filter by status (draft, active, paused, archived)
        - repository_provider: Filter by provider (github, gitlab)
        - is_enabled: Filter by enabled status (true, false)
        - tags: Filter by tags (comma-separated)
        - search: Search by name (partial match)
        - sort_by: Sort field (created_at, updated_at, name)

    Returns:
        JSON with flows array, pagination info
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Pagination
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, int(request.args.get("per_page", 20)))
        offset = (page - 1) * per_page

        # Filters
        status = request.args.get("status")
        provider = request.args.get("repository_provider")
        is_enabled = request.args.get("is_enabled")
        tags = request.args.getlist("tags")
        search = request.args.get("search")
        sort_by = request.args.get("sort_by", "updated_at")

        # Build query
        query = db.iceflows.created_by_id == user_id

        if status:
            query &= db.iceflows.status == status
        if provider:
            query &= db.iceflows.repository_provider == provider
        if is_enabled is not None:
            query &= db.iceflows.is_enabled == (is_enabled.lower() == "true")
        if tags:
            for tag in tags:
                query &= db.iceflows.tags.contains(tag)
        if search:
            query &= db.iceflows.name.contains(search)

        # Determine sort order
        if sort_by == "name":
            orderby = db.iceflows.name
        elif sort_by == "created_at":
            orderby = ~db.iceflows.created_at
        else:  # updated_at (default)
            orderby = ~db.iceflows.updated_at

        # Count total
        total = db(query).count()

        # Execute query with pagination
        flows = db(query).select(orderby=orderby, limitby=(offset, offset + per_page))

        result = [serialize_flow(flow) for flow in flows]

        return (
            jsonify(
                {
                    "success": True,
                    "flows": result,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing flows: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def create_flow():
    """Create a new flow.

    Request body:
        - name (required): Flow name
        - repository_url (required): Git repository URL
        - credential_id (optional): Credential ID for Git provider access
        - description (optional): Flow description
        - repository_provider (optional): github or gitlab (auto-detected if not provided)
        - default_branch (optional): Default branch (default: main)
        - gitops_enabled (optional): Enable GitOps (default: false)
        - gitops_repo_url (optional): GitOps repository URL
        - gitops_branch (optional): GitOps branch (default: main)
        - gitops_path (optional): GitOps path (default: empty)
        - tags (optional): Array of tags

    Returns:
        JSON with created flow
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        # Validation
        if not data.get("name"):
            return jsonify({"success": False, "error": "name is required"}), 400
        if not data.get("repository_url"):
            return jsonify(
                {"success": False, "error": "repository_url is required"}
            ), 400

        # Auto-detect repository provider from URL
        repo_url = data["repository_url"].lower()
        provider = data.get("repository_provider")
        if not provider:
            if "github.com" in repo_url:
                provider = "github"
            elif "gitlab.com" in repo_url or "gitlab" in repo_url:
                provider = "gitlab"
            else:
                provider = "github"  # Default to github

        # Validate credential_id if provided
        credential_db_id = None
        if data.get("credential_id"):
            credential = db(
                (db.iceflows_credentials.credential_id == data["credential_id"])
                & (db.iceflows_credentials.created_by_id == user_id)
            ).select().first()
            if not credential:
                return jsonify({"success": False, "error": "Invalid credential_id"}), 400
            credential_db_id = credential.id

        # Generate flow_id and webhook_secret
        flow_id = str(uuid.uuid4())
        webhook_secret = secrets.token_hex(32)

        # Create flow record
        db_id = db.iceflows.insert(
            flow_id=flow_id,
            name=data["name"],
            description=data.get("description", ""),
            repository_url=data["repository_url"],
            repository_provider=provider,
            repository_name=data.get("repository_url").split("/")[-1].replace(".git", ""),
            default_branch=data.get("default_branch", "main"),
            credential_id=credential_db_id,
            gitops_enabled=data.get("gitops_enabled", False),
            gitops_repo_url=data.get("gitops_repo_url", ""),
            gitops_branch=data.get("gitops_branch", "main"),
            gitops_path=data.get("gitops_path", ""),
            webhook_secret=webhook_secret,
            status="draft",
            is_enabled=True,
            created_by_id=user_id,
            tags=data.get("tags", []),
        )
        db.commit()

        # Fetch and return created flow
        flow = db.iceflows[db_id]

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(flow),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating flow: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_flow(flow_id: str):
    """Get flow details with stages and metadata.

    Args:
        flow_id: Flow identifier

    Returns:
        JSON with flow and stages
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check access
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(flow, include_stages=True),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_flow(flow_id: str):
    """Update flow configuration.

    Args:
        flow_id: Flow identifier

    Returns:
        JSON with updated flow
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Build update dict
        update_data = {"updated_at": datetime.datetime.now(datetime.timezone.utc)}

        if "name" in data:
            update_data["name"] = data["name"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "repository_url" in data:
            update_data["repository_url"] = data["repository_url"]
        if "repository_provider" in data:
            update_data["repository_provider"] = data["repository_provider"]
        if "default_branch" in data:
            update_data["default_branch"] = data["default_branch"]
        if "credential_id" in data:
            # Validate credential if provided
            if data["credential_id"]:
                credential = db(
                    (db.iceflows_credentials.credential_id == data["credential_id"])
                    & (db.iceflows_credentials.created_by_id == user_id)
                ).select().first()
                if not credential:
                    return jsonify({"success": False, "error": "Invalid credential_id"}), 400
                update_data["credential_id"] = credential.id
            else:
                update_data["credential_id"] = None
        if "gitops_enabled" in data:
            update_data["gitops_enabled"] = data["gitops_enabled"]
        if "gitops_repo_url" in data:
            update_data["gitops_repo_url"] = data["gitops_repo_url"]
        if "gitops_branch" in data:
            update_data["gitops_branch"] = data["gitops_branch"]
        if "gitops_path" in data:
            update_data["gitops_path"] = data["gitops_path"]
        if "status" in data:
            update_data["status"] = data["status"]
        if "tags" in data:
            update_data["tags"] = data["tags"]

        flow.update_record(**update_data)
        db.commit()

        # Fetch updated flow
        updated_flow = db((db.iceflows.flow_id == flow_id)).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(updated_flow),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:delete")
def delete_flow(flow_id: str):
    """Delete flow and all related resources (cascade).

    Args:
        flow_id: Flow identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Delete flow (cascade handles stages and their children)
        db(db.iceflows.id == flow.id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Flow deleted successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/enable", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def enable_flow(flow_id: str):
    """Enable a flow.

    Args:
        flow_id: Flow identifier

    Returns:
        JSON with updated flow
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        flow.update_record(
            is_enabled=True, updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.commit()

        updated_flow = db((db.iceflows.flow_id == flow_id)).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(updated_flow),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error enabling flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/disable", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def disable_flow(flow_id: str):
    """Disable a flow.

    Args:
        flow_id: Flow identifier

    Returns:
        JSON with updated flow
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        flow.update_record(
            is_enabled=False, updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.commit()

        updated_flow = db((db.iceflows.flow_id == flow_id)).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(updated_flow),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error disabling flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/duplicate", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def duplicate_flow(flow_id: str):
    """Duplicate a flow including all stages.

    Args:
        flow_id: Flow identifier to duplicate

    Returns:
        JSON with new flow
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        original = db((db.iceflows.flow_id == flow_id)).select().first()
        if not original:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if original.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Create new flow
        new_flow_id = str(uuid.uuid4())
        webhook_secret = secrets.token_hex(32)

        db_id = db.iceflows.insert(
            flow_id=new_flow_id,
            name=f"{original.name} (Copy)",
            description=original.description,
            repository_url=original.repository_url,
            repository_provider=original.repository_provider,
            repository_name=original.repository_name,
            default_branch=original.default_branch,
            gitops_enabled=original.gitops_enabled,
            gitops_repo_url=original.gitops_repo_url,
            gitops_branch=original.gitops_branch,
            gitops_path=original.gitops_path,
            webhook_secret=webhook_secret,
            status="draft",
            is_enabled=False,
            created_by_id=user_id,
            tags=original.tags or [],
        )
        db.commit()

        # Copy all stages
        original_stages = db(
            db.iceflows_stages.flow_id == original.id
        ).select(orderby=db.iceflows_stages.stage_order)

        stage_mapping = {}  # Map old stage IDs to new stage IDs

        for stage in original_stages:
            new_stage_id = str(uuid.uuid4())
            stage_db_id = db.iceflows_stages.insert(
                stage_id=new_stage_id,
                flow_id=db_id,
                stage_order=stage.stage_order,
                branch_name=stage.branch_name,
                display_name=stage.display_name,
                description=stage.description,
                is_production=stage.is_production,
                auto_promote=stage.auto_promote,
                require_approval=stage.require_approval,
                min_approvers=stage.min_approvers,
                override_min_approvers=stage.override_min_approvers,
                day_restrictions=stage.day_restrictions,
                time_restrictions=stage.time_restrictions,
                notification_config=stage.notification_config,
                is_enabled=stage.is_enabled,
            )
            db.commit()
            stage_mapping[stage.id] = stage_db_id

            # Copy approvers
            approvers = db(
                db.iceflows_stage_approvers.stage_id == stage.id
            ).select()
            for approver in approvers:
                db.iceflows_stage_approvers.insert(
                    approver_id=str(uuid.uuid4()),
                    stage_id=stage_db_id,
                    identity_id=approver.identity_id,
                    group_id=approver.group_id,
                    role=approver.role,
                    can_override=approver.can_override,
                )
            db.commit()

            # Copy tests
            tests = db(
                db.iceflows_stage_tests.stage_id == stage.id
            ).select()
            for test in tests:
                db.iceflows_stage_tests.insert(
                    test_id=str(uuid.uuid4()),
                    stage_id=stage_db_id,
                    name=test.name,
                    test_type=test.test_type,
                    path_mode=test.path_mode,
                    centralized_path=test.centralized_path,
                    repo_relative_path=test.repo_relative_path,
                    command=test.command,
                    timeout_seconds=test.timeout_seconds,
                    is_blocking=test.is_blocking,
                    is_required=test.is_required,
                    execution_order=test.execution_order,
                    env_vars=test.env_vars,
                )
            db.commit()

            # Copy calls
            calls = db(
                db.iceflows_stage_calls.stage_id == stage.id
            ).select()
            for call in calls:
                db.iceflows_stage_calls.insert(
                    call_id=str(uuid.uuid4()),
                    stage_id=stage_db_id,
                    name=call.name,
                    call_type=call.call_type,
                    target_id=call.target_id,
                    trigger_on=call.trigger_on,
                    input_template=call.input_template,
                    timeout_seconds=call.timeout_seconds,
                    is_blocking=call.is_blocking,
                    retry_count=call.retry_count,
                    execution_order=call.execution_order,
                )
            db.commit()

        new_flow = db.iceflows[db_id]

        return (
            jsonify(
                {
                    "success": True,
                    "flow": serialize_flow(new_flow, include_stages=True),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error duplicating flow {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Stage CRUD
# ============================================================================


@iceflows_v1_bp.route("/<flow_id>/stages", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_stages(flow_id: str):
    """List all stages for a flow ordered by stage_order.

    Args:
        flow_id: Flow identifier

    Returns:
        JSON with stages array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check access
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        stages = db(db.iceflows_stages.flow_id == flow.id).select(
            orderby=db.iceflows_stages.stage_order
        )

        return (
            jsonify(
                {
                    "success": True,
                    "stages": [serialize_stage(stage, include_details=True) for stage in stages],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing stages for {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/stages", methods=["POST"])
@auth_required
@scopes_required("iceflows:write")
def create_stage(flow_id: str):
    """Create a new stage for a flow.

    Request body:
        - branch_name (required): Git branch name
        - display_name (optional): Display name
        - description (optional): Stage description
        - is_production (optional): Production stage flag
        - auto_promote (optional): Auto-promote flag
        - require_approval (optional): Require approval flag
        - min_approvers (optional): Minimum approvers
        - override_min_approvers (optional): Override minimum
        - day_restrictions (optional): Day restrictions JSON
        - time_restrictions (optional): Time restrictions JSON
        - notification_config (optional): Notification config JSON

    Returns:
        JSON with created stage
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Validation
        if not data.get("branch_name"):
            return (
                jsonify({"success": False, "error": "branch_name is required"}),
                400,
            )

        # Get max stage_order
        max_order = db(
            db.iceflows_stages.flow_id == flow.id
        ).select(db.iceflows_stages.stage_order.max()).first()
        next_order = (max_order[db.iceflows_stages.stage_order.max()] or 0) + 1

        # Create stage
        stage_id = str(uuid.uuid4())

        db_id = db.iceflows_stages.insert(
            stage_id=stage_id,
            flow_id=flow.id,
            stage_order=next_order,
            branch_name=data["branch_name"],
            display_name=data.get("display_name") or data["branch_name"],
            description=data.get("description", ""),
            is_production=data.get("is_production", False),
            auto_promote=data.get("auto_promote", False),
            require_approval=data.get("require_approval", True),
            min_approvers=data.get("min_approvers", 1),
            override_min_approvers=data.get("override_min_approvers", 2),
            day_restrictions=data.get("day_restrictions", {}),
            time_restrictions=data.get("time_restrictions", {}),
            notification_config=data.get("notification_config", {}),
            is_enabled=True,
        )
        db.commit()

        stage = db.iceflows_stages[db_id]

        return (
            jsonify(
                {
                    "success": True,
                    "stage": serialize_stage(stage, include_details=True),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating stage for {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/stages/<stage_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_stage(flow_id: str, stage_id: str):
    """Get stage details including approvers, tests, and calls.

    Args:
        flow_id: Flow identifier
        stage_id: Stage identifier

    Returns:
        JSON with stage details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check access
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        stage = db(
            (db.iceflows_stages.stage_id == stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        # Get related records
        approvers = db(db.iceflows_stage_approvers.stage_id == stage.id).select()
        tests = db(db.iceflows_stage_tests.stage_id == stage.id).select(
            orderby=db.iceflows_stage_tests.execution_order
        )
        calls = db(db.iceflows_stage_calls.stage_id == stage.id).select(
            orderby=db.iceflows_stage_calls.execution_order
        )

        result = serialize_stage(stage, include_details=True)
        result["approvers"] = [
            {
                "approver_id": a.approver_id,
                "identity_id": a.identity_id,
                "group_id": a.group_id,
                "role": a.role,
                "can_override": a.can_override,
            }
            for a in approvers
        ]
        result["tests"] = [
            {
                "test_id": t.test_id,
                "name": t.name,
                "test_type": t.test_type,
                "path_mode": t.path_mode,
                "centralized_path": t.centralized_path,
                "repo_relative_path": t.repo_relative_path,
                "command": t.command,
                "timeout_seconds": t.timeout_seconds,
                "is_blocking": t.is_blocking,
                "is_required": t.is_required,
                "execution_order": t.execution_order,
            }
            for t in tests
        ]
        result["calls"] = [
            {
                "call_id": c.call_id,
                "name": c.name,
                "call_type": c.call_type,
                "target_id": c.target_id,
                "trigger_on": c.trigger_on,
                "timeout_seconds": c.timeout_seconds,
                "is_blocking": c.is_blocking,
                "retry_count": c.retry_count,
                "execution_order": c.execution_order,
            }
            for c in calls
        ]

        return (
            jsonify(
                {
                    "success": True,
                    "stage": result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/stages/<stage_id>", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def update_stage(flow_id: str, stage_id: str):
    """Update stage configuration.

    Args:
        flow_id: Flow identifier
        stage_id: Stage identifier

    Returns:
        JSON with updated stage
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        stage = db(
            (db.iceflows_stages.stage_id == stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        # Build update dict
        update_data = {"updated_at": datetime.datetime.now(datetime.timezone.utc)}

        if "branch_name" in data:
            update_data["branch_name"] = data["branch_name"]
        if "display_name" in data:
            update_data["display_name"] = data["display_name"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "is_production" in data:
            update_data["is_production"] = data["is_production"]
        if "auto_promote" in data:
            update_data["auto_promote"] = data["auto_promote"]
        if "require_approval" in data:
            update_data["require_approval"] = data["require_approval"]
        if "min_approvers" in data:
            update_data["min_approvers"] = data["min_approvers"]
        if "override_min_approvers" in data:
            update_data["override_min_approvers"] = data["override_min_approvers"]
        if "day_restrictions" in data:
            update_data["day_restrictions"] = data["day_restrictions"]
        if "time_restrictions" in data:
            update_data["time_restrictions"] = data["time_restrictions"]
        if "notification_config" in data:
            update_data["notification_config"] = data["notification_config"]
        if "is_enabled" in data:
            update_data["is_enabled"] = data["is_enabled"]

        stage.update_record(**update_data)
        db.commit()

        updated_stage = db(
            (db.iceflows_stages.stage_id == stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "stage": serialize_stage(updated_stage, include_details=True),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/stages/<stage_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:delete")
def delete_stage(flow_id: str, stage_id: str):
    """Delete stage and reorder remaining stages.

    Args:
        flow_id: Flow identifier
        stage_id: Stage identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        stage = db(
            (db.iceflows_stages.stage_id == stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        if not stage:
            return (
                jsonify({"success": False, "error": "Stage not found"}),
                404,
            )

        deleted_order = stage.stage_order

        # Delete stage (cascade handles approvers, tests, calls)
        db(db.iceflows_stages.id == stage.id).delete()
        db.commit()

        # Reorder remaining stages
        remaining_stages = db(db.iceflows_stages.flow_id == flow.id).select(
            orderby=db.iceflows_stages.stage_order
        )

        for idx, s in enumerate(remaining_stages, start=1):
            if s.stage_order != idx:
                db(db.iceflows_stages.id == s.id).update(stage_order=idx)
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Stage deleted successfully",
                }
            ),
            204,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting stage {stage_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_v1_bp.route("/<flow_id>/stages/reorder", methods=["PUT"])
@auth_required
@scopes_required("iceflows:write")
def reorder_stages(flow_id: str):
    """Reorder stages within a flow.

    Request body:
        - stage_order: Array of stage_ids in desired order

    Returns:
        JSON with reordered stages
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check ownership
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        stage_ids = data.get("stage_order", [])
        if not stage_ids:
            return (
                jsonify({"success": False, "error": "stage_order is required"}),
                400,
            )

        # Update order for each stage
        for order, stage_id in enumerate(stage_ids, start=1):
            stage = db(
                (db.iceflows_stages.stage_id == stage_id)
                & (db.iceflows_stages.flow_id == flow.id)
            ).select().first()

            if not stage:
                return (
                    jsonify(
                        {"success": False, "error": f"Stage {stage_id} not found"}
                    ),
                    404,
                )

            db(db.iceflows_stages.id == stage.id).update(stage_order=order)

        db.commit()

        # Fetch and return reordered stages
        stages = db(db.iceflows_stages.flow_id == flow.id).select(
            orderby=db.iceflows_stages.stage_order
        )

        return (
            jsonify(
                {
                    "success": True,
                    "stages": [serialize_stage(stage) for stage in stages],
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error reordering stages for {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Export Endpoints
# ============================================================================


@iceflows_v1_bp.route("/<flow_id>/export/yaml", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def export_flow_yaml(flow_id: str):
    """Export flow configuration as YAML following GitOps schema.

    Args:
        flow_id: Flow identifier

    Returns:
        YAML response with Content-Type: application/x-yaml
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Fetch flow
        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return (
                jsonify({"success": False, "error": "Flow not found"}),
                404,
            )

        # Check access
        if flow.created_by_id != user_id:
            return (
                jsonify({"success": False, "error": "Access denied"}),
                403,
            )

        # Fetch all stages ordered by stage_order
        stages = db(db.iceflows_stages.flow_id == flow.id).select(
            orderby=db.iceflows_stages.stage_order
        )

        # Build stages list for YAML
        stages_list = []
        for stage in stages:
            # Fetch approvers for this stage
            approvers = db(db.iceflows_stage_approvers.stage_id == stage.id).select()
            approver_emails = []
            for approver in approvers:
                if approver.identity_id:
                    identity = db.identities[approver.identity_id]
                    if identity:
                        approver_emails.append(
                            identity.email or identity.username
                        )
                elif approver.group_id:
                    group = db.groups[approver.group_id]
                    if group:
                        approver_emails.append(group.name)

            # Fetch tests for this stage
            tests = db(db.iceflows_stage_tests.stage_id == stage.id).select(
                orderby=db.iceflows_stage_tests.execution_order
            )
            tests_list = []
            for test in tests:
                test_obj = {
                    "name": test.name,
                    "command": test.command,
                }
                if test.repo_relative_path:
                    test_obj["path"] = test.repo_relative_path
                if test.timeout_seconds:
                    test_obj["timeoutSeconds"] = test.timeout_seconds
                if test.is_blocking:
                    test_obj["isBlocking"] = test.is_blocking
                tests_list.append(test_obj)

            # Fetch calls for this stage
            calls = db(db.iceflows_stage_calls.stage_id == stage.id).select(
                orderby=db.iceflows_stage_calls.execution_order
            )
            calls_list = []
            for call in calls:
                call_obj = {
                    "name": call.name,
                    "type": call.call_type,  # "icestreams" or "iceruns"
                    "targetId": call.target_id,
                    "triggerOn": call.trigger_on,
                }
                if call.is_blocking:
                    call_obj["isBlocking"] = call.is_blocking
                calls_list.append(call_obj)

            # Parse day_restrictions and time_restrictions
            day_restrictions = stage.day_restrictions or {}
            time_restrictions = stage.time_restrictions or {}

            # Build stage object
            stage_obj = {
                "name": stage.display_name or stage.branch_name,
                "branch": stage.branch_name,
                "order": stage.stage_order,
                "isProduction": stage.is_production or False,
                "approval": {
                    "required": stage.require_approval or True,
                    "minApprovers": stage.min_approvers or 1,
                    "overrideMinApprovers": stage.override_min_approvers or 2,
                    "approvers": approver_emails,
                },
            }

            # Add day restrictions if present
            if day_restrictions or time_restrictions:
                stage_obj["dayRestrictions"] = {}
                if day_restrictions.get("blocked_days"):
                    stage_obj["dayRestrictions"]["blockedDays"] = day_restrictions[
                        "blocked_days"
                    ]
                if time_restrictions:
                    stage_obj["dayRestrictions"]["timeRestrictions"] = {
                        "startHour": time_restrictions.get("start_hour"),
                        "endHour": time_restrictions.get("end_hour"),
                        "timezone": time_restrictions.get("timezone", "UTC"),
                    }

            # Add tests if present
            if tests_list:
                stage_obj["tests"] = tests_list

            # Add calls if present
            if calls_list:
                stage_obj["calls"] = calls_list

            stages_list.append(stage_obj)

        # Build root YAML object
        yaml_data = {
            "apiVersion": "iceflows/v1",
            "kind": "Flow",
            "metadata": {
                "name": flow.name,
                "description": flow.description or "",
            },
            "spec": {
                "repository": {
                    "url": flow.repository_url,
                    "provider": flow.repository_provider or "github",
                    "defaultBranch": flow.default_branch or "main",
                },
                "stages": stages_list,
            },
        }

        # Convert to YAML
        yaml_output = yaml.dump(
            yaml_data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        # Return YAML response
        response = Response(yaml_output, mimetype="application/x-yaml")
        response.headers[
            "Content-Disposition"
        ] = f'attachment; filename="{flow.name}-flow.yaml"'

        return response, 200

    except Exception as e:
        current_app.logger.error(f"Error exporting flow {flow_id} to YAML: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
