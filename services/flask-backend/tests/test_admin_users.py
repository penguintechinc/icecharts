"""Tests for Admin Users API endpoints."""

import pytest


class TestAdminListUsers:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_list_requires_admin(self, client, auth_headers):
        """Regular viewer should receive 403."""
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_list_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "users" in data
        assert "total" in data

    def test_list_pagination(self, client, admin_auth_headers):
        response = client.get(
            "/api/v1/admin/users?page=1&per_page=5", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "page" in data
        assert "per_page" in data

    def test_list_with_search(self, client, admin_auth_headers):
        response = client.get(
            "/api/v1/admin/users?search=admin", headers=admin_auth_headers
        )
        assert response.status_code == 200


class TestAdminGetUser:
    def test_get_user_requires_auth(self, client):
        response = client.get("/api/v1/admin/users/1")
        assert response.status_code == 401

    def test_get_user_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/users/1", headers=auth_headers)
        assert response.status_code == 403

    def test_get_user_with_admin(self, client, admin_auth_headers, test_admin):
        response = client.get(
            f"/api/v1/admin/users/{test_admin['id']}", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "user" in data

    def test_get_nonexistent_user_returns_404(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/users/999999", headers=admin_auth_headers)
        assert response.status_code == 404


class TestAdminCreateUser:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/admin/users",
            json={"email": "new@example.com", "password": "Pass123!", "role": "viewer"},
        )
        assert response.status_code == 401

    def test_create_requires_admin(self, client, auth_headers):
        response = client.post(
            "/api/v1/admin/users",
            json={"email": "new@example.com", "password": "Pass123!", "role": "viewer"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_with_admin(self, client, admin_auth_headers):
        payload = {
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "full_name": "New User",
            "role": "viewer",
        }
        response = client.post(
            "/api/v1/admin/users", json=payload, headers=admin_auth_headers
        )
        assert response.status_code in (201, 409)  # 409 if already exists

    def test_create_missing_email_returns_400(self, client, admin_auth_headers):
        payload = {"password": "Pass123!", "role": "viewer"}
        response = client.post(
            "/api/v1/admin/users", json=payload, headers=admin_auth_headers
        )
        assert response.status_code == 400

    def test_create_short_password_returns_400(self, client, admin_auth_headers):
        payload = {"email": "user@test.com", "password": "short", "role": "viewer"}
        response = client.post(
            "/api/v1/admin/users", json=payload, headers=admin_auth_headers
        )
        assert response.status_code == 400

    def test_create_invalid_role_returns_400(self, client, admin_auth_headers):
        payload = {
            "email": "user@test.com",
            "password": "Pass123456!",
            "role": "superadmin",
        }
        response = client.post(
            "/api/v1/admin/users", json=payload, headers=admin_auth_headers
        )
        assert response.status_code == 400


class TestAdminUpdateUser:
    def test_update_requires_auth(self, client):
        response = client.put("/api/v1/admin/users/1", json={"role": "maintainer"})
        assert response.status_code == 401

    def test_update_requires_admin(self, client, auth_headers):
        response = client.put(
            "/api/v1/admin/users/1",
            json={"role": "maintainer"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_update_nonexistent_returns_404(self, client, admin_auth_headers):
        response = client.put(
            "/api/v1/admin/users/999999",
            json={"full_name": "Updated Name"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    def test_update_with_admin(self, client, admin_auth_headers, test_user):
        response = client.put(
            f"/api/v1/admin/users/{test_user['id']}",
            json={"full_name": "Updated Name"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200


class TestAdminDeleteUser:
    def test_delete_requires_auth(self, client):
        response = client.delete("/api/v1/admin/users/999")
        assert response.status_code == 401

    def test_delete_requires_admin(self, client, auth_headers):
        response = client.delete("/api/v1/admin/users/999", headers=auth_headers)
        assert response.status_code == 403

    def test_delete_nonexistent_returns_404(self, client, admin_auth_headers):
        response = client.delete(
            "/api/v1/admin/users/999999", headers=admin_auth_headers
        )
        assert response.status_code == 404


class TestAdminActivateDeactivate:
    def test_activate_requires_auth(self, client):
        response = client.post("/api/v1/admin/users/1/activate")
        assert response.status_code == 401

    def test_activate_requires_admin(self, client, auth_headers):
        response = client.post("/api/v1/admin/users/1/activate", headers=auth_headers)
        assert response.status_code == 403

    def test_activate_with_admin(self, client, admin_auth_headers, test_user):
        response = client.post(
            f"/api/v1/admin/users/{test_user['id']}/activate",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    def test_deactivate_requires_auth(self, client):
        response = client.post("/api/v1/admin/users/1/deactivate")
        assert response.status_code == 401

    def test_deactivate_requires_admin(self, client, auth_headers):
        response = client.post("/api/v1/admin/users/1/deactivate", headers=auth_headers)
        assert response.status_code == 403

    def test_deactivate_self_returns_400(self, client, admin_auth_headers, test_admin):
        """Admin cannot deactivate their own account."""
        response = client.post(
            f"/api/v1/admin/users/{test_admin['id']}/deactivate",
            headers=admin_auth_headers,
        )
        assert response.status_code == 400


class TestAdminBulkImport:
    def test_bulk_import_requires_auth(self, client):
        response = client.post("/api/v1/admin/users/bulk-import", json={"users": []})
        assert response.status_code == 401

    def test_bulk_import_requires_admin(self, client, auth_headers):
        response = client.post(
            "/api/v1/admin/users/bulk-import",
            json={"users": []},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_bulk_import_empty_users_returns_error(self, client, admin_auth_headers):
        response = client.post(
            "/api/v1/admin/users/bulk-import",
            json={"users": []},
            headers=admin_auth_headers,
        )
        assert response.status_code in (400, 422)

    def test_bulk_import_with_admin(self, client, admin_auth_headers):
        users = [
            {
                "email": "bulk1@example.com",
                "password": "BulkPass123!",
                "full_name": "Bulk User 1",
                "role": "viewer",
            },
        ]
        response = client.post(
            "/api/v1/admin/users/bulk-import",
            json={"users": users},
            headers=admin_auth_headers,
        )
        assert response.status_code not in (401, 403)


class TestAdminStats:
    def test_stats_requires_auth(self, client):
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401

    def test_stats_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    def test_stats_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/stats", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "stats" in data


class TestAdminActivity:
    def test_activity_requires_auth(self, client):
        response = client.get("/api/v1/admin/activity")
        assert response.status_code == 401

    def test_activity_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/activity", headers=auth_headers)
        assert response.status_code == 403

    def test_activity_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/activity", headers=admin_auth_headers)
        assert response.status_code == 200


class TestAdminAuditLog:
    def test_audit_log_requires_auth(self, client):
        response = client.get("/api/v1/admin/audit-log")
        assert response.status_code == 401

    def test_audit_log_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/audit-log", headers=auth_headers)
        assert response.status_code == 403

    def test_audit_log_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/audit-log", headers=admin_auth_headers)
        assert response.status_code == 200


class TestAdminSystemEndpoints:
    def test_system_health_requires_auth(self, client):
        response = client.get("/api/v1/admin/system/health")
        assert response.status_code == 401

    def test_system_health_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/system/health", headers=auth_headers)
        assert response.status_code == 403

    def test_system_health_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/system/health", headers=admin_auth_headers)
        assert response.status_code in (200, 503)

    def test_system_config_requires_auth(self, client):
        response = client.get("/api/v1/admin/system/config")
        assert response.status_code == 401

    def test_system_config_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/system/config", headers=auth_headers)
        assert response.status_code == 403

    def test_system_config_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/system/config", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "config" in data


class TestAdminStorage:
    def test_list_storage_requires_auth(self, client):
        response = client.get("/api/v1/admin/storage")
        assert response.status_code == 401

    def test_list_storage_requires_admin(self, client, auth_headers):
        response = client.get("/api/v1/admin/storage", headers=auth_headers)
        assert response.status_code == 403

    def test_list_storage_with_admin(self, client, admin_auth_headers):
        response = client.get("/api/v1/admin/storage", headers=admin_auth_headers)
        assert response.status_code == 200

    def test_create_storage_requires_auth(self, client):
        response = client.post(
            "/api/v1/admin/storage",
            json={"provider": "s3", "bucket": "my-bucket"},
        )
        assert response.status_code == 401

    def test_create_storage_requires_admin(self, client, auth_headers):
        response = client.post(
            "/api/v1/admin/storage",
            json={"provider": "s3", "bucket": "my-bucket"},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_create_storage_invalid_provider_returns_400(
        self, client, admin_auth_headers
    ):
        response = client.post(
            "/api/v1/admin/storage",
            json={"provider": "dropbox"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 400

    def test_update_storage_requires_auth(self, client):
        response = client.put("/api/v1/admin/storage/1", json={"enabled": True})
        assert response.status_code == 401

    def test_update_storage_requires_admin(self, client, auth_headers):
        response = client.put(
            "/api/v1/admin/storage/1", json={"enabled": True}, headers=auth_headers
        )
        assert response.status_code == 403

    def test_patch_storage_requires_auth(self, client):
        response = client.patch("/api/v1/admin/storage/1", json={"enabled": False})
        assert response.status_code == 401

    def test_patch_storage_requires_admin(self, client, auth_headers):
        response = client.patch(
            "/api/v1/admin/storage/1",
            json={"enabled": False},
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_delete_storage_requires_auth(self, client):
        response = client.delete("/api/v1/admin/storage/1")
        assert response.status_code == 401

    def test_delete_storage_requires_admin(self, client, auth_headers):
        response = client.delete("/api/v1/admin/storage/1", headers=auth_headers)
        assert response.status_code == 403
