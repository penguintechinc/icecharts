"""Tests for IceFlows Stage Configuration API endpoints (approvers, tests, calls, reviews)."""

import pytest

NONEXISTENT_STAGE_ID = "nonexistent-stage-id-00000000-0000-0000-0000-000000000000"
NONEXISTENT_ITEM_ID = "nonexistent-item-id-00000000-0000-0000-0000-000000000000"


class TestStageApprovers:
    def test_list_approvers_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers"
        )
        assert response.status_code == 401

    def test_list_approvers_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_add_approver_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers",
            json={"identity_id": "1"},
        )
        assert response.status_code == 401

    def test_add_approver_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers",
            json={"identity_id": "1", "role": "approver"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_approver_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers/{NONEXISTENT_ITEM_ID}"
        )
        assert response.status_code == 401

    def test_delete_approver_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/approvers/{NONEXISTENT_ITEM_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestStageTests:
    def test_list_tests_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests")
        assert response.status_code == 401

    def test_list_tests_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_test_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests",
            json={"name": "test-suite"},
        )
        assert response.status_code == 401

    def test_create_test_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests",
            json={"name": "test-suite", "command": "pytest"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_test_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests/{NONEXISTENT_ITEM_ID}"
        )
        assert response.status_code == 401

    def test_update_test_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests/{NONEXISTENT_ITEM_ID}",
            json={"name": "updated"},
        )
        assert response.status_code == 401

    def test_delete_test_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests/{NONEXISTENT_ITEM_ID}"
        )
        assert response.status_code == 401

    def test_delete_test_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/tests/{NONEXISTENT_ITEM_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestStageCalls:
    def test_list_calls_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls")
        assert response.status_code == 401

    def test_list_calls_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_call_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls",
            json={"name": "deploy-call"},
        )
        assert response.status_code == 401

    def test_create_call_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls",
            json={"name": "deploy-call", "call_type": "icestreams"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_call_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls/{NONEXISTENT_ITEM_ID}"
        )
        assert response.status_code == 401

    def test_update_call_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls/{NONEXISTENT_ITEM_ID}",
            json={"name": "updated"},
        )
        assert response.status_code == 401

    def test_delete_call_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls/{NONEXISTENT_ITEM_ID}"
        )
        assert response.status_code == 401

    def test_delete_call_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/calls/{NONEXISTENT_ITEM_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestStageReviews:
    def test_get_review_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/reviews")
        assert response.status_code == 401

    def test_update_review_requires_auth(self, client):
        response = client.put(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/reviews",
            json={"enabled": True},
        )
        assert response.status_code == 401

    def test_get_review_nonexistent_stage_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/stages/{NONEXISTENT_STAGE_ID}/reviews",
            headers=auth_headers,
        )
        assert response.status_code == 404
