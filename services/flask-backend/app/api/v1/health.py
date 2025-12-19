"""Health check endpoints."""

from flask import Blueprint, jsonify

health_v1_bp = Blueprint("health", __name__, url_prefix="/health")


@health_v1_bp.route("", methods=["GET"], strict_slashes=False)
@health_v1_bp.route("/", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@health_v1_bp.route("/ready", methods=["GET"], strict_slashes=False)
def readiness():
    """Readiness check endpoint."""
    return jsonify({"status": "ready"}), 200


@health_v1_bp.route("/z", methods=["GET"], strict_slashes=False)
def healthz():
    """Health check endpoint alias (/healthz)."""
    return health()
