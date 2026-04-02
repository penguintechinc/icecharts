"""Pytest Configuration and Fixtures for Flask Backend Tests."""

import os
import sys


# PostgreSQL test database connection details - MUST be set before app imports
# Uses the icecharts-postgres Docker container.
# TEST_DB_HOST env var overrides; otherwise auto-discovers via docker inspect.
def _discover_pg_host() -> str:
    if "TEST_DB_HOST" in os.environ:
        return os.environ["TEST_DB_HOST"]
    try:
        import subprocess

        ip = subprocess.check_output(
            [
                "docker",
                "inspect",
                "icecharts-postgres",
                "--format={{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if ip:
            return ip
    except Exception:
        pass
    return "172.18.0.4"  # fallback: known Docker bridge IP


_PG_HOST = _discover_pg_host()
_PG_PORT = os.environ.get("TEST_DB_PORT", "5432")
_PG_DB = os.environ.get("TEST_DB_NAME", "icecharts_test")
_PG_USER = os.environ.get("TEST_DB_USER", "icecharts_user")
_PG_PASSWORD = os.environ.get("TEST_DB_PASSWORD", "changeme")

# Set DB env vars BEFORE importing app (decouple reads env at import time)
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "true"
os.environ["DB_TYPE"] = "postgresql"
os.environ["DB_HOST"] = _PG_HOST
os.environ["DB_PORT"] = _PG_PORT
os.environ["DB_NAME"] = _PG_DB
os.environ["DB_USER"] = _PG_USER
os.environ["DB_PASSWORD"] = _PG_PASSWORD
os.environ["RATELIMIT_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.api.v1.auth import create_access_token, hash_password
from app.config import TestingConfig
from app.models import close_db, create_user, get_db, store_refresh_token


@pytest.fixture(scope="session")
def app() -> Flask:
    """Create and configure a test Flask application with PostgreSQL.

    Session-scoped: the app and database schema are created once for the
    entire test session.  Per-test data isolation is handled by the
    ``_clean_data`` autouse fixture which truncates all tables between
    tests.
    """
    import glob

    import psycopg2
    from pydal import DAL

    # Close any leftover PyDAL connection
    close_db()

    instance_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "instance"
    )
    os.makedirs(instance_folder, exist_ok=True)

    db_uri = f"postgres://{_PG_USER}:{_PG_PASSWORD}@" f"{_PG_HOST}:{_PG_PORT}/{_PG_DB}"

    # ── Phase 1: Clean slate ──────────────────────────────────────
    # DROP all tables directly via psycopg2 (bypasses PyDAL)
    try:
        conn = psycopg2.connect(
            host=_PG_HOST,
            port=_PG_PORT,
            dbname=_PG_DB,
            user=_PG_USER,
            password=_PG_PASSWORD,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = %s AND pid != pg_backend_pid() "
            "AND state = 'idle in transaction'",
            (_PG_DB,),
        )
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = [r[0] for r in cur.fetchall()]
        if tables:
            cur.execute(f"DROP TABLE IF EXISTS {', '.join(tables)} CASCADE")
        cur.close()
        conn.close()
    except Exception:
        pass  # First run or DB not ready

    # Remove ALL PyDAL migration tracking files
    for f in glob.glob(os.path.join(instance_folder, "*.table")):
        try:
            os.remove(f)
        except OSError:
            pass

    # ── Phase 2: Create all tables via PyDAL migration ────────────
    # Do this BEFORE create_app() so init_db() finds them already present
    from app.models.pydal_models import define_all_tables

    migrate_db = DAL(
        db_uri,
        pool_size=1,
        migrate_enabled=True,
        fake_migrate_all=False,
        check_reserved=["common"],
        lazy_tables=True,
        folder=instance_folder,
    )
    define_all_tables(migrate_db)

    # Force all lazy tables to resolve (triggers CREATE TABLE DDL)
    for table_name in list(migrate_db.tables):
        _ = migrate_db[table_name]

    migrate_db.commit()
    migrate_db.close()

    # ── Phase 3: Create Flask app ─────────────────────────────────
    # Now create_app() calls init_db() which calls get_db() with
    # fake_migrate_all=True.  Since tables already exist in PG and
    # .table files were written by Phase 2, this just syncs metadata.
    app = create_app(config_class=TestingConfig)

    with app.app_context():
        db = get_db()

        # Seed a default tenant (idempotent)
        db.tenants.update_or_insert(
            db.tenants.slug == "test-tenant",
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
        )
        db.commit()

        yield app

        # Close PyDAL connection at end of session
        close_db()


# ── Per-test data cleanup ─────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_data(app: Flask):
    """Truncate ALL data tables before each test for isolation.

    Uses TRUNCATE ... RESTART IDENTITY CASCADE to:
    - Remove all rows
    - Reset auto-increment sequences to 1
    - Handle FK constraints automatically
    """
    with app.app_context():
        db = get_db()
        # Rollback any failed transaction before truncating
        try:
            db.rollback()
        except Exception:
            pass
        all_tables = list(db.tables)
        if all_tables:
            quoted = ", ".join(f'"{t}"' for t in all_tables)
            try:
                db.executesql(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
            except Exception:
                # Transaction may be in error state; rollback and retry
                try:
                    db.rollback()
                    db.executesql(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE")
                except Exception:
                    pass
        # Ensure we are in a clean transaction state before re-seeding.
        # The TRUNCATE block above may have silently swallowed an exception,
        # leaving the psycopg2 connection in an aborted state.  A rollback
        # here is always safe (no-op when no transaction is active) and
        # prevents the subsequent update_or_insert from failing with
        # "InFailedSqlTransaction".
        try:
            db.rollback()
        except Exception:
            pass

        # Re-seed the default tenant after truncation
        try:
            db.tenants.update_or_insert(
                db.tenants.slug == "test-tenant",
                name="Test Tenant",
                slug="test-tenant",
                is_active=True,
            )
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass
    yield


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
            token = create_access_token(user["id"], role)
            return {
                "id": user["id"],
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
                "token": token,
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
        expired_time = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": "1",
            "role": "viewer",
            "type": "access",
            "exp": expired_time,
            "iat": datetime.now(UTC),
        }
        import jwt

        return jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm="HS256")


@pytest.fixture
def refresh_token(app: Flask, test_user: dict) -> str:
    """Create a valid refresh token."""
    with app.app_context():
        expires = datetime.now(UTC) + timedelta(days=30)
        payload = {
            "sub": str(test_user["id"]),
            "type": "refresh",
            "exp": expires,
            "iat": datetime.now(UTC),
        }
        import hashlib

        import jwt

        token = jwt.encode(payload, app.config["JWT_SECRET_KEY"], algorithm="HS256")
        # Store token hash in database
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        store_refresh_token(test_user["id"], token_hash, expires)
        return token
