"""Tests for IceRuns execution lifecycle."""

import pytest
import time
from unittest.mock import patch


class TestExecutionLifecycle:
    """Test execution queuing, running, and completion."""

    def test_execute_function_async(self, api_client, auth_token, sample_function):
        """Test async function execution."""
        # Create and activate function
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        # Execute
        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"test": "data"}, "async": True},
            headers={"Authorization": auth_token},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "queued"
        assert "execution_id" in data

    def test_execute_function_sync(self, api_client, auth_token, sample_function):
        """Test synchronous function execution (wait for result)."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        api_client.put(
            f"/api/v1/iceruns/{function_id}/activate",
            headers={"Authorization": auth_token},
        )

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {"test": "data"}, "async": False},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_get_execution_status(self, api_client, auth_token, sample_function):
        """Test polling execution status."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        execution_id = exec_response.get_json()["execution_id"]

        response = api_client.get(
            f"/api/v1/iceruns/executions/{execution_id}/status",
            headers={"Authorization": auth_token},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert data["execution_id"] == execution_id

    def test_list_executions_for_function(
        self, api_client, auth_token, sample_function
    ):
        """Test listing executions for a specific function."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.get(
            f"/api/v1/iceruns/{function_id}/executions",
            headers={"Authorization": auth_token},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data

    def test_list_all_executions(self, api_client, auth_token):
        """Test listing all executions globally."""
        response = api_client.get(
            "/api/v1/iceruns/executions?page=1&limit=20",
            headers={"Authorization": auth_token},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        assert "total" in data

    def test_cancel_execution(self, api_client, auth_token, sample_function):
        """Test canceling a running execution."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        execution_id = exec_response.get_json()["execution_id"]

        response = api_client.delete(
            f"/api/v1/iceruns/executions/{execution_id}",
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 204]

    def test_get_execution_logs(self, api_client, auth_token, sample_function):
        """Test retrieving execution logs."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        execution_id = exec_response.get_json()["execution_id"]

        response = api_client.get(
            f"/api/v1/iceruns/executions/{execution_id}/logs",
            headers={"Authorization": auth_token},
        )
        assert response.status_code == 200

    def test_get_execution_output(self, api_client, auth_token, sample_function):
        """Test retrieving execution output."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        execution_id = exec_response.get_json()["execution_id"]

        response = api_client.get(
            f"/api/v1/iceruns/executions/{execution_id}/output",
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_retry_failed_execution(self, api_client, auth_token, sample_function):
        """Test retrying a failed execution."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": auth_token},
        )
        execution_id = exec_response.get_json()["execution_id"]

        response = api_client.post(
            f"/api/v1/iceruns/executions/{execution_id}/retry",
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]

    def test_execution_timeout(self, api_client, auth_token, sample_function):
        """Test execution with custom timeout override."""
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": auth_token},
        )
        function_id = create_response.get_json()["function_id"]

        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}, "timeout_override": 30},
            headers={"Authorization": auth_token},
        )
        assert response.status_code in [200, 202]
