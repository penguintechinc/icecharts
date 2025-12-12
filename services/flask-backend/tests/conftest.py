"""Pytest Configuration and Fixtures for Flask Backend Tests."""

import os
import sys
from datetime import datetime, timedelta

import pytest
from flask import Flask
from pydal import DAL

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.api.v1.auth import create_access_token, hash_password
from app.config import TestingConfig
from app.models import (
    create_user,
    get_db,
    store_refresh_token,
)


@pytest.fixture
def app() -> Flask:
    """Create and configure a test Flask application."""
    # Create app with testing config
    os.environ["FLASK_ENV"] = "testing"
    os.environ["TESTING"] = "true"
    os.environ["DB_TYPE"] = "sqlite"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["RATELIMIT_ENABLED"] = "false"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"

    app = create_app()
    app.config.from_object(TestingConfig)

    # Create application context
    with app.app_context():
        from app.models import init_db

        # Initialize database
        init_db(app)
        yield app


@pytest.fixture
def client(app: Flask):
    """Create a test client for the Flask app."""
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def db(app: Flask):
    """Get database instance for tests."""
    with app.app_context():
        from app.models import get_db

        return get_db()


@pytest.fixture
def test_user_data() -> dict:
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "role": "viewer",
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Provide test admin user data."""
    return {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "Admin User",
        "role": "admin",
    }


@pytest.fixture
def create_test_user(app: Flask):
    """Factory fixture to create test users."""

    def _create_user(
        email: str = "user@example.com",
        password: str = "TestPass123!",
        full_name: str = "Test User",
        role: str = "viewer",
    ) -> dict:
        with app.app_context():
            user = create_user(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=role,
            )
            return {
                "id": user.id,
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
            }

    return _create_user


@pytest.fixture
def test_user(create_test_user) -> dict:
    """Create a default test user."""
    return create_test_user(email="test@example.com")


@pytest.fixture
def test_admin(create_test_user) -> dict:
    """Create a default test admin user."""
    return create_test_user(email="admin@example.com", role="admin")


@pytest.fixture
def auth_headers(app: Flask, test_user: dict) -> dict:
    """Create authorization headers with valid JWT token."""
    with app.app_context():
        access_token = create_access_token(test_user["id"], test_user["role"])
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(app: Flask, test_admin: dict) -> dict:
    """Create authorization headers with admin JWT token."""
    with app.app_context():
        access_token = create_access_token(test_admin["id"], test_admin["role"])
        return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def valid_jwt_token(app: Flask, test_user: dict) -> str:
    """Create a valid JWT token."""
    with app.app_context():
        return create_access_token(test_user["id"], test_user["role"])


@pytest.fixture
def expired_jwt_token(app: Flask) -> str:
    """Create an expired JWT token."""
    with app.app_context():
        expired_time = datetime.utcnow() - timedelta(hours=1)
        payload = {
            "sub": "1",
            "role": "viewer",
            "type": "access",
            "exp": expired_time,
            "iat": datetime.utcnow(),
        }
        import jwt

        return jwt.encode(
            payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
        )


@pytest.fixture
def refresh_token(app: Flask, test_user: dict) -> str:
    """Create a valid refresh token."""
    with app.app_context():
        expires = datetime.utcnow() + timedelta(days=30)
        payload = {
            "sub": str(test_user["id"]),
            "type": "refresh",
            "exp": expires,
            "iat": datetime.utcnow(),
        }
        import jwt
        import hashlib

        token = jwt.encode(
            payload, app.config["JWT_SECRET_KEY"], algorithm="HS256"
        )
        # Store token hash in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        store_refresh_token(test_user["id"], token_hash, expires)
        return token
