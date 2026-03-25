"""IceFlows Promotions & Approvals API Endpoints for API v1.

Provides promotion request and approval workflow management, including:
- Promotion request creation and management
- Approval and rejection handling
- Day/time restriction checking
- Override approval logic
- Merge execution
- Approval status tracking

Complex Logic:
- Day/time restriction validation with timezone support
- Multi-level approval thresholds
- Override approval for blocked days
- Test and review prerequisite checking
"""

import datetime
import uuid
from typing import Tuple

import pytz
from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...services.iceflows_notification_service import IceFlowsNotificationService

iceflows_promotions_bp = Blueprint(
    "iceflows_promotions", __name__, url_prefix="/iceflows"
)


# ============================================================================
# Helper Functions - Day/Time Restriction Logic
# ============================================================================


def check_day_restrictions(stage) -> Tuple[bool, str]:
    """Check if current day/time allows approval.

    Args:
        stage: Database stage record with day_restrictions and time_restrictions

    Returns:
        Tuple of (is_allowed, reason_if_blocked)

    Day restrictions format:
        {"blocked_days": [5, 6, 0]}  # Friday=5, Saturday=6, Sunday=0

    Time restrictions format:
        {
            "start_hour": 9,
            "end_hour": 17,
            "timezone": "America/New_York"
        }
    """
    day_restrictions = stage.day_restrictions or {}
    time_restrictions = stage.time_restrictions or {}

    # Get current time in stage's timezone (default to UTC)
    tz_name = time_restrictions.get("timezone", "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        current_app.logger.warning(
            f"Unknown timezone {tz_name}, defaulting to UTC"
        )
        tz = pytz.UTC

    now = datetime.datetime.now(tz)
    current_weekday = now.weekday()  # Monday=0, Sunday=6
    current_hour = now.hour

    # Check blocked days (convert Sunday from 6 to 0 for comparison)
    blocked_days = day_restrictions.get("blocked_days", [])
    if blocked_days:
        # PyDAL stores as weekday (Mon=0, Sun=6), but display often uses Sun=0
        # Normalize: if 0 in blocked_days, it means Sunday (weekday=6)
        normalized_blocked = []
        for day in blocked_days:
            if day == 0:
                normalized_blocked.append(6)  # Sunday
            else:
                normalized_blocked.append(day - 1)  # Shift others

        if current_weekday in normalized_blocked:
            day_names = {
                0: "Monday",
                1: "Tuesday",
                2: "Wednesday",
                3: "Thursday",
                4: "Friday",
                5: "Saturday",
                6: "Sunday",
            }
            return (
                False,
                f"Deployments blocked on {day_names[current_weekday]}. "
                f"Override approval required.",
            )

    # Check time restrictions
    start_hour = time_restrictions.get("start_hour")
    end_hour = time_restrictions.get("end_hour")

    if start_hour is not None and end_hour is not None:
        if not (start_hour <= current_hour < end_hour):
            return (
                False,
                f"Deployments allowed only between {start_hour}:00 and "
                f"{end_hour}:00 {tz_name}. Override approval required.",
            )

    return (True, "")


