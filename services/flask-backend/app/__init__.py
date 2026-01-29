"""IceCharts Flask Application Package."""

import logging
import os

from flask import Flask
from flask_cors import CORS

from .config import Config
from .models import init_db


__version__ = "0.1.0"


logger = logging.getLogger(__name__)


def create_app(config_class=None):
    """
    Create and configure Flask application.

    Args:
        config_class: Configuration class to use (defaults based on FLASK_ENV)

    Returns:
        Configured Flask app instance
    """
    if config_class is None:
        from .config import get_config
        config_class = get_config(os.getenv("FLASK_ENV", "development"))

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database
    init_db(app)

    # Configure CORS
    CORS(app, origins=app.config["CORS_ORIGINS"])

    # Initialize WebSocket support
    from .websocket import init_socketio
    socketio = init_socketio(app)
    app.socketio = socketio

    # Initialize licensing
    try:
        from .licensing import initialize_licensing
        if initialize_licensing():
            logger.info("License server integration enabled")
        else:
            logger.info("License server integration disabled (no license key)")
    except Exception as e:
        logger.warning(f"Failed to initialize licensing: {e}")

    # Register blueprints
    from .api import api_v1_bp
    app.register_blueprint(api_v1_bp)

    # Health check endpoint
    @app.route("/healthz")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}, 200

    @app.route("/readyz")
    def readiness_check():
        """Readiness check endpoint."""
        try:
            from .models import get_db
            db = get_db()
            db.executesql("SELECT 1")
            return {"status": "ready"}, 200
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return {"status": "not_ready", "error": str(e)}, 503

    return app
