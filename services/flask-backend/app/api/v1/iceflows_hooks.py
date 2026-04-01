"""IceFlows Webhook Hooks - Handlers for GitHub and GitLab webhooks.

These endpoints are public (no auth required) and use signature-based validation.
Webhooks trigger automatic promotions and reviews for CI/CD pipeline orchestration.
"""

import datetime
import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request

from ...models import get_db

iceflows_hooks_bp = Blueprint("iceflows_hooks", __name__, url_prefix="/iceflows/hooks")


# ============================================================================
# Signature Verification Functions
# ============================================================================


def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature using HMAC-SHA256.

    GitHub sends the signature in the format: sha256=<hex_digest>

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value
        secret: Webhook secret from database

    Returns:
        True if signature is valid, False otherwise
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_sig = signature[7:]  # Remove 'sha256=' prefix
    computed_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)


def verify_gitlab_token(token: str, secret: str) -> bool:
    """Verify GitLab webhook token.

    GitLab sends the token in the X-Gitlab-Token header.
    This is a simple string comparison (constant-time).

    Args:
        token: X-Gitlab-Token header value
        secret: Webhook secret from database

    Returns:
        True if token matches secret, False otherwise
    """
    if not token or not secret:
        return False

    return hmac.compare_digest(token, secret)


# ============================================================================
# Event Handling Functions
# ============================================================================


