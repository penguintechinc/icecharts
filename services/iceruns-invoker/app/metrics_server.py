"""Flask server for Prometheus metrics endpoint."""

import logging
import os

from app.metrics import MetricsRecorder
from flask import Flask, Response

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_metrics_app() -> Flask:
    """Create Flask app with metrics endpoint."""
    app = Flask(__name__)

    @app.route("/metrics", methods=["GET"])
    def metrics():
        """Prometheus metrics endpoint."""
        metrics_output = MetricsRecorder.get_metrics_output()
        return Response(metrics_output, mimetype="text/plain; version=0.0.4")

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return {"status": "healthy"}, 200

    return app


def run_metrics_server(host: str = "0.0.0.0", port: int = 8081):
    """Run metrics server on separate port."""
    app = create_metrics_app()
    logger.info(f"Starting metrics server on {host}:{port}")
    app.run(host=host, port=port, debug=False)
