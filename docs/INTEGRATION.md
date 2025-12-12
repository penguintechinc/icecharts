# IceCharts External App Integration Guide

This guide documents how to integrate external applications (such as Elder) with IceCharts using service accounts.

## Overview

IceCharts supports service account authentication for machine-to-machine communication. Service accounts provide:

- **Long-lived JWT tokens**: Up to 1 year validity
- **Fine-grained scoped permissions**: Control exactly what the service can access
- **Configurable rate limits**: Higher than regular users (default: 1000/hour vs 100/hour)
- **Token management**: Generate, revoke, and track token usage

## Quick Start

### 1. Create a Service Account (Admin UI/API)

```bash
# Create a service account with specific scopes
curl -X POST "https://your-icecharts.com/api/v1/admin/service-accounts" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Elder Integration",
    "description": "Service account for Elder app",
    "scopes": ["drawings:read", "drawings:write", "exports:create"],
    "rate_limit": 1000
  }'
```

Response:
```json
{
  "success": true,
  "message": "Service account created successfully",
  "service_account": {
    "id": 1,
    "client_id": "sa_abc123def456",
    "name": "Elder Integration",
    "scopes": ["drawings:read", "drawings:write", "exports:create"],
    "rate_limit": 1000,
    "is_active": true
  }
}
```

### 2. Generate an API Token

```bash
curl -X POST "https://your-icecharts.com/api/v1/admin/service-accounts/1/tokens" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Token",
    "expires_days": 365
  }'
```

Response:
```json
{
  "success": true,
  "message": "Token generated successfully. Store it securely - it cannot be retrieved again.",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_info": {
    "token_jti": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Production Token",
    "expires_at": "2026-01-01T00:00:00Z"
  }
}
```

**Important**: Store the token securely. It cannot be retrieved again after creation.

### 3. Use the Token

Include the token in the `Authorization` header:

```bash
curl -X GET "https://your-icecharts.com/api/v1/drawings" \
  -H "Authorization: Bearer <service-account-token>"
```

## Available Scopes

| Scope | Description |
|-------|-------------|
| `drawings:read` | Read drawing metadata and content |
| `drawings:write` | Create and update drawings |
| `drawings:delete` | Delete drawings |
| `exports:create` | Generate exports (PNG, PDF, SVG, JSON) |
| `exports:read` | Download export results |
| `templates:read` | Read available templates |
| `templates:write` | Create and modify templates |
| `collections:read` | Read collections |
| `collections:write` | Manage collections |

### Scope Groups (Convenience)

| Group | Included Scopes |
|-------|-----------------|
| `integration_standard` | drawings:read, drawings:write, exports:create, templates:read |
| `drawings_full` | drawings:read, drawings:write, drawings:delete |
| `readonly` | drawings:read, exports:read, templates:read, collections:read |

## Rate Limits

- **Default service account limit**: 1000 requests/hour
- **Configurable per account**: 1 to 100,000 requests/hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1609459200
```

When rate limited, you'll receive:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

## API Reference

### Service Account Management (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/service-accounts` | List all service accounts |
| POST | `/api/v1/admin/service-accounts` | Create service account |
| GET | `/api/v1/admin/service-accounts/<id>` | Get service account |
| PUT | `/api/v1/admin/service-accounts/<id>` | Update service account |
| DELETE | `/api/v1/admin/service-accounts/<id>` | Delete service account |
| GET | `/api/v1/admin/service-accounts/<id>/tokens` | List tokens |
| POST | `/api/v1/admin/service-accounts/<id>/tokens` | Generate token |
| DELETE | `/api/v1/admin/service-accounts/<id>/tokens/<jti>` | Revoke token |
| POST | `/api/v1/admin/service-accounts/<id>/tokens/revoke-all` | Revoke all tokens |
| GET | `/api/v1/admin/service-accounts/scopes` | List available scopes |

### Key Integration Endpoints

| Method | Endpoint | Required Scope | Description |
|--------|----------|----------------|-------------|
| GET | `/api/v1/drawings` | drawings:read | List drawings |
| POST | `/api/v1/drawings` | drawings:write | Create drawing |
| GET | `/api/v1/drawings/<id>` | drawings:read | Get drawing |
| PUT | `/api/v1/drawings/<id>` | drawings:write | Update drawing |
| DELETE | `/api/v1/drawings/<id>` | drawings:delete | Delete drawing |
| POST | `/api/v1/drawings/<id>/export` | exports:create | Export drawing |
| GET | `/api/v1/templates` | templates:read | List templates |

## Code Examples

### Python (requests)

