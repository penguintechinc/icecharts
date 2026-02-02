# IceRuns API Reference

Complete REST API documentation for IceRuns.

## Base URL
```
https://your-icecharts.com/api/v1
```

## Authentication

All endpoints require authentication via JWT bearer token (except webhooks):
```bash
curl -H "Authorization: Bearer <your-token>" \
  https://your-icecharts.com/api/v1/iceruns
```

## Functions Management

### List Functions

**Endpoint:** `GET /iceruns`

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `limit` (int, default: 20, max: 100) - Results per page
- `status` (string) - Filter by status (draft, active, paused, archived)
- `runtime` (string) - Filter by runtime
- `search` (string) - Search in name/description
- `tags` (string) - Comma-separated tag filter

**Response:**
```json
{
  "functions": [
    {
      "function_id": "f7e8d9c0-...",
      "name": "Process Image",
      "description": "Resize images",
      "runtime": "python3.13",
      "status": "active",
      "created_at": "2026-01-20T12:00:00Z",
      "execution_count": 1250,
      "last_executed_at": "2026-01-20T15:30:45Z",
      "webhook_url": "https://your-icecharts.com/api/v1/iceruns/hook/abc123..."
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

**Required Scopes:** `iceruns:read`

---

### Create Function

**Endpoint:** `POST /iceruns`

**Request Body:**
```json
{
  "name": "Process Image",
  "description": "Resize and optimize images",
  "runtime": "python3.13",
  "entrypoint": "main.py",
  "handler": "main.process",
  "memory_limit_mb": 512,
  "timeout_seconds": 120,
  "cpu_limit": 0.5,
  "env_vars": {
    "API_KEY": "encrypted-value",
    "REGION": "us-east-1"
  },
  "tags": ["image", "processing"]
}
```

**Response (201 Created):**
```json
{
  "function_id": "f7e8d9c0-...",
  "name": "Process Image",
  "runtime": "python3.13",
  "status": "draft",
  "webhook_token": "abc123...",
  "webhook_url": "https://your-icecharts.com/api/v1/iceruns/hook/abc123...",
  "created_at": "2026-01-20T12:00:00Z"
}
```

**Required Scopes:** `iceruns:write`

---

### Get Function

**Endpoint:** `GET /iceruns/{function_id}`

**Response:**
```json
{
  "function_id": "f7e8d9c0-...",
  "name": "Process Image",
  "description": "Resize and optimize images",
  "runtime": "python3.13",
  "entrypoint": "main.py",
  "handler": "main.process",
  "status": "active",
  "package_size": 15728640,
  "package_hash": "sha256:...",
  "memory_limit_mb": 512,
  "timeout_seconds": 120,
  "cpu_limit": 0.5,
  "env_vars": {
    "API_KEY": "***",
    "REGION": "us-east-1"
  },
  "execution_count": 1250,
  "last_executed_at": "2026-01-20T15:30:45Z",
  "created_at": "2026-01-20T12:00:00Z",
  "updated_at": "2026-01-20T14:00:00Z"
}
```

**Required Scopes:** `iceruns:read`

---

### Update Function

**Endpoint:** `PUT /iceruns/{function_id}`

**Request Body:** (all fields optional)
```json
{
  "name": "New Name",
  "description": "Updated description",
  "memory_limit_mb": 1024,
  "timeout_seconds": 300,
  "env_vars": {
    "NEW_KEY": "new-value"
  }
}
```

**Response:** Updated function object

**Required Scopes:** `iceruns:write`

---

### Delete Function

**Endpoint:** `DELETE /iceruns/{function_id}`

**Response (204 No Content)**

**Required Scopes:** `iceruns:delete`

---

## Package Management

### Upload Package

**Endpoint:** `POST /iceruns/{function_id}/package`

**Content-Type:** `multipart/form-data`

**Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "package=@function.zip" \
  https://your-icecharts.com/api/v1/iceruns/{function_id}/package
```

**Response:**
```json
{
  "function_id": "f7e8d9c0-...",
  "package_size": 15728640,
  "package_hash": "sha256:abcdef...",
  "uploaded_at": "2026-01-20T12:00:00Z"
}
```

