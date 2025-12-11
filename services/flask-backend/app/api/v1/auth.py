"""Authentication Endpoints for API v1."""

import hashlib
import secrets
from datetime import datetime

import bcrypt
import jwt
from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import (
    create_user,
    get_db,
    get_user_by_email,
    get_user_by_google_id,
    get_user_by_id,
    is_refresh_token_valid,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
    update_user,
)
from ...oauth import GoogleOAuthHandler
from ...schemas.auth_schemas import LoginRequest, RegisterRequest
from ...utils.validation import validate_json

auth_v1_bp = Blueprint("auth_v1", __name__, url_prefix="/auth")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: int, role: str) -> str:
    """Create JWT access token."""
    expires = datetime.utcnow() + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expires,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    """Create JWT refresh token and store hash in database."""
    expires = datetime.utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expires,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")

    # Store hash of token in database for revocation
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    store_refresh_token(user_id, token_hash, expires)

    return token, expires


@auth_v1_bp.route("/login", methods=["POST"])
@validate_json(LoginRequest)
def login(validated_data: LoginRequest):
    """Login endpoint - returns access and refresh tokens."""
    # Email is already validated by Pydantic
    email = validated_data.email.lower()
    password = validated_data.password

    # Find user
    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # Verify password
    if not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    # Check if user is active
    if not user.get("is_active"):
        return jsonify({"error": "Account is deactivated"}), 401

    # Generate tokens
    access_token = create_access_token(user["id"], user["role"])
    refresh_token, refresh_expires = create_refresh_token(user["id"])

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "role": user["role"],
        },
    }), 200


@auth_v1_bp.route("/register", methods=["POST"])
@validate_json(RegisterRequest)
def register(validated_data: RegisterRequest):
    """Register new user (creates viewer role by default)."""
    # Email is already validated and normalized by Pydantic
    email = validated_data.email.lower()
    password = validated_data.password
    full_name = validated_data.full_name

    # Check if user exists
    existing = get_user_by_email(email)
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    # Create user
    password_hash = hash_password(password)
    user = create_user(
        email=email,
        password_hash=password_hash,
        full_name=full_name or "",
        role="viewer",  # Default role for self-registration
    )

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "role": user["role"],
        },
    }), 201


@auth_v1_bp.route("/logout", methods=["POST"])
@auth_required
def logout():
    """Logout endpoint - revokes all refresh tokens for user."""
    user = get_current_user()

    # Revoke all user's refresh tokens
    revoked_count = revoke_all_user_tokens(user["id"])

    return jsonify({
        "message": "Successfully logged out",
        "tokens_revoked": revoked_count,
    }), 200


@auth_v1_bp.route("/me", methods=["GET"])
@auth_required
def get_me():
    """Get current user info - used to verify token is still valid."""
    user = get_current_user()
    return jsonify({
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user["role"],
    }), 200


@auth_v1_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh access token using refresh token."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    refresh_token = data.get("refresh_token", "")

    if not refresh_token:
        return jsonify({"error": "Refresh token required"}), 400

    # Decode token
    try:
        payload = jwt.decode(
            refresh_token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid refresh token"}), 401

    # Verify token type
    if payload.get("type") != "refresh":
        return jsonify({"error": "Invalid token type"}), 401

    # Check if token is revoked
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    if not is_refresh_token_valid(token_hash):
        return jsonify({"error": "Refresh token has been revoked"}), 401

    # Get user
    user_id = int(payload["sub"])
    user = get_user_by_id(user_id)
    if not user or not user.get("is_active"):
        return jsonify({"error": "User not found or deactivated"}), 401

    # Revoke old refresh token
    revoke_refresh_token(token_hash)

    # Generate new tokens
    access_token = create_access_token(user["id"], user["role"])
    new_refresh_token, refresh_expires = create_refresh_token(user["id"])

    return jsonify({
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
    }), 200


@auth_v1_bp.route("/mfa/enable", methods=["POST"])
@auth_required
def enable_mfa():
    """Enable MFA for current user."""
    user = get_current_user()
    db = get_db()

    # Generate MFA secret
    import pyotp
    secret = pyotp.random_base32()

    # Store MFA secret (encrypted in production)
    update_user(user["id"], mfa_secret=secret, mfa_enabled=False)

    # Generate provisioning URI for QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="IceCharts"
    )

    return jsonify({
        "message": "MFA setup initiated",
        "secret": secret,
        "provisioning_uri": provisioning_uri,
        "qr_code_url": f"/api/v1/auth/mfa/qrcode?secret={secret}",
    }), 200


