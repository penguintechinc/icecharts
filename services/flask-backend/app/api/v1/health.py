"""Health check endpoints for IceCharts API."""

from flask import Blueprint, jsonify

from app.models import get_db

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz", methods=["GET"])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON response with health status
    """
    try:
        db = get_db()
        db.executesql("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@health_bp.route("/readyz", methods=["GET"])
def readiness_check():
    """
    Readiness check endpoint.

    Returns:
        JSON response with readiness status
    """
    try:
        db = get_db()
        db.executesql("SELECT 1")
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "not_ready", "error": str(e)}), 503
