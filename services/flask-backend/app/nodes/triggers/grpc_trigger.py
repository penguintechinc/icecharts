"""gRPC trigger node for IceCharts workflows.

Trigger workflow execution from gRPC service calls. Fires when a gRPC method
is called, receiving method name, metadata, and request payload.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


class GrpcTrigger(BaseTrigger):
    """
    Trigger that fires when a gRPC call is received.

    Monitors incoming gRPC method calls and triggers workflow execution.
    Supports method filtering and optional authentication validation.
    Parses full method path to extract service and method names.

    Configuration:
        allowedMethods: List of allowed gRPC method paths (e.g., ["/service/Method"]).
                       Empty list allows all methods.
        requireAuth: Whether to require authentication headers (default: False).
        authHeader: Name of the authentication header to check (default: "authorization").
    """

    node_type = "trigger_grpc"
    name = "gRPC"
    description = "Trigger from incoming gRPC calls"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """gRPC triggers have no inputs."""
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for gRPC request data and metadata."""
        return [
            NodeOutput(
                name="out",
                description="gRPC call data with method and payload",
                data_type="object",
            ),
            NodeOutput(
                name="request", description="Raw gRPC request payload", data_type="any"
            ),
            NodeOutput(
                name="metadata", description="gRPC call metadata", data_type="object"
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate gRPC trigger configuration.

        Ensures allowed methods are properly formatted and auth settings are valid.

        Args:
            config: Node configuration to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate allowed methods if specified
        allowed_methods = config.get("allowedMethods", [])
        for method in allowed_methods:
            if not isinstance(method, str) or not method:
                errors.append(f"Invalid gRPC method name: {method}")
            elif not method.startswith("/"):
                errors.append(f"gRPC method should start with '/': {method}")

        # Validate auth requirement if set
        require_auth = config.get("requireAuth", False)
        if require_auth:
            auth_header = config.get("authHeader", "authorization")
            if not auth_header:
                errors.append("authHeader required when requireAuth is true")

        return errors

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """
        Execute the gRPC trigger.

        Extracts gRPC call information from trigger_data, validates method and
        authentication, and returns trigger output with parsed method information.

        Args:
            context: Execution context with config and logging.
            trigger_data: Trigger activation data containing gRPC call info.

        Returns:
            NodeResult with gRPC call data and metadata outputs.
        """
        start_time = time.perf_counter()

        try:
            # Extract gRPC data from trigger data
            trigger_data_obj = context.config.get("_trigger_data", {})

            method = trigger_data_obj.get("method", "/unknown/Unknown")
            metadata = trigger_data_obj.get("metadata", {})
            request_payload = trigger_data_obj.get("request", {})
            peer = trigger_data_obj.get("peer", "unknown")

            # Check allowed methods
            allowed_methods = context.config.get("allowedMethods", [])
            if allowed_methods and method not in allowed_methods:
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=f"Method {method} not allowed. Allowed: {allowed_methods}",
                    execution_time_ms=execution_time,
                )

            # Check authentication if required
            require_auth = context.config.get("requireAuth", False)
            if require_auth:
                auth_header = context.config.get("authHeader", "authorization")
                # Check for header case-insensitively
                has_auth = any(
                    k.lower() == auth_header.lower() for k in metadata.keys()
                )
                if not has_auth:
                    execution_time = (time.perf_counter() - start_time) * 1000
                    return NodeResult.failure_result(
                        error=f"Authentication required but {auth_header} not found in metadata",
                        execution_time_ms=execution_time,
                    )

            # Log the trigger firing
            context.log_info(f"gRPC trigger fired: {method} from {peer}")

            # Parse service and method name from full method path
            parts = method.strip("/").split("/")
            service_name = parts[0] if parts else "unknown"
            method_name = parts[1] if len(parts) > 1 else "unknown"

            # Build output data with sensitive metadata filtered
            output_data = {
                "triggered_at": datetime.now(timezone.utc).isoformat(),
                "trigger_type": "grpc",
                "full_method": method,
                "service": service_name,
                "method": method_name,
                "peer": peer,
                "request": request_payload,
                "metadata": {
                    k: v
                    for k, v in metadata.items()
                    if not k.lower().startswith("authorization")
                },
            }

            execution_time = (time.perf_counter() - start_time) * 1000

            return NodeResult.success_result(
                outputs={
                    "out": output_data,
                    "request": request_payload,
                    "metadata": metadata,
                },
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            error_msg = f"gRPC trigger execution failed: {str(e)}"
            context.log_error(error_msg)
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )
