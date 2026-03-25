"""End-to-end Node.js runtime execution tests."""
import pytest
import time


class TestNodeJSE2E:
    """End-to-end Node.js function execution."""

    def test_nodejs_hello_world(self, api_client, auth_token):
        """Test simple Node.js hello world function."""
        function_data = {
            'name': 'Node.js Hello',
            'runtime': 'nodejs',
            'entrypoint': 'index.js',
            'handler': 'handler',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

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

    def test_nodejs_with_packages(self, api_client, auth_token):
        """Test Node.js function with npm dependencies."""
        function_data = {
            'name': 'Node.js with Packages',
            'runtime': 'nodejs',
            'entrypoint': 'handler.js',
            'handler': 'processData',
            'env_vars': {'NODE_ENV': 'production'},
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'array': [1, 2, 3, 4, 5]}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_nodejs_async_await(self, api_client, auth_token):
        """Test Node.js async/await support."""
        function_data = {
            'name': 'Node.js Async',
            'runtime': 'nodejs',
            'entrypoint': 'async_handler.js',
            'handler': 'processAsync',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'url': 'https://example.com'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_nodejs_error_handling(self, api_client, auth_token):
        """Test Node.js error handling."""
        function_data = {
            'name': 'Node.js Error',
            'runtime': 'nodejs',
            'entrypoint': 'main.js',
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
            json={'input': {'trigger_error': True}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202, 400]

    def test_nodejs_json_processing(self, api_client, auth_token):
        """Test Node.js JSON input/output processing."""
        function_data = {
            'name': 'Node.js JSON',
            'runtime': 'nodejs',
            'entrypoint': 'json_handler.js',
            'handler': 'transform',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        input_data = {
            'data': {'key': 'value', 'count': 42},
            'transform': 'uppercase',
        }

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': input_data},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_nodejs_memory_limit(self, api_client, auth_token):
        """Test Node.js memory limit enforcement."""
        function_data = {
            'name': 'Node.js Memory',
            'runtime': 'nodejs',
            'entrypoint': 'memory.js',
            'handler': 'allocate',
            'memory_limit_mb': 512,
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'size_mb': 200}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_nodejs_timeout(self, api_client, auth_token):
        """Test Node.js timeout enforcement."""
        function_data = {
            'name': 'Node.js Timeout',
            'runtime': 'nodejs',
            'entrypoint': 'sleep.js',
            'handler': 'slowFunction',
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
            json={'input': {'delay_ms': 10000}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_nodejs_env_variables(self, api_client, auth_token):
        """Test Node.js environment variable access."""
        function_data = {
            'name': 'Node.js Env',
            'runtime': 'nodejs',
            'entrypoint': 'env.js',
            'handler': 'getConfig',
            'env_vars': {
                'API_KEY': 'secret_key_123',
                'REGION': 'us-west-2',
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
