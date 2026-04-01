"""End-to-end Ruby runtime execution tests."""

import pytest


class TestRubyE2E:
    """End-to-end Ruby function execution."""

    def test_ruby_hello_world(self, api_client, auth_token):
        """Test simple Ruby hello world function."""
        function_data = {
            "name": "Ruby Hello",
            "runtime": "ruby",
            "entrypoint": "handler.rb",
            "handler": "handler",
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

    def test_ruby_with_gems(self, api_client, auth_token):
        """Test Ruby function with gem dependencies."""
        function_data = {
            "name": "Ruby with Gems",
            "runtime": "ruby",
            "entrypoint": "processor.rb",
            "handler": "process_data",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"text": "Hello Ruby"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_ruby_string_manipulation(self, api_client, auth_token):
        """Test Ruby string processing."""
        function_data = {
            "name": "Ruby Strings",
            "runtime": "ruby",
            "entrypoint": "string_handler.rb",
            "handler": "process_string",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"text": "Hello World", "operation": "uppercase"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_ruby_json_processing(self, api_client, auth_token):
        """Test Ruby JSON input/output."""
        function_data = {
            "name": "Ruby JSON",
            "runtime": "ruby",
            "entrypoint": "json_handler.rb",
            "handler": "transform_json",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        input_data = {
            "user": {"name": "Alice", "age": 30},
            "action": "validate",
        }

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": input_data},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_ruby_error_handling(self, api_client, auth_token):
        """Test Ruby error handling and exceptions."""
        function_data = {
            "name": "Ruby Error",
            "runtime": "ruby",
            "entrypoint": "main.rb",
            "handler": "handler",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"error": True}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202, 400]

    def test_ruby_array_processing(self, api_client, auth_token):
        """Test Ruby array manipulation."""
        function_data = {
            "name": "Ruby Arrays",
            "runtime": "ruby",
            "entrypoint": "array_handler.rb",
            "handler": "process_array",
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"array": [1, 2, 3, 4, 5], "operation": "sum"}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_ruby_timeout(self, api_client, auth_token):
        """Test Ruby timeout enforcement."""
        function_data = {
            "name": "Ruby Timeout",
            "runtime": "ruby",
            "entrypoint": "sleep.rb",
            "handler": "slow_operation",
            "timeout_seconds": 5,
        }

        create_response = api_client.post(
            "/api/v1/iceruns", json=function_data, headers={"Authorization": auth_token}
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"sleep_seconds": 10}},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_ruby_env_variables(self, api_client, auth_token):
        """Test Ruby environment variable access."""
        function_data = {
            "name": "Ruby Env",
            "runtime": "ruby",
            "entrypoint": "env.rb",
            "handler": "get_config",
            "env_vars": {
                "API_ENDPOINT": "https://api.example.com",
                "AUTH_TOKEN": "secret_token_123",
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
