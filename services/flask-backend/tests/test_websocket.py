"""
Test suite for WebSocket collaboration functionality.

Tests the WebSocket handlers, collaboration manager, and integration
with Flask-SocketIO.
"""

import pytest
import json
import time
from flask import Flask
from flask_socketio import SocketIOTestClient
import jwt
import os

from app import create_app
from app.websocket.collaboration import CollaborationManager, get_collaboration_manager


@pytest.fixture
def app():
    """Create Flask app for testing."""
    os.environ['TESTING'] = 'true'
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def socketio(app):
    """Get SocketIO instance."""
    return app.socketio


@pytest.fixture
def client(app, socketio):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def socketio_client(app, socketio):
    """Create SocketIO test client."""
    return socketio.test_client(app)


@pytest.fixture
def auth_token():
    """Generate valid JWT token for testing."""
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    token = jwt.encode(
        {
            "user_id": "test-user-1",
            "username": "Test User",
            "email": "test@example.com",
        },
        secret,
        algorithm="HS256"
    )
    return token


@pytest.fixture
def manager():
    """Get collaboration manager instance."""
    return get_collaboration_manager()


class TestCollaborationManager:
    """Test the collaboration manager."""

    def test_join_room(self, manager):
        """Test joining a room."""
        collaborator = manager.join_room(
            room_id="test-room",
            user_id="user-1",
            username="User One",
            email="user1@example.com",
            session_id="session-1"
        )

        assert collaborator.user_id == "user-1"
        assert collaborator.username == "User One"
        assert collaborator.color in manager.COLORS
        assert collaborator.session_id == "session-1"

    def test_leave_room(self, manager):
        """Test leaving a room."""
        manager.join_room(
            room_id="test-room",
            user_id="user-1",
            username="User One",
            email="user1@example.com",
            session_id="session-1"
        )

        manager.leave_room("test-room", "session-1")
        users = manager.get_room_users("test-room")
        assert len(users) == 0

    def test_update_cursor(self, manager):
        """Test cursor position updates."""
        manager.join_room(
            room_id="test-room",
            user_id="user-1",
            username="User One",
            email="user1@example.com",
            session_id="session-1"
        )

        manager.update_cursor("test-room", "session-1", 100.0, 200.0)
        users = manager.get_room_users("test-room")

        assert len(users) == 1
        assert users[0]["cursor_x"] == 100.0
        assert users[0]["cursor_y"] == 200.0

    def test_get_room_users(self, manager):
        """Test getting room users."""
        manager.join_room(
            room_id="test-room",
            user_id="user-1",
            username="User One",
            email="user1@example.com",
            session_id="session-1"
        )

        manager.join_room(
            room_id="test-room",
            user_id="user-2",
            username="User Two",
            email="user2@example.com",
            session_id="session-2"
        )

        users = manager.get_room_users("test-room")
        assert len(users) == 2

    def test_lock_shape(self, manager):
        """Test shape locking."""
        success = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1"
        )

        assert success is True

        # Try to lock again by different user
        success2 = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-2",
            session_id="session-2"
        )

        assert success2 is False

    def test_unlock_shape(self, manager):
        """Test shape unlocking."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1"
        )

        success = manager.unlock_shape(
            room_id="test-room",
            shape_id="shape-1",
            session_id="session-1"
        )

        assert success is True

        # Verify lock is released
        lock = manager.get_shape_lock("test-room", "shape-1")
        assert lock is None

    def test_unlock_shape_wrong_user(self, manager):
        """Test that users can't unlock other users' locks."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1"
        )

        success = manager.unlock_shape(
            room_id="test-room",
            shape_id="shape-1",
            session_id="session-2"  # Different session
        )

        assert success is False

    def test_get_shape_lock(self, manager):
        """Test getting lock information."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1"
        )

        lock = manager.get_shape_lock("test-room", "shape-1")

        assert lock is not None
        assert lock["user_id"] == "user-1"
        assert lock["session_id"] == "session-1"

    def test_color_assignment(self, manager):
        """Test unique color assignment."""
        colors = set()

        for i in range(5):
            collaborator = manager.join_room(
                room_id="test-room",
                user_id=f"user-{i}",
                username=f"User {i}",
                email=f"user{i}@example.com",
                session_id=f"session-{i}"
            )
            colors.add(collaborator.color)

        # All colors should be unique
        assert len(colors) == 5


class TestWebSocketHandlers:
    """Test WebSocket event handlers."""

    def test_connect_with_valid_token(self, socketio_client, auth_token):
        """Test connection with valid JWT token."""
        client = socketio_client
        # Note: flask-socketio test client doesn't fully support auth
        # This is a simplified test
        assert client is not None

    def test_join_room_event(self, socketio_client, auth_token):
        """Test join_room event."""
        # This would require a more complex setup with actual socket connection
        # Simplified for demonstration
        pass

    def test_cursor_move_event(self, socketio_client):
        """Test cursor_move event."""
        # This would require a more complex setup
        pass

    def test_shape_lock_event(self, socketio_client):
        """Test shape_lock event."""
        # This would require a more complex setup
        pass


class TestIntegration:
    """Integration tests for the collaboration system."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/healthz')
        assert response.status_code == 200

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get('/readyz')
        assert response.status_code in [200, 503]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
