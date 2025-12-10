"""WebSocket event handlers for real-time collaboration."""

from typing import Dict, Any
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
import jwt
import os

from . import get_socketio
from .collaboration import get_collaboration_manager
from ..models import get_db


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return user data.

    Args:
        token: JWT token string

    Returns:
        User data dict

    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    return jwt.decode(token, secret, algorithms=["HS256"])


# Get global instances
socketio = get_socketio()
manager = get_collaboration_manager()


@socketio.on("connect")
def handle_connect(auth: Dict[str, Any]) -> bool:
    """
    Handle WebSocket connection with JWT authentication.

    Args:
        auth: Authentication data containing 'token'

    Returns:
        True if connection accepted, False otherwise
    """
    try:
        # Verify JWT token
        token = auth.get("token") if auth else None
        if not token:
            print("Connection rejected: No token provided")
            return False

        user_data = verify_token(token)
        user_id = user_data.get("user_id")

        if not user_id:
            print("Connection rejected: Invalid token")
            return False

        # Store user data in session
        request.sid_user_data = {
            "user_id": user_id,
            "username": user_data.get("username", "Anonymous"),
            "email": user_data.get("email", ""),
        }

        print(f"User {user_id} connected with session {request.sid}")
        emit("connected", {"session_id": request.sid})
        return True

    except jwt.InvalidTokenError as e:
        print(f"Connection rejected: Invalid token - {e}")
        return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle WebSocket disconnection and cleanup."""
    try:
        # Get user's rooms and clean up
        session_id = request.sid
        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id", "unknown")

        print(f"User {user_id} disconnected (session {session_id})")

        # Note: Flask-SocketIO automatically removes from rooms on disconnect
        # but we need to update collaboration state

    except Exception as e:
        print(f"Disconnect error: {e}")


@socketio.on("join_room")
def handle_join_room(data: Dict[str, Any]) -> None:
    """
    Handle user joining a drawing room.

    Args:
        data: Contains 'room_id'
    """
    try:
        room_id = data.get("room_id")
        if not room_id:
            emit("error", {"message": "room_id is required"})
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        username = user_data.get("username", "Anonymous")
        email = user_data.get("email", "")
        session_id = request.sid

        if not user_id:
            emit("error", {"message": "Not authenticated"})
            return

        # Join Socket.IO room
        join_room(room_id)

        # Register in collaboration manager
        collaborator = manager.join_room(
            room_id, user_id, username, email, session_id
        )

        # Notify user of successful join
        emit(
            "room_joined",
            {
                "room_id": room_id,
                "user_id": user_id,
                "color": collaborator.color,
            },
        )

        # Get all room users
        room_users = manager.get_room_users(room_id)

        # Broadcast presence update to all users in room
        emit(
            "presence_update",
            {"users": room_users},
            room=room_id,
        )

        print(f"User {user_id} joined room {room_id}")

    except Exception as e:
        print(f"Join room error: {e}")
        emit("error", {"message": f"Failed to join room: {str(e)}"})


@socketio.on("leave_room")
def handle_leave_room(data: Dict[str, Any]) -> None:
    """
    Handle user leaving a drawing room.

    Args:
        data: Contains 'room_id'
    """
    try:
        room_id = data.get("room_id")
        if not room_id:
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        session_id = request.sid

        # Leave Socket.IO room
        leave_room(room_id)

        # Unregister from collaboration manager
        manager.leave_room(room_id, session_id)

        # Get updated room users
        room_users = manager.get_room_users(room_id)

        # Broadcast presence update to remaining users
        emit(
            "presence_update",
            {"users": room_users},
            room=room_id,
        )

        print(f"User {user_id} left room {room_id}")

    except Exception as e:
        print(f"Leave room error: {e}")


@socketio.on("cursor_move")
def handle_cursor_move(data: Dict[str, Any]) -> None:
    """
    Handle cursor position updates.

    Args:
        data: Contains 'room_id', 'x', 'y'
    """
    try:
        room_id = data.get("room_id")
        x = data.get("x", 0)
        y = data.get("y", 0)

        if not room_id:
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        session_id = request.sid

        # Update cursor position
        manager.update_cursor(room_id, session_id, x, y)

        # Broadcast cursor position to other users in room
        emit(
            "cursor_moved",
            {
                "user_id": user_id,
                "session_id": session_id,
                "x": x,
                "y": y,
            },
            room=room_id,
            include_self=False,
        )

    except Exception as e:
        print(f"Cursor move error: {e}")


@socketio.on("shape_lock")
def handle_shape_lock(data: Dict[str, Any]) -> None:
    """
    Handle request to lock a shape for editing.

    Args:
        data: Contains 'room_id', 'shape_id'
    """
    try:
        room_id = data.get("room_id")
        shape_id = data.get("shape_id")

        if not room_id or not shape_id:
            emit(
                "error",
                {"message": "room_id and shape_id are required"},
            )
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        session_id = request.sid

        # Try to acquire lock
        success = manager.lock_shape(room_id, shape_id, user_id, session_id)

        if success:
            # Notify user of successful lock
            emit(
                "shape_locked",
                {
                    "room_id": room_id,
                    "shape_id": shape_id,
                    "user_id": user_id,
                },
            )

            # Broadcast lock to other users
            emit(
                "shape_locked",
                {
                    "room_id": room_id,
                    "shape_id": shape_id,
                    "user_id": user_id,
                },
                room=room_id,
                include_self=False,
            )

            print(f"User {user_id} locked shape {shape_id}")
        else:
            # Get current lock holder
            lock_info = manager.get_shape_lock(room_id, shape_id)
            emit(
                "shape_lock_failed",
                {
                    "room_id": room_id,
                    "shape_id": shape_id,
                    "locked_by": lock_info.get("user_id") if lock_info else None,
                },
            )

    except Exception as e:
        print(f"Shape lock error: {e}")
        emit("error", {"message": f"Failed to lock shape: {str(e)}"})


@socketio.on("shape_unlock")
def handle_shape_unlock(data: Dict[str, Any]) -> None:
    """
    Handle request to unlock a shape.

    Args:
        data: Contains 'room_id', 'shape_id'
    """
    try:
        room_id = data.get("room_id")
        shape_id = data.get("shape_id")

        if not room_id or not shape_id:
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        session_id = request.sid

        # Try to release lock
        success = manager.unlock_shape(room_id, shape_id, session_id)

        if success:
            # Notify user of successful unlock
            emit(
                "shape_unlocked",
                {
                    "room_id": room_id,
                    "shape_id": shape_id,
                },
            )

            # Broadcast unlock to other users
            emit(
                "shape_unlocked",
                {
                    "room_id": room_id,
                    "shape_id": shape_id,
                },
                room=room_id,
                include_self=False,
            )

            print(f"User {user_id} unlocked shape {shape_id}")

    except Exception as e:
        print(f"Shape unlock error: {e}")


@socketio.on("shape_update")
def handle_shape_update(data: Dict[str, Any]) -> None:
    """
    Handle shape updates and broadcast to other users.

    Args:
        data: Contains 'room_id', 'shape_id', 'shape_data'
    """
    try:
        room_id = data.get("room_id")
        shape_id = data.get("shape_id")
        shape_data = data.get("shape_data")

        if not room_id or not shape_id or not shape_data:
            return

        user_data = getattr(request, "sid_user_data", {})
        user_id = user_data.get("user_id")
        session_id = request.sid

        # Verify user has lock on shape
        lock_info = manager.get_shape_lock(room_id, shape_id)
        if not lock_info or lock_info.get("session_id") != session_id:
            emit(
                "error",
                {
                    "message": "You don't have lock on this shape",
                    "shape_id": shape_id,
                },
            )
            return

        # Broadcast shape update to other users
        emit(
            "shape_updated",
            {
                "room_id": room_id,
                "shape_id": shape_id,
                "shape_data": shape_data,
                "user_id": user_id,
            },
            room=room_id,
            include_self=False,
        )

    except Exception as e:
        print(f"Shape update error: {e}")


@socketio.on("request_presence")
def handle_request_presence(data: Dict[str, Any]) -> None:
    """
    Handle request for current room presence.

    Args:
        data: Contains 'room_id'
    """
    try:
        room_id = data.get("room_id")
        if not room_id:
            return

        # Get all room users
        room_users = manager.get_room_users(room_id)

        # Send presence update to requester
        emit("presence_update", {"users": room_users})

    except Exception as e:
        print(f"Request presence error: {e}")
