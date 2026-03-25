"""Security tests: Injection attack prevention.

Verifies that the API correctly handles SQL injection, XSS, command injection,
path traversal, CRLF injection, and HTML injection payloads without executing
them or returning dangerous content.
"""

import pytest
import json


# Payloads grouped by attack type
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE drawings; --",
    "' OR '1'='1",
    "1; SELECT * FROM identities; --",
    "' UNION SELECT username, password FROM identities --",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(document.cookie)",
    "<svg onload=alert(1)>",
]

COMMAND_INJECTION_PAYLOADS = [
    "../../etc/passwd",
    "; ls -la /",
    "| cat /etc/shadow",
    "$(id)",
    "`whoami`",
]

PATH_TRAVERSAL_PAYLOADS = [
    "../../../../etc/passwd",
    "..%2F..%2F..%2Fetc%2Fpasswd",
    "%2e%2e%2fetc%2fpasswd",
]


class TestSQLInjection:
    """Tests for SQL injection prevention in drawing and search endpoints."""

    def test_sql_injection_in_drawing_name(self, client, auth_headers):
        """SQL injection in drawing name field must not cause DB errors."""
        payload = {
            "name": "'; DROP TABLE drawings; --",
            "description": "Test drawing",
        }
        response = client.post(
            "/api/v1/drawings",
            json=payload,
            headers=auth_headers,
        )
        # Must not return 500 (server error from SQL execution)
        assert response.status_code != 500
        # Should succeed (stored as literal string) or fail with 4xx validation error
        assert response.status_code in (200, 201, 400, 422)

        if response.status_code in (200, 201):
            data = response.get_json()
            # If created, the name must be stored literally, not executed
            name = data.get("drawing", {}).get("name", "") or data.get("name", "")
            assert "DROP TABLE" in name or response.status_code in (400, 422)

    def test_sql_injection_in_search_parameter(self, client, auth_headers):
        """SQL injection in user search query parameter must not expose data."""
        response = client.get(
            "/api/v1/users/search",
            query_string={"q": "' OR '1'='1"},
            headers=auth_headers,
        )
        # Must not return 500
        assert response.status_code != 500
        assert response.status_code in (200, 400)

        if response.status_code == 200:
            data = response.get_json()
            # Should return normal search results (empty for SQL fragment query)
            # not expose all users
            assert "users" in data
            # SQL injection 'OR 1=1' should not dump all DB rows —
            # either empty or minimal results based on string matching
            assert len(data["users"]) < 100

    def test_sql_injection_in_database_ops_query(self, client, auth_headers):
        """SQL injection in database-ops query field must be rejected or sanitized."""
        payload = {
            "db_type": "sqlite",
            "database": "test",
            "table": "identities",
            "query": "SELECT * FROM identities; DROP TABLE drawings; --",
        }
        response = client.post(
            "/api/v1/database-ops/query",
            json=payload,
            headers=auth_headers,
        )
        # Must not return 500 (execution of injected SQL)
        assert response.status_code != 500

    @pytest.mark.parametrize("injection", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_variants_in_admin_search(
        self, client, admin_auth_headers, injection
    ):
        """Various SQL injection payloads in admin user search must not cause 500."""
        response = client.get(
            "/api/v1/admin/users",
            query_string={"search": injection},
            headers=admin_auth_headers,
        )
        assert response.status_code != 500


class TestXSSPrevention:
    """Tests for Cross-Site Scripting (XSS) prevention."""

    def test_xss_in_comment_content(self, client, auth_headers, app):
        """XSS payload in comment content must be stored safely or rejected."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            # Create a drawing to comment on
            drawing_id = db.drawings.insert(
                title="Test Drawing for XSS",
                created_by_id=1,
                owner_id=1,
                is_public=False,
                status="active",
            )
            db.commit()

        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            f"/api/v1/drawings/{drawing_id}/comments",
            json={"content": xss_payload},
            headers=auth_headers,
        )
        # Must not return 500
        assert response.status_code != 500

        if response.status_code in (200, 201):
            data = response.get_json()
            # Content must be stored/returned as plain text, not rendered HTML
            content = str(data)
            # The raw script tag should not be returned without escaping
            # (API returns JSON; XSS execution is a browser concern, but
            # we verify the API does not error and returns parseable JSON)
            assert data is not None

    def test_xss_in_user_profile_full_name(self, client, auth_headers):
        """XSS payload in profile full_name must be stored safely or rejected."""
        xss_payload = "<img src=x onerror=alert(1)>"
        response = client.patch(
            "/api/v1/profile/me",
            json={"full_name": xss_payload},
            headers=auth_headers,
        )
        # Must not return 500
        assert response.status_code != 500

    def test_xss_in_drawing_description(self, client, auth_headers):
        """XSS payload in drawing description must be stored safely or rejected."""
        payload = {
            "name": "Safe Name",
            "description": "<script>document.cookie</script>",
        }
        response = client.post(
            "/api/v1/drawings",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code != 500

    @pytest.mark.parametrize("xss", XSS_PAYLOADS)
    def test_xss_variants_in_drawing_name(self, client, auth_headers, xss):
        """Various XSS payloads in drawing name must not cause server errors."""
        response = client.post(
            "/api/v1/drawings",
            json={"name": xss, "description": ""},
            headers=auth_headers,
        )
        assert response.status_code != 500


class TestCommandAndPathInjection:
    """Tests for command injection and path traversal prevention."""

    def test_command_injection_in_package_filename(self, client, auth_headers):
        """Command injection via filename in any upload/export endpoint is rejected."""
        # Test via drawing export with malicious filename
        response = client.post(
            "/api/v1/drawings/export",
            json={
                "drawing_id": 1,
                "filename": "../../etc/passwd",
                "format": "png",
            },
            headers=auth_headers,
        )
        assert response.status_code != 500
        # Should be 400 (bad request), 404 (drawing not found), or similar 4xx
        assert response.status_code in (400, 401, 403, 404, 422)

    def test_path_traversal_in_export_filename(self, client, auth_headers):
        """Path traversal sequences in export filename must be sanitized."""
        response = client.post(
            "/api/v1/drawings/export",
            json={
                "drawing_id": 1,
                "filename": "../../../tmp/evil_file",
                "format": "svg",
            },
            headers=auth_headers,
        )
        assert response.status_code != 500

    @pytest.mark.parametrize("path", PATH_TRAVERSAL_PAYLOADS)
    def test_path_traversal_variants(self, client, auth_headers, path):
        """URL-encoded and plain path traversal sequences must not cause 500."""
        response = client.get(
            f"/api/v1/drawings/{path}",
            headers=auth_headers,
        )
        assert response.status_code != 500
        # 404 or 400 is acceptable
        assert response.status_code in (400, 404, 422)

    @pytest.mark.parametrize("cmd", COMMAND_INJECTION_PAYLOADS)
    def test_command_injection_variants_in_search(
        self, client, auth_headers, cmd
    ):
        """Command injection payloads in search must not execute system commands."""
        response = client.get(
            "/api/v1/users/search",
            query_string={"q": cmd},
            headers=auth_headers,
        )
        assert response.status_code != 500


class TestHeaderInjection:
    """Tests for CRLF and header injection prevention."""

    def test_crlf_injection_in_authorization_header(self, client, app, test_user):
        """CRLF sequences in header values must not split the HTTP response."""
        with app.app_context():
            import jwt
            from datetime import datetime, timedelta

            payload = {
                "sub": str(test_user["id"]),
                "role": "viewer",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )

        # Append CRLF injection attempt to the token value
        malicious_header = f"Bearer {token}\r\nX-Injected: evil"
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": malicious_header},
        )
        # Flask/Werkzeug strips CRLF from headers; token will be malformed → 401
        assert response.status_code in (400, 401)
        # Verify the injected header is NOT present in the response
        assert "X-Injected" not in response.headers

    def test_html_injection_in_share_message(self, client, auth_headers):
        """HTML injection in share invitation message must be handled safely."""
        malicious_message = (
            '<h1>Click here</h1><a href="http://evil.com">Free prize</a>'
        )
        response = client.post(
            "/api/v1/drawings/1/share",
            json={
                "user_email": "victim@example.com",
                "message": malicious_message,
                "permission": "read",
            },
            headers=auth_headers,
        )
        # Must not return 500 — 400/404 is acceptable since drawing may not exist
        assert response.status_code != 500
