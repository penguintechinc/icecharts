# Collaboration System - Quick Start Guide

This guide will help you quickly integrate real-time collaboration into IceCharts.

## 5-Minute Setup

### 1. Start Redis (Required)

```bash
# Using Docker
docker run -d --name icecharts-redis -p 6379:6379 redis:7-alpine

# Or using your system's Redis
redis-server
```

### 2. Backend Setup

The WebSocket server is already integrated into the Flask backend. Just ensure you have the dependencies installed:

```bash
cd services/flask-backend
pip install -r requirements.txt
```

Start the Flask server:

```bash
python run.py
# Or with Flask-SocketIO:
python -c "from app import create_app; app = create_app(); app.socketio.run(app, host='0.0.0.0', port=5000)"
```

### 3. Frontend Setup

Dependencies are already in `package.json`. Just install:

```bash
cd services/webui
npm install
npm run dev
```

### 4. Add Collaboration to Your Canvas

**Step 1:** Import the components and hook:

```tsx
import { useCollaboration } from './hooks/useCollaboration';
import { CollaboratorCursors, CollaboratorAvatars } from './components/canvas';
```

**Step 2:** Use the hook in your component:

```tsx
function MyCanvas({ drawingId }) {
  const { sendCursorPosition, lockShape, unlockShape } = useCollaboration({
    roomId: drawingId,
    enabled: true,
  });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    sendCursorPosition(x, y);
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

**Step 3:** That's it! You now have:
- Real-time cursor tracking
- User presence indicators
- Collaborative editing with shape locking

## Common Use Cases

### Use Case 1: Basic Cursor Tracking

```tsx
import { useCollaboration } from './hooks/useCollaboration';
import { CollaboratorCursors } from './components/canvas';

function SimpleCanvas() {
  const { sendCursorPosition } = useCollaboration({
    roomId: 'my-drawing',
    enabled: true,
  });

  return (
    <div onMouseMove={(e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      sendCursorPosition(
        e.clientX - rect.left,
        e.clientY - rect.top
      );
    }}>
      <canvas />
      <CollaboratorCursors />
    </div>
  );
}
```

### Use Case 2: Shape Locking

```tsx
function EditableCanvas() {
  const { lockShape, unlockShape, sendShapeUpdate } = useCollaboration({
    roomId: 'my-drawing',
  });

  const isShapeLocked = useCollaborationStore(state => state.isShapeLocked);

  const handleShapeClick = async (shapeId) => {
    // Check if shape is locked by someone else
    if (isShapeLocked(shapeId)) {
      alert('Shape is being edited by another user');
      return;
    }

    try {
      // Lock the shape
      await lockShape(shapeId);

      // Edit the shape
      const updatedShape = editShape(shapeId);

      // Broadcast changes
      sendShapeUpdate(shapeId, updatedShape);

      // Release lock when done
      unlockShape(shapeId);
    } catch (error) {
      console.error('Failed to lock shape:', error);
    }
  };

  return <canvas onClick={handleShapeClick} />;
}
```

### Use Case 3: Listen for Remote Updates

```tsx
function SyncedCanvas() {
  useEffect(() => {
    const handleRemoteUpdate = (event) => {
      const { shape_id, shape_data } = event.detail;

      // Apply remote changes to your local canvas
      updateLocalShape(shape_id, shape_data);
    };

    window.addEventListener(
      'collaboration:shape_updated',
      handleRemoteUpdate
    );

    return () => {
      window.removeEventListener(
        'collaboration:shape_updated',
        handleRemoteUpdate
      );
    };
  }, []);

  return <canvas />;
}
```

### Use Case 4: Show Collaborator List

```tsx
import { CollaboratorAvatars } from './components/canvas';

function CanvasWithCollaborators() {
  return (
    <div className="relative">
      <canvas />

      {/* Show avatars in different positions */}
      <CollaboratorAvatars position="top-right" maxVisible={5} />
      {/* or */}
      <CollaboratorAvatars position="top-left" maxVisible={3} />
    </div>
  );
}
```

### Use Case 5: Connection Status

```tsx
import { useCollaborationStore } from './store/collaborationStore';

function ConnectionStatus() {
  const connected = useCollaborationStore(state => state.connected);
  const connecting = useCollaborationStore(state => state.connecting);
  const error = useCollaborationStore(state => state.error);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (connecting) {
    return <div>Connecting...</div>;
  }

  if (connected) {
    return <div>Connected</div>;
  }

  return <div>Disconnected</div>;
}
```

## Environment Variables

### Backend (.env)

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

### Frontend (.env)

```bash
# API URL (WebSocket will connect to same host)
VITE_API_URL=http://localhost:5000
```

## Testing

### Test Connection

```bash
# Terminal 1: Start backend
cd services/flask-backend
python run.py

# Terminal 2: Start frontend
cd services/webui
npm run dev

# Terminal 3: Test with curl
curl http://localhost:5000/healthz
```

### Test Collaboration

1. Open two browser windows to your app
2. Navigate to the same drawing
3. Move your mouse in one window
4. See the cursor appear in the other window

## Debugging

### Enable Debug Logging

**Backend:**
```python
# In app/websocket/__init__.py
socketio = SocketIO(
    app,
    logger=True,
    engineio_logger=True,
)
```

**Frontend:**
```typescript
// In browser console
localStorage.debug = '*';
// Then refresh the page
```

### Check WebSocket Connection

```javascript
// In browser console
// The socket instance is exposed in the hook
const socket = window.socket; // If you export it
console.log('Connected:', socket.connected);
console.log('ID:', socket.id);
```

### Monitor Redis

```bash
# Connect to Redis CLI
redis-cli

# Monitor all commands
MONITOR

# List all keys
KEYS collab:*

# Get room data
HGETALL collab:room:drawing-123

# Get lock data
GET collab:lock:drawing-123:shape-456
```

## Performance Tips

1. **Throttle cursor updates** (already implemented at 50ms)
2. **Use Redis for production** (don't rely on in-memory fallback)
3. **Set appropriate lock timeouts** (default 5 minutes)
4. **Clean up on disconnect** (already handled automatically)
5. **Batch shape updates** when possible

## Security Checklist

- [ ] JWT tokens are properly generated and validated
- [ ] CORS is configured for your domains only
- [ ] Redis is secured (password + firewall)
- [ ] WebSocket connections require authentication
- [ ] Lock timeouts are enforced
- [ ] Rate limiting is in place (cursor throttling)

## Next Steps

1. **Customize Colors:** Edit the color palette in `collaboration.py`
2. **Add Features:** Implement chat, annotations, or voice
3. **Scale Up:** Use Redis Cluster and load balancers
4. **Monitor:** Add metrics and logging

## Troubleshooting

**Problem:** "Cannot connect to WebSocket"
- Check if Flask server is running
- Verify CORS_ORIGINS includes your frontend URL
- Check JWT token is valid

**Problem:** "Cursors not showing"
- Verify you're calling `sendCursorPosition()`
- Check if users are in the same room
- Look for errors in browser console

**Problem:** "Shape locks not working"
- Ensure Redis is running
- Check lock timeout settings
- Verify user has correct permissions

## Support

For more details, see the full documentation:
- [COLLABORATION.md](./COLLABORATION.md) - Complete technical documentation
- [API Reference](./COLLABORATION.md#api-reference) - WebSocket event details

## Example Projects

See the example component for a complete implementation:
- [CollaborativeCanvas.example.tsx](../services/webui/src/client/components/canvas/CollaborativeCanvas.example.tsx)
