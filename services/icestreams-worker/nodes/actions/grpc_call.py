"""
gRPC Call Action Node for IceStreams Workflow System.

Calls remote gRPC services with support for dynamic service/method invocation,
request/response message handling, TLS/mTLS support, and timeout configuration.
"""

from __future__ import annotations

import json
import logging
import ssl
import time
from typing import Any, Dict, List, Optional

import grpc
from grpc import aio

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


@register_node("action_grpc_call", "actions", "gRPC Call")
class GrpcCallAction(BaseNode):
    """Call remote gRPC services with dynamic method invocation."""

    node_type = "action_grpc_call"
    name = "gRPC Call"
    description = "Call remote gRPC services with TLS/mTLS support"
    category = "actions"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the gRPC call node."""
        return [
            NodeInput(
                name="service",
                description="Target service address (e.g., localhost:50051)",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="method",
                description="gRPC method path (e.g., /package.Service/Method)",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="request",
                description="Request message data as dictionary",
                required=True,
                data_type="object",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the gRPC call node."""
        return [
            NodeOutput(
                name="response",
                description="Response message data",
                data_type="object",
            ),
            NodeOutput(
                name="code",
                description="gRPC status code",
                data_type="string",
            ),
            NodeOutput(
                name="message",
                description="gRPC status message",
                data_type="string",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate gRPC call configuration."""
        errors = []

        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout must be a positive number")

        tls_mode = config.get("tlsMode", "insecure")
        valid_modes = {"insecure", "tls", "mtls"}
        if tls_mode not in valid_modes:
            errors.append(f"Invalid tlsMode: {tls_mode}")

        if tls_mode in {"tls", "mtls"}:
            if tls_mode == "tls" and not config.get("caPath"):
                errors.append("caPath required for TLS mode")
            if tls_mode == "mtls":
                if not config.get("caPath") or not config.get("certPath") or not config.get("keyPath"):
                    errors.append("caPath, certPath, and keyPath required for mTLS mode")

        return errors

    async def _get_channel(
        self, context: NodeContext, service: str
    ) -> aio.Channel:
        """Create gRPC channel with appropriate credentials."""
        tls_mode = context.get_config_value("tlsMode", "insecure")

        if tls_mode == "insecure":
            return aio.insecure_channel(service)

        elif tls_mode == "tls":
            ca_path = context.get_config_value("caPath")
            with open(ca_path, "rb") as f:
                ca_cert = f.read()

            credentials = grpc.ssl_channel_credentials(root_certificates=ca_cert)
            return aio.secure_channel(service, credentials)

        elif tls_mode == "mtls":
            ca_path = context.get_config_value("caPath")
            cert_path = context.get_config_value("certPath")
            key_path = context.get_config_value("keyPath")

            with open(ca_path, "rb") as f:
                ca_cert = f.read()
            with open(cert_path, "rb") as f:
                client_cert = f.read()
            with open(key_path, "rb") as f:
                client_key = f.read()

            credentials = grpc.ssl_channel_credentials(
                root_certificates=ca_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )
            return aio.secure_channel(service, credentials)

        else:
            raise ValueError(f"Invalid TLS mode: {tls_mode}")

    async def _call_grpc_method(
        self,
        context: NodeContext,
        service: str,
        method: str,
        request: Dict[str, Any],
        timeout: float,
    ) -> tuple[bool, Any, str, str]:
        """Call gRPC method and return response."""
        channel = None

        try:
            channel = await self._get_channel(context, service)

            unary_unary = grpc.aio.unary_unary(
                method, request_serializer=self._serialize_request,
                response_deserializer=self._deserialize_response
            )

            response = await unary_unary(
                channel, method, request, timeout=timeout
            )

            return True, response, "OK", ""

        except grpc.RpcError as e:
            code_name = e.code().name if e.code() else "UNKNOWN"
            return False, None, code_name, e.details() or str(e)

        except asyncio.TimeoutError:
            return False, None, "DEADLINE_EXCEEDED", "Call timeout"

        except Exception as e:
            return False, None, "UNKNOWN", str(e)

        finally:
            if channel:
                await channel.close()

    def _serialize_request(self, message: Any) -> bytes:
        """Serialize request message to bytes."""
        if isinstance(message, dict):
            return json.dumps(message).encode()
        return str(message).encode()

    def _deserialize_response(self, data: bytes) -> Any:
        """Deserialize response bytes to object."""
        try:
            return json.loads(data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return data.decode()

    async def execute(
        self, context: NodeContext, inputs: Dict[str, Any]
    ) -> NodeResult:
        """Execute gRPC call."""
        start_time = time.perf_counter()

        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        service = inputs.get("service", "")
        method = inputs.get("method", "")
        request = inputs.get("request", {})

        if not service or not method:
            return NodeResult.failure_result(
                error="service and method are required",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        timeout = float(context.get_config_value("timeout", 30))

        try:
            import asyncio

            context.log_info(f"Calling gRPC {method} on {service}")
            success, response, code, message = await self._call_grpc_method(
                context, service, method, request, timeout
            )

            if success:
                context.log_info(f"gRPC call successful: {code}")
                return NodeResult.success_result(
                    outputs={
                        "response": response,
                        "code": code,
                        "message": message,
                    },
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )
            else:
                context.log_error(f"gRPC call failed: {code} {message}")
                return NodeResult.success_result(
                    outputs={
                        "response": None,
                        "code": code,
                        "message": message,
                    },
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

        except Exception as e:
            context.log_error(f"gRPC call error: {e}")
            return NodeResult.failure_result(
                error=f"gRPC call error: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
