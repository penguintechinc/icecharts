"""Security tests: Service account scope enforcement.

Verifies that service account tokens are restricted to their declared scopes
and cannot access endpoints requiring scopes they do not possess.

The middleware (scopes_required) passes through user tokens unconditionally
but strictly enforces scopes for service account tokens.
"""

import uuid
import pytest
import jwt
from datetime import datetime, timedelta


def _make_sa_token(app, db, scopes, sa_name=None):
    """Helper: create a service account + token record and return the JWT string."""
    sa_name = sa_name or f"test-sa-{uuid.uuid4().hex[:8]}"
    client_id = f"sa-{uuid.uuid4().hex[:8]}"

    sa_id = db.service_accounts.insert(
        client_id=client_id,
        name=sa_name,
        tenant_id=1,
        is_active=True,
        scopes=scopes,
    )
    db.commit()

    jti = str(uuid.uuid4())
    db.service_account_tokens.insert(
        service_account_id=sa_id,
        token_jti=jti,
        name=f"{sa_name}-token",
        scopes=scopes,
    )
    db.commit()

    payload = {
        "sub": client_id,
        "type": "service",
        "tenant_id": 1,
        "scopes": scopes,
        "jti": jti,
        "service_account_id": sa_id,
        "exp": datetime.utcnow() + timedelta(days=1),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm="HS256")


class TestDrawingScopes:
    """Tests for drawings:read and drawings:write scope enforcement."""

    def test_service_account_drawings_read_can_list(self, app, client):
        """SA with drawings:read scope can list drawings (not 403)."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["drawings:read"])

        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code != 403

    def test_service_account_drawings_read_cannot_create(self, app, client):
        """SA with only drawings:read scope cannot create drawings (403)."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["drawings:read"])

        response = client.post(
            "/api/v1/drawings",
            json={"name": "Scope Test Drawing", "description": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        # drawings:write is required to create; read-only SA must get 403
        assert response.status_code == 403

    def test_service_account_drawings_write_can_create(self, app, client):
        """SA with drawings:write scope can attempt to create drawings (not 403)."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["drawings:read", "drawings:write"])

        response = client.post(
            "/api/v1/drawings",
            json={"name": "Write Scope Drawing", "description": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        # 403 would indicate scope check failure; 400/200/201 means scope passed
        assert response.status_code != 403


class TestIceRunsScopes:
    """Tests for iceruns:write scope enforcement."""

    def test_service_account_iceruns_write_can_create(self, app, client):
        """SA with iceruns:write scope can attempt to create an IceRun."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["iceruns:write"])

        response = client.post(
            "/api/v1/iceruns",
            json={"name": "Test IceRun", "drawing_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Must not fail with 403 (scope check); 400/404 from business logic is fine
        assert response.status_code != 403

    def test_service_account_without_iceruns_write_cannot_create(self, app, client):
        """SA without iceruns:write scope cannot create an IceRun."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["drawings:read"])

        response = client.post(
            "/api/v1/iceruns",
            json={"name": "Unauthorized IceRun", "drawing_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestPlaybookScopes:
    """Tests for playbooks:execute scope enforcement."""

    def test_service_account_playbooks_execute_can_trigger(self, app, client):
        """SA with playbooks:execute scope can attempt playbook execution."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["playbooks:execute"])

        response = client.post(
            "/api/v1/playbooks/1/execute",
            json={"trigger": "api"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # 403 would be a scope failure; 404 means scope passed but playbook not found
        assert response.status_code != 403

    def test_service_account_without_playbooks_execute_is_blocked(self, app, client):
        """SA without playbooks:execute scope cannot execute playbooks."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["drawings:read"])

        response = client.post(
            "/api/v1/playbooks/1/execute",
            json={"trigger": "api"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestAdminScopes:
    """Tests for admin scope enforcement."""

    def test_service_account_cannot_access_admin_user_list(self, app, client):
        """SA tokens (even with many scopes) cannot access admin-only endpoints."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(
                app, db, ["drawings:read", "drawings:write", "playbooks:execute"]
            )

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Service account token type "service" in auth_required sets
        # is_service_account=True, then admin_required checks g.current_user (None)
        assert response.status_code in (401, 403)


class TestMultipleScopesAndEdgeCases:
    """Tests for multiple scopes, empty scopes, and invalid scope formats."""

    def test_multiple_scopes_work_correctly(self, app, client):
        """SA with multiple scopes can access all endpoints covered by those scopes."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(
                app, db, ["drawings:read", "drawings:write", "iceruns:write"]
            )

        # drawings:read — should work
        r1 = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code != 403

        # drawings:write — should work
        r2 = client.post(
            "/api/v1/drawings",
            json={"name": "Multi-scope Drawing"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code != 403

    def test_empty_scopes_rejected_on_scope_required_endpoint(self, app, client):
        """SA with empty scopes list cannot access scope-protected endpoints."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, [])

        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_invalid_scope_format_does_not_grant_access(self, app, client):
        """SA with malformed scope strings (e.g. wildcards) must not gain access."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["*", "**", "drawings:*"])

        response = client.post(
            "/api/v1/drawings",
            json={"name": "Wildcard Scope Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Wildcard scopes are not valid — must not match "drawings:write"
        assert response.status_code == 403

    def test_revoked_service_account_token_rejected(self, app, client):
        """A SA token whose DB record is revoked must be rejected."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            client_id = f"sa-revoked-{uuid.uuid4().hex[:8]}"
            sa_id = db.service_accounts.insert(
                client_id=client_id,
                name="Revoked SA",
                tenant_id=1,
                is_active=True,
                scopes=["drawings:read"],
            )
            db.commit()

            jti = str(uuid.uuid4())
            db.service_account_tokens.insert(
                service_account_id=sa_id,
                token_jti=jti,
                name="revoked-token",
                scopes=["drawings:read"],
                revoked_at=datetime.utcnow(),  # Already revoked
            )
            db.commit()

            payload = {
                "sub": client_id,
                "type": "service",
                "tenant_id": 1,
                "scopes": ["drawings:read"],
                "jti": jti,
                "service_account_id": sa_id,
                "exp": datetime.utcnow() + timedelta(days=1),
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

    def test_no_cross_scope_leakage(self, app, client):
        """SA with iceruns:write must not be able to list drawings (drawings:read)."""
        with app.app_context():
            from app.models import get_db

            db = get_db()
            token = _make_sa_token(app, db, ["iceruns:write"])

        response = client.get(
            "/api/v1/drawings",
            headers={"Authorization": f"Bearer {token}"},
        )
        # drawings:read is required; iceruns:write must not leak into it
        assert response.status_code == 403
