"""WebSocket handlers for real-time collaboration with permission-based editing."""

import os
from typing import Any, Dict

import jwt
from flask import request
from flask_socketio import emit, join_room, leave_room

from app.services.collaboration_service import CollaborationService


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


def register_handlers(socketio_instance):
    """Register all collaboration WebSocket handlers with SocketIO instance."""

    @socketio_instance.on("join_drawing")
    def handle_join_drawing(data: Dict[str, Any]) -> None:
        """
        Handle user joining a drawing for collaboration.

        Verifies permission, joins room, and emits user_joined event.

        Args:
            data: Contains 'drawing_id' and 'token'
        """
        try:
            drawing_id = data.get("drawing_id")
            token = data.get("token")

            if not drawing_id:
                emit("error", {"message": "drawing_id is required"})
                return

            if not token:
                emit("error", {"message": "authentication token is required"})
                return

            # Verify JWT token
            try:
                user_data = verify_token(token)
                user_id = user_data.get("user_id")
            except jwt.InvalidTokenError as e:
                emit("error", {"message": f"Invalid token: {str(e)}"})
                return

            if not user_id:
                emit("error", {"message": "Invalid token: user_id not found"})
                return

            # Join drawing session (includes permission check)
            try:
                session_info = CollaborationService.join_drawing_session(
                    drawing_id=drawing_id,
                    user_id=user_id,
                    session_id=request.sid,
                    socket_id=request.sid,
                )
            except PermissionError as e:
                emit("error", {"message": str(e)})
                return

            # Join Socket.IO room
            room_name = f"drawing_{drawing_id}"
            join_room(room_name)

            # Notify user of successful join
            emit(
                "drawing_joined",
                {
                    "drawing_id": drawing_id,
                    "session": session_info["session"],
                    "user": session_info["user"],
                    "can_edit": session_info["can_edit"],
                    "collaborators": session_info["collaborators"],
                },
            )

            # Broadcast user_joined to other users in the room
            emit(
                "user_joined",
                {
                    "drawing_id": drawing_id,
                    "user": session_info["user"],
                    "permission": session_info["session"]["permission"],
                    "can_edit": session_info["can_edit"],
                },
                room=room_name,
                include_self=False,
            )

            print(f"User {user_id} joined drawing {drawing_id} (session {request.sid})")

        except Exception as e:
            print(f"Join drawing error: {e}")
            emit("error", {"message": f"Failed to join drawing: {str(e)}"})

    @socketio_instance.on("leave_drawing")
    def handle_leave_drawing(data: Dict[str, Any]) -> None:
        """
        Handle user leaving a drawing.

        Args:
            data: Contains 'drawing_id' and 'token'
        """
        try:
            drawing_id = data.get("drawing_id")
            token = data.get("token")

            if not drawing_id or not token:
                return

            # Verify JWT token
            try:
                user_data = verify_token(token)
                user_id = user_data.get("user_id")
            except jwt.InvalidTokenError:
                return

            if not user_id:
                return

            # Leave drawing session
            CollaborationService.leave_drawing_session(
                drawing_id=drawing_id, user_id=user_id, session_id=request.sid
            )

            # Leave Socket.IO room
            room_name = f"drawing_{drawing_id}"
            leave_room(room_name)

            # Broadcast user_left to other users
            emit(
                "user_left",
                {
                    "drawing_id": drawing_id,
                    "user_id": user_id,
                    "session_id": request.sid,
                },
                room=room_name,
            )

            print(f"User {user_id} left drawing {drawing_id}")

        except Exception as e:
            print(f"Leave drawing error: {e}")

    @socketio_instance.on("cursor_move")
    def handle_cursor_move(data: Dict[str, Any]) -> None:
        """
        Handle cursor position updates and broadcast to other users.

        Args:
            data: Contains 'drawing_id', 'token', 'x', 'y'
        """
        try:
            drawing_id = data.get("drawing_id")
            token = data.get("token")
            cursor_x = data.get("x", 0.0)
            cursor_y = data.get("y", 0.0)

            if not drawing_id or not token:
                return

            # Verify JWT token
            try:
                user_data = verify_token(token)
                user_id = user_data.get("user_id")
            except jwt.InvalidTokenError:
                return

            if not user_id:
                return

            # Update cursor position in database
            CollaborationService.update_cursor_position(
                drawing_id=drawing_id,
                user_id=user_id,
                session_id=request.sid,
                cursor_x=cursor_x,
                cursor_y=cursor_y,
            )

            # Broadcast cursor position to other users
            room_name = f"drawing_{drawing_id}"
            emit(
                "cursor_moved",
                {
                    "drawing_id": drawing_id,
                    "user_id": user_id,
                    "session_id": request.sid,
                    "x": cursor_x,
                    "y": cursor_y,
                },
                room=room_name,
                include_self=False,
            )

        except Exception as e:
            print(f"Cursor move error: {e}")

    @socketio_instance.on("attention_click")
    def handle_attention_click(data: Dict[str, Any]) -> None:
        """
        Handle attention click event (user wants to draw attention to a location).

        Args:
            data: Contains 'drawing_id', 'token', 'x', 'y'
        """
        try:
            drawing_id = data.get("drawing_id")
            token = data.get("token")
            click_x = data.get("x", 0.0)
            click_y = data.get("y", 0.0)

            if not drawing_id or not token:
                return

            # Verify JWT token
            try:
                user_data = verify_token(token)
                user_id = user_data.get("user_id")
            except jwt.InvalidTokenError:
                return

            if not user_id:
                return

            # Trigger attention click event
            click_event = CollaborationService.trigger_attention_click(
                drawing_id=drawing_id, user_id=user_id, click_x=click_x, click_y=click_y
            )

            # Broadcast attention click to all users (including self for confirmation)
            room_name = f"drawing_{drawing_id}"
            emit("attention_clicked", click_event, room=room_name)

            print(f"User {user_id} triggered attention click at ({click_x}, {click_y})")

        except Exception as e:
            print(f"Attention click error: {e}")

    @socketio_instance.on("drawing_change")
    def handle_drawing_change(data: Dict[str, Any]) -> None:
        """
        Handle drawing change events (shape add/update/delete).

        Verifies edit permission before broadcasting changes.

        Args:
            data: Contains 'drawing_id', 'token', 'change_type', 'change_data'
        """
        try:
            drawing_id = data.get("drawing_id")
            token = data.get("token")
            change_type = data.get("change_type")  # 'add', 'update', 'delete'
            change_data = data.get("change_data")  # shape/connector data

            if not drawing_id or not token or not change_type:
                emit(
                    "error",
                    {"message": "drawing_id, token, and change_type are required"},
                )
                return

            # Verify JWT token
            try:
                user_data = verify_token(token)
                user_id = user_data.get("user_id")
            except jwt.InvalidTokenError as e:
                emit("error", {"message": f"Invalid token: {str(e)}"})
                return

            if not user_id:
                emit("error", {"message": "Invalid token: user_id not found"})
                return

            # Verify user has edit permission
            if not CollaborationService.can_edit_drawing_realtime(user_id, drawing_id):
                emit(
                    "error",
                    {
                        "message": "You do not have permission to edit this drawing",
                        "permission_required": "editor",
                    },
                )
                return

            # Broadcast drawing change to other users
            room_name = f"drawing_{drawing_id}"
            emit(
                "drawing_changed",
                {
                    "drawing_id": drawing_id,
                    "user_id": user_id,
                    "change_type": change_type,
                    "change_data": change_data,
                    "timestamp": data.get("timestamp"),
                },
                room=room_name,
                include_self=False,
            )

            print(f"User {user_id} made drawing change: {change_type}")

        except Exception as e:
            print(f"Drawing change error: {e}")
            emit("error", {"message": f"Failed to process drawing change: {str(e)}"})

    @socketio_instance.on("disconnect")
    def handle_disconnect() -> None:
        """
        Handle WebSocket disconnection and cleanup sessions.

        Automatically called when a client disconnects.
        """
        try:
            session_id = request.sid

            # Get session info
            session_info = CollaborationService.get_session_by_socket_id(session_id)

            if session_info:
                drawing_id = session_info.get("drawing_id")
                user_id = session_info.get("user_id")

                # Mark session as inactive
                CollaborationService.leave_drawing_session(
                    drawing_id=drawing_id, user_id=user_id, session_id=session_id
                )

                # Notify other users
                room_name = f"drawing_{drawing_id}"
                emit(
                    "user_left",
                    {
                        "drawing_id": drawing_id,
                        "user_id": user_id,
                        "session_id": session_id,
                    },
                    room=room_name,
                )

                print(f"User {user_id} disconnected from drawing {drawing_id}")
            else:
                print(f"Session {session_id} disconnected (no active drawing session)")

        except Exception as e:
            print(f"Disconnect error: {e}")

    @socketio_instance.on("request_collaborators")
    def handle_request_collaborators(data: Dict[str, Any]) -> None:
        """
        Handle request for current collaborators list.

        Args:
            data: Contains 'drawing_id'
        """
        try:
            drawing_id = data.get("drawing_id")

            if not drawing_id:
                emit("error", {"message": "drawing_id is required"})
                return

            # Get active collaborators
            collaborators = CollaborationService.get_active_collaborators(drawing_id)

            # Send collaborators list to requester
            emit(
                "collaborators_list",
                {"drawing_id": drawing_id, "collaborators": collaborators},
            )

        except Exception as e:
            print(f"Request collaborators error: {e}")
            emit("error", {"message": f"Failed to get collaborators: {str(e)}"})

    @socketio_instance.on("cleanup_inactive_sessions")
    def handle_cleanup_inactive_sessions(data: Dict[str, Any]) -> None:
        """
        Handle request to cleanup inactive sessions (admin only).

        Args:
            data: Contains optional 'drawing_id'
        """
        try:
            drawing_id = data.get("drawing_id")

            # Clean up inactive sessions
            cleaned = CollaborationService.cleanup_inactive_sessions(drawing_id)

            emit("cleanup_complete", {"sessions_cleaned": cleaned})

        except Exception as e:
            print(f"Cleanup error: {e}")
            emit("error", {"message": f"Failed to cleanup sessions: {str(e)}"})
