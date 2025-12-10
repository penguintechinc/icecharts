"""Collaboration session management with Redis."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
import json
import time
import os
import redis
from redis.exceptions import RedisError


@dataclass(slots=True, frozen=True)
class Collaborator:
    """Represents a collaborator in a drawing session."""

    user_id: str
    username: str
    email: str
    color: str
    session_id: str
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    last_seen: float = 0.0


class CollaborationManager:
    """
    Manages collaboration sessions using Redis for state storage.

    Handles:
    - User presence tracking
    - Color assignment
    - Shape lock management
    - Session cleanup
    """

    # Color palette for collaborators
    COLORS = [
        "#FF6B6B",  # Red
        "#4ECDC4",  # Teal
        "#45B7D1",  # Blue
        "#FFA07A",  # Light Salmon
        "#98D8C8",  # Mint
        "#F7DC6F",  # Yellow
        "#BB8FCE",  # Purple
        "#85C1E2",  # Sky Blue
        "#F8B739",  # Orange
        "#52C41A",  # Green
    ]

    LOCK_TIMEOUT = 300  # 5 minutes in seconds
    SESSION_TIMEOUT = 3600  # 1 hour in seconds

    def __init__(self):
        """Initialize the collaboration manager with Redis connection."""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_db = int(os.getenv("REDIS_DB", "0"))

        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
        except RedisError as e:
            # Fallback to in-memory storage if Redis is unavailable
            print(f"Redis unavailable, using in-memory storage: {e}")
            self.redis_client = None
            self._memory_storage: Dict[str, Dict] = {}
            self._memory_locks: Dict[str, Dict] = {}

    def _get_room_key(self, room_id: str) -> str:
        """Get Redis key for a room."""
        return f"collab:room:{room_id}"

    def _get_lock_key(self, room_id: str, shape_id: str) -> str:
        """Get Redis key for a shape lock."""
        return f"collab:lock:{room_id}:{shape_id}"

    def join_room(
        self,
        room_id: str,
        user_id: str,
        username: str,
        email: str,
        session_id: str,
    ) -> Collaborator:
        """
        Add a user to a collaboration room.

        Args:
            room_id: Drawing room identifier
            user_id: User identifier
            username: User display name
            email: User email
            session_id: WebSocket session ID

        Returns:
            Collaborator object with assigned color
        """
        room_key = self._get_room_key(room_id)
        color = self._assign_color(room_id)

        collaborator = Collaborator(
            user_id=user_id,
            username=username,
            email=email,
            color=color,
            session_id=session_id,
            cursor_x=0.0,
            cursor_y=0.0,
            last_seen=time.time(),
        )

        collaborator_data = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "color": color,
            "session_id": session_id,
            "cursor_x": 0.0,
            "cursor_y": 0.0,
            "last_seen": time.time(),
        }

        if self.redis_client:
            try:
                self.redis_client.hset(
                    room_key, session_id, json.dumps(collaborator_data)
                )
                self.redis_client.expire(room_key, self.SESSION_TIMEOUT)
            except RedisError:
                pass
        else:
            if room_id not in self._memory_storage:
                self._memory_storage[room_id] = {}
            self._memory_storage[room_id][session_id] = collaborator_data

        return collaborator

    def leave_room(self, room_id: str, session_id: str) -> None:
        """
        Remove a user from a collaboration room.

        Args:
            room_id: Drawing room identifier
            session_id: WebSocket session ID
        """
        room_key = self._get_room_key(room_id)

        if self.redis_client:
            try:
                self.redis_client.hdel(room_key, session_id)
            except RedisError:
                pass
        else:
            if room_id in self._memory_storage:
                self._memory_storage[room_id].pop(session_id, None)

        # Clean up any locks held by this user
        self._cleanup_user_locks(room_id, session_id)

    def update_cursor(
        self, room_id: str, session_id: str, x: float, y: float
    ) -> None:
        """
        Update cursor position for a user.

        Args:
            room_id: Drawing room identifier
            session_id: WebSocket session ID
            x: Cursor X coordinate
            y: Cursor Y coordinate
        """
        room_key = self._get_room_key(room_id)

        if self.redis_client:
            try:
                user_data = self.redis_client.hget(room_key, session_id)
                if user_data:
                    data = json.loads(user_data)
                    data["cursor_x"] = x
                    data["cursor_y"] = y
                    data["last_seen"] = time.time()
                    self.redis_client.hset(
                        room_key, session_id, json.dumps(data)
                    )
            except RedisError:
                pass
        else:
            if room_id in self._memory_storage:
                if session_id in self._memory_storage[room_id]:
                    self._memory_storage[room_id][session_id]["cursor_x"] = x
                    self._memory_storage[room_id][session_id]["cursor_y"] = y
                    self._memory_storage[room_id][session_id][
                        "last_seen"
                    ] = time.time()

    def get_room_users(self, room_id: str) -> List[Dict]:
        """
        Get all active users in a room.

        Args:
            room_id: Drawing room identifier

        Returns:
            List of collaborator dictionaries
        """
        room_key = self._get_room_key(room_id)
        current_time = time.time()

        if self.redis_client:
            try:
                users_data = self.redis_client.hgetall(room_key)
                return [
                    json.loads(data)
                    for data in users_data.values()
                    if current_time - json.loads(data).get("last_seen", 0)
                    < 60
                ]
            except RedisError:
                return []
        else:
            if room_id not in self._memory_storage:
                return []
            return [
                data
                for data in self._memory_storage[room_id].values()
                if current_time - data.get("last_seen", 0) < 60
            ]

    def lock_shape(
        self, room_id: str, shape_id: str, user_id: str, session_id: str
    ) -> bool:
        """
        Acquire a lock on a shape for editing.

        Args:
            room_id: Drawing room identifier
            shape_id: Shape identifier
            user_id: User identifier
            session_id: WebSocket session ID

        Returns:
            True if lock acquired, False if already locked by another user
        """
        lock_key = self._get_lock_key(room_id, shape_id)
        lock_data = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": time.time(),
        }

        if self.redis_client:
            try:
                # Try to set lock with NX (only if not exists)
                result = self.redis_client.set(
                    lock_key,
                    json.dumps(lock_data),
                    ex=self.LOCK_TIMEOUT,
                    nx=True,
                )
                return bool(result)
            except RedisError:
                return False
        else:
            lock_full_key = f"{room_id}:{shape_id}"
            if lock_full_key not in self._memory_locks:
                self._memory_locks[lock_full_key] = lock_data
                return True
            else:
                # Check if lock expired
                existing = self._memory_locks[lock_full_key]
                if (
                    time.time() - existing["timestamp"]
                    > self.LOCK_TIMEOUT
                ):
                    self._memory_locks[lock_full_key] = lock_data
                    return True
                return False

    def unlock_shape(
        self, room_id: str, shape_id: str, session_id: str
    ) -> bool:
        """
        Release a lock on a shape.

        Args:
            room_id: Drawing room identifier
            shape_id: Shape identifier
            session_id: WebSocket session ID

        Returns:
            True if lock released, False if not holding lock
        """
        lock_key = self._get_lock_key(room_id, shape_id)

        if self.redis_client:
            try:
                lock_data = self.redis_client.get(lock_key)
                if lock_data:
                    data = json.loads(lock_data)
                    if data["session_id"] == session_id:
                        self.redis_client.delete(lock_key)
                        return True
                return False
            except RedisError:
                return False
        else:
            lock_full_key = f"{room_id}:{shape_id}"
            if lock_full_key in self._memory_locks:
                if (
                    self._memory_locks[lock_full_key]["session_id"]
                    == session_id
                ):
                    del self._memory_locks[lock_full_key]
                    return True
            return False

    def get_shape_lock(self, room_id: str, shape_id: str) -> Optional[Dict]:
        """
        Get current lock holder for a shape.

        Args:
            room_id: Drawing room identifier
            shape_id: Shape identifier

        Returns:
            Lock data dict or None if not locked
        """
        lock_key = self._get_lock_key(room_id, shape_id)

        if self.redis_client:
            try:
                lock_data = self.redis_client.get(lock_key)
                return json.loads(lock_data) if lock_data else None
            except RedisError:
                return None
        else:
            lock_full_key = f"{room_id}:{shape_id}"
            return self._memory_locks.get(lock_full_key)

    def _assign_color(self, room_id: str) -> str:
        """Assign a unique color to a user in a room."""
        users = self.get_room_users(room_id)
        used_colors = {user.get("color") for user in users}

        for color in self.COLORS:
            if color not in used_colors:
                return color

        # If all colors used, return a random one
        import random

        return random.choice(self.COLORS)

    def _cleanup_user_locks(self, room_id: str, session_id: str) -> None:
        """Clean up all locks held by a user."""
        if self.redis_client:
            try:
                pattern = f"collab:lock:{room_id}:*"
                for key in self.redis_client.scan_iter(pattern):
                    lock_data = self.redis_client.get(key)
                    if lock_data:
                        data = json.loads(lock_data)
                        if data.get("session_id") == session_id:
                            self.redis_client.delete(key)
            except RedisError:
                pass
        else:
            keys_to_remove = []
            for key, lock_data in self._memory_locks.items():
                if (
                    key.startswith(f"{room_id}:")
                    and lock_data.get("session_id") == session_id
                ):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._memory_locks[key]


# Global collaboration manager instance
_manager: Optional[CollaborationManager] = None


def get_collaboration_manager() -> CollaborationManager:
    """Get the global collaboration manager instance."""
    global _manager
    if _manager is None:
        _manager = CollaborationManager()
    return _manager
