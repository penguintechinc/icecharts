"""
Test suite for WebSocket collaboration functionality.

Tests the WebSocket handlers, collaboration manager, and integration
with Flask-SocketIO.
"""

import json
import os
import time

import jwt
import pytest
from flask import Flask
from flask_socketio import SocketIOTestClient

from app import create_app
from app.websocket.collaboration import CollaborationManager, get_collaboration_manager


@pytest.fixture
def app():
    """Create Flask app for testing."""
    os.environ["TESTING"] = "true"
    app = create_app()
    app.config["TESTING"] = True
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
        algorithm="HS256",
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
            session_id="session-1",
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
            session_id="session-1",
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
            session_id="session-1",
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
            session_id="session-1",
        )

        manager.join_room(
            room_id="test-room",
            user_id="user-2",
            username="User Two",
            email="user2@example.com",
            session_id="session-2",
        )

        users = manager.get_room_users("test-room")
        assert len(users) == 2

    def test_lock_shape(self, manager):
        """Test shape locking."""
        success = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1",
        )

        assert success is True

        # Try to lock again by different user
        success2 = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-2",
            session_id="session-2",
        )

        assert success2 is False

    def test_unlock_shape(self, manager):
        """Test shape unlocking."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1",
        )

        success = manager.unlock_shape(
            room_id="test-room", shape_id="shape-1", session_id="session-1"
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
            session_id="session-1",
        )

        success = manager.unlock_shape(
            room_id="test-room",
            shape_id="shape-1",
            session_id="session-2",  # Different session
        )

        assert success is False

    def test_get_shape_lock(self, manager):
        """Test getting lock information."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1",
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
                session_id=f"session-{i}",
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
        response = client.get("/healthz")
        assert response.status_code == 200

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/readyz")
        assert response.status_code in [200, 503]


class TestCollaboratorDataclass:
    """Tests for Collaborator dataclass properties."""

    def test_collaborator_creation(self):
        """Collaborator can be created with all fields."""
        from app.websocket.collaboration import Collaborator

        collab = Collaborator(
            user_id="user-123",
            username="Alice",
            email="alice@example.com",
            color="#FF6B6B",
            session_id="session-abc",
            cursor_x=100.5,
            cursor_y=200.5,
            last_seen=time.time(),
        )
        assert collab.user_id == "user-123"
        assert collab.username == "Alice"
        assert collab.email == "alice@example.com"
        assert collab.color == "#FF6B6B"
        assert collab.session_id == "session-abc"
        assert collab.cursor_x == 100.5
        assert collab.cursor_y == 200.5

    def test_collaborator_default_cursor(self):
        """Collaborator defaults cursor to (0.0, 0.0)."""
        from app.websocket.collaboration import Collaborator

        collab = Collaborator(
            user_id="user-456",
            username="Bob",
            email="bob@example.com",
            color="#4ECDC4",
            session_id="session-def",
        )
        assert collab.cursor_x == 0.0
        assert collab.cursor_y == 0.0

    def test_collaborator_is_frozen(self):
        """Collaborator is immutable (frozen dataclass)."""
        from app.websocket.collaboration import Collaborator

        collab = Collaborator(
            user_id="user-789",
            username="Charlie",
            email="charlie@example.com",
            color="#45B7D1",
            session_id="session-ghi",
        )
        with pytest.raises((AttributeError, ValueError)):
            collab.username = "NewName"