**Required Scopes:** `iceruns:write`

---

### Get Package URL

**Endpoint:** `GET /iceruns/{function_id}/package`

**Query Parameters:**
- `expires_in` (int, default: 3600) - URL expiry in seconds

**Response:**
```json
{
  "download_url": "https://minio.example.com/icecharts/...",
  "expires_at": "2026-01-20T13:00:00Z"
}
```

**Required Scopes:** `iceruns:read`

---

## Execution Management

### Execute Function

**Endpoint:** `POST /iceruns/{function_id}/execute`

**Request Body:**
```json
{
  "input": {
    "image_url": "https://example.com/photo.jpg",
    "width": 800
  },
  "async": true,
  "timeout_override": 120
}
```

**Response (async=true):**
```json
{
  "execution_id": "e1a2b3c4-...",
  "status": "queued",
  "function_id": "f7e8d9c0-...",
  "created_at": "2026-01-20T12:01:00Z",
  "status_url": "/api/v1/iceruns/executions/e1a2b3c4-.../status",
  "websocket_url": "wss://your-icecharts.com/ws/iceruns/executions/e1a2b3c4-..."
}
```

**Response (async=false):**
```json
{
  "execution_id": "e1a2b3c4-...",
  "status": "completed",
  "output": {
    "optimized_url": "https://cdn.example.com/photo.jpg"
  },
  "duration_ms": 2340,
  "exit_code": 0
}
```

**Required Scopes:** `iceruns:execute`

---

### Get Execution

**Endpoint:** `GET /iceruns/executions/{execution_id}`

**Response:**
```json
{
  "execution_id": "e1a2b3c4-...",
  "function_id": "f7e8d9c0-...",
  "status": "completed",
  "input": {
    "image_url": "https://example.com/photo.jpg"
  },
  "output": {
    "optimized_url": "https://cdn.example.com/photo.jpg"
  },
  "exit_code": 0,
  "duration_ms": 2340,
  "memory_used_mb": 256,
  "cpu_time_ms": 1800,
  "started_at": "2026-01-20T12:01:05Z",
  "completed_at": "2026-01-20T12:01:07Z",
  "created_at": "2026-01-20T12:01:00Z"
}
```

**Required Scopes:** `iceruns:logs`

---

### Get Execution Logs

**Endpoint:** `GET /iceruns/executions/{execution_id}/logs`

**Response:**
```json
{
  "stdout": "Processing image...\nOptimized successfully\n",
  "stderr": "",
  "exit_code": 0
}
```

**Required Scopes:** `iceruns:logs`

---

### List Executions

**Endpoint:** `GET /iceruns/{function_id}/executions`

**Query Parameters:**
- `page` (int) - Page number
- `limit` (int) - Results per page
- `status` (string) - Filter by status

**Response:**
```json
{
  "executions": [
    {
      "execution_id": "e1a2b3c4-...",
      "status": "completed",
      "exit_code": 0,
      "duration_ms": 2340,
      "created_at": "2026-01-20T12:01:00Z"
    }
  ],
  "total": 1250,
  "page": 1
}
```

**Required Scopes:** `iceruns:logs`

---

### Cancel Execution

**Endpoint:** `DELETE /iceruns/executions/{execution_id}`

**Response (204 No Content)**

**Required Scopes:** `iceruns:execute` (own) or `iceruns:admin` (any)

---

### Retry Execution

**Endpoint:** `POST /iceruns/executions/{execution_id}/retry`

**Response:**
```json
{
  "new_execution_id": "e5f6g7h8-...",
  "parent_execution_id": "e1a2b3c4-...",
  "status": "queued"
}
```

**Required Scopes:** `iceruns:execute`

---

## Function Status

### Activate Function

**Endpoint:** `PUT /iceruns/{function_id}/activate`

**Response:** Updated function object with `status: "active"`

**Required Scopes:** `iceruns:write`

---

### Pause Function

**Endpoint:** `PUT /iceruns/{function_id}/pause`

**Response:** Updated function object with `status: "paused"`

