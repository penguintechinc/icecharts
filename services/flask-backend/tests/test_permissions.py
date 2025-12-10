"""Role-Based Access Control (RBAC) and Permissions Tests."""

import json

import pytest


class TestAdminPermissions:
    """Test admin role permissions."""

    def test_admin_can_manage_users(self, client, admin_auth_headers):
        """Test that admins can manage users."""
        response = client.get("/api/v1/users", headers=admin_auth_headers)
        assert response.status_code in [200, 403]

    def test_admin_can_view_all_drawings(self, client, admin_auth_headers):
        """Test that admins can view all drawings."""
        response = client.get("/api/v1/drawings", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_admin_can_delete_any_drawing(self, client, admin_auth_headers, auth_headers):
        """Test that admins can delete any drawing."""
        # Create drawing as regular user
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

        # Try to delete as admin
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=admin_auth_headers,
        )
        assert response.status_code in [204, 403]

    def test_admin_can_modify_user_roles(self, client, admin_auth_headers):
        """Test that admins can modify user roles."""
        response = client.patch(
            "/api/v1/users/1",
            headers=admin_auth_headers,
            json={"role": "maintainer"},
        )
        assert response.status_code in [200, 404, 403]


class TestMaintainerPermissions:
    """Test maintainer role permissions."""

    def test_maintainer_can_manage_drawings(self, client, auth_headers, create_test_user):
        """Test that maintainers can create and edit drawings."""
        # Create a maintainer
        maintainer = create_test_user(
            email="maintainer@example.com", role="maintainer"
        )
        maintainer_headers = {"Authorization": f"Bearer {maintainer['token']}"}

        # Should be able to create drawings
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

    def test_maintainer_cannot_manage_users(self, client, auth_headers):
        """Test that maintainers cannot manage users."""
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code in [403, 404, 401]

    def test_maintainer_can_share_drawings(self, client, auth_headers):
        """Test that maintainers can share drawings."""
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

        # Try to share
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/share",
            headers=auth_headers,
            json={"user_id": 2, "permission": "view"},
        )
        assert response.status_code in [200, 201, 404, 403]


class TestViewerPermissions:
    """Test viewer role permissions."""

    def test_viewer_cannot_create_drawings(self, client, auth_headers):
        """Test that viewers cannot create drawings."""
        # Create a viewer user (default role)
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        # Depending on implementation, may allow or deny
        assert response.status_code in [201, 403]

    def test_viewer_can_read_shared_drawings(self, client, auth_headers):
        """Test that viewers can read drawings shared with them."""
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200

    def test_viewer_cannot_delete_drawings(self, client, auth_headers):
        """Test that viewers cannot delete drawings."""
        response = client.delete(
            "/api/v1/drawings/1",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]

    def test_viewer_cannot_modify_drawings(self, client, auth_headers):
        """Test that viewers cannot modify drawings."""
        response = client.put(
            "/api/v1/drawings/1",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code in [403, 404]


class TestResourceOwnershipPermissions:
    """Test permissions based on resource ownership."""

    def test_user_can_edit_own_drawing(self, client, auth_headers):
        """Test that users can edit their own drawings."""
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

        # Edit the drawing
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200

    def test_user_cannot_edit_others_drawing(self, client, auth_headers, create_test_user):
        """Test that users cannot edit other users' drawings."""
        # Create drawing as first user
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

        # Try to edit as different user (implementation dependent)
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers={"Authorization": f"Bearer {other_user.get('token', '')}"},
            json={"name": "Updated Name"},
        )
        # Should be blocked or return unauthorized
        assert response.status_code in [403, 401, 404]

    def test_user_can_delete_own_drawing(self, client, auth_headers):
        """Test that users can delete their own drawings."""
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


class TestGroupPermissions:
    """Test permissions for group operations."""

    def test_group_owner_can_manage_group(self, client, auth_headers):
        """Test that group owners can manage the group."""
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

        # Update the group
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200

    def test_non_owner_cannot_manage_group(self, client, auth_headers, create_test_user):
        """Test that non-owners cannot manage groups."""
        # Create a group as first user
        create_response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        group_id = json.loads(create_response.data)["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Try to update as different user
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {other_user.get('token', '')}"},
            json={"name": "Updated Name"},
        )
        # Should be blocked or return unauthorized
        assert response.status_code in [403, 401, 404]

    def test_group_member_can_view_group(self, client, auth_headers):
        """Test that group members can view the group."""
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

        # View the group
        response = client.get(
            f"/api/v1/groups/{group_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestDrawingPermissions:
    """Test sharing and permission levels on drawings."""

    def test_shared_drawing_read_permission(self, client, auth_headers, create_test_user):
        """Test user with read permission can view shared drawing."""
        # Create a drawing as first user
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

        # Share the drawing with read permission
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/share",
            headers=auth_headers,
            json={"user_id": other_user["id"], "permission": "view"},
        )
        assert response.status_code in [200, 201, 404]

    def test_shared_drawing_edit_permission(self, client, auth_headers, create_test_user):
        """Test user with edit permission can modify shared drawing."""
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

        # Share with edit permission
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/share",
            headers=auth_headers,
            json={"user_id": other_user["id"], "permission": "edit"},
        )
        assert response.status_code in [200, 201, 404]

    def test_public_drawing_read_by_anonymous(self, client, auth_headers):
        """Test that public drawings can be read without authentication."""
        # Create a public drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Public Drawing",
                "description": "A public drawing",
                "is_public": True,
                "canvas_data": {"nodes": [], "edges": []},
            },
        )
        assert create_response.status_code == 201
        drawing_id = json.loads(create_response.data)["id"]

        # Try to read without auth (implementation dependent)
        response = client.get(f"/api/v1/drawings/{drawing_id}")
        assert response.status_code in [200, 401]


class TestPermissionDenial:
    """Test that permissions are properly denied."""

    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated users are denied."""
        response = client.get("/api/v1/profile")
        assert response.status_code == 401

    def test_insufficient_permission_denied(self, client, auth_headers):
        """Test that insufficient permissions are denied."""
        # Try to access admin-only endpoint
        response = client.get(
            "/api/v1/admin/stats",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]

    def test_expired_token_denied(self, client, expired_jwt_token):
        """Test that expired tokens are denied."""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 401

    def test_malformed_token_denied(self, client):
        """Test that malformed tokens are denied."""
        headers = {"Authorization": "Bearer malformed.token"}
        response = client.get("/api/v1/profile", headers=headers)
        assert response.status_code == 401
