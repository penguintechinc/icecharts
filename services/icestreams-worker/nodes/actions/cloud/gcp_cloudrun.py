"""
GCP Cloud Run service action node.

This node invokes GCP Cloud Run services using OIDC authentication with
ID tokens. Supports HTTP-based invocations with proper authentication
headers and regional endpoint support.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import aiohttp

from ...base import NodeContext, NodeInput, NodeOutput, NodeResult
from ...auth.oidc import OIDCClient, OIDCConfig
from .base_cloud import BaseCloudFunction
from ....executor.node_registry import register_node


@register_node(
    node_type="gcp_cloudrun",
    category="cloud",
    display_name="GCP Cloud Run",
    description="Invoke GCP Cloud Run service with HTTP request",
)
class GcpCloudRunAction(BaseCloudFunction):
    """
    GCP Cloud Run service invocation node.

    Invokes Cloud Run services using OIDC authentication. Cloud Run services
    are HTTP-based, so this node sends authenticated HTTP requests with
    ID tokens in the Authorization header.
    """

    node_type = "gcp_cloudrun"
    name = "GCP Cloud Run"
    description = "Invoke GCP Cloud Run service"
    category = "cloud"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports."""
        return [
            NodeInput(
                name="payload",
                description="Request body to send to Cloud Run service",
                required=False,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports."""
        return [
            NodeOutput(
                name="result",
                description="Cloud Run service response",
                data_type="object",
            ),
            NodeOutput(
                name="error",
                description="Error output if invocation fails",
                data_type="string",
            ),
        ]

    async def _authenticate(self, context: NodeContext) -> OIDCClient:
        """
        Authenticate with GCP using OIDC.

        Args:
            context: Node execution context.

        Returns:
            Configured OIDCClient.

        Raises:
            ValueError: If required credentials are missing.
        """
        # Get service account configuration
        service_account_json = context.get_config_value("service_account_json")
        service_url = context.get_config_value("service_url")

        if not service_account_json:
            raise ValueError("GCP Cloud Run requires 'service_account_json'")
        if not service_url:
            raise ValueError("GCP Cloud Run requires 'service_url'")

        # Handle service account as file path or JSON string
        if isinstance(service_account_json, str):
            # Check if it's a file path or JSON string
            if service_account_json.startswith("{"):
                # JSON string - use create_from_json_string
                return OIDCClient.create_from_json_string(
                    json_string=service_account_json,
                    target_audience=service_url,
                )
            else:
                # File path
                oidc_config = OIDCConfig(
                    service_account_json=service_account_json,
                    target_audience=service_url,
                )
                return OIDCClient(oidc_config)
        elif isinstance(service_account_json, dict):
            # Dictionary - convert to JSON string
            json_string = json.dumps(service_account_json)
            return OIDCClient.create_from_json_string(
                json_string=json_string,
                target_audience=service_url,
            )
        else:
            raise ValueError(
                "service_account_json must be a file path, JSON string, or dictionary"
            )

    async def _invoke_function(
        self,
        context: NodeContext,
        auth_client: OIDCClient,
        function_config: Dict[str, Any],
        payload: Any,
    ) -> Dict[str, Any]:
        """
        Invoke GCP Cloud Run service.

        Args:
            context: Node execution context.
            auth_client: Authenticated OIDC client.
            function_config: Cloud Run service configuration.
            payload: Request body payload.

        Returns:
            Cloud Run service response.

        Raises:
            Exception: If invocation fails.
        """
        # Extract configuration
        service_url = function_config.get("service_url")
        http_method = function_config.get("http_method", "POST").upper()
        path = function_config.get("path", "")
        headers = function_config.get("headers", {})
        query_params = function_config.get("query_params", {})

        if not service_url:
            raise ValueError("Cloud Run 'service_url' is required")

        # Validate HTTP method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if http_method not in valid_methods:
            raise ValueError(
                f"Invalid http_method '{http_method}'. "
                f"Must be one of: {', '.join(valid_methods)}"
            )

        # Build full URL
        service_url = service_url.rstrip("/")
        if path:
            path = path.lstrip("/")
            full_url = f"{service_url}/{path}"
        else:
            full_url = service_url

        context.log_info(f"Invoking Cloud Run service: {http_method} {full_url}")

        # Get ID token
        id_token = auth_client.get_id_token(target_audience=service_url)

        # Prepare headers
        request_headers = {
            "Authorization": f"Bearer {id_token}",
            **headers,
        }

        # Prepare request body
        request_body = None
        if payload is not None:
            if http_method in ["POST", "PUT", "PATCH"]:
                if isinstance(payload, (dict, list)):
                    request_headers["Content-Type"] = "application/json"
                    request_body = json.dumps(payload)
                elif isinstance(payload, str):
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "text/plain"
                    request_body = payload
                elif isinstance(payload, bytes):
                    if "Content-Type" not in request_headers:
                        request_headers["Content-Type"] = "application/octet-stream"
                    request_body = payload
                else:
                    request_headers["Content-Type"] = "application/json"
                    request_body = json.dumps(str(payload))

        # Make HTTP request
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=http_method,
                url=full_url,
                headers=request_headers,
                params=query_params,
                data=request_body,
                timeout=aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT),
            ) as response:
                # Read response
                response_text = await response.text()
                status_code = response.status

                # Try to parse JSON response
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = response_text

                # Build result
                result = {
                    "status_code": status_code,
                    "headers": dict(response.headers),
                    "body": response_data,
                }

                # Check for HTTP errors
                if status_code >= 400:
                    error_msg = f"Cloud Run request failed with status {status_code}"
                    if isinstance(response_data, dict):
                        error_detail = response_data.get("error") or response_data.get(
                            "message"
                        )
                        if error_detail:
                            error_msg += f": {error_detail}"
                    elif isinstance(response_data, str):
                        error_msg += f": {response_data}"

                    raise RuntimeError(error_msg)

                context.log_info(
                    f"Cloud Run service responded with status {status_code}"
                )

                return result

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute GCP Cloud Run service invocation.

        Args:
            context: Node execution context.
            inputs: Input data containing optional payload.

        Returns:
            NodeResult with service response or error.
        """
        import time

        start_time = time.time()

        try:
            # Validate inputs
            errors = self._validate_inputs(inputs)
            if errors:
                return NodeResult.failure_result(
                    error=f"Input validation failed: {', '.join(errors)}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Get payload (optional)
            payload = self._get_input_value(inputs, "payload")

            # Extract configuration
            required_keys = ["service_url"]
            optional_keys = {
                "http_method": "POST",
                "path": "",
                "headers": {},
                "query_params": {},
                "max_retries": self.DEFAULT_MAX_RETRIES,
                "retry_delay": self.DEFAULT_RETRY_DELAY,
            }

            function_config = self._extract_config_values(
                context, required_keys, optional_keys
            )

            # Authenticate
            context.log_debug("Authenticating with GCP OIDC...")
            auth_client = await self._authenticate(context)
            self._auth_client = auth_client

            # Invoke service with retry
            context.log_debug(
                f"Invoking Cloud Run service: {function_config['service_url']}"
            )

            async def invoke_operation():
                return await self._invoke_function(
                    context, auth_client, function_config, payload
                )

            response = await self._retry_operation(
                invoke_operation,
                function_config["max_retries"],
                function_config["retry_delay"],
                context,
            )

            # Standardize response
            standardized = self._standardize_response(response, success=True)

            execution_time_ms = (time.time() - start_time) * 1000
            context.log_info(
                f"Cloud Run invocation completed in {execution_time_ms:.2f}ms"
            )

            return NodeResult.success_result(
                outputs={"result": standardized},
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"GCP Cloud Run invocation failed: {str(e)}"
            context.log_error(error_msg)

            return NodeResult(
                success=False,
                outputs={"error": error_msg},
                error=error_msg,
                execution_time_ms=execution_time_ms,
            )
