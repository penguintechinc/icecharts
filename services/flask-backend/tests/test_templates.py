"""Tests for Drawing Templates API endpoints."""
import pytest


class TestListTemplates:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/templates")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/templates", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "templates" in data or "error" in data

    def test_list_returns_success(self, client, auth_headers):
        response = client.get("/api/v1/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["templates"], list)

    def test_list_with_search_filter(self, client, auth_headers):
        response = client.get(
            "/api/v1/templates?search=flowchart", headers=auth_headers
        )
        assert response.status_code == 200


class TestGetTemplate:
    def test_get_requires_auth(self, client):
        response = client.get("/api/v1/templates/999")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get("/api/v1/templates/999999", headers=auth_headers)
        assert response.status_code == 404


class TestCreateTemplate:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/templates",
            json={"name": "My Template", "drawing_id": "1"},
        )
        assert response.status_code == 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        payload = {"drawing_id": "1"}
        response = client.post("/api/v1/templates", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_missing_drawing_id_returns_400(self, client, auth_headers):
        payload = {"name": "My Template"}
        response = client.post("/api/v1/templates", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_create_with_nonexistent_drawing_returns_404(self, client, auth_headers):
        payload = {
            "name": "My Template",
            "drawing_id": "999999",
            "description": "A test template",
        }
        response = client.post("/api/v1/templates", json=payload, headers=auth_headers)
        assert response.status_code == 404

    def test_create_with_valid_drawing(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Drawing for Template",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        payload = {
            "name": "Template from Drawing",
            "drawing_id": str(drawing_id),
            "description": "A template",
            "is_public": False,
        }
        response = client.post("/api/v1/templates", json=payload, headers=auth_headers)
        assert response.status_code != 401


class TestUpdateTemplate:
    def test_update_requires_auth(self, client):
        response = client.put(
            "/api/v1/templates/1", json={"name": "Updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/templates/999999",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteTemplate:
    def test_delete_requires_auth(self, client):
        response = client.delete("/api/v1/templates/1")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete("/api/v1/templates/999999", headers=auth_headers)
        assert response.status_code == 404


class TestUseTemplate:
    def test_use_requires_auth(self, client):
        response = client.post(
            "/api/v1/templates/1/use",
            json={"name": "My Drawing from Template"},
        )
        assert response.status_code == 401

    def test_use_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/templates/999999/use",
            json={"name": "My Drawing from Template"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_use_missing_name_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            template_id = db.drawings.insert(
                tenant_id=1,
                title="Test Template",
                owner_id=1,
                user_id=1,
                created_by_id=1,
                is_template=True,
                is_public=True,
            )
            db.commit()

        response = client.post(
            f"/api/v1/templates/{template_id}/use",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400
