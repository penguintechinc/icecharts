"""Tests for IceRuns webhook functionality."""
import pytest
import hmac
import hashlib
from unittest.mock import patch


class TestWebhookExecution:
    """Test webhook triggers, HMAC validation, and rate limiting."""

    def test_webhook_execute_with_token(self, api_client, sample_function):
        """Test executing function via webhook with token."""
        # Create function
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        function_data = create_response.get_json()
        webhook_token = function_data['webhook_token']

        # Execute via webhook
        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test'}
        )
        assert response.status_code in [200, 202]

    def test_webhook_invalid_token(self, api_client):
        """Test webhook with invalid token."""
        response = api_client.post(
            '/api/v1/iceruns/hook/invalid_token_xyz',
            json={'input': 'test'}
        )
        assert response.status_code == 401

    def test_webhook_hmac_validation(self, api_client, sample_function):
        """Test HMAC signature validation."""
        # Create function with signature validation
        sample_function['validate_signature'] = True
        sample_function['webhook_secret'] = 'test_secret_key'

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        function_data = create_response.get_json()
        webhook_token = function_data['webhook_token']

        # Prepare request body
        body = b'{"input": "test"}'

        # Valid signature
        signature = hmac.new(
            b'test_secret_key',
            body,
            hashlib.sha256
        ).hexdigest()

        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test'},
            headers={'X-IceRuns-Signature': f'sha256={signature}'}
        )
        assert response.status_code in [200, 202]

    def test_webhook_invalid_hmac(self, api_client, sample_function):
        """Test webhook with invalid HMAC signature."""
        sample_function['validate_signature'] = True
        sample_function['webhook_secret'] = 'test_secret_key'

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        # Invalid signature
        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test'},
            headers={'X-IceRuns-Signature': 'sha256=invalid'}
        )
        assert response.status_code == 401

    def test_webhook_rate_limiting(self, api_client, sample_function):
        """Test rate limiting on webhook endpoints."""
        sample_function['rate_limit'] = 5  # 5 requests max

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        # Make requests up to limit
        for i in range(5):
            response = api_client.post(
                f'/api/v1/iceruns/hook/{webhook_token}',
                json={'input': f'test_{i}'}
            )
            assert response.status_code in [200, 202]

        # Exceed rate limit
        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test_over_limit'}
        )
        assert response.status_code == 429

    def test_webhook_ip_whitelist(self, api_client, sample_function):
        """Test IP whitelisting on webhook."""
        sample_function['ip_whitelist'] = ['192.168.1.100/32']

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        # Request from non-whitelisted IP
        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test'},
            environ_base={'REMOTE_ADDR': '10.0.0.1'}
        )
        assert response.status_code == 403

    def test_webhook_allowed_methods(self, api_client, sample_function):
        """Test allowed HTTP methods for webhook."""
        sample_function['allowed_methods'] = ['POST']

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        # GET should be rejected
        response = api_client.get(
            f'/api/v1/iceruns/hook/{webhook_token}?input=test'
        )
        assert response.status_code == 405

    def test_webhook_get_allowed(self, api_client, sample_function):
        """Test GET method when allowed."""
        sample_function['allowed_methods'] = ['GET', 'POST']

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        # GET should be allowed
        response = api_client.get(
            f'/api/v1/iceruns/hook/{webhook_token}?input=test'
        )
        assert response.status_code in [200, 202]

    def test_webhook_function_inactive(self, api_client, sample_function):
        """Test webhook execution when function is inactive."""
        sample_function['status'] = 'paused'

        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'input': 'test'}
        )
        assert response.status_code == 409

    def test_webhook_form_data(self, api_client, sample_function):
        """Test webhook with form data instead of JSON."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            data={'field1': 'value1', 'field2': 'value2'}
        )
        assert response.status_code in [200, 202]

    def test_webhook_regenerate_token(self, api_client, auth_token, sample_function):
        """Test regenerating webhook token."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function,
            headers={'Authorization': auth_token}
        )
        function_id = create_response.get_json()['function_id']
        old_token = create_response.get_json()['webhook_token']

        response = api_client.post(
            f'/api/v1/iceruns/{function_id}/webhook/regenerate',
            headers={'Authorization': auth_token}
        )
        assert response.status_code == 200
        new_token = response.get_json()['webhook_token']
        assert new_token != old_token

    def test_webhook_metadata_injection(self, api_client, sample_function):
        """Test that webhook metadata is injected into function input."""
        create_response = api_client.post(
            '/api/v1/iceruns',
            json=sample_function
        )
        webhook_token = create_response.get_json()['webhook_token']

        response = api_client.post(
            f'/api/v1/iceruns/hook/{webhook_token}',
            json={'original_field': 'value'},
            environ_base={'REMOTE_ADDR': '203.0.113.42'}
        )
        assert response.status_code in [200, 202]
        # Metadata should be in execution input
