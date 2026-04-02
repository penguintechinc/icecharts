"""
Webhook Out Action Node for IceStreams Workflow System.

Sends webhooks to configured URLs with support for multiple authentication methods
(Bearer token, Basic auth, API Key) and configurable retry logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from ...executor.node_registry import register_node
from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class AuthConfig:
    """Authentication configuration for webhooks."""

    auth_type: str = "none"  # none, bearer, basic, apikey
    bearer_token: Optional[str] = None
    basic_username: Optional[str] = None
    basic_password: Optional[str] = None
    api_key_header: Optional[str] = None
    api_key_value: Optional[str] = None

    def build_headers(self) -> Dict[str, str]:
        """Build authentication headers based on auth type."""
        headers = {}

        if self.auth_type == "bearer" and self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        elif self.auth_type == "basic" and self.basic_username and self.basic_password:
            credentials = base64.b64encode(
                f"{self.basic_username}:{self.basic_password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"

        elif self.auth_type == "apikey" and self.api_key_header and self.api_key_value:
            headers[self.api_key_header] = self.api_key_value

        return headers


@register_node("action_webhook_out", "actions", "Webhook Out")
class WebhookOutAction(BaseNode):
    """Send webhooks to configured URLs with authentication and retry logic."""

    node_type = "action_webhook_out"
    name = "Webhook Out"
    description = (
        "Send webhooks with authentication and exponential backoff retry logic"
    )
    category = "actions"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the webhook out node."""
        return [
            NodeInput(
                name="url",
                description="Webhook URL to send to",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="payload",
                description="Payload data to send in webhook",
                required=True,
                data_type="any",
            ),
            NodeInput(
                name="headers",
                description="Custom HTTP headers (overrides auth headers)",
                required=False,
                data_type="object",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the webhook out node."""
        return [
            NodeOutput(
                name="success",
                description="Whether webhook was sent successfully",
                data_type="bool",
            ),
            NodeOutput(
                name="status",
                description="HTTP status code from webhook endpoint",
                data_type="number",
            ),
            NodeOutput(
                name="message",
                description="Status message or error description",
                data_type="string",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate webhook configuration."""
        errors = []

        auth_type = config.get("authType", "none")
        valid_auth_types = {"none", "bearer", "basic", "apikey"}
        if auth_type not in valid_auth_types:
            errors.append(f"Invalid authType: {auth_type}")

        if auth_type == "bearer" and not config.get("bearerToken"):
            errors.append("bearerToken required for bearer authentication")

        if auth_type == "basic":
            if not config.get("basicUsername") or not config.get("basicPassword"):
                errors.append("basicUsername and basicPassword required for basic auth")

        if auth_type == "apikey":
            if not config.get("apiKeyHeader") or not config.get("apiKeyValue"):
                errors.append("apiKeyHeader and apiKeyValue required for API key auth")

        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout must be a positive number")

        max_retries = config.get("maxRetries", 3)
        if not isinstance(max_retries, int) or max_retries < 0:
            errors.append("maxRetries must be a non-negative integer")

        return errors

    def _build_auth_config(self, context: NodeContext) -> AuthConfig:
        """Build authentication configuration from context."""
        auth_type = context.get_config_value("authType", "none")

        return AuthConfig(
            auth_type=auth_type,
            bearer_token=context.get_config_value("bearerToken"),
            basic_username=context.get_config_value("basicUsername"),
            basic_password=context.get_config_value("basicPassword"),
            api_key_header=context.get_config_value("apiKeyHeader"),
            api_key_value=context.get_config_value("apiKeyValue"),
        )

    async def _send_webhook(
        self,
        context: NodeContext,
        url: str,
        payload: Any,
        custom_headers: Optional[Dict[str, str]],
        timeout: float,
        max_retries: int,
    ) -> tuple[bool, int, str]:
        """Send webhook with retry logic."""
        auth_config = self._build_auth_config(context)
        auth_headers = auth_config.build_headers()

        headers = {"Content-Type": "application/json"}
        headers.update(auth_headers)
        if custom_headers:
            headers.update(custom_headers)

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(max_retries + 1):
                try:
                    if isinstance(payload, (dict, list)):
                        body = json.dumps(payload)
                    else:
                        body = str(payload)

                    response = await client.post(url, content=body, headers=headers)

                    if response.status_code < 500:
                        success = 200 <= response.status_code < 300
                        message = f"HTTP {response.status_code}"
                        return success, response.status_code, message

                    if attempt < max_retries:
                        wait_time = (2**attempt) * 1.0
                        context.log_warning(
                            f"Webhook send failed with {response.status_code}, "
                            f"retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        return (
                            False,
                            response.status_code,
                            f"HTTP {response.status_code}",
                        )

                except (asyncio.TimeoutError, httpx.TimeoutException) as e:
                    if attempt < max_retries:
                        wait_time = (2**attempt) * 1.0
                        context.log_warning(
                            f"Webhook send timeout, retrying in {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        return False, 0, f"Timeout: {e}"

                except (httpx.ConnectError, httpx.NetworkError) as e:
                    if attempt < max_retries:
                        wait_time = (2**attempt) * 1.0
                        context.log_warning(
                            f"Webhook connect error, retrying in {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        return False, 0, f"Connection error: {e}"

        return False, 0, "Failed after retries"

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute webhook send."""
        start_time = time.perf_counter()

        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        url = inputs.get("url", "")
        if not url:
            return NodeResult.failure_result(
                error="Webhook URL is required",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        payload = inputs.get("payload", {})
        custom_headers = inputs.get("headers")

        timeout = float(context.get_config_value("timeout", 30))
        max_retries = int(context.get_config_value("maxRetries", 3))

        try:
            context.log_info(f"Sending webhook to {url}")
            success, status, message = await self._send_webhook(
                context, url, payload, custom_headers, timeout, max_retries
            )

            if success:
                context.log_info(f"Webhook sent successfully: {message}")

            return NodeResult.success_result(
                outputs={
                    "success": success,
                    "status": status,
                    "message": message,
                },
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"Webhook send failed: {e}")
            return NodeResult.failure_result(
                error=f"Webhook send failed: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
