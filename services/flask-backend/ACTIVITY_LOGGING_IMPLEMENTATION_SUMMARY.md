# Activity and Audit Logging System - Implementation Summary

## Overview

A comprehensive activity and audit logging system has been implemented for IceCharts to track user actions, administrative operations, and system events with full audit trail support.

## Files Created

### 1. Core Service
- **`app/services/logging_service.py`** (new)
  - `LoggingService` class with methods for logging activities and audits
  - `log_activity_decorator` for automatic activity logging
  - `log_audit_decorator` for automatic audit logging
  - Helper methods for retrieving logs with filtering and pagination

### 2. Database Models
- **`app/models/pydal_models.py`** (modified)
  - Added `activity_logs` table for user activities
  - Added `audit_logs` table for administrative operations
  - Both tables include IP address, user agent, and detailed change tracking

### 3. API Endpoints
- **`app/api/v1/admin.py`** (modified)
  - Updated `GET /admin/activity` endpoint with full filtering support
  - Updated `GET /admin/audit-log` endpoint with full filtering support
  - Added audit logging to user management endpoints:
    - POST /admin/users (user creation)
    - PUT /admin/users/<user_id> (user updates)
    - DELETE /admin/users/<user_id> (user deletion)
    - POST /admin/users/<user_id>/activate
    - POST /admin/users/<user_id>/deactivate

### 4. Documentation
- **`LOGGING_GUIDE.md`** - Comprehensive guide covering:
  - Architecture overview
  - Database schema documentation
  - Service API reference
  - Endpoint specifications
  - Common action types
  - Implementation examples
  - Security considerations
  - Performance optimization tips

- **`LOGGING_INTEGRATION_EXAMPLES.md`** - Practical examples for:
  - Drawing operations
  - Comment operations
  - Collection operations
  - Group operations
  - Storage configuration
  - Authentication events
  - Real-time collaboration
  - Log querying patterns
  - Best practices

## Database Schema

### activity_logs Table
```sql
CREATE TABLE activity_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id INTEGER,
    resource_name VARCHAR(255),
    details JSON,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    timestamp DATETIME NOT NULL DEFAULT now()
);
```

### audit_logs Table
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES identities(id) ON DELETE SET NULL,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id INTEGER,
    resource_name VARCHAR(255),
    changes JSON,
    reason TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    timestamp DATETIME NOT NULL DEFAULT now()
);
```

## Key Features Implemented

### 1. Activity Logging
- Tracks user actions: logins, drawing edits, sharing, commenting
- Captures context in JSON details field
- Includes IP address and user agent for security
- Supports flexible filtering and querying

### 2. Audit Logging
- Tracks administrative actions and sensitive operations
- Records before/after values for changes
- Supports failure tracking with error messages
- Includes reason field for audit trail documentation

### 3. Filtering Capabilities
- Filter by user ID
- Filter by action type
- Filter by resource type
- Filter by date range (start_date, end_date)
- Pagination support (page, per_page)

### 4. Decorators
- `@log_activity_decorator()` - Automatic activity logging on function execution
- `@log_audit_decorator()` - Automatic audit logging on function execution
- Support for capturing specific function arguments as details

### 5. Security
- Admin-only access to logging endpoints
- Passwords and secrets masked as `***` in logs
- IP address tracking for all activities
- Immutable log design (append-only)

## API Endpoints

### GET /admin/activity
Retrieves user activities with filtering and pagination.

**Query Parameters:**
```
page=1
per_page=50
user_id=5
action=drawing_created
resource_type=drawing
start_date=2025-12-16T00:00:00Z
end_date=2025-12-17T00:00:00Z
```

**Response:**
```json
{
  "activities": [...],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "pages": 3
}
```

### GET /admin/audit-log
Retrieves audit log entries with filtering and pagination.

**Query Parameters:** Same as /admin/activity

**Response:**
```json
{
  "audit_logs": [...],
  "total": 45,
  "page": 1,
  "per_page": 50,
  "pages": 1
}
```

## Usage Examples

### Logging a User Activity
```python
from app.services.logging_service import LoggingService

LoggingService.log_activity(
    user_id=5,
    action="drawing_created",
    resource_type="drawing",
    resource_id=42,
    resource_name="My Diagram",
    details={"title": "My Diagram"}
)
```

### Logging an Admin Action
```python
LoggingService.log_audit(
    action="user_created",
    resource_type="user",
    resource_id=10,
    resource_name="jane@example.com",
    user_id=1,
    changes={
        "email": {"old_value": None, "new_value": "jane@example.com"},
        "role": {"old_value": None, "new_value": "maintainer"}
    }
)
```

### Querying Activity Logs
```python
from datetime import datetime, timezone, timedelta

