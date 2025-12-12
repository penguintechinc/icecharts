"""Authentication and authorization decorators for IceCharts."""

import inspect
from functools import wraps
from typing import Callable, List, Union

from flask import current_app, g, jsonify

from app.auth.jwt_handler import get_current_user


def login_required(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.

    Makes current_user available via flask.g.current_user.

    Usage:
        @bp.route('/protected')
        @login_required
        def protected_route():
            from flask import g
            return jsonify({"user": g.current_user.username})
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()

        if not user:
            return jsonify({"error": "Authentication required"}), 401

        g.current_user = user

        if inspect.iscoroutinefunction(f):
            return f(*args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated_function


def role_required(allowed_roles: Union[str, List[str]]) -> Callable:
    """
    Decorator to require specific role(s) for an endpoint.

    Args:
        allowed_roles: String or list of allowed roles ('admin', 'maintainer', 'viewer')

    Usage:
        @bp.route('/admin-only')
        @login_required
        @role_required('admin')
        def admin_route():
            return jsonify({"message": "Admin access"})

        @bp.route('/write-access')
        @login_required
        @role_required(['admin', 'maintainer'])
        def write_route():
            return jsonify({"message": "Write access"})
    """
    # Normalize to list
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            # Superusers bypass all role checks
            if user.is_superuser:
                g.current_user = user
                return f(*args, **kwargs)

            # Check role
            user_role = user.get("role", "viewer")
            if user_role not in allowed_roles:
                return (
                    jsonify(
                        {
                            "error": "Insufficient permissions",
                            "required_roles": allowed_roles,
                            "your_role": user_role,
                        }
                    ),
                    403,
                )

            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def license_required(required_tier: str) -> Callable:
    """
    Decorator to check license tier requirement.

    Args:
        required_tier: Required license tier ('community', 'professional', 'enterprise')

    Usage:
        @bp.route('/advanced/analytics')
        @login_required
        @license_required("professional")
        def generate_advanced_report():
            return jsonify({"report": analytics.generate_report()})
    """
    tier_hierarchy = {"community": 1, "professional": 2, "enterprise": 3}

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if license enforcement is enabled
            if not current_app.config.get("RELEASE_MODE", False):
                # Development mode - allow all features
                return f(*args, **kwargs)

            # Get user's tenant
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401

            from app.models import get_db

            db = get_db()
            tenant = db(db.tenants.id == user.tenant_id).select().first()

            if not tenant:
                return jsonify({"error": "Tenant not found"}), 404

            # Check tier
            user_tier = tenant.subscription_tier or "community"
            required_level = tier_hierarchy.get(required_tier, 1)
            user_level = tier_hierarchy.get(user_tier, 1)

            if user_level < required_level:
                return (
                    jsonify(
                        {
                            "error": "License upgrade required",
                            "message": f"This feature requires {required_tier} tier or higher",
                            "current_tier": user_tier,
                            "required_tier": required_tier,
                        }
                    ),
                    403,
                )

            g.current_user = user
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin role. Alias for @role_required('admin')."""
    return role_required("admin")(f)
