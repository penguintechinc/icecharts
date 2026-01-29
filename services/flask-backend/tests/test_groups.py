"""Group Management Tests."""

import json

import pytest


class TestGroupCreate:
    """Test group creation."""

    def test_create_group_success(self, client, admin_auth_headers):
        """Test successful group creation (requires admin/maintainer role)."""
        response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "group" in data
        assert "id" in data["group"]
        assert data["group"]["name"] == "Test Group"
        assert data["group"]["description"] == "A test group"

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

    def test_create_group_viewer_forbidden(self, client, auth_headers):
        """Test group creation with viewer role is forbidden."""
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        assert response.status_code == 403

    def test_create_group_missing_name(self, client, admin_auth_headers):
        """Test group creation without name."""
        response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={"description": "A test group"},
        )
        assert response.status_code == 400

    def test_create_group_empty_name(self, client, admin_auth_headers):
        """Test group creation with empty name."""
        response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "",
                "description": "A test group",
            },
        )
        assert response.status_code == 400

    def test_create_duplicate_group_name(self, client, admin_auth_headers):
        """Test creating group with duplicate name."""
        # Create first group
        client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "First group",
            },
        )

        # Try to create duplicate
        response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "Second group",
            },
        )
        # Depending on implementation, may be 409 (conflict) or allowed
        assert response.status_code in [201, 409]


class TestGroupRead:
    """Test group retrieval."""

    def test_get_group_by_id(self, client, admin_auth_headers):
        """Test retrieving a group by ID."""
        # Create a group (requires admin/maintainer)
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Retrieve the group (admin can see all groups)
        response = client.get(
            f"/api/v1/groups/{group_id}", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "group" in data
        assert data["group"]["id"] == group_id
        assert data["group"]["name"] == "Test Group"

    def test_get_group_not_found(self, client, admin_auth_headers):
        """Test retrieving non-existent group."""
        response = client.get(
            "/api/v1/groups/99999", headers=admin_auth_headers
        )
        assert response.status_code == 404

    def test_get_group_viewer_not_member_forbidden(self, client, auth_headers,
                                                   admin_auth_headers):
        """Test that a viewer who is not a group member cannot access it."""
        # Create a group as admin
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Private Group",
                "description": "A private group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Viewer (not a member) tries to access
        response = client.get(
            f"/api/v1/groups/{group_id}", headers=auth_headers
        )
        assert response.status_code == 403

    def test_list_groups_as_admin(self, client, admin_auth_headers):
        """Test listing groups as admin (admin sees all groups)."""
        # Create multiple groups
        for i in range(3):
            client.post(
                "/api/v1/groups",
                headers=admin_auth_headers,
                json={
                    "name": f"Group {i}",
                    "description": f"Test group {i}",
                },
            )

        # List groups as admin
        response = client.get("/api/v1/groups", headers=admin_auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "groups" in data
        assert len(data["groups"]) == 3

    def test_list_groups_pagination(self, client, admin_auth_headers):
        """Test group list pagination."""
        # Create 15 groups
        for i in range(15):
            client.post(
                "/api/v1/groups",
                headers=admin_auth_headers,
                json={
                    "name": f"Group {i}",
                    "description": f"Test group {i}",
                },
            )

        # Get first page
        response = client.get(
            "/api/v1/groups?page=1&per_page=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["groups"]) == 10
        assert data["total"] == 15


class TestGroupUpdate:
    """Test group updates."""

    def test_update_group_name(self, client, admin_auth_headers):
        """Test updating group name."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Original Name",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Update the group (admin or group admin can update)
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["group"]["name"] == "Updated Name"

    def test_update_group_description(self, client, admin_auth_headers):
        """Test updating group description."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "Original description",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Update the description
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["group"]["description"] == "Updated description"

    def test_update_group_without_auth(self, client):
        """Test updating group without authentication."""
        response = client.put(
            "/api/v1/groups/1",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    def test_update_group_viewer_forbidden(self, client, auth_headers,
                                           admin_auth_headers):
        """Test that a viewer cannot update a group."""
        # Create a group as admin
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Viewer tries to update
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 403

    def test_update_nonexistent_group(self, client, admin_auth_headers):
        """Test updating non-existent group."""
        response = client.put(
            "/api/v1/groups/99999",
            headers=admin_auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 404


class TestGroupDelete:
    """Test group deletion."""

    def test_delete_group_success(self, client, admin_auth_headers):
        """Test successful group deletion."""
        # Create a group
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Delete the group (returns 200, not 204)
        response = client.delete(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data

        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_group_not_found(self, client, admin_auth_headers):
        """Test deleting non-existent group."""
        response = client.delete(
            "/api/v1/groups/99999",
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_delete_group_without_auth(self, client):
        """Test deleting group without authentication."""
        response = client.delete("/api/v1/groups/1")
        assert response.status_code == 401

    def test_delete_group_viewer_forbidden(self, client, auth_headers,
                                           admin_auth_headers):
        """Test that a viewer cannot delete a group."""
        # Create a group as admin
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["group"]["id"]

        # Viewer tries to delete
        response = client.delete(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestGroupMembers:
    """Test group member management."""

    def test_add_member_to_group(self, client, admin_auth_headers,
                                 create_test_user):
        """Test adding a member to a group."""
        # Create a group as admin (admin becomes group admin member)
        group_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["group"]["id"]

        # Create another user
        other_user = create_test_user("member@example.com")

        # Add member to group (admin auth has permissions)
        response = client.post(
            f"/api/v1/groups/{group_id}/members",
            headers=admin_auth_headers,
            json={"user_id": other_user["id"], "role": "member"},
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "message" in data

    def test_add_member_viewer_forbidden(self, client, auth_headers,
                                         admin_auth_headers,
                                         create_test_user):
        """Test that a viewer cannot add members to a group."""
        # Create a group as admin
        group_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["group"]["id"]

        # Create another user
        other_user = create_test_user("member@example.com")

        # Viewer tries to add member
        response = client.post(
            f"/api/v1/groups/{group_id}/members",
            headers=auth_headers,
            json={"user_id": other_user["id"], "role": "member"},
        )
        assert response.status_code == 403

    def test_list_group_members(self, client, admin_auth_headers):
        """Test listing group members."""
        # Create a group (creator becomes admin member automatically)
        group_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["group"]["id"]

        # List members (admin can access)
        response = client.get(
            f"/api/v1/groups/{group_id}/members",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "members" in data
        assert "total" in data
        # Creator is automatically added as admin member
        assert data["total"] >= 1

    def test_list_group_members_viewer_not_member_forbidden(
        self, client, auth_headers, admin_auth_headers
    ):
        """Test that a viewer not in the group cannot list members."""
        # Create a group as admin
        group_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["group"]["id"]

        # Viewer (not a member) tries to list members
        response = client.get(
            f"/api/v1/groups/{group_id}/members",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_remove_member_from_group(self, client, admin_auth_headers,
                                      create_test_user):
        """Test removing a member from a group."""
        # Create a group as admin
        group_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(group_response.data)["group"]["id"]

        # Create and add a user
        other_user = create_test_user("member@example.com")
        client.post(
            f"/api/v1/groups/{group_id}/members",
            headers=admin_auth_headers,
            json={"user_id": other_user["id"], "role": "member"},
        )

        # Remove member (returns 200 with JSON, not 204)
        response = client.delete(
            f"/api/v1/groups/{group_id}/members/{other_user['id']}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "message" in data
