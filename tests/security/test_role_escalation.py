"""Security tests: Role escalation and privilege boundary enforcement.

Verifies that users cannot elevate their own privileges, access other users'
private resources, or bypass ownership and sharing restrictions.
"""

import pytest


class TestSelfEscalation:
    """Tests that prevent users from upgrading their own role."""

    def test_viewer_cannot_self_promote_to_admin_via_profile_update(
        self, client, auth_headers, test_user
    ):
        """A viewer sending role=admin in a profile PATCH must be ignored."""
        response = client.patch(
            "/api/v1/profile/me",
            json={"full_name": "Hacker", "role": "admin"},
            headers=auth_headers,
        )
        # Request may succeed (200) but role must not change,
        # or server rejects role field (400)
        assert response.status_code not in (500,)

        if response.status_code == 200:
            data = response.get_json()
            # profile endpoint only allows full_name, bio, preferences
            # role must remain "viewer"
            assert data.get("role") != "admin"

    def test_viewer_cannot_update_own_role_via_profile(
        self, client, auth_headers
    ):
        """profile/me PATCH must not accept a 'role' field."""
        response = client.patch(
            "/api/v1/profile/me",
            json={"role": "maintainer"},
            headers=auth_headers,
        )
        # Allowed fields are: full_name, bio, preferences
        # Sending only 'role' should give 400 (no valid fields) or ignore it
        if response.status_code == 200:
            # If somehow succeeds, role must not have changed
            data = response.get_json()
            assert data.get("role") != "maintainer"
        else:
            # 400 "No valid fields to update" is expected
            assert response.status_code == 400

    def test_maintainer_cannot_self_promote_to_admin(
        self, app, client, create_test_user
    ):
        """A maintainer cannot promote themselves to admin via any profile endpoint."""
        from app.api.v1.auth import create_access_token

        with app.app_context():
            maintainer = create_test_user(
                email="maintainer@example.com", role="maintainer"
            )
            token = create_access_token(maintainer["id"], maintainer["role"])

        response = client.patch(
            "/api/v1/profile/me",
            json={"role": "admin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            data = response.get_json()
            assert data.get("role") != "admin"
        else:
            assert response.status_code == 400


class TestCrossUserAccess:
    """Tests for cross-user resource access prevention."""

    def test_viewer_cannot_access_other_users_private_drawing(
        self, app, client, auth_headers, create_test_user
    ):
        """A viewer cannot access a private drawing owned by a different user."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            # Create a second user who owns a private drawing
            other_user = create_test_user(email="other@example.com", role="viewer")
            drawing_id = db.drawings.insert(
                title="Private Drawing",
                created_by_id=other_user["id"],
                owner_id=other_user["id"],
                is_public=False,
                status="active",
            )
            db.commit()

        response = client.get(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        # Either 403 (forbidden) or 404 (hidden from non-owners) is correct
        assert response.status_code in (403, 404)

    def test_user_cannot_update_another_users_profile(
        self, app, client, auth_headers, create_test_user
    ):
        """A viewer cannot update another user's profile via admin or profile endpoints."""
        with app.app_context():
            other_user = create_test_user(email="victim@example.com", role="viewer")

        # Attempt to update victim's profile through admin endpoint
        response = client.patch(
            f"/api/v1/admin/users/{other_user['id']}",
            json={"full_name": "Hacked Name"},
            headers=auth_headers,
        )
        # viewer must get 403 (not admin)
        assert response.status_code == 403

    def test_viewer_cannot_access_other_users_private_playbook(
        self, app, client, auth_headers, create_test_user
    ):
        """A viewer cannot read a private playbook owned by another user."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            other_user = create_test_user(
                email="playbook-owner@example.com", role="maintainer"
            )
            pb_id = db.playbooks.insert(
                name="Private Playbook",
                created_by_id=other_user["id"],
                trigger_type="manual",
                is_public=False,
                is_enabled=True,
                status="active",
            )
            db.commit()

        response = client.get(
            f"/api/v1/playbooks/{pb_id}",
            headers=auth_headers,
        )
        # Should be 403 or 404 — not 200 exposing the private playbook
        assert response.status_code in (403, 404)


class TestExecutionIsolation:
    """Tests for playbook execution isolation."""

    def test_viewer_cannot_execute_playbook_they_dont_own(
        self, app, client, auth_headers, create_test_user
    ):
        """A viewer cannot execute a playbook they have no access to."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            owner = create_test_user(
                email="pb-exec-owner@example.com", role="admin"
            )
            pb_id = db.playbooks.insert(
                name="Restricted Playbook",
                created_by_id=owner["id"],
                trigger_type="manual",
                is_public=False,
                is_enabled=True,
                status="active",
            )
            db.commit()

        response = client.post(
            f"/api/v1/playbooks/{pb_id}/execute",
            json={"trigger": "manual"},
            headers=auth_headers,
        )
        assert response.status_code in (403, 404)

    def test_public_drawing_share_is_read_only(
        self, app, client, auth_headers, create_test_user
    ):
        """A publicly shared drawing can be read but not modified by non-owners."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            owner = create_test_user(email="share-owner@example.com", role="admin")
            drawing_id = db.drawings.insert(
                title="Public Drawing",
                created_by_id=owner["id"],
                owner_id=owner["id"],
                is_public=True,
                status="active",
            )
            db.commit()

        # Attempt to DELETE the public drawing as a different user (viewer)
        response = client.delete(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        # Non-owner attempting to delete → 403 or 404
        assert response.status_code in (403, 404)

    def test_group_membership_required_for_group_shared_drawing(
        self, app, client, auth_headers, create_test_user
    ):
        """A user not in the sharing group cannot access a group-shared drawing."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            owner = create_test_user(
                email="group-owner@example.com", role="admin"
            )
            # Create a group (test_user is NOT a member)
            group_id = db.groups.insert(
                name="Secret Group",
                created_by_id=owner["id"],
                tenant_id=1,
            )
            drawing_id = db.drawings.insert(
                title="Group Drawing",
                created_by_id=owner["id"],
                owner_id=owner["id"],
                is_public=False,
                status="active",
            )
            # Share with the group only
            db.drawing_shares.insert(
                drawing_id=drawing_id,
                group_id=group_id,
                shared_by_id=owner["id"],
                permission="read",
            )
            db.commit()

        # test_user is not in the group → should get 403 or 404
        response = client.get(
            f"/api/v1/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code in (403, 404)
