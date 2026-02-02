# Storage API Reference

## Quick Reference Guide

### Endpoints Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/storage/usage` | GET | Required | Get user's storage usage |
| `/storage/quota` | GET | Required | Get user's storage quota |
| `/storage/quota` | PUT | Admin | Update storage quota |
| `/dashboard/storage` | GET | Required | Get storage widget data |

---

## Detailed Endpoint Documentation

### 1. GET /storage/usage

Get detailed storage usage breakdown for the current user.

**Request:**
```bash
curl -X GET http://localhost:5000/api/v1/storage/usage \
  -H "Authorization: Bearer {token}"
```

**Response:**
```json
{
  "usage": {
    "user_id": 1,
    "total_size_bytes": 524288000,
    "total_size_mb": 500.0,
    "total_drawings": 42,
    "drawings_content_bytes": 400000000,
    "drawing_versions_bytes": 100000000,
    "attachments_bytes": 24288000,
    "thumbnails_bytes": 0,
    "quota_bytes": 1073741824,
    "quota_mb": 1024.0,
    "usage_percentage": 48.83,
    "by_provider": [
      {
        "provider_id": 1,
        "provider_name": "MinIO Default",
        "provider_type": "minio",
        "size_bytes": 500000000,
        "size_mb": 476.83,
        "file_count": 50
      }
    ]
  }
}
```

**Response Fields:**
- `total_size_bytes` - Total storage used in bytes
- `total_size_mb` - Total storage used in megabytes
- `total_drawings` - Number of drawings owned by user
- `drawings_content_bytes` - Size of drawing content files
- `drawing_versions_bytes` - Size of all version history
- `attachments_bytes` - Size of attachments (currently 0)
- `thumbnails_bytes` - Size of thumbnails (currently 0)
- `quota_bytes` - User's quota in bytes
- `quota_mb` - User's quota in megabytes
- `usage_percentage` - Percentage of quota used (0-100+)
- `by_provider` - Breakdown by storage provider

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `500` - Server error

---

### 2. GET /storage/quota

Get the current user's storage quota.

**Request:**
```bash
curl -X GET http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer {token}"
```

**Response:**
```json
{
  "quota": {
    "user_id": 1,
    "quota_bytes": 1073741824,
    "quota_mb": 1024.0,
    "quota_type": "tenant",
    "can_increase": false
  }
}
```

**Response Fields:**
- `user_id` - The user's ID
- `quota_bytes` - Quota limit in bytes
- `quota_mb` - Quota limit in megabytes
- `quota_type` - Type of quota ("tenant" or "user")
- `can_increase` - Whether user can increase their own quota

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `500` - Server error

---

### 3. PUT /storage/quota

Update a user's or tenant's storage quota. **Admin only.**

**Request (Update Tenant Quota):**
```bash
curl -X PUT http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 1,
    "quota_gb": 20
  }'
```

**Request (Update User Quota):**
```bash
curl -X PUT http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 5,
    "quota_mb": 2048
  }'
```

**Request Body:**

For tenant quota:
```json
{
  "tenant_id": 1,
  "quota_gb": 20
}
```

For user quota:
```json
{
  "user_id": 5,
  "quota_mb": 2048
}
```

**Response (Tenant):**
```json
{
  "message": "Tenant storage quota updated successfully",
  "tenant_id": 1,
  "quota_gb": 20
}
```

**Response (User):**
```json
{
  "message": "User storage quota updated successfully",
  "user_id": 5,
  "quota_mb": 2048
}
```

**Request Requirements:**
- Must provide either `tenant_id` or `user_id`
- For tenant: provide `quota_gb` (in gigabytes)
- For user: provide `quota_mb` (in megabytes)
- Quota must be >= 0

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing/invalid parameters)
- `401` - Unauthorized
- `403` - Forbidden (not admin)
- `500` - Server error

**Error Responses:**

Missing parameters:
```json
{
  "error": "tenant_id and quota_gb are required for tenant quota"
}
```

Invalid quota:
```json
{
  "error": "Quota must be non-negative"
}
```

Missing auth:
```json
{
  "error": "Either user_id or tenant_id must be provided"
}
```

---

### 4. GET /dashboard/storage

Get simplified storage statistics for dashboard widget display.

**Request:**
```bash
curl -X GET http://localhost:5000/api/v1/dashboard/storage \
  -H "Authorization: Bearer {token}"
```

**Response:**
```json
{
  "storage": {
    "used_mb": 500.0,
    "quota_mb": 1024.0,
    "usage_percentage": 48.83,
    "usage_status": "ok",
    "total_drawings": 42
  }
}
```

**Response Fields:**
- `used_mb` - Storage used in MB
- `quota_mb` - Storage quota in MB
- `usage_percentage` - Percentage of quota used (0-100+)
- `usage_status` - Status indicator:
  - `"ok"` - 0-74% used
  - `"warning"` - 75-89% used
  - `"critical"` - 90%+ used
- `total_drawings` - Number of drawings owned by user

**Status Codes:**
- `200` - Success
- `401` - Unauthorized
- `500` - Server error

---

## Code Examples

### Python (requests library)

