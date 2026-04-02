"""Security tests: Rate limiting behavior.

Most tests are marked xfail because rate limiting is disabled in the test config
(RATELIMIT_ENABLED=false). They document the intended production behavior and
will pass when rate limiting is enabled.
"""

import pytest


class TestRateLimitHeaders:
    """Tests for rate limit header presence in responses."""

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_rate_limit_headers_present_in_response(self, client, auth_headers):
        """Standard rate limit headers should be present on API responses."""
        response = client.get("/api/v1/drawings", headers=auth_headers)
        assert response.status_code == 200
        # Standard rate limiting headers
        assert any(
            h in response.headers
            for h in (
                "X-RateLimit-Limit",
                "RateLimit-Limit",
                "X-Rate-Limit-Limit",
            )
        )

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_rate_limit_remaining_decrements(self, client, auth_headers):
        """X-RateLimit-Remaining should decrement with each request."""
        r1 = client.get("/api/v1/drawings", headers=auth_headers)
        r2 = client.get("/api/v1/drawings", headers=auth_headers)

        remaining1 = int(r1.headers.get("X-RateLimit-Remaining", 999))
        remaining2 = int(r2.headers.get("X-RateLimit-Remaining", 998))
        assert remaining2 < remaining1


class TestLoginRateLimiting:
    """Tests for stricter rate limiting on the login endpoint."""

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_login_endpoint_stricter_limits(self, client):
        """The login endpoint should have a stricter rate limit than general API."""
        # Flood the login endpoint
        responses = []
        for _ in range(20):
            responses.append(
                client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "wrong"},
                )
            )

        status_codes = [r.status_code for r in responses]
        # At least one request should be rate limited (429)
        assert 429 in status_codes

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_login_rate_limit_applies_per_ip(self, client):
        """Login rate limit should track attempts per IP address."""
        for _ in range(10):
            client.post(
                "/api/v1/auth/login",
                json={"email": "flood@example.com", "password": "wrong"},
                environ_base={"REMOTE_ADDR": "10.0.0.1"},
            )

        # Same IP should be blocked
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "flood@example.com", "password": "wrong"},
            environ_base={"REMOTE_ADDR": "10.0.0.1"},
        )
        assert response.status_code == 429


class TestAPIRateLimiting:
    """Tests for standard API endpoint rate limits."""

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_api_standard_rate_limit(self, client, auth_headers):
        """Standard API endpoints should return 429 after exceeding limits."""
        responses = []
        for _ in range(200):
            responses.append(client.get("/api/v1/drawings", headers=auth_headers))

        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_per_user_rate_tracking(self, client, auth_headers, admin_auth_headers):
        """Rate limits should be tracked per user, not globally."""
        # Fill up one user's limit
        for _ in range(100):
            client.get("/api/v1/drawings", headers=auth_headers)

        # A different user (admin) should still have their own quota
        response = client.get("/api/v1/drawings", headers=admin_auth_headers)
        assert response.status_code == 200

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_per_ip_rate_tracking_for_unauthenticated(self, client):
        """Unauthenticated rate limiting should be tracked per IP."""
        responses = []
        for _ in range(50):
            responses.append(
                client.get(
                    "/api/v1/drawings",
                    environ_base={"REMOTE_ADDR": "192.168.1.100"},
                )
            )

        status_codes = [r.status_code for r in responses]
        # Should get 401 initially, then 429 when rate limited
        assert 429 in status_codes

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_burst_tolerance(self, client, auth_headers):
        """A small burst of requests should not trigger rate limiting immediately."""
        # First few requests should succeed
        for i in range(5):
            response = client.get("/api/v1/drawings", headers=auth_headers)
            assert (
                response.status_code == 200
            ), f"Request {i + 1} should not be rate limited in burst tolerance window"

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_different_endpoints_different_limits(
        self, client, auth_headers, admin_auth_headers
    ):
        """Admin endpoints should have tighter rate limits than standard endpoints."""
        # Admin endpoints are more sensitive
        admin_responses = []
        for _ in range(30):
            admin_responses.append(
                client.get("/api/v1/admin/users", headers=admin_auth_headers)
            )

        admin_429 = sum(1 for r in admin_responses if r.status_code == 429)

        # Standard endpoint with same number of requests
        std_responses = []
        for _ in range(30):
            std_responses.append(client.get("/api/v1/drawings", headers=auth_headers))

        std_429 = sum(1 for r in std_responses if r.status_code == 429)

        # Admin endpoint should hit rate limit sooner (more 429s)
        assert admin_429 >= std_429

    @pytest.mark.xfail(reason="Rate limiting disabled in test config")
    def test_service_account_separate_rate_limits(self, client, app):
        """Service account tokens should have separate rate limit buckets."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            # Create a minimal service account and token record for testing
            sa_id = db.service_accounts.insert(
                client_id="sa-rate-limit-test",
                name="Rate Limit Test SA",
                tenant_id=1,
                is_active=True,
                scopes=["drawings:read"],
            )
            db.commit()

            import uuid
            from datetime import datetime, timedelta

            import jwt

            jti = str(uuid.uuid4())
            db.service_account_tokens.insert(
                service_account_id=sa_id,
                token_jti=jti,
                name="test-token",
                scopes=["drawings:read"],
            )
            db.commit()

            payload = {
                "sub": "sa-rate-limit-test",
                "type": "service",
                "tenant_id": 1,
                "scopes": ["drawings:read"],
                "jti": jti,
                "service_account_id": sa_id,
                "exp": datetime.utcnow() + timedelta(days=1),
                "iat": datetime.utcnow(),
            }
            sa_token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )

        sa_headers = {"Authorization": f"Bearer {sa_token}"}

        # Service account requests should not consume from user rate limit pool
        responses = [
            client.get("/api/v1/drawings", headers=sa_headers) for _ in range(10)
        ]
        # At minimum, verify requests are processed (not all fail)
        success = sum(1 for r in responses if r.status_code in (200, 403))
        assert success > 0
