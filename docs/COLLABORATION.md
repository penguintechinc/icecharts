# Real-Time Collaboration System

IceCharts includes a comprehensive WebSocket-based collaboration system that enables multiple users to work on diagrams simultaneously with real-time updates, cursor tracking, and shape locking.

## Quick Start

### 5-Minute Setup

**1. Start Redis (Required)**

```bash
# Using Docker
docker run -d --name icecharts-redis -p 6379:6379 redis:7-alpine

# Or using your system's Redis
redis-server
```

**2. Backend Setup**

```bash
cd services/flask-backend
pip install -r requirements.txt
python run.py
```

**3. Frontend Setup**

```bash
cd services/webui
npm install
npm run dev
```

**4. Add Collaboration to Your Canvas**

```tsx
import { useCollaboration } from './hooks/useCollaboration';
import { CollaboratorCursors, CollaboratorAvatars } from './components/canvas';

function MyCanvas({ drawingId }) {
  const { sendCursorPosition, lockShape, unlockShape } = useCollaboration({
    roomId: drawingId,
    enabled: true,
  });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    sendCursorPosition(e.clientX - rect.left, e.clientY - rect.top);
  };

  return (
    <div onMouseMove={handleMouseMove}>
      {/* Your canvas content */}
      <CollaboratorCursors />
      <CollaboratorAvatars position="top-right" />
    </div>
  );
}
```

That's it! You now have real-time cursor tracking, user presence indicators, and collaborative editing with shape locking.

---

## Architecture Overview

The collaboration system consists of three main components:

1. **Backend (Flask-SocketIO)**: WebSocket server handling connections, rooms, and event broadcasting
2. **Frontend (Socket.IO Client)**: React hooks and components for collaboration features
3. **State Management (Zustand)**: Centralized state store for collaboration data

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  useCollaboration Hook                                    │  │
│  │  - WebSocket connection management                        │  │
│  │  - Event handlers                                         │  │
│  │  - Reconnection logic                                     │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │  Collaboration Store (Zustand)                           │  │
│  │  - Collaborators state                                   │  │
│  │  - Cursor positions                                      │  │
│  │  - Shape locks                                           │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │  UI Components                                           │  │
│  │  - CollaboratorCursors                                   │  │
│  │  - CollaboratorAvatars                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    Socket.IO (WebSocket)
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    Flask Backend Server                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Flask-SocketIO                                          │  │
│  │  - Connection handling                                   │  │
│  │  - JWT authentication                                    │  │
│  │  - Event routing                                         │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │  WebSocket Handlers                                      │  │
│  │  - join_room / leave_room                                │  │
│  │  - cursor_move                                           │  │
│  │  - shape_lock / shape_unlock                             │  │
│  │  - shape_update                                          │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │  Collaboration Manager                                   │  │
│  │  - Session tracking                                      │  │
│  │  - Color assignment                                      │  │
│  │  - Lock management                                       │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                          │
│  ┌───────────────────▼──────────────────────────────────────┐  │
│  │  Redis (State Storage)                                   │  │
│  │  - Active sessions                                       │  │
│  │  - Shape locks                                           │  │
│  │  - Presence data                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Components

### 1. WebSocket Initialization (`/app/websocket/__init__.py`)

Initializes Flask-SocketIO with the Flask app:

```python
from app.websocket import init_socketio

socketio = init_socketio(app)
```

**Configuration:**
- CORS support for cross-origin connections
- Threading async mode
- Automatic reconnection handling
- Session management

### 2. Collaboration Manager (`/app/websocket/collaboration.py`)

Manages collaboration state using Redis:

**Features:**
- User presence tracking with color assignment
- Shape lock management with timeouts (5 minutes)
- Session cleanup and expiration
- Fallback to in-memory storage if Redis unavailable