```python
import requests

BASE_URL = "http://localhost:5000/api/v1"
TOKEN = "your-auth-token"
headers = {"Authorization": f"Bearer {TOKEN}"}

# Get storage usage
response = requests.get(
    f"{BASE_URL}/storage/usage",
    headers=headers
)
usage = response.json()["usage"]
print(f"Using {usage['total_size_mb']}MB of {usage['quota_mb']}MB")

# Get storage quota
response = requests.get(
    f"{BASE_URL}/storage/quota",
    headers=headers
)
quota = response.json()["quota"]
print(f"Quota: {quota['quota_mb']}MB")

# Update tenant quota (admin)
admin_token = "admin-token"
headers = {"Authorization": f"Bearer {admin_token}"}
response = requests.put(
    f"{BASE_URL}/storage/quota",
    headers=headers,
    json={"tenant_id": 1, "quota_gb": 20}
)
print(response.json()["message"])

# Get dashboard widget
response = requests.get(
    f"{BASE_URL}/dashboard/storage",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
stats = response.json()["storage"]
print(f"Storage: {stats['usage_status']} ({stats['usage_percentage']}%)")
```

### JavaScript (fetch API)

```javascript
const BASE_URL = "http://localhost:5000/api/v1";
const TOKEN = "your-auth-token";

// Get storage usage
async function getStorageUsage() {
  const response = await fetch(`${BASE_URL}/storage/usage`, {
    headers: { Authorization: `Bearer ${TOKEN}` }
  });
  const data = await response.json();
  return data.usage;
}

// Get storage quota
async function getStorageQuota() {
  const response = await fetch(`${BASE_URL}/storage/quota`, {
    headers: { Authorization: `Bearer ${TOKEN}` }
  });
  const data = await response.json();
  return data.quota;
}

// Update tenant quota (admin)
async function updateTenantQuota(tenantId, quotaGb) {
  const adminToken = "admin-token";
  const response = await fetch(`${BASE_URL}/storage/quota`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${adminToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ tenant_id: tenantId, quota_gb: quotaGb })
  });
  return response.json();
}

// Get dashboard storage widget
async function getDashboardStorage() {
  const response = await fetch(`${BASE_URL}/dashboard/storage`, {
    headers: { Authorization: `Bearer ${TOKEN}` }
  });
  const data = await response.json();
  return data.storage;
}

// Usage
getStorageUsage().then(usage => {
  console.log(`Using ${usage.total_size_mb}MB of ${usage.quota_mb}MB`);
});

getDashboardStorage().then(stats => {
  console.log(`Status: ${stats.usage_status} (${stats.usage_percentage}%)`);
});
```

### cURL Examples

```bash
# Get storage usage
curl -X GET http://localhost:5000/api/v1/storage/usage \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get storage quota
curl -X GET http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update tenant quota (requires admin token)
curl -X PUT http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": 1, "quota_gb": 20}'

# Update user quota (requires admin token)
curl -X PUT http://localhost:5000/api/v1/storage/quota \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 5, "quota_mb": 2048}'

# Get dashboard storage widget
curl -X GET http://localhost:5000/api/v1/dashboard/storage \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Handling

### Common Error Responses

**Unauthorized (401):**
```json
{
  "error": "Unauthorized"
}
```

**Forbidden (403):**
```json
{
  "error": "Access denied"
}
```

**Bad Request (400):**
```json
{
  "error": "Request body required"
}
```

**Server Error (500):**
```json
{
  "error": "Internal server error"
}
```

---

## Best Practices

### 1. Caching
Cache storage widget results for 5-10 minutes in your frontend:
```javascript
const cacheKey = `storage_widget_${userId}`;
const cachedData = localStorage.getItem(cacheKey);
const cacheTime = localStorage.getItem(cacheKey + "_time");

if (cachedData && Date.now() - cacheTime < 300000) {
  // Use cached data (5 minutes)
  return JSON.parse(cachedData);
} else {
  // Fetch fresh data
  const data = await getDashboardStorage();
  localStorage.setItem(cacheKey, JSON.stringify(data));
  localStorage.setItem(cacheKey + "_time", Date.now());
  return data;
}
```

### 2. Warning Users
Display warning when usage exceeds 75%:
```javascript
const stats = await getDashboardStorage();
if (stats.usage_percentage > 75) {
  showWarning(`Storage nearly full: ${stats.usage_percentage}%`);
}
```

### 3. Preventing Quota Exceeded
Check quota before allowing uploads:
```javascript
async function canUploadDrawing(drawingSizeBytes) {
  const usage = await getStorageUsage();
  const remainingBytes = usage.quota_bytes - usage.total_size_bytes;
  return drawingSizeBytes <= remainingBytes;
}
```

---

## Limits and Defaults

| Item | Default | Min | Max |
|------|---------|-----|-----|
| User Quota | 1 GB | 0 GB | Unlimited |
| Tenant Quota | 10 GB | 0 GB | Unlimited |
| Usage Status Check | "ok" | 0% | 100%+ |

---

## Migration from Placeholder

If updating from placeholder implementation:

1. The endpoints now return actual storage usage
2. Calculations happen on-demand
3. No database migration required initially
4. Consider adding background job to cache results

---

## Support

For issues or questions:
- Check STORAGE_IMPLEMENTATION.md for detailed architecture
- Review test_storage_usage_service.py for examples
- Enable debug logging: `FLASK_DEBUG=true`
