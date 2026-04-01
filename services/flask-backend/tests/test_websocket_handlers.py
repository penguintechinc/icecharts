"""Test suite for WebSocket event handlers.

Tests cover JWT token verification, connection/disconnection,
room joining/leaving, cursor movement, and shape locking.
"""

from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta, UTC

import jwt
import pytest


class TestVerifyToken:
    """Tests for JWT token verification."""

    @pytest.fixture
    def app_secret(self, app):
        """Get the app's JWT secret key."""
        return app.config["JWT_SECRET_KEY"]

    def test_verify_token_valid_jwt_returns_payload(self, app, app_secret):
        """Test verify_token with valid JWT returns decoded payload."""
        # Import handler inside context to get the app instance
        with app.app_context():
            from app.websocket.handlers import verify_token

            payload = {
                "sub": "1",
                "user_id": 1,
                "username": "testuser",
                "email": "test@example.com",
                "role": "viewer",
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            result = verify_token(token)
            assert result["user_id"] == 1
            assert result["username"] == "testuser"
            assert result["email"] == "test@example.com"

    def test_verify_token_missing_token_raises_error(self, app):
        """Test verify_token with missing token raises error."""
        with app.app_context():
            from app.websocket.handlers import verify_token

            with pytest.raises(jwt.InvalidTokenError):
                verify_token("")

    def test_verify_token_invalid_signature_raises_error(self, app, app_secret):
        """Test verify_token with invalid signature raises error."""
        with app.app_context():
            from app.websocket.handlers import verify_token

            payload = {"sub": "1", "user_id": 1}
            token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

            with pytest.raises(jwt.InvalidTokenError):
                verify_token(token)

    def test_verify_token_expired_jwt_raises_error(self, app, app_secret):
        """Test verify_token with expired JWT raises error."""
        with app.app_context():
            from app.websocket.handlers import verify_token

            expired_time = datetime.now(UTC) - timedelta(hours=1)
            payload = {
                "sub": "1",
                "user_id": 1,
                "exp": expired_time,
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            with pytest.raises(jwt.InvalidTokenError):
                verify_token(token)

    def test_verify_token_missing_user_id_still_decodes(self, app, app_secret):
        """Test verify_token decodes token even if user_id missing."""
        with app.app_context():
            from app.websocket.handlers import verify_token

            payload = {
                "sub": "1",
                "username": "testuser",
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            result = verify_token(token)
            assert "user_id" not in result
            assert result["username"] == "testuser"


class TestHandleConnect:
    """Tests for WebSocket connection handler."""

    @pytest.fixture
    def app_secret(self, app):
        """Get the app's JWT secret key."""
        return app.config["JWT_SECRET_KEY"]

    def test_handle_connect_valid_token_succeeds(self, app, app_secret):
        """Test handle_connect with valid token succeeds."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            payload = {
                "sub": "1",
                "user_id": 1,
                "username": "testuser",
                "email": "test@example.com",
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    mock_request.sid = "session-123"
                    result = handle_connect({"token": token})

                    assert result is True
                    mock_emit.assert_called_once()
                    call_args = mock_emit.call_args
                    assert call_args[0][0] == "connected"

    def test_handle_connect_without_token_rejects(self, app):
        """Test handle_connect without token rejects connection."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                result = handle_connect({})

            assert result is False

    def test_handle_connect_with_none_token_rejects(self, app):
        """Test handle_connect with None token rejects connection."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                result = handle_connect({"token": None})

            assert result is False

    def test_handle_connect_invalid_token_rejects(self, app):
        """Test handle_connect with invalid token rejects connection."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                result = handle_connect({"token": "invalid-token"})

            assert result is False

    def test_handle_connect_token_without_user_id_rejects(self, app, app_secret):
        """Test handle_connect with token missing user_id rejects."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            payload = {
                "sub": "1",
                "username": "testuser",
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                result = handle_connect({"token": token})

            assert result is False

    def test_handle_connect_stores_user_data(self, app, app_secret):
        """Test handle_connect stores user data in request."""
        with app.app_context():
            from app.websocket.handlers import handle_connect

            payload = {
                "sub": "1",
                "user_id": 42,
                "username": "testuser",
                "email": "test@example.com",
            }
            token = jwt.encode(payload, app_secret, algorithm="HS256")

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit"):
                    mock_request.sid = "session-123"
                    handle_connect({"token": token})

                    assert hasattr(mock_request, "sid_user_data")
                    user_data = mock_request.sid_user_data
                    assert user_data["user_id"] == 42
                    assert user_data["username"] == "testuser"
                    assert user_data["email"] == "test@example.com"


class TestHandleDisconnect:
    """Tests for WebSocket disconnection handler."""

    def test_handle_disconnect_no_error(self, app):
        """Test handle_disconnect completes without error."""
        with app.app_context():
            from app.websocket.handlers import handle_disconnect

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                mock_request.sid_user_data = {"user_id": 1}

                # Should not raise any exception
                handle_disconnect()

    def test_handle_disconnect_handles_missing_user_data(self, app):
        """Test handle_disconnect handles missing user data gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_disconnect

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                (
                    delattr(mock_request, "sid_user_data")
                    if hasattr(mock_request, "sid_user_data")
                    else None
                )

                # Should not raise any exception
                handle_disconnect()


class TestHandleJoinRoom:
    """Tests for WebSocket join room handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.join_room.return_value = MagicMock(color="#FF0000")
        manager.get_room_users.return_value = [
            {"user_id": 1, "username": "user1", "color": "#FF0000"}
        ]
        return manager

    def test_join_room_valid_drawing_id_joins(self, app, mock_collaboration_manager):
        """Test join_room with valid room_id joins successfully."""
        with app.app_context():
            from app.websocket.handlers import handle_join_room

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch("app.websocket.handlers.join_room") as mock_join:
                        with patch(
                            "app.websocket.handlers.manager",
                            mock_collaboration_manager,
                        ):
                            mock_request.sid = "session-123"
                            mock_request.sid_user_data = {
                                "user_id": 1,
                                "username": "testuser",
                                "email": "test@example.com",
                            }

                            handle_join_room({"room_id": "drawing-1"})

                            mock_join.assert_called_once_with("drawing-1")
                            # Verify room_joined event was emitted
                            assert any(
                                call[0][0] == "room_joined"
                                for call in mock_emit.call_args_list
                            )

    def test_join_room_no_room_id_returns_error(self, app):
        """Test join_room without room_id returns error."""
        with app.app_context():
            from app.websocket.handlers import handle_join_room

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    mock_request.sid = "session-123"
                    mock_request.sid_user_data = {"user_id": 1}

                    handle_join_room({})

                    # Verify error was emitted
                    assert any(
                        call[0][0] == "error" for call in mock_emit.call_args_list
                    )

    def test_join_room_not_authenticated_returns_error(self, app):
        """Test join_room without authentication returns error."""
        with app.app_context():
            from app.websocket.handlers import handle_join_room

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    mock_request.sid = "session-123"
                    # No sid_user_data attribute

                    handle_join_room({"room_id": "drawing-1"})

                    # Verify error was emitted
                    assert any(
                        call[0][0] == "error" for call in mock_emit.call_args_list
                    )

    def test_join_room_broadcasts_presence(self, app, mock_collaboration_manager):
        """Test join_room broadcasts presence update to room."""
        with app.app_context():
            from app.websocket.handlers import handle_join_room

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch("app.websocket.handlers.join_room"):
                        with patch(
                            "app.websocket.handlers.manager",
                            mock_collaboration_manager,
                        ):
                            mock_request.sid = "session-123"
                            mock_request.sid_user_data = {
                                "user_id": 1,
                                "username": "testuser",
                                "email": "test@example.com",
                            }

                            handle_join_room({"room_id": "drawing-1"})

                            # Verify presence_update was broadcast
                            presence_calls = [
                                call
                                for call in mock_emit.call_args_list
                                if call[0][0] == "presence_update"
                            ]
                            assert len(presence_calls) > 0


class TestHandleLeaveRoom:
    """Tests for WebSocket leave room handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.get_room_users.return_value = []
        return manager

    def test_leave_room_valid_room_leaves(self, app, mock_collaboration_manager):
        """Test leave_room with valid room_id leaves successfully."""
        with app.app_context():
            from app.websocket.handlers import handle_leave_room

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch("app.websocket.handlers.leave_room") as mock_leave:
                        with patch(
                            "app.websocket.handlers.manager",
                            mock_collaboration_manager,
                        ):
                            mock_request.sid = "session-123"
                            mock_request.sid_user_data = {
                                "user_id": 1,
                                "username": "testuser",
                            }

                            handle_leave_room({"room_id": "drawing-1"})

                            mock_leave.assert_called_once_with("drawing-1")

    def test_leave_room_no_room_id_returns_gracefully(self, app):
        """Test leave_room without room_id returns gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_leave_room

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                mock_request.sid_user_data = {"user_id": 1}

                # Should not raise exception
                handle_leave_room({})


class TestHandleCursorMove:
    """Tests for WebSocket cursor movement handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        return manager

    def test_cursor_move_broadcasts_to_room(self, app, mock_collaboration_manager):
        """Test cursor_move broadcasts position to room."""
        with app.app_context():
            from app.websocket.handlers import handle_cursor_move

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {
                            "user_id": 1,
                            "username": "testuser",
                        }

                        handle_cursor_move(
                            {
                                "room_id": "drawing-1",
                                "x": 100,
                                "y": 200,
                            }
                        )

                        # Verify cursor_moved event was emitted
                        assert any(
                            call[0][0] == "cursor_moved"
                            for call in mock_emit.call_args_list
                        )
                        mock_collaboration_manager.update_cursor.assert_called_once_with(
                            "drawing-1", "session-123", 100, 200
                        )

    def test_cursor_move_no_room_id_returns_gracefully(self, app):
        """Test cursor_move without room_id returns gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_cursor_move

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                mock_request.sid_user_data = {"user_id": 1}

                # Should not raise exception
                handle_cursor_move({"x": 100, "y": 200})

    def test_cursor_move_with_default_coordinates(
        self, app, mock_collaboration_manager
    ):
        """Test cursor_move uses default coordinates if not provided."""
        with app.app_context():
            from app.websocket.handlers import handle_cursor_move

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit"):
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_cursor_move({"room_id": "drawing-1"})

                        # Should use default x=0, y=0
                        mock_collaboration_manager.update_cursor.assert_called_once_with(
                            "drawing-1", "session-123", 0, 0
                        )


class TestHandleShapeLock:
    """Tests for WebSocket shape locking handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.lock_shape.return_value = True
        manager.get_shape_lock.return_value = {"user_id": 1}
        return manager

    def test_lock_shape_success(self, app, mock_collaboration_manager):
        """Test lock_shape succeeds and broadcasts lock."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_lock

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_lock(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                            }
                        )

                        mock_collaboration_manager.lock_shape.assert_called_once()
                        # Verify shape_locked event was emitted
                        assert any(
                            call[0][0] == "shape_locked"
                            for call in mock_emit.call_args_list
                        )

    def test_lock_shape_already_locked(self, app, mock_collaboration_manager):
        """Test lock_shape when shape is already locked."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_lock

            mock_collaboration_manager.lock_shape.return_value = False
            mock_collaboration_manager.get_shape_lock.return_value = {"user_id": 2}

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_lock(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                            }
                        )

                        # Verify shape_lock_failed event was emitted
                        assert any(
                            call[0][0] == "shape_lock_failed"
                            for call in mock_emit.call_args_list
                        )

    def test_lock_shape_no_room_id_returns_error(self, app):
        """Test lock_shape without room_id returns error."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_lock

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    mock_request.sid = "session-123"
                    mock_request.sid_user_data = {"user_id": 1}

                    handle_shape_lock({"shape_id": "shape-123"})

                    # Verify error was emitted
                    assert any(
                        call[0][0] == "error" for call in mock_emit.call_args_list
                    )

    def test_lock_shape_no_shape_id_returns_error(self, app):
        """Test lock_shape without shape_id returns error."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_lock

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    mock_request.sid = "session-123"
                    mock_request.sid_user_data = {"user_id": 1}

                    handle_shape_lock({"room_id": "drawing-1"})

                    # Verify error was emitted
                    assert any(
                        call[0][0] == "error" for call in mock_emit.call_args_list
                    )


class TestHandleShapeUnlock:
    """Tests for WebSocket shape unlocking handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.unlock_shape.return_value = True
        return manager

    def test_unlock_shape_success(self, app, mock_collaboration_manager):
        """Test unlock_shape succeeds and broadcasts unlock."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_unlock

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_unlock(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                            }
                        )

                        mock_collaboration_manager.unlock_shape.assert_called_once()
                        # Verify shape_unlocked event was emitted
                        assert any(
                            call[0][0] == "shape_unlocked"
                            for call in mock_emit.call_args_list
                        )

    def test_unlock_shape_not_locked(self, app, mock_collaboration_manager):
        """Test unlock_shape when shape is not locked."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_unlock

            mock_collaboration_manager.unlock_shape.return_value = False

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_unlock(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                            }
                        )

                        # No shape_unlocked event should be emitted
                        unlock_calls = [
                            call
                            for call in mock_emit.call_args_list
                            if call[0][0] == "shape_unlocked"
                        ]
                        assert len(unlock_calls) == 0

    def test_unlock_shape_no_room_id_returns_gracefully(self, app):
        """Test unlock_shape without room_id returns gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_unlock

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                mock_request.sid_user_data = {"user_id": 1}

                # Should not raise exception
                handle_shape_unlock({"shape_id": "shape-123"})


class TestHandleShapeUpdate:
    """Tests for WebSocket shape update handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.get_shape_lock.return_value = {"session_id": "session-123"}
        return manager

    def test_shape_update_with_lock_broadcasts(self, app, mock_collaboration_manager):
        """Test shape_update with valid lock broadcasts update."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_update

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_update(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                                "shape_data": {"x": 100, "y": 200},
                            }
                        )

                        # Verify shape_updated event was emitted
                        assert any(
                            call[0][0] == "shape_updated"
                            for call in mock_emit.call_args_list
                        )

    def test_shape_update_without_lock_returns_error(
        self, app, mock_collaboration_manager
    ):
        """Test shape_update without lock returns error."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_update

            mock_collaboration_manager.get_shape_lock.return_value = None

            with patch("app.websocket.handlers.request") as mock_request:
                with patch("app.websocket.handlers.emit") as mock_emit:
                    with patch(
                        "app.websocket.handlers.manager",
                        mock_collaboration_manager,
                    ):
                        mock_request.sid = "session-123"
                        mock_request.sid_user_data = {"user_id": 1}

                        handle_shape_update(
                            {
                                "room_id": "drawing-1",
                                "shape_id": "shape-123",
                                "shape_data": {"x": 100, "y": 200},
                            }
                        )

                        # Verify error was emitted
                        assert any(
                            call[0][0] == "error" for call in mock_emit.call_args_list
                        )

    def test_shape_update_missing_room_id_returns_gracefully(self, app):
        """Test shape_update without room_id returns gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_shape_update

            with patch("app.websocket.handlers.request") as mock_request:
                mock_request.sid = "session-123"
                mock_request.sid_user_data = {"user_id": 1}

                # Should not raise exception
                handle_shape_update(
                    {
                        "shape_id": "shape-123",
                        "shape_data": {"x": 100, "y": 200},
                    }
                )


class TestHandleRequestPresence:
    """Tests for WebSocket presence request handler."""

    @pytest.fixture
    def mock_collaboration_manager(self):
        """Create mock collaboration manager."""
        manager = MagicMock()
        manager.get_room_users.return_value = [
            {
                "user_id": 1,
                "username": "user1",
                "color": "#FF0000",
            }
        ]
        return manager

    def test_request_presence_returns_users(self, app, mock_collaboration_manager):
        """Test request_presence returns current room users."""
        with app.app_context():
            from app.websocket.handlers import handle_request_presence

            with patch("app.websocket.handlers.emit") as mock_emit:
                with patch(
                    "app.websocket.handlers.manager",
                    mock_collaboration_manager,
                ):
                    handle_request_presence({"room_id": "drawing-1"})

                    # Verify presence_update was emitted
                    assert any(
                        call[0][0] == "presence_update"
                        for call in mock_emit.call_args_list
                    )

    def test_request_presence_no_room_id_returns_gracefully(self, app):
        """Test request_presence without room_id returns gracefully."""
        with app.app_context():
            from app.websocket.handlers import handle_request_presence

            # Should not raise exception
            handle_request_presence({})
