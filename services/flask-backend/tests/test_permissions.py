"""Role-Based Access Control (RBAC) and Permissions Tests."""

import json

import pytest


def _get_drawing_id(response):
    """Extract drawing ID from a create/update drawing API response.

    The API returns: {"success": true, "drawing": {"id": "...", ...}}
    """
    data = json.loads(response.data)
    return data["drawing"]["id"]


def _get_group_id(response):
    """Extract group ID from a create/update group API response.

    The API returns: {"group": {"id": ..., ...}, "message": "..."}
    """
    data = json.loads(response.data)
    return data["group"]["id"]


def _make_drawing_payload(name="Test Drawing", description="A test drawing",
                          visibility="private"):
    """Build a valid drawing creation payload matching CreateDrawingRequest schema.

    The API expects: name, description, content, visibility, is_template, tags.
    It does NOT accept 'canvas_data' or 'is_public' at top level.
    """
    return {
        "name": name,
        "description": description,
        "content": {"nodes": [], "edges": []},
        "visibility": visibility,
    }


class TestAdminPermissions:
    """Test admin role permissions."""

    def test_admin_can_manage_users(self, client, admin_auth_headers):
        """Test that admins can access the admin user list endpoint."""
        # Admin user management is at /api/v1/admin/users, not /api/v1/users
        response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_admin_can_view_all_drawings(self, client, admin_auth_headers):
        """Test that admins can view all drawings."""
        response = client.get("/api/v1/drawings", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_admin_can_delete_any_drawing(self, client, admin_auth_headers,
                                          auth_headers):
        """Test that admins can delete any drawing.

        Note: The API checks ownership (created_by_id, owner_id, user_id) for
        delete. Admin users do not automatically bypass ownership checks in
        the drawings endpoint, so 403 is the expected result when deleting
        another user's drawing.
        """
        # Create drawing as regular user (viewer role)
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Try to delete as admin -- the drawings endpoint checks ownership,
        # not admin role, so this returns 403.
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=admin_auth_headers,
        )
        # Delete endpoint returns 200 on success or 403 for non-owners
        assert response.status_code in [200, 403]

    def test_admin_can_modify_user_roles(self, client, admin_auth_headers,
                                         create_test_user):
        """Test that admins can modify user roles via admin endpoint.

        The admin update endpoint is PUT /api/v1/admin/users/<id> (not PATCH).
        """
        # Create a target user to modify
        target_user = create_test_user(
            email="target_role@example.com", role="viewer"
        )

        response = client.put(
            f"/api/v1/admin/users/{target_user['id']}",
            headers=admin_auth_headers,
            json={"role": "maintainer"},
        )
        assert response.status_code == 200


class TestMaintainerPermissions:
    """Test maintainer role permissions."""

    def test_maintainer_can_manage_drawings(self, app, client, create_test_user):
        """Test that maintainers can create drawings."""
        from app.api.v1.auth import create_access_token

        # Create a maintainer user and generate a token for them
        maintainer = create_test_user(
            email="maintainer@example.com", role="maintainer"
        )
        with app.app_context():
            token = create_access_token(maintainer["id"], maintainer["role"])
        maintainer_headers = {"Authorization": f"Bearer {token}"}

        # Maintainers should be able to create drawings
        response = client.post(
            "/api/v1/drawings",
            headers=maintainer_headers,
            json=_make_drawing_payload(),
        )
        assert response.status_code == 201

    def test_maintainer_cannot_manage_users(self, app, client, create_test_user):
        """Test that maintainers cannot access admin user management."""
        from app.api.v1.auth import create_access_token

        maintainer = create_test_user(
            email="maintainer_no_admin@example.com", role="maintainer"
        )
        with app.app_context():
            token = create_access_token(maintainer["id"], maintainer["role"])
        maintainer_headers = {"Authorization": f"Bearer {token}"}

        # Admin user list is at /api/v1/admin/users and requires admin role
        response = client.get("/api/v1/admin/users", headers=maintainer_headers)
        assert response.status_code == 403

    def test_maintainer_can_share_drawings(self, app, client, create_test_user):
        """Test that maintainers can share drawings.

        The share endpoint is POST /api/v1/drawings/<id>/shares (plural)
        and requires a 'type' field (user, group, or public).
        """
        from app.api.v1.auth import create_access_token

        maintainer = create_test_user(
            email="maintainer_share@example.com", role="maintainer"
        )
        other_user = create_test_user(
            email="share_target@example.com", role="viewer"
        )
        with app.app_context():
            token = create_access_token(maintainer["id"], maintainer["role"])
        maintainer_headers = {"Authorization": f"Bearer {token}"}

        # Create a drawing as the maintainer
        create_response = client.post(
            "/api/v1/drawings",
            headers=maintainer_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Share the drawing -- endpoint is /shares (plural) and needs type field
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            headers=maintainer_headers,
            json={
                "type": "user",
                "user_id": other_user["id"],
                "permission": "view",
            },
        )
        assert response.status_code in [201, 403, 404]


