"""Tests for IceRuns function CRUD operations."""
import pytest
from unittest.mock import patch, MagicMock


class TestFunctionCRUD:
    """Test function create, read, update, delete operations."""

    def test_create_function(self, api_client, auth_token, sample_function):
        """Test creating a new IceRuns function."""
        response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == sample_function['name']
        assert data['runtime'] == sample_function['runtime']
        assert 'function_id' in data
        assert 'webhook_token' in data

    def test_create_function_missing_required_field(self, api_client, auth_token):
        """Test creating function with missing required field."""
        incomplete_function = {
            'description': 'No name provided',
            'runtime': 'python3.13',
        }
        response = api_client.post(
            '/api/v1/iceruns',
            json=incomplete_function,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400

    def test_list_functions(self, api_client, auth_token):
        """Test listing all functions with pagination."""
        response = api_client.get(
            '/api/v1/iceruns?page=1&limit=10',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data

    def test_get_function(self, api_client, auth_token, sample_function):
        """Test retrieving function details."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.get(
            f'/api/v1/iceruns/{function_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['function_id'] == function_id
        assert data['name'] == sample_function['name']

    def test_get_function_not_found(self, api_client, auth_token):
        """Test retrieving non-existent function."""
        response = api_client.get(
            '/api/v1/iceruns/nonexistent_id',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 404

    def test_update_function(self, api_client, auth_token, sample_function):
        """Test updating function configuration."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        update_data = {
            'description': 'Updated description',
            'memory_limit_mb': 256,
        }
        response = api_client.put(
            f'/api/v1/iceruns/{function_id}',
            json=update_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['description'] == 'Updated description'
        assert data['memory_limit_mb'] == 256

    def test_delete_function(self, api_client, auth_token, sample_function):
        """Test deleting a function."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.delete(
            f'/api/v1/iceruns/{function_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 204

        # Verify deletion
        get_response = api_client.get(
            f'/api/v1/iceruns/{function_id}',
            headers={'Authorization': auth_token}
        )
        assert get_response.status_code == 404

    def test_invalid_runtime(self, api_client, auth_token):
        """Test creating function with invalid runtime."""
        invalid_function = {
            'name': 'Invalid Runtime',
            'runtime': 'invalid_runtime',
            'entrypoint': 'main.py',
            'handler': 'handler',
        }
        response = api_client.post(
            '/api/v1/iceruns',
            json=invalid_function,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400

    def test_invalid_memory_limit(self, api_client, auth_token, sample_function):
        """Test validation of memory limit bounds."""
        sample_function['memory_limit_mb'] = 16384  # Too high
        response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400

    def test_invalid_timeout(self, api_client, auth_token, sample_function):
        """Test validation of timeout bounds."""
        sample_function['timeout_seconds'] = 1800  # Too high
        response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400
