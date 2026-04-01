"""
HTTP Request Action Node for IceStreams Workflow System.

Executes async HTTP requests using httpx with support for multiple methods,
headers, query parameters, request bodies, timeouts, retries, and response parsing.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RetryConfig:
    """Retry configuration for HTTP requests."""

    max_retries: int = 3
    backoff_factor: float = 1.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


@register_node("action_http_request", "actions", "HTTP Request")
class HttpRequestAction(BaseNode):
    """Execute async HTTP requests with configurable methods, headers, and retries."""

    node_type = "action_http_request"
    name = "HTTP Request"
    description = "Execute HTTP requests with configurable methods and parameters"
    category = "actions"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the HTTP request node."""
        return [
            NodeInput(
                name="url",
                description="Request URL",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="method",
                description="HTTP method (GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS)",
                required=False,
                data_type="string",
            ),
            NodeInput(
                name="body",
                description="Request body data (for POST/PUT/PATCH)",
                required=False,
                data_type="any",
            ),
            NodeInput(
                name="headers",
                description="Custom HTTP headers as dictionary",
                required=False,
                data_type="object",
            ),
            NodeInput(
                name="params",
                description="Query parameters as dictionary",
                required=False,
                data_type="object",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the HTTP request node."""
        return [
            NodeOutput(
                name="response",
                description="HTTP response data",
                data_type="object",
            ),
            NodeOutput(
                name="status",
                description="HTTP status code",
                data_type="number",
            ),
            NodeOutput(
                name="headers",
                description="Response headers",
                data_type="object",
            ),
            NodeOutput(
                name="body",
                description="Response body",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate HTTP request configuration."""
        errors = []

        method = config.get("method", "GET").upper()
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        if method not in valid_methods:
            errors.append(f"Invalid HTTP method: {method}")

        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout must be a positive number")

        if "maxRetries" in config:
            max_retries = config.get("maxRetries", 3)
            if not isinstance(max_retries, int) or max_retries < 0:
                errors.append("maxRetries must be a non-negative integer")

        return errors

    async def _make_request(
        self,
        context: NodeContext,
        url: str,
        method: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, str]],
        body: Optional[Any],
        timeout: float,
        retry_config: RetryConfig,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(retry_config.max_retries + 1):
                try:
                    request_kwargs = {
                        "url": url,
                        "method": method,
                        "headers": headers or {},
                        "params": params or {},
                    }

                    if body is not None and method not in {"GET", "HEAD", "OPTIONS"}:
                        if isinstance(body, (dict, list)):
                            request_kwargs["json"] = body
                        else:
                            request_kwargs["content"] = str(body)

                    response = await client.request(**request_kwargs)

                    if response.status_code < 500:
                        return response

                    if attempt < retry_config.max_retries:
                        wait_time = retry_config.backoff_factor * (
                            retry_config.backoff_multiplier**attempt
                        )
                        if retry_config.jitter:
                            import random

                            wait_time *= random.uniform(0.5, 1.5)
                        context.log_warning(
                            f"HTTP request failed with {response.status_code}, "
                            f"retrying in {wait_time:.2f}s (attempt {attempt + 1}/{retry_config.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        return response

                except httpx.TimeoutException as e:
                    if attempt < retry_config.max_retries:
                        wait_time = retry_config.backoff_factor * (
                            retry_config.backoff_multiplier**attempt
                        )
                        context.log_warning(
                            f"HTTP request timeout, retrying in {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{retry_config.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise

                except (httpx.ConnectError, httpx.NetworkError) as e:
                    if attempt < retry_config.max_retries:
                        wait_time = retry_config.backoff_factor * (
                            retry_config.backoff_multiplier**attempt
                        )
                        context.log_warning(
                            f"HTTP connection error, retrying in {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{retry_config.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        raise

            raise RuntimeError("Failed to complete HTTP request after retries")

    def _parse_response_body(self, response: httpx.Response, content_type: str) -> Any:
        """Parse response body based on content type."""
        if not response.content:
            return None

        if "application/json" in content_type:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text

        if content_type.startswith("text/"):
            return response.text

        if content_type.startswith("application/"):
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text

        return response.text

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute HTTP request."""
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
                error="URL is required",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        method = inputs.get("method") or context.get_config_value("method", "GET")
        method = method.upper()
        body = inputs.get("body")
        headers = inputs.get("headers") or context.get_config_value("headers", {})
        params = inputs.get("params") or context.get_config_value("params", {})

        timeout = float(context.get_config_value("timeout", 30))
        max_retries = int(context.get_config_value("maxRetries", 3))

        retry_config = RetryConfig(
            max_retries=max_retries,
            backoff_factor=float(context.get_config_value("backoffFactor", 1.0)),
            backoff_multiplier=float(
                context.get_config_value("backoffMultiplier", 2.0)
            ),
            jitter=context.get_config_value("jitter", True),
        )

        try:
            context.log_info(f"HTTP {method} request to {url}")
            response = await self._make_request(
                context, url, method, headers, params, body, timeout, retry_config
            )

            content_type = response.headers.get("content-type", "text/plain")
            response_body = self._parse_response_body(response, content_type)

            context.log_info(f"HTTP response: {response.status_code}")

            return NodeResult.success_result(
                outputs={
                    "response": {
                        "status": response.status_code,
                        "headers": dict(response.headers),
                        "body": response_body,
                    },
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                },
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except asyncio.TimeoutError as e:
            context.log_error(f"HTTP request timeout: {e}")
            return NodeResult.failure_result(
                error=f"HTTP request timeout: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except httpx.NetworkError as e:
            context.log_error(f"HTTP network error: {e}")
            return NodeResult.failure_result(
                error=f"HTTP network error: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            context.log_error(f"HTTP request failed: {e}")
            return NodeResult.failure_result(
                error=f"HTTP request failed: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
