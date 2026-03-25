"""Security tests: Authentication bypass attempts.

Verifies that the JWT middleware correctly rejects malformed, forged, expired,
and algorithm-confused tokens across all protected endpoints.
"""

import pytest
import jwt
from datetime import datetime, timedelta


class TestJWTAlgorithmConfusion:
    """Tests for JWT algorithm confusion attacks."""

    def test_alg_none_attack_rejected(self, app, client, test_user):
        """A token signed with alg:none must be rejected with 401."""
        with app.app_context():
            payload = {
                "sub": str(test_user["id"]),
                "role": "admin",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            }
            # PyJWT raises InvalidAlgorithmError for alg:none by default,
            # but we test what the server responds with when such a token arrives.
            # Manually craft the token parts without a real signature.
            import base64
            import json

            header = base64.urlsafe_b64encode(
                json.dumps({"alg": "none", "typ": "JWT"}).encode()
            ).rstrip(b"=")
            body = base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": str(test_user["id"]),
                        "role": "admin",
                        "type": "access",
                        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                        "iat": int(datetime.utcnow().timestamp()),
                    }
                ).encode()
            ).rstrip(b"=")
            none_token = f"{header.decode()}.{body.decode()}."

            response = client.get(
                "/api/v1/drawings",
                headers={"Authorization": f"Bearer {none_token}"},
            )
            assert response.status_code == 401

    def test_wrong_secret_rejected(self, app, client, test_user):
        """A token signed with a different secret must be rejected with 401."""
        with app.app_context():
            payload = {
                "sub": str(test_user["id"]),
                "role": "viewer",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            }
            bad_token = jwt.encode(payload, "wrong-secret-key-xyz", algorithm="HS256")

            response = client.get(
                "/api/v1/drawings",
                headers={"Authorization": f"Bearer {bad_token}"},
            )
            assert response.status_code == 401

    def test_expired_token_rejected(self, client, expired_jwt_token):
        """An expired token must be rejected with 401."""
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Bearer {expired_jwt_token}"},
        )
        assert response.status_code == 401

    def test_hs256_token_with_rs256_claim_rejected(self, app, client, test_user):
        """A token claiming RS256 in header but signed with HS256 must be rejected."""
        with app.app_context():
            # Manually craft a token with mismatched header algorithm claim
            import base64
            import json

            payload = {
                "sub": str(test_user["id"]),
                "role": "admin",
                "type": "access",
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                "iat": int(datetime.utcnow().timestamp()),
            }
            # Header claims RS256 but the signature is HS256
            header = base64.urlsafe_b64encode(
                json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
            ).rstrip(b"=")
            body = base64.urlsafe_b64encode(
                json.dumps(payload).encode()
            ).rstrip(b"=")
            # Sign with HS256 secret — decoding must fail
            import hmac
            import hashlib

            signing_input = f"{header.decode()}.{body.decode()}"
            sig = hmac.new(
                app.config["JWT_SECRET_KEY"].encode(),
                signing_input.encode(),
                hashlib.sha256,
            ).digest()
            sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
            forged_token = f"{signing_input}.{sig_b64.decode()}"

            response = client.get(
                "/api/v1/drawings",
                headers={"Authorization": f"Bearer {forged_token}"},
            )
            assert response.status_code == 401


class TestMalformedHeaders:
    """Tests for malformed Authorization header handling."""

    def test_malformed_bearer_header_rejected(self, client, test_user):
        """A Bearer token with extra spaces must be rejected."""
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": "Bearer token1 token2"},
        )
        assert response.status_code == 401

    def test_empty_authorization_header_rejected(self, client):
        """An empty Authorization header must return 401."""
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": ""},
        )
        assert response.status_code == 401

    def test_no_authorization_header_returns_401(self, client):
        """A request with no Authorization header on a protected endpoint returns 401."""
        response = client.get("/api/v1/drawings")
        assert response.status_code == 401

    def test_basic_auth_scheme_rejected(self, client):
        """A Basic auth header (wrong scheme) must be rejected."""
        import base64

        credentials = base64.b64encode(b"admin:password").decode()
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Basic {credentials}"},
        )
        assert response.status_code == 401

    def test_bearer_without_token_rejected(self, client):
        """'Bearer ' with no token must be rejected."""
        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401


class TestClaimsValidation:
    """Tests for JWT claim validation."""

    def test_missing_sub_claim_rejected(self, app, client):
        """A token without a 'sub' claim on user access type must be rejected."""
        with app.app_context():
            payload = {
                # no "sub"
                "role": "admin",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )
            response = client.get(
                "/api/v1/drawings",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 401

    def test_future_iat_token_still_validated(self, app, client, test_user):
        """A token with a future iat should not be automatically accepted as admin."""
        with app.app_context():
            # Token with future iat but valid structure — should still be checked
            # against the secret. If valid signature, middleware accepts it
            # (iat is not enforced by PyJWT unless leeway is configured).
            # The key assertion: even if accepted, it must NOT grant admin access
            # when the user is a viewer.
            payload = {
                "sub": str(test_user["id"]),
                "role": "admin",  # Forged role escalation
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow() + timedelta(hours=24),  # future iat
            }
            token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )
            # Even if the token decodes, the user DB lookup will find a viewer
            # The role in DB must take precedence over token role claim
            response = client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {token}"},
            )
            # Either 401 (token rejected) or 403 (user found but not admin)
            assert response.status_code in (401, 403)

    def test_wrong_token_type_rejected(self, app, client, test_user):
        """A refresh token used as access token must be rejected."""
        with app.app_context():
            payload = {
                "sub": str(test_user["id"]),
                "type": "refresh",  # Wrong type for API access
                "exp": datetime.utcnow() + timedelta(days=30),
                "iat": datetime.utcnow(),
            }
            refresh_token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )
            response = client.get(
                "/api/v1/drawings",
                headers={"Authorization": f"Bearer {refresh_token}"},
            )
            assert response.status_code == 401


class TestRoleEnforcement:
    """Tests for role-based access control enforcement."""

    def test_viewer_cannot_access_admin_endpoint(self, client, auth_headers):
        """A viewer-role token must be rejected on admin-only endpoints with 403."""
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 403

    def test_forged_admin_role_in_token_for_viewer_user(
        self, app, client, test_user
    ):
        """A viewer user with a forged admin role in the token must still be blocked.

        The middleware reads the role from the database row, not the token payload,
        after performing the user lookup by sub. Role in token payload is secondary.
        """
        with app.app_context():
            # Craft a valid-signature token with role=admin but the sub points to
            # a viewer user in the DB.
            payload = {
                "sub": str(test_user["id"]),
                "role": "admin",  # Forged
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(
                payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
            )
            response = client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {token}"},
            )
            # Must be 403 (forbidden) not 200 — role comes from DB, not token
            assert response.status_code == 403
