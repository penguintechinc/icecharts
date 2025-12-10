"""WebSocket module initialization with Flask-SocketIO."""

from typing import Optional
from flask import Flask
from flask_socketio import SocketIO

# Global SocketIO instance
socketio: Optional[SocketIO] = None


def init_socketio(app: Flask) -> SocketIO:
    """
    Initialize Flask-SocketIO with the Flask app.

    Args:
        app: Flask application instance

    Returns:
        SocketIO instance
    """
    global socketio

    socketio = SocketIO(
        app,
        cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"),
        async_mode="threading",
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25,
        manage_session=False,  # Use Flask sessions instead
    )

    # Import and register event handlers
    from . import handlers  # noqa: F401

    return socketio


def get_socketio() -> SocketIO:
    """
    Get the global SocketIO instance.

    Returns:
        SocketIO instance

    Raises:
        RuntimeError: If SocketIO has not been initialized
    """
    if socketio is None:
        raise RuntimeError(
            "SocketIO not initialized. Call init_socketio() first."
        )
    return socketio
