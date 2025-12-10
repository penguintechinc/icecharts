"""PyDAL database initialization for IceCharts."""

import os
from threading import local

from pydal import DAL

from app.config import get_config

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
        _thread_local.db = DAL(
            db_uri,
            pool_size=config.DB_POOL_SIZE,
            migrate_enabled=True,
            check_reserved=["all"],
            lazy_tables=True,
            folder=os.path.join(os.path.dirname(__file__), "..", "..", "instance"),
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

    Args:
        app: Flask application instance
    """
    # Store db getter in app context
    app.db = property(lambda self: get_db())

    # Register teardown to close connections
    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db()
