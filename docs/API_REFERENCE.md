# IceCharts API Reference

Complete API documentation for IceCharts REST API.

**Base URL**: `http://localhost:5001/api/v1` (or your configured API endpoint)

**Authentication**: All endpoints except `/auth/login` require JWT token in `Authorization: Bearer {token}` header

## Table of Contents

- [Authentication](#authentication)
- [Drawings](#drawings)
- [Comments](#comments)
- [Export](#export)
- [Sharing](#sharing)
- [Users](#users)
- [Groups](#groups)
- [Connectors](#connectors)
- [Elder Integration](#elder-integration)
- [Health & Status](#health--status)

---

## Authentication

### Login

**POST** `/auth/login`

Authenticate user and receive JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "maintainer"
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
- `400 Bad Request`: Missing fields

---

### Refresh Token

**POST** `/auth/refresh`

Refresh access token.

**Headers**: `Authorization: Bearer {refresh_token}`

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

### Logout

**POST** `/auth/logout`

Invalidate current token.

**Headers**: `Authorization: Bearer {token}`

**Response** (200 OK):
```json
{
  "message": "Successfully logged out"
}
```

---

## Drawings

### List Drawings

**GET** `/drawings`

Retrieve all drawings accessible to the user.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of items to skip |
| `limit` | integer | 20 | Maximum items to return |
| `sort_by` | string | updated_at | Field to sort by |
| `order` | string | desc | Sort order (asc/desc) |
| `search` | string | - | Search in name/description |

**Example**:
```bash
GET /drawings?limit=10&sort_by=created_at&order=desc
```

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "name": "System Architecture",
      "description": "Main system design",
      "owner_id": 1,
      "is_public": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T14:22:00Z",
      "thumbnail_url": "https://minio.local/icecharts-thumbnails/1.png",
      "comment_count": 5,
      "collaborators_count": 2
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

---

### Create Drawing

**POST** `/drawings`

Create a new drawing.

**Request Body**:
```json
{
  "name": "New Diagram",
  "description": "Optional description",
  "is_public": false,
  "template": "blank"  // or specific template
}
```

**Response** (201 Created):
```json
{
  "id": 123,
  "name": "New Diagram",
  "description": "Optional description",
  "owner_id": 1,
  "is_public": false,
  "data": {
    "nodes": [],
    "edges": [],
    "viewport": { "x": 0, "y": 0, "zoom": 1 }
  },
  "created_at": "2024-01-16T15:00:00Z",
  "updated_at": "2024-01-16T15:00:00Z"
}
```

---

### Get Drawing

**GET** `/drawings/{id}`

Retrieve a specific drawing.

**Parameters**:
- `id` (integer, required): Drawing ID

**Response** (200 OK):
```json
{
  "id": 123,
  "name": "System Architecture",
  "description": "Main system design",
  "owner_id": 1,
  "is_public": true,
  "data": {
    "nodes": [
      {
        "id": "node-1",
        "type": "rectangle",
        "x": 100,
        "y": 100,
        "width": 150,
        "height": 80,
        "text": "Web Server",
        "style": { "fill": "#3498db", "stroke": "#2980b9" }
      }
    ],
    "edges": [
      {
        "id": "edge-1",
        "source": "node-1",
        "target": "node-2",
        "label": "HTTP",
        "style": { "stroke": "#34495e", "strokeWidth": 2 }
      }
    ],
    "viewport": { "x": 0, "y": 0, "zoom": 1 }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:22:00Z",
  "collaborators": [
    { "id": 1, "email": "user1@example.com", "full_name": "John Doe", "role": "owner" },
    { "id": 2, "email": "user2@example.com", "full_name": "Jane Smith", "role": "editor" }
  ]
}
```

**Error Responses**:
- `404 Not Found`: Drawing doesn't exist
- `403 Forbidden`: No access to drawing

---

### Update Drawing

**PUT** `/drawings/{id}`

Update drawing data or metadata.

**Parameters**:
- `id` (integer, required): Drawing ID

**Request Body**:
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_public": true,
  "data": {
    "nodes": [...],
    "edges": [...],
    "viewport": {...}
  }
}
```

**Response** (200 OK):
```json
{
  "id": 123,
  "name": "Updated Name",
  "description": "Updated description",
  "is_public": true,
  "data": {...},
  "updated_at": "2024-01-16T15:30:00Z"
}
```

---

### Delete Drawing

**DELETE** `/drawings/{id}`

Delete a drawing permanently.

**Parameters**:
- `id` (integer, required): Drawing ID

**Response** (204 No Content)

**Error Responses**:
- `404 Not Found`: Drawing doesn't exist
- `403 Forbidden`: No permission to delete

---

## Comments

### List Comments

**GET** `/drawings/{drawing_id}/comments`

Retrieve all comments for a drawing.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `shape_id` | string | Filter by specific shape |
| `filter` | string | all/open/resolved |
| `thread` | boolean | Return threaded structure |

**Example**:
```bash
GET /drawings/123/comments?thread=true&filter=open
```

**Response** (200 OK):
```json
{
  "drawing_id": 123,
  "comments": [
    {
      "id": 1,
      "content": "This needs revision",
      "author": {
        "id": 1,
        "email": "user@example.com",
        "full_name": "John Doe"
      },
      "shape_id": "node-42",
      "is_resolved": false,
      "created_at": "2024-01-16T10:00:00Z",
      "replies": [
        {
          "id": 2,
          "content": "Agreed, let's update the styling",
          "author": {...},
          "is_resolved": false,
          "replies": []
        }
      ]
    }
  ],
  "total": 5,
  "unresolved_count": 3
}
```

---

### Create Comment

**POST** `/drawings/{drawing_id}/comments`

Add a new comment to a drawing.

**Parameters**:
- `drawing_id` (integer, required): Drawing ID

**Request Body**:
```json
{
  "content": "This section needs to be updated",
  "shape_id": "node-42",
  "parent_comment_id": null
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "drawing_id": 123,
  "content": "This section needs to be updated",
  "author": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "shape_id": "node-42",
  "parent_comment_id": null,
  "is_resolved": false,
  "created_at": "2024-01-16T10:00:00Z"
}
```

---

### Update Comment

**PUT** `/drawings/{drawing_id}/comments/{comment_id}`

Edit comment content (only by author).

**Parameters**:
- `drawing_id` (integer, required): Drawing ID
- `comment_id` (integer, required): Comment ID

**Request Body**:
```json
{
  "content": "Updated comment content"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "content": "Updated comment content",
  "updated_at": "2024-01-16T10:30:00Z"
}
```

---

### Delete Comment

**DELETE** `/drawings/{drawing_id}/comments/{comment_id}`

Delete a comment and all its replies.

**Parameters**:
- `drawing_id` (integer, required): Drawing ID
- `comment_id` (integer, required): Comment ID

**Response** (204 No Content)

---

### Resolve Comment

**POST** `/drawings/{drawing_id}/comments/{comment_id}/resolve`

Mark a comment as resolved.

**Parameters**:
- `drawing_id` (integer, required): Drawing ID
- `comment_id` (integer, required): Comment ID

**Response** (200 OK):
```json
{
  "id": 1,
  "is_resolved": true,
  "resolved_by_id": 1,
  "resolved_at": "2024-01-16T11:00:00Z"
}
```

---

### Get Comment Summary

**GET** `/drawings/{drawing_id}/comments/summary`

Get comment statistics for a drawing.

**Parameters**:
- `drawing_id` (integer, required): Drawing ID

**Response** (200 OK):
```json
{
  "drawing_id": 123,
  "total_comments": 10,
  "resolved_comments": 6,
  "unresolved_comments": 4,
  "comments_by_shape": {
    "node-1": 4,
    "node-2": 3,
    "edge-1": 2,
    "other": 1
  }
}
```

---

## Export

### Generate Export

**POST** `/drawings/{drawing_id}/export`

Export drawing in specified format.

**Parameters**:
- `drawing_id` (integer, required): Drawing ID

**Query Parameters**:
| Parameter | Type | Options | Default |
|-----------|------|---------|---------|
| `format` | string | png, svg, pdf, json | png |
| `width` | integer | 100-10000 | auto |
| `height` | integer | 100-10000 | auto |
| `quality` | integer | 1-100 | 90 |

**Example**:
```bash
POST /drawings/123/export?format=pdf&width=1920&height=1080
```

**Response** (202 Accepted):
```json
{
  "export_id": "exp_abc123def",
  "status": "processing",
  "format": "pdf",
  "created_at": "2024-01-16T12:00:00Z"
}
```

---

### Get Export Status

**GET** `/exports/{export_id}`

Check export generation status.

**Parameters**:
- `export_id` (string, required): Export ID from generation response

**Response** (200 OK):
```json
{
  "export_id": "exp_abc123def",
  "status": "completed",
  "format": "pdf",
  "download_url": "https://minio.local/icecharts-exports/exp_abc123def.pdf",
  "created_at": "2024-01-16T12:00:00Z",
  "expires_at": "2024-01-17T12:00:00Z"
}
```

**Status Values**:
- `processing`: Export is being generated
- `completed`: Export ready for download
- `failed`: Export generation failed
- `expired`: Download link expired

---

## Sharing

### Get Share Settings

**GET** `/drawings/{id}/share`

Get current share settings for a drawing.

**Parameters**:
- `id` (integer, required): Drawing ID

**Response** (200 OK):
```json
{
  "drawing_id": 123,
  "is_public": true,
  "public_token": "share_abc123",
  "permissions": {
    "can_view": true,
    "can_edit": false,
    "can_comment": true,
    "can_export": false
  },
  "shared_with": [
    {
      "user_id": 2,
      "email": "user2@example.com",
      "full_name": "Jane Smith",
      "permission_level": "edit",
      "shared_at": "2024-01-16T10:00:00Z"
    }
  ]
}
```

---

### Update Share Settings

**PUT** `/drawings/{id}/share`

Update drawing sharing settings.

**Parameters**:
- `id` (integer, required): Drawing ID

**Request Body**:
```json
{
  "is_public": true,
  "permissions": {
    "can_view": true,
    "can_edit": false,
    "can_comment": true,
    "can_export": false
  }
}
```

**Response** (200 OK):
```json
{
  "drawing_id": 123,
  "is_public": true,
  "public_token": "share_abc123",
  "permissions": {...}
}
```

---

### Share with User

**POST** `/drawings/{id}/share/user`

Share drawing with specific user.

**Parameters**:
- `id` (integer, required): Drawing ID

**Request Body**:
```json
{
  "user_email": "user2@example.com",
  "permission_level": "edit"  // or "view"
}
```

**Response** (201 Created):
```json
{
  "user_id": 2,
  "email": "user2@example.com",
  "permission_level": "edit",
  "shared_at": "2024-01-16T14:00:00Z"
}
```

---

### Revoke Share

**DELETE** `/drawings/{id}/share/{user_id}`

Remove user's access to drawing.

**Parameters**:
- `id` (integer, required): Drawing ID
- `user_id` (integer, required): User ID to remove

**Response** (204 No Content)

---

## Users

### Get Current User

**GET** `/users/me`

Get authenticated user's profile.

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "maintainer",
  "avatar_url": null,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### Update Profile

**PUT** `/users/me`

Update user's own profile.

**Request Body**:
```json
{
  "full_name": "John Updated",
  "avatar_url": "https://example.com/avatar.png"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Updated",
  "avatar_url": "https://example.com/avatar.png"
}
```

---

### Change Password

**POST** `/users/me/change-password`

Change authenticated user's password.

**Request Body**:
```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

**Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

---

### List Users (Admin Only)

**GET** `/users`

Get all users (requires admin role).

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `skip` | integer | Pagination offset |
| `limit` | integer | Max results |
| `role` | string | Filter by role |
| `search` | string | Search by email/name |

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "email": "user1@example.com",
      "full_name": "John Doe",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 25,
  "skip": 0,
  "limit": 20
}
```

---

## Connectors

The Connector Framework provides endpoints for managing external service integrations.
See [CONNECTORS.md](CONNECTORS.md) for complete documentation.

### List Connectors

**GET** `/connectors`

Get all available connectors and their node definitions.

**Response** (200 OK):
```json
{
  "connectors": [
    {
      "id": "waddlebot",
      "name": "WaddleBot",
      "description": "Chat bot platform for Twitch, Discord, Slack, Kick",
      "icon": "🤖",
      "color": "#6366F1",
      "version": "1.0.0",
      "triggers": [
        {
          "id": "command",
          "name": "Chat Command",
          "description": "Triggered when a chat command is executed",
          "icon": "💬",
          "outputs": [{"name": "out", "type": "object"}],
          "config_schema": [...]
        }
      ],
      "actions": [...],
      "transforms": [...]
    }
  ]
}
```

---

### Get Connector

**GET** `/connectors/{connector_id}`

Get a specific connector's definition.

**Path Parameters**:
- `connector_id` (string): Connector identifier (e.g., "waddlebot")

**Response** (200 OK):
```json
{
  "connector": {
    "id": "waddlebot",
    "name": "WaddleBot",
    ...
  }
}
```

**Error Responses**:
- `404 Not Found`: Connector not found

---

### Get Connector Nodes

**GET** `/connectors/{connector_id}/nodes`

Get all nodes (triggers, actions, transforms) for a specific connector.

**Path Parameters**:
- `connector_id` (string): Connector identifier

**Response** (200 OK):
```json
{
  "nodes": [
    {
      "node_type": "trigger_waddlebot_command",
      "category": "triggers",
      "name": "WaddleBot: Chat Command",
      "description": "Triggered when a chat command is executed",
      "icon": "💬",
      "inputs": [],
      "outputs": [{"name": "out", "type": "object"}],
      "config_schema": [...],
      "connector_id": "waddlebot",
      "connector_color": "#6366F1"
    }
  ]
}
```

---

### Get All Connector Nodes

**GET** `/connectors/nodes`

Get all connector nodes across all connectors.

**Query Parameters**:
- `category` (optional): Filter by category (`triggers`, `actions`, `transforms`)

**Response** (200 OK):
```json
{
  "nodes": [
    {
      "node_type": "trigger_waddlebot_command",
      "category": "triggers",
      "name": "WaddleBot: Chat Command",
      "connector_id": "waddlebot",
      "connector_name": "WaddleBot",
      "connector_color": "#6366F1",
      ...
    },
    {
      "node_type": "action_waddlebot_send_chat",
      "category": "actions",
      "name": "WaddleBot: Send Chat",
      ...
    }
  ]
}
```

---

## Elder Integration

### Validate Connection

**POST** `/elder/validate-connection`

Test connection to Elder instance.

**Request Body**:
```json
{
  "elder_url": "https://elder.example.com",
  "api_key": "your-api-key"
}
```

**Response** (200 OK):
```json
{
  "status": "connected",
  "version": "1.0.0",
  "message": "Successfully connected to Elder"
}
```

---

### Get Entities

**GET** `/elder/entities`

Fetch infrastructure entities from Elder.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_type` | string | Filter by type |
| `limit` | integer | Max results |
| `skip` | integer | Pagination offset |

**Response** (200 OK):
```json
{
  "entities": [
    {
      "id": "ent_001",
      "name": "web-server-01",
      "type": "server",
      "status": "active",
      "properties": {
        "location": "us-west",
        "owner": "DevOps Team"
      }
    }
  ],
  "total": 42
}
```

---

### Get Relationships

**GET** `/elder/relationships`

Fetch dependencies between entities.

**Response** (200 OK):
```json
{
  "relationships": [
    {
      "source_entity_id": "ent_001",
      "target_entity_id": "ent_002",
      "relationship_type": "depends_on",
      "description": "Web server depends on database"
    }
  ],
  "total": 15
}
```

---

### Import Entities

**POST** `/elder/import`

Import selected entities as drawing shapes.

**Request Body**:
```json
{
  "drawing_id": 123,
  "entity_ids": ["ent_001", "ent_002", "ent_003"],
  "include_relationships": true
}
```

**Response** (200 OK):
```json
{
  "drawing_id": 123,
  "imported_count": 3,
  "relationship_count": 2,
  "shapes": [
    {
      "id": "node-001",
      "entity_id": "ent_001",
      "type": "rectangle",
      "text": "web-server-01"
    }
  ]
}
```

---

## Health & Status

### Health Check

**GET** `/health`

Check API service health.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T15:00:00Z",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "minio": "connected"
  }
}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Drawing with id 999 not found",
    "status": 404,
    "timestamp": "2024-01-16T15:00:00Z"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body |
| `UNAUTHORIZED` | 401 | Missing/invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource doesn't exist |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

## Rate Limiting

API endpoints are rate limited:

- **Authenticated users**: 1000 requests/hour
- **Public endpoints**: 100 requests/hour
- **WebSocket connections**: 10 concurrent connections per user

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705425600
```

---

## WebSocket Events

For real-time collaboration, connect WebSocket to:

**URL**: `ws://localhost:5001/ws`

### Subscribe to Drawing

```json
{
  "action": "subscribe",
  "drawing_id": 123,
  "user_id": 1
}
```

### Receive Updates

```json
{
  "event": "drawing_updated",
  "drawing_id": 123,
  "data": {
    "node_id": "node-1",
    "position": { "x": 150, "y": 200 }
  },
  "user_id": 1,
  "timestamp": "2024-01-16T15:00:00Z"
}
```

---

## Related Documentation

- [Getting Started](GETTING_STARTED.md) - Setup and configuration
- [Architecture](ARCHITECTURE.md) - System design
- [Features Guide](FEATURES.md) - Feature documentation
- [Deployment](DEPLOYMENT.md) - Production deployment
