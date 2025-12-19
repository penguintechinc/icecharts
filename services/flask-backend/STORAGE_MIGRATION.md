# Storage Migration Implementation

## Overview

The storage migration functionality allows users to asynchronously migrate drawing data and files from one storage provider to another. This feature supports large-scale migrations with progress tracking, error handling, and rollback capabilities.

## Architecture

### Components

1. **API Endpoints** (`app/api/v1/storage.py`)
   - `POST /storage/migrate` - Initiate migration
   - `GET /storage/migrations/<migration_id>` - Get migration status
   - `POST /storage/migrations/<migration_id>/cancel` - Cancel migration
   - `POST /storage/migrations/<migration_id>/rollback` - Rollback failed migration
   - `GET /storage/migrations` - List all migrations

2. **Background Tasks** (`app/tasks/migration_tasks.py`)
   - `migrate_storage_task()` - Main migration task
   - `rollback_migration_task()` - Rollback task
   - Async storage provider operations using asyncio

3. **Database** (`app/models/pydal_models.py`)
   - `migration_jobs` table - Tracks all migration operations

4. **Storage Services** (`app/services/drawing_storage_service.py`)
   - Leverages existing DrawingStorageService for file operations
   - Uses asyncio for async provider operations

## Database Schema

### migration_jobs Table

```sql
CREATE TABLE migration_jobs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id INTEGER NOT NULL REFERENCES identities(id),
    source_provider_id INTEGER NOT NULL REFERENCES storage_providers(id),
    target_provider_id INTEGER NOT NULL REFERENCES storage_providers(id),
    status VARCHAR(50) DEFAULT 'pending',
        -- Values: pending, queued, in_progress, completed, completed_with_errors,
        --         failed, rolled_back, rollback_failed, cancelled
    progress INTEGER DEFAULT 0,              -- 0-100 percentage
    total_count INTEGER DEFAULT 0,           -- Total drawings to migrate
    migrated_count INTEGER DEFAULT 0,        -- Successfully migrated
    failed_count INTEGER DEFAULT 0,          -- Failed migrations
    skipped_count INTEGER DEFAULT 0,         -- Skipped (no versions, etc.)
    error_message TEXT,                      -- Error if status is 'failed'
    celery_task_id VARCHAR(255),             -- Celery task ID for monitoring
    result_json JSON,                        -- Detailed results and failed drawings
    status_json JSON,                        -- Current status metadata
    started_at DATETIME,                     -- When migration started
    completed_at DATETIME,                   -- When migration completed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
);
```

## API Documentation

### 1. Initiate Migration

**Endpoint:** `POST /storage/migrate`

**Authentication:** Required

**Request Body:**
```json
{
    "source_provider_id": 1,
    "target_provider_id": 2,
    "drawing_ids": [1, 2, 3]  // Optional, empty = migrate all
}
```

**Response (202 Accepted):**
```json
{
    "message": "Storage migration initiated",
    "migration_id": 42,
    "celery_task_id": "abc-123-def-456",
    "status": "queued",
    "drawing_count": 3,
    "source_provider_id": 1,
    "target_provider_id": 2
}
```

**Error Cases:**
- `400` - Missing required parameters or invalid drawing IDs
- `403` - Access denied to provider or drawing
- `404` - Provider not found
- `500` - Failed to queue migration task

### 2. Get Migration Status

**Endpoint:** `GET /storage/migrations/<migration_id>`

**Authentication:** Required

**Response (200 OK):**
```json
{
    "migration_id": 42,
    "status": "in_progress",
    "progress": 45,
    "source_provider_id": 1,
    "target_provider_id": 2,
    "statistics": {
        "total": 100,
        "migrated": 45,
        "failed": 2,
        "skipped": 0
    },
    "timestamps": {
        "created_at": "2025-12-16T10:00:00Z",
        "started_at": "2025-12-16T10:00:05Z",
        "completed_at": null
    },
    "celery_task_id": "abc-123-def-456",
    "status_metadata": {
        "migrated": 45,
        "failed": 2,
        "skipped": 0,
        "current_drawing": 98
    }
}
```

**Error Cases:**
- `403` - Access denied
- `404` - Migration job not found

### 3. Cancel Migration

**Endpoint:** `POST /storage/migrations/<migration_id>/cancel`

**Authentication:** Required

