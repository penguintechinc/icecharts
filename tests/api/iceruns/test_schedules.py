"""Tests for IceRuns cron scheduling and timezone support."""
import pytest


class TestScheduling:
    """Test cron scheduling and timezone handling."""

    def test_create_schedule(self, api_client, auth_token, sample_function):
        """Test creating a cron schedule for a function."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        schedule_data = {
            'cron_expression': '0 9 * * MON',
            'timezone': 'America/New_York',
            'static_input': {'key': 'value'},
        }

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json=schedule_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert 'schedule_id' in data
        assert data['cron_expression'] == '0 9 * * MON'
        assert data['timezone'] == 'America/New_York'

    def test_list_schedules(self, api_client, auth_token, sample_function):
        """Test listing schedules for a function."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.get(
            f'/api/v1/iceruns/{function_id}/schedules',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'items' in data

    def test_get_schedule(self, api_client, auth_token, sample_function):
        """Test retrieving schedule details."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        schedule_data = {
            'cron_expression': '0 12 * * *',
            'timezone': 'UTC',
        }
        schedule_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json=schedule_data,
            headers={'Authorization': auth_token}
        )
        schedule_id = schedule_response.get_json()['schedule_id']

        response = api_client.get(
            f'/api/v1/iceruns/{function_id}/schedules/{schedule_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['schedule_id'] == schedule_id

    def test_update_schedule(self, api_client, auth_token, sample_function):
        """Test updating a schedule."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        schedule_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={'cron_expression': '0 9 * * *'},
            headers={'Authorization': auth_token}
        )
        schedule_id = schedule_response.get_json()['schedule_id']

        update_data = {
            'cron_expression': '0 15 * * *',
            'is_active': False,
        }
        response = api_client.put(
            f'/api/v1/iceruns/{function_id}/schedules/{schedule_id}',
            json=update_data,
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200

    def test_delete_schedule(self, api_client, auth_token, sample_function):
        """Test deleting a schedule."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        schedule_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={'cron_expression': '0 9 * * *'},
            headers={'Authorization': auth_token}
        )
        schedule_id = schedule_response.get_json()['schedule_id']

        response = api_client.delete(
            f'/api/v1/iceruns/{function_id}/schedules/{schedule_id}',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 204

    def test_invalid_cron_expression(self, api_client, auth_token, sample_function):
        """Test validation of invalid cron expression."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={'cron_expression': 'invalid'},
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400

    def test_timezone_validation(self, api_client, auth_token, sample_function):
        """Test timezone validation."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={'cron_expression': '0 12 * * *', 'timezone': 'Invalid/Timezone'},
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 400

    def test_schedule_next_run_calculation(self, api_client, auth_token, sample_function):
        """Test next_run_at is calculated correctly."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={
                'cron_expression': '0 12 * * *',
                'timezone': 'UTC',
                'is_active': True,
            },
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert 'next_run_at' in data

    def test_schedule_disable_enable(self, api_client, auth_token, sample_function):
        """Test enabling/disabling a schedule."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        schedule_response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={'cron_expression': '0 12 * * *', 'is_active': True},
            headers={'Authorization': auth_token}
        )
        schedule_id = schedule_response.get_json()['schedule_id']

        # Disable
        response = api_client.put(
            f'/api/v1/iceruns/{function_id}/schedules/{schedule_id}',
            json={'is_active': False},
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        assert response.get_json()['is_active'] == False

        # Re-enable
        response = api_client.put(
            f'/api/v1/iceruns/{function_id}/schedules/{schedule_id}',
            json={'is_active': True},
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        assert response.get_json()['is_active'] == True

    def test_schedule_with_static_input(self, api_client, auth_token, sample_function):
        """Test schedule with static input payload."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']

        static_input = {
            'user_id': 123,
            'action': 'generate_report',
            'options': {'format': 'pdf'}
        }

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/schedules',
            json={
                'cron_expression': '0 1 * * SUN',
                'timezone': 'America/New_York',
                'static_input': static_input,
            },
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['static_input'] == static_input