def get_approval_status(promotion_id: str) -> dict:
    """Calculate approval status for a promotion.

    Args:
        promotion_id: Promotion identifier

    Returns:
        Dictionary with approval status metrics:
        - total_approvers: count of approvers for target stage
        - approvals_received: count of 'approve' decisions
        - rejections_received: count of 'reject' decisions
        - min_approvers: required from stage config
        - override_min_approvers: required to override day restrictions
        - is_day_blocked: whether current day/time is blocked
        - can_merge: True if ready to merge
        - override_active: True if override threshold met
        - blocking_reason: why merge is blocked (if applicable)
    """
    db = get_db()

    # Get promotion
    promotion = db(
        db.iceflows_promotions.promotion_id == promotion_id
    ).select().first()
    if not promotion:
        return {"error": "Promotion not found"}

    # Get target stage
    target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()
    if not target_stage:
        return {"error": "Target stage not found"}

    # Count approvals and rejections
    approvals = db(
        (db.iceflows_approvals.promotion_id == promotion.id)
        & (db.iceflows_approvals.decision == "approve")
    ).count()

    rejections = db(
        (db.iceflows_approvals.promotion_id == promotion.id)
        & (db.iceflows_approvals.decision == "reject")
    ).count()

    # Count override approvals (approvals from users with can_override=True)
    override_approvals = db(
        (db.iceflows_approvals.promotion_id == promotion.id)
        & (db.iceflows_approvals.decision == "approve")
        & (db.iceflows_approvals.can_override == True)  # noqa: E712
    ).count()

    # Get stage configuration
    min_approvers = target_stage.min_approvers or 1
    override_min_approvers = target_stage.override_min_approvers or 2
    total_approvers = db(
        db.iceflows_stage_approvers.stage_id == target_stage.id
    ).count()

    # Check day/time restrictions
    is_day_allowed, block_reason = check_day_restrictions(target_stage)
    is_day_blocked = not is_day_allowed

    # Check if override is active
    override_active = override_approvals >= override_min_approvers

    # Determine if can merge
    can_merge = False
    blocking_reason = ""

    # Check if any rejections exist
    if rejections > 0:
        blocking_reason = f"Promotion has {rejections} rejection(s)"
    # Check if minimum approvals met
    elif approvals < min_approvers:
        blocking_reason = (
            f"Need {min_approvers - approvals} more approval(s) "
            f"({approvals}/{min_approvers})"
        )
    # Check day restrictions
    elif is_day_blocked and not override_active:
        blocking_reason = (
            f"{block_reason} Need {override_min_approvers - override_approvals} "
            f"more override approval(s) ({override_approvals}/{override_min_approvers})"
        )
    else:
        can_merge = True

    return {
        "total_approvers": total_approvers,
        "approvals_received": approvals,
        "rejections_received": rejections,
        "override_approvals": override_approvals,
        "min_approvers": min_approvers,
        "override_min_approvers": override_min_approvers,
        "is_day_blocked": is_day_blocked,
        "can_merge": can_merge,
        "override_active": override_active,
        "blocking_reason": blocking_reason if blocking_reason else None,
    }


def serialize_promotion(promotion, include_approvals=False):
    """Serialize promotion database row to JSON-safe dict.

    Args:
        promotion: Database promotion record
        include_approvals: Whether to include approval records

    Returns:
        Dictionary representation of promotion
    """
    db = get_db()

    # Get flow
    flow = db(db.iceflows.id == promotion.flow_id).select().first()

    # Get stages
    source_stage = db(db.iceflows_stages.id == promotion.source_stage_id).select().first()
    target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()

    # Get user info
    requested_by = None
    if promotion.requested_by_id:
        user = db(db.auth_user.id == promotion.requested_by_id).select().first()
        if user:
            requested_by = {"id": str(user.id), "name": user.username or user.email}

    merged_by = None
    if promotion.merged_by_id:
        user = db(db.auth_user.id == promotion.merged_by_id).select().first()
        if user:
            merged_by = {"id": str(user.id), "name": user.username or user.email}

    result = {
        "promotion_id": promotion.promotion_id,
        "flow_id": flow.flow_id if flow else None,
        "flow_name": flow.name if flow else None,
        "source_stage": {
            "stage_id": source_stage.stage_id if source_stage else None,
            "branch_name": source_stage.branch_name if source_stage else None,
            "display_name": source_stage.display_name if source_stage else None,
        },
        "target_stage": {
            "stage_id": target_stage.stage_id if target_stage else None,
            "branch_name": target_stage.branch_name if target_stage else None,
            "display_name": target_stage.display_name if target_stage else None,
        },
        "source_commit": promotion.source_commit or "",
        "status": promotion.status or "pending",
        "requested_by": requested_by,
        "merged_by": merged_by,
        "merged_at": promotion.merged_at.isoformat() if promotion.merged_at else None,
        "created_at": promotion.created_at.isoformat() if promotion.created_at else None,
    }

    # Add approval status
    approval_status = get_approval_status(promotion.promotion_id)
    result["approval_status"] = approval_status

    # Include approval records if requested
    if include_approvals:
        approvals = db(
            db.iceflows_approvals.promotion_id == promotion.id
        ).select(orderby=db.iceflows_approvals.approved_at)

        result["approvals"] = []
        for approval in approvals:
            approver = db(db.auth_user.id == approval.approver_id).select().first()
            result["approvals"].append({
                "approval_id": approval.approval_id,
                "approver": {
                    "id": str(approver.id) if approver else None,
                    "name": approver.username or approver.email if approver else None,
                },
                "decision": approval.decision,
                "comment": approval.comment or "",
                "can_override": approval.can_override or False,
                "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
            })

    return result


