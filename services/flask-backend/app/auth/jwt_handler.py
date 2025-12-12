"""JWT token handling for IceCharts authentication."""

import datetime
import uuid
from typing import Dict, Optional, Tuple

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


def generate_service_token(
    service_account: dict, expires_days: int = 365
) -> Tuple[str, str]:
    """
    Generate long-lived JWT token for service account.

    Args:
        service_account: Dictionary containing service account data
            (id, client_id, tenant_id, scopes)
        expires_days: Number of days until token expires (default: 365)

    Returns:
        Tuple of (token_string, jti) where jti is the unique token ID
    """
    jti = str(uuid.uuid4())

    payload = {
        "sub": service_account["client_id"],
        "type": "service",  # Distinguishes from "access" (user tokens)
        "tenant_id": service_account["tenant_id"],
        "scopes": service_account.get("scopes", []),
        "jti": jti,
        "service_account_id": service_account["id"],
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=expires_days),
    }

    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )

    return token, jti


def decode_service_token(token: str) -> Optional[Dict]:
    """
    Decode and verify a service account JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid service token, None otherwise
    """
    payload = decode_token(token)
    if not payload:
        return None

    # Verify it's a service token
    if payload.get("type") != "service":
        return None

    return payload


def verify_service_token(token: str) -> Optional[Dict]:
    """
    Verify a service token is valid and not revoked.

    Args:
        token: JWT token string

    Returns:
        Token payload if valid and not revoked, None otherwise
    """
    payload = decode_service_token(token)
    if not payload:
        return None

    # Check if token is revoked
    from app.models import get_db

    db = get_db()
    token_record = db(
        db.service_account_tokens.token_jti == payload.get("jti")
    ).select().first()

    if not token_record:
        return None

    if token_record.revoked_at is not None:
        return None

    # Check if service account is active
    service_account = db(
        db.service_accounts.id == payload.get("service_account_id")
    ).select().first()

    if not service_account or not service_account.is_active:
        return None

    return payload


def get_service_account_from_token() -> Optional[dict]:
    """
    Get service account from the current request's token.

    Returns:
        Service account dictionary if valid service token, None otherwise
    """
    # Check if already loaded in request context
    if hasattr(g, "service_account") and g.service_account is not None:
        return g.service_account

    token = get_token_from_header()
    if not token:
        return None

    payload = verify_service_token(token)
    if not payload:
        return None

    # Load service account from database
    from app.models import get_db

    db = get_db()
    service_account = db(
        db.service_accounts.id == payload["service_account_id"]
    ).select().first()

    if not service_account:
        return None

    # Store in request context
    sa_dict = service_account.as_dict()
    sa_dict["token_scopes"] = payload.get("scopes", [])
    sa_dict["token_jti"] = payload.get("jti")
    g.service_account = sa_dict
    g.is_service_account = True
    g.token_scopes = payload.get("scopes", [])

    return sa_dict
