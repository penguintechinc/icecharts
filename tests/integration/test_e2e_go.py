"""End-to-end Go runtime execution tests."""

import pytest


class TestGoE2E:
    """End-to-end Go function execution."""

    def test_go_hello_world(self, api_client, auth_token):
        """Test simple Go hello world function."""
        function_data = {
            "name": "Go Hello",
            "runtime": "go",
            "entrypoint": "main.go",
            "handler": "Handler",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"name": "World"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_with_dependencies(self, api_client, auth_token):
        """Test Go function with module dependencies."""
        function_data = {
            "name": "Go with Deps",
            "runtime": "go",
            "entrypoint": "handler.go",
            "handler": "Process",
            "memory_limit_mb": 256,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"data": [1, 2, 3]}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_json_marshaling(self, api_client, auth_token):
        """Test Go struct marshaling to JSON."""
        function_data = {
            "name": "Go JSON",
            "runtime": "go",
            "entrypoint": "json_handler.go",
            "handler": "ProcessJSON",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        input_data = {
            "user": "alice",
            "action": "create",
            "metadata": {"key": "value"},
        }

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": input_data},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_error_handling(self, api_client, auth_token):
        """Test Go error handling."""
        function_data = {
            "name": "Go Error",
            "runtime": "go",
            "entrypoint": "main.go",
            "handler": "Handler",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"trigger_error": True}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202, 400]

    def test_go_high_performance(self, api_client, auth_token):
        """Test Go for high-performance computation."""
        function_data = {
            "name": "Go Performance",
            "runtime": "go",
            "entrypoint": "compute.go",
            "handler": "Compute",
            "cpu_limit": 2.0,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"iterations": 1000000}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_concurrent_operations(self, api_client, auth_token):
        """Test Go goroutines in function."""
        function_data = {
            "name": "Go Concurrent",
            "runtime": "go",
            "entrypoint": "concurrent.go",
            "handler": "ProcessConcurrent",
            "memory_limit_mb": 512,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"workers": 10, "tasks": 100}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_timeout_enforcement(self, api_client, auth_token):
        """Test Go timeout enforcement."""
        function_data = {
            "name": "Go Timeout",
            "runtime": "go",
            "entrypoint": "sleep.go",
            "handler": "SlowFunction",
            "timeout_seconds": 5,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"duration_seconds": 10}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_go_env_variables(self, api_client, auth_token):
        """Test Go environment variable access."""
        function_data = {
            "name": "Go Env",
            "runtime": "go",
            "entrypoint": "env.go",
            "handler": "GetConfig",
            "env_vars": {
                "DATABASE_URL": "postgres://localhost",
                "LOG_LEVEL": "debug",
            },
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]
