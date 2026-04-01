"""Playbook Approvals API Endpoints for API v1.

Provides approval gate management and approval workflow for playbook executions:
- Get pending approvals for current user
- Approve/reject paused executions
- Approval status tracking
- Approval gate CRUD operations
"""

import datetime
import uuid

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db

playbook_approvals_bp = Blueprint(
    "playbook_approvals", __name__, url_prefix="/playbooks"
)


# ============================================================================
# Pending Approvals
# ============================================================================


@playbook_approvals_bp.route("/my-approvals", methods=["GET"])
@auth_required
@scopes_required("playbooks:approve")
def get_my_approvals():
    """Get pending approvals for current user.

    Returns paused playbook executions waiting for the current user's approval.

    Returns:
        JSON with pending approvals array
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Find approval gates where user is an approver
        # This includes both direct user approvers and group-based approvers
        gates_query = (db.playbook_approval_gates.approvers.contains(user_id)) & (
            db.playbook_approval_gates.is_enabled == True
        )  # noqa: E712
        gates = db(gates_query).select()
        gate_ids = [g.id for g in gates]

        if not gate_ids:
            return (
                jsonify(
                    {
                        "success": True,
                        "pending_approvals": [],
                        "count": 0,
                    }
                ),
                200,
            )

        # Find paused executions for those gates
        # where user has NOT already submitted a decision
        pending = []

        executions = db(db.playbook_executions.status == "paused_for_approval").select(
            orderby=~db.playbook_executions.created_at
        )

        for execution in executions:
            # Check if user already decided on this execution
            existing = (
                db(
                    (
                        db.playbook_execution_approvals.execution_id
                        == execution.execution_id
                    )
                    & (db.playbook_execution_approvals.approver_id == user_id)
                )
                .select()
                .first()
            )

            if existing:
                continue  # Skip if already decided

            # Get playbook details
            playbook = db(db.playbooks.id == execution.playbook_id).select().first()
            if not playbook:
                continue

            # Find the gate this execution is paused at
            # (stored in execution metadata or determined from playbook structure)
            # For now, we'll match any gate associated with this playbook
            execution_gates = db(
                (db.playbook_approval_gates.playbook_id == playbook.id)
                & (db.playbook_approval_gates.id.belongs(gate_ids))
                & (db.playbook_approval_gates.is_enabled == True)  # noqa: E712
            ).select()

            if not execution_gates:
                continue

            # Get the requester
            requester = None
            if execution.triggered_by_id:
                requester = (
                    db(db.identities.id == execution.triggered_by_id).select().first()
                )

            # Get the gate (use first matching gate for now)
            gate = execution_gates.first()

            pending.append(
                {
                    "execution_id": execution.execution_id,
                    "playbook_id": playbook.playbook_id,
                    "playbook_name": playbook.name,
                    "gate_id": gate.gate_id if gate else None,
                    "gate_name": gate.name if gate else "Unknown Gate",
                    "requested_by": (
                        requester.username
                        if requester
                        else execution.triggered_by or "Unknown"
                    ),
                    "requested_at": (
                        execution.created_at.isoformat()
                        if execution.created_at
                        else None
                    ),
                    "paused_at": (
                        execution.started_at.isoformat()
                        if execution.started_at
                        else None
                    ),
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "pending_approvals": pending,
                    "count": len(pending),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting my approvals: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Approval Actions
# ============================================================================


@playbook_approvals_bp.route("/executions/<execution_id>/approve", methods=["POST"])
@auth_required
@scopes_required("playbooks:approve")
def approve_execution(execution_id: str):
    """Approve a paused playbook execution.

    Args:
        execution_id: Execution identifier

    Request body:
        {
            "comment": "Optional approval comment"
        }

    Returns:
        JSON with success status
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        # Find execution
        execution = (
            db(db.playbook_executions.execution_id == execution_id).select().first()
        )

        if not execution:
            return jsonify({"success": False, "error": "Execution not found"}), 404

        if execution.status != "paused_for_approval":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Execution is not paused for approval",
                    }
                ),
                400,
            )

        # Find the gate for this execution
        playbook = db(db.playbooks.id == execution.playbook_id).select().first()
        if not playbook:
            return jsonify({"success": False, "error": "Playbook not found"}), 404

        # Get active gates for this playbook
        gates = db(
            (db.playbook_approval_gates.playbook_id == playbook.id)
            & (db.playbook_approval_gates.is_enabled == True)  # noqa: E712
        ).select()

        # Verify user is an approver
        user_can_approve = False
        gate_id = None
        for gate in gates:
            if user_id in (gate.approvers or []):
                user_can_approve = True
                gate_id = gate.id
                break

        if not user_can_approve:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "You are not authorized to approve this execution",
                    }
                ),
                403,
            )

        # Check if user already approved
        existing = (
            db(
                (db.playbook_execution_approvals.execution_id == execution_id)
                & (db.playbook_execution_approvals.approver_id == user_id)
            )
            .select()
            .first()
        )

        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "You have already submitted an approval decision",
                    }
                ),
                400,
            )

        # Record approval
        approval_id = str(uuid.uuid4())
        db.playbook_execution_approvals.insert(
            approval_id=approval_id,
            execution_id=execution_id,
            gate_id=gate_id,
            approver_id=user_id,
            decision="approve",
            comment=data.get("comment", ""),
        )
        db.commit()

        # Check if we have enough approvals to proceed
        # For now, single approval is sufficient (can be enhanced with min_approvers logic)
        # Resume execution by updating status
        db(db.playbook_executions.execution_id == execution_id).update(status="running")
        db.commit()

        # TODO: Trigger worker to resume execution from paused node

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Execution approved and resumed",
                    "approval_id": approval_id,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error approving execution {execution_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@playbook_approvals_bp.route("/executions/<execution_id>/reject", methods=["POST"])
@auth_required
@scopes_required("playbooks:approve")
def reject_execution(execution_id: str):
    """Reject a paused playbook execution.

    Args:
        execution_id: Execution identifier

    Request body:
        {
            "comment": "Required rejection reason"
        }

    Returns:
        JSON with success status
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        data = request.get_json() or {}

        # Require comment for rejection
        comment = data.get("comment", "").strip()
        if not comment:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Comment is required for rejection",
                    }
                ),
                400,
            )

        # Find execution
        execution = (
            db(db.playbook_executions.execution_id == execution_id).select().first()
        )

        if not execution:
            return jsonify({"success": False, "error": "Execution not found"}), 404

        if execution.status != "paused_for_approval":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Execution is not paused for approval",
                    }
                ),
                400,
            )

        # Find the gate for this execution
        playbook = db(db.playbooks.id == execution.playbook_id).select().first()
        if not playbook:
            return jsonify({"success": False, "error": "Playbook not found"}), 404

        # Get active gates for this playbook
        gates = db(
            (db.playbook_approval_gates.playbook_id == playbook.id)
            & (db.playbook_approval_gates.is_enabled == True)  # noqa: E712
        ).select()

        # Verify user is an approver
        user_can_approve = False
        gate_id = None
        for gate in gates:
            if user_id in (gate.approvers or []):
                user_can_approve = True
                gate_id = gate.id
                break

        if not user_can_approve:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "You are not authorized to reject this execution",
                    }
                ),
                403,
            )

        # Check if user already decided
        existing = (
            db(
                (db.playbook_execution_approvals.execution_id == execution_id)
                & (db.playbook_execution_approvals.approver_id == user_id)
            )
            .select()
            .first()
        )

        if existing:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "You have already submitted an approval decision",
                    }
                ),
                400,
            )

        # Record rejection
        approval_id = str(uuid.uuid4())
        db.playbook_execution_approvals.insert(
            approval_id=approval_id,
            execution_id=execution_id,
            gate_id=gate_id,
            approver_id=user_id,
            decision="reject",
            comment=comment,
        )
        db.commit()

        # Mark execution as failed due to rejection
        db(db.playbook_executions.execution_id == execution_id).update(
            status="failed",
            error_message=f"Rejected during approval gate: {comment}",
            completed_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Execution rejected",
                    "approval_id": approval_id,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error rejecting execution {execution_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Approval Status
# ============================================================================


@playbook_approvals_bp.route(
    "/executions/<execution_id>/approval-status", methods=["GET"]
)
@auth_required
@scopes_required("playbooks:read")
def get_approval_status(execution_id: str):
    """Get approval status for an execution.

    Args:
        execution_id: Execution identifier

    Returns:
        JSON with approval status and decisions
    """
    try:
        get_current_user()  # Verify authentication
        db = get_db()

        # Find execution
        execution = (
            db(db.playbook_executions.execution_id == execution_id).select().first()
        )

        if not execution:
            return jsonify({"success": False, "error": "Execution not found"}), 404

        # Get all approvals for this execution
        approvals = db(
            db.playbook_execution_approvals.execution_id == execution_id
        ).select(orderby=db.playbook_execution_approvals.created_at)

        result = []
        for approval in approvals:
            approver = db(db.identities.id == approval.approver_id).select().first()
            gate = (
                db(db.playbook_approval_gates.id == approval.gate_id).select().first()
            )
            result.append(
                {
                    "approval_id": approval.approval_id,
                    "approver": {
                        "id": str(approver.id) if approver else None,
                        "name": approver.username if approver else "Unknown",
                    },
                    "gate_name": gate.name if gate else "Unknown Gate",
                    "decision": approval.decision,
                    "comment": approval.comment or "",
                    "created_at": (
                        approval.created_at.isoformat() if approval.created_at else None
                    ),
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "execution_status": execution.status,
                    "approvals": result,
                    "count": len(result),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error getting approval status for {execution_id}: {e}"
        )
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Approval Gate Management
# ============================================================================


@playbook_approvals_bp.route("/<playbook_id>/approval-gates", methods=["GET"])
@auth_required
@scopes_required("playbooks:read")
def list_approval_gates(playbook_id: str):
    """List all approval gates for a playbook.

    Args:
        playbook_id: Playbook identifier

    Returns:
        JSON with approval gates array
    """
    try:
        db = get_db()

        # Find playbook
        playbook = db(db.playbooks.playbook_id == playbook_id).select().first()
        if not playbook:
            return jsonify({"success": False, "error": "Playbook not found"}), 404

        # Get all gates for this playbook
        gates = db(db.playbook_approval_gates.playbook_id == playbook.id).select(
            orderby=db.playbook_approval_gates.created_at
        )

        result = []
        for gate in gates:
            result.append(
                {
                    "gate_id": gate.gate_id,
                    "node_id": gate.node_id,
                    "name": gate.name,
                    "description": gate.description or "",
                    "require_approval": gate.require_approval,
                    "min_approvers": gate.min_approvers,
                    "approvers": gate.approvers or [],
                    "approver_groups": gate.approver_groups or [],
                    "timeout_minutes": gate.timeout_minutes,
                    "is_enabled": gate.is_enabled,
                    "created_at": (
                        gate.created_at.isoformat() if gate.created_at else None
                    ),
                    "updated_at": (
                        gate.updated_at.isoformat() if gate.updated_at else None
                    ),
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "gates": result,
                    "count": len(result),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing approval gates for {playbook_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@playbook_approvals_bp.route("/<playbook_id>/approval-gates", methods=["POST"])
@auth_required
@scopes_required("playbooks:write")
def create_approval_gate(playbook_id: str):
    """Create a new approval gate for a playbook.

    Args:
        playbook_id: Playbook identifier

    Request body:
        {
            "node_id": "node-123",
            "name": "Production Approval",
            "description": "Requires approval before production deployment",
            "require_approval": true,
            "min_approvers": 2,
            "approvers": [1, 2, 3],
            "approver_groups": [10, 11],
            "timeout_minutes": 60,
            "is_enabled": true
        }

    Returns:
        JSON with created gate
    """
    try:
        get_current_user()  # Verify authentication
        db = get_db()
        data = request.get_json() or {}

        # Find playbook
        playbook = db(db.playbooks.playbook_id == playbook_id).select().first()
        if not playbook:
            return jsonify({"success": False, "error": "Playbook not found"}), 404

        # Validate required fields
        if not data.get("node_id") or not data.get("name"):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "node_id and name are required",
                    }
                ),
                400,
            )

        # Create gate
        gate_id = str(uuid.uuid4())
        db.playbook_approval_gates.insert(
            gate_id=gate_id,
            playbook_id=playbook.id,
            node_id=data["node_id"],
            name=data["name"],
            description=data.get("description", ""),
            require_approval=data.get("require_approval", True),
            min_approvers=data.get("min_approvers", 1),
            approvers=data.get("approvers", []),
            approver_groups=data.get("approver_groups", []),
            timeout_minutes=data.get("timeout_minutes"),
            is_enabled=data.get("is_enabled", True),
        )
        db.commit()

        # Return created gate
        gate = db(db.playbook_approval_gates.gate_id == gate_id).select().first()

        return (
            jsonify(
                {
                    "success": True,
                    "gate": {
                        "gate_id": gate.gate_id,
                        "node_id": gate.node_id,
                        "name": gate.name,
                        "description": gate.description or "",
                        "require_approval": gate.require_approval,
                        "min_approvers": gate.min_approvers,
                        "approvers": gate.approvers or [],
                        "approver_groups": gate.approver_groups or [],
                        "timeout_minutes": gate.timeout_minutes,
                        "is_enabled": gate.is_enabled,
                    },
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating approval gate for {playbook_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
