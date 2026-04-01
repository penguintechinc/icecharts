"""Tests for IceRuns multi-runtime support."""

import pytest


class TestMultiRuntimeSupport:
    """Test all 7 supported runtimes."""

    @pytest.mark.parametrize(
        "runtime",
        [
            "python3.13",
            "nodejs",
            "go",
            "ruby",
            "bash",
            "powershell",
            "rust",
        ],
    )
    def test_create_function_all_runtimes(self, api_client, auth_token, runtime):
        """Test creating functions for all supported runtimes."""
        function_data = {
            "name": f"Test {runtime}",
            "runtime": runtime,
            "entrypoint": "main.py" if runtime == "python3.13" else "index.js",
            "handler": "handler",
            "memory_limit_mb": 128,
            "timeout_seconds": 60,
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["runtime"] == runtime

    def test_python_runtime_specifics(self, api_client, auth_token):
        """Test Python 3.13 specific configuration."""
        function_data = {
            "name": "Python Test",
            "runtime": "python3.13",
            "entrypoint": "main.py",
            "handler": "handler",
            "env_vars": {"PYTHONUNBUFFERED": "1"},
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_nodejs_runtime_specifics(self, api_client, auth_token):
        """Test Node.js specific configuration."""
        function_data = {
            "name": "Node.js Test",
            "runtime": "nodejs",
            "entrypoint": "index.js",
            "handler": "handler",
            "env_vars": {"NODE_ENV": "production"},
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_go_runtime_specifics(self, api_client, auth_token):
        """Test Go specific configuration."""
        function_data = {
            "name": "Go Test",
            "runtime": "go",
            "entrypoint": "main.go",
            "handler": "Handler",
            "memory_limit_mb": 256,
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_ruby_runtime_specifics(self, api_client, auth_token):
        """Test Ruby specific configuration."""
        function_data = {
            "name": "Ruby Test",
            "runtime": "ruby",
            "entrypoint": "handler.rb",
            "handler": "handler",
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_bash_runtime_specifics(self, api_client, auth_token):
        """Test Bash specific configuration."""
        function_data = {
            "name": "Bash Test",
            "runtime": "bash",
            "entrypoint": "script.sh",
            "handler": "main",
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_powershell_runtime_specifics(self, api_client, auth_token):
        """Test PowerShell specific configuration."""
        function_data = {
            "name": "PowerShell Test",
            "runtime": "powershell",
            "entrypoint": "handler.ps1",
            "handler": "Invoke-Handler",
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_rust_runtime_specifics(self, api_client, auth_token):
        """Test Rust specific configuration."""
        function_data = {
            "name": "Rust Test",
            "runtime": "rust",
            "entrypoint": "src/main.rs",
            "handler": "handler",
            "memory_limit_mb": 512,
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 201

    def test_list_functions_by_runtime(self, api_client, auth_token):
        """Test filtering functions by runtime."""
        response = api_client.get(
            "/api/v1/iceruns?runtime=python3.13", headers={"Authorization": auth_token}
        )
        assert response.status_code == 200

    def test_runtime_validation(self, api_client, auth_token):
        """Test validation rejects unsupported runtimes."""
        function_data = {
            "name": "Unsupported",
            "runtime": "java11",  # Not supported
            "entrypoint": "Main.java",
            "handler": "Handler",
        }

        response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        assert response.status_code == 400
