"""
MCP Server Trigger Node - Executes workflow from MCP tool calls.

This trigger node fires when an MCP (Model Context Protocol) tool call is received.
It validates the tool call against configured constraints, validates arguments against
an optional JSON schema, and outputs the tool call data and context to downstream nodes.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..base import BaseTrigger, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


class McpServerTrigger(BaseTrigger):
    """Trigger that fires when an MCP tool call is received.

    This node integrates with MCP (Model Context Protocol) servers and fires when
    an AI agent makes a tool call. It supports tool filtering, argument validation
    against optional JSON schemas, and includes request tracking for audit and
    debugging purposes.

    Configuration:
        toolName (str, optional): Expected MCP tool name. If provided, trigger
                                 only fires when this specific tool is called.
        allowedTools (list, optional): List of tool names to accept. If provided,
                                      trigger only fires for tools in this list.
        argumentSchema (dict, optional): JSON schema for validating tool arguments.
                                        Supports basic type checking and required
                                        field validation.

    Example Configuration:
        {
            "toolName": "send_email",
            "allowedTools": ["send_email", "schedule_email"],
            "argumentSchema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    """

    node_type = "trigger_mcp"
    name = "MCP Server"
    description = "Trigger from MCP (Model Context Protocol) tool calls"
    category = "triggers"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """MCP triggers have no inputs - they are entry points."""
        return []

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for MCP tool call data.

        Returns:
            List of output ports: out (complete tool call data), arguments (tool arguments),
            and context (MCP context and metadata).
        """
        return [
            NodeOutput(
                name="out",
                description="MCP tool call data including tool name, arguments, and context",
                data_type="object",
            ),
            NodeOutput(
                name="arguments",
                description="Tool call arguments extracted from the request",
                data_type="object",
            ),
            NodeOutput(
                name="context",
                description="MCP context and metadata including request ID and timestamps",
                data_type="object",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate MCP server trigger configuration.

        Validates:
        - toolName is a string if provided
        - allowedTools contains only valid string tool names
        - argumentSchema is a valid JSON schema if provided

        Args:
            config: Configuration dictionary.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        # Validate toolName if specified
        tool_name = config.get("toolName")
        if tool_name is not None:
            if not isinstance(tool_name, str):
                errors.append("toolName must be a string")
            elif not tool_name.strip():
                errors.append("toolName cannot be an empty string")

        # Validate allowedTools if specified
        allowed_tools = config.get("allowedTools", [])
        if not isinstance(allowed_tools, list):
            errors.append("allowedTools must be a list")
        else:
            for idx, tool in enumerate(allowed_tools):
                if not isinstance(tool, str):
                    errors.append(
                        f"Tool at index {idx} in allowedTools must be a string"
                    )
                elif not tool.strip():
                    errors.append(
                        f"Tool at index {idx} in allowedTools cannot be empty"
                    )

        # Validate argumentSchema if provided
        argument_schema = config.get("argumentSchema")
        if argument_schema is not None:
            if not isinstance(argument_schema, dict):
                errors.append("argumentSchema must be a JSON object (dictionary)")
            else:
                # Basic schema validation
                if "type" not in argument_schema:
                    errors.append("argumentSchema should have a 'type' field")
                elif argument_schema.get("type") != "object":
                    errors.append("argumentSchema type should be 'object'")

        return errors

    def _validate_arguments(
        self, arguments: Dict[str, Any], schema: Dict[str, Any]
    ) -> List[str]:
        """Validate tool arguments against a JSON schema.

        Performs basic schema validation including:
        - Checking required fields are present
        - Validating argument types match schema specifications

        Args:
            arguments: Tool arguments to validate.
            schema: JSON schema for validation.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: List[str] = []

        if not schema:
            return errors

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                errors.append(f"Missing required argument: {field}")

        # Check property types
        properties = schema.get("properties", {})
        for key, value in arguments.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type:
                    actual_type = type(value).__name__
                    type_mapping = {
                        "string": "str",
                        "number": ("int", "float"),
                        "integer": "int",
                        "boolean": "bool",
                        "array": "list",
                        "object": "dict",
                    }
                    expected = type_mapping.get(expected_type, expected_type)
                    if isinstance(expected, tuple):
                        if actual_type not in expected:
                            errors.append(
                                f"Argument '{key}' should be {expected_type}, "
                                f"got {actual_type}"
                            )
                    elif actual_type != expected:
                        errors.append(
                            f"Argument '{key}' should be {expected_type}, "
                            f"got {actual_type}"
                        )

        return errors

    async def fire(
        self, context: NodeContext, trigger_data: Dict[str, Any]
    ) -> NodeResult:
        """Execute the MCP server trigger.

        Validates the MCP tool call against configured constraints, validates
        arguments against an optional JSON schema, and produces output containing
        the tool call data, arguments, and context.

        Args:
            context: Execution context containing configuration and logger.
            trigger_data: MCP tool call data from the request.

        Returns:
            NodeResult with success status and tool call data in outputs,
            or failure status with error message on validation failure.
        """
        start_time = time.perf_counter()

        # Extract trigger data
        tool_name = trigger_data.get("tool_name", "unknown")
        arguments = trigger_data.get("arguments", {})
        mcp_context = trigger_data.get("context", {})
        request_id = trigger_data.get("request_id", "")

        # Check allowed tools constraint
        allowed_tools = context.config.get("allowedTools", [])
        if allowed_tools and tool_name not in allowed_tools:
            error_msg = (
                f"Tool '{tool_name}' not allowed. "
                f"Allowed tools: {', '.join(allowed_tools)}"
            )
            context.log_error(error_msg)
            execution_time = (time.perf_counter() - start_time) * 1000
            return NodeResult.failure_result(
                error=error_msg, execution_time_ms=execution_time
            )

        # Validate arguments against schema if provided
        argument_schema = context.config.get("argumentSchema")
        if argument_schema:
            validation_errors = self._validate_arguments(arguments, argument_schema)
            if validation_errors:
                error_msg = (
                    f"Argument validation failed: {'; '.join(validation_errors)}"
                )
                context.log_error(error_msg)
                execution_time = (time.perf_counter() - start_time) * 1000
                return NodeResult.failure_result(
                    error=error_msg, execution_time_ms=execution_time
                )

        context.log_info(
            f"MCP trigger fired: tool={tool_name}, request_id={request_id}"
        )

        # Build output data
        output_data = {
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "trigger_type": "mcp",
            "tool_name": tool_name,
            "request_id": request_id,
            "arguments": arguments,
            "context": mcp_context,
        }

        execution_time = (time.perf_counter() - start_time) * 1000

        return NodeResult.success_result(
            outputs={
                "out": output_data,
                "arguments": arguments,
                "context": mcp_context,
            },
            execution_time_ms=execution_time,
        )