def handle_push_event(
    webhook: Any, payload: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """Process push event and create automatic promotion if applicable.

    Args:
        webhook: Database webhook record
        payload: Parsed JSON payload from webhook
        provider: "github" or "gitlab"

    Returns:
        Dictionary with action result
    """
    try:
        db = get_db()

        # Extract repository and branch information based on provider
        if provider == "github":
            repo_name = payload.get("repository", {}).get("name", "")
            branch = payload.get("ref", "").split("/")[-1]  # refs/heads/main -> main
            commit_sha = payload.get("after", "")
            pusher_name = payload.get("pusher", {}).get("name", "unknown")
        elif provider == "gitlab":
            repo_name = payload.get("project", {}).get("name", "")
            branch = payload.get("ref", "").split("/")[-1]  # refs/heads/main -> main
            commit_sha = payload.get("after", "")
            pusher_name = payload.get("user_name", "unknown")
        else:
            return {"status": "error", "message": "Unknown provider"}

        flow = db.iceflows(webhook.flow_id)
        if not flow:
            return {"status": "error", "message": "Flow not found"}

        # Check if this branch is a tracked stage
        source_stage = (
            db(
                (db.iceflows_stages.flow_id == flow.id)
                & (db.iceflows_stages.branch_name == branch)
            )
            .select()
            .first()
        )

        if not source_stage:
            current_app.logger.info(
                f"Push to {branch} on {repo_name} - branch not tracked in flow"
            )
            return {"status": "skipped", "message": f"Branch {branch} not tracked"}

        # Find the next stage for auto-promotion
        target_stage = (
            db(
                (db.iceflows_stages.flow_id == flow.id)
                & (db.iceflows_stages.stage_order == source_stage.stage_order + 1)
            )
            .select()
            .first()
        )

        if not target_stage:
            current_app.logger.info(
                f"Push to {branch} on {repo_name} - no target stage for promotion"
            )
            return {"status": "skipped", "message": "No target stage for promotion"}

        # Check if auto-promote is enabled
        if not target_stage.auto_promote:
            current_app.logger.info(
                f"Auto-promote disabled for {target_stage.display_name}"
            )
            return {
                "status": "skipped",
                "message": "Auto-promote disabled for target stage",
            }

        # Create automatic promotion
        result = create_automatic_promotion(
            flow_id=flow.id,
            source_stage_id=source_stage.id,
            target_stage_id=target_stage.id,
            commit_sha=commit_sha,
            pusher_name=pusher_name,
        )

        return result

    except Exception as e:
        current_app.logger.error(f"Error handling push event: {e}")
        return {"status": "error", "message": str(e)}


def handle_pr_event(
    webhook: Any, payload: Dict[str, Any], provider: str
) -> Dict[str, Any]:
    """Process pull/merge request event and trigger review if applicable.

    Args:
        webhook: Database webhook record
        payload: Parsed JSON payload from webhook
        provider: "github" or "gitlab"

    Returns:
        Dictionary with action result
    """
    try:
        db = get_db()

        # Extract PR/MR information based on provider
        if provider == "github":
            action = payload.get("action", "")
            pr_number = payload.get("number")
            pr_title = payload.get("pull_request", {}).get("title", "")
            source_branch = (
                payload.get("pull_request", {}).get("head", {}).get("ref", "")
            )
            target_branch = (
                payload.get("pull_request", {}).get("base", {}).get("ref", "")
            )
            pr_url = payload.get("pull_request", {}).get("html_url", "")
            author = (
                payload.get("pull_request", {}).get("user", {}).get("login", "unknown")
            )

            # Only process opened or synchronize actions
            if action not in ["opened", "synchronize"]:
                return {
                    "status": "skipped",
                    "message": f"Action '{action}' not tracked",
                }

        elif provider == "gitlab":
            action = payload.get("object_attributes", {}).get("action", "")
            mr_number = payload.get("object_attributes", {}).get("iid")
            pr_title = payload.get("object_attributes", {}).get("title", "")
            source_branch = payload.get("object_attributes", {}).get(
                "source_branch", ""
            )
            target_branch = payload.get("object_attributes", {}).get(
                "target_branch", ""
            )
            pr_url = payload.get("object_attributes", {}).get("url", "")
            author = payload.get("user", {}).get("username", "unknown")

            # Only process opened or updated actions
            if action not in ["open", "update"]:
                return {
                    "status": "skipped",
                    "message": f"Action '{action}' not tracked",
                }
        else:
            return {"status": "error", "message": "Unknown provider"}

        flow = db.iceflows(webhook.flow_id)
        if not flow:
            return {"status": "error", "message": "Flow not found"}

        # Check if target branch is a tracked stage
        target_stage = (
            db(
                (db.iceflows_stages.flow_id == flow.id)
                & (db.iceflows_stages.branch_name == target_branch)
            )
            .select()
            .first()
        )

        if not target_stage:
            current_app.logger.info(
                f"PR/MR #{pr_number} targeting {target_branch} - branch not tracked"
            )
            return {
                "status": "skipped",
                "message": f"Branch {target_branch} not tracked",
            }

        # Log PR/MR event - in a real implementation, this would trigger review workflows
        current_app.logger.info(
            f"PR/MR #{pr_number} '{pr_title}' targeting {target_branch} by {author}"
        )

        return {
            "status": "received",
            "message": f"PR/MR #{pr_number} received for review",
            "pr_number": pr_number if provider == "github" else mr_number,
            "title": pr_title,
            "author": author,
        }

    except Exception as e:
        current_app.logger.error(f"Error handling PR/MR event: {e}")
        return {"status": "error", "message": str(e)}


def create_automatic_promotion(
    flow_id: int,
    source_stage_id: int,
    target_stage_id: int,
    commit_sha: str,
    pusher_name: str = "webhook",
) -> Dict[str, Any]:
    """Create an automatic promotion between stages.

    Args:
        flow_id: Flow database ID
        source_stage_id: Source stage database ID
        target_stage_id: Target stage database ID
        commit_sha: Git commit SHA
        pusher_name: Name of user triggering the promotion

    Returns:
        Dictionary with promotion creation result
    """
    try:
        db = get_db()

        # Create promotion record
        promotion_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()

        db.iceflows_promotions.insert(
            promotion_id=promotion_id,
            flow_id=flow_id,
            source_stage_id=source_stage_id,
            target_stage_id=target_stage_id,
            triggered_by=pusher_name,
            trigger_type="webhook_push",
            commit_sha=commit_sha,
            status="pending",
            created_at=now,
        )
        db.commit()

        current_app.logger.info(
            f"Created automatic promotion {promotion_id} "
            f"from stage {source_stage_id} to {target_stage_id} "
            f"by {pusher_name}"
        )

        return {
            "status": "created",
            "message": "Automatic promotion created",
            "promotion_id": promotion_id,
        }

    except Exception as e:
        current_app.logger.error(f"Error creating automatic promotion: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# Webhook Endpoints
# ============================================================================


@iceflows_hooks_bp.route("/github/<webhook_id>", methods=["POST"])
def github_webhook(webhook_id: str):
    """GitHub webhook endpoint.

    Handles GitHub webhook events (push, pull_request, ping).
    Verifies signature using X-Hub-Signature-256 header.

    Args:
        webhook_id: Webhook ID from URL path

    Returns:
        JSON response with status
    """
    try:
        db = get_db()

        # Look up webhook configuration
        webhook = db(db.iceflows_webhooks.webhook_id == webhook_id).select().first()

        if not webhook:
            current_app.logger.warning(f"GitHub webhook not found: {webhook_id}")
            return jsonify({"error": "Webhook not found"}), 404

        if not webhook.is_active:
            current_app.logger.warning(f"GitHub webhook disabled: {webhook_id}")
            return jsonify({"error": "Webhook is disabled"}), 403

        if webhook.provider != "github":
            return jsonify({"error": "Webhook provider mismatch"}), 400

        # Get request body and signature
        payload = request.get_data()
        signature = request.headers.get("X-Hub-Signature-256")

        # Verify signature
        if not verify_github_signature(payload, signature, webhook.webhook_secret):
            current_app.logger.warning(
                f"Invalid GitHub signature for webhook {webhook_id}"
            )
            return jsonify({"error": "Invalid signature"}), 401

        # Get event type
        event_type = request.headers.get("X-GitHub-Event", "unknown")

        # Update webhook record
        now = datetime.datetime.utcnow()
        webhook.update_record(last_received_at=now, last_status="received")
        db.commit()

        # Handle ping event (webhook verification)
        if event_type == "ping":
            current_app.logger.info(f"GitHub webhook ping received: {webhook_id}")
            return jsonify({"status": "pong"}), 200

        # Parse JSON payload
        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError:
            current_app.logger.error(f"Invalid JSON in GitHub webhook: {webhook_id}")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Route to appropriate handler
        result = {
            "status": "unhandled",
            "message": f"Event type '{event_type}' not handled",
        }

        if event_type == "push":
            result = handle_push_event(webhook, payload_json, "github")
        elif event_type == "pull_request":
            result = handle_pr_event(webhook, payload_json, "github")

        # Log the action
        current_app.logger.info(
            f"GitHub webhook {webhook_id} processed event '{event_type}': {result.get('status')}"
        )

        # Update webhook status
        webhook.update_record(last_status=result.get("status", "unknown"))
        db.commit()

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"Error processing GitHub webhook {webhook_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@iceflows_hooks_bp.route("/gitlab/<webhook_id>", methods=["POST"])
def gitlab_webhook(webhook_id: str):
    """GitLab webhook endpoint.

    Handles GitLab webhook events (Push Hook, Merge Request Hook, System Hook).
    Verifies token using X-Gitlab-Token header.

    Args:
        webhook_id: Webhook ID from URL path

    Returns:
        JSON response with status
    """
    try:
        db = get_db()

        # Look up webhook configuration
        webhook = db(db.iceflows_webhooks.webhook_id == webhook_id).select().first()

        if not webhook:
            current_app.logger.warning(f"GitLab webhook not found: {webhook_id}")
            return jsonify({"error": "Webhook not found"}), 404

        if not webhook.is_active:
            current_app.logger.warning(f"GitLab webhook disabled: {webhook_id}")
            return jsonify({"error": "Webhook is disabled"}), 403

        if webhook.provider != "gitlab":
            return jsonify({"error": "Webhook provider mismatch"}), 400

        # Get token
        token = request.headers.get("X-Gitlab-Token")

        # Verify token
        if not verify_gitlab_token(token, webhook.webhook_secret):
            current_app.logger.warning(f"Invalid GitLab token for webhook {webhook_id}")
            return jsonify({"error": "Invalid token"}), 401

        # Get event type
        event_type = request.headers.get("X-Gitlab-Event", "unknown")

        # Update webhook record
        now = datetime.datetime.utcnow()
        webhook.update_record(last_received_at=now, last_status="received")
        db.commit()

        # Handle System Hook ping
        if event_type == "System Hook":
            current_app.logger.info(f"GitLab system hook ping received: {webhook_id}")
            return jsonify({"status": "pong"}), 200

        # Parse JSON payload
        try:
            payload_json = json.loads(request.get_data())
        except json.JSONDecodeError:
            current_app.logger.error(f"Invalid JSON in GitLab webhook: {webhook_id}")
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Route to appropriate handler
        result = {
            "status": "unhandled",
            "message": f"Event type '{event_type}' not handled",
        }

        if event_type == "Push Hook":
            result = handle_push_event(webhook, payload_json, "gitlab")
        elif event_type == "Merge Request Hook":
            result = handle_pr_event(webhook, payload_json, "gitlab")

        # Log the action
        current_app.logger.info(
            f"GitLab webhook {webhook_id} processed event '{event_type}': {result.get('status')}"
        )

        # Update webhook status
        webhook.update_record(last_status=result.get("status", "unknown"))
        db.commit()

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"Error processing GitLab webhook {webhook_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
