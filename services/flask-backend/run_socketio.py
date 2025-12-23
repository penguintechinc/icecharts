#!/usr/bin/env python3
"""
Run Flask application with SocketIO support.

This script properly starts the Flask application with Flask-SocketIO,
which is required for WebSocket collaboration features.

Usage:
    python run_socketio.py
    python run_socketio.py --host 0.0.0.0 --port 5000
    python run_socketio.py --debug
"""

import os
import argparse
from app import create_app


def main():
    """Main entry point for running Flask with SocketIO."""
    parser = argparse.ArgumentParser(
        description='Run Flask application with SocketIO support'
    )
    parser.add_argument(
        '--host',
        default=os.getenv('FLASK_HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000'))),
        help='Port to bind to (default: $PORT or 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--allow-unsafe-werkzeug',
        action='store_true',
        help='Allow running with Werkzeug (not recommended for production)'
    )

    args = parser.parse_args()

    # Create Flask app
    app = create_app()

    # Get SocketIO instance from app
    socketio = app.socketio

    # Production warning
    if not args.debug and not args.allow_unsafe_werkzeug:
        print("=" * 70)
        print("WARNING: Running in production mode with Werkzeug")
        print("For production, use: gunicorn with eventlet/gevent worker")
        print("Example: gunicorn --worker-class eventlet -w 1 'app:create_app()'")
        print("=" * 70)
        print()

    # Run with SocketIO
    print(f"Starting Flask-SocketIO server on {args.host}:{args.port}")
    print(f"Debug mode: {args.debug}")
    print(f"WebSocket support: Enabled")
    print()

    try:
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            allow_unsafe_werkzeug=args.allow_unsafe_werkzeug or args.debug,
        )
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
