"""Main Flask application for IceCharts."""

import logging
import os

import structlog
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from prometheus_flask_exporter import PrometheusMetrics

from app.config import get_config
from app.models import init_db

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global SocketIO instance
socketio = SocketIO()


def create_app(config_name: str = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    config = get_config(config_name)
    app.config.from_object(config)
    config.init_app(app)

    # Initialize extensions
    _init_extensions(app)

    # Initialize database
    init_db(app)

    # Create default admin user if needed
    _create_default_admin(app)

    # Initialize SocketIO
    if app.config.get("SOCKETIO_ENABLED"):
        _init_socketio(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    # Health check endpoint
    @app.route("/healthz")
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "icecharts"}), 200

    # Readiness check endpoint
    @app.route("/readyz")
    def readiness_check():
        """Readiness check endpoint."""
        return jsonify({"status": "ready"}), 200

    logger.info(
        "icecharts_app_created",
        config=config_name,
        debug=app.config["DEBUG"],
        version=app.config["APP_VERSION"],
    )

    return app


def _init_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    # CORS
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        methods=app.config["CORS_METHODS"],
        allow_headers=app.config["CORS_ALLOW_HEADERS"],
        supports_credentials=app.config.get("CORS_SUPPORTS_CREDENTIALS", True),
    )

    # Prometheus Metrics
    if app.config.get("METRICS_ENABLED"):
        metrics = PrometheusMetrics(app)
        metrics.info(
            "icecharts_app_info",
            "IceCharts Application",
            version=app.config["APP_VERSION"],
        )

    logger.info("extensions_initialized")


def _init_socketio(app: Flask) -> None:
    """Initialize SocketIO for real-time collaboration."""
    socketio.init_app(
        app,
        cors_allowed_origins=app.config["SOCKETIO_CORS_ALLOWED_ORIGINS"],
        message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"),
        async_mode="threading",
    )

    # Register WebSocket handlers after SocketIO is initialized
    from app.api.v1.collaboration_socket import register_handlers

    register_handlers(socketio)

    logger.info("socketio_initialized")


def _register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    from app.api.v1 import api_v1_bp

    api_prefix = app.config["API_PREFIX"]

    # Register API v1 blueprints
    app.register_blueprint(api_v1_bp, url_prefix=api_prefix)

    logger.info("blueprints_registered", api_prefix=api_prefix)


def _register_error_handlers(app: Flask) -> None:
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        logger.warning("bad_request", error=str(error))
        return jsonify({"error": "Bad Request", "message": "Invalid request"}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized."""
        return (
            jsonify({"error": "Unauthorized", "message": "Authentication required"}),
            401,
        )

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden."""
        return (
            jsonify({"error": "Forbidden", "message": "Insufficient permissions"}),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({"error": "Not Found", "message": "Resource not found"}), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Rate Limit Exceeded."""
        return (
            jsonify({"error": "Rate Limit Exceeded", "message": "Too many requests"}),
            429,
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error("internal_server_error", error=str(error))
        return (
            jsonify({"error": "Internal Server Error", "message": "An error occurred"}),
            500,
        )

    logger.info("error_handlers_registered")


def _create_default_admin(app: Flask) -> None:
    """Create default admin user if no users exist."""
    from app.auth import hash_password
    from app.models import create_user, get_db, get_user_by_email

    with app.app_context():
        try:
            db = get_db()

            # Force table creation for lazy tables by accessing them
            # This ensures the underlying database tables are created
            _ = db.tenants
            _ = db.identities

            # Ensure default tenant exists (required for foreign key constraint)
            tenant_count = db(db.tenants).count()
            if tenant_count == 0:
                logger.info("creating_default_tenant")
                db.tenants.insert(
                    name="Default Organization",
                    slug="default",
                    subscription_tier="community",
                    is_active=True,
                )
                db.commit()
                logger.info("default_tenant_created")

            user_count = db(db.identities).count()

            if user_count == 0:
                admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@localhost")
                admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

                # Check if admin already exists
                existing = get_user_by_email(admin_email)
                if not existing:
                    logger.info("creating_default_admin", email=admin_email)
                    create_user(
                        email=admin_email,
                        password_hash=hash_password(admin_password),
                        full_name="System Administrator",
                        role="admin",
                    )
                    logger.warning(
                        "default_admin_created",
                        email=admin_email,
                        message="Change the default password immediately!",
                    )
                else:
                    logger.info("admin_already_exists")
            else:
                logger.info("users_exist_skip_default_admin", user_count=user_count)
        except Exception as e:
            logger.error("failed_to_create_default_admin", error=str(e))


def create_asgi_app() -> "ASGIApplication":
    """
    Create ASGI-compatible application for uvicorn.

    Flask is WSGI, so we wrap it with WsgiToAsgi adapter.

    Returns:
        ASGI application that wraps Flask
    """
    from asgiref.wsgi import WsgiToAsgi

    flask_app = create_app()
    return WsgiToAsgi(flask_app)


if __name__ == "__main__":
    # Development server (use uvicorn in production)
    import uvicorn

    app = create_app()
    uvicorn.run(
        "app.main:create_asgi_app",
        factory=True,
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        reload=True,
    )
