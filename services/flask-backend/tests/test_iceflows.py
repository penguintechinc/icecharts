"""Tests for IceFlows CI/CD Pipeline Orchestration API endpoints."""

import pytest

NONEXISTENT_FLOW_ID = "nonexistent-flow-id-00000000-0000-0000-0000-000000000000"
NONEXISTENT_STAGE_ID = "nonexistent-stage-id-00000000-0000-0000-0000-000000000000"


class TestIceFlowsList:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/iceflows")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceflows", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "flows" in data or "error" in data


class TestIceFlowsCreate:
    def test_create_requires_auth(self, client):
        response = client.post("/api/v1/iceflows", json={"name": "test"})
        assert response.status_code == 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        payload = {"repository_url": "https://github.com/test/repo"}
        response = client.post("/api/v1/iceflows", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_missing_repository_url_returns_400(self, client, auth_headers):
        payload = {"name": "test-flow", "repository_provider": "github"}
        response = client.post("/api/v1/iceflows", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_with_valid_data(self, client, auth_headers):
        payload = {
            "name": "test-flow",
            "repository_url": "https://github.com/test/repo",
            "repository_provider": "github",
        }
        response = client.post("/api/v1/iceflows", json=payload, headers=auth_headers)
        assert response.status_code != 401


class TestIceFlowsGetById:
    def test_get_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceFlowsUpdate:
    def test_update_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}", json={"name": "updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}",
            json={"name": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestIceFlowsDelete:
    def test_delete_requires_auth(self, client):
        response = client.delete(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceFlowsEnableDisable:
    def test_enable_requires_auth(self, client):
        response = client.put(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/enable")
        assert response.status_code == 401

    def test_disable_requires_auth(self, client):
        response = client.put(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/disable")
        assert response.status_code == 401

    def test_enable_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/enable", headers=auth_headers
        )
        assert response.status_code == 404

    def test_disable_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/disable", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceFlowsDuplicate:
    def test_duplicate_requires_auth(self, client):
        response = client.post(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/duplicate")
        assert response.status_code == 401

    def test_duplicate_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/duplicate", headers=auth_headers
        )
        assert response.status_code == 404


class TestIceFlowsStages:
    def test_list_stages_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages")
        assert response.status_code == 401

    def test_create_stage_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages",
            json={"branch_name": "main"},
        )
        assert response.status_code == 401

    def test_list_stages_nonexistent_flow_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages", headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_stage_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages/{NONEXISTENT_STAGE_ID}"
        )
        assert response.status_code == 401

    def test_update_stage_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages/{NONEXISTENT_STAGE_ID}",
            json={"display_name": "updated"},
        )
        assert response.status_code == 401

    def test_delete_stage_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages/{NONEXISTENT_STAGE_ID}"
        )
        assert response.status_code == 401

    def test_reorder_stages_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/stages/reorder",
            json={"stage_ids": []},
        )
        assert response.status_code == 401


class TestIceFlowsExport:
    def test_export_yaml_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/export/yaml")
        assert response.status_code == 401

    def test_export_yaml_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/export/yaml",
            headers=auth_headers,
        )
        assert response.status_code == 404