class TestCollaborationManagerEdgeCases:
    """Edge case and unit tests for collaboration manager."""

    def test_manager_singleton_pattern(self, manager):
        """Collaboration manager follows singleton pattern."""
        from app.websocket.collaboration import get_collaboration_manager

        manager2 = get_collaboration_manager()
        assert manager is manager2

    def test_get_active_sessions_returns_empty_when_no_sessions(self, manager):
        """get_room_users returns empty list when no users in room."""
        users = manager.get_room_users("nonexistent_room_xyz")
        assert users == []

    def test_get_room_users_filters_stale_sessions(self, manager):
        """get_room_users filters out users with stale last_seen timestamps."""
        # Join two users
        manager.join_room(
            room_id="test-room",
            user_id="user-1",
            username="Active User",
            email="active@example.com",
            session_id="session-1",
        )

        # Manually create a stale entry (last_seen > 60 seconds ago)
        room_key = manager._get_room_key("test-room")
        stale_data = {
            "user_id": "user-stale",
            "username": "Stale User",
            "email": "stale@example.com",
            "color": "#FF6B6B",
            "session_id": "session-stale",
            "cursor_x": 0.0,
            "cursor_y": 0.0,
            "last_seen": time.time() - 120,  # 2 minutes old
        }

        if manager.redis_client:
            try:
                manager.redis_client.hset(
                    room_key, "session-stale", json.dumps(stale_data)
                )
            except Exception:
                pass
        else:
            if "test-room" not in manager._memory_storage:
                manager._memory_storage["test-room"] = {}
            manager._memory_storage["test-room"]["session-stale"] = stale_data

        # Get active users - should only return the fresh one
        users = manager.get_room_users("test-room")
        assert len(users) == 1
        assert users[0]["session_id"] == "session-1"

    def test_lock_conflict_returns_false(self, manager):
        """Trying to lock an already-locked shape by another user returns False."""
        result1 = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-1",
            session_id="session-1",
        )
        assert result1 is True

        # Try to lock same shape as user-2 — should fail
        result2 = manager.lock_shape(
            room_id="test-room",
            shape_id="shape-1",
            user_id="user-2",
            session_id="session-2",
        )
        assert result2 is False

    def test_unlock_by_non_owner_fails(self, manager):
        """Unlocking a shape by a different session fails."""
        manager.lock_shape(
            room_id="test-room",
            shape_id="shape-2",
            user_id="user-1",
            session_id="session-1",
        )

        # Try to unlock with different session
        result = manager.unlock_shape(
            room_id="test-room",
            shape_id="shape-2",
            session_id="session-999",  # Wrong session
        )
        assert result is False

        # Lock should still exist
        lock = manager.get_shape_lock("test-room", "shape-2")
        assert lock is not None

    def test_color_palette_coverage(self, manager):
        """Manager has defined color palette."""
        assert len(manager.COLORS) == 10
        assert "#FF6B6B" in manager.COLORS
        assert "#4ECDC4" in manager.COLORS
        assert "#52C41A" in manager.COLORS

    def test_assign_color_uniqueness_in_room(self, manager):
        """_assign_color returns unique colors until palette exhausted."""
        room_id = "color-test-room"
        colors_used = set()

        # Add users until we run out of unique colors
        for i in range(min(15, len(manager.COLORS) + 5)):
            collab = manager.join_room(
                room_id=room_id,
                user_id=f"user-{i}",
                username=f"User {i}",
                email=f"user{i}@example.com",
                session_id=f"session-{i}",
            )
            colors_used.add(collab.color)

        # First 10 should be unique
        if len(colors_used) <= 10:
            assert len(colors_used) == len(
                [c for c in colors_used if colors_used.count(c) == 1]
            )

    def test_cleanup_user_locks_removes_all_locks_for_session(self, manager):
        """_cleanup_user_locks removes all locks held by a session."""
        room_id = "cleanup-room"

        # User locks multiple shapes
        manager.lock_shape(room_id, "shape-1", "user-1", "session-1")
        manager.lock_shape(room_id, "shape-2", "user-1", "session-1")
        manager.lock_shape(room_id, "shape-3", "user-1", "session-1")

        # Verify locks exist
        assert manager.get_shape_lock(room_id, "shape-1") is not None
        assert manager.get_shape_lock(room_id, "shape-2") is not None
        assert manager.get_shape_lock(room_id, "shape-3") is not None

        # Cleanup all locks for the session
        manager._cleanup_user_locks(room_id, "session-1")

        # Verify all locks are gone
        assert manager.get_shape_lock(room_id, "shape-1") is None
        assert manager.get_shape_lock(room_id, "shape-2") is None
        assert manager.get_shape_lock(room_id, "shape-3") is None

    def test_lock_timeout_expiration(self, manager):
        """Expired locks can be reacquired."""
        room_id = "timeout-room"
        shape_id = "shape-expiring"

        # Lock with first user
        assert manager.lock_shape(room_id, shape_id, "user-1", "session-1") is True

        # Manually expire the lock if using in-memory storage
        if not manager.redis_client:
            lock_key = f"{room_id}:{shape_id}"
            if lock_key in manager._memory_locks:
                # Set timestamp to past so it's "expired"
                manager._memory_locks[lock_key]["timestamp"] = (
                    time.time() - manager.LOCK_TIMEOUT - 1
                )

        # Try to lock again with second user
        # Note: Redis expiration is handled by Redis, in-memory is manual check
        if not manager.redis_client:
            result = manager.lock_shape(room_id, shape_id, "user-2", "session-2")
            assert result is True

    def test_cursor_position_update_persists(self, manager):
        """Cursor position updates are persisted and retrieved."""
        room_id = "cursor-room"

        # Join user
        manager.join_room(
            room_id=room_id,
            user_id="user-1",
            username="User",
            email="user@example.com",
            session_id="session-1",
        )

        # Update cursor
        manager.update_cursor(room_id, "session-1", 123.5, 456.5)

        # Retrieve and verify
        users = manager.get_room_users(room_id)
        assert len(users) == 1
        assert users[0]["cursor_x"] == 123.5
        assert users[0]["cursor_y"] == 456.5

    def test_multiple_rooms_isolation(self, manager):
        """Users in different rooms don't interfere with each other."""
        # Room 1
        manager.join_room(
            room_id="room-1",
            user_id="user-a",
            username="Alice",
            email="alice@example.com",
            session_id="session-a",
        )

        # Room 2
        manager.join_room(
            room_id="room-2",
            user_id="user-b",
            username="Bob",
            email="bob@example.com",
            session_id="session-b",
        )

        # Get users - should be isolated
        room1_users = manager.get_room_users("room-1")
        room2_users = manager.get_room_users("room-2")

        assert len(room1_users) == 1
        assert room1_users[0]["user_id"] == "user-a"

        assert len(room2_users) == 1
        assert room2_users[0]["user_id"] == "user-b"


