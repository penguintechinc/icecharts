"""
MCP Call Action Node for IceStreams Workflow System.

Invokes MCP (Model Context Protocol) server tools with parameter support,
handling responses and errors, with support for multiple MCP servers.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional

from ...executor.node_registry import register_node
from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult

logger = logging.getLogger(__name__)


@register_node("action_mcp_call", "actions", "MCP Call")
class McpCallAction(BaseNode):
    """Invoke MCP server tools with parameter support."""

    node_type = "action_mcp_call"
    name = "MCP Call"
    description = "Call MCP (Model Context Protocol) server tools"
    category = "actions"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for the MCP call node."""
        return [
            NodeInput(
                name="server",
                description="MCP server identifier or URL",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="tool",
                description="Tool name to invoke",
                required=True,
                data_type="string",
            ),
            NodeInput(
                name="parameters",
                description="Tool parameters as dictionary",
                required=False,
                data_type="object",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for the MCP call node."""
        return [
            NodeOutput(
                name="result",
                description="Tool execution result",
                data_type="any",
            ),
            NodeOutput(
                name="success",
                description="Whether tool executed successfully",
                data_type="bool",
            ),
            NodeOutput(
                name="error",
                description="Error message if execution failed",
                data_type="string",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate MCP call configuration."""
        errors = []

        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout must be a positive number")

        return errors

    async def _call_mcp_tool(
        self,
        context: NodeContext,
        server: str,
        tool: str,
        parameters: Optional[Dict[str, Any]],
        timeout: float,
    ) -> tuple[bool, Any, Optional[str]]:
        """Call MCP tool and return result."""
        try:
            import asyncio
            import subprocess

            mcp_config = context.get_config_value("mcpServers", {})

            if server not in mcp_config:
                return False, None, f"MCP server '{server}' not configured"

            server_config = mcp_config[server]

            if isinstance(server_config, dict):
                server_command = server_config.get("command")
                server_args = server_config.get("args", [])
            else:
                server_command = str(server_config)
                server_args = []

            if not server_command:
                return False, None, f"No command configured for MCP server '{server}'"

            request_data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": parameters or {},
                },
            }

            request_json = json.dumps(request_data)

            try:
                process = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        server_command,
                        *server_args,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    ),
                    timeout=timeout,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(request_json.encode()),
                    timeout=timeout,
                )

                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Process failed"
                    return False, None, error_msg

                response_data = json.loads(stdout.decode())

                if "error" in response_data:
                    error = response_data["error"]
                    error_msg = error.get("message", "Unknown error")
                    return False, None, error_msg

                result = response_data.get("result")
                return True, result, None

            except asyncio.TimeoutError:
                return False, None, f"MCP call timeout after {timeout}s"

            except json.JSONDecodeError as e:
                return False, None, f"Invalid JSON response from MCP server: {e}"

            except Exception as e:
                return False, None, f"MCP call error: {e}"

        except Exception as e:
            return False, None, f"MCP setup error: {e}"

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """Execute MCP tool call."""
        start_time = time.perf_counter()

        input_errors = self._validate_inputs(inputs)
        if input_errors:
            error_msg = "; ".join(input_errors)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        server = inputs.get("server", "")
        tool = inputs.get("tool", "")
        parameters = inputs.get("parameters", {})

        if not server or not tool:
            return NodeResult.failure_result(
                error="server and tool are required",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        timeout = float(context.get_config_value("timeout", 30))

        try:
            context.log_info(f"Calling MCP tool '{tool}' on server '{server}'")

            success, result, error = await self._call_mcp_tool(
                context, server, tool, parameters, timeout
            )

            if success:
                context.log_info(f"MCP call successful")
                return NodeResult.success_result(
                    outputs={
                        "result": result,
                        "success": True,
                        "error": None,
                    },
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )
            else:
                context.log_error(f"MCP call failed: {error}")
                return NodeResult.success_result(
                    outputs={
                        "result": None,
                        "success": False,
                        "error": error,
                    },
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

        except Exception as e:
            context.log_error(f"MCP execution error: {e}")
            return NodeResult.failure_result(
                error=f"MCP execution error: {e}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
