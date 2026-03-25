"""Tests for IceRuns activation ID tracking and retrieval."""
import pytest


class TestActivationTracking:
    """Test activation ID tracking and status retrieval."""

    def test_activation_id_returned_on_execute(self, api_client, auth_token, sample_function):
        """Test that execution returns an activation ID."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        api_client.put(
            f'/api/v1/iceruns/{function_id}/activate',
            headers={'Authorization': auth_token}
        )

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {}},
            headers={'Authorization': auth_token}
        )
        assert response.status_code in [200, 202]
        data = response.get_json()
        assert 'execution_id' in data or 'activation_id' in data

    def test_activation_id_format(self, api_client, auth_token, sample_function):
        """Test activation ID has expected UUID format."""
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
        activation_id = exec_response.get_json().get('execution_id')

        # Should be UUID format
        assert activation_id is not None
        assert len(activation_id) == 36
        assert activation_id.count('-') == 4

    def test_get_activation_status(self, api_client, auth_token, sample_function):
        """Test retrieving activation status by ID."""
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
        activation_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/activations/{activation_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['execution_id'] == activation_id

    def test_activation_status_queued(self, api_client, auth_token, sample_function):
        """Test activation status shows as queued initially."""
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
        activation_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/activations/{activation_id}',
            headers={'Authorization': auth_token}
        )
        data = response.get_json()
        assert data['status'] in ['queued', 'running', 'completed']

    def test_activation_contains_input(self, api_client, auth_token, sample_function):
        """Test activation record contains input data."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        exec_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/execute',
            json={'input': {'test_key': 'test_value'}},
            headers={'Authorization': auth_token}
        )
        activation_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/activations/{activation_id}',
            headers={'Authorization': auth_token}
        )
        data = response.get_json()
        assert 'input' in data or 'input_json' in data

    def test_activation_contains_metadata(self, api_client, auth_token, sample_function):
        """Test activation contains creation metadata."""
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
        activation_id = exec_response.get_json()['execution_id']

        response = api_client.get(
            f'/api/v1/iceruns/activations/{activation_id}',
            headers={'Authorization': auth_token}
        )
        data = response.get_json()
        assert 'created_at' in data or 'timestamp' in data

    def test_activation_not_found(self, api_client, auth_token):
        """Test retrieving non-existent activation."""
        response = api_client.get(
            '/api/v1/iceruns/activations/nonexistent-id',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 404

    def test_list_activations(self, api_client, auth_token):
        """Test listing all activations."""
        response = api_client.get(
            '/api/v1/iceruns/activations',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data

    def test_filter_activations_by_status(self, api_client, auth_token):
        """Test filtering activations by status."""
        response = api_client.get(
            '/api/v1/iceruns/activations?status=completed',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200

    def test_filter_activations_by_function(self, api_client, auth_token, sample_function):
        """Test filtering activations by function ID."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.get(
            f'/api/v1/iceruns/activations?function_id={function_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200

    def test_activation_pagination(self, api_client, auth_token):
        """Test paginating through activations."""
        response = api_client.get(
            '/api/v1/iceruns/activations?page=1&limit=10',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'page' in data
        assert 'total' in data
        assert 'limit' in data

    def test_activation_contains_result(self, api_client, auth_token, sample_function):
        """Test completed activation contains result data."""
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
        activation_id = exec_response.get_json()['execution_id']

        # Poll until completion
        for _ in range(20):
            response = api_client.get(
                f'/api/v1/iceruns/activations/{activation_id}',
                headers={'Authorization': auth_token}
            )
            data = response.get_json()
            if data['status'] == 'completed':
                assert 'output' in data or 'result' in data or 'exit_code' in data
                break

    def test_activation_includes_duration(self, api_client, auth_token, sample_function):
        """Test activation includes execution duration."""
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
        activation_id = exec_response.get_json()['execution_id']

        # Poll until completion
        for _ in range(20):
            response = api_client.get(
                f'/api/v1/iceruns/activations/{activation_id}',
                headers={'Authorization': auth_token}
            )
            data = response.get_json()
            if data['status'] == 'completed':
                assert 'duration_ms' in data or 'duration' in data
                break
