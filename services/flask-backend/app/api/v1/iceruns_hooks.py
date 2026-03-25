"""IceRuns Webhook Endpoints for API v1.

Provides public webhook execution and webhook configuration management.
"""

import datetime
import hashlib
import hmac
import secrets

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...services.redis_streams import RedisStreams

iceruns_hooks_v1_bp = Blueprint("iceruns_hooks_v1", __name__, url_prefix="/iceruns")


def validate_hmac_signature(webhook_secret: str, body: bytes, signature_header: str) -> bool:
    """Validate HMAC signature for webhook request."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("=", 1)[1]
    computed_signature = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_signature, computed_signature)


def check_rate_limit(redis, function_id: str, rate_limit: int) -> bool:
    """Check if rate limit is exceeded (simple sliding window)."""
    key = f"iceruns:ratelimit:{function_id}"
    now = datetime.datetime.utcnow().timestamp()
    hour_ago = now - 3600

    # Remove old entries
    redis.client.zremrangebyscore(key, 0, hour_ago)

    # Count recent requests
    count = redis.client.zcount(key, hour_ago, now)

    if count >= rate_limit:
        return False

    # Add current request
    redis.client.zadd(key, {str(now): now})
    redis.client.expire(key, 3600)  # TTL 1 hour

    return True


@iceruns_hooks_v1_bp.route("/hook/<token>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def webhook_handler(token: str):
    """Public webhook endpoint for executing functions.

    No authentication middleware - uses token-based validation.
    """
    try:
        db = get_db()

        # Lookup function by webhook token
        func = db(db.iceruns.webhook_token == token).select().first()

        if not func:
            return jsonify({"error": "Invalid webhook token"}), 404

        # Check function status
        if func.status != "active":
            return jsonify({"error": f"Function is not active (status: {func.status})"}), 400

        # Validate HTTP method
        if func.allowed_methods and request.method not in func.allowed_methods:
            return jsonify({"error": f"Method {request.method} not allowed"}), 405

        # Validate IP whitelist
        if func.ip_whitelist:
            client_ip = request.remote_addr
            # Simple check - should use ipaddress module for CIDR
            if client_ip not in func.ip_whitelist:
                return jsonify({"error": "IP not whitelisted"}), 403

        # Check rate limit
        redis = RedisStreams()
        if not check_rate_limit(redis, func.function_id, func.rate_limit):
            return jsonify({"error": "Rate limit exceeded"}), 429

        # Validate HMAC signature if required
        if func.validate_signature:
            signature = request.headers.get("X-IceRuns-Signature")
            if not validate_hmac_signature(func.webhook_secret, request.get_data(), signature):
                return jsonify({"error": "Invalid signature"}), 403

        # Parse input from various sources
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
            "ip": request.remote_addr,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "signature_valid": func.validate_signature,
        }

        # Create execution record
        execution_id = secrets.token_urlsafe(16)

        exec_id = db.iceruns_executions.insert(
            execution_id=execution_id,
            function_id=func.id,
            status="queued",
            trigger_type="webhook",
            triggered_by=request.remote_addr,
            input_json=input_data,
            webhook_headers=dict(request.headers),
            webhook_ip=request.remote_addr,
            created_at=datetime.datetime.utcnow(),
        )

        db.commit()

        # Publish to Redis Streams
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

        redis.publish_icerun_task(execution_id, func.function_id, input_data, config)

        # Update execution count
        db(db.iceruns.id == func.id).update(
            execution_count=(func.execution_count or 0) + 1,
            last_executed_at=datetime.datetime.utcnow(),
        )
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "execution_id": execution_id,
                    "status": "queued",
                    "message": "Function execution queued",
                }
            ),
            202,
        )

    except Exception as e:
        current_app.logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500


@iceruns_hooks_v1_bp.route("/<function_id>/webhook", methods=["GET"])
@auth_required
@scopes_required("iceruns:read")
def get_webhook_config(function_id: str):
    """Get webhook configuration."""
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "webhook": {
                        "url": f"/api/v1/iceruns/hook/{func.webhook_token}",
                        "token": func.webhook_token,
                        "secret": func.webhook_secret,
                        "validate_signature": func.validate_signature,
                        "allowed_methods": func.allowed_methods or ["POST"],
                        "ip_whitelist": func.ip_whitelist or [],
                        "rate_limit": func.rate_limit,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting webhook config: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_hooks_v1_bp.route("/<function_id>/webhook/config", methods=["PUT"])
@auth_required
@scopes_required("iceruns:write")
def update_webhook_config(function_id: str):
    """Update webhook configuration."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json()
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        update_fields = {}
        if "validate_signature" in data:
            update_fields["validate_signature"] = bool(data["validate_signature"])
        if "allowed_methods" in data:
            if not isinstance(data["allowed_methods"], list):
                return jsonify({"error": "allowed_methods must be an array"}), 400
            update_fields["allowed_methods"] = data["allowed_methods"]
        if "ip_whitelist" in data:
            if not isinstance(data["ip_whitelist"], list):
                return jsonify({"error": "ip_whitelist must be an array"}), 400
            update_fields["ip_whitelist"] = data["ip_whitelist"]
        if "rate_limit" in data:
            if not isinstance(data["rate_limit"], int) or data["rate_limit"] < 1:
                return jsonify({"error": "rate_limit must be a positive integer"}), 400
            update_fields["rate_limit"] = data["rate_limit"]

        update_fields["updated_at"] = datetime.datetime.utcnow()

        db(db.iceruns.id == func.id).update(**update_fields)
        db.commit()

        return jsonify({"success": True, "message": "Webhook configuration updated"}), 200

    except Exception as e:
        current_app.logger.error(f"Error updating webhook config: {e}")
        return jsonify({"error": str(e)}), 500


@iceruns_hooks_v1_bp.route("/<function_id>/webhook/test", methods=["POST"])
@auth_required
@scopes_required("iceruns:execute")
def test_webhook(function_id: str):
    """Test webhook with sample payload."""
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json() or {}
        db = get_db()

        func = db((db.iceruns.function_id == function_id) & (db.iceruns.created_by_id == user_id)).select().first()

        if not func:
            return jsonify({"error": "Function not found"}), 404

        # Generate test HMAC signature
        test_payload = data.get("payload", {"test": True})
        payload_bytes = str(test_payload).encode()
        signature = hmac.new(func.webhook_secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

        return (
            jsonify(
                {
                    "success": True,
                    "test_webhook": {
                        "url": f"/api/v1/iceruns/hook/{func.webhook_token}",
                        "method": "POST",
                        "headers": {
                            "Content-Type": "application/json",
                            "X-IceRuns-Signature": f"sha256={signature}",
                        },
                        "payload": test_payload,
                        "curl_example": f'curl -X POST "{request.host_url}api/v1/iceruns/hook/{func.webhook_token}" '
                        f'-H "Content-Type: application/json" '
                        f'-H "X-IceRuns-Signature: sha256={signature}" '
                        f"-d '{test_payload}'",
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error testing webhook: {e}")
        return jsonify({"error": str(e)}), 500
