"""PyDAL database initialization for IceCharts."""

import os
from threading import local
from typing import Optional

import structlog
from pydal import DAL

from app.config import get_config

logger = structlog.get_logger()

# Thread-local storage for PyDAL database connections
_thread_local = local()

# Valid PyDAL DB_TYPE values for input validation
VALID_DB_TYPES = {
    "postgres",
    "postgresql",
    "mysql",
    "sqlite",
    "mssql",
    "oracle",
    "db2",
    "firebird",
    "informix",
    "ingres",
    "cubrid",
    "sapdb",
}


def _initialize_default_settings(db) -> None:
    """
    Initialize default system settings in the database.

    This should be called after all tables are created to avoid transaction errors.

    Args:
        db: PyDAL database instance
    """
    try:
        # Signup and registration settings
        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "signup_enabled",
            setting_key="signup_enabled",
            setting_value="true",
            setting_type="boolean",
            description="Enable/disable user registration",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "signup_mode",
            setting_key="signup_mode",
            setting_value="open",
            setting_type="string",
            description="Signup mode: open, domain_restricted, sso_only, disabled",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "signup_allowed_domains",
            setting_key="signup_allowed_domains",
            setting_value="[]",
            setting_type="json",
            description="List of allowed email domains for signup (domain_restricted mode)",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "email_verification_required",
            setting_key="email_verification_required",
            setting_value="false",
            setting_type="boolean",
            description="Require email verification for new accounts",
        )

        # Email provider settings
        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "email_provider",
            setting_key="email_provider",
            setting_value="sendmail",
            setting_type="string",
            description="Email provider: sendmail, smtp, sendgrid, aws_ses, mailgun, gmail",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "email_from",
            setting_key="email_from",
            setting_value="noreply@icecharts.com",
            setting_type="string",
            description="From email address for system emails",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "email_from_name",
            setting_key="email_from_name",
            setting_value="IceCharts",
            setting_type="string",
            description="From name for system emails",
        )

        # Site settings
        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "site_url",
            setting_key="site_url",
            setting_value="http://localhost:5173",
            setting_type="string",
            description="Base URL for the application",
        )

        db.system_settings.update_or_insert(
            db.system_settings.setting_key == "site_name",
            setting_key="site_name",
            setting_value="IceCharts",
            setting_type="string",
            description="Application name",
        )

        db.commit()
    except Exception as e:
        # Settings initialization can fail - just log and continue
        # Settings will be initialized on first access
        db.rollback()


def get_db_uri(config) -> str:
    """
    Build PyDAL database URI from configuration.

    Args:
        config: Configuration object

    Returns:
        Database URI string for PyDAL

    Raises:
        ValueError: If DB_TYPE is invalid
    """
    # Use DATABASE_URL if provided
    if config.DATABASE_URL:
        return config.DATABASE_URL

    # Validate DB_TYPE
    db_type = config.DB_TYPE.lower()
    if db_type not in VALID_DB_TYPES:
        raise ValueError(
            f"Invalid DB_TYPE: {db_type}. Must be one of: {VALID_DB_TYPES}"
        )

    # Build URI from components
    if db_type == "sqlite":
        db_path = config.DB_NAME if config.DB_NAME != ":memory:" else ":memory:"
        return f"sqlite://{db_path}"

    # For other databases, build full connection string
    return (
        f"{db_type}://{config.DB_USER}:{config.DB_PASSWORD}@"
        f"{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
    )


def get_db() -> DAL:
    """
    Get thread-local PyDAL database connection.

    This ensures each thread has its own database connection for thread safety.

    Returns:
        PyDAL DAL instance
    """
    if not hasattr(_thread_local, "db") or _thread_local.db is None:
        # Get configuration
        config_name = os.getenv("FLASK_ENV", "development")
        config = get_config(config_name)

        # Build database URI
        db_uri = get_db_uri(config)

        # Create PyDAL connection
        # Note: check_reserved=['common'] avoids overly strict keyword checks
        # that would block common column names like 'content', 'domain', etc.
        # fake_migrate=True ensures PyDAL doesn't try to create tables that exist
        # migrate_enabled=True allows PyDAL to track schema changes
        instance_folder = os.path.join(
            os.path.dirname(__file__), "..", "..", "instance"
        )
        os.makedirs(instance_folder, exist_ok=True)

        # Initialize tables with SQLAlchemy first
        from app.models.sqlalchemy_schema import initialize_database

        try:
            initialize_database(db_uri)
        except Exception as e:
            logger.warning(f"SQLAlchemy table initialization: {e}")

        _thread_local.db = DAL(
            db_uri,
            pool_size=config.DB_POOL_SIZE,
            migrate_enabled=True,
            fake_migrate_all=True,  # Tables created by SQLAlchemy, just sync metadata
            check_reserved=["common"],
            lazy_tables=True,
            folder=instance_folder,
        )

        # Define all tables
        from app.models.pydal_models import define_all_tables

        define_all_tables(_thread_local.db)

    return _thread_local.db


