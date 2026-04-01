"""Tests for IceRuns Execution Management API endpoints."""

import pytest

NONEXISTENT_FUNCTION_ID = "nonexistent-function-id-abc123"
NONEXISTENT_EXECUTION_ID = "nonexistent-execution-id-xyz"


class TestIceRunsListAllExecutions:
    def test_list_executions_requires_auth(self, client):
        response = client.get("/api/v1/iceruns/executions")
        assert response.status_code == 401

    def test_list_executions_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceruns/executions", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "items" in data or "error" in data


class TestIceRunsFunctionExecutions:
    def test_list_function_executions_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/executions")
        assert response.status_code == 401

    def test_list_function_executions_nonexistent_returns_404(
        self, client, auth_headers
    ):
        response = client.get(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/executions",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsExecuteFunction:
    def test_execute_requires_auth(self, client):
        response = client.post(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/execute")
        assert response.status_code == 401

    def test_execute_nonexistent_function_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/execute",
            json={"input": {}},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsGetExecution:
    def test_get_execution_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}")
        assert response.status_code == 401

    def test_get_execution_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsCancelExecution:
    def test_cancel_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}"
        )
        assert response.status_code == 401

    def test_cancel_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsExecutionLogs:
    def test_get_logs_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/logs"
        )
        assert response.status_code == 401

    def test_get_logs_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/logs",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsExecutionOutput:
    def test_get_output_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/output"
        )
        assert response.status_code == 401

    def test_get_output_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/output",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsExecutionStatus:
    def test_get_status_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/status"
        )
        assert response.status_code == 401

    def test_get_status_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/status",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsRetryExecution:
    def test_retry_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/retry"
        )
        assert response.status_code == 401

    def test_retry_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/retry",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsExecutionArtifacts:
    def test_list_artifacts_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/artifacts"
        )
        assert response.status_code == 401

    def test_list_artifacts_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/executions/{NONEXISTENT_EXECUTION_ID}/artifacts",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceRunsFunctionStats:
    def test_get_stats_requires_auth(self, client):
        response = client.get(f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/stats")
        assert response.status_code == 401

    def test_get_stats_nonexistent_function_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceruns/{NONEXISTENT_FUNCTION_ID}/stats",
            headers=auth_headers,
        )
        assert response.status_code == 404
