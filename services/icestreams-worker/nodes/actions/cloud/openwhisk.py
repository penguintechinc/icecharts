"""
Apache OpenWhisk cloud function action node.

This node invokes Apache OpenWhisk actions using OAuth2 authentication.
Supports both blocking and non-blocking invocations with result polling
for asynchronous executions.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

import aiohttp

from ...base import NodeContext, NodeInput, NodeOutput, NodeResult
from ...auth.oauth2 import OAuth2Client, OAuth2Config
from .base_cloud import BaseCloudFunction
from ....executor.node_registry import register_node


@register_node(
    node_type="openwhisk_action",
    category="cloud",
    display_name="OpenWhisk Action",
    description="Invoke Apache OpenWhisk action with payload"
)
class OpenWhiskAction(BaseCloudFunction):
    """
    Apache OpenWhisk action invocation node.

    Invokes OpenWhisk actions using OAuth2 or basic authentication.
    Supports both blocking and non-blocking invocations with automatic
    result polling for async executions.
    """

    node_type = "openwhisk_action"
    name = "OpenWhisk Action"
    description = "Invoke Apache OpenWhisk action"
    category = "cloud"

    # OpenWhisk-specific configuration
    DEFAULT_POLL_INTERVAL = 1.0  # seconds
    DEFAULT_POLL_TIMEOUT = 60.0  # seconds

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports."""
        return [
            NodeInput(
                name="payload",
                description="Payload to send to OpenWhisk action",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports."""
        return [
            NodeOutput(
                name="result",
                description="OpenWhisk action response",
                data_type="object",
            ),
            NodeOutput(
                name="error",
                description="Error output if invocation fails",
                data_type="string",
            ),
        ]

    async def _authenticate(self, context: NodeContext) -> Optional[OAuth2Client]:
        """
        Authenticate with OpenWhisk.

        OpenWhisk supports basic auth (auth_key) or OAuth2. This method
        handles OAuth2 authentication if configured.

        Args:
            context: Node execution context.

        Returns:
            OAuth2Client if OAuth2 is configured, None for basic auth.

        Raises:
            ValueError: If required credentials are missing.
        """
        # Check for OAuth2 configuration
        client_id = context.get_config_value("oauth_client_id")
        client_secret = context.get_config_value("oauth_client_secret")
        token_url = context.get_config_value("oauth_token_url")

        if client_id and client_secret and token_url:
            oauth_config = OAuth2Config(
                client_id=client_id,
                client_secret=client_secret,
                token_url=token_url,
                scope=context.get_config_value("oauth_scope"),
            )
            return OAuth2Client(oauth_config)

        # Basic auth doesn't require an auth client
        auth_key = context.get_config_value("auth_key")
        if not auth_key:
            raise ValueError(
                "OpenWhisk requires either 'auth_key' for basic auth "
                "or OAuth2 credentials (oauth_client_id, oauth_client_secret, oauth_token_url)"
            )

        return None

    async def _invoke_function(
        self,
        context: NodeContext,
        auth_client: Optional[OAuth2Client],
        function_config: Dict[str, Any],
        payload: Any,
    ) -> Dict[str, Any]:
        """
        Invoke OpenWhisk action.

        Args:
            context: Node execution context.
            auth_client: OAuth2Client if using OAuth2, None for basic auth.
            function_config: OpenWhisk action configuration.
            payload: Payload to send to action.

        Returns:
            OpenWhisk action response.

        Raises:
            Exception: If invocation fails.
        """
        # Extract configuration
        api_host = function_config.get("api_host")
        action_name = function_config.get("action_name")
        namespace = function_config.get("namespace", "_")
        blocking = function_config.get("blocking", True)
        result_only = function_config.get("result_only", True)

        if not api_host:
            raise ValueError("OpenWhisk 'api_host' is required")
        if not action_name:
            raise ValueError("OpenWhisk 'action_name' is required")

        # Normalize API host
        api_host = api_host.rstrip("/")

        # Build invocation URL
        url = f"{api_host}/api/v1/namespaces/{namespace}/actions/{action_name}"

        # Add query parameters
        params = {}
        if blocking:
            params["blocking"] = "true"
            if result_only:
                params["result"] = "true"

        context.log_info(
            f"Invoking OpenWhisk action '{action_name}' "
            f"(namespace: {namespace}, blocking: {blocking})"
        )

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        # Add authentication
        auth_key = context.get_config_value("auth_key")
        if auth_client:
            # OAuth2 authentication
            token = auth_client.get_access_token()
            headers["Authorization"] = f"Bearer {token}"
        elif auth_key:
            # Basic authentication (UUID:KEY format)
            import base64
            encoded = base64.b64encode(auth_key.encode("utf-8")).decode("utf-8")
            headers["Authorization"] = f"Basic {encoded}"
        else:
            raise ValueError("No authentication credentials configured")

        # Serialize payload
        if isinstance(payload, (dict, list)):
            payload_json = payload
        else:
            payload_json = {"value": payload}

        # Invoke action
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload_json,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT),
            ) as response:
                response_text = await response.text()

                if response.status not in (200, 202):
                    raise RuntimeError(
                        f"OpenWhisk invocation failed with status {response.status}: "
                        f"{response_text}"
                    )

                # Parse response
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    result = {"raw_response": response_text}

                # Handle non-blocking invocations
                if not blocking and response.status == 202:
                    activation_id = result.get("activationId")
                    if activation_id:
                        context.log_debug(
                            f"Non-blocking invocation initiated (activation: {activation_id})"
                        )
                        # Poll for result
                        result = await self._poll_activation(
                            context,
                            api_host,
                            namespace,
                            activation_id,
                            headers,
                            function_config.get("poll_timeout", self.DEFAULT_POLL_TIMEOUT),
                            function_config.get("poll_interval", self.DEFAULT_POLL_INTERVAL),
                        )

                context.log_info(f"OpenWhisk action '{action_name}' completed successfully")
                return result

    async def _poll_activation(
        self,
        context: NodeContext,
        api_host: str,
        namespace: str,
        activation_id: str,
        headers: Dict[str, str],
        timeout: float,
        interval: float,
    ) -> Dict[str, Any]:
        """
        Poll for activation result.

        Args:
            context: Node execution context.
            api_host: OpenWhisk API host.
            namespace: Namespace.
            activation_id: Activation ID to poll.
            headers: HTTP headers including authentication.
            timeout: Maximum time to poll in seconds.
            interval: Polling interval in seconds.

        Returns:
            Activation result.

        Raises:
            TimeoutError: If polling times out.
            RuntimeError: If activation fails.
        """
        url = f"{api_host}/api/v1/namespaces/{namespace}/activations/{activation_id}"
        elapsed = 0.0

        context.log_debug(f"Polling activation {activation_id}...")

        async with aiohttp.ClientSession() as session:
            while elapsed < timeout:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        activation = await response.json()

                        # Check if activation is complete
                        if activation.get("end"):
                            result = activation.get("response", {}).get("result", {})
                            success = activation.get("response", {}).get("success", False)

                            if not success:
                                error = activation.get("response", {}).get("error")
                                raise RuntimeError(
                                    f"OpenWhisk activation failed: {error or 'Unknown error'}"
                                )

                            context.log_debug(f"Activation {activation_id} completed")
                            return result

                # Wait before next poll
                await asyncio.sleep(interval)
                elapsed += interval

        raise TimeoutError(
            f"Activation {activation_id} did not complete within {timeout}s"
        )

    async def execute(
        self,
        context: NodeContext,
        inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute OpenWhisk action invocation.

        Args:
            context: Node execution context.
            inputs: Input data containing payload.

        Returns:
            NodeResult with action response or error.
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

            # Get payload
            payload = self._get_input_value(inputs, "payload")

            # Extract configuration
            required_keys = ["api_host", "action_name"]
            optional_keys = {
                "namespace": "_",
                "blocking": True,
                "result_only": True,
                "poll_timeout": self.DEFAULT_POLL_TIMEOUT,
                "poll_interval": self.DEFAULT_POLL_INTERVAL,
                "max_retries": self.DEFAULT_MAX_RETRIES,
                "retry_delay": self.DEFAULT_RETRY_DELAY,
            }

            function_config = self._extract_config_values(
                context, required_keys, optional_keys
            )

            # Authenticate
            context.log_debug("Authenticating with OpenWhisk...")
            auth_client = await self._authenticate(context)
            self._auth_client = auth_client

            # Invoke action with retry
            context.log_debug(f"Invoking action: {function_config['action_name']}")

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
            context.log_info(f"OpenWhisk invocation completed in {execution_time_ms:.2f}ms")

            return NodeResult.success_result(
                outputs={"result": standardized},
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"OpenWhisk action invocation failed: {str(e)}"
            context.log_error(error_msg)

            return NodeResult(
                success=False,
                outputs={"error": error_msg},
                error=error_msg,
                execution_time_ms=execution_time_ms,
            )