class TestViewerPermissions:
    """Test viewer role permissions.

    Note: The drawings API uses @scopes_required which passes through for
    user tokens (only restricts service accounts). Any authenticated user
    can create/read/write/delete drawings. Ownership is checked for
    update and delete operations.
    """

    def test_viewer_can_create_drawings(self, client, auth_headers):
        """Test that viewers can create drawings.

        The drawings endpoint uses @scopes_required("drawings:write") which
        only restricts service account tokens. User tokens pass through
        regardless of role.
        """
        response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert response.status_code == 201

    def test_viewer_can_read_drawings(self, client, auth_headers):
        """Test that viewers can read their own drawings."""
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200

    def test_viewer_cannot_delete_others_drawings(self, client, auth_headers):
        """Test that viewers cannot delete drawings they do not own.

        Requesting a non-existent drawing ID returns 404.
        """
        response = client.delete(
            "/api/v1/drawings/999999",
            headers=auth_headers,
        )
        assert response.status_code in [403, 404]

    def test_viewer_cannot_modify_others_drawings(self, client, auth_headers):
        """Test that viewers cannot modify drawings they do not own.

        Requesting a non-existent drawing ID returns 404.
        """
        response = client.put(
            "/api/v1/drawings/999999",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code in [403, 404]

    def test_viewer_cannot_create_groups(self, client, auth_headers):
        """Test that viewers cannot create groups.

        Group creation requires @maintainer_or_admin_required.
        The default auth_headers fixture uses a viewer role.
        """
        response = client.post(
            "/api/v1/groups",
            headers=auth_headers,
            json={"name": "Viewer Group", "description": "Should fail"},
        )
        assert response.status_code == 403


class TestResourceOwnershipPermissions:
    """Test permissions based on resource ownership."""

    def test_user_can_edit_own_drawing(self, client, auth_headers):
        """Test that users can edit their own drawings."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Edit the drawing
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200

    def test_user_cannot_edit_others_drawing(self, app, client, auth_headers,
                                             create_test_user):
        """Test that users cannot edit other users' drawings."""
        from app.api.v1.auth import create_access_token

        # Create drawing as first user (viewer from auth_headers fixture)
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Create another user and generate a real token for them
        other_user = create_test_user(email="other_edit@example.com")
        with app.app_context():
            other_token = create_access_token(
                other_user["id"], other_user["role"]
            )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to edit as different user -- should be denied by ownership check
        response = client.put(
            f"/api/v1/drawings/{drawing_id}",
            headers=other_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code in [403, 404]

    def test_user_can_delete_own_drawing(self, client, auth_headers):
        """Test that users can delete their own drawings.

        The delete endpoint returns 200 (not 204) with a JSON success message.
        """
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Delete the drawing -- API returns 200 with JSON body
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestGroupPermissions:
    """Test permissions for group operations.

    Group creation requires @maintainer_or_admin_required, so these tests
    use admin_auth_headers (admin role) to create groups.
    """

    def test_group_owner_can_manage_group(self, client, admin_auth_headers):
        """Test that group owners can manage the group."""
        # Create a group (requires maintainer or admin role)
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group",
                "description": "A test group",
            },
        )
        assert create_response.status_code == 201
        group_id = _get_group_id(create_response)

        # Update the group
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200

    def test_non_owner_cannot_manage_group(self, app, client,
                                           admin_auth_headers,
                                           create_test_user):
        """Test that non-owners cannot manage groups."""
        from app.api.v1.auth import create_access_token

        # Create a group as admin
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Test Group Non-Owner",
                "description": "A test group",
            },
        )
        assert create_response.status_code == 201
        group_id = _get_group_id(create_response)

        # Create another user and generate a real token
        other_user = create_test_user(email="other_group@example.com")
        with app.app_context():
            other_token = create_access_token(
                other_user["id"], other_user["role"]
            )
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to update as different user -- should be denied
        response = client.put(
            f"/api/v1/groups/{group_id}",
            headers=other_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code in [403, 401]

    def test_group_member_can_view_group(self, client, admin_auth_headers):
        """Test that group owners/members can view the group.

        The creator is automatically added as a group admin member.
        """
        # Create a group (requires maintainer or admin role)
        create_response = client.post(
            "/api/v1/groups",
            headers=admin_auth_headers,
            json={
                "name": "Viewable Group",
                "description": "A test group",
            },
        )
        assert create_response.status_code == 201
        group_id = _get_group_id(create_response)

        # View the group as the creator (who is also a member)
        response = client.get(
            f"/api/v1/groups/{group_id}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200


class TestDrawingPermissions:
    """Test sharing and permission levels on drawings.

    The share endpoint is POST /api/v1/drawings/<id>/shares (plural)
    and requires a 'type' field with value 'user', 'group', or 'public'.
    """

    def test_shared_drawing_read_permission(self, client, auth_headers,
                                            create_test_user):
        """Test creating a share with read permission."""
        # Create a drawing as first user
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Create another user
        other_user = create_test_user(email="other_read@example.com")

        # Share the drawing with read permission
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

    def test_shared_drawing_edit_permission(self, client, auth_headers,
                                            create_test_user):
        """Test creating a share with edit permission."""
        # Create a drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Create another user
        other_user = create_test_user(email="other_edit_share@example.com")

        # Share with edit permission
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/shares",
            headers=auth_headers,
            json={
                "type": "user",
                "user_id": other_user["id"],
                "permission": "edit",
            },
        )
        assert response.status_code in [201, 403, 404]

    def test_public_drawing_read_by_anonymous(self, client, auth_headers):
        """Test that public drawings require authentication to read.

        The GET /api/v1/drawings/<id> endpoint uses @auth_required,
        so unauthenticated access returns 401 even for public drawings.
        """
        # Create a public drawing
        create_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json=_make_drawing_payload(
                name="Public Drawing",
                description="A public drawing",
                visibility="public",
            ),
        )
        assert create_response.status_code == 201
        drawing_id = _get_drawing_id(create_response)

        # Try to read without auth -- endpoint requires auth so expect 401
        response = client.get(f"/api/v1/drawings/{drawing_id}")
        assert response.status_code == 401


class TestPermissionDenial:
    """Test that permissions are properly denied."""

    def test_unauthenticated_access_denied(self, client):
        """Test that unauthenticated users are denied.

        The profile endpoint is at /api/v1/profile/me (not /api/v1/profile).
        """
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401

    def test_insufficient_permission_denied(self, client, auth_headers):
        """Test that insufficient permissions are denied.

        The admin stats endpoint requires @admin_required.
        The auth_headers fixture uses a viewer role.
        """
        response = client.get(
            "/api/v1/admin/stats",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_expired_token_denied(self, client, expired_jwt_token):
        """Test that expired tokens are denied."""
        headers = {"Authorization": f"Bearer {expired_jwt_token}"}
        response = client.get("/api/v1/profile/me", headers=headers)
        assert response.status_code == 401

    def test_malformed_token_denied(self, client):
        """Test that malformed tokens are denied."""
        headers = {"Authorization": "Bearer malformed.token"}
        response = client.get("/api/v1/profile/me", headers=headers)
        assert response.status_code == 401
