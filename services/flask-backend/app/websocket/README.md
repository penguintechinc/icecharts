# WebSocket Package

Real-time collaboration support for IceCharts using Flask-SocketIO.

## Overview

This package provides WebSocket functionality for real-time collaboration features including:
- User presence tracking
- Cursor position synchronization
- Shape locking mechanism
- Real-time updates broadcasting
- Session management with Redis

## Architecture

```
websocket/
├── __init__.py          # Flask-SocketIO initialization
├── collaboration.py     # Collaboration session manager
├── handlers.py          # WebSocket event handlers
└── README.md           # This file
```

## Components

### `__init__.py` - WebSocket Initialization

Initializes Flask-SocketIO with the Flask application.

**Usage**:
```python
from app import create_app
from app.websocket import init_socketio

app = create_app()
socketio = init_socketio(app)

# Run with SocketIO
socketio.run(app, host='0.0.0.0', port=5000)
```

**Configuration**:
- `CORS_ORIGINS`: Allowed origins for WebSocket connections
- `async_mode`: 'threading' (default)
- `ping_timeout`: 60 seconds
- `ping_interval`: 25 seconds

### `collaboration.py` - Collaboration Manager

Manages collaboration state using Redis (with in-memory fallback).

**Key Classes**:

**`Collaborator`** (dataclass):
```python
@dataclass(slots=True, frozen=True)
class Collaborator:
    user_id: str
    username: str
    email: str
    color: str
    session_id: str
    cursor_x: float = 0.0
    cursor_y: float = 0.0
    last_seen: float = 0.0
```

**`CollaborationManager`**:
```python
manager = CollaborationManager()

# Join a room
collaborator = manager.join_room(
    room_id="drawing-123",
    user_id="user-456",
    username="John Doe",
    email="john@example.com",
    session_id="socket-session-id"
)

# Update cursor
manager.update_cursor(room_id, session_id, x=100.0, y=200.0)

# Lock a shape
success = manager.lock_shape(room_id, shape_id, user_id, session_id)

# Unlock a shape
success = manager.unlock_shape(room_id, shape_id, session_id)

# Get room users
users = manager.get_room_users(room_id)

# Leave room
manager.leave_room(room_id, session_id)
```

**Configuration**:
```bash
# Environment variables
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

**Features**:
- 10 unique colors for collaborators
- 5-minute lock timeout
- 1-hour session timeout
- Automatic cleanup on disconnect
- Fallback to in-memory storage

### `handlers.py` - Event Handlers

WebSocket event handlers for all collaboration events.

**Connection Events**:
```python
@socketio.on('connect')
def handle_connect(auth):
    # Validates JWT token
    # Returns True/False for accept/reject
```

**Room Events**:
```python
@socketio.on('join_room')
def handle_join_room(data):
    # data = {'room_id': 'drawing-123'}
    # Emits: 'room_joined', 'presence_update'

@socketio.on('leave_room')
def handle_leave_room(data):
    # data = {'room_id': 'drawing-123'}
    # Emits: 'presence_update'
```

**Cursor Events**:
```python
@socketio.on('cursor_move')
def handle_cursor_move(data):
    # data = {'room_id': 'drawing-123', 'x': 100, 'y': 200}
    # Emits: 'cursor_moved' (broadcast)
```

**Lock Events**:
```python
@socketio.on('shape_lock')
def handle_shape_lock(data):
    # data = {'room_id': 'drawing-123', 'shape_id': 'shape-456'}
    # Emits: 'shape_locked' or 'shape_lock_failed'

@socketio.on('shape_unlock')
def handle_shape_unlock(data):
    # data = {'room_id': 'drawing-123', 'shape_id': 'shape-456'}
    # Emits: 'shape_unlocked'
```

**Shape Update Events**:
```python
@socketio.on('shape_update')
def handle_shape_update(data):
    # data = {
    #     'room_id': 'drawing-123',
    #     'shape_id': 'shape-456',
    #     'shape_data': {...}
    # }
    # Emits: 'shape_updated' (broadcast)
```

## Authentication

All WebSocket connections require JWT authentication:

```python
# Connect with auth token
socket = io('http://localhost:5000', {
    auth: {
        token: 'your-jwt-token-here'
    }
})
```

Token must include:
- `user_id`: User identifier
- `username`: Display name
- `email`: User email

## Data Flow

```
Client                    Handler                 Manager              Redis
  │                          │                       │                    │
  ├─ connect(jwt) ─────────>│                       │                    │
  │                          ├─ verify_token()       │                    │
  │<─ connected ─────────────┤                       │                    │
  │                          │                       │                    │
  ├─ join_room ─────────────>│                       │                    │
  │                          ├─ join_room() ───────>│                    │
  │                          │                       ├─ HSET ──────────>│
  │                          │                       │<─ OK ─────────────┤
  │<─ room_joined ───────────┤                       │                    │
  │<─ presence_update ───────┤<─ get_room_users() ──┤                    │
  │                          │                       │                    │
  ├─ cursor_move ───────────>│                       │                    │
  │                          ├─ update_cursor() ────>│                    │
  │                          │                       ├─ HSET ──────────>│
  │                          ├─ broadcast ─────────>│                    │
  │<─ cursor_moved ──────────┤ (to room)            │                    │
```

## Error Handling

All handlers include comprehensive error handling:

```python
try:
    # Handler logic
except Exception as e:
    print(f"Error: {e}")
    emit('error', {'message': str(e)})
```

Common errors:
- `"Authentication required"` - No JWT token provided
- `"room_id is required"` - Missing room_id parameter
- `"You don't have lock on this shape"` - Lock ownership violation

## Performance

**Optimization Features**:
- Efficient Redis hash storage for room data
- Room-based broadcasting (only to room members)
- Automatic cleanup of stale sessions
- Connection pooling for Redis
- Lazy data loading

**Limits**:
- Lock timeout: 5 minutes
- Session timeout: 1 hour
- Ping timeout: 60 seconds
- Ping interval: 25 seconds

## Testing

Run tests:
```bash
pytest tests/test_websocket.py -v
```

Manual testing with Python:
```python
from socketio import SimpleClient

client = SimpleClient()
client.connect('http://localhost:5000', auth={'token': 'jwt-token'})

# Join room
client.emit('join_room', {'room_id': 'test-room'})

# Wait for response
event = client.receive()
print(event)

client.disconnect()
```

## Debugging

Enable debug logging:
```python
socketio = SocketIO(
    app,
    logger=True,
    engineio_logger=True,
)
```

Monitor Redis:
```bash
redis-cli
> MONITOR
> KEYS collab:*
> HGETALL collab:room:drawing-123
```

## Integration

See the complete documentation:
- [/docs/COLLABORATION.md](../../../../docs/COLLABORATION.md) - Full documentation
- [/docs/COLLABORATION_QUICKSTART.md](../../../../docs/COLLABORATION_QUICKSTART.md) - Quick start guide

Example integration:
```python
from flask import Flask
from app.websocket import init_socketio

app = Flask(__name__)
socketio = init_socketio(app)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

## License

Part of IceCharts - See main LICENSE file for details.
