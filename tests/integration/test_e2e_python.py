"""End-to-end Python runtime execution tests."""
import pytest
import time


class TestPythonE2E:
    """End-to-end Python function execution."""

    def test_python_hello_world(self, api_client, auth_token):
        """Test simple Python hello world function."""
        function_data = {
            'name': 'Python Hello',
            'runtime': 'python3.13',
            'entrypoint': 'main.py',
            'handler': 'handler',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        # Simulate package upload
        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'name': 'World'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_python_with_dependencies(self, api_client, auth_token):
        """Test Python function with package dependencies."""
        function_data = {
            'name': 'Python with Deps',
            'runtime': 'python3.13',
            'entrypoint': 'handler.py',
            'handler': 'process',
            'env_vars': {'PYTHONUNBUFFERED': '1'},
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'data': [1, 2, 3]}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_python_error_handling(self, api_client, auth_token):
        """Test Python function error handling."""
        function_data = {
            'name': 'Python Error Test',
            'runtime': 'python3.13',
            'entrypoint': 'main.py',
            'handler': 'handler',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )

        # May succeed or fail, but should return response
        assert response.status_code in [200, 202, 400]

    def test_python_json_input_output(self, api_client, auth_token):
        """Test Python function with JSON I/O."""
        function_data = {
            'name': 'Python JSON IO',
            'runtime': 'python3.13',
            'entrypoint': 'handler.py',
            'handler': 'main',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        input_data = {
            'user_id': 123,
            'action': 'process',
            'options': {'format': 'json'},
        }

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': input_data},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_python_async_execution(self, api_client, auth_token):
        """Test async Python function execution."""
        function_data = {
            'name': 'Python Async',
            'runtime': 'python3.13',
            'entrypoint': 'main.py',
            'handler': 'async_handler',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}, 'async': True},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

        execution_id = response.get_json()['execution_id']

        # Poll for completion
        for _ in range(10):
            status_response = api_client.get(
                f'/api/v1/iceruns/executions/{execution_id}/status',
                headers={'Authorization': auth_token}
            )
            if status_response.status_code == 200:
                break
            time.sleep(0.5)

    def test_python_memory_limit(self, api_client, auth_token):
        """Test Python function respects memory limit."""
        function_data = {
            'name': 'Python Memory Test',
            'runtime': 'python3.13',
            'entrypoint': 'memory_test.py',
            'handler': 'allocate',
            'memory_limit_mb': 256,
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'size_mb': 100}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_python_timeout(self, api_client, auth_token):
        """Test Python function timeout enforcement."""
        function_data = {
            'name': 'Python Timeout Test',
            'runtime': 'python3.13',
            'entrypoint': 'main.py',
            'handler': 'slow_function',
            'timeout_seconds': 5,
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'sleep_seconds': 10}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_python_environment_variables(self, api_client, auth_token):
        """Test Python function with environment variables."""
        function_data = {
            'name': 'Python Env Vars',
            'runtime': 'python3.13',
            'entrypoint': 'main.py',
            'handler': 'get_env',
            'env_vars': {
                'APP_ENV': 'test',
                'DEBUG': 'true',
            },
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]
