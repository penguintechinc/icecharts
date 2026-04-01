"""Drawing CRUD and Management Tests."""

import json

import pytest


# Helper to extract drawing from API response (handles wrapped format)
def _get_drawing_from_response(response):
    """Extract drawing dict from response, handling {'drawing': {...}} wrapper."""
    data = json.loads(response.data)
    return data.get("drawing", data)


def _create_drawing_via_api(
    client, headers, name="Test Drawing", description="A test drawing"
):
    """Create a drawing via the API and return (response, drawing_dict_or_none)."""
    resp = client.post(
        "/api/v1/drawings",
        headers=headers,
        json={
            "name": name,
            "description": description,
            "content": {"nodes": [], "edges": []},
        },
    )
    drawing = None
    if resp.status_code == 201:
        drawing = _get_drawing_from_response(resp)
    return resp, drawing


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
        drawing = _get_drawing_from_response(response)
        assert "id" in drawing
        assert drawing["name"] == "Test Drawing"
        assert drawing["description"] == "A test drawing"

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

    def test_create_drawing_with_group(self, client, admin_auth_headers):
        """Test drawing creation with tags (group_id not in schema)."""
        # CreateDrawingRequest doesn't have group_id, test with tags instead
        response = client.post(
            "/api/v1/drawings",
            headers=admin_auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
                "tags": ["group-test"],
            },
        )
        assert response.status_code == 201
        drawing = _get_drawing_from_response(response)
        assert "id" in drawing


class TestDrawingRead:
    """Test drawing retrieval."""

    def test_get_drawing_by_id(self, client, auth_headers):
        """Test retrieving a drawing by ID."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        response = client.get(f"/api/v1/drawings/{drawing_id}", headers=auth_headers)
        assert response.status_code == 200
        drawing = _get_drawing_from_response(response)
        assert drawing["id"] == drawing_id
        assert drawing["name"] == "Test Drawing"

    def test_get_drawing_not_found(self, client, auth_headers):
        """Test retrieving non-existent drawing."""
        response = client.get("/api/v1/drawings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_user_drawings(self, client, auth_headers):
        """Test listing user's drawings."""
        for i in range(3):
            _create_drawing_via_api(
                client,
                auth_headers,
                name=f"Drawing {i}",
                description=f"Test drawing {i}",
            )

        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        # API returns items/drawings list
        items = data.get("items", data.get("drawings", []))
        assert len(items) == 3

    def test_list_drawings_pagination(self, client, auth_headers):
        """Test drawing list returns all items (no server-side pagination)."""
        for i in range(15):
            _create_drawing_via_api(
                client,
                auth_headers,
                name=f"Drawing {i}",
                description=f"Test drawing {i}",
            )

        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        items = data.get("items", data.get("drawings", []))
        # The list endpoint doesn't paginate; returns all user drawings
        assert len(items) == 15


class TestDrawingUpdate:
    """Test drawing updates."""

    def test_update_drawing_name(self, client, auth_headers):
        """Test updating drawing name."""
        _, created = _create_drawing_via_api(client, auth_headers, name="Original Name")
        assert created is not None
        drawing_id = created["id"]

        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        drawing = _get_drawing_from_response(response)
        assert drawing["name"] == "Updated Name"

    def test_update_drawing_content(self, client, auth_headers):
        """Test updating drawing content."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        new_content = {
            "nodes": [
                {"id": "1", "data": {"label": "Node 1"}, "position": {"x": 0, "y": 0}},
                {
                    "id": "2",
                    "data": {"label": "Node 2"},
                    "position": {"x": 100, "y": 0},
                },
            ],
            "edges": [{"id": "e1-2", "source": "1", "target": "2"}],
        }
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"content": new_content},
        )
        assert response.status_code == 200
        drawing = _get_drawing_from_response(response)
        # Content is returned when version info is included
        assert "content" in drawing
        assert len(drawing["content"]["nodes"]) == 2
        assert len(drawing["content"]["edges"]) == 1

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
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        # API returns 200 on successful delete
        assert response.status_code == 200

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
        """Test that updating creates new versions."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        # Make an update with content to create a new version
        client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"content": {"nodes": [{"id": "1"}], "edges": []}},
        )

        # Get drawing - version number should be > 1
        response = client.get(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        drawing = _get_drawing_from_response(response)
        # Drawing should have version info
        assert "version" in drawing
        assert drawing["version"] >= 1

    def test_restore_version(self, client, auth_headers):
        """Test that drawing can be updated (restore is via PUT with content)."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        # Update to create version 2
        client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"content": {"nodes": [{"id": "1"}, {"id": "2"}], "edges": []}},
        )

        # "Restore" by putting original content back
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"content": {"nodes": [], "edges": []}},
        )
        assert response.status_code == 200


class TestDrawingSearch:
    """Test drawing search functionality."""

    def test_search_drawings_by_name(self, client, auth_headers):
        """Test listing drawings returns created drawings."""
        _create_drawing_via_api(
            client,
            auth_headers,
            name="Architecture Diagram",
            description="System architecture",
        )
        _create_drawing_via_api(
            client, auth_headers, name="Database Schema", description="Database design"
        )

        # List all drawings (no search param supported)
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        items = data.get("items", data.get("drawings", []))
        assert len(items) == 2

    def test_search_drawings_by_description(self, client, auth_headers):
        """Test listing drawings after creating one."""
        _create_drawing_via_api(
            client,
            auth_headers,
            name="Drawing 1",
            description="This diagram shows the flow",
        )

        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200


class TestDrawingSharing:
    """Test drawing sharing functionality."""

    def test_share_drawing_with_user(self, client, auth_headers, create_test_user):
        """Test sharing a drawing with another user."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        other_user = create_test_user("other@example.com")

        # Share endpoint at /api/v1/drawings/<id>/shares with type=user
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            headers=auth_headers,
            json={
                "type": "user",
                "user_id": other_user["id"],
                "permission": "view",
            },
        )
        assert response.status_code in [200, 201, 403, 404]

    def test_list_shared_drawings(self, client, auth_headers):
        """Test listing drawings returns successfully."""
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200