**Required Scopes:** `iceruns:write`

---

### Archive Function

**Endpoint:** `PUT /iceruns/{function_id}/archive`

**Response:** Updated function object with `status: "archived"`

**Required Scopes:** `iceruns:delete`

---

## Webhook Endpoints

### Public Webhook Trigger

**Endpoint:** `POST /iceruns/hook/{webhook_token}`

**Authentication:** Token in URL

**Content-Type:** `application/json` or `multipart/form-data`

**Request:**
```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/abc123... \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

**Response:**
```json
{
  "execution_id": "e1a2b3c4-...",
  "status": "queued",
  "webhook_timestamp": "2026-01-20T12:01:00Z"
}
```

**No authentication required** (token-based)

---

### Get Webhook Configuration

**Endpoint:** `GET /iceruns/{function_id}/webhook`

**Response:**
```json
{
  "webhook_url": "https://your-icecharts.com/api/v1/iceruns/hook/abc123...",
  "webhook_token": "abc123...",
  "validate_signature": false,
  "allowed_methods": ["POST"],
  "rate_limit": 100,
  "ip_whitelist": []
}
```

**Required Scopes:** `iceruns:read`

---

### Update Webhook Configuration

**Endpoint:** `PUT /iceruns/{function_id}/webhook/config`

**Request:**
```json
{
  "validate_signature": true,
  "allowed_methods": ["GET", "POST"],
  "rate_limit": 500,
  "ip_whitelist": ["203.0.113.0/24"]
}
```

**Response:** Updated webhook config

**Required Scopes:** `iceruns:write`

---

### Regenerate Webhook Token

**Endpoint:** `POST /iceruns/{function_id}/webhook/regenerate`

**Response:**
```json
{
  "webhook_url": "https://your-icecharts.com/api/v1/iceruns/hook/xyz789...",
  "webhook_token": "xyz789...",
  "created_at": "2026-01-20T12:02:00Z"
}
```

**Required Scopes:** `iceruns:write`

---

## Statistics

### Function Statistics

**Endpoint:** `GET /iceruns/{function_id}/stats`

**Response:**
```json
{
  "function_id": "f7e8d9c0-...",
  "total_executions": 1250,
  "successful_executions": 1200,
  "failed_executions": 50,
  "success_rate": 96.0,
  "average_duration_ms": 2340,
  "p50_duration_ms": 2100,
  "p95_duration_ms": 4500,
  "p99_duration_ms": 6200,
  "average_memory_mb": 256,
  "max_memory_mb": 512
}
```

**Required Scopes:** `iceruns:read`

---

### Global Statistics

**Endpoint:** `GET /iceruns/stats`

**Response:**
```json
{
  "total_functions": 42,
  "active_functions": 38,
  "total_executions": 125000,
  "executions_today": 8500,
  "average_success_rate": 97.3,
  "active_invokers": 5,
  "queue_size": 342,
  "p50_latency_ms": 2100,
  "p99_latency_ms": 6200
}
```

**Required Scopes:** `iceruns:read`

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "invalid_input",
  "message": "Timeout must be between 1 and 900 seconds",
  "details": {
    "field": "timeout_seconds",
    "value": 1200
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "insufficient_scope",
  "message": "This operation requires iceruns:execute scope",
  "required_scopes": ["iceruns:execute"]
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Function not found",
  "type": "function",
  "id": "f7e8d9c0-..."
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit: 100 requests per hour",
  "retry_after": 3600
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req-12345..."
}
```

---

## Status Codes Reference

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Successful (no body) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Auth failed |
| 403 | Forbidden - No permission |
| 404 | Not Found - Resource missing |
| 409 | Conflict - Invalid state transition |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Error - Server error |

---

## Execution Status Values

- `queued` - Waiting in execution queue
- `running` - Currently executing
- `completed` - Finished with exit code 0
- `failed` - Finished with non-zero exit code
- `timeout` - Exceeded timeout limit
- `cancelled` - Manually cancelled

---

See also:
- [Webhooks Guide](./webhook-guide.md)
- [Security](./security.md)
- [Troubleshooting](./troubleshooting.md)