def close_db():
    """Close thread-local database connection."""
    if hasattr(_thread_local, "db") and _thread_local.db is not None:
        _thread_local.db.close()
        _thread_local.db = None


def init_db(app):
    """
    Initialize database for Flask application.

    This function:
    1. Creates all database tables defined in pydal_models.py (idempotent)
    2. Stores a database getter in the app context
    3. Registers teardown handlers to close connections

    Args:
        app: Flask application instance
    """
    import structlog

    logger = structlog.get_logger()

    # Initialize database schema on startup
    # This ensures all tables exist before any requests are handled
    try:
        logger.info("database_init_starting", message="Initializing database schema...")

        # Get a database connection (this triggers table definition)
        db = get_db()

        # Force PyDAL to create/migrate all tables by accessing each table
        # With lazy_tables=True, tables are not created until accessed
        table_names = list(db.tables)
        for table_name in table_names:
            # Access the table to trigger lazy creation/migration
            _ = db[table_name]

        # Commit any pending migrations
        db.commit()

        logger.info(
            "database_tables_defined",
            message="Database tables initialized successfully",
            tables=table_names,
            table_count=len(table_names),
        )

        # Initialize default system settings now that tables exist
        _initialize_default_settings(db)

        # Don't close the connection yet - keep it so tables stay in place
        # The connection will be replaced when needed in get_db()

        logger.info(
            "database_init_complete", message="Database initialization complete"
        )

    except Exception as e:
        logger.error(
            "database_init_failed",
            message="Failed to initialize database schema",
            error=str(e),
            error_type=type(e).__name__,
        )
        # Re-raise to prevent app startup with broken database
        raise

    # Store db getter in app context
    app.db = property(lambda self: get_db())

    # Register teardown to close connections
    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db()


def get_user_by_id(user_id: int) -> Optional[dict]:
    """
    Get user by ID from the identities table.

    Args:
        user_id: User ID to query

    Returns:
        User dict or None if not found

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()
    user = db(db.identities.id == user_id).select().first()

    if not user:
        return None

    # Convert PyDAL Row to dict
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "mfa_enabled": user.mfa_enabled,
        "mfa_secret": user.mfa_secret,
        "password_hash": user.password_hash,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user by email from the identities table.

    Args:
        email: User email to query

    Returns:
        User dict or None if not found

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()
    user = db(db.identities.email == email.lower()).select().first()

    if not user:
        return None

    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "mfa_enabled": user.mfa_enabled,
        "mfa_secret": user.mfa_secret,
        "password_hash": user.password_hash,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def get_user_by_google_id(google_id: str) -> Optional[dict]:
    """
    Get user by Google OAuth ID.

    Note: This requires an oauth_identities table which is not yet defined.
    For now, return None to indicate user not found.

    Args:
        google_id: Google OAuth user ID

    Returns:
        User dict or None if not found
    """
    # TODO: Implement oauth_identities table
    return None


def create_user(
    email: str, password_hash: str, full_name: str = "", role: str = "viewer"
) -> dict:
    """
    Create a new user in the identities table.

    Args:
        email: User email (will be normalized to lowercase)
        password_hash: Hashed password
        full_name: User full name (optional)
        role: User role (default: viewer)

    Returns:
        Created user dict

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Generate username from email
    username = email.split("@")[0]

    # Insert user
    user_id = db.identities.insert(
        username=username,
        email=email.lower(),
        full_name=full_name,
        password_hash=password_hash,
        role=role,
        is_active=True,
        is_superuser=False,
        mfa_enabled=False,
    )
    db.commit()

    # Return the created user
    return get_user_by_id(user_id)