**Response (200 OK):**
```json
{
    "message": "Migration cancelled successfully",
    "migration_id": 42,
    "status": "cancelled"
}
```

**Error Cases:**
- `400` - Cannot cancel migration in current status
- `403` - Access denied
- `404` - Migration not found

### 4. Rollback Migration

**Endpoint:** `POST /storage/migrations/<migration_id>/rollback`

**Authentication:** Required

**Response (202 Accepted):**
```json
{
    "message": "Rollback initiated",
    "migration_id": 42,
    "status": "rollback_in_progress",
    "celery_task_id": "def-456-ghi-789"
}
```

**Error Cases:**
- `400` - Cannot rollback migration in current status
- `403` - Access denied
- `404` - Migration not found
- `500` - Failed to queue rollback task

### 5. List Migrations

**Endpoint:** `GET /storage/migrations?status=in_progress&limit=20&offset=0`

**Authentication:** Required

**Query Parameters:**
- `status` (optional) - Filter by status
- `limit` (optional, default: 20, max: 100)
- `offset` (optional, default: 0)

**Response (200 OK):**
```json
{
    "migrations": [
        {
            "migration_id": 42,
            "status": "completed",
            "progress": 100,
            "source_provider_id": 1,
            "target_provider_id": 2,
            "statistics": {
                "total": 100,
                "migrated": 100,
                "failed": 0,
                "skipped": 0
            },
            "created_at": "2025-12-16T10:00:00Z",
            "started_at": "2025-12-16T10:00:05Z",
            "completed_at": "2025-12-16T10:15:30Z"
        }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
}
```

## Migration Flow

### Successful Migration Flow

```
1. User initiates migration via POST /storage/migrate
   ├─ Validate provider access
   ├─ Validate drawing IDs if provided
   └─ Create migration_jobs record with status='pending'

2. Background task queued via Celery
   ├─ Update migration_jobs with status='queued'
   └─ Return 202 response with migration_id

3. Celery task executes
   ├─ Update status='in_progress'
   ├─ Iterate through drawing versions
   │  ├─ Download from source provider
   │  ├─ Upload to target provider
   │  └─ Update drawing_versions.storage_provider_id
   ├─ Update progress (0-100%)
   └─ Update status='completed'

4. User queries status via GET /storage/migrations/<migration_id>
   └─ Returns complete migration statistics
```

### Failed Migration with Rollback Flow

```
1. Migration fails during execution
   ├─ Backup data captured for rollback
   ├─ Update status='failed' or 'completed_with_errors'
   └─ Store error message in error_message field

2. User initiates rollback via POST /storage/migrations/<migration_id>/rollback
   ├─ Verify migration status is 'failed' or 'completed_with_errors'
   └─ Queue rollback_migration_task

3. Rollback task executes
   ├─ Restore original storage_provider_id for failed versions
   ├─ Update status='rolled_back'
   └─ Store rollback statistics in result_json

4. Database state restored to pre-migration
```

## Implementation Details

### Migration Algorithm

```python
def migrate_drawing(drawing_id, source_provider, target_provider):
    """
    For each drawing:
    1. Find all versions stored in source provider
    2. For each version:
       a. Generate storage key: drawings/{drawing_id}/v{version}.json
       b. Check if file exists in source
       c. Download from source
       d. Upload to target
       e. Update drawing_versions.storage_provider_id
       f. Store backup info for potential rollback
    3. Return migration status (success/failed)
    """
```

### Async Operations

All storage operations use asyncio for non-blocking I/O:

```python
async def download():
    return await source_provider.download(content_key)

async def upload():
    return await target_provider.upload(...)

# Execute in sync context
content_data = asyncio.run(download())
asyncio.run(upload())
```

### Error Handling

1. **Pre-migration validation:**
   - Provider existence and access
   - Drawing ownership/access
   - Provider type compatibility

2. **During migration:**
   - Per-drawing try-catch
   - Failed count tracking
   - Detailed error messages stored

3. **Automatic retry:**
   - Celery configured with auto-retry
   - Max 3 retries with exponential backoff
   - Task time limit: 1 hour

### Progress Tracking

Progress is updated in real-time via `status_json`:

```json
{
    "migrated": 45,
    "failed": 2,
    "skipped": 0,
    "current_drawing": 98
}
```

Calculated as: `progress = (processed_count / total_count) * 100`

## Security Considerations

