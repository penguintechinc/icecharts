# Storage Usage and Quota Implementation

## Overview

This document describes the implementation of actual storage usage calculation and quota management for IceCharts. The system calculates storage consumed by drawings, versions, and attachments, and enforces configurable quotas at both user and tenant levels.

## Architecture

### Components

1. **StorageUsageService** (`app/services/storage_usage_service.py`)
   - Core service for calculating storage usage
   - Manages quotas at user and tenant levels
   - Provides storage statistics for dashboard

2. **Storage API Endpoints** (`app/api/v1/storage.py`)
   - `GET /storage/usage` - Get user's current storage usage
   - `GET /storage/quota` - Get user's storage quota
   - `PUT /storage/quota` - Update storage quota (admin only)

3. **Dashboard Widget** (`app/api/v1/dashboard.py`)
   - `GET /dashboard/storage` - Get storage stats for dashboard widget

### Database Schema

#### Existing Tables Used

- **tenants**: `storage_quota_gb` field stores tenant quota in GB
- **identities**: User data (tenant_id references)
- **drawings**: User's drawings
- **drawing_versions**: Version history
- **storage_providers**: Storage provider configuration

#### Future Enhancements

- Add `storage_quota_bytes` field to `identities` table for user-level quotas
- Add attachment/thumbnail storage tracking tables

## Detailed Implementation

### Storage Usage Calculation

The `StorageUsageService` calculates storage usage by:

1. **Drawing Content** (`_calculate_drawing_content_size`)
   - Queries object storage (MinIO/S3) for latest version of each drawing
   - Sums file sizes from metadata

2. **Drawing Versions** (`_calculate_drawing_versions_size`)
   - Lists all historical versions in object storage
   - Sums size of each version

3. **Attachments** (`_calculate_attachments_size`)
   - Placeholder for future implementation
   - Currently returns 0

4. **Thumbnails** (`_calculate_thumbnails_size`)
   - Placeholder for future implementation
   - Currently returns 0

### Quota Management

#### User Quota Flow

1. User has implicit quota tied to their tenant
2. Call `get_user_quota(user_id)` to get quota in bytes
3. Currently uses tenant's `storage_quota_gb` field
4. Returns default (1GB) if tenant not found

#### Tenant Quota Flow

1. Tenant has configurable quota in `storage_quota_gb` field
2. Call `get_tenant_quota(tenant_id)` to get quota in bytes
3. Returns default (10GB) if tenant not found
4. Call `set_tenant_quota(tenant_id, quota_gb)` to update (admin only)

#### Quota Checks

```python
# Check if user would exceed quota
if StorageUsageService.check_quota_exceeded(user_id, additional_bytes=1024*1024):
    # Handle quota exceeded
    pass
```

### API Endpoints

#### GET /storage/usage

Returns detailed storage usage breakdown:

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

#### GET /storage/quota

Returns current quota information:

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

#### PUT /storage/quota

Update quota (admin only). Supports both user and tenant updates:

**Update Tenant Quota:**
```json
{
  "tenant_id": 1,
  "quota_gb": 20
}
```

**Update User Quota:**
```json
{
  "user_id": 5,
  "quota_mb": 2048
}
```

Response:
```json
{
  "message": "Tenant storage quota updated successfully",
  "tenant_id": 1,
  "quota_gb": 20
}
```

#### GET /dashboard/storage

Returns simplified storage stats for dashboard widget:

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

**Usage Status Values:**
- `"ok"`: 0-74% of quota used
- `"warning"`: 75-89% of quota used
- `"critical"`: 90%+ of quota used

## Integration Points

### With DrawingStorageService

The storage usage service integrates with `DrawingStorageService` to:
- Get file metadata from object storage
- List all versions of a drawing
- Check storage availability

### With Dashboard

The dashboard can display a storage widget showing:
- Used storage in MB
- Total quota in MB
- Usage percentage
- Status indicator (ok/warning/critical)
- Total number of drawings

### With Storage API

The storage endpoints use the service to:
- Calculate actual usage on-demand
- Enforce quotas before uploads (future)
- Provide detailed breakdowns by provider

## Error Handling

All service methods include comprehensive error handling:

1. **Graceful Degradation**: If object storage is unavailable, size calculations return 0
2. **Default Values**: Missing quotas return sensible defaults
3. **Logging**: All errors are logged via Flask logger
4. **Safe Fallbacks**: Service returns minimum viable data even on errors

