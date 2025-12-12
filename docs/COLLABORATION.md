# Real-Time Collaboration System

IceCharts includes a comprehensive WebSocket-based collaboration system that enables multiple users to work on diagrams simultaneously with real-time updates, cursor tracking, and shape locking.

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

**State:**
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

  // Use collaboration methods...
};
```

### 3. CollaboratorCursors Component (`/src/client/components/canvas/CollaboratorCursors.tsx`)

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

### 4. CollaboratorAvatars Component (`/src/client/components/canvas/CollaboratorAvatars.tsx`)

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

<CollaboratorAvatars
  position="top-right"
  maxVisible={5}
/>
```

## Setup and Configuration

### Backend Setup

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure Environment Variables:**
```bash
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional
REDIS_DB=0

# JWT configuration
JWT_SECRET_KEY=your-secret-key

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

3. **Start Flask with SocketIO:**
```python
from app import create_app

app = create_app()
socketio = app.socketio

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
```

### Frontend Setup

1. **Install Dependencies:**
```bash
npm install
```

2. **Configure Environment Variables:**
```bash
# .env
VITE_API_URL=http://localhost:5000
```

3. **Use Collaboration in Your App:**
```tsx
import { CollaborativeCanvas } from './components/canvas/CollaborativeCanvas.example';

function App() {
  return <CollaborativeCanvas drawingId="drawing-123" />;
}
```

## API Reference

### WebSocket Events

#### Client → Server

**connect**
```typescript
// Automatically sent by socket.io-client
// Requires auth.token in connection options
```

**join_room**
```typescript
socket.emit('join_room', {
  room_id: string
});
```

**leave_room**
```typescript
socket.emit('leave_room', {
  room_id: string
});
```

**cursor_move**
```typescript
socket.emit('cursor_move', {
  room_id: string,
  x: number,
  y: number
});
```

**shape_lock**
```typescript
socket.emit('shape_lock', {
  room_id: string,
  shape_id: string
});
```

**shape_unlock**
```typescript
socket.emit('shape_unlock', {
  room_id: string,
  shape_id: string
});
```

**shape_update**
```typescript
socket.emit('shape_update', {
  room_id: string,
  shape_id: string,
  shape_data: any
});
```

**request_presence**
```typescript
socket.emit('request_presence', {
  room_id: string
});
```

#### Server → Client

**connected**
```typescript
socket.on('connected', (data: {
  session_id: string
}) => {});
```

**room_joined**
```typescript
socket.on('room_joined', (data: {
  room_id: string,
  user_id: string,
  color: string
}) => {});
```

**presence_update**
```typescript
socket.on('presence_update', (data: {
  users: Array<{
    user_id: string,
    username: string,
    email: string,
    color: string,
    session_id: string,
    cursor_x: number,
    cursor_y: number,
    last_seen: number
  }>
}) => {});
```

**cursor_moved**
```typescript
socket.on('cursor_moved', (data: {
  user_id: string,
  session_id: string,
  x: number,
  y: number
}) => {});
```

**shape_locked**
```typescript
socket.on('shape_locked', (data: {
  room_id: string,
  shape_id: string,
  user_id: string
}) => {});
```

**shape_unlocked**
```typescript
socket.on('shape_unlocked', (data: {
  room_id: string,
  shape_id: string
}) => {});
```

**shape_lock_failed**
```typescript
socket.on('shape_lock_failed', (data: {
  room_id: string,
  shape_id: string,
  locked_by: string
}) => {});
```

**shape_updated**
```typescript
socket.on('shape_updated', (data: {
  room_id: string,
  shape_id: string,
  shape_data: any,
  user_id: string
}) => {});
```

**error**
```typescript
socket.on('error', (data: {
  message: string
}) => {});
```

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

### Data Validation
- All incoming data validated
- Room IDs and shape IDs checked
- User permissions verified

## Performance Optimization

### Cursor Tracking
- Client-side throttling (50ms)
- Smooth interpolation to reduce jitter
- Only broadcast to room members

### Lock Management
- Redis-based locking with NX (set if not exists)
- Automatic lock expiration
- Lock cleanup on disconnect

### Presence Tracking
- Efficient Redis hash storage
- Automatic cleanup of stale sessions
- Periodic presence updates

### Network Optimization
- Binary protocol with Socket.IO
- Message batching where possible
- Reconnection with exponential backoff

## Troubleshooting

### Connection Issues

**Problem:** WebSocket fails to connect
**Solution:**
- Check CORS configuration
- Verify JWT token is present
- Ensure Redis is running
- Check firewall rules

**Problem:** Frequent disconnections
**Solution:**
- Increase ping timeout
- Check network stability
- Review server logs for errors

### Cursor Issues

**Problem:** Cursors are jumpy
**Solution:**
- Verify throttling is working (50ms)
- Check interpolation logic
- Review network latency

**Problem:** Cursors not appearing
**Solution:**
- Verify presence updates
- Check cursor position calculations
- Review component rendering

### Lock Issues

**Problem:** Cannot lock shapes
**Solution:**
- Check lock timeout (5 minutes)
- Verify user has lock permission
- Check Redis connectivity

**Problem:** Locks not released
**Solution:**
- Verify unlock is called
- Check session cleanup on disconnect
- Review lock expiration settings

## Future Enhancements

Potential improvements for the collaboration system:

1. **Conflict Resolution**
   - Operational transformation (OT) for concurrent edits
   - CRDT-based collaborative editing
   - Automatic merge strategies

2. **Performance**
   - WebRTC for peer-to-peer communication
   - Message compression
   - Selective sync for large diagrams

3. **Features**
   - Voice/video chat integration
   - Collaborative annotations
   - Version history with playback
   - Commenting system

4. **Scalability**
   - Redis Cluster support
   - Load balancing with sticky sessions
   - Horizontal scaling with multiple servers
   - Connection pooling optimization

## License

Part of IceCharts - See main LICENSE file for details.