1. **Authentication:** All endpoints require auth_required
2. **Authorization:**
   - Users can only migrate their own drawings
   - Users can only access migrations they created
   - Admins can perform all operations
3. **Data Safety:**
   - Migrations don't delete source files
   - Backup data retained for rollback
   - Original storage references preserved until confirmed

## Performance Optimization

1. **Async Processing:**
   - Non-blocking I/O via asyncio
   - Concurrent provider operations
   - Prevents blocking request threads

2. **Batch Operations:**
   - Process multiple drawings in single task
   - Single database update per migration job
   - Efficient storage provider API usage

3. **Database Queries:**
   - Indexed lookups by provider_id
   - Single query for all versions per drawing
   - Minimal transaction scope

## Testing

### Unit Tests

```python
def test_migrate_storage():
    """Test successful migration"""
    migration = create_migration_job(...)
    result = migrate_storage_task(...)
    assert result['migrated'] == expected_count

def test_migration_with_errors():
    """Test migration with some failures"""
    migration = create_migration_job(...)
    result = migrate_storage_task(...)
    assert result['failed'] > 0
    assert result['status'] == 'completed_with_errors'

def test_rollback():
    """Test rollback after failed migration"""
    migration = create_failed_migration(...)
    result = rollback_migration_task(migration.id)
    assert migration.status == 'rolled_back'
    # Verify storage references restored
```

### Integration Tests

```python
def test_full_migration_workflow():
    """Test complete migration workflow"""
    # 1. Create providers
    source = create_storage_provider('s3')
    target = create_storage_provider('gcs')

    # 2. Create drawings with versions
    drawings = create_test_drawings(count=10)

    # 3. Initiate migration
    response = client.post('/storage/migrate', json={
        'source_provider_id': source.id,
        'target_provider_id': target.id,
        'drawing_ids': [d.id for d in drawings]
    })
    assert response.status_code == 202

    # 4. Wait for migration to complete
    migration_id = response.json()['migration_id']
    wait_for_migration(migration_id)

    # 5. Verify all drawings migrated
    status = get_migration_status(migration_id)
    assert status['statistics']['migrated'] == 10
    assert status['progress'] == 100
```

## Monitoring and Logging

All migration operations are logged with:
- Migration ID
- User ID
- Provider IDs
- Status transitions
- Progress updates
- Error details

Example logs:

```
Starting migration task task-abc for migration_id 42 from provider 1 to 2
Migrating 100 drawings
Updated migration 42 status to in_progress (25%)
Migrated drawing 100 v1
Migration task task-abc completed: 98 migrated, 2 failed, 0 skipped
```

## Future Enhancements

1. **Scheduled Migrations:**
   - Queue migrations for off-peak hours
   - Recurring migrations for sync

2. **Provider-specific Optimizations:**
   - S3 multipart upload for large files
   - Batch operations where supported
   - Provider-specific retry logic

3. **Enhanced Monitoring:**
   - WebSocket status updates
   - Migration templates/presets
   - Performance statistics per provider

4. **Parallel Processing:**
   - Concurrent drawing migrations
   - Task priority queues
   - Resource throttling

## Configuration

### Environment Variables

```bash
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_TIME_LIMIT=3600  # 1 hour

# Storage Provider Configuration
STORAGE_PROVIDER=s3
STORAGE_ENDPOINT=s3.amazonaws.com
STORAGE_BUCKET=icecharts
STORAGE_REGION=us-east-1
```

### Application Configuration

```python
# config.py
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
CELERY_TASK_TIME_LIMIT = 3600  # 1 hour for migration tasks
```

## Troubleshooting

### Migration Stuck in "in_progress"

1. Check Celery worker status: `celery -A app.tasks inspect active`
2. Verify Redis connection: `redis-cli ping`
3. Check database for orphaned tasks
4. If needed, cancel migration and retry

### Failed Migrations

1. Check error_message field for details
2. Verify target provider credentials
3. Check disk space on target provider
4. Verify network connectivity between providers

### Rollback Issues

1. Verify backup_data exists in result_json
2. Check target provider still accessible
3. Ensure source provider references still valid
4. Review migration logs for more details

## References

- **Storage Providers:** `app/storage/base.py`
- **Drawing Service:** `app/services/drawing_storage_service.py`
- **Export Tasks Pattern:** `app/tasks/export_tasks.py`
- **API Structure:** `app/api/v1/`
