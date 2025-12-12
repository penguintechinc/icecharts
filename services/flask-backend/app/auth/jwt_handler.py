"""JWT token handling for IceCharts authentication."""

import datetime
from typing import Dict, Optional

import jwt
from flask import current_app, g, request
from pydal.objects import Row


def generate_access_token(user: Row) -> str:
    """
    Generate JWT access token for user.

    Args:
        user: PyDAL Row representing identity

    Returns:
        JWT access token string
    """
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "type": "access",
    }

    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def generate_refresh_token(user: Row) -> str:
    """
    Generate JWT refresh token for user.

    Args:
        user: PyDAL Row representing identity

    Returns:
        JWT refresh token string
    """
    payload = {
        "user_id": user.id,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"],
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Returns:
        Token string if found, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def get_current_user() -> Optional[Row]:
    """
    Get current authenticated user from request context.

    Returns:
        PyDAL Row for current user if authenticated, None otherwise
    """
    # Check if already loaded in request context
    if hasattr(g, "current_user") and g.current_user is not None:
        return g.current_user

    # Extract token from header
    token = get_token_from_header()
    if not token:
        return None

    # Decode token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    # Load user from database
    from app.models import get_db

    db = get_db()
    user = db(db.identities.id == payload["user_id"]).select().first()

    if not user or not user.is_active:
        return None

    # Store in request context
    g.current_user = user
    return user


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Generate new access token from refresh token.

    Args:
        refresh_token: JWT refresh token

    Returns:
        New access token if refresh token is valid, None otherwise
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None

    # Load user
    from app.models import get_db

    db = get_db()
    user = db(db.identities.id == payload["user_id"]).select().first()

    if not user or not user.is_active:
        return None

    return generate_access_token(user)