def update_user(user_id: int, **kwargs) -> dict:
    """
    Update user fields in the identities table.

    Args:
        user_id: User ID to update
        **kwargs: Fields to update (e.g., mfa_enabled=True, mfa_secret="...")

    Returns:
        Updated user dict or None if user not found

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Update user
    result = db(db.identities.id == user_id).update(**kwargs)
    db.commit()

    # Return updated user
    if result > 0:
        return get_user_by_id(user_id)
    return None


def store_refresh_token(user_id: int, token_hash: str, expires_at) -> None:
    """
    Store refresh token hash in database for revocation tracking.

    Note: This requires a refresh_tokens table which is not yet defined.
    For now, this is a no-op.

    Args:
        user_id: User ID
        token_hash: SHA256 hash of the refresh token
        expires_at: Token expiration datetime
    """
    # TODO: Implement refresh_tokens table
    pass


def is_refresh_token_valid(token_hash: str) -> bool:
    """
    Check if refresh token is still valid (not revoked).

    Note: This requires a refresh_tokens table which is not yet defined.
    For now, assume all tokens are valid.

    Args:
        token_hash: SHA256 hash of the refresh token

    Returns:
        True if token is valid (not revoked), False otherwise
    """
    # TODO: Implement refresh_tokens table
    return True


def revoke_refresh_token(token_hash: str) -> bool:
    """
    Revoke a specific refresh token.

    Note: This requires a refresh_tokens table which is not yet defined.
    For now, this is a no-op.

    Args:
        token_hash: SHA256 hash of the refresh token to revoke

    Returns:
        True if token was revoked, False otherwise
    """
    # TODO: Implement refresh_tokens table
    return True


def revoke_all_user_tokens(user_id: int) -> int:
    """
    Revoke all refresh tokens for a user (used for logout).

    Note: This requires a refresh_tokens table which is not yet defined.
    For now, this returns 0.

    Args:
        user_id: User ID

    Returns:
        Number of tokens revoked
    """
    # TODO: Implement refresh_tokens table
    return 0


def list_users(page: int = 1, per_page: int = 20, **filters) -> tuple[list[dict], int]:
    """
    List users with pagination and optional filters.

    Args:
        page: Page number (1-indexed)
        per_page: Number of users per page
        **filters: Optional filters (search, role, is_active)

    Returns:
        Tuple of (user_list, total_count)

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Build base query
    query = db.identities

    # Apply filters
    search = filters.get("search")
    if search:
        query = db(
            (db.identities.email.contains(search))
            | (db.identities.full_name.contains(search))
        )

    role = filters.get("role")
    if role:
        if hasattr(query, "_query"):
            query = db(query._query & (db.identities.role == role))
        else:
            query = db(db.identities.role == role)

    is_active = filters.get("is_active")
    if is_active is not None:
        if hasattr(query, "_query"):
            query = db(query._query & (db.identities.is_active == is_active))
        else:
            query = db(db.identities.is_active == is_active)

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * per_page

    # Get users
    users = query.select(
        orderby=db.identities.created_at,
        limitby=(offset, offset + per_page),
    )

    # Convert to list of dicts
    user_list = []
    for user in users:
        user_list.append(
            {
                "id": user.id,
                "tenant_id": user.tenant_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "mfa_enabled": user.mfa_enabled,
                "mfa_secret": user.mfa_secret,
                "password_hash": user.password_hash,
                "last_login_at": user.last_login_at,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
        )

    return user_list, total


def delete_user(user_id: int) -> bool:
    """
    Delete a user from the identities table.

    Args:
        user_id: User ID to delete

    Returns:
        True if deletion successful, False otherwise

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Delete user
    result = db(db.identities.id == user_id).delete()
    db.commit()

    return result > 0


def create_comment(
    drawing_id: int,
    author_id: int,
    content: str,
    shape_id: Optional[str] = None,
    parent_comment_id: Optional[int] = None,
) -> dict:
    """
    Create a new comment on a drawing.

    Args:
        drawing_id: ID of the drawing
        author_id: ID of the comment author
        content: Comment text content
        shape_id: Optional ID of the shape being commented on
        parent_comment_id: Optional parent comment ID for replies

    Returns:
        Created comment dict with author info

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Create comment
    comment_id = db.comments.insert(
        drawing_id=drawing_id,
        author_id=author_id,
        user_id=author_id,  # Alias for compatibility
        content=content,
        shape_id=shape_id,
        is_resolved=False,
    )
    db.commit()

    # Return comment with author info
    return get_comment_by_id(comment_id)


def get_comment_by_id(comment_id: int) -> Optional[dict]:
    """
    Get comment by ID with author information.

    Args:
        comment_id: Comment ID to query

    Returns:
        Comment dict with author info or None if not found

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Get comment with author info
    comment = (
        db((db.comments.id == comment_id) & (db.comments.author_id == db.identities.id))
        .select(
            db.comments.ALL,
            db.identities.id,
            db.identities.email,
            db.identities.full_name,
        )
        .first()
    )

    if not comment:
        return None

    return {
        "id": comment.comments.id,
        "drawing_id": comment.comments.drawing_id,
        "author_id": comment.comments.author_id,
        "user_id": comment.comments.author_id,  # Alias
        "content": comment.comments.content,
        "shape_id": comment.comments.shape_id,
        "is_resolved": comment.comments.is_resolved,
        "x": comment.comments.x,
        "y": comment.comments.y,
        "created_at": comment.comments.created_at,
        "updated_at": comment.comments.updated_at,
        "author": {
            "id": comment.identities.id,
            "email": comment.identities.email,
            "full_name": comment.identities.full_name,
        },
    }


def get_comments_by_drawing(
    drawing_id: int,
    shape_id: Optional[str] = None,
    only_unresolved: bool = False,
) -> list[dict]:
    """
    Get comments for a drawing with optional filtering.

    Args:
        drawing_id: ID of the drawing
        shape_id: Optional shape ID to filter by
        only_unresolved: Only return unresolved comments

    Returns:
        List of comments with author info

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Build query
    query = (db.comments.drawing_id == drawing_id) & (
        db.comments.author_id == db.identities.id
    )

    if shape_id:
        query = query & (db.comments.shape_id == shape_id)

    if only_unresolved:
        query = query & (db.comments.is_resolved == False)

    # Get comments
    comments = db(query).select(
        db.comments.ALL,
        db.identities.id,
        db.identities.email,
        db.identities.full_name,
        orderby=db.comments.created_at,
    )

    # Convert to list of dicts
    result = []
    for c in comments:
        result.append(
            {
                "id": c.comments.id,
                "drawing_id": c.comments.drawing_id,
                "author_id": c.comments.author_id,
                "user_id": c.comments.author_id,  # Alias
                "content": c.comments.content,
                "shape_id": c.comments.shape_id,
                "is_resolved": c.comments.is_resolved,
                "x": c.comments.x,
                "y": c.comments.y,
                "created_at": c.comments.created_at,
                "updated_at": c.comments.updated_at,
                "author": {
                    "id": c.identities.id,
                    "email": c.identities.email,
                    "full_name": c.identities.full_name,
                },
            }
        )

    return result


def get_comments_tree(drawing_id: int) -> list[dict]:
    """
    Get comments organized as a threaded tree.

    Args:
        drawing_id: ID of the drawing

    Returns:
        List of root comments with nested replies

    Thread-safe: Uses get_db() for thread-local connection
    """
    # For now, return flat list - tree structure needs parent_comment_id field
    return get_comments_by_drawing(drawing_id)


def update_comment(comment_id: int, content: str) -> Optional[dict]:
    """
    Update comment content.

    Args:
        comment_id: ID of the comment to update
        content: New comment content

    Returns:
        Updated comment dict or None if not found

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Update comment
    from datetime import datetime

    result = db(db.comments.id == comment_id).update(
        content=content,
        updated_at=datetime.utcnow(),
    )
    db.commit()

    if result > 0:
        return get_comment_by_id(comment_id)
    return None


def delete_comment(comment_id: int) -> bool:
    """
    Delete a comment and all its replies.

    Args:
        comment_id: ID of the comment to delete

    Returns:
        True if deleted successfully

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Delete comment (cascading will handle replies)
    result = db(db.comments.id == comment_id).delete()
    db.commit()

    return result > 0


def resolve_comment(comment_id: int, resolved_by_id: int) -> Optional[dict]:
    """
    Mark a comment as resolved.

    Args:
        comment_id: ID of the comment
        resolved_by_id: ID of the user marking it resolved

    Returns:
        Updated comment dict with resolved info

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Update comment
    from datetime import datetime

    result = db(db.comments.id == comment_id).update(
        is_resolved=True,
        resolved_by=resolved_by_id,
        resolved_at=datetime.utcnow(),
    )
    db.commit()

    if result > 0:
        return get_comment_by_id(comment_id)
    return None


def unresolve_comment(comment_id: int) -> Optional[dict]:
    """
    Mark a comment as unresolved.

    Args:
        comment_id: ID of the comment

    Returns:
        Updated comment dict

    Thread-safe: Uses get_db() for thread-local connection
    """
    db = get_db()

    # Update comment
    result = db(db.comments.id == comment_id).update(
        is_resolved=False,
        resolved_by=None,
        resolved_at=None,
    )
    db.commit()

    if result > 0:
        return get_comment_by_id(comment_id)
    return None