**Key Methods:**
- `join_room(room_id, user_id, username, email, session_id)` - Add user to room
- `leave_room(room_id, session_id)` - Remove user from room
- `update_cursor(room_id, session_id, x, y)` - Update cursor position
- `lock_shape(room_id, shape_id, user_id, session_id)` - Acquire shape lock
- `unlock_shape(room_id, shape_id, session_id)` - Release shape lock
- `get_room_users(room_id)` - Get all active collaborators

### 3. WebSocket Event Handlers (`/app/websocket/handlers.py`)

Handles all WebSocket events:

**Connection Events:**
- `connect` - Authenticate user with JWT token
- `disconnect` - Clean up user presence and locks

**Room Events:**
- `join_room` - Join a drawing room
- `leave_room` - Leave a drawing room
- `request_presence` - Get current room users

**Cursor Events:**
- `cursor_move` - Broadcast cursor position to room

**Lock Events:**
- `shape_lock` - Request to lock a shape
- `shape_unlock` - Release shape lock

**Shape Events:**
- `shape_update` - Broadcast shape changes to room

## Frontend Components

### 1. Collaboration Store (`/src/client/store/collaborationStore.ts`)

Zustand store managing collaboration state:

```typescript
interface CollaborationState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  sessionId: string | null;
  currentRoom: string | null;
  myColor: string | null;
  collaborators: Map<string, Collaborator>;
  shapeLocks: Map<string, ShapeLock>;
  cursors: Map<string, CursorPosition>;
}
```

**Usage:**
```typescript
import { useCollaborationStore } from './store/collaborationStore';

const collaborators = useCollaborationStore(state => state.collaborators);
const isShapeLocked = useCollaborationStore(state => state.isShapeLocked);
```

### 2. useCollaboration Hook (`/src/client/hooks/useCollaboration.ts`)

React hook providing collaboration functionality:

**Features:**
- Automatic connection management
- JWT authentication
- Reconnection with exponential backoff
- Event handling and broadcasting
- Optimistic updates

**Usage:**
```typescript
import { useCollaboration } from './hooks/useCollaboration';

const MyComponent = () => {
  const {
    connect,
    disconnect,
    joinRoom,
    leaveRoom,
    sendCursorPosition,
    lockShape,
    unlockShape,
    sendShapeUpdate,
  } = useCollaboration({
    roomId: 'drawing-123',
    enabled: true,
    onConnected: () => console.log('Connected'),
    onDisconnected: () => console.log('Disconnected'),
    onError: (error) => console.error(error),
  });
};
```

### 3. CollaboratorCursors Component

Renders real-time cursors for other users:

**Features:**
- Smooth position interpolation (ease-out animation)
- Color-coded cursors matching user colors
- Username labels
- Automatic cleanup when users disconnect

**Usage:**
```tsx
import { CollaboratorCursors } from './components/canvas/CollaboratorCursors';

<div className="canvas-container">
  {/* Your canvas content */}
  <CollaboratorCursors />
</div>
```

### 4. CollaboratorAvatars Component

Displays active collaborators with avatars:

**Features:**
- Avatar stack showing initials
- Hover tooltips with user info
- Overflow indicator (+N)
- Connection status indicator
- Your color indicator

**Usage:**
```tsx
import { CollaboratorAvatars } from './components/canvas/CollaboratorAvatars';

<CollaboratorAvatars position="top-right" maxVisible={5} />
```

## Common Use Cases

### Shape Locking

```tsx
function EditableCanvas() {
  const { lockShape, unlockShape, sendShapeUpdate } = useCollaboration({
    roomId: 'my-drawing',
  });
  const isShapeLocked = useCollaborationStore(state => state.isShapeLocked);

  const handleShapeClick = async (shapeId) => {
    if (isShapeLocked(shapeId)) {
      alert('Shape is being edited by another user');
      return;
    }

    try {
      await lockShape(shapeId);
      const updatedShape = editShape(shapeId);
      sendShapeUpdate(shapeId, updatedShape);
      unlockShape(shapeId);
    } catch (error) {
      console.error('Failed to lock shape:', error);
    }
  };

  return <canvas onClick={handleShapeClick} />;
}
```

