# Logging Integration Examples

This document shows practical examples of how to integrate the activity and audit logging system into various parts of the IceCharts application.

## Table of Contents

1. [Drawing Operations](#drawing-operations)
2. [Comment Operations](#comment-operations)
3. [Collection Operations](#collection-operations)
4. [Group Operations](#group-operations)
5. [Storage Configuration](#storage-configuration)
6. [Authentication Events](#authentication-events)
7. [Real-time Collaboration](#real-time-collaboration)

## Drawing Operations

### Logging Drawing Creation

**File:** `app/api/v1/drawings.py`

```python
from app.services.logging_service import LoggingService
from flask import g

@bp.route('', methods=['POST'])
@auth_required
def create_drawing():
    """Create a new drawing."""
    data = request.get_json()

    # Validate and create drawing
    drawing = drawing_service.create_drawing(
        title=data.get('title'),
        description=data.get('description'),
        created_by_id=g.current_user['id']
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=g.current_user['id'],
        action='drawing_created',
        resource_type='drawing',
        resource_id=drawing['id'],
        resource_name=drawing['title'],
        details={
            'is_template': drawing.get('is_template', False),
            'status': drawing.get('status', 'draft')
        }
    )

    return jsonify(drawing), 201
```

### Logging Drawing Updates

```python
@bp.route('<int:drawing_id>', methods=['PUT'])
@auth_required
def update_drawing(drawing_id):
    """Update a drawing."""
    current_user = g.current_user
    data = request.get_json()

    # Get original drawing for change tracking
    original = drawing_service.get_drawing(drawing_id)

    # Update drawing
    updated = drawing_service.update_drawing(
        drawing_id=drawing_id,
        **data
    )

    # Build change history
    changes = {}
    for key in ['title', 'description', 'status', 'is_public']:
        if key in data and data[key] != original.get(key):
            changes[key] = {
                'old_value': original.get(key),
                'new_value': data[key]
            }

    # Log the activity
    if changes:
        LoggingService.log_activity(
            user_id=current_user['id'],
            action='drawing_updated',
            resource_type='drawing',
            resource_id=drawing_id,
            resource_name=original['title'],
            details=changes
        )

    return jsonify(updated), 200
```

### Logging Drawing Deletion

```python
@bp.route('<int:drawing_id>', methods=['DELETE'])
@auth_required
def delete_drawing(drawing_id):
    """Delete a drawing."""
    current_user = g.current_user
    drawing = drawing_service.get_drawing(drawing_id)

    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404

    # Delete the drawing
    drawing_service.delete_drawing(drawing_id)

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='drawing_deleted',
        resource_type='drawing',
        resource_id=drawing_id,
        resource_name=drawing['title']
    )

    return jsonify({'message': 'Drawing deleted'}), 200
```

## Comment Operations

### Logging Comment Creation

**File:** `app/api/v1/comments.py`

```python
from app.services.logging_service import LoggingService

@bp.route('/drawings/<int:drawing_id>/comments', methods=['POST'])
@auth_required
def create_comment(drawing_id):
    """Create a comment on a drawing."""
    current_user = g.current_user
    data = request.get_json()

    comment = comment_service.create_comment(
        drawing_id=drawing_id,
        author_id=current_user['id'],
        content=data.get('comment_text'),
        shape_id=data.get('shape_id')
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='comment_added',
        resource_type='comment',
        resource_id=comment['id'],
        resource_name=f"Comment on drawing {drawing_id}",
        details={
            'drawing_id': drawing_id,
            'shape_id': data.get('shape_id'),
            'preview': data.get('comment_text')[:100]  # First 100 chars
        }
    )

    return jsonify(comment), 201
```

### Logging Comment Resolution

```python
@bp.route('/comments/<int:comment_id>/resolve', methods=['POST'])
@auth_required
def resolve_comment(comment_id):
    """Mark a comment as resolved."""
    current_user = g.current_user
    comment = comment_service.get_comment(comment_id)

    # Resolve the comment
    updated = comment_service.resolve_comment(
        comment_id=comment_id,
        resolved_by=current_user['id']
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='comment_resolved',
        resource_type='comment',
        resource_id=comment_id,
        details={
            'drawing_id': comment['drawing_id'],
            'resolved': True
        }
    )

    return jsonify(updated), 200
```

## Collection Operations

### Logging Collection Creation

**File:** `app/api/v1/collections.py`

```python
from app.services.logging_service import LoggingService

@bp.route('', methods=['POST'])
@auth_required
def create_collection():
    """Create a new collection."""
    current_user = g.current_user
    data = request.get_json()

    collection = collection_service.create_collection(
        name=data.get('name'),
        description=data.get('description'),
        owner_id=current_user['id'],
        is_public=data.get('is_public', False)
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='collection_created',
        resource_type='collection',
        resource_id=collection['id'],
        resource_name=collection['name'],
        details={
            'is_public': collection['is_public'],
            'share_mode': collection.get('share_mode', 'private')
        }
    )

    return jsonify(collection), 201
```

## Group Operations

### Logging Group Creation (Audit)

**File:** `app/api/v1/groups.py`

```python
from app.services.logging_service import LoggingService

@bp.route('', methods=['POST'])
@auth_required
@admin_required
def create_group():
    """Create a new group (admin only)."""
    current_user = g.current_user
    data = request.get_json()

    group = group_service.create_group(
        name=data.get('name'),
        description=data.get('description'),
        owner_id=current_user['id']
    )

    # Log as audit action
    LoggingService.log_audit(
        action='group_created',
        resource_type='group',
        resource_id=group['id'],
        resource_name=group['name'],
        user_id=current_user['id'],
        changes={
            'name': {'old_value': None, 'new_value': group['name']},
            'description': {'old_value': None, 'new_value': data.get('description')}
        }
    )

    return jsonify(group), 201
```

### Logging Group Membership Changes

```python
@bp.route('<int:group_id>/members/<int:user_id>', methods=['POST'])
@auth_required
@admin_required
def add_group_member(group_id, user_id):
    """Add a member to a group."""
    current_user = g.current_user

    membership = group_service.add_member(
        group_id=group_id,
        user_id=user_id
    )

    # Log as audit action
    LoggingService.log_audit(
        action='group_member_added',
        resource_type='group',
        resource_id=group_id,
        user_id=current_user['id'],
        changes={
            'member_added': {
                'old_value': None,
                'new_value': user_id
            }
        }
    )

    return jsonify(membership), 201
```

## Storage Configuration

### Logging Storage Configuration Changes

**File:** `app/api/v1/admin.py` (already implemented)

**Example of what's being logged:**

```python
from app.services.logging_service import LoggingService

@admin_v1_bp.route('/storage', methods=['POST'])
@auth_required
@admin_required
def admin_create_storage_config():
    """Create storage configuration (admin only)."""
    current_user = get_current_user()
    data = request.get_json()

    # Create storage config...
    config_id = db.storage_providers.insert(...)

    # Log as audit action
    LoggingService.log_audit(
        action='storage_configured',
        resource_type='storage',
        resource_id=config_id,
        resource_name=data.get('name'),
        user_id=current_user.get('id'),
        changes={
            'provider': {'old_value': None, 'new_value': data.get('provider')},
            'name': {'old_value': None, 'new_value': data.get('name')}
        }
    )

    return jsonify({...}), 201
```

## Authentication Events

### Logging Successful Logins

**File:** `app/api/v1/auth.py`

```python
from app.services.logging_service import LoggingService

@bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Authenticate user
    user = authenticate_user(email, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generate token
    token = create_access_token(user)

    # Log the activity
    LoggingService.log_activity(
        user_id=user['id'],
        action='login',
        resource_type='auth',
        details={
            'login_type': 'password',
            'email': email
        }
    )

    return jsonify({'token': token}), 200
```

### Logging Failed Login Attempts

```python
@bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Authenticate user
    user = authenticate_user(email, password)
    if not user:
        # Log failed attempt (no user_id available, use email as identifier)
        LoggingService.log_activity(
            user_id=1,  # Or use a system user ID
            action='login_failed',
            resource_type='auth',
            details={
                'email': email,
                'reason': 'invalid_credentials'
            }
        )
        return jsonify({'error': 'Invalid credentials'}), 401

    # ... rest of login logic
```

## Real-time Collaboration

### Logging Collaboration Session Events

**File:** `app/api/v1/collaboration_socket.py` or `app/websocket/collaboration.py`

```python
from app.services.logging_service import LoggingService

def handle_collaboration_join(data):
    """Handle user joining a collaboration session."""
    drawing_id = data.get('drawing_id')
    current_user = g.current_user

    # Create collaboration session
    session = collaboration_service.create_session(
        drawing_id=drawing_id,
        user_id=current_user['id']
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='collaboration_joined',
        resource_type='drawing',
        resource_id=drawing_id,
        details={
            'session_id': session['session_id'],
            'permission': session['permission']
        }
    )

def handle_collaboration_leave(data):
    """Handle user leaving a collaboration session."""
    drawing_id = data.get('drawing_id')
    current_user = g.current_user

    # Update collaboration session
    collaboration_service.end_session(
        drawing_id=drawing_id,
        user_id=current_user['id']
    )

    # Log the activity
    LoggingService.log_activity(
        user_id=current_user['id'],
        action='collaboration_left',
        resource_type='drawing',
        resource_id=drawing_id
    )
```

## Querying Logs

### Get All Activities for a Specific User (Last 30 Days)

```python
from datetime import datetime, timezone, timedelta
from app.services.logging_service import LoggingService

def get_user_activity_report(user_id):
    """Get activity report for a user."""
    start_date = datetime.now(timezone.utc) - timedelta(days=30)

    logs, total = LoggingService.get_activity_logs(
        user_id=user_id,
        start_date=start_date,
        limit=1000
    )

    # Group by action type
    by_action = {}
    for log in logs:
        action = log['action']
        by_action[action] = by_action.get(action, 0) + 1

    return {
        'user_id': user_id,
        'total_activities': total,
        'by_action': by_action,
        'date_range': '30 days'
    }
```

### Get Recent Admin Actions

```python
def get_recent_admin_actions(hours=24):
    """Get recent admin actions."""
    start_date = datetime.now(timezone.utc) - timedelta(hours=hours)

    logs, total = LoggingService.get_audit_logs(
        start_date=start_date,
        limit=100
    )

    return {
        'total': total,
        'logs': logs,
        'time_period': f'{hours} hours'
    }
```

### Get All Changes to a Specific User

```python
def get_user_modification_history(user_id):
    """Get audit history of changes to a user."""
    logs, total = LoggingService.get_audit_logs(
        resource_type='user',
        resource_id=user_id,
        limit=100
    )

    changes_timeline = []
    for log in logs:
        changes_timeline.append({
            'timestamp': log['timestamp'],
            'action': log['action'],
            'modified_by': log['user']['full_name'] if log.get('user') else 'System',
            'changes': log.get('changes')
        })

    return {
        'user_id': user_id,
        'modification_count': total,
        'timeline': changes_timeline
    }
```

## Best Practices

1. **Always include resource identifiers** - Use `resource_id` and `resource_name` to make logs searchable and human-readable

2. **Capture meaningful details** - Include context that helps understand why an action was taken

3. **Use consistent action names** - Follow the naming conventions (e.g., `drawing_created`, `user_updated`)

4. **Mask sensitive data** - Never log passwords, API keys, or tokens

5. **Log both success and failure** - Track failed operations with `status='failed'` and `error_message`

6. **Use audit logs for security-sensitive operations** - Admin actions, permission changes, user creation/deletion

7. **Use activity logs for user behavior** - Regular user actions, editing, sharing, commenting

8. **Include IP addresses and user agents** - Already automatic in the LoggingService

9. **Test log retrieval** - Verify filters work correctly before relying on them

10. **Consider performance** - Use pagination for large result sets