# ============================================================================
# Promotion CRUD
# ============================================================================


@iceflows_promotions_bp.route("/<flow_id>/promotions", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_promotions(flow_id: str):
    """List all promotions for a flow.

    Args:
        flow_id: Flow identifier

    Query parameters:
        - status: Filter by status (pending, approved, rejected, merged, cancelled)
        - page: Page number (default 1)
        - per_page: Items per page (default 20)

    Returns:
        JSON with promotions array and pagination
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Get flow
        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return jsonify({"success": False, "error": "Flow not found"}), 404

        # Check access
        if flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Pagination
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, int(request.args.get("per_page", 20)))
        offset = (page - 1) * per_page

        # Build query
        query = db.iceflows_promotions.flow_id == flow.id

        status = request.args.get("status")
        if status:
            query &= db.iceflows_promotions.status == status

        # Count total
        total = db(query).count()

        # Execute query with pagination
        promotions = db(query).select(
            orderby=~db.iceflows_promotions.created_at,
            limitby=(offset, offset + per_page),
        )

        result = [serialize_promotion(p, include_approvals=False) for p in promotions]

        return (
            jsonify({
                "success": True,
                "promotions": result,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing promotions for {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/<flow_id>/promotions", methods=["POST"])
@auth_required
@scopes_required("iceflows:execute")
def create_promotion(flow_id: str):
    """Request a promotion from source stage to target stage.

    Args:
        flow_id: Flow identifier

    Request body:
        - source_stage_id (required): Source stage identifier
        - target_stage_id (required): Target stage identifier
        - allow_skip (optional): Allow skipping stages (default: false)

    Returns:
        JSON with created promotion
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        # Get flow
        flow = db((db.iceflows.flow_id == flow_id)).select().first()
        if not flow:
            return jsonify({"success": False, "error": "Flow not found"}), 404

        # Check access
        if flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Validate required fields
        source_stage_id = data.get("source_stage_id")
        target_stage_id = data.get("target_stage_id")

        if not source_stage_id or not target_stage_id:
            return (
                jsonify({
                    "success": False,
                    "error": "source_stage_id and target_stage_id are required",
                }),
                400,
            )

        # Get stages
        source_stage = db(
            (db.iceflows_stages.stage_id == source_stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        target_stage = db(
            (db.iceflows_stages.stage_id == target_stage_id)
            & (db.iceflows_stages.flow_id == flow.id)
        ).select().first()

        if not source_stage or not target_stage:
            return (
                jsonify({"success": False, "error": "Source or target stage not found"}),
                404,
            )

        # Validate stage order (target should be next in sequence unless skip allowed)
        allow_skip = data.get("allow_skip", False)
        if not allow_skip and target_stage.stage_order != source_stage.stage_order + 1:
            return (
                jsonify({
                    "success": False,
                    "error": (
                        f"Target stage must be next in sequence. "
                        f"Source order: {source_stage.stage_order}, "
                        f"Target order: {target_stage.stage_order}. "
                        f"Use allow_skip=true to override."
                    ),
                }),
                400,
            )

        # Get current commit SHA (placeholder - will integrate with git later)
        source_commit = "placeholder_commit_sha_" + str(uuid.uuid4())[:8]

        # Create promotion
        promotion_id = str(uuid.uuid4())

        db_id = db.iceflows_promotions.insert(
            promotion_id=promotion_id,
            flow_id=flow.id,
            source_stage_id=source_stage.id,
            target_stage_id=target_stage.id,
            source_commit=source_commit,
            status="pending",
            requested_by_id=user_id,
        )
        db.commit()

        # Send promotion_requested notification
        try:
            flow_name = flow.name if flow else "Unknown"
            source_stage_name = (
                source_stage.display_name or source_stage.branch_name
                if source_stage else "Unknown"
            )
            target_stage_name = (
                target_stage.display_name or target_stage.branch_name
                if target_stage else "Unknown"
            )

            IceFlowsNotificationService.send_notification(
                flow_id=flow.id,
                event_type="promotion_requested",
                data={
                    "pipeline_name": flow_name,
                    "stage_name": target_stage_name,
                    "source_branch": source_stage_name,
                    "target_branch": target_stage_name,
                },
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Failed to send notification: {notify_err}")

        # Fetch and return created promotion
        promotion = db.iceflows_promotions[db_id]

        return (
            jsonify({
                "success": True,
                "promotion": serialize_promotion(promotion, include_approvals=True),
            }),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating promotion for {flow_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_promotion(promotion_id: str):
    """Get promotion details including approvals.

    Args:
        promotion_id: Promotion identifier

    Returns:
        JSON with promotion details
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Check access via flow ownership
        flow = db(db.iceflows.id == promotion.flow_id).select().first()
        if not flow or flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        return (
            jsonify({
                "success": True,
                "promotion": serialize_promotion(promotion, include_approvals=True),
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting promotion {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>", methods=["DELETE"])
@auth_required
@scopes_required("iceflows:execute")
def cancel_promotion(promotion_id: str):
    """Cancel a pending promotion.

    Args:
        promotion_id: Promotion identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Check access
        flow = db(db.iceflows.id == promotion.flow_id).select().first()
        if not flow or flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Only allow cancelling pending promotions
        if promotion.status not in ["pending", "approved"]:
            return (
                jsonify({
                    "success": False,
                    "error": f"Cannot cancel promotion with status: {promotion.status}",
                }),
                400,
            )

        # Update status to cancelled
        promotion.update_record(
            status="cancelled",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        return (
            jsonify({
                "success": True,
                "message": "Promotion cancelled successfully",
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error cancelling promotion {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>/merge", methods=["POST"])
@auth_required
@scopes_required("iceflows:execute")
def merge_promotion(promotion_id: str):
    """Execute merge for an approved promotion.

    Args:
        promotion_id: Promotion identifier

    Returns:
        JSON with merge result
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Check access
        flow = db(db.iceflows.id == promotion.flow_id).select().first()
        if not flow or flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Verify promotion is ready to merge
        approval_status = get_approval_status(promotion_id)

        if not approval_status["can_merge"]:
            return (
                jsonify({
                    "success": False,
                    "error": "Promotion not ready to merge",
                    "blocking_reason": approval_status.get("blocking_reason"),
                }),
                400,
            )

        # Check for blocking test failures (placeholder - integrate with test executions)
        # In production, check iceflows_executions for failed blocking tests
        current_app.logger.info(
            f"Checking for blocking test failures for promotion {promotion_id}"
        )

        # Check for Darwin review (placeholder - integrate with Darwin)
        current_app.logger.info(
            f"Checking for Darwin review completion for promotion {promotion_id}"
        )

        # Execute merge (placeholder - will integrate with git operations)
        current_app.logger.info(
            f"Executing merge for promotion {promotion_id}: "
            f"{promotion.source_commit} -> target stage"
        )

        # Update promotion status
        promotion.update_record(
            status="merged",
            merged_by_id=user_id,
            merged_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        # Send execution_completed notification
        try:
            flow = db(db.iceflows.id == promotion.flow_id).select().first()
            target_stage = db(
                db.iceflows_stages.id == promotion.target_stage_id
            ).select().first()
            source_stage = db(
                db.iceflows_stages.id == promotion.source_stage_id
            ).select().first()

            flow_name = flow.name if flow else "Unknown"
            source_stage_name = (
                source_stage.display_name or source_stage.branch_name
                if source_stage else "Unknown"
            )
            target_stage_name = (
                target_stage.display_name or target_stage.branch_name
                if target_stage else "Unknown"
            )

            IceFlowsNotificationService.send_notification(
                flow_id=flow.id,
                event_type="execution_completed",
                data={
                    "pipeline_name": flow_name,
                    "stage_name": target_stage_name,
                    "source_branch": source_stage_name,
                    "target_branch": target_stage_name,
                },
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Failed to send notification: {notify_err}")

        # Trigger post-merge calls (placeholder for worker integration)
        current_app.logger.info(
            f"Triggering post-merge calls for promotion {promotion_id}"
        )

        return (
            jsonify({
                "success": True,
                "promotion": serialize_promotion(promotion, include_approvals=True),
                "message": "Merge executed successfully",
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error merging promotion {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Approval Actions
# ============================================================================


@iceflows_promotions_bp.route("/promotions/<promotion_id>/approve", methods=["POST"])
@auth_required
@scopes_required("iceflows:approve")
def approve_promotion(promotion_id: str):
    """Approve a promotion.

    Args:
        promotion_id: Promotion identifier

    Request body:
        - comment (optional): Approval comment

    Returns:
        JSON with approval record
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Only allow approving pending promotions
        if promotion.status != "pending":
            return (
                jsonify({
                    "success": False,
                    "error": f"Cannot approve promotion with status: {promotion.status}",
                }),
                400,
            )

        # Get target stage
        target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()
        if not target_stage:
            return jsonify({"success": False, "error": "Target stage not found"}), 404

        # Verify user is an authorized approver for target stage
        approver = db(
            (db.iceflows_stage_approvers.stage_id == target_stage.id)
            & (db.iceflows_stage_approvers.identity_id == user_id)
        ).select().first()

        if not approver:
            return (
                jsonify({
                    "success": False,
                    "error": "User not authorized to approve for this stage",
                }),
                403,
            )

        # Check for existing approval from this user
        existing = db(
            (db.iceflows_approvals.promotion_id == promotion.id)
            & (db.iceflows_approvals.approver_id == user_id)
        ).select().first()

        if existing:
            return (
                jsonify({
                    "success": False,
                    "error": "User has already submitted a decision for this promotion",
                }),
                400,
            )

        # Create approval record
        approval_id = str(uuid.uuid4())

        db_id = db.iceflows_approvals.insert(
            approval_id=approval_id,
            promotion_id=promotion.id,
            approver_id=user_id,
            decision="approve",
            comment=data.get("comment", ""),
            can_override=approver.can_override or False,
            approved_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        # Check if approval threshold is met
        approval_status_before = get_approval_status(promotion_id)
        approval_status = approval_status_before

        # Check if override just became active (day was blocked, now it's not)
        if (
            approval_status["is_day_blocked"]
            and approval_status["override_active"]
            and approver.can_override
        ):
            # Get previous override status to detect first-time activation
            previous_override_approvals = (
                approval_status["override_approvals"] - 1
            )
            override_min = approval_status["override_min_approvers"]
            if previous_override_approvals < override_min:
                # Send promotion_override notification
                try:
                    flow = db(db.iceflows.id == promotion.flow_id).select().first()
                    target_stage = db(
                        db.iceflows_stages.id == promotion.target_stage_id
                    ).select().first()
                    source_stage = db(
                        db.iceflows_stages.id == promotion.source_stage_id
                    ).select().first()

                    flow_name = flow.name if flow else "Unknown"
                    source_stage_name = (
                        source_stage.display_name or source_stage.branch_name
                        if source_stage else "Unknown"
                    )
                    target_stage_name = (
                        target_stage.display_name or target_stage.branch_name
                        if target_stage else "Unknown"
                    )

                    IceFlowsNotificationService.send_notification(
                        flow_id=flow.id,
                        event_type="promotion_override",
                        data={
                            "pipeline_name": flow_name,
                            "stage_name": target_stage_name,
                            "source_branch": source_stage_name,
                            "target_branch": target_stage_name,
                        },
                    )
                except Exception as notify_err:
                    current_app.logger.warning(
                        f"Failed to send notification: {notify_err}"
                    )

        if approval_status["can_merge"]:
            promotion.update_record(
                status="approved",
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.commit()

            # Send promotion_approved notification
            try:
                flow = db(db.iceflows.id == promotion.flow_id).select().first()
                target_stage = db(
                    db.iceflows_stages.id == promotion.target_stage_id
                ).select().first()
                source_stage = db(
                    db.iceflows_stages.id == promotion.source_stage_id
                ).select().first()

                flow_name = flow.name if flow else "Unknown"
                source_stage_name = (
                    source_stage.display_name or source_stage.branch_name
                    if source_stage else "Unknown"
                )
                target_stage_name = (
                    target_stage.display_name or target_stage.branch_name
                    if target_stage else "Unknown"
                )

                IceFlowsNotificationService.send_notification(
                    flow_id=flow.id,
                    event_type="promotion_approved",
                    data={
                        "pipeline_name": flow_name,
                        "stage_name": target_stage_name,
                        "source_branch": source_stage_name,
                        "target_branch": target_stage_name,
                    },
                )
            except Exception as notify_err:
                current_app.logger.warning(
                    f"Failed to send notification: {notify_err}"
                )

        approval = db.iceflows_approvals[db_id]
        approver_user = db(db.auth_user.id == user_id).select().first()

        return (
            jsonify({
                "success": True,
                "approval": {
                    "approval_id": approval.approval_id,
                    "approver": {
                        "id": str(approver_user.id),
                        "name": approver_user.username or approver_user.email,
                    },
                    "decision": approval.decision,
                    "comment": approval.comment or "",
                    "can_override": approval.can_override or False,
                    "approved_at": approval.approved_at.isoformat(),
                },
                "approval_status": approval_status,
            }),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error approving promotion {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>/reject", methods=["POST"])
@auth_required
@scopes_required("iceflows:approve")
def reject_promotion(promotion_id: str):
    """Reject a promotion.

    Args:
        promotion_id: Promotion identifier

    Request body:
        - comment (required): Rejection reason

    Returns:
        JSON with rejection record
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Only allow rejecting pending promotions
        if promotion.status != "pending":
            return (
                jsonify({
                    "success": False,
                    "error": f"Cannot reject promotion with status: {promotion.status}",
                }),
                400,
            )

        # Require comment for rejections
        if not data.get("comment"):
            return (
                jsonify({"success": False, "error": "Rejection comment is required"}),
                400,
            )

        # Get target stage
        target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()
        if not target_stage:
            return jsonify({"success": False, "error": "Target stage not found"}), 404

        # Verify user is an authorized approver for target stage
        approver = db(
            (db.iceflows_stage_approvers.stage_id == target_stage.id)
            & (db.iceflows_stage_approvers.identity_id == user_id)
        ).select().first()

        if not approver:
            return (
                jsonify({
                    "success": False,
                    "error": "User not authorized to reject for this stage",
                }),
                403,
            )

        # Check for existing decision from this user
        existing = db(
            (db.iceflows_approvals.promotion_id == promotion.id)
            & (db.iceflows_approvals.approver_id == user_id)
        ).select().first()

        if existing:
            return (
                jsonify({
                    "success": False,
                    "error": "User has already submitted a decision for this promotion",
                }),
                400,
            )

        # Create rejection record
        approval_id = str(uuid.uuid4())

        db_id = db.iceflows_approvals.insert(
            approval_id=approval_id,
            promotion_id=promotion.id,
            approver_id=user_id,
            decision="reject",
            comment=data["comment"],
            can_override=approver.can_override or False,
            approved_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        # Update promotion status to rejected
        promotion.update_record(
            status="rejected",
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        # Send promotion_rejected notification
        try:
            flow = db(db.iceflows.id == promotion.flow_id).select().first()
            target_stage = db(
                db.iceflows_stages.id == promotion.target_stage_id
            ).select().first()
            source_stage = db(
                db.iceflows_stages.id == promotion.source_stage_id
            ).select().first()

            flow_name = flow.name if flow else "Unknown"
            source_stage_name = (
                source_stage.display_name or source_stage.branch_name
                if source_stage else "Unknown"
            )
            target_stage_name = (
                target_stage.display_name or target_stage.branch_name
                if target_stage else "Unknown"
            )

            IceFlowsNotificationService.send_notification(
                flow_id=flow.id,
                event_type="promotion_rejected",
                data={
                    "pipeline_name": flow_name,
                    "stage_name": target_stage_name,
                    "source_branch": source_stage_name,
                    "target_branch": target_stage_name,
                },
            )
        except Exception as notify_err:
            current_app.logger.warning(f"Failed to send notification: {notify_err}")

        approval = db.iceflows_approvals[db_id]
        approver_user = db(db.auth_user.id == user_id).select().first()

        return (
            jsonify({
                "success": True,
                "approval": {
                    "approval_id": approval.approval_id,
                    "approver": {
                        "id": str(approver_user.id),
                        "name": approver_user.username or approver_user.email,
                    },
                    "decision": approval.decision,
                    "comment": approval.comment or "",
                    "can_override": approval.can_override or False,
                    "approved_at": approval.approved_at.isoformat(),
                },
            }),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error rejecting promotion {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>/override", methods=["POST"])
@auth_required
@scopes_required("iceflows:approve")
def override_restrictions(promotion_id: str):
    """Override day/time restrictions for a promotion.

    This endpoint is informational - overrides are counted automatically
    based on approvals from users with can_override=True.

    Args:
        promotion_id: Promotion identifier

    Request body:
        - reason (required): Override justification

    Returns:
        JSON with override status
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Require override reason
        if not data.get("reason"):
            return (
                jsonify({"success": False, "error": "Override reason is required"}),
                400,
            )

        # Get target stage
        target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()
        if not target_stage:
            return jsonify({"success": False, "error": "Target stage not found"}), 404

        # Verify current day IS blocked (otherwise no override needed)
        is_day_allowed, block_reason = check_day_restrictions(target_stage)
        if is_day_allowed:
            return (
                jsonify({
                    "success": False,
                    "error": "No day/time restrictions active, override not needed",
                }),
                400,
            )

        # Verify user has override capability
        approver = db(
            (db.iceflows_stage_approvers.stage_id == target_stage.id)
            & (db.iceflows_stage_approvers.identity_id == user_id)
            & (db.iceflows_stage_approvers.can_override == True)  # noqa: E712
        ).select().first()

        if not approver:
            return (
                jsonify({
                    "success": False,
                    "error": "User not authorized to override restrictions",
                }),
                403,
            )

        # Check approval status
        approval_status = get_approval_status(promotion_id)

        return (
            jsonify({
                "success": True,
                "message": (
                    "Override counted via approval. Submit regular approval "
                    "with can_override=True to count toward override threshold."
                ),
                "override_status": {
                    "override_approvals": approval_status["override_approvals"],
                    "override_min_approvers": approval_status["override_min_approvers"],
                    "override_active": approval_status["override_active"],
                    "is_day_blocked": approval_status["is_day_blocked"],
                    "restriction_reason": block_reason,
                },
                "reason": data["reason"],
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error overriding restrictions for {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/my-approvals", methods=["GET"])
@auth_required
@scopes_required("iceflows:approve")
def get_my_approvals():
    """Get pending approvals for current user.

    Returns:
        JSON with pending approvals array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Find stages where user is an approver
        approver_records = db(
            db.iceflows_stage_approvers.identity_id == user_id
        ).select()

        stage_ids = [a.stage_id for a in approver_records]

        if not stage_ids:
            return (
                jsonify({
                    "success": True,
                    "pending_approvals": [],
                    "count": 0,
                }),
                200,
            )

        # Find pending promotions for those stages
        # where user has NOT already submitted a decision
        pending = []

        promotions = db(
            (db.iceflows_promotions.target_stage_id.belongs(stage_ids))
            & (db.iceflows_promotions.status == "pending")
        ).select(orderby=~db.iceflows_promotions.created_at)

        for promotion in promotions:
            # Check if user already decided
            existing = db(
                (db.iceflows_approvals.promotion_id == promotion.id)
                & (db.iceflows_approvals.approver_id == user_id)
            ).select().first()

            if existing:
                continue  # Skip if already decided

            # Get flow and stages
            flow = db(db.iceflows.id == promotion.flow_id).select().first()
            source_stage = db(db.iceflows_stages.id == promotion.source_stage_id).select().first()
            target_stage = db(db.iceflows_stages.id == promotion.target_stage_id).select().first()
            requester = db(db.auth_user.id == promotion.requested_by_id).select().first()

            # Check day restrictions
            is_day_allowed, _ = check_day_restrictions(target_stage)

            pending.append({
                "promotion_id": promotion.promotion_id,
                "flow_name": flow.name if flow else None,
                "source_branch": source_stage.branch_name if source_stage else None,
                "target_branch": target_stage.branch_name if target_stage else None,
                "requested_by": requester.username or requester.email if requester else None,
                "requested_at": promotion.created_at.isoformat() if promotion.created_at else None,
                "is_day_blocked": not is_day_allowed,
            })

        return (
            jsonify({
                "success": True,
                "pending_approvals": pending,
                "count": len(pending),
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting my approvals: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Approval Status
# ============================================================================


@iceflows_promotions_bp.route("/promotions/<promotion_id>/approvals", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def list_approvals(promotion_id: str):
    """List all approvals for a promotion.

    Args:
        promotion_id: Promotion identifier

    Returns:
        JSON with approvals array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Check access
        flow = db(db.iceflows.id == promotion.flow_id).select().first()
        if not flow or flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Get all approvals
        approvals = db(
            db.iceflows_approvals.promotion_id == promotion.id
        ).select(orderby=db.iceflows_approvals.approved_at)

        result = []
        for approval in approvals:
            approver = db(db.auth_user.id == approval.approver_id).select().first()
            result.append({
                "approval_id": approval.approval_id,
                "approver": {
                    "id": str(approver.id) if approver else None,
                    "name": approver.username or approver.email if approver else None,
                },
                "decision": approval.decision,
                "comment": approval.comment or "",
                "can_override": approval.can_override or False,
                "approved_at": approval.approved_at.isoformat() if approval.approved_at else None,
            })

        return (
            jsonify({
                "success": True,
                "approvals": result,
                "count": len(result),
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing approvals for {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@iceflows_promotions_bp.route("/promotions/<promotion_id>/status", methods=["GET"])
@auth_required
@scopes_required("iceflows:read")
def get_promotion_status(promotion_id: str):
    """Get approval status summary for a promotion.

    Args:
        promotion_id: Promotion identifier

    Returns:
        JSON with approval status metrics
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        promotion = db(
            db.iceflows_promotions.promotion_id == promotion_id
        ).select().first()
        if not promotion:
            return jsonify({"success": False, "error": "Promotion not found"}), 404

        # Check access
        flow = db(db.iceflows.id == promotion.flow_id).select().first()
        if not flow or flow.created_by_id != user_id:
            return jsonify({"success": False, "error": "Access denied"}), 403

        approval_status = get_approval_status(promotion_id)

        return (
            jsonify({
                "success": True,
                "status": approval_status,
            }),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting status for {promotion_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
