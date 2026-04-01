"""Tests for IceRuns authorization and scope enforcement."""

import pytest


class TestAuthorizationAndScopes:
    """Test scope enforcement and authorization."""

    def test_iceruns_read_scope(self, api_client, token_with_scope):
        """Test iceruns:read scope allows listing functions."""
        token = token_with_scope(["iceruns:read"])

        response = api_client.get(
            "/api/v1/iceruns", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    def test_iceruns_write_scope(self, api_client, token_with_scope, sample_function):
        """Test iceruns:write scope allows creating functions."""
        token = token_with_scope(["iceruns:write"])

        response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_iceruns_delete_scope(self, api_client, token_with_scope, sample_function):
        """Test iceruns:delete scope allows deleting functions."""
        # Create function
        create_token = token_with_scope(["iceruns:write"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {create_token}"},
        )
        function_id = create_response.get_json()["function_id"]

        # Delete function
        delete_token = token_with_scope(["iceruns:delete"])
        response = api_client.delete(
            f"/api/v1/iceruns/{function_id}",
            headers={"Authorization": f"Bearer {delete_token}"},
        )
        assert response.status_code == 204

    def test_iceruns_execute_scope(self, api_client, token_with_scope, sample_function):
        """Test iceruns:execute scope allows executing functions."""
        # Create function
        create_token = token_with_scope(["iceruns:write"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {create_token}"},
        )
        function_id = create_response.get_json()["function_id"]

        # Execute function
        exec_token = token_with_scope(["iceruns:execute"])
        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": f"Bearer {exec_token}"},
        )
        assert response.status_code in [200, 202]

    def test_iceruns_logs_scope(self, api_client, token_with_scope, sample_function):
        """Test iceruns:logs scope allows viewing execution logs."""
        # Create and execute function
        token = token_with_scope(["iceruns:write", "iceruns:execute", "iceruns:logs"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token}"},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        execution_id = exec_response.get_json()["execution_id"]

        # View logs
        response = api_client.get(
            f"/api/v1/iceruns/executions/{execution_id}/logs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_missing_scope_denied(self, api_client, token_with_scope):
        """Test request denied when required scope is missing."""
        token = token_with_scope(["other:scope"])

        response = api_client.get(
            "/api/v1/iceruns", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403

    def test_no_token_unauthorized(self, api_client):
        """Test request without token is unauthorized."""
        response = api_client.get("/api/v1/iceruns")
        assert response.status_code == 401

    def test_invalid_token(self, api_client):
        """Test request with invalid token is rejected."""
        response = api_client.get(
            "/api/v1/iceruns", headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert response.status_code == 401

    def test_scope_group_full_access(
        self, api_client, token_with_scope, sample_function
    ):
        """Test iceruns:full scope group grants all access."""
        token = token_with_scope(["iceruns:full"])

        # Test read
        read_response = api_client.get(
            "/api/v1/iceruns", headers={"Authorization": f"Bearer {token}"}
        )
        assert read_response.status_code == 200

        # Test write
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201

    def test_scope_group_readonly(self, api_client, token_with_scope, sample_function):
        """Test iceruns:readonly scope group."""
        token = token_with_scope(["iceruns:readonly"])

        # Test read allowed
        read_response = api_client.get(
            "/api/v1/iceruns", headers={"Authorization": f"Bearer {token}"}
        )
        assert read_response.status_code == 200

        # Test write denied
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 403

    def test_scope_group_execute_only(
        self, api_client, token_with_scope, sample_function
    ):
        """Test iceruns:execute_only scope group."""
        # Create function first
        full_token = token_with_scope(["iceruns:write", "iceruns:execute"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {full_token}"},
        )
        function_id = create_response.get_json()["function_id"]

        # Test execute with limited token
        exec_token = token_with_scope(["iceruns:execute_only"])
        response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": f"Bearer {exec_token}"},
        )
        assert response.status_code in [200, 202]

    def test_admin_can_delete_others_execution(
        self, api_client, token_with_scope, sample_function
    ):
        """Test admin scope allows canceling others' executions."""
        # Create and execute
        token = token_with_scope(["iceruns:write", "iceruns:execute"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token}"},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        execution_id = exec_response.get_json()["execution_id"]

        # Admin cancels
        admin_token = token_with_scope(["iceruns:admin"])
        response = api_client.delete(
            f"/api/v1/iceruns/executions/{execution_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code in [200, 204]

    def test_non_admin_cannot_delete_others_execution(
        self, api_client, token_with_scope, sample_function
    ):
        """Test non-admin cannot cancel others' executions."""
        # Create and execute
        token1 = token_with_scope(["iceruns:write", "iceruns:execute"])
        create_response = api_client.post(
            "/api/v1/iceruns",
            json=sample_function,
            headers={"Authorization": f"Bearer {token1}"},
        )
        function_id = create_response.get_json()["function_id"]

        exec_response = api_client.post(
            f"/api/v1/iceruns/{function_id}/execute",
            json={"input": {}},
            headers={"Authorization": f"Bearer {token1}"},
        )
        execution_id = exec_response.get_json()["execution_id"]

        # Different user tries to cancel
        token2 = token_with_scope(["iceruns:execute"])
        response = api_client.delete(
            f"/api/v1/iceruns/executions/{execution_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 403