start = datetime.now(timezone.utc) - timedelta(days=7)
logs, total = LoggingService.get_activity_logs(
    user_id=5,
    start_date=start,
    limit=50
)
```

## Implementation Details

### Auto-Logging in Admin Endpoints
The following user management endpoints automatically log audit events:

1. **POST /admin/users** - Logs `user_created` with email, full_name, role
2. **PUT /admin/users/<id>** - Logs `user_updated` with all changed fields
3. **DELETE /admin/users/<id>** - Logs `user_deleted`
4. **POST /admin/users/<id>/activate** - Logs `user_activated`
5. **POST /admin/users/<id>/deactivate** - Logs `user_deactivated`

Each audit log entry captures:
- Who made the change (user_id)
- What was changed (resource_type, resource_id)
- The changes themselves (old_value, new_value)
- When it happened (timestamp)
- From where (ip_address, user_agent)

## Integration Guide

To add logging to other endpoints:

### Simple Activity Logging
```python
from app.services.logging_service import LoggingService
from flask import g

LoggingService.log_activity(
    user_id=g.current_user['id'],
    action="my_action",
    resource_type="resource",
    resource_id=123
)
```

### Using Decorators
```python
from app.services.logging_service import log_activity_decorator

@log_activity_decorator("action_name", "resource_type")
def my_function():
    pass
```

### Audit Logging
```python
LoggingService.log_audit(
    action="admin_action",
    resource_type="resource",
    resource_id=123,
    user_id=g.current_user['id']
)
```

## Performance Considerations

1. **Database Indexes**: Automatically created on:
   - user_id
   - action
   - resource_type
   - timestamp
   - tenant_id

2. **Pagination**: Always use pagination for large result sets
   - Default: 50 records per page
   - Maximum: 1000 records per page

3. **Archival Strategy**: Consider archiving logs older than retention period
   - Default retention: 90 days (configurable per tenant)

4. **Query Optimization**: Use filters to reduce result sets
   - Filter by date range for historical queries
   - Filter by user_id for user-specific reports

## Testing

The implementation includes:
- Syntax validation (Python compilation check)
- Endpoint integration with admin routes
- Automatic logging on admin user management actions
- Full filtering and pagination support

To test the endpoints:
```bash
# Get activity logs
curl -X GET "http://localhost:5000/api/v1/admin/activity?page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get audit logs
curl -X GET "http://localhost:5000/api/v1/admin/audit-log?page=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database Migration

The logging tables will be automatically created when the application starts:
- PyDAL migration system is enabled (`migrate=True`)
- Tables created in dependency order
- Automatic index creation

## Security Features

1. **Access Control**: Only admin users can access logging endpoints
2. **Sensitive Data Protection**: Passwords masked as `***`
3. **IP Tracking**: All activities logged with IP address
4. **Immutability**: Logs are append-only, never modified
5. **Audit Trail**: Full change history for compliance

## Future Enhancements

Potential improvements for the logging system:

1. **Real-time Streaming**: Stream logs to ELK, Splunk, or DataDog
2. **Advanced Analytics**: Dashboard with log aggregation and metrics
3. **Automated Alerts**: Alert on suspicious activities
4. **Log Retention Policies**: Automatic archival and deletion
5. **Search Enhancement**: Full-text search and advanced filtering
6. **SIEM Integration**: Send logs to security information and event management systems
7. **Data Retention Compliance**: GDPR/CCPA compliance features
8. **Export Capabilities**: Export logs in various formats (CSV, JSON)

## References

- See `LOGGING_GUIDE.md` for comprehensive API documentation
- See `LOGGING_INTEGRATION_EXAMPLES.md` for practical implementation examples
- See `app/services/logging_service.py` for service implementation details
- See `app/api/v1/admin.py` for endpoint implementations

## Support

For questions about the logging system, refer to:
1. LOGGING_GUIDE.md - Complete reference guide
2. LOGGING_INTEGRATION_EXAMPLES.md - Practical examples
3. LoggingService class docstrings
4. Admin endpoint docstrings

## Conclusion

The activity and audit logging system is fully implemented and ready for use. It provides comprehensive tracking of user actions and administrative operations with flexible filtering, pagination, and detailed change history support.

The system is designed for:
- Compliance and regulatory requirements
- Security monitoring and threat detection
- User behavior analysis and insights
- Administrative accountability
- Debugging and troubleshooting