```python
import requests

class IceChartsClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {token}'
        self.session.headers['Content-Type'] = 'application/json'

    def list_drawings(self):
        """List all accessible drawings."""
        response = self.session.get(f'{self.base_url}/api/v1/drawings')
        response.raise_for_status()
        return response.json()['drawings']

    def create_drawing(self, name: str, content: dict, **kwargs):
        """Create a new drawing."""
        data = {
            'name': name,
            'content': content,
            'visibility': kwargs.get('visibility', 'private'),
            'is_template': kwargs.get('is_template', False),
        }
        response = self.session.post(
            f'{self.base_url}/api/v1/drawings',
            json=data
        )
        response.raise_for_status()
        return response.json()['drawing']

    def export_drawing(self, drawing_id: str, format: str = 'png', **options):
        """Export a drawing to specified format."""
        data = {
            'format': format,
            **options
        }
        response = self.session.post(
            f'{self.base_url}/api/v1/drawings/{drawing_id}/export',
            json=data
        )
        response.raise_for_status()

        # Check if async export
        if response.status_code == 202:
            return {'async': True, 'job_id': response.json()['job_id']}

        return {'async': False, 'content': response.content}


# Usage
client = IceChartsClient(
    base_url='https://your-icecharts.com',
    token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
)

# List drawings
drawings = client.list_drawings()
print(f"Found {len(drawings)} drawings")

# Create a new drawing
new_drawing = client.create_drawing(
    name='My Diagram',
    content={'nodes': [], 'edges': []}
)
print(f"Created drawing: {new_drawing['id']}")

# Export to PNG
result = client.export_drawing(new_drawing['id'], format='png', width=1200, height=800)
if result['async']:
    print(f"Export job queued: {result['job_id']}")
else:
    with open('export.png', 'wb') as f:
        f.write(result['content'])
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class IceChartsClient {
  constructor(baseUrl, token) {
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async listDrawings() {
    const response = await this.client.get('/api/v1/drawings');
    return response.data.drawings;
  }

  async createDrawing(name, content, options = {}) {
    const response = await this.client.post('/api/v1/drawings', {
      name,
      content,
      visibility: options.visibility || 'private',
      is_template: options.isTemplate || false
    });
    return response.data.drawing;
  }

  async exportDrawing(drawingId, format = 'png', options = {}) {
    const response = await this.client.post(
      `/api/v1/drawings/${drawingId}/export`,
      { format, ...options },
      { responseType: response.status === 202 ? 'json' : 'arraybuffer' }
    );

    if (response.status === 202) {
      return { async: true, jobId: response.data.job_id };
    }
    return { async: false, content: response.data };
  }
}

// Usage
const client = new IceChartsClient(
  'https://your-icecharts.com',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
);

(async () => {
  // List drawings
  const drawings = await client.listDrawings();
  console.log(`Found ${drawings.length} drawings`);

  // Create a drawing
  const drawing = await client.createDrawing('My Diagram', {
    nodes: [],
    edges: []
  });
  console.log(`Created drawing: ${drawing.id}`);

  // Export
  const result = await client.exportDrawing(drawing.id, 'png', {
    width: 1200,
    height: 800
  });
  if (result.async) {
    console.log(`Export job queued: ${result.jobId}`);
  }
})();
```

### cURL Examples

```bash
# List drawings
curl -X GET "https://your-icecharts.com/api/v1/drawings" \
  -H "Authorization: Bearer <token>"

# Create drawing
curl -X POST "https://your-icecharts.com/api/v1/drawings" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Diagram",
    "content": {"nodes": [], "edges": []},
    "visibility": "private"
  }'

# Export drawing to PNG
curl -X POST "https://your-icecharts.com/api/v1/drawings/123/export" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"format": "png", "width": 1200, "height": 800}' \
  --output export.png
```

## Error Handling

### Authentication Errors (401)

```json
{
  "error": "Missing authorization token"
}
```

```json
{
  "error": "Invalid or expired token"
}
```

```json
{
  "error": "Service account is deactivated"
}
```

```json
{
  "error": "Service token has been revoked"
}
```

### Scope Errors (403)

```json
{
  "error": "Insufficient scope",
  "required_scopes": ["drawings:delete"],
  "missing_scopes": ["drawings:delete"]
}
```

### Rate Limit Errors (429)

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

## Best Practices

### Token Security

1. **Store tokens securely**: Use environment variables or secrets management
2. **Never commit tokens**: Add to `.gitignore` and use `.env` files
3. **Rotate regularly**: Generate new tokens periodically
4. **Use separate tokens**: Different tokens for different environments

### Scope Minimization

1. **Request only needed scopes**: Don't request more than necessary
2. **Use scope groups**: For common combinations
3. **Audit regularly**: Review and remove unused scopes

### Error Handling

1. **Handle rate limits**: Implement exponential backoff
2. **Check scope errors**: Update token scopes if needed
3. **Monitor token expiration**: Implement automatic renewal

### Rate Limit Management

```python
import time
from requests.exceptions import HTTPError

def api_call_with_retry(client, method, *args, max_retries=3, **kwargs):
    """Make API call with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            return method(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 60))
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
            raise
```

## Changelog

### v1.0.0 (Initial Release)
- Service account support with scoped permissions
- Long-lived JWT tokens (up to 1 year)
- Configurable rate limits per account
- Token management (generate, revoke, track usage)
- Admin API endpoints for service account management