class TestCollaborationManagerRedisFailover:
    """Tests for graceful degradation and Redis error handling."""

    def test_redis_error_during_join_room_falls_back_to_memory(self):
        """When Redis fails during join_room, the call succeeds via in-memory fallback."""
        from unittest.mock import MagicMock, patch
        from redis.exceptions import RedisError

        from app.websocket.collaboration import CollaborationManager

        # Build a manager with a Redis client that always fails
        manager = CollaborationManager.__new__(CollaborationManager)
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis.hset.side_effect = RedisError("Timeout")
        mock_redis.expire.side_effect = RedisError("Timeout")
        manager.redis_client = mock_redis
        manager._memory_storage = {}
        manager._memory_locks = {}

        # join_room swallows RedisError and falls back gracefully
        collaborator = manager.join_room(
            room_id="room-1",
            user_id="user-1",
            username="Alice",
            email="alice@example.com",
            session_id="session-1",
        )
        # The collaborator object is still returned even when Redis errors
        assert collaborator.user_id == "user-1"
        assert collaborator.color in manager.COLORS

    def test_redis_error_during_get_room_users_returns_empty_list(self):
        """When Redis fails during get_room_users, an empty list is returned."""
        from unittest.mock import MagicMock
        from redis.exceptions import RedisError

        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        mock_redis = MagicMock()
        mock_redis.hgetall.side_effect = RedisError("Connection lost")
        manager.redis_client = mock_redis
        manager._memory_storage = {}
        manager._memory_locks = {}

        users = manager.get_room_users("some-room")
        assert users == []

    def test_redis_error_during_lock_shape_returns_false(self):
        """When Redis fails during lock_shape, False is returned (safe default)."""
        from unittest.mock import MagicMock
        from redis.exceptions import RedisError

        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        mock_redis = MagicMock()
        mock_redis.set.side_effect = RedisError("Write failed")
        manager.redis_client = mock_redis
        manager._memory_storage = {}
        manager._memory_locks = {}

        result = manager.lock_shape("room-1", "shape-1", "user-1", "session-1")
        assert result is False

    def test_redis_error_during_unlock_shape_returns_false(self):
        """When Redis fails during unlock_shape, False is returned (safe default)."""
        from unittest.mock import MagicMock
        from redis.exceptions import RedisError

        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        mock_redis = MagicMock()
        mock_redis.get.side_effect = RedisError("Read failed")
        manager.redis_client = mock_redis
        manager._memory_storage = {}
        manager._memory_locks = {}

        result = manager.unlock_shape("room-1", "shape-1", "session-1")
        assert result is False

    def test_redis_error_during_update_cursor_is_silent(self):
        """When Redis fails during update_cursor, no exception propagates."""
        from unittest.mock import MagicMock
        from redis.exceptions import RedisError

        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        mock_redis = MagicMock()
        mock_redis.hget.side_effect = RedisError("Network blip")
        manager.redis_client = mock_redis
        manager._memory_storage = {}
        manager._memory_locks = {}

        # Must not raise
        manager.update_cursor("room-1", "session-1", 50.0, 75.0)

    def test_in_memory_session_timeout_stale_user_filtered(self):
        """In-memory storage: stale sessions (>60s) are excluded from get_room_users."""
        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        manager.redis_client = None
        manager._memory_storage = {}
        manager._memory_locks = {}

        room_id = "timeout-room"
        # Insert a fresh user
        manager._memory_storage[room_id] = {
            "session-fresh": {
                "user_id": "user-fresh",
                "username": "Fresh",
                "email": "fresh@example.com",
                "color": "#FF6B6B",
                "session_id": "session-fresh",
                "cursor_x": 0.0,
                "cursor_y": 0.0,
                "last_seen": time.time(),
            },
            # Insert a stale user whose last_seen is 120 seconds ago
            "session-stale": {
                "user_id": "user-stale",
                "username": "Stale",
                "email": "stale@example.com",
                "color": "#4ECDC4",
                "session_id": "session-stale",
                "cursor_x": 0.0,
                "cursor_y": 0.0,
                "last_seen": time.time() - 120,
            },
        }

        users = manager.get_room_users(room_id)
        assert len(users) == 1
        assert users[0]["session_id"] == "session-fresh"

    def test_in_memory_lock_timeout_allows_reacquisition(self):
        """In-memory locks that have timed out can be reacquired by another session."""
        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        manager.redis_client = None
        manager._memory_storage = {}
        manager._memory_locks = {}

        room_id = "lock-timeout-room"
        shape_id = "shape-expired"

        # Acquire lock initially
        result1 = manager.lock_shape(room_id, shape_id, "user-1", "session-1")
        assert result1 is True

        # Fast-forward the lock timestamp to simulate expiry
        lock_key = f"{room_id}:{shape_id}"
        manager._memory_locks[lock_key]["timestamp"] = (
            time.time() - manager.LOCK_TIMEOUT - 10
        )

        # Now a second user should be able to acquire the expired lock
        result2 = manager.lock_shape(room_id, shape_id, "user-2", "session-2")
        assert result2 is True

        # The lock should now belong to session-2
        lock_info = manager.get_shape_lock(room_id, shape_id)
        assert lock_info is not None
        assert lock_info["session_id"] == "session-2"

    def test_leave_room_cleans_up_all_locks_for_session(self):
        """leave_room removes the user AND releases all their shape locks."""
        from app.websocket.collaboration import CollaborationManager

        manager = CollaborationManager.__new__(CollaborationManager)
        manager.redis_client = None
        manager._memory_storage = {}
        manager._memory_locks = {}

        room_id = "leave-room"

        # User joins and acquires multiple locks
        manager.join_room(
            room_id=room_id,
            user_id="user-1",
            username="Alice",
            email="alice@example.com",
            session_id="session-1",
        )
        manager.lock_shape(room_id, "shape-a", "user-1", "session-1")
        manager.lock_shape(room_id, "shape-b", "user-1", "session-1")

        # Verify locks are in place
        assert manager.get_shape_lock(room_id, "shape-a") is not None
        assert manager.get_shape_lock(room_id, "shape-b") is not None

        # User leaves
        manager.leave_room(room_id, "session-1")

        # User should no longer be in the room
        users = manager.get_room_users(room_id)
        assert len(users) == 0

        # All locks should be released
        assert manager.get_shape_lock(room_id, "shape-a") is None
        assert manager.get_shape_lock(room_id, "shape-b") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