@auth_v1_bp.route("/mfa/verify", methods=["POST"])
@auth_required
def verify_mfa():
    """Verify MFA code and complete setup."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    code = data.get("code", "").strip()

    if not code:
        return jsonify({"error": "MFA code required"}), 400

    # Get user's MFA secret
    db = get_db()
    user_record = db(db.users.id == user["id"]).select().first()

    if not user_record or not user_record.mfa_secret:
        return jsonify({"error": "MFA not initiated"}), 400

    # Verify code
    import pyotp
    totp = pyotp.TOTP(user_record.mfa_secret)

    if not totp.verify(code, valid_window=1):
        return jsonify({"error": "Invalid MFA code"}), 401

    # Enable MFA for user
    update_user(user["id"], mfa_enabled=True)

    return jsonify({
        "message": "MFA enabled successfully",
        "mfa_enabled": True,
    }), 200


@auth_v1_bp.route("/mfa/disable", methods=["POST"])
@auth_required
def disable_mfa():
    """Disable MFA for current user."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    password = data.get("password", "")

    if not password:
        return jsonify({"error": "Password required to disable MFA"}), 400

    # Verify password
    user_record = get_user_by_id(user["id"])
    if not verify_password(password, user_record["password_hash"]):
        return jsonify({"error": "Invalid password"}), 401

    # Disable MFA
    update_user(user["id"], mfa_enabled=False, mfa_secret=None)

    return jsonify({
        "message": "MFA disabled successfully",
        "mfa_enabled": False,
    }), 200


@auth_v1_bp.route("/google", methods=["GET"])
def google_login():
    """Redirect to Google OAuth authorization endpoint."""
    # Generate CSRF protection state
    state = secrets.token_urlsafe(32)

    # Store state in session for verification
    from flask import session
    session["oauth_state"] = state

    # Get Google authorization URL
    auth_url = GoogleOAuthHandler.get_google_auth_url(state)

    return jsonify({
        "auth_url": auth_url,
    }), 200


@auth_v1_bp.route("/google/callback", methods=["POST"])
def google_callback():
    """Handle Google OAuth callback - exchange code for tokens and create/link user."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    code = data.get("code", "").strip()
    state = data.get("state", "").strip()

    if not code:
        return jsonify({"error": "Authorization code required"}), 400

    # Verify CSRF state
    from flask import session
    stored_state = session.get("oauth_state")
    if not stored_state or stored_state != state:
        return jsonify({"error": "Invalid state parameter - CSRF validation failed"}), 401

    # Clear state from session
    session.pop("oauth_state", None)

    try:
        # Exchange code for tokens
        access_token, token_data = GoogleOAuthHandler.handle_google_callback(code)

        # Fetch user info from Google
        google_user = GoogleOAuthHandler.get_google_user_info(access_token)

        # Create or link user
        user, is_new = GoogleOAuthHandler.create_or_link_user(google_user)

        if not user.get("is_active"):
            return jsonify({"error": "Account is deactivated"}), 401

        # Generate JWT tokens
        jwt_access_token = create_access_token(user["id"], user["role"])
        jwt_refresh_token, refresh_expires = create_refresh_token(user["id"])

        return jsonify({
            "access_token": jwt_access_token,
            "refresh_token": jwt_refresh_token,
            "token_type": "Bearer",
            "expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "role": user["role"],
            },
            "is_new_user": is_new,
        }), 200

    except ValueError as e:
        return jsonify({"error": f"Authentication failed: {str(e)}"}), 401
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500
