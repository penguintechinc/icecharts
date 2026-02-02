# Activity and Audit Logging - Quick Start Guide

## Quick Overview

The activity and audit logging system tracks user actions and administrative operations in IceCharts.

## 5-Minute Setup

### 1. Database Tables (Already Created)
Two new tables in the database:
- `activity_logs` - User activities (logins, drawing edits, etc.)
- `audit_logs` - Admin actions (user creation, settings changes, etc.)

### 2. API Endpoints (Ready to Use)
```
GET /api/v1/admin/activity      - View user activities
GET /api/v1/admin/audit-log     - View admin actions
```

Both require admin role.

## Common Tasks

### Log a User Activity
```python
from app.services.logging_service import LoggingService
from flask import g

LoggingService.log_activity(
    user_id=g.current_user['id'],
    action="drawing_created",
    resource_type="drawing",
    resource_id=42,
    resource_name="My Diagram"
)
```

### Log an Admin Action
```python
LoggingService.log_audit(
    action="user_created",
    resource_type="user",
    resource_id=10,
    resource_name="jane@example.com",
    user_id=g.current_user['id'],
    changes={
        "email": {"old_value": None, "new_value": "jane@example.com"}
    }
)
```

### Get Activity Logs
```python
logs, total = LoggingService.get_activity_logs(
    user_id=5,              # Optional: filter by user
    action="drawing_created",  # Optional: filter by action
    limit=50,               # Records to return
    offset=0                # Pagination
)
```

### Get Audit Logs
```python
logs, total = LoggingService.get_audit_logs(
    resource_type="user",   # Optional: filter by resource type
    limit=50
)
```

## API Examples

### Get All Activity Logs
```bash
curl -X GET "http://localhost:5000/api/v1/admin/activity" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter Activity by User
```bash
curl -X GET "http://localhost:5000/api/v1/admin/activity?user_id=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by Date Range
```bash
curl -X GET "http://localhost:5000/api/v1/admin/activity?start_date=2025-12-16T00:00:00Z&end_date=2025-12-17T00:00:00Z" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by Action Type
```bash
curl -X GET "http://localhost:5000/api/v1/admin/activity?action=drawing_created" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Audit Logs with Pagination
```bash
curl -X GET "http://localhost:5000/api/v1/admin/audit-log?page=1&per_page=25" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Using Decorators (Automatic Logging)

### Automatic Activity Logging
```python
from app.services.logging_service import log_activity_decorator

@log_activity_decorator("drawing_created", "drawing")
def create_drawing(title, description):
    # Your code here
    return drawing_obj
```

### Automatic Audit Logging
```python
from app.services.logging_service import log_audit_decorator

@log_audit_decorator("user_created", "user")
def create_user(email, role):
    # Your code here
    return user_obj
```

## Standard Actions

### Activity Log Actions
- `login` - User login
- `drawing_created` - Drawing created
- `drawing_updated` - Drawing updated
- `drawing_deleted` - Drawing deleted
- `drawing_shared` - Drawing shared
- `comment_added` - Comment created
- `collection_created` - Collection created

### Audit Log Actions
- `user_created` - User account created
- `user_updated` - User details updated
- `user_deleted` - User account deleted
- `user_activated` - User activated
- `user_deactivated` - User deactivated
- `group_created` - Group created
- `storage_configured` - Storage configured

## Real-World Examples

### Log Drawing Creation
```python
LoggingService.log_activity(
    user_id=current_user['id'],
    action="drawing_created",
    resource_type="drawing",
    resource_id=drawing['id'],
    resource_name=drawing['title'],
    details={
        "status": "draft",
        "is_template": False
    }
)
```

### Log Permission Change
```python
LoggingService.log_audit(
    action="user_role_changed",
    resource_type="user",
    resource_id=user_id,
    resource_name=user['email'],
    user_id=admin_id,
    changes={
        "role": {
            "old_value": "viewer",
            "new_value": "maintainer"
        }
    }
)
```

### Query User's Last Week Activity
```python
from datetime import datetime, timezone, timedelta

start = datetime.now(timezone.utc) - timedelta(days=7)
logs, total = LoggingService.get_activity_logs(
    user_id=5,
    start_date=start,
    limit=100
)
print(f"User had {total} activities in the last 7 days")
```

## Response Examples

### Activity Log Entry
```json
{
  "id": 1,
  "user_id": 5,
  "action": "drawing_created",
  "resource_type": "drawing",
  "resource_id": 42,
  "resource_name": "My Diagram",
  "details": {"status": "draft"},
  "ip_address": "192.168.1.100",
  "timestamp": "2025-12-16T10:30:00Z",
  "user": {
    "id": 5,
    "username": "john.doe",
    "email": "john@example.com"
  }
}
```

### Audit Log Entry
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
    }
  },
  "status": "success",
  "timestamp": "2025-12-16T10:30:00Z",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

## Query Parameters Cheat Sheet

| Parameter | Type | Example | Purpose |
|-----------|------|---------|---------|
| page | int | 1 | Page number for pagination |
| per_page | int | 50 | Records per page (max 1000) |
| user_id | int | 5 | Filter by user ID |
| action | string | drawing_created | Filter by action name |
| resource_type | string | drawing | Filter by resource type |
| start_date | ISO 8601 | 2025-12-16T00:00:00Z | Filter from this date |
| end_date | ISO 8601 | 2025-12-17T00:00:00Z | Filter until this date |

## Common Filters

### Get all drawing creation activities
```
/admin/activity?action=drawing_created&resource_type=drawing
```

### Get specific user's recent actions
```
/admin/activity?user_id=5&per_page=20
```

### Get all admin actions in past week
```
/admin/audit-log?start_date=2025-12-09T00:00:00Z
```

### Get all user management audits
```
/admin/audit-log?resource_type=user
```

## Field Reference

### Activity Logs
- `id` - Unique identifier
- `user_id` - User who performed action
- `action` - Action name
- `resource_type` - Type of resource (drawing, comment, etc.)
- `resource_id` - ID of resource
- `resource_name` - Human-readable name
- `details` - Additional context (JSON)
- `ip_address` - Source IP
- `timestamp` - When it happened

### Audit Logs
- `id` - Unique identifier
- `user_id` - Admin who made change
- `action` - Action name
- `resource_type` - Type of resource
- `resource_id` - ID of resource
- `resource_name` - Human-readable name
- `changes` - Before/after values (JSON)
- `reason` - Why it was done
- `status` - success or failed
- `error_message` - Error details if failed
- `ip_address` - Source IP
- `timestamp` - When it happened

## Troubleshooting

### Logs not showing up?
1. Verify you're using admin account
2. Check database has the tables: `activity_logs` and `audit_logs`
3. Ensure `LoggingService.log_activity()` is being called
4. Check for errors in application logs

### Queries returning no results?
1. Verify date range is correct
2. Check that user_id exists
3. Try removing filters to see all logs
4. Check pagination (page=1)

### Getting "Insufficient permissions"?
- Only admin users can access `/admin/activity` and `/admin/audit-log`
- Check your token is valid
- Verify your user has admin role

## Next Steps

1. **Read LOGGING_GUIDE.md** - Complete documentation
2. **Read LOGGING_INTEGRATION_EXAMPLES.md** - Real-world examples
3. **Add logging to endpoints** - Start logging important actions
4. **Monitor logs** - Use admin panel to view activities
5. **Set up automation** - Create dashboards or alerts

## Support

For more details:
- See `LOGGING_GUIDE.md` for comprehensive reference
- See `LOGGING_INTEGRATION_EXAMPLES.md` for implementation patterns
- See `app/services/logging_service.py` for API details
- See `app/api/v1/admin.py` for endpoint code
