"""Playbook Webhook Hooks - Public endpoints for triggering playbooks.

These endpoints are public (no auth required) and use token-based validation.
"""

import datetime
import hashlib
import hmac
import uuid

from flask import Blueprint, current_app, jsonify, request

from ...models import get_db

playbook_hooks_v1_bp = Blueprint("playbook_hooks_v1", __name__, url_prefix="/hooks")


def verify_hmac_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature.

    Args:
        payload: Request body bytes
        signature: Signature from header (sha256=...)
        secret: HMAC secret

    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_sig = signature[7:]  # Remove 'sha256=' prefix
    computed_sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_sig, computed_sig)


@playbook_hooks_v1_bp.route(
    "/<token>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
def trigger_webhook(token: str):
    """Trigger a playbook via webhook.

    This is a public endpoint - no authentication required.
    The token in the URL identifies and authorizes the webhook.

    Args:
        token: Webhook token

    Returns:
        JSON execution info or error
    """
    try:
        db = get_db()

        # Find webhook by token
        webhook = db(db.playbook_webhooks.token == token).select().first()
        if not webhook:
            return jsonify({"error": "Invalid webhook token"}), 404

        if not webhook.is_enabled:
            return jsonify({"error": "Webhook is disabled"}), 403

        # Check allowed methods
        allowed_methods = webhook.allowed_methods or ["POST"]
        if request.method not in allowed_methods:
            return (
                jsonify(
                    {
                        "error": f"Method {request.method} not allowed. Allowed: {allowed_methods}"
                    }
                ),
                405,
            )

        # Get playbook
        playbook = db.playbooks(webhook.playbook_id)
        if not playbook:
            return jsonify({"error": "Playbook not found"}), 404

        if not playbook.is_enabled:
            return jsonify({"error": "Playbook is disabled"}), 403

        # Validate signature if required
        if webhook.validate_signature and webhook.signature_secret:
            signature = request.headers.get(
                "X-Hub-Signature-256"
            ) or request.headers.get("X-Signature-256")
            if not verify_hmac_signature(
                request.data, signature, webhook.signature_secret
            ):
                return jsonify({"error": "Invalid signature"}), 401

        # Get input data from request
        input_data = {}
        if request.is_json:
            input_data = request.get_json() or {}
        elif request.form:
            input_data = dict(request.form)
        elif request.args:
            input_data = dict(request.args)

        # Add webhook metadata
        input_data["__webhook__"] = {
            "method": request.method,
            "headers": dict(request.headers),
            "remote_addr": request.remote_addr,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }

        # Create execution record
        execution_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()

        db.playbook_executions.insert(
            id=execution_id,
            playbook_id=playbook.id,
            triggered_by_id=None,  # No user - triggered by webhook
            trigger_type="webhook",
            status="pending",
            input_json=input_data,
            started_at=now,
        )
        db.commit()

        # Update playbook execution stats
        playbook.update_record(
            execution_count=(playbook.execution_count or 0) + 1,
            last_execution_at=now,
        )
        db.commit()

        # TODO: Queue task to Redis Streams for worker processing
        # redis_streams.publish_task(execution_id, playbook.id, input_data)

        current_app.logger.info(
            f"Webhook triggered playbook {playbook.id}, execution {execution_id}"
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
        current_app.logger.error(f"Error triggering webhook {token}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@playbook_hooks_v1_bp.route("/<token>/test", methods=["GET", "POST"])
def test_webhook(token: str):
    """Test a webhook without triggering execution.

    Args:
        token: Webhook token

    Returns:
        JSON with webhook info and validation result
    """
    try:
        db = get_db()

        webhook = db(db.playbook_webhooks.token == token).select().first()
        if not webhook:
            return jsonify({"error": "Invalid webhook token"}), 404

        playbook = db.playbooks(webhook.playbook_id)

        # Validate signature if provided and required
        signature_valid = None
        if webhook.validate_signature and webhook.signature_secret:
            signature = request.headers.get(
                "X-Hub-Signature-256"
            ) or request.headers.get("X-Signature-256")
            if signature:
                signature_valid = verify_hmac_signature(
                    request.data, signature, webhook.signature_secret
                )
            else:
                signature_valid = False

        return (
            jsonify(
                {
                    "success": True,
                    "webhook": {
                        "name": webhook.name,
                        "is_enabled": webhook.is_enabled,
                        "allowed_methods": webhook.allowed_methods or ["POST"],
                        "validate_signature": webhook.validate_signature,
                    },
                    "playbook": {
                        "id": str(playbook.id) if playbook else None,
                        "name": playbook.name if playbook else None,
                        "is_enabled": playbook.is_enabled if playbook else None,
                    },
                    "request": {
                        "method": request.method,
                        "content_type": request.content_type,
                        "has_body": len(request.data) > 0,
                    },
                    "signature_valid": signature_valid,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error testing webhook {token}: {e}")
        return jsonify({"error": "Internal server error"}), 500
