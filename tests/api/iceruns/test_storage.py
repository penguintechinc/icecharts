"""Tests for IceRuns package storage operations."""
import pytest
import io
from unittest.mock import patch, MagicMock


class TestPackageStorage:
    """Test package upload/download to MinIO/S3."""

    def test_upload_package(self, api_client, auth_token, sample_function):
        """Test uploading function package."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        # Create test zip file
        zip_data = io.BytesIO(b'PK\x03\x04...')

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (zip_data, 'function.zip')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'package_key' in data
        assert 'package_size' in data
        assert 'package_hash' in data

    def test_upload_package_invalid_format(self, api_client, auth_token, sample_function):
        """Test uploading package with invalid format."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        # Invalid file type
        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (io.BytesIO(b'invalid'), 'file.txt')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400

    def test_download_package(self, api_client, auth_token, sample_function):
        """Test downloading package via presigned URL."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        # Upload package first
        zip_data = io.BytesIO(b'PK\x03\x04...')
        api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (zip_data, 'function.zip')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )

        response = api_client.get(
            f'/api/v1/iceruns/{function_id}/package',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'presigned_url' in data or 'url' in data

    def test_delete_package(self, api_client, auth_token, sample_function):
        """Test deleting package from storage."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.delete(
            f'/api/v1/iceruns/{function_id}/package',
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 204]

    def test_upload_package_tar_gz(self, api_client, auth_token, sample_function):
        """Test uploading tar.gz package."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        tar_data = io.BytesIO(b'\x1f\x8b\x08...')  # gzip magic

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (tar_data, 'function.tar.gz')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200

    def test_upload_single_file_package(self, api_client, auth_token, sample_function):
        """Test uploading single Python file."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        py_data = io.BytesIO(b'def handler(event):\n    return {"status": "ok"}')

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (py_data, 'main.py')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200

    def test_package_hash_verification(self, api_client, auth_token, sample_function):
        """Test package hash integrity check."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        zip_data = io.BytesIO(b'PK\x03\x04...')

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/package',
            data={'package': (zip_data, 'function.zip')},
            headers={'Authorization': auth_token},
            content_type='multipart/form-data'
        )
        assert response.status_code == 200
        data = response.get_json()
        # Should contain SHA256 hash
        assert 'package_hash' in data
        assert len(data['package_hash']) == 64

    def test_save_execution_logs(self, api_client, auth_token, sample_function):
        """Test saving execution logs to storage."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        exec_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        execution_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/executions/{execution_id}/logs',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200

    def test_list_artifacts(self, api_client, auth_token, sample_function):
        """Test listing execution artifacts."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        exec_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        execution_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/executions/{execution_id}/artifacts',
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 404]

    def test_download_artifact(self, api_client, auth_token, sample_function):
        """Test downloading specific artifact."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        exec_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        execution_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/executions/{execution_id}/artifacts/output.json',
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 404]
