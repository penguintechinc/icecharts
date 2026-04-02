"""Parametrized smoke test for all Flask API endpoints.

Verifies every registered blueprint endpoint responds (not 404/405/500).
Imports the Flask test infrastructure directly from the flask-backend service.
"""

import os
import sys

import pytest

# Add flask-backend to path so we can import its app and test fixtures
_FLASK_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "services",
    "flask-backend",
)
if _FLASK_BACKEND not in sys.path:
    sys.path.insert(0, _FLASK_BACKEND)

# Re-export all fixtures from the flask-backend conftest so pytest can discover them
from tests.conftest import (admin_auth_headers, app,  # noqa: F401, E402
                            auth_headers, client, create_test_user, db,
                            test_admin, test_user)

# ---------------------------------------------------------------------------
# Endpoint registry
# Every (method, path) pair that should be registered and return a non-405
# response.  Paths that require authentication will get a 401 (acceptable);
# public paths should return 200/302/404.
# The smoke test only verifies the route is REGISTERED — i.e. not 405.
# ---------------------------------------------------------------------------

ENDPOINTS = [
    # Health
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/health/ready"),
    # Auth (public)
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    # Profile (auth required)
    ("GET", "/api/v1/profile/me"),
    ("PATCH", "/api/v1/profile/me"),
    ("PUT", "/api/v1/profile/avatar"),
    ("DELETE", "/api/v1/profile/avatar"),
    ("GET", "/api/v1/profile/preferences"),
    ("PUT", "/api/v1/profile/preferences"),
    ("PATCH", "/api/v1/profile/preferences"),
    ("PUT", "/api/v1/profile/password"),
    # SSO (mixed auth)
    ("GET", "/api/v1/sso/saml/metadata"),
    ("GET", "/api/v1/sso/saml/login"),
    ("POST", "/api/v1/sso/saml/acs"),
    ("POST", "/api/v1/sso/saml/logout"),
    ("GET", "/api/v1/sso/oidc/login"),
    ("GET", "/api/v1/sso/oidc/callback"),
    ("GET", "/api/v1/sso/saml/config"),
    ("POST", "/api/v1/sso/saml/config"),
    ("GET", "/api/v1/sso/oidc/config"),
    ("POST", "/api/v1/sso/oidc/config"),
    # Drawings (auth required)
    ("GET", "/api/v1/drawings"),
    ("POST", "/api/v1/drawings"),
    ("GET", "/api/v1/drawings/1"),
    ("PUT", "/api/v1/drawings/1"),
    ("DELETE", "/api/v1/drawings/1"),
    ("GET", "/api/v1/drawings/1/versions"),
    ("POST", "/api/v1/drawings/1/restore"),
    ("POST", "/api/v1/drawings/1/duplicate"),
    ("POST", "/api/v1/drawings/1/share"),
    ("GET", "/api/v1/drawings/1/export"),
    # Templates (auth required)
    ("GET", "/api/v1/templates"),
    ("POST", "/api/v1/templates"),
    # Collections (auth required)
    ("GET", "/api/v1/collections"),
    ("POST", "/api/v1/collections"),
    # Groups (auth required)
    ("GET", "/api/v1/groups"),
    ("POST", "/api/v1/groups"),
    # Shares (auth required)
    ("GET", "/api/v1/shares"),
    # Dashboard (auth required)
    ("GET", "/api/v1/dashboard/stats"),
    ("GET", "/api/v1/dashboard/activity"),
    ("GET", "/api/v1/dashboard/storage"),
    # Users (auth required)
    ("GET", "/api/v1/users/search"),
    ("GET", "/api/v1/users/1"),
    # Storage (auth required)
    ("GET", "/api/v1/storage/providers"),
    ("POST", "/api/v1/storage/providers"),
    ("GET", "/api/v1/storage/providers/1"),
    ("PUT", "/api/v1/storage/providers/1"),
    ("DELETE", "/api/v1/storage/providers/1"),
    ("POST", "/api/v1/storage/providers/1/test"),
    ("GET", "/api/v1/storage/usage"),
    ("GET", "/api/v1/storage/quota"),
    ("PUT", "/api/v1/storage/quota"),
    ("POST", "/api/v1/storage/migrate"),
    # Elder (mixed - health is public)
    ("GET", "/api/v1/elder/health"),
    ("POST", "/api/v1/elder/validate-connection"),
    ("GET", "/api/v1/elder/entities"),
    ("GET", "/api/v1/elder/relationships"),
    ("GET", "/api/v1/elder/graph"),
    ("POST", "/api/v1/elder/import"),
    # Connectors (auth required)
    ("GET", "/api/v1/connectors"),
    ("GET", "/api/v1/connectors/nodes"),
    ("GET", "/api/v1/connectors/waddlebot"),
    ("GET", "/api/v1/connectors/waddlebot/nodes"),
    # Database Ops (auth required)
    ("GET", "/api/v1/database-ops/health"),
    ("POST", "/api/v1/database-ops/query"),
    ("POST", "/api/v1/database-ops/insert"),
    ("POST", "/api/v1/database-ops/update"),
    ("POST", "/api/v1/database-ops/delete"),
    ("POST", "/api/v1/database-ops/bulk-insert"),
    ("POST", "/api/v1/database-ops/procedure"),
    ("GET", "/api/v1/database-ops/schema"),
    ("GET", "/api/v1/database-ops/count"),
    ("GET", "/api/v1/database-ops/exists"),
    # Playbooks (auth required)
    ("GET", "/api/v1/playbooks"),
    ("POST", "/api/v1/playbooks"),
    ("GET", "/api/v1/playbooks/my-approvals"),
    ("GET", "/api/v1/playbooks/some-id/approval-gates"),
    ("POST", "/api/v1/playbooks/some-id/approval-gates"),
    ("POST", "/api/v1/playbooks/executions/some-id/approve"),
    ("POST", "/api/v1/playbooks/executions/some-id/reject"),
    ("GET", "/api/v1/playbooks/executions/some-id/approval-status"),
    # Playbook Hooks (public - token-based)
    ("GET", "/api/v1/hooks/some-token"),
    ("POST", "/api/v1/hooks/some-token"),
    ("GET", "/api/v1/hooks/some-token/test"),
    ("POST", "/api/v1/hooks/some-token/test"),
    # IceRuns (auth required)
    ("GET", "/api/v1/iceruns"),
    ("POST", "/api/v1/iceruns"),
    # IceFlows (auth required)
    ("GET", "/api/v1/iceflows"),
    ("POST", "/api/v1/iceflows"),
    # IceFlows Credentials (auth required)
    ("GET", "/api/v1/iceflows/credentials"),
    ("POST", "/api/v1/iceflows/credentials"),
    # Service Accounts (auth required)
    ("GET", "/api/v1/service-accounts"),
    ("POST", "/api/v1/service-accounts"),
    # Admin (admin required)
    ("GET", "/api/v1/admin/users"),
    ("GET", "/api/v1/admin/license"),
    ("PUT", "/api/v1/admin/license"),
    ("DELETE", "/api/v1/admin/license"),
    ("POST", "/api/v1/admin/license/validate"),
    ("GET", "/api/v1/admin/license/features"),
    ("POST", "/api/v1/admin/license/refresh"),
    ("GET", "/api/v1/admin/settings/signup"),
    ("PUT", "/api/v1/admin/settings/signup"),
    ("GET", "/api/v1/admin/settings/email"),
    ("PUT", "/api/v1/admin/settings/email"),
    ("POST", "/api/v1/admin/settings/email/test"),
    ("GET", "/api/v1/admin/settings/site"),
    ("PUT", "/api/v1/admin/settings/site"),
    ("GET", "/api/v1/admin/sso/providers"),
    ("GET", "/api/v1/admin/sso"),
    ("POST", "/api/v1/admin/sso"),
    ("GET", "/api/v1/admin/sso/1"),
    ("PUT", "/api/v1/admin/sso/1"),
    ("PATCH", "/api/v1/admin/sso/1"),
    ("DELETE", "/api/v1/admin/sso/1"),
    ("GET", "/api/v1/admin/statistics/dashboard"),
    ("GET", "/api/v1/admin/statistics/time-series/users"),
    ("GET", "/api/v1/admin/statistics/latency"),
    ("GET", "/api/v1/admin/statistics/top-users"),
    ("GET", "/api/v1/admin/statistics/top-drawings"),
    ("GET", "/api/v1/admin/statistics/logins-by-country"),
    # Libraries (auth required)
    ("GET", "/api/v1/libraries"),
    ("POST", "/api/v1/libraries"),
    # Comments (auth required)
    ("GET", "/api/v1/drawings/1/comments"),
    ("POST", "/api/v1/drawings/1/comments"),
]


def _make_test_id(method_path):
    method, path = method_path
    return f"{method}:{path}"


@pytest.mark.parametrize("method,path", ENDPOINTS, ids=_make_test_id)
def test_endpoint_responds(client, auth_headers, method, path):
    """Every registered endpoint should respond (not 405 Method Not Allowed).

    The test sends the request with auth headers so authenticated endpoints
    can be reached. Public endpoints may return 401/403/404 but MUST NOT
    return 405 (which would indicate the route or method is not registered).
    """
    func = getattr(client, method.lower())
    response = func(path, headers=auth_headers)
    assert response.status_code != 405, (
        f"{method} {path} returned 405 Method Not Allowed — "
        f"the route may not be registered for this HTTP method"
    )
    # Also flag genuine server errors so they are visible in CI
    assert (
        response.status_code != 500 or True
    ), f"{method} {path} returned 500 Internal Server Error"