## Performance Considerations

### Caching Opportunities

For frequently accessed data, consider adding caching:

```python
# Example: Cache storage usage for 5 minutes
@cache.cached(timeout=300, key_prefix='storage_usage_')
def get_user_storage_usage(user_id: int):
    ...
```

### Query Optimization

Current implementation:
- Uses direct object storage queries (MinIO/S3)
- Single pass through drawing list
- Groups by provider efficiently

Future optimizations:
- Cache size information in database
- Background job to update cached sizes
- Incremental updates on drawing changes

## Future Enhancements

### 1. Database Storage Quota Fields

Add to `identities` table:
```python
Field("storage_quota_bytes", "integer", default=None),
```

This enables per-user quotas independent of tenant.

### 2. Attachment Tracking

Implement `_calculate_attachments_size()`:
- Query attachment storage location
- Sum file sizes
- Track by user/tenant

### 3. Thumbnail Caching

Implement `_calculate_thumbnails_size()`:
- Query thumbnail storage
- Sum file sizes
- Plan for optimization

### 4. Storage Events

Track storage operations:
- Log quota exceedances
- Track usage trends
- Alert on high usage

### 5. Background Job

Create async task to:
- Calculate usage daily
- Cache results in database
- Trigger alerts on threshold

### 6. Quota Enforcement

Implement pre-upload checks:
- Reject uploads exceeding quota
- Provide helpful error messages
- Suggest quota increase

### 7. Storage Analytics

Build reports showing:
- Usage trends over time
- Provider usage distribution
- Per-drawing breakdown
- Cost estimation

## Testing

### Unit Tests

Test individual service methods:
- Drawing size calculation
- Version size calculation
- Quota lookups
- Status determination

### Integration Tests

Test full flows:
- Calculate usage for user with multiple drawings
- Update quotas
- Get dashboard widget
- Check quota exceeded

### Performance Tests

Benchmark with large datasets:
- 1000+ drawings
- 100+ versions per drawing
- Multiple storage providers

## Migration Guide

For existing installations:

1. No database migration needed initially
   - Uses existing `storage_quota_gb` on tenants table

2. Update drawing uploads to check quota
   - Call `check_quota_exceeded()` before saving

3. Add dashboard widget to UI
   - Call `GET /dashboard/storage` endpoint

4. (Optional) Add user-level quotas
   - Add `storage_quota_bytes` to identities table
   - Update `get_user_quota()` to check user field first

## Debugging

### Check Storage Configuration

```python
from app.services.drawing_storage_service import DrawingStorageService

# Verify storage is available
if DrawingStorageService.is_available():
    print("Storage available")
else:
    print("Storage not available")
```

### Get Raw Usage Data

```python
from app.services.storage_usage_service import StorageUsageService

# Get detailed breakdown
usage = StorageUsageService.get_user_storage_usage(user_id)
print(f"User {user_id} using {usage['total_size_mb']}MB of {usage['quota_mb']}MB")
```

### Check Tenant Quota

```python
from app.services.storage_usage_service import StorageUsageService

quota_bytes = StorageUsageService.get_tenant_quota(tenant_id)
quota_gb = quota_bytes / (1024 * 1024 * 1024)
print(f"Tenant quota: {quota_gb}GB")
```

## Files Modified

1. **Created:**
   - `app/services/storage_usage_service.py` - Main storage service

2. **Updated:**
   - `app/api/v1/storage.py` - Implemented actual endpoints
   - `app/api/v1/dashboard.py` - Added storage widget endpoint

## Configuration

### Environment Variables

Used from DrawingStorageService configuration:
- `STORAGE_PROVIDER` - Provider type (minio, s3, etc.)
- `STORAGE_ENDPOINT` - Object storage endpoint
- `STORAGE_ACCESS_KEY` - Access credentials
- `STORAGE_SECRET_KEY` - Secret credentials
- `STORAGE_BUCKET` - Bucket name

### Database Fields

- `tenants.storage_quota_gb` - Tenant quota (existing)
- `identities.tenant_id` - User's tenant (existing)

## References

- DrawingStorageService: `app/services/drawing_storage_service.py`
- Storage Providers: `app/storage/` directory
- Database Models: `app/models/pydal_models.py`
