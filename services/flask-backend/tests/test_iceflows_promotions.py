"""Tests for IceFlows Promotions and Approvals API endpoints."""

import pytest

NONEXISTENT_FLOW_ID = "nonexistent-flow-id-00000000-0000-0000-0000-000000000000"
NONEXISTENT_PROMOTION_ID = (
    "nonexistent-promotion-id-00000000-0000-0000-0000-000000000000"
)


class TestListPromotions:
    def test_list_promotions_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions")
        assert response.status_code == 401

    def test_list_promotions_nonexistent_flow_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_list_promotions_with_auth(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions",
            headers=auth_headers,
        )
        assert response.status_code != 401


class TestCreatePromotion:
    def test_create_promotion_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions",
            json={"source_stage_id": "stage-1", "target_stage_id": "stage-2"},
        )
        assert response.status_code == 401

    def test_create_promotion_nonexistent_flow_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions",
            json={"source_stage_id": "stage-1", "target_stage_id": "stage-2"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_promotion_missing_fields_returns_error(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/{NONEXISTENT_FLOW_ID}/promotions",
            json={},
            headers=auth_headers,
        )
        assert response.status_code in (400, 404)


class TestGetPromotion:
    def test_get_promotion_requires_auth(self, client):
        response = client.get(f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}")
        assert response.status_code == 401

    def test_get_promotion_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeletePromotion:
    def test_delete_promotion_requires_auth(self, client):
        response = client.delete(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}"
        )
        assert response.status_code == 401

    def test_delete_promotion_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestPromotionMerge:
    def test_merge_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/merge"
        )
        assert response.status_code == 401

    def test_merge_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/merge",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestPromotionApproval:
    def test_approve_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/approve"
        )
        assert response.status_code == 401

    def test_approve_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/approve",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 404

    def test_reject_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/reject"
        )
        assert response.status_code == 401

    def test_reject_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/reject",
            json={"reason": "Not ready"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_override_requires_auth(self, client):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/override"
        )
        assert response.status_code == 401

    def test_override_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/override",
            json={"reason": "Emergency override"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestMyApprovals:
    def test_my_approvals_requires_auth(self, client):
        response = client.get("/api/v1/iceflows/my-approvals")
        assert response.status_code == 401

    def test_my_approvals_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceflows/my-approvals", headers=auth_headers)
        assert response.status_code != 401


class TestAllApprovals:
    def test_all_approvals_requires_auth(self, client):
        response = client.get("/api/v1/iceflows/approvals")
        assert response.status_code == 401

    def test_all_approvals_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/iceflows/approvals", headers=auth_headers)
        assert response.status_code != 401


class TestPromotionStatus:
    def test_approval_status_requires_auth(self, client):
        response = client.get(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/status"
        )
        assert response.status_code == 401

    def test_approval_status_nonexistent_returns_404(self, client, auth_headers):
        response = client.get(
            f"/api/v1/iceflows/promotions/{NONEXISTENT_PROMOTION_ID}/status",
            headers=auth_headers,
        )
        assert response.status_code == 404
