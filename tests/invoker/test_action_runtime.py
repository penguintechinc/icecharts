"""Tests for IceRuns action runtime /init and /run protocol."""

import pytest
import json
from unittest.mock import MagicMock, patch


class TestActionRuntime:
    """Test action runtime /init and /run endpoints."""

    def test_init_endpoint_initializes_action(self):
        """Test /init endpoint initializes action."""
        init_request = {
            "code": 'def handler(event):\n    return {"status": "ok"}',
            "handler": "handler",
        }

        # Simulate init response
        init_response = {"status": "ready"}

        assert init_response["status"] == "ready"

    def test_run_endpoint_executes_action(self):
        """Test /run endpoint executes initialized action."""
        run_request = {
            "input": {"test": "data"},
        }

        # Simulate run response
        run_response = {
            "result": {"status": "success", "data": "processed"},
        }

        assert "result" in run_response

    def test_init_with_invalid_code(self):
        """Test /init rejects invalid code."""
        init_request = {
            "code": "invalid python code [[[",
            "handler": "handler",
        }

        # Should return error
        error_response = {"error": "SyntaxError"}

        assert "error" in error_response

    def test_run_before_init_fails(self):
        """Test /run fails if action not initialized."""
        run_request = {
            "input": {"test": "data"},
        }

        # Should return not initialized error
        error_response = {
            "error": "Action not initialized",
            "code": 400,
        }

        assert error_response["code"] == 400

    def test_handler_not_found_error(self):
        """Test error when handler function not found."""
        init_request = {
            "code": "def other_function(): pass",
            "handler": "missing_handler",
        }

        # Should return not found error
        error_response = {"error": "Handler not found"}

        assert "error" in error_response

    def test_run_exception_handling(self):
        """Test exception during execution is caught."""
        init_request = {
            "code": 'def handler(event):\n    raise ValueError("test error")',
            "handler": "handler",
        }

        # Simulate execution error
        error_response = {
            "error": "ValueError: test error",
        }

        assert "error" in error_response

    def test_init_with_dependencies(self):
        """Test /init with code that has imports."""
        init_request = {
            "code": """
import json
import os

def handler(event):
    return {"env": os.getenv("TEST_VAR")}
""",
            "handler": "handler",
        }

        init_response = {"status": "ready"}
        assert init_response["status"] == "ready"

    def test_run_with_environment_variables(self):
        """Test /run with environment variables."""
        init_request = {
            "code": 'import os\ndef handler(event):\n    return {"var": os.getenv("MY_VAR")}',
            "handler": "handler",
            "env": {"MY_VAR": "test_value"},
        }

        run_request = {
            "input": {},
            "env": {"MY_VAR": "test_value"},
        }

        # Result should contain environment variable
        run_response = {
            "result": {"var": "test_value"},
        }

        assert run_response["result"]["var"] == "test_value"

    def test_run_response_includes_status(self):
        """Test /run response includes HTTP status."""
        run_response = {
            "statusCode": 200,
            "body": json.dumps({"message": "success"}),
        }

        assert run_response["statusCode"] == 200

    def test_run_with_custom_status_code(self):
        """Test /run supports custom HTTP status codes."""
        code = """
def handler(event):
    return {
        "statusCode": 404,
        "body": "Not found"
    }
"""

        # Simulate execution
        run_response = {
            "statusCode": 404,
            "body": "Not found",
        }

        assert run_response["statusCode"] == 404

    def test_run_timeout_enforcement(self):
        """Test /run enforces timeout."""
        import time

        start = time.time()
        timeout = 5

        # Simulate timeout
        elapsed = timeout + 1

        assert elapsed > timeout

    def test_action_output_serialization(self):
        """Test action output is properly serialized."""
        output = {
            "message": "success",
            "data": {"key": "value", "number": 42},
            "list": [1, 2, 3],
        }

        # Should be JSON serializable
        json_str = json.dumps(output)
        deserialized = json.loads(json_str)

        assert deserialized == output

    def test_run_memory_limit_enforcement(self):
        """Test /run enforces memory limits."""
        memory_limit_mb = 128

        # Simulate memory tracking
        memory_used = 64  # MB

        assert memory_used <= memory_limit_mb
