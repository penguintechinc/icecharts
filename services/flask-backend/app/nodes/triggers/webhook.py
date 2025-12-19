"""
Webhook Trigger Node - Executes workflow when external HTTP request is received.

This trigger node fires workflow execution based on incoming HTTP requests to a
webhook endpoint. It validates HTTP methods, verifies webhook signatures (GitHub
and Stripe style), and passes request payload, headers, and metadata to downstream
nodes.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


class WebhookTrigger(BaseTrigger):
    """
    Webhook trigger node for HTTP request-based workflow execution.

    This node fires a workflow when an external system makes an HTTP request to
    the webhook endpoint. It supports signature verification (GitHub and Stripe
    style), HTTP method filtering, and passes the complete request context to
    downstream nodes including payload, headers, method, and source IP.

    Configuration:
        allowedMethods (list, optional): List of allowed HTTP methods
                                        (e.g., ["GET", "POST", "PUT"]).
                                        If empty, all methods are allowed.
                                        Default: [].
        secretKey (str, optional): Secret key for HMAC signature verification.
                                  Required for signature validation.
                                  Minimum 16 characters recommended.
                                  Default: "".

    Example Configuration:
        {
            "allowedMethods": ["POST", "PUT"],
            "secretKey": "your-secret-key-here"
        }
    """

    node_type = "trigger_webhook"
    name = "Webhook"
    description = "Trigger workflow from incoming webhook requests"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """
        Webhook triggers have no inputs.

        Returns:
            Empty list - triggers are entry points with no upstream inputs.
        """
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """
        Define output ports for webhook data.

        Returns:
            List containing output ports for webhook payload and metadata.
        """
        return [
            NodeOutput(
                name="out",
                description="Webhook payload and metadata including timestamp, method, headers",
                data_type="object",
            ),
            NodeOutput(
                name="body", description="Raw request body (payload)", data_type="any"
            ),
            NodeOutput(
                name="headers",
                description="Request headers dictionary",
                data_type="object",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate webhook trigger configuration.

        Validates:
        - HTTP methods are valid (GET, POST, PUT, PATCH, DELETE)
        - Secret key minimum length for security (if provided)

        Args:
            config: Configuration dictionary containing allowedMethods and secretKey.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        # Validate allowed methods if specified
        allowed_methods = config.get("allowedMethods", [])
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}

        if not isinstance(allowed_methods, list):
            errors.append("allowedMethods must be a list")
        else:
            for method in allowed_methods:
                if not isinstance(method, str):
                    errors.append("All methods in allowedMethods must be strings")
                    break
                if method.upper() not in valid_methods:
                    errors.append(
                        f"Invalid HTTP method: {method}. "
                        f"Valid methods: {', '.join(sorted(valid_methods))}"
                    )

        # Validate secret key format if provided
        secret = config.get("secretKey", "")
        if secret:
            if not isinstance(secret, str):
                errors.append("secretKey must be a string")
            elif len(secret) < 16:
                errors.append("secretKey should be at least 16 characters for security")

        return errors

    def _verify_signature(
        self, payload: bytes, signature: str, secret: str, algorithm: str = "sha256"
    ) -> bool:
        """
        Verify webhook signature (supports GitHub and Stripe-style signatures).

        This method validates HMAC signatures in two formats:
        - GitHub: X-Hub-Signature-256 header with "sha256=" prefix
        - Stripe: X-Signature header with "sha256=" prefix

        Args:
            payload: Raw request body as bytes.
            signature: Signature string from request header (with or without prefix).
            secret: Secret key used to compute expected signature.
            algorithm: Hash algorithm ("sha256" or "sha1").

        Returns:
            True if signature is valid or no verification required, False if invalid.
        """
        if not signature or not secret:
            return True

        # Handle different signature formats (remove algorithm prefix if present)
        sig_value = signature
        if sig_value.startswith("sha256="):
            sig_value = sig_value[7:]
            algorithm = "sha256"
        elif sig_value.startswith("sha1="):
            sig_value = sig_value[5:]
            algorithm = "sha1"

        # Select hash algorithm
        hash_algo = hashlib.sha256 if algorithm == "sha256" else hashlib.sha1

        # Compute expected signature
        expected = hmac.new(secret.encode("utf-8"), payload, hash_algo).hexdigest()

        # Compare signatures using constant-time comparison
        return hmac.compare_digest(expected.lower(), sig_value.lower())

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """
        Fire the webhook trigger and produce output data.

        Validates incoming webhook request, verifies signature if configured,
        checks allowed HTTP methods, and outputs request context to downstream nodes.

        Args:
            context: Execution context containing configuration and logger.
            trigger_data: Trigger-specific webhook data from the request.

        Returns:
            NodeResult with webhook payload and metadata in output ports,
            or failure status with error message on validation failure.
        """
        start_time = time.perf_counter()

        try:
            # Extract webhook data from trigger context
            trigger_data_config = context.config.get("_trigger_data", {})

            method = trigger_data_config.get("method", "POST")
            headers = trigger_data_config.get("headers", {})
            body = trigger_data_config.get("body", {})
            raw_body = trigger_data_config.get("raw_body", b"")
            query_params = trigger_data_config.get("query_params", {})
            source_ip = trigger_data_config.get("source_ip", "unknown")

            # Validate HTTP method if restrictions are configured
            allowed_methods = context.config.get("allowedMethods", [])
            if allowed_methods:
                method_upper = method.upper()
                allowed_methods_upper = [m.upper() for m in allowed_methods]

                if method_upper not in allowed_methods_upper:
                    error_msg = (
                        f"HTTP method {method} not allowed. "
                        f"Allowed methods: {', '.join(allowed_methods)}"
                    )
                    context.log_warning(error_msg)
                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.failure_result(
                        error=error_msg, execution_time_ms=execution_time
                    )

            # Verify signature if secret key is configured
            secret = context.config.get("secretKey", "")
            if secret:
                # Check for signature in standard headers
                signature = (
                    headers.get("X-Hub-Signature-256")
                    or headers.get("X-Hub-Signature")
                    or headers.get("X-Signature")
                    or ""
                )

                # Ensure raw_body is bytes
                if isinstance(raw_body, str):
                    raw_body_bytes = raw_body.encode("utf-8")
                elif isinstance(raw_body, bytes):
                    raw_body_bytes = raw_body
                else:
                    raw_body_bytes = b""

                if not self._verify_signature(raw_body_bytes, signature, secret):
                    error_msg = "Webhook signature verification failed"
                    context.log_warning(
                        f"Signature verification failed for webhook from {source_ip}"
                    )
                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.failure_result(
                        error=error_msg, execution_time_ms=execution_time
                    )

            # Log successful webhook receipt
            context.log_info(f"Webhook received: {method} from {source_ip}")

            # Build output data excluding sensitive headers
            sensitive_header_prefixes = ("x-signature", "authorization")
            filtered_headers = {
                k: v
                for k, v in headers.items()
                if not k.lower().startswith(sensitive_header_prefixes)
            }

            output_data = {
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "trigger_type": "webhook",
                "method": method,
                "source_ip": source_ip,
                "query_params": query_params,
                "body": body,
                "headers": filtered_headers,
            }

            execution_time = (time.perf_counter() - start_time) * 1000

            return NodeResult.success_result(
                outputs={
                    "out": output_data,
                    "body": body,
                    "headers": filtered_headers,
                },
                execution_time_ms=execution_time,
            )

        except Exception as e:
            error_msg = f"Webhook trigger execution failed: {str(e)}"
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )
