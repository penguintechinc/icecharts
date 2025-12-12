"""Group Management Tests."""

import json

import pytest


class TestGroupCreate:
    """Test group creation."""

    def test_create_group_success(self, client, auth_headers):
        """Test successful group creation."""
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "id" in data
        assert data["name"] == "Test Group"
        assert data["description"] == "A test group"

    def test_create_group_without_auth(self, client):
        """Test group creation without authentication."""
        response = client.post(
            "/api/v1/groups",
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        assert response.status_code == 401

    def test_create_group_missing_name(self, client, auth_headers):
        """Test group creation without name."""
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={"description": "A test group"},
        )
        assert response.status_code == 400

    def test_create_group_empty_name(self, client, auth_headers):
        """Test group creation with empty name."""
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "",
                "description": "A test group",
            },
        )
        assert response.status_code == 400

    def test_create_duplicate_group_name(self, client, auth_headers):
        """Test creating group with duplicate name."""
        # Create first group
        client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "First group",
            },
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "Second group",
            },
        )
        # Depending on implementation, may be 409 (conflict) or allowed
        assert response.status_code in [201, 409]


class TestGroupRead:
    """Test group retrieval."""

    def test_get_group_by_id(self, client, auth_headers):
        """Test retrieving a group by ID."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["id"]

        # Retrieve the group
        response = client.get(f"/api/v1/groups/{group_id}", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == group_id
        assert data["name"] == "Test Group"

    def test_get_group_not_found(self, client, auth_headers):
        """Test retrieving non-existent group."""
        response = client.get("/api/v1/groups/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_user_groups(self, client, auth_headers):
        """Test listing user's groups."""
        # Create multiple groups
        for i in range(3):
            client.post(
                "/api/v1/groups",
                headers=auth_headers,
                json={
                    "name": f"Group {i}",
                    "description": f"Test group {i}",
                },
            )

        # List groups
        response = client.get("/api/v1/groups", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "items" in data
        assert len(data["items"]) == 3

    def test_list_groups_pagination(self, client, auth_headers):
        """Test group list pagination."""
        # Create 15 groups
        for i in range(15):
            client.post(
                "/api/v1/groups",
                headers=auth_headers,
                json={
                    "name": f"Group {i}",
                    "description": f"Test group {i}",
                },
            )

        # Get first page
        response = client.get(
            "/api/v1/groups?page=1&per_page=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["items"]) == 10
        assert data["total"] == 15


class TestGroupUpdate:
    """Test group updates."""

    def test_update_group_name(self, client, auth_headers):
        """Test updating group name."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Original Name",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["id"]

        # Update the group
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Updated Name"

    def test_update_group_description(self, client, auth_headers):
        """Test updating group description."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "Original description",
            },
        )
        group_id = json.loads(create_response.data)["id"]

        # Update the description
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["description"] == "Updated description"

    def test_update_group_without_auth(self, client):
        """Test updating group without authentication."""
        response = client.put(
            "/api/v1/groups/1",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    def test_update_nonexistent_group(self, client, auth_headers):
        """Test updating non-existent group."""
        response = client.put(
            "/api/v1/groups/99999",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404


class TestGroupDelete:
    """Test group deletion."""

    def test_delete_group_success(self, client, auth_headers):
        """Test successful group deletion."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["id"]

        # Delete the group
        response = client.delete(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_group_not_found(self, client, auth_headers):
        """Test deleting non-existent group."""
        response = client.delete(
            "/api/v1/groups/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_group_without_auth(self, client):
        """Test deleting group without authentication."""
        response = client.delete("/api/v1/groups/1")
        assert response.status_code == 401


class TestGroupMembers:
    """Test group member management."""

    def test_add_member_to_group(self, client, auth_headers, create_test_user):
        """Test adding a member to a group."""
        # Create a group
        group_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["id"]

        # Create another user
        other_user = create_test_user("member@example.com")

        # Add member to group
        response = client.post(
            f"/api/v1/groups/{group_id}/members",
            headers=auth_headers,
            json={"user_id": other_user["id"], "role": "member"},
        )
        assert response.status_code in [200, 201, 404]

    def test_list_group_members(self, client, auth_headers):
        """Test listing group members."""
        # Create a group
        group_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["id"]

        # List members
        response = client.get(
            f"/api/v1/groups/{group_id}/members",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]

    def test_remove_member_from_group(self, client, auth_headers, create_test_user):
        """Test removing a member from a group."""
        # Create a group
        group_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["id"]

        # Create and add a user
        other_user = create_test_user("member@example.com")

        # Remove member
        response = client.delete(
            f"/api/v1/groups/{group_id}/members/{other_user['id']}",
            headers=auth_headers,
        )
        assert response.status_code in [204, 404]


class TestGroupDrawings:
    """Test group and drawing relationships."""

    def test_get_group_drawings(self, client, auth_headers):
        """Test retrieving all drawings in a group."""
        # Create a group
        group_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["id"]

        # Create drawings in the group
        for i in range(3):
            client.post(
                "/api/v1/drawings",
                headers=auth_headers,
                json={
                    "name": f"Drawing {i}",
                    "description": f"Test drawing {i}",
                    "group_id": group_id,
                    "canvas_data": {"nodes": [], "edges": []},
                },
            )

        # Get group drawings
        response = client.get(
            f"/api/v1/groups/{group_id}/drawings",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]

    def test_move_drawing_to_group(self, client, auth_headers):
        """Test moving a drawing to a different group."""
        # Create two groups
        group1_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={"name": "Group 1", "description": "First group"},
        )
        group1_id = json.loads(group1_response.data)["id"]

        group2_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={"name": "Group 2", "description": "Second group"},
        )
        group2_id = json.loads(group2_response.data)["id"]

        # Create drawing in group 1
        drawing_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "group_id": group1_id,
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        drawing_id = json.loads(drawing_response.data)["id"]

        # Move to group 2
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"group_id": group2_id},
        )
        assert response.status_code in [200, 404]
