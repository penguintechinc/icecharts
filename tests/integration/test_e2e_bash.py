"""End-to-end Bash runtime execution tests."""

import pytest


class TestBashE2E:
    """End-to-end Bash script execution."""

    def test_bash_hello_world(self, api_client, auth_token):
        """Test simple Bash hello world script."""
        function_data = {
            "name": "Bash Hello",
            "runtime": "bash",
            "entrypoint": "script.sh",
            "handler": "main",
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

    def test_bash_file_processing(self, api_client, auth_token):
        """Test Bash file manipulation."""
        function_data = {
            "name": "Bash Files",
            "runtime": "bash",
            "entrypoint": "process.sh",
            "handler": "process",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"action": "list_files"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_bash_text_processing(self, api_client, auth_token):
        """Test Bash text utilities (grep, sed, awk)."""
        function_data = {
            "name": "Bash Text",
            "runtime": "bash",
            "entrypoint": "text_process.sh",
            "handler": "process_text",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"text": "line1\nline2\nline3", "operation": "count_lines"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_bash_json_output(self, api_client, auth_token):
        """Test Bash outputting JSON."""
        function_data = {
            "name": "Bash JSON",
            "runtime": "bash",
            "entrypoint": "json_output.sh",
            "handler": "output_json",
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

    def test_bash_exit_codes(self, api_client, auth_token):
        """Test Bash exit code handling."""
        function_data = {
            "name": "Bash Exit",
            "runtime": "bash",
            "entrypoint": "main.sh",
            "handler": "handler",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"should_fail": False}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_bash_command_piping(self, api_client, auth_token):
        """Test Bash command piping and redirection."""
        function_data = {
            "name": "Bash Pipe",
            "runtime": "bash",
            "entrypoint": "pipe.sh",
            "handler": "pipe_commands",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"data": "test data to process"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_bash_environment_variables(self, api_client, auth_token):
        """Test Bash environment variable access."""
        function_data = {
            "name": "Bash Env",
            "runtime": "bash",
            "entrypoint": "env.sh",
            "handler": "show_env",
            "env_vars": {
                "CONFIG_PATH": "/config",
                "DEBUG_MODE": "true",
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

    def test_bash_timeout(self, api_client, auth_token):
        """Test Bash timeout enforcement."""
        function_data = {
            "name": "Bash Timeout",
            "runtime": "bash",
            "entrypoint": "sleep.sh",
            "handler": "sleep_function",
            "timeout_seconds": 5,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"duration": 10}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]
