"""Tests for Profile API endpoints."""

import io

import pytest


class TestGetProfile:
    """Tests for GET /profile/me."""

    def test_get_profile_requires_auth(self, client):
        """Getting profile requires authentication."""
        response = client.get("/api/v1/profile/me")
        assert response.status_code == 401

    def test_get_profile_with_auth(self, client, auth_headers, test_user):
        """Authenticated user can retrieve their profile."""
        response = client.get("/api/v1/profile/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "email" in data
        assert data["email"] == test_user["email"]

    def test_get_profile_contains_expected_fields(self, client, auth_headers):
        """Profile response includes expected fields."""
        response = client.get("/api/v1/profile/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert "is_active" in data


class TestUpdateProfile:
    """Tests for PATCH /profile/me."""

    def test_update_profile_requires_auth(self, client):
        """Updating profile requires authentication."""
        response = client.patch(
            "/api/v1/profile/me",
            json={"full_name": "New Name"},
        )
        assert response.status_code == 401

    def test_update_profile_full_name(self, client, auth_headers):
        """User can update their full name."""
        response = client.patch(
            "/api/v1/profile/me",
            headers=auth_headers,
            json={"full_name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data

    def test_update_profile_no_body(self, client, auth_headers):
        """Updating profile without body returns error."""
        response = client.patch(
            "/api/v1/profile/me",
            headers=auth_headers,
            data="",
            content_type="application/json",
        )
        # 400 for empty body or 415 for missing content type
        assert response.status_code in [400, 415]

    def test_update_profile_disallowed_field(self, client, auth_headers):
        """Updating a disallowed field (e.g. role) is ignored or rejected."""
        response = client.patch(
            "/api/v1/profile/me",
            headers=auth_headers,
            json={"role": "admin"},
        )
        # Server either ignores invalid fields (returns 400 for no valid fields)
        # or updates successfully (ignoring unrecognised keys)
        assert response.status_code in [200, 400]

    def test_update_profile_bio(self, client, auth_headers):
        """User can update their bio."""
        response = client.patch(
            "/api/v1/profile/me",
            headers=auth_headers,
            json={"bio": "Hello, I am a test user."},
        )
        assert response.status_code == 200


class TestAvatarUpload:
    """Tests for PUT /profile/avatar."""

    def test_upload_avatar_requires_auth(self, client):
        """Uploading avatar requires authentication."""
        data = {"avatar": (io.BytesIO(b"fake-image-data"), "avatar.png")}
        response = client.put(
            "/api/v1/profile/avatar",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 401

    def test_upload_avatar_no_file(self, client, auth_headers):
        """Upload without file returns 400."""
        response = client.put(
            "/api/v1/profile/avatar",
            headers=auth_headers,
            data={},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_upload_avatar_invalid_extension(self, client, auth_headers):
        """Upload with invalid extension returns 400."""
        data = {"avatar": (io.BytesIO(b"fake-file-data"), "malicious.exe")}
        response = client.put(
            "/api/v1/profile/avatar",
            headers=auth_headers,
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400


class TestAvatarDelete:
    """Tests for DELETE /profile/avatar."""

    def test_delete_avatar_requires_auth(self, client):
        """Deleting avatar requires authentication."""
        response = client.delete("/api/v1/profile/avatar")
        assert response.status_code == 401

    def test_delete_avatar_with_auth(self, client, auth_headers):
        """Authenticated user can delete their avatar."""
        response = client.delete("/api/v1/profile/avatar", headers=auth_headers)
        assert response.status_code == 200


class TestGetPreferences:
    """Tests for GET /profile/preferences."""

    def test_get_preferences_requires_auth(self, client):
        """Getting preferences requires authentication."""
        response = client.get("/api/v1/profile/preferences")
        assert response.status_code == 401

    def test_get_preferences_with_auth(self, client, auth_headers):
        """Authenticated user can retrieve their preferences."""
        response = client.get("/api/v1/profile/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "preferences" in data


class TestUpdatePreferences:
    """Tests for PUT /profile/preferences (full replace)."""

    def test_update_preferences_requires_auth(self, client):
        """Updating preferences requires authentication."""
        response = client.put(
            "/api/v1/profile/preferences",
            json={"theme": "dark"},
        )
        assert response.status_code == 401

    def test_update_preferences_with_auth(self, client, auth_headers):
        """Authenticated user can replace preferences."""
        response = client.put(
            "/api/v1/profile/preferences",
            headers=auth_headers,
            json={"theme": "dark", "language": "en"},
        )
        assert response.status_code == 200

    def test_update_preferences_no_body(self, client, auth_headers):
        """Updating preferences without body returns error."""
        response = client.put(
            "/api/v1/profile/preferences",
            headers=auth_headers,
            data="",
            content_type="application/json",
        )
        # 400 for empty body or 415 for missing content type
        assert response.status_code in [400, 415]


class TestPatchPreferences:
    """Tests for PATCH /profile/preferences (partial update)."""

    def test_patch_preferences_requires_auth(self, client):
        """Patching preferences requires authentication."""
        response = client.patch(
            "/api/v1/profile/preferences",
            json={"theme": "light"},
        )
        assert response.status_code == 401

    def test_patch_preferences_with_auth(self, client, auth_headers):
        """Authenticated user can partially update preferences."""
        response = client.patch(
            "/api/v1/profile/preferences",
            headers=auth_headers,
            json={"theme": "light"},
        )
        assert response.status_code == 200


class TestChangePassword:
    """Tests for PUT /profile/password."""

    def test_change_password_requires_auth(self, client):
        """Changing password requires authentication."""
        response = client.put(
            "/api/v1/profile/password",
            json={"current_password": "old", "new_password": "newpassword"},
        )
        assert response.status_code == 401

    def test_change_password_missing_fields(self, client, auth_headers):
        """Missing current or new password returns 400."""
        response = client.put(
            "/api/v1/profile/password",
            headers=auth_headers,
            json={"new_password": "newpassword123"},
        )
        assert response.status_code == 400

    def test_change_password_too_short(self, client, auth_headers, test_user):
        """New password shorter than 8 chars returns 400."""
        response = client.put(
            "/api/v1/profile/password",
            headers=auth_headers,
            json={
                "current_password": test_user["password"],
                "new_password": "short",
            },
        )
        assert response.status_code == 400

    def test_change_password_wrong_current(self, client, auth_headers):
        """Wrong current password returns 400."""
        response = client.put(
            "/api/v1/profile/password",
            headers=auth_headers,
            json={
                "current_password": "WrongPassword999!",
                "new_password": "NewValidPassword123!",
            },
        )
        assert response.status_code == 400
