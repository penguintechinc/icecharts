"""Tests for Shape Libraries API endpoints."""
import pytest


class TestListLibraries:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/libraries")
        assert response.status_code == 401

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/libraries", headers=auth_headers)
        assert response.status_code != 401
        data = response.get_json()
        assert "libraries" in data

    def test_list_returns_pagination_info(self, client, auth_headers):
        response = client.get("/api/v1/libraries", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "total" in data
        assert "page" in data

    def test_list_with_search(self, client, auth_headers):
        response = client.get(
            "/api/v1/libraries?search=mylib", headers=auth_headers
        )
        assert response.status_code == 200


class TestCreateLibrary:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/libraries", json={"name": "My Library"}
        )
        assert response.status_code == 401

    def test_create_missing_name_returns_400(self, client, auth_headers):
        response = client.post(
            "/api/v1/libraries", json={}, headers=auth_headers
        )
        assert response.status_code == 400

    def test_create_with_valid_data(self, client, auth_headers):
        payload = {
            "name": "Test Library",
            "description": "A test shape library",
            "is_public": False,
        }
        response = client.post("/api/v1/libraries", json=payload, headers=auth_headers)
        assert response.status_code in (200, 201)
        if response.status_code == 201:
            data = response.get_json()
            assert "library" in data
            assert data["library"]["name"] == "Test Library"

    def test_create_missing_body_returns_400(self, client, auth_headers):
        response = client.post("/api/v1/libraries", json=None, headers=auth_headers)
        assert response.status_code == 400


class TestGetLibrary:
    def test_get_requires_auth(self, client):
        response = client.get("/api/v1/libraries/1")
        assert response.status_code == 401

    def test_get_nonexistent_returns_404(self, client, auth_headers):
        response = client.get("/api/v1/libraries/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_existing_library(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Test Lib for Get",
                description="description",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.get(f"/api/v1/libraries/{lib_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "library" in data


class TestUpdateLibrary:
    def test_update_requires_auth(self, client):
        response = client.put(
            "/api/v1/libraries/1", json={"name": "Updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/libraries/999999",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_missing_body_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Test Lib for Update",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.put(
            f"/api/v1/libraries/{lib_id}", json=None, headers=auth_headers
        )
        assert response.status_code == 400


class TestDeleteLibrary:
    def test_delete_requires_auth(self, client):
        response = client.delete("/api/v1/libraries/1")
        assert response.status_code == 401

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete("/api/v1/libraries/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_existing_library(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Library to Delete",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.delete(f"/api/v1/libraries/{lib_id}", headers=auth_headers)
        assert response.status_code == 200


class TestListShapes:
    def test_list_shapes_requires_auth(self, client):
        response = client.get("/api/v1/libraries/1/shapes")
        assert response.status_code == 401

    def test_list_shapes_nonexistent_library_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/libraries/999999/shapes", headers=auth_headers
        )
        assert response.status_code == 404

    def test_list_shapes_existing_library(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Library for Shape List",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.get(f"/api/v1/libraries/{lib_id}/shapes", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "shapes" in data


class TestAddShape:
    def test_add_shape_requires_auth(self, client):
        response = client.post(
            "/api/v1/libraries/1/shapes",
            json={"name": "My Shape", "shape_data": {}},
        )
        assert response.status_code == 401

    def test_add_shape_nonexistent_library_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/libraries/999999/shapes",
            json={"name": "My Shape", "shape_data": {"type": "rect"}},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_add_shape_missing_name_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Library for Add Shape",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.post(
            f"/api/v1/libraries/{lib_id}/shapes",
            json={"shape_data": {"type": "rect"}},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_add_shape_with_valid_data(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Library for Valid Add Shape",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        payload = {
            "name": "My Custom Shape",
            "shape_data": {"type": "rect", "width": 100, "height": 50},
            "description": "A custom shape",
        }
        response = client.post(
            f"/api/v1/libraries/{lib_id}/shapes",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code in (200, 201)


class TestGetShape:
    def test_get_shape_requires_auth(self, client):
        response = client.get("/api/v1/libraries/1/shapes/1")
        assert response.status_code == 401

    def test_get_shape_nonexistent_library_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/libraries/999999/shapes/1", headers=auth_headers
        )
        assert response.status_code == 404


class TestUpdateShape:
    def test_update_shape_requires_auth(self, client):
        response = client.put(
            "/api/v1/libraries/1/shapes/1", json={"name": "Updated"}
        )
        assert response.status_code == 401

    def test_update_shape_nonexistent_library_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/libraries/999999/shapes/1",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteShape:
    def test_delete_shape_requires_auth(self, client):
        response = client.delete("/api/v1/libraries/1/shapes/1")
        assert response.status_code == 401

    def test_delete_shape_nonexistent_library_returns_404(self, client, auth_headers):
        response = client.delete(
            "/api/v1/libraries/999999/shapes/1", headers=auth_headers
        )
        assert response.status_code == 404


class TestDuplicateLibrary:
    def test_duplicate_requires_auth(self, client):
        response = client.post("/api/v1/libraries/1/duplicate")
        assert response.status_code == 401

    def test_duplicate_nonexistent_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/libraries/999999/duplicate", headers=auth_headers
        )
        assert response.status_code == 404

    def test_duplicate_existing_library(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            lib_id = db.shape_libraries.insert(
                name="Library to Duplicate",
                owner_id=1,
                is_public=False,
            )
            db.commit()

        response = client.post(
            f"/api/v1/libraries/{lib_id}/duplicate", headers=auth_headers
        )
        assert response.status_code in (200, 201)
        data = response.get_json()
        assert "library" in data
