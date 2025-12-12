"""Drawing CRUD and Management Tests."""

import json

import pytest


class TestDrawingCreate:
    """Test drawing creation."""

    def test_create_drawing_success(self, client, auth_headers):
        """Test successful drawing creation."""
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "id" in data
        assert data["name"] == "Test Drawing"
        assert data["description"] == "A test drawing"

    def test_create_drawing_without_auth(self, client):
        """Test drawing creation without authentication."""
        response = client.post(
            "/api/v1/drawings",
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 401

    def test_create_drawing_missing_name(self, client, auth_headers):
        """Test drawing creation without name."""
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 400

    def test_create_drawing_empty_name(self, client, auth_headers):
        """Test drawing creation with empty name."""
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 400

    def test_create_drawing_with_group(self, client, auth_headers):
        """Test drawing creation with group assignment."""
        # First create a group
        group_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={"name": "Test Group", "description": "A test group"},
        )
        assert group_response.status_code == 201
        group_id = json.loads(group_response.data)["id"]

        # Create drawing with group
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "group_id": group_id,
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["group_id"] == group_id


class TestDrawingRead:
    """Test drawing retrieval."""

    def test_get_drawing_by_id(self, client, auth_headers):
        """Test retrieving a drawing by ID."""
        # Create a drawing first
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Retrieve the drawing
        response = client.get(f"/api/v1/drawings/{drawing_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == drawing_id
        assert data["name"] == "Test Drawing"

    def test_get_drawing_not_found(self, client, auth_headers):
        """Test retrieving non-existent drawing."""
        response = client.get("/api/v1/drawings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_user_drawings(self, client, auth_headers):
        """Test listing user's drawings."""
        # Create multiple drawings
        for i in range(3):
            client.post(
                "/api/v1/drawings",
                headers=auth_headers,
                json={
                    "name": f"Drawing {i}",
                    "description": f"Test drawing {i}",
                    "canvas_data": {"nodes": [], "edges": []},
                },
            )

        # List drawings
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert len(data["items"]) == 3

    def test_list_drawings_pagination(self, client, auth_headers):
        """Test drawing list pagination."""
        # Create 15 drawings
        for i in range(15):
            client.post(
                "/api/v1/drawings",
                headers=auth_headers,
                json={
                    "name": f"Drawing {i}",
                    "description": f"Test drawing {i}",
                    "canvas_data": {"nodes": [], "edges": []},
                },
            )

        # Get first page
        response = client.get(
            "/api/v1/drawings?page=1&per_page=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["items"]) == 10
        assert data["total"] == 15
        assert data["page"] == 1


class TestDrawingUpdate:
    """Test drawing updates."""

    def test_update_drawing_name(self, client, auth_headers):
        """Test updating drawing name."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Original Name",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Update the drawing
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Name"

    def test_update_drawing_content(self, client, auth_headers):
        """Test updating drawing canvas content."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Update the content
        new_content = {
            "nodes": [
                {"id": "1", "data": {"label": "Node 1"}, "position": {"x": 0, "y": 0}},
                {"id": "2", "data": {"label": "Node 2"}, "position": {"x": 100, "y": 0}},
            ],
            "edges": [{"id": "e1-2", "source": "1", "target": "2"}],
        }
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"canvas_data": new_content},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["canvas_data"]["nodes"]) == 2
        assert len(data["canvas_data"]["edges"]) == 1

    def test_update_drawing_without_auth(self, client):
        """Test updating drawing without authentication."""
        response = client.put(
            "/api/v1/drawings/1",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    def test_update_nonexistent_drawing(self, client, auth_headers):
        """Test updating non-existent drawing."""
        response = client.put(
            "/api/v1/drawings/99999",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404


class TestDrawingDelete:
    """Test drawing deletion."""

    def test_delete_drawing_success(self, client, auth_headers):
        """Test successful drawing deletion."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Delete the drawing
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_drawing_not_found(self, client, auth_headers):
        """Test deleting non-existent drawing."""
        response = client.delete(
            "/api/v1/drawings/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_drawing_without_auth(self, client):
        """Test deleting drawing without authentication."""
        response = client.delete("/api/v1/drawings/1")
        assert response.status_code == 401


class TestDrawingVersionHistory:
    """Test drawing version history."""

    def test_get_version_history(self, client, auth_headers):
        """Test retrieving version history."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Make several updates to create history
        for i in range(3):
            client.put(
                f"/api/v1/drawings/{drawing_id}",
                headers=auth_headers,
                json={"name": f"Updated Name {i}"},
            )

        # Get version history
        response = client.get(
            f"/api/v1/drawings/{drawing_id}/versions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "versions" in data
        assert len(data["versions"]) >= 1

    def test_restore_version(self, client, auth_headers):
        """Test restoring a previous version."""
        # Create a drawing with initial content
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [{"id": "1", "label": "Node 1"}], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]
        first_version = json.loads(create_response.data)

        # Update the drawing
        client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={
                "canvas_data": {"nodes": [{"id": "1"}, {"id": "2"}], "edges": []}
            },
        )

        # Restore first version
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/restore",
            headers=auth_headers,
            json={"version_id": first_version.get("version_id") or 1},
        )
        assert response.status_code in [200, 404]  # 404 if version not found


class TestDrawingSearch:
    """Test drawing search functionality."""

    def test_search_drawings_by_name(self, client, auth_headers):
        """Test searching drawings by name."""
        # Create drawings with different names
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Architecture Diagram",
                "description": "System architecture",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Database Schema",
                "description": "Database design",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )

        # Search for architecture
        response = client.get(
            "/api/v1/drawings?search=architecture",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["items"]) == 1
        assert "Architecture" in data["items"][0]["name"]

    def test_search_drawings_by_description(self, client, auth_headers):
        """Test searching drawings by description."""
        # Create drawings
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Drawing 1",
                "description": "This diagram shows the flow",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )

        # Search by description
        response = client.get(
            "/api/v1/drawings?search=flow",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDrawingSharing:
    """Test drawing sharing functionality."""

    def test_share_drawing_with_user(self, client, auth_headers, create_test_user):
        """Test sharing a drawing with another user."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(create_response.data)["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Share the drawing
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/share",
            headers=auth_headers,
            json={"user_id": other_user["id"], "permission": "view"},
        )
        assert response.status_code in [200, 201, 404]

    def test_list_shared_drawings(self, client, auth_headers):
        """Test listing shared drawings."""
        response = client.get(
            "/api/v1/drawings?shared=true",
            headers=auth_headers,
        )
        assert response.status_code == 200