### Connection Status

```tsx
import { useCollaborationStore } from './store/collaborationStore';

function ConnectionStatus() {
  const connected = useCollaborationStore(state => state.connected);
  const connecting = useCollaborationStore(state => state.connecting);
  const error = useCollaborationStore(state => state.error);

  if (error) return <div>Error: {error}</div>;
  if (connecting) return <div>Connecting...</div>;
  if (connected) return <div>Connected</div>;
  return <div>Disconnected</div>;
}
```

## Configuration

### Backend Environment Variables

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend Environment Variables

```bash
# API URL (WebSocket will connect to same host)
VITE_API_URL=http://localhost:5000
```

## API Reference

### WebSocket Events

#### Client → Server

| Event | Payload | Description |
|-------|---------|-------------|
| `join_room` | `{ room_id: string }` | Join a drawing room |
| `leave_room` | `{ room_id: string }` | Leave a drawing room |
| `cursor_move` | `{ room_id, x, y }` | Update cursor position |
| `shape_lock` | `{ room_id, shape_id }` | Request shape lock |
| `shape_unlock` | `{ room_id, shape_id }` | Release shape lock |
| `shape_update` | `{ room_id, shape_id, shape_data }` | Broadcast shape changes |
| `request_presence` | `{ room_id }` | Get current room users |

#### Server → Client

| Event | Payload | Description |
|-------|---------|-------------|
| `connected` | `{ session_id }` | Connection confirmed |
| `room_joined` | `{ room_id, user_id, color }` | Successfully joined room |
| `presence_update` | `{ users: [...] }` | List of active collaborators |
| `cursor_moved` | `{ user_id, session_id, x, y }` | Cursor position update |
| `shape_locked` | `{ room_id, shape_id, user_id }` | Shape lock acquired |
| `shape_unlocked` | `{ room_id, shape_id }` | Shape lock released |
| `shape_lock_failed` | `{ room_id, shape_id, locked_by }` | Lock request denied |
| `shape_updated` | `{ room_id, shape_id, shape_data, user_id }` | Remote shape change |
| `error` | `{ message }` | Error notification |

## Security Considerations

### Authentication
- JWT tokens required for all WebSocket connections
- Tokens validated on connection
- Invalid tokens rejected immediately

### Authorization
- Users can only join rooms they have access to
- Shape locks tied to session IDs
- Users can only unlock shapes they locked

### Rate Limiting
- Cursor updates throttled to 20/second (50ms interval)
- Lock timeout: 5 minutes
- Session timeout: 1 hour

## Performance Optimization

### Cursor Tracking
- Client-side throttling (50ms)
- Smooth interpolation to reduce jitter
- Only broadcast to room members

### Lock Management
- Redis-based locking with NX (set if not exists)
- Automatic lock expiration
- Lock cleanup on disconnect

### Network Optimization
- Binary protocol with Socket.IO
- Message batching where possible
- Reconnection with exponential backoff

## Debugging

### Enable Debug Logging

**Backend:**
```python
socketio = SocketIO(app, logger=True, engineio_logger=True)
```

**Frontend:**
```typescript
localStorage.debug = '*';
```

### Monitor Redis

```bash
redis-cli
MONITOR
KEYS collab:*
HGETALL collab:room:drawing-123
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cannot connect to WebSocket | Check CORS config, verify JWT token, ensure Redis is running |
| Frequent disconnections | Increase ping timeout, check network stability |
| Cursors are jumpy | Verify throttling (50ms), check interpolation logic |
| Cursors not appearing | Verify presence updates, check cursor position calculations |
| Cannot lock shapes | Check lock timeout (5 min), verify Redis connectivity |
| Locks not released | Verify unlock is called, check session cleanup on disconnect |

## License

Part of IceCharts - See main LICENSE file for details.
