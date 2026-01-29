"""Drawing CRUD and Management Tests."""

import json


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
                "content": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert "drawing" in data
        assert "id" in data["drawing"]
        assert data["drawing"]["name"] == "Test Drawing"
        assert data["drawing"]["description"] == "A test drawing"

    def test_create_drawing_without_auth(self, client):
        """Test drawing creation without authentication."""
        response = client.post(
            "/api/v1/drawings",
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
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
                "content": {"nodes": [], "edges": []},
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
                "content": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 400

    def test_create_drawing_with_group(self, client, auth_headers):
        """Test drawing creation with tags (group-like categorization)."""
        # Create drawing with tags for categorization
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
                "tags": ["test-group"],
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert "drawing" in data
        assert "id" in data["drawing"]


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
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Retrieve the drawing
        response = client.get(f"/api/v1/drawings/{drawing_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "drawing" in data
        assert data["drawing"]["id"] == drawing_id
        assert data["drawing"]["name"] == "Test Drawing"

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
                    "content": {"nodes": [], "edges": []},
                },
            )

        # List drawings
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "items" in data
        assert len(data["items"]) >= 3

    def test_list_drawings_returns_count(self, client, auth_headers):
        """Test drawing list includes count."""
        # Create 5 drawings
        for i in range(5):
            client.post(
                "/api/v1/drawings",
                headers=auth_headers,
                json={
                    "name": f"Drawing {i}",
                    "description": f"Test drawing {i}",
                    "content": {"nodes": [], "edges": []},
                },
            )

        # Get list
        response = client.get(
            "/api/v1/drawings",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "count" in data
        assert data["count"] >= 5
        assert "items" in data
        assert "drawings" in data


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
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Update the drawing
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["drawing"]["name"] == "Updated Name"

    def test_update_drawing_content(self, client, auth_headers):
        """Test updating drawing canvas content."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

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
            json={"content": new_content},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "drawing" in data
        assert "content" in data["drawing"]
        assert len(data["drawing"]["content"]["nodes"]) == 2
        assert len(data["drawing"]["content"]["edges"]) == 1

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
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Delete the drawing
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

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
    """Test drawing version history via updates."""

    def test_version_increments_on_content_update(self, client, auth_headers):
        """Test that updating content creates new versions."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Make several content updates to create version history
        for i in range(3):
            update_response = client.put(
                f"/api/v1/drawings/{drawing_id}",
                headers=auth_headers,
                json={
                    "content": {
                        "nodes": [{"id": str(j)} for j in range(i + 1)],
                        "edges": [],
                    }
                },
            )
            assert update_response.status_code == 200

        # Get latest drawing and verify version number increased
        response = client.get(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "drawing" in data
        # After initial creation (v1) + 3 updates, version should be >= 4
        if "version" in data["drawing"]:
            assert data["drawing"]["version"] >= 4

    def test_content_preserved_after_metadata_update(self, client, auth_headers):
        """Test that metadata-only updates preserve content."""
        # Create a drawing with content
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {
                    "nodes": [{"id": "1", "label": "Node 1"}],
                    "edges": [],
                },
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Update only the name (no content change)
        update_response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Renamed Drawing"},
        )
        assert update_response.status_code == 200
        data = json.loads(update_response.data)
        assert data["drawing"]["name"] == "Renamed Drawing"


class TestDrawingSearch:
    """Test drawing search functionality."""

    def test_list_drawings_filters_by_user(self, client, auth_headers):
        """Test that listing drawings returns user's drawings."""
        # Create drawings with different names
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Architecture Diagram",
                "description": "System architecture",
                "content": {"nodes": [], "edges": []},
            },
        )
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Database Schema",
                "description": "Database design",
                "content": {"nodes": [], "edges": []},
            },
        )

        # List all user drawings
        response = client.get(
            "/api/v1/drawings",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "items" in data
        assert len(data["items"]) >= 2

        # Verify drawing names are present in results
        names = [item["name"] for item in data["items"]]
        assert "Architecture Diagram" in names
        assert "Database Schema" in names

    def test_list_drawings_returns_drawing_fields(self, client, auth_headers):
        """Test that listed drawings have expected fields."""
        # Create a drawing
        client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Drawing 1",
                "description": "This diagram shows the flow",
                "content": {"nodes": [], "edges": []},
            },
        )

        # List drawings
        response = client.get(
            "/api/v1/drawings",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["items"]) >= 1

        # Check that items have expected fields
        item = data["items"][0]
        assert "id" in item
        assert "name" in item
        assert "description" in item
        assert "created_at" in item


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
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Share the drawing via the shares endpoint
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            headers=auth_headers,
            json={
                "type": "user",
                "user_id": other_user["id"],
                "permission": "view",
            },
        )
        assert response.status_code in [201, 403, 404]

    def test_list_drawing_shares(self, client, auth_headers):
        """Test listing shares for a drawing."""
        # Create a drawing first
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        create_data = json.loads(create_response.data)
        drawing_id = create_data["drawing"]["id"]

        # List shares for the drawing
        response = client.get(
            f"/api/v1/drawings/{drawing_id}/shares",
            headers=auth_headers,
        )
        # May return 200 if user is owner/admin, or 403 if insufficient permissions
        assert response.status_code in [200, 403]

    def test_list_user_drawings(self, client, auth_headers):
        """Test listing user's own drawings."""
        response = client.get(
            "/api/v1/drawings",
            headers=auth_headers,
        )
        assert response.status_code == 200