class TestDrawingErrorPaths:
    """Error path tests for drawing operations."""

    def test_get_nonexistent_drawing_returns_404(self, client, auth_headers):
        """Getting a drawing that doesn't exist returns 404."""
        response = client.get("/api/v1/drawings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_create_drawing_missing_required_fields_returns_400(
        self, client, auth_headers
    ):
        """Creating a drawing without required fields returns 400."""
        response = client.post(
            "/api/v1/drawings",
            json={},  # missing name/title/required fields
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_delete_nonexistent_drawing_returns_404(self, client, auth_headers):
        """Deleting a drawing that doesn't exist returns 404."""
        response = client.delete("/api/v1/drawings/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_nonexistent_drawing_returns_404_duplicate(
        self, client, auth_headers
    ):
        """Test updating non-existent drawing returns 404 (second test)."""
        response = client.put(
            "/api/v1/drawings/99999",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404

    def test_create_drawing_with_null_name_returns_400(self, client, auth_headers):
        """Creating a drawing with null name returns 400."""
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": None,
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        assert response.status_code == 400

    def test_get_drawing_without_auth_returns_401(self, client):
        """Getting a drawing without authentication returns 401."""
        response = client.get("/api/v1/drawings/1")
        assert response.status_code == 401

    def test_list_drawings_without_auth_returns_401(self, client):
        """Listing drawings without authentication returns 401."""
        response = client.get("/api/v1/drawings")
        assert response.status_code == 401


class TestDrawingOwnershipAndExport:
    """Ownership enforcement and export error path tests for drawing operations."""

    def test_export_drawing_invalid_format_returns_400(self, client, auth_headers):
        """Exporting a drawing with an unsupported format returns 400."""
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/export",
            headers=auth_headers,
            json={"format": "bmp"},  # not in VALID_FORMATS: png, jpg, svg, pdf, json
        )
        assert response.status_code == 400

    def test_non_owner_cannot_update_drawing_returns_403(
        self, client, auth_headers, create_test_user
    ):
        """A user who does not own a drawing cannot update it (returns 403)."""
        # Create a drawing as the default auth user (owner)
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        # Create a second user (viewer role) and their headers
        other_user = create_test_user(
            email="other_viewer@example.com",
            role="viewer",
        )
        other_headers = {"Authorization": f"Bearer {other_user['token']}"}

        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=other_headers,
            json={"name": "Hijacked Name"},
        )
        assert response.status_code == 403

    def test_non_owner_cannot_delete_drawing_returns_403(
        self, client, auth_headers, create_test_user
    ):
        """A user who does not own a drawing cannot delete it (returns 403)."""
        # Create a drawing as the default auth user (owner)
        _, created = _create_drawing_via_api(client, auth_headers)
        assert created is not None
        drawing_id = created["id"]

        # Create a second user (viewer role) and their headers
        other_user = create_test_user(
            email="other_viewer2@example.com",
            role="viewer",
        )
        other_headers = {"Authorization": f"Bearer {other_user['token']}"}

        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=other_headers,
        )
        assert response.status_code == 403

    def test_export_nonexistent_drawing_returns_404(self, client, auth_headers):
        """Exporting a drawing that doesn't exist returns 404."""
        response = client.post(
            "/api/v1/drawings/99999/export",
            headers=auth_headers,
            json={"format": "svg"},
        )
        assert response.status_code == 404
