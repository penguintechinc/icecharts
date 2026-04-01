"""
CodeTransform node for executing user-provided Python code in a sandboxed environment.

This module provides a secure way to execute arbitrary Python code with restricted
access to dangerous functions and modules. Uses a limited built-in namespace and
enforces timeouts to prevent malicious or infinite-looping code from hanging the system.

The sandbox provides safe utilities (json, re, datetime) while blocking access to
file I/O, system commands, imports, and introspection capabilities.

User code must set a 'result' variable to provide output. All print statements are
captured and logged.

Example:
    # Simple transformation
    code = '''
    result = [x * 2 for x in data]
    '''

    # With logging
    code = '''
    print(f"Processing {len(data)} items")
    result = {
        "count": len(data),
        "sum": sum(data),
        "avg": sum(data) / len(data) if data else 0
    }
    '''
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Dict, List

from ..base import BaseNode, NodeContext, NodeInput, NodeOutput, NodeResult
from ...executor.node_registry import register_node

logger = logging.getLogger(__name__)


# Safe builtins for sandboxed execution
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
}

# Dangerous names that should never be allowed
FORBIDDEN_NAMES = {
    "exec",
    "eval",
    "compile",
    "open",
    "file",
    "__import__",
    "importlib",
    "os",
    "sys",
    "subprocess",
    "shutil",
    "pathlib",
    "glob",
    "__builtins__",
    "__loader__",
    "__spec__",
    "__file__",
    "__name__",
    "breakpoint",
    "input",
    "exit",
    "quit",
    "help",
    "copyright",
    "license",
    "credits",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "vars",
    "dir",
    "globals",
    "locals",
    "memoryview",
    "object",
    "property",
    "super",
    "staticmethod",
    "classmethod",
    "__class__",
    "__bases__",
    "__mro__",
}


@register_node("transform_code", "transforms", "Code")
class CodeTransform(BaseNode):
    """Execute sandboxed Python code for custom transformations."""

    node_type = "transform_code"
    name = "Code"
    description = "Run sandboxed Python code for custom data transformation"
    category = "transforms"

    @classmethod
    def inputs(cls) -> List[NodeInput]:
        """Define input ports for code transform."""
        return [
            NodeInput(
                name="in",
                description="Input data (accessible as 'data' in code)",
                required=True,
                data_type="any",
            ),
        ]

    @classmethod
    def outputs(cls) -> List[NodeOutput]:
        """Define output ports for code transform."""
        return [
            NodeOutput(
                name="out",
                description="Transformed output (value of 'result' variable)",
                data_type="any",
            ),
        ]

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> List[str]:
        """
        Validate the code configuration.

        Checks for:
        - Required 'code' field
        - Forbidden names and dangerous patterns
        - Syntax errors
        - Valid timeout value

        Args:
            config: Node configuration dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for code field
        code = config.get("code", "")
        if not code:
            errors.append("code is required")
            return errors

        # Check for forbidden names
        for forbidden in FORBIDDEN_NAMES:
            if forbidden in code:
                errors.append(f"Forbidden name in code: {forbidden}")

        # Check for dangerous patterns (basic string matching)
        dangerous_patterns = [
            "__",
            "import ",
            "from ",
            "exec(",
            "eval(",
            "compile(",
            "open(",
            "file(",
            "subprocess",
            "os.",
            "sys.",
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                errors.append(f"Dangerous pattern in code: {pattern}")

        # Try to compile the code
        try:
            compile(code, "<user_code>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error in code: {e}")

        # Validate timeout if provided
        timeout = config.get("timeout", 10)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("timeout must be a positive number")
        if timeout > 30:
            errors.append("timeout cannot exceed 30 seconds")

        return errors

    def _create_sandbox(self, input_data: Any) -> Dict[str, Any]:
        """
        Create the sandboxed execution environment.

        Provides:
        - Safe builtins (math, type checking, iteration)
        - Input data as 'data' variable
        - Output capture for print statements
        - Safe utilities (json, re, datetime)

        Args:
            input_data: The input data to make available as 'data'

        Returns:
            Sandbox dictionary with safe globals and builtins
        """
        output_capture = []

        def safe_print(*args, **kwargs):
            """Capture print output for logging."""
            output_capture.append(" ".join(str(a) for a in args))

        # Build sandbox with safe utilities
        # We import these modules here to give them to the sandbox
        import json as json_module
        import re as re_module
        import datetime as datetime_module

        sandbox = {
            **SAFE_BUILTINS,
            "print": safe_print,
            "data": input_data,
            "result": None,
            "_output": output_capture,
            # Safe modules/utilities via function wrappers
            "json_dumps": json_module.dumps,
            "json_loads": json_module.loads,
            "datetime_now": lambda: datetime_module.datetime.now(
                datetime_module.timezone.utc
            ),
            "re_match": re_module.match,
            "re_search": re_module.search,
            "re_findall": re_module.findall,
            "re_sub": re_module.sub,
        }

        return sandbox

    async def execute(self, context: NodeContext, inputs: Dict[str, Any]) -> NodeResult:
        """
        Execute the sandboxed code transform.

        Validates inputs, compiles code, executes in sandbox with timeout,
        and returns the 'result' variable as output.

        Args:
            context: Execution context with config and logging
            inputs: Dictionary with 'in' key containing input data

        Returns:
            NodeResult with output data or error message
        """
        start_time = time.perf_counter()

        # Validate required inputs
        input_errors = self._validate_inputs(inputs)
        if input_errors:
            return NodeResult.failure_result(
                error=f"Input validation failed: {', '.join(input_errors)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        input_data = self._get_input_value(inputs, "in")
        code = context.get_config_value("code", "result = data")
        timeout_seconds = min(context.get_config_value("timeout", 10), 30)

        # Additional runtime safety checks
        for forbidden in FORBIDDEN_NAMES:
            if forbidden in code:
                return NodeResult.failure_result(
                    error=f"Forbidden name in code: {forbidden}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                )

        # Create sandbox
        sandbox = self._create_sandbox(input_data)

        try:
            # Compile the code
            compiled = compile(code, "<user_code>", "exec")

            # Define the code execution function
            def run_code():
                """Execute the compiled code in the sandbox."""
                exec(compiled, {"__builtins__": {}}, sandbox)
                return sandbox.get("result")

            # Execute with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, run_code), timeout=timeout_seconds
            )

            # Log any captured output
            if sandbox["_output"]:
                for line in sandbox["_output"]:
                    context.log_info(f"[code] {line}")

            context.log_info("Code execution completed successfully")

            return NodeResult.success_result(
                outputs={"out": result},
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except asyncio.TimeoutError:
            context.log_error(f"Code execution timed out after {timeout_seconds}s")
            return NodeResult.failure_result(
                error=f"Code execution timed out after {timeout_seconds}s",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
        except Exception as e:
            error_msg = f"Code execution failed: {str(e)}"
            context.log_error(error_msg)
            return NodeResult.failure_result(
                error=error_msg,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )
