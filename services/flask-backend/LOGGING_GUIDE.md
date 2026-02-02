# Activity and Audit Logging System

## Overview

The IceCharts activity and audit logging system provides comprehensive tracking of user actions and administrative operations. This system helps with:

- Compliance and regulatory requirements
- Security monitoring and threat detection
- User behavior analysis
- Administrative change tracking
- Debugging and troubleshooting

## Architecture

### Database Tables

#### `activity_logs` Table
Tracks user activities and general system events.

**Fields:**
- `id` - Primary key
- `user_id` - Reference to the user performing the action
- `tenant_id` - Tenant identifier
- `action` - Action name (e.g., "login", "drawing_created", "comment_added")
- `resource_type` - Type of resource (e.g., "drawing", "comment", "user")
- `resource_id` - ID of the resource being acted upon
- `resource_name` - Human-readable name of the resource
- `details` - JSON field for additional context-specific data
- `ip_address` - IP address of the request
- `user_agent` - User agent string
- `timestamp` - When the action occurred (UTC)

**Example Activity Log Entry:**
```json
{
  "id": 1,
  "user_id": 5,
  "action": "drawing_created",
  "resource_type": "drawing",
  "resource_id": 42,
  "resource_name": "My Architecture Diagram",
  "details": {
    "title": "My Architecture Diagram",
    "description": "System design for microservices"
  },
  "ip_address": "192.168.1.100",
  "timestamp": "2025-12-16T10:30:00Z",
  "user": {
    "id": 5,
    "username": "john.doe",
    "email": "john@example.com",
    "full_name": "John Doe"
  }
}
```

#### `audit_logs` Table
Tracks administrative and sensitive operations with full change history.

**Fields:**
- `id` - Primary key
- `user_id` - Reference to the user making the change
- `tenant_id` - Tenant identifier
- `action` - Action name (e.g., "user_created", "user_updated", "user_deleted")
- `resource_type` - Type of resource (e.g., "user", "group", "settings", "system")
- `resource_id` - ID of the resource being modified
- `resource_name` - Human-readable name of the resource
- `changes` - JSON field with old_value and new_value for each changed field
- `reason` - Why the action was taken (optional)
- `ip_address` - IP address of the request
- `user_agent` - User agent string
- `status` - "success" or "failed"
- `error_message` - Error message if status is "failed"
- `timestamp` - When the action occurred (UTC)

**Example Audit Log Entry:**
```json
{
  "id": 1,
  "user_id": 1,
  "action": "user_created",
  "resource_type": "user",
  "resource_id": 10,
  "resource_name": "jane@example.com",
  "changes": {
    "email": {
      "old_value": null,
      "new_value": "jane@example.com"
    },
    "role": {
      "old_value": null,
      "new_value": "maintainer"
    },
    "full_name": {
      "old_value": null,
      "new_value": "Jane Smith"
    }
  },
  "status": "success",
  "timestamp": "2025-12-16T10:30:00Z",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator"
  }
}
```

## Logging Service

### `LoggingService` Class

Located in `app/services/logging_service.py`

#### Methods

##### `log_activity()`

Logs a user activity.

**Parameters:**
- `user_id` (int, required) - ID of the user performing the action
- `action` (str, required) - Action name
- `resource_type` (str, optional) - Type of resource
- `resource_id` (int, optional) - ID of the resource
- `resource_name` (str, optional) - Human-readable name
- `details` (dict, optional) - Additional context data
- `tenant_id` (int, optional, default=1) - Tenant ID

**Returns:** ID of the created log record, or None if creation failed

**Example:**
```python
from app.services.logging_service import LoggingService

LoggingService.log_activity(
    user_id=5,
    action="drawing_shared",
    resource_type="drawing",
    resource_id=42,
    resource_name="My Architecture",
    details={
        "shared_with": "jane@example.com",
        "permission": "viewer"
    }
)
```

##### `log_audit()`

Logs an administrative/sensitive action with change history.

**Parameters:**
- `action` (str, required) - Action name
- `resource_type` (str, required) - Type of resource
- `resource_id` (int, optional) - ID of the resource
- `resource_name` (str, optional) - Human-readable name
- `changes` (dict, optional) - Field changes with old/new values
- `reason` (str, optional) - Why the action was taken
- `user_id` (int, optional) - ID of the user making the change
- `tenant_id` (int, optional, default=1) - Tenant ID
- `status` (str, optional, default="success") - "success" or "failed"
- `error_message` (str, optional) - Error message if failed

**Returns:** ID of the created log record, or None if creation failed

**Example:**
```python
LoggingService.log_audit(
    action="user_role_changed",
    resource_type="user",
    resource_id=10,
    resource_name="jane@example.com",
    user_id=1,
    changes={
        "role": {
            "old_value": "viewer",
            "new_value": "maintainer"
        }
    },
    reason="Promotion to team lead"
)
```

##### `get_activity_logs()`

Retrieves activity logs with filtering and pagination.

**Parameters:**
- `user_id` (int, optional) - Filter by user ID
- `action` (str, optional) - Filter by action name
- `resource_type` (str, optional) - Filter by resource type
- `start_date` (datetime, optional) - Filter by start date
- `end_date` (datetime, optional) - Filter by end date
- `tenant_id` (int, optional, default=1) - Tenant ID
- `limit` (int, optional, default=100) - Max records to return
- `offset` (int, optional, default=0) - Records to skip

**Returns:** Tuple of (logs list, total count)

**Example:**
```python
from datetime import datetime, timezone, timedelta

start = datetime.now(timezone.utc) - timedelta(days=7)
logs, total = LoggingService.get_activity_logs(
    user_id=5,
    action="drawing_created",
    start_date=start,
    limit=50,
    offset=0
)
```

##### `get_audit_logs()`

Retrieves audit logs with filtering and pagination.

**Parameters:** Same as `get_activity_logs()`

**Returns:** Tuple of (logs list, total count)

### Decorators

#### `@log_activity_decorator()`

Automatically logs user activity when a function is executed.

**Parameters:**
- `action` (str, required) - Action name to log
- `resource_type` (str, optional) - Type of resource
- `include_args` (list, optional) - Argument names to include in details

**Example:**
```python
from app.services.logging_service import log_activity_decorator

@log_activity_decorator(
    "drawing_created",
    "drawing",
    include_args=["title", "description"]
)
def create_drawing(title, description):
    # Function implementation
    pass
```

#### `@log_audit_decorator()`

Automatically logs audit action when a function is executed.

**Parameters:**
- `action` (str, required) - Action name to log
- `resource_type` (str, required) - Type of resource
- `include_args` (list, optional) - Argument names to include in details

**Example:**
```python
from app.services.logging_service import log_audit_decorator

@log_audit_decorator(
    "user_created",
    "user",
    include_args=["email", "role"]
)
def create_user(email, role, password):
    # Function implementation
    pass
```

## API Endpoints

### GET `/admin/activity`

Retrieves recent system activity logs.

**Authentication:** Admin role required

**Query Parameters:**
- `page` (int, default=1) - Page number
- `per_page` (int, default=50, max=1000) - Records per page
- `user_id` (int) - Filter by user ID
- `action` (str) - Filter by action type
- `resource_type` (str) - Filter by resource type
- `start_date` (ISO 8601) - Filter by start date (e.g., "2025-12-16T00:00:00Z")
- `end_date` (ISO 8601) - Filter by end date

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/activity?page=1&per_page=50&user_id=5&action=drawing_created" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "activities": [
    {
      "id": 1,
      "user_id": 5,
      "action": "drawing_created",
      "resource_type": "drawing",
      "resource_id": 42,
      "resource_name": "My Diagram",
      "timestamp": "2025-12-16T10:30:00Z",
      "user": {
        "id": 5,
        "username": "john.doe",
        "email": "john@example.com"
      }
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 50,
  "pages": 1
}
```

### GET `/admin/audit-log`

Retrieves audit log entries.

**Authentication:** Admin role required

**Query Parameters:**
- `page` (int, default=1) - Page number
- `per_page` (int, default=50, max=1000) - Records per page
- `user_id` (int) - Filter by user ID
- `action` (str) - Filter by action type
- `resource_type` (str) - Filter by resource type
- `start_date` (ISO 8601) - Filter by start date
- `end_date` (ISO 8601) - Filter by end date

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/admin/audit-log?page=1&resource_type=user&action=user_created" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "audit_logs": [
    {
      "id": 1,
      "user_id": 1,
      "action": "user_created",
      "resource_type": "user",
      "resource_id": 10,
      "resource_name": "jane@example.com",
      "changes": {
        "email": {
          "old_value": null,
          "new_value": "jane@example.com"
        },
        "role": {
          "old_value": null,
          "new_value": "maintainer"
        }
      },
      "status": "success",
      "timestamp": "2025-12-16T10:30:00Z",
      "user": {
        "id": 1,
        "username": "admin"
      }
    }
  ],
  "total": 23,
  "page": 1,
  "per_page": 50,
  "pages": 1
}
```

## Common Action Types

### Activity Log Actions
- `login` - User login
- `logout` - User logout
- `drawing_created` - Drawing created
- `drawing_updated` - Drawing updated
- `drawing_deleted` - Drawing deleted
- `drawing_shared` - Drawing shared with user/group
- `drawing_unshared` - Sharing removed
- `comment_added` - Comment created
- `comment_updated` - Comment updated
- `comment_deleted` - Comment deleted
- `collection_created` - Collection created
- `collection_updated` - Collection updated
- `collection_deleted` - Collection deleted

### Audit Log Actions
- `user_created` - User account created
- `user_updated` - User details updated
- `user_deleted` - User account deleted
- `user_activated` - User account activated
- `user_deactivated` - User account deactivated
- `group_created` - Group created
- `group_updated` - Group updated
- `group_deleted` - Group deleted
- `settings_changed` - System settings changed
- `storage_configured` - Storage provider configured
- `storage_deleted` - Storage provider deleted
- `sso_configured` - SSO configuration changed

## Implementation Examples

### Logging a Custom Action

**In a service or endpoint:**
```python
from app.services.logging_service import LoggingService
from flask import g, request

def share_drawing(drawing_id, user_id):
    # Perform the sharing operation
    # ...

    # Log the activity
    current_user = g.current_user
    LoggingService.log_activity(
        user_id=current_user.get("id"),
        action="drawing_shared",
        resource_type="drawing",
        resource_id=drawing_id,
        details={
            "shared_with_user_id": user_id,
            "permission": "viewer"
        }
    )
```

### Logging with Decorator

**Using the decorator approach:**
```python
from app.services.logging_service import log_activity_decorator

@log_activity_decorator(
    "drawing_created",
    "drawing",
    include_args=["title"]
)
def create_drawing(title, description):
    # Implementation
    return {"id": 1, "title": title}
```

### Querying Logs

**Get all user activities for the past 7 days:**
```python
from datetime import datetime, timezone, timedelta
from app.services.logging_service import LoggingService

start = datetime.now(timezone.utc) - timedelta(days=7)
logs, total = LoggingService.get_activity_logs(
    user_id=5,
    start_date=start
)

print(f"Found {total} activities")
for log in logs:
    print(f"{log['action']} on {log['resource_name']}")
```

## Data Retention

Activity logs should be retained according to your compliance requirements. Configure retention policies:

- Store in `tenants` table: `data_retention_days` field
- Default retention: 90 days
- Enterprise customers may have longer retention

## Security Considerations

1. **Access Control**: Only admin users can access `/admin/activity` and `/admin/audit-log` endpoints
2. **Sensitive Data**: Passwords and secrets are masked in audit logs (shown as `***`)
3. **IP Tracking**: IP addresses are logged for all activities
4. **Immutability**: Logs should never be modified after creation; implement read-only database access if possible
5. **Encryption**: Consider encrypting sensitive log data at rest
6. **Archival**: Archive old logs to cold storage for long-term retention

## Performance Optimization

For large deployments:

1. **Indexing**: Database indexes are created on:
   - `user_id`
   - `action`
   - `resource_type`
   - `timestamp`
   - `tenant_id`

2. **Partitioning**: Consider partitioning by date or tenant ID

3. **Archival**: Move logs older than retention period to archive tables

4. **Pagination**: Always use pagination when querying logs

## Troubleshooting

### Logs Not Being Recorded

1. Check that the database tables exist: `activity_logs` and `audit_logs`
2. Verify that `LoggingService.log_activity()` is being called
3. Check application logs for any errors in the logging service
4. Ensure user is authenticated (has valid ID)

### Slow Log Queries

1. Check database indexes are created
2. Reduce date range in queries
3. Use pagination with reasonable limits
4. Consider archiving old logs
5. Monitor database query performance

### Missing Fields in Logs

1. Ensure all required parameters are provided to `log_activity()` or `log_audit()`
2. Check that `tenant_id` is set correctly
3. Verify IP address and user agent are being captured from request context

## Database Migrations

Tables were created with PyDAL migration enabled. To verify tables exist:

```bash
# Check database for tables
psql -d icecharts -c "\dt activity_logs"
psql -d icecharts -c "\dt audit_logs"
```

## Future Enhancements

Potential improvements for the logging system:

1. Real-time log streaming to external logging service (ELK, Splunk, etc.)
2. Log aggregation and analytics dashboards
3. Automated alerting on suspicious activities
4. Advanced filtering and search capabilities
5. Log retention policy enforcement
6. Compression of old logs
7. Integration with SIEM systems
