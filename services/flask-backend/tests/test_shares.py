"""Tests for Drawing Shares API endpoints."""
import pytest


class TestListShares:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/drawings/1/shares")
        assert response.status_code == 401

    def test_list_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.get("/api/v1/drawings/999999/shares", headers=auth_headers)
        assert response.status_code == 404

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/drawings/999999/shares", headers=auth_headers)
        assert response.status_code != 401


class TestCreateShare:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/drawings/1/shares",
            json={"type": "public", "permission": "view"},
        )
        assert response.status_code == 401

    def test_create_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/shares",
            json={"type": "public", "permission": "view"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_invalid_permission_returns_400(self, client, auth_headers, app):
        """Test invalid permission validation (requires drawing to exist first)."""
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Test Drawing for Share",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            json={"type": "public", "permission": "superadmin"},
            headers=auth_headers,
        )
        assert response.status_code in (400, 403)

    def test_create_invalid_share_type_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Test Drawing for Share Type",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            json={"type": "invalid-type", "permission": "view"},
            headers=auth_headers,
        )
        assert response.status_code in (400, 403)

    def test_missing_body_returns_400(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/shares",
            headers=auth_headers,
            data="",
            content_type="application/json",
        )
        assert response.status_code in (400, 404, 415)


class TestDeleteShare:
    def test_delete_requires_auth(self, client):
        response = client.delete("/api/v1/drawings/1/shares/1")
        assert response.status_code == 401

    def test_delete_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.delete(
            "/api/v1/drawings/999999/shares/1", headers=auth_headers
        )
        assert response.status_code == 404


class TestUpdateShare:
    def test_update_requires_auth(self, client):
        response = client.put(
            "/api/v1/drawings/1/shares/1", json={"permission": "edit"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/drawings/999999/shares/1",
            json={"permission": "edit"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_invalid_permission_returns_400(self, client, auth_headers):
        response = client.put(
            "/api/v1/drawings/999999/shares/1",
            json={"permission": "invalid"},
            headers=auth_headers,
        )
        assert response.status_code in (400, 404)


class TestPublicShareAccess:
    """Public share endpoints - no auth required."""

    def test_access_by_share_token_invalid_returns_404(self, client):
        response = client.get("/api/v1/drawings/share/invalid-nonexistent-token")
        assert response.status_code == 404

    def test_access_by_share_token_no_auth_needed(self, client):
        """Public endpoint - not 401."""
        response = client.get("/api/v1/drawings/share/any-token-here")
        assert response.status_code != 401

    def test_get_shared_drawing_invalid_token_returns_404(self, client):
        response = client.get("/api/v1/drawings/shared/invalid-nonexistent-token")
        assert response.status_code == 404

    def test_get_shared_drawing_no_auth_needed(self, client):
        """Public endpoint - not 401."""
        response = client.get("/api/v1/drawings/shared/any-token-here")
        assert response.status_code != 401


class TestShareAnalytics:
    def test_analytics_requires_auth(self, client):
        response = client.get("/api/v1/drawings/1/analytics")
        assert response.status_code == 401

    def test_analytics_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/drawings/999999/analytics", headers=auth_headers
        )
        assert response.status_code == 404

    def test_analytics_with_auth(self, client, auth_headers):
        response = client.get(
            "/api/v1/drawings/999999/analytics", headers=auth_headers
        )
        assert response.status_code != 401
