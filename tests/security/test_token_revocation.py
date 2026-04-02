"""Security tests: Refresh token revocation.

All tests are marked xfail because revoke_refresh_token() and
is_refresh_token_valid() are currently stubbed (they always return True/0
without a refresh_tokens table).

These tests document the correct production behavior once the refresh_tokens
table is implemented.
"""

import hashlib
from datetime import datetime, timedelta

import jwt
import pytest

REVOCATION_STUBBED = pytest.mark.xfail(
    reason="revoke_refresh_token() currently stubbed — refresh_tokens table not yet implemented"
)


class TestRevocationStorage:
    """Tests for refresh token revocation persistence."""

    @REVOCATION_STUBBED
    def test_revoke_stores_in_db(self, app, test_user, refresh_token):
        """revoke_refresh_token() must mark the token as revoked in the DB."""
        with app.app_context():
            from app.models import (get_db, is_refresh_token_valid,
                                    revoke_refresh_token)

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

            # Token should be valid before revocation
            assert is_refresh_token_valid(token_hash) is True

            # Revoke it
            result = revoke_refresh_token(token_hash)
            assert result is True

            # Must be invalid now
            assert is_refresh_token_valid(token_hash) is False

    @REVOCATION_STUBBED
    def test_double_revocation_is_idempotent(self, app, test_user, refresh_token):
        """Revoking an already-revoked token must not raise an error."""
        with app.app_context():
            from app.models import revoke_refresh_token

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

            # Revoke twice — must not raise
            revoke_refresh_token(token_hash)
            result = revoke_refresh_token(token_hash)
            # Second revocation should return True (idempotent) or False (not found)
            assert result in (True, False)

    @REVOCATION_STUBBED
    def test_invalid_token_hash_revocation_is_noop(self, app):
        """Revoking a hash that was never stored must be a safe no-op."""
        with app.app_context():
            from app.models import revoke_refresh_token

            fake_hash = "a" * 64  # Valid-length SHA256 hex but never stored
            result = revoke_refresh_token(fake_hash)
            # Should return False (not found) without raising
            assert result is False


class TestRevocationEnforcement:
    """Tests that revoked tokens are actually rejected by the refresh endpoint."""

    @REVOCATION_STUBBED
    def test_revoked_token_rejected_on_refresh(
        self, app, client, test_user, refresh_token
    ):
        """A revoked refresh token must be rejected by POST /auth/refresh."""
        with app.app_context():
            from app.models import revoke_refresh_token

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            revoke_refresh_token(token_hash)

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert "revoked" in data.get("error", "").lower()

    @REVOCATION_STUBBED
    def test_logout_revokes_refresh_token(
        self, app, client, test_user, auth_headers, refresh_token
    ):
        """POST /auth/logout must revoke the user's refresh token(s)."""
        # Logout
        logout_response = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200

        # Attempting to refresh after logout must fail
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401

    @REVOCATION_STUBBED
    def test_revoke_all_user_tokens_invalidates_all(self, app, client, test_user):
        """revoke_all_user_tokens() must invalidate all tokens for the user."""
        with app.app_context():
            from app.api.v1.auth import create_refresh_token
            from app.models import (get_db, is_refresh_token_valid,
                                    revoke_all_user_tokens)

            # Create two refresh tokens for the user
            token1, _ = create_refresh_token(test_user["id"])
            token2, _ = create_refresh_token(test_user["id"])

            hash1 = hashlib.sha256(token1.encode()).hexdigest()
            hash2 = hashlib.sha256(token2.encode()).hexdigest()

            # Revoke all tokens
            count = revoke_all_user_tokens(test_user["id"])
            assert count >= 2

            # Both must now be invalid
            assert is_refresh_token_valid(hash1) is False
            assert is_refresh_token_valid(hash2) is False


class TestStatelessAccessTokens:
    """Tests for access token behavior (stateless — not revocable until expiry)."""

    @REVOCATION_STUBBED
    def test_revoked_refresh_token_access_token_still_valid_until_expiry(
        self, app, client, test_user, auth_headers, refresh_token
    ):
        """Revoking a refresh token does NOT invalidate the associated access token.

        Access tokens are stateless JWT — they remain valid until their exp claim.
        Only the refresh token is revoked; the access token keeps working.
        """
        with app.app_context():
            from app.models import revoke_refresh_token

            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            revoke_refresh_token(token_hash)

        # Access token should still work (stateless, not revoked)
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200

    @REVOCATION_STUBBED
    def test_per_token_revocation_leaves_others_valid(self, app, client, test_user):
        """Revoking one refresh token must not invalidate other tokens for the same user."""
        with app.app_context():
            from app.api.v1.auth import create_refresh_token
            from app.models import is_refresh_token_valid, revoke_refresh_token

            token1, _ = create_refresh_token(test_user["id"])
            token2, _ = create_refresh_token(test_user["id"])

            hash1 = hashlib.sha256(token1.encode()).hexdigest()
            hash2 = hashlib.sha256(token2.encode()).hexdigest()

            # Revoke only token1
            revoke_refresh_token(hash1)

            # token2 must still be valid
            assert is_refresh_token_valid(hash1) is False
            assert is_refresh_token_valid(hash2) is True
