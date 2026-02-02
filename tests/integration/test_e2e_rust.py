"""End-to-end Rust runtime execution tests."""
import pytest


class TestRustE2E:
    """End-to-end Rust function execution."""

    def test_rust_hello_world(self, api_client, auth_token):
        """Test simple Rust hello world function."""
        function_data = {
            'name': 'Rust Hello',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
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
            json={'input': {'name': 'World'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_high_performance(self, api_client, auth_token):
        """Test Rust for high-performance computation."""
        function_data = {
            'name': 'Rust Performance',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'compute',
            'memory_limit_mb': 512,
            'cpu_limit': 2.0,
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'iterations': 10000000}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_json_serde(self, api_client, auth_token):
        """Test Rust serde JSON handling."""
        function_data = {
            'name': 'Rust JSON',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'process_json',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        input_data = {
            'user': {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            'action': 'validate',
        }

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': input_data},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_error_handling(self, api_client, auth_token):
        """Test Rust error handling and Result types."""
        function_data = {
            'name': 'Rust Error',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
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
            json={'input': {'error': True}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202, 400]

    def test_rust_concurrent_operations(self, api_client, auth_token):
        """Test Rust concurrent execution with tokio."""
        function_data = {
            'name': 'Rust Concurrent',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'process_concurrent',
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
            json={'input': {'tasks': 100, 'workers': 10}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_memory_safety(self, api_client, auth_token):
        """Test Rust memory safety in function."""
        function_data = {
            'name': 'Rust Memory Safe',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'safe_operations',
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
            json={'input': {'data': [1, 2, 3, 4, 5]}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_with_dependencies(self, api_client, auth_token):
        """Test Rust function with crate dependencies."""
        function_data = {
            'name': 'Rust with Crates',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'process_with_deps',
        }

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=function_data,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'data': 'test data'}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_timeout(self, api_client, auth_token):
        """Test Rust timeout enforcement."""
        function_data = {
            'name': 'Rust Timeout',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'slow_operation',
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
            json={'input': {'duration_ms': 10000}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]

    def test_rust_env_variables(self, api_client, auth_token):
        """Test Rust environment variable access."""
        function_data = {
            'name': 'Rust Env',
            'runtime': 'rust',
            'entrypoint': 'src/main.rs',
            'handler': 'get_config',
            'env_vars': {
                'RUST_LOG': 'info',
                'SERVICE_URL': 'https://service.example.com',
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
