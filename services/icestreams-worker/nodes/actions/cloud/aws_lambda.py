"""
AWS Lambda cloud function action node.

This node invokes AWS Lambda functions using AWS STS credentials from the OAuth2
authentication client. Supports both synchronous and asynchronous invocations with
comprehensive error handling and response parsing.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

from ...base import NodeContext, NodeInput, NodeOutput, NodeResult
from ...auth.oauth2 import AWSSTSClient, AWSSTSConfig
from .base_cloud import BaseCloudFunction
from ....executor.node_registry import register_node


@register_node(
    node_type="aws_lambda",
    category="cloud",
    display_name="AWS Lambda",
    description="Invoke AWS Lambda function with payload"
)
class AwsLambdaAction(BaseCloudFunction):
    """
    AWS Lambda function invocation node.

    Invokes AWS Lambda functions using STS credentials. Supports both
    synchronous (RequestResponse) and asynchronous (Event) invocations,
    with automatic retries and comprehensive error handling.
    """

    node_type = "aws_lambda"
    name = "AWS Lambda"
    description = "Invoke AWS Lambda function"
    category = "cloud"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports."""
        return [
            NodeInput(
                name="payload",
                description="Payload to send to Lambda function",
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
                description="Lambda function response",
                data_type="object",
            ),
            NodeOutput(
                name="error",
                description="Error output if invocation fails",
                data_type="string",
            ),
        ]

    async def _authenticate(self, context: NodeContext) -> AWSSTSClient:
        """
        Authenticate with AWS using STS credentials.

        Args:
            context: Node execution context containing AWS credentials.

        Returns:
            Configured AWSSTSClient.

        Raises:
            ValueError: If required credentials are missing.
        """
        required_keys = ["aws_access_key_id", "aws_secret_access_key", "aws_region"]
        optional_keys = {
            "aws_session_token": None,
            "role_arn": None,
            "session_duration": 3600,
        }

        config_values = self._extract_config_values(
            context, required_keys, optional_keys
        )

        sts_config = AWSSTSConfig(
            access_key_id=config_values["aws_access_key_id"],
            secret_access_key=config_values["aws_secret_access_key"],
            region=config_values["aws_region"],
            session_token=config_values.get("aws_session_token"),
            role_arn=config_values.get("role_arn"),
            session_duration=config_values.get("session_duration", 3600),
        )

        return AWSSTSClient(sts_config)

    async def _invoke_function(
        self,
        context: NodeContext,
        auth_client: AWSSTSClient,
        function_config: Dict[str, Any],
        payload: Any,
    ) -> Dict[str, Any]:
        """
        Invoke AWS Lambda function.

        Args:
            context: Node execution context.
            auth_client: Authenticated AWS STS client.
            function_config: Lambda function configuration.
            payload: Payload to send to function.

        Returns:
            Lambda function response.

        Raises:
            Exception: If invocation fails.
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as e:
            raise RuntimeError(
                "boto3 is required for AWS Lambda invocation. "
                "Install with: pip install boto3"
            ) from e

        # Get AWS credentials
        credentials = auth_client.get_credentials()

        # Extract function configuration
        function_name = function_config.get("function_name")
        invocation_type = function_config.get("invocation_type", "RequestResponse")
        qualifier = function_config.get("qualifier")

        if not function_name:
            raise ValueError("Lambda function_name is required")

        # Validate invocation type
        valid_types = ["RequestResponse", "Event", "DryRun"]
        if invocation_type not in valid_types:
            raise ValueError(
                f"Invalid invocation_type '{invocation_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        # Create Lambda client
        lambda_client = boto3.client(
            "lambda",
            aws_access_key_id=credentials["access_key_id"],
            aws_secret_access_key=credentials["secret_access_key"],
            aws_session_token=credentials.get("session_token"),
            region_name=function_config.get("aws_region", context.get_config_value("aws_region")),
        )

        # Serialize payload
        if isinstance(payload, (dict, list)):
            payload_bytes = json.dumps(payload).encode("utf-8")
        elif isinstance(payload, str):
            payload_bytes = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            payload_bytes = payload
        else:
            payload_bytes = json.dumps(str(payload)).encode("utf-8")

        context.log_info(
            f"Invoking Lambda function '{function_name}' "
            f"(type: {invocation_type}, size: {len(payload_bytes)} bytes)"
        )

        # Prepare invocation parameters
        invoke_params = {
            "FunctionName": function_name,
            "InvocationType": invocation_type,
            "Payload": payload_bytes,
        }

        if qualifier:
            invoke_params["Qualifier"] = qualifier

        # Invoke Lambda function in thread pool (boto3 is synchronous)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: lambda_client.invoke(**invoke_params)
        )

        # Parse response
        status_code = response.get("StatusCode", 0)
        function_error = response.get("FunctionError")

        result = {
            "status_code": status_code,
            "request_id": response.get("RequestId"),
            "log_result": response.get("LogResult"),
            "executed_version": response.get("ExecutedVersion"),
        }

        # Parse payload for synchronous invocations
        if invocation_type == "RequestResponse":
            payload_response = response.get("Payload")
            if payload_response:
                payload_data = payload_response.read()
                try:
                    result["payload"] = json.loads(payload_data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result["payload"] = payload_data.decode("utf-8", errors="replace")

        # Check for function errors
        if function_error:
            error_msg = f"Lambda function error: {function_error}"
            if "payload" in result:
                error_msg += f" - {result['payload']}"
            raise RuntimeError(error_msg)

        # Check for invocation errors
        if status_code not in (200, 202, 204):
            raise RuntimeError(
                f"Lambda invocation failed with status code {status_code}"
            )

        context.log_info(
            f"Lambda function '{function_name}' invoked successfully "
            f"(status: {status_code}, request_id: {result['request_id']})"
        )

        return result

    async def execute(
        self,
        context: NodeContext,
        inputs: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute AWS Lambda invocation.

        Args:
            context: Node execution context.
            inputs: Input data containing payload.

        Returns:
            NodeResult with Lambda response or error.
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
            required_keys = ["function_name"]
            optional_keys = {
                "invocation_type": "RequestResponse",
                "qualifier": None,
                "max_retries": self.DEFAULT_MAX_RETRIES,
                "retry_delay": self.DEFAULT_RETRY_DELAY,
            }

            function_config = self._extract_config_values(
                context, required_keys, optional_keys
            )

            # Authenticate
            context.log_debug("Authenticating with AWS STS...")
            auth_client = await self._authenticate(context)
            self._auth_client = auth_client

            # Invoke Lambda with retry
            context.log_debug(f"Invoking Lambda function: {function_config['function_name']}")

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
            context.log_info(f"Lambda invocation completed in {execution_time_ms:.2f}ms")

            return NodeResult.success_result(
                outputs={"result": standardized},
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"AWS Lambda invocation failed: {str(e)}"
            context.log_error(error_msg)

            return NodeResult(
                success=False,
                outputs={"error": error_msg},
                error=error_msg,
                execution_time_ms=execution_time_ms,
            )
