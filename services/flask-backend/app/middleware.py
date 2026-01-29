"""Authentication and Authorization Middleware."""

import datetime
from functools import wraps
from typing import Callable, List, Optional

import jwt
from flask import current_app, g, jsonify, request

from .models import get_user_by_id


def get_token_from_header() -> Optional[str]:
    """Extract JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user() -> Optional[dict]:
    """Get current authenticated user from request context."""
    return getattr(g, "current_user", None)


def is_service_account_request() -> bool:
    """Check if the current request is from a service account."""
    return getattr(g, "is_service_account", False)


def get_token_scopes() -> List[str]:
    """Get scopes from the current service account token."""
    return getattr(g, "token_scopes", [])


def _authenticate_service_account(payload: dict) -> tuple:
    """
    Authenticate a service account from token payload.

    Returns:
        Tuple of (success: bool, error_response or None)
    """
    from .models import get_db

    db = get_db()

    # Get service account ID from payload
    service_account_id = payload.get("service_account_id")
    if not service_account_id:
        return False, (jsonify({"error": "Invalid service token payload"}), 401)

    # Check if token is revoked
    token_jti = payload.get("jti")
    if not token_jti:
        return False, (jsonify({"error": "Invalid service token: missing jti"}), 401)

    token_record = db(
        db.service_account_tokens.token_jti == token_jti
    ).select().first()

    if not token_record:
        return False, (jsonify({"error": "Service token not found"}), 401)

    if token_record.revoked_at is not None:
        return False, (jsonify({"error": "Service token has been revoked"}), 401)

    # Load service account
    service_account = db(
        db.service_accounts.id == service_account_id
    ).select().first()

    if not service_account:
        return False, (jsonify({"error": "Service account not found"}), 401)

    if not service_account.is_active:
        return False, (jsonify({"error": "Service account is deactivated"}), 401)

    # Update last used timestamp on token
    db(db.service_account_tokens.token_jti == token_jti).update(
        last_used_at=datetime.datetime.now(datetime.timezone.utc),
        last_used_ip=request.remote_addr,
    )

    # Update last used timestamp on service account
    db(db.service_accounts.id == service_account_id).update(
        last_used_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.commit()

    # Store service account info in request context
    sa_dict = service_account.as_dict()
    sa_dict["token_scopes"] = payload.get("scopes", [])
    sa_dict["token_jti"] = token_jti

    g.service_account = sa_dict
    g.is_service_account = True
    g.token_scopes = payload.get("scopes", [])

    return True, None


def auth_required(f: Callable) -> Callable:
    """Decorator to require authentication (user or service account)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        token_type = payload.get("type")

        # Handle service account tokens
        if token_type == "service":
            success, error = _authenticate_service_account(payload)
            if not success:
                return error
            return f(*args, **kwargs)

        # Handle user access tokens
        if token_type != "access":
            return jsonify({"error": "Invalid token type"}), 401

        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "Invalid token payload"}), 401

        user = get_user_by_id(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 401

        if not user.get("is_active"):
            return jsonify({"error": "User account is deactivated"}), 401

        # Store user in request context
        g.current_user = user
        g.is_service_account = False

        return f(*args, **kwargs)

    return decorated


def optional_auth(f: Callable) -> Callable:
    """Decorator for optional authentication.

    Sets g.current_user if a valid token is present, otherwise sets it
    to None and continues without returning an error.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user = None
        g.is_service_account = False

        token = get_token_from_header()
        if token:
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    user = get_user_by_id(int(user_id))
                    if user and user.get("is_active"):
                        g.current_user = user

        return f(*args, **kwargs)

    return decorated


def user_auth_required(f: Callable) -> Callable:
    """Decorator to require user authentication only (no service accounts)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()

        if not token:
            return jsonify({"error": "Missing authorization token"}), 401

        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Only accept user access tokens
        if payload.get("type") != "access":
            return jsonify({"error": "This endpoint requires user authentication"}), 401

        # Get user from database
        user_id = payload.get("sub")
        if not user_id:
            return jsonify({"error": "Invalid token payload"}), 401

        user = get_user_by_id(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 401

        if not user.get("is_active"):
            return jsonify({"error": "User account is deactivated"}), 401

        # Store user in request context
        g.current_user = user
        g.is_service_account = False

        return f(*args, **kwargs)

    return decorated


def scopes_required(*required_scopes: str) -> Callable:
    """
    Decorator to require specific scopes for service account access.

    For user tokens, this decorator passes through (users have all permissions).
    For service account tokens, it checks that all required scopes are present.

    Args:
        *required_scopes: Variable number of scope strings required

    Usage:
        @auth_required
        @scopes_required("drawings:read", "drawings:write")
        def my_endpoint():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # User tokens pass through - users have full access
            if not is_service_account_request():
                return f(*args, **kwargs)

            # Service account tokens must have required scopes
            token_scopes = get_token_scopes()
            missing = set(required_scopes) - set(token_scopes)

            if missing:
                return jsonify({
                    "error": "Insufficient scope",
                    "required_scopes": list(required_scopes),
                    "missing_scopes": list(missing),
                }), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


def role_required(*allowed_roles: str) -> Callable:
    """Decorator to require specific roles."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({"error": "Authentication required"}), 401

            user_role = user.get("role", "")
            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_roles": list(allowed_roles),
                    "your_role": user_role,
                }), 403

            return f(*args, **kwargs)

        return decorated

    return decorator


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin role."""
    return role_required("admin")(f)


def maintainer_or_admin_required(f: Callable) -> Callable:
    """Decorator to require maintainer or admin role."""
    return role_required("admin", "maintainer")(f)
