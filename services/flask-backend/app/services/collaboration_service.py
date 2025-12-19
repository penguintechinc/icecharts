"""Collaboration Service for real-time drawing collaboration with permission checks."""

import datetime
from typing import Dict, List, Optional

from app.models import get_db
from app.services.permission_service import PermissionService


class CollaborationService:
    """
    Service for managing real-time collaboration sessions.

    Handles:
    - Session creation and management
    - Cursor position tracking
    - Permission-based editing enforcement
    - Active collaborator tracking
    """

    @staticmethod
    def join_drawing_session(
        drawing_id: int, user_id: int, session_id: str, socket_id: Optional[str] = None
    ) -> Dict:
        """
        Join a drawing collaboration session.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user joining
            session_id: Unique session identifier
            socket_id: Optional WebSocket connection ID

        Returns:
            Dictionary with session info and active collaborators

        Raises:
            PermissionError: If user lacks view permission
        """
        db = get_db()

        # Check if user has permission to view the drawing
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError(
                f"User {user_id} does not have permission to view drawing {drawing_id}"
            )

        # Get user's permission level
        permission_level = PermissionService.get_drawing_permission_level(
            user_id, drawing_id
        )

        # Check if session already exists
        existing = (
            db(
                (db.collaboration_sessions.drawing_id == drawing_id)
                & (db.collaboration_sessions.identity_id == user_id)
                & (db.collaboration_sessions.session_id == session_id)
            )
            .select()
            .first()
        )

        if existing:
            # Update existing session
            db(db.collaboration_sessions.id == existing.id).update(
                socket_id=socket_id,
                is_active=True,
                permission=permission_level or "viewer",
                joined_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.commit()
            session = db(db.collaboration_sessions.id == existing.id).select().first()
        else:
            # Create new session
            session_record_id = db.collaboration_sessions.insert(
                drawing_id=drawing_id,
                identity_id=user_id,
                session_id=session_id,
                socket_id=socket_id,
                permission=permission_level or "viewer",
                is_active=True,
                last_cursor_x=0.0,
                last_cursor_y=0.0,
                joined_at=datetime.datetime.now(datetime.timezone.utc),
            )
            db.commit()
            session = (
                db(db.collaboration_sessions.id == session_record_id).select().first()
            )

        # Get all active collaborators
        collaborators = CollaborationService.get_active_collaborators(drawing_id)

        # Get user info
        user = db(db.identities.id == user_id).select().first()

        return {
            "session": {
                "id": session.id,
                "drawing_id": drawing_id,
                "user_id": user_id,
                "session_id": session_id,
                "permission": session.permission,
                "joined_at": (
                    session.joined_at.isoformat() if session.joined_at else None
                ),
            },
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
            },
            "collaborators": collaborators,
            "can_edit": PermissionService.can_edit_drawing(user_id, drawing_id),
        }

    @staticmethod
    def leave_drawing_session(drawing_id: int, user_id: int, session_id: str) -> bool:
        """
        Leave a drawing collaboration session.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user leaving
            session_id: Session identifier

        Returns:
            True if session was updated, False otherwise
        """
        db = get_db()

        # Update session to inactive
        updated = db(
            (db.collaboration_sessions.drawing_id == drawing_id)
            & (db.collaboration_sessions.identity_id == user_id)
            & (db.collaboration_sessions.session_id == session_id)
        ).update(is_active=False, left_at=datetime.datetime.now(datetime.timezone.utc))
        db.commit()

        return updated > 0

    @staticmethod
    def update_cursor_position(
        drawing_id: int, user_id: int, session_id: str, cursor_x: float, cursor_y: float
    ) -> bool:
        """
        Update cursor position for a collaboration session.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user
            session_id: Session identifier
            cursor_x: X coordinate of cursor
            cursor_y: Y coordinate of cursor

        Returns:
            True if cursor position was updated, False otherwise
        """
        db = get_db()

        # Update cursor position and last active timestamp
        updated = db(
            (db.collaboration_sessions.drawing_id == drawing_id)
            & (db.collaboration_sessions.identity_id == user_id)
            & (db.collaboration_sessions.session_id == session_id)
            & (db.collaboration_sessions.is_active == True)
        ).update(
            last_cursor_x=cursor_x,
            last_cursor_y=cursor_y,
            cursor_position_json={"x": cursor_x, "y": cursor_y},
        )
        db.commit()

        return updated > 0

    @staticmethod
    def trigger_attention_click(
        drawing_id: int, user_id: int, click_x: float, click_y: float
    ) -> Dict:
        """
        Trigger an attention click event to broadcast to other collaborators.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user clicking
            click_x: X coordinate of click
            click_y: Y coordinate of click

        Returns:
            Dictionary with click event data
        """
        db = get_db()

        # Get user info
        user = db(db.identities.id == user_id).select().first()

        if not user:
            raise ValueError(f"User {user_id} not found")

        return {
            "drawing_id": drawing_id,
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
            },
            "click_position": {"x": click_x, "y": click_y},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    @staticmethod
    def can_edit_drawing_realtime(user_id: int, drawing_id: int) -> bool:
        """
        Check if user can edit a drawing in real-time (permission check).

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            True if user has edit permission, False otherwise
        """
        return PermissionService.can_edit_drawing(user_id, drawing_id)

    @staticmethod
    def get_active_collaborators(drawing_id: int) -> List[Dict]:
        """
        Get all active collaborators for a drawing.

        Args:
            drawing_id: ID of the drawing

        Returns:
            List of active collaborator dictionaries
        """
        db = get_db()

        # Get active sessions (active in last 5 minutes)
        cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=5
        )

        sessions = db(
            (db.collaboration_sessions.drawing_id == drawing_id)
            & (db.collaboration_sessions.is_active == True)
            & (db.collaboration_sessions.joined_at > cutoff_time)
        ).select(
            db.collaboration_sessions.ALL, orderby=db.collaboration_sessions.joined_at
        )

        collaborators = []
        for session in sessions:
            # Get user info
            user = db(db.identities.id == session.identity_id).select().first()

            if user:
                collaborators.append(
                    {
                        "session_id": session.session_id,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "full_name": user.full_name,
                        },
                        "permission": session.permission,
                        "cursor_position": {
                            "x": session.last_cursor_x or 0.0,
                            "y": session.last_cursor_y or 0.0,
                        },
                        "joined_at": (
                            session.joined_at.isoformat() if session.joined_at else None
                        ),
                    }
                )

        return collaborators

    @staticmethod
    def cleanup_inactive_sessions(drawing_id: Optional[int] = None) -> int:
        """
        Clean up inactive collaboration sessions.

        Args:
            drawing_id: Optional drawing ID to limit cleanup to specific drawing

        Returns:
            Number of sessions cleaned up
        """
        db = get_db()

        # Mark sessions as inactive if no activity in last 10 minutes
        cutoff_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=10
        )

        query = (db.collaboration_sessions.is_active == True) & (
            db.collaboration_sessions.joined_at < cutoff_time
        )

        if drawing_id:
            query &= db.collaboration_sessions.drawing_id == drawing_id

        updated = db(query).update(
            is_active=False, left_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.commit()

        return updated

    @staticmethod
    def get_session_by_socket_id(socket_id: str) -> Optional[Dict]:
        """
        Get session information by socket ID.

        Args:
            socket_id: WebSocket connection ID

        Returns:
            Session dictionary or None if not found
        """
        db = get_db()

        session = (
            db(
                (db.collaboration_sessions.socket_id == socket_id)
                & (db.collaboration_sessions.is_active == True)
            )
            .select()
            .first()
        )

        if not session:
            return None

        # Get user info
        user = db(db.identities.id == session.identity_id).select().first()

        return {
            "id": session.id,
            "drawing_id": session.drawing_id,
            "user_id": session.identity_id,
            "session_id": session.session_id,
            "socket_id": session.socket_id,
            "permission": session.permission,
            "user": (
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                }
                if user
                else None
            ),
        }
