# Real-Time Collaboration Feature

## Overview

The IceCharts real-time collaboration feature enables multiple users to work on the same drawing simultaneously with live cursor tracking, permission-based editing, and attention gestures.

## Components

### 1. CollaborationService (`app/services/collaboration_service.py`)

Service layer for managing collaboration sessions with permission enforcement.

#### Key Methods:

- **`join_drawing_session(drawing_id, user_id, session_id, socket_id)`**
  - Checks view permissions via PermissionService
  - Creates or updates collaboration session
  - Returns session info, user data, and active collaborators
  - Raises `PermissionError` if user lacks permission

- **`leave_drawing_session(drawing_id, user_id, session_id)`**
  - Marks session as inactive
  - Sets `left_at` timestamp
  - Returns True if successful

- **`update_cursor_position(drawing_id, user_id, session_id, cursor_x, cursor_y)`**
  - Updates cursor position in database
  - Stores in both `cursor_position_json` and separate x/y fields
  - Returns True if successful

- **`trigger_attention_click(drawing_id, user_id, click_x, click_y)`**
  - Creates attention click event for broadcasting
  - Returns event data with user info and click position

- **`can_edit_drawing_realtime(user_id, drawing_id)`**
  - Permission check wrapper around PermissionService
  - Returns True if user has edit permission

- **`get_active_collaborators(drawing_id)`**
  - Returns list of active collaborators (active in last 5 minutes)
  - Includes user info, permission level, and cursor position

- **`cleanup_inactive_sessions(drawing_id=None)`**
  - Cleans up sessions inactive for 10+ minutes
  - Optional drawing_id parameter to limit scope

- **`get_session_by_socket_id(socket_id)`**
  - Retrieves session info by WebSocket ID
  - Used for disconnect cleanup

### 2. WebSocket Handlers (`app/api/v1/collaboration_socket.py`)

Flask-SocketIO event handlers for real-time communication.

#### Events:

##### Client → Server:

1. **`join_drawing`**
   - Payload: `{drawing_id, token}`
   - Verifies JWT token
   - Checks permissions via CollaborationService
   - Joins Socket.IO room `drawing_{drawing_id}`
   - Emits `drawing_joined` to sender
   - Broadcasts `user_joined` to others

2. **`leave_drawing`**
   - Payload: `{drawing_id, token}`
   - Leaves collaboration session
   - Broadcasts `user_left` to room

3. **`cursor_move`**
   - Payload: `{drawing_id, token, x, y}`
   - Updates cursor position in database
   - Broadcasts `cursor_moved` to others (not self)

4. **`attention_click`**
   - Payload: `{drawing_id, token, x, y}`
   - Broadcasts `attention_clicked` to all (including self)

5. **`drawing_change`**
   - Payload: `{drawing_id, token, change_type, change_data}`
   - **Permission check**: Verifies edit permission
   - Broadcasts `drawing_changed` to others
   - Rejects viewers with error message

6. **`disconnect`**
   - Automatic cleanup on WebSocket disconnect
   - Marks session as inactive
   - Broadcasts `user_left`

7. **`request_collaborators`**
   - Payload: `{drawing_id}`
   - Returns `collaborators_list` with active users

##### Server → Client:

1. **`drawing_joined`** - Confirmation with session data
2. **`user_joined`** - Someone joined the drawing
3. **`user_left`** - Someone left the drawing
4. **`cursor_moved`** - Cursor position update
5. **`attention_clicked`** - Attention gesture event
6. **`drawing_changed`** - Drawing modification
7. **`collaborators_list`** - List of active collaborators
8. **`error`** - Error message

## Permission-Based Editing

The collaboration system enforces RBAC permissions:

- **Viewers**: Can see live cursors and changes, **cannot** edit
- **Editors**: Can see and make changes
- **Admins**: Full access (can see and make changes)

### Enforcement Points:

1. **Join Session**: Requires at least view permission
2. **Drawing Changes**: Requires edit permission
   - `drawing_change` event verifies permission before broadcasting
   - Returns error if user is viewer

### Permission Checks:

```python
# Via PermissionService
can_view = PermissionService.can_view_drawing(user_id, drawing_id)
can_edit = PermissionService.can_edit_drawing(user_id, drawing_id)
permission_level = PermissionService.get_drawing_permission_level(user_id, drawing_id)
```

## Database Schema

### `collaboration_sessions` Table:

```sql
CREATE TABLE collaboration_sessions (
    id INTEGER PRIMARY KEY,
    drawing_id INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
    identity_id INTEGER NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    socket_id VARCHAR(255),
    cursor_position_json JSON,
    last_cursor_x DOUBLE,
    last_cursor_y DOUBLE,
    permission VARCHAR(50) DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    joined_at DATETIME,
    left_at DATETIME
);
```

## Usage Example

### Client-Side (JavaScript):

```javascript
import io from 'socket.io-client';

// Connect to WebSocket
const socket = io('http://localhost:5000', {
  auth: { token: jwtToken }
});

// Join drawing
socket.emit('join_drawing', {
  drawing_id: 123,
  token: jwtToken
});

// Listen for events
socket.on('drawing_joined', (data) => {
  console.log('Joined drawing:', data);
  console.log('Can edit:', data.can_edit);
  console.log('Collaborators:', data.collaborators);
});

socket.on('user_joined', (data) => {
  console.log('User joined:', data.user);
});

socket.on('cursor_moved', (data) => {
  console.log('Cursor moved:', data.user_id, data.x, data.y);
  // Update cursor visualization
});

socket.on('drawing_changed', (data) => {
  console.log('Drawing changed:', data.change_type);
  // Apply change to local drawing
});

socket.on('error', (data) => {
  console.error('Error:', data.message);
});

// Send cursor updates
socket.emit('cursor_move', {
  drawing_id: 123,
  token: jwtToken,
  x: 100,
  y: 200
});

// Send drawing changes (requires edit permission)
socket.emit('drawing_change', {
  drawing_id: 123,
  token: jwtToken,
  change_type: 'add',
  change_data: { /* shape data */ }
});

// Leave drawing
socket.emit('leave_drawing', {
  drawing_id: 123,
  token: jwtToken
});
```

## Testing

### Manual Testing:

1. **Single User Join**:
   ```bash
   # Use a WebSocket client to connect
   wscat -c ws://localhost:5000/socket.io/?transport=websocket

   # Send join event
   42["join_drawing",{"drawing_id":1,"token":"YOUR_JWT_TOKEN"}]
   ```

2. **Multiple Concurrent Connections**:
   - Open multiple browser tabs
   - Each tab connects with different user token
   - Verify all users see each other's cursors
   - Verify only editors can make changes

3. **Permission Testing**:
   - Connect as viewer: should receive error on `drawing_change`
   - Connect as editor: should successfully broadcast changes
   - Verify permission level in `drawing_joined` response

### Automated Testing:

```python
# tests/test_collaboration.py
def test_join_drawing_session():
    # Test joining with valid permission
    # Test joining without permission (should raise PermissionError)
    # Test duplicate session handling

def test_cursor_updates():
    # Test cursor position updates
    # Verify broadcast to other users

def test_permission_enforcement():
    # Test viewer cannot edit
    # Test editor can edit
    # Test admin can edit
```

## Architecture Notes

### Session Management:

- Sessions are stored in database (`collaboration_sessions` table)
- Active sessions tracked via `is_active` flag
- Sessions expire after 5 minutes of inactivity (for collaborator list)
- Cleanup task marks sessions inactive after 10 minutes

### Room Naming:

- Socket.IO rooms use format: `drawing_{drawing_id}`
- Each drawing has its own room for isolated broadcasting

### Authentication:

- JWT tokens verified on each event
- Token contains `user_id` for permission checks
- Invalid tokens result in error emissions

### Error Handling:

- Permission errors emit `error` event to client
- All exceptions caught and logged
- Clients receive user-friendly error messages

## Future Enhancements

1. **Shape Locking**: Lock shapes during editing (already in `websocket/handlers.py`)
2. **Presence Indicators**: Show who is actively editing vs. just viewing
3. **Chat**: Add real-time chat between collaborators
4. **Conflict Resolution**: Operational transformation for simultaneous edits
5. **Session Metrics**: Track collaboration analytics (time spent, changes made)
6. **Notifications**: Desktop notifications for important events

## Security Considerations

1. **Authentication**: All events require valid JWT token
2. **Authorization**: RBAC permissions enforced via PermissionService
3. **Input Validation**: Drawing IDs and coordinates validated
4. **Rate Limiting**: Consider adding rate limits on cursor updates
5. **Token Refresh**: Clients should refresh tokens before expiry
6. **XSS Protection**: Sanitize user-provided data before broadcasting
