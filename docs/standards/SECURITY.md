<<<<<<< HEAD
# Security Standards - Keeping Your App Safe

Part of [Development Standards](../STANDARDS.md)

Security isn't about being paranoid—it's about making smart choices so your users can trust you. This guide walks through common threats and how we defend against them.

## Common Vulnerabilities (The Cautionary Tales)

### The SQL Injection Attack
**The danger:** A bad actor sneaks SQL code into a form field, tricking your database into doing things you never intended.

**Example of bad code:**
```python
# DON'T DO THIS!
query = f"SELECT * FROM users WHERE username = '{user_input}'"
```

Someone types: `' OR '1'='1` → Suddenly they can see all users!

**How we protect:** Use parameterized queries with PyDAL (never concatenate user input):
```python
# DO THIS!
users = db((db.users.username == user_input)).select()
```

PyDAL automatically sanitizes inputs. Safe and simple.

### Cross-Site Scripting (XSS) - The Script Injection
**The danger:** Attackers inject JavaScript that runs in other users' browsers.

**Bad code:**
```python
# DON'T DO THIS!
return f"<div>{user_comment}</div>"  # User could add: <script>steal_cookies()</script>
```

**How we protect:**
- Always escape user content before displaying: `{{ user_comment | escape }}`
- Use modern frameworks (React) that escape by default
- Never use `dangerouslySetInnerHTML` unless you really know what you're doing

### CSRF (Cross-Site Request Forgery) - The Invisible Button Click
**The danger:** A malicious site tricks your user into performing actions on your app without realizing it.

**How we protect:** Flask handles this with CSRF tokens automatically. Every form submission validates that the request actually came from your app, not some attacker's website.

## Secrets Management - Where Passwords Live

Never hardcode secrets. Never. Ever.

**Safe approach:**
```python
import os

# Read from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

# Development: Use .env file (add to .gitignore!)
# Production: Set via container environment or secrets manager
```

**Files to keep OUT of git:**
- `.env` - Local development secrets
- `.env.local` - Any user-specific overrides
- `credentials.json` - Service account keys
- `*.key` - Private keys

These belong in `.gitignore` and should be managed by your CI/CD system or secrets vault.

## Authentication & Authorization

### Three-Tier Role System

**Global Level** (organization-wide):
- **Admin**: Full access everywhere, manage users
- **Maintainer**: Read/write on resources, no user management
- **Viewer**: Read-only access

**Container/Team Level** (per service):
- **Team Admin**: Full access within this team
- **Team Maintainer**: Read/write for this team
- **Team Viewer**: Read-only for this team

**Resource Level** (specific items):
- **Owner**: Full control
- **Editor**: Can read and modify
- **Viewer**: Can only read

### OAuth2-Style Scopes (Granular Permissions)

Think of scopes like keys to different rooms in your building:

```python
# Available scopes
SCOPES = {
    'users:read': 'View user list',
    'users:write': 'Create/update users',
    'users:admin': 'Delete users, change roles',
    'reports:read': 'View reports',
    'reports:write': 'Create/edit reports',
}

# Admin has all keys, Viewer only has read keys
ROLE_SCOPES = {
    'admin': ['users:read', 'users:write', 'users:admin', 'reports:read', 'reports:write'],
    'viewer': ['users:read', 'reports:read'],
}
```

**Implementation:**
```python
from functools import wraps
from flask import request

def require_scope(*required_scopes):
    """Only allow users with specific scopes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = request.user  # Set by auth middleware
            user_scopes = user.get_scopes()

            if not any(scope in user_scopes for scope in required_scopes):
                return {'error': 'Insufficient permissions'}, 403
=======
# Security Standards

Part of [Development Standards](../STANDARDS.md)

## Input Validation

- ALL inputs MUST have appropriate validators
- Use framework-native validation (PyDAL validators, Go libraries)
- Implement XSS and SQL injection prevention
- Server-side validation for all client input
- CSRF protection using framework native features

## Authentication & Authorization

**Core Requirements:**
- Multi-factor authentication support
- Role-based access control (RBAC) with OAuth2-style scopes
- API key management with rotation
- JWT token validation with proper expiration
- Session management with secure cookies

**OAuth2-Style Scopes Model:**
- All APIs and user permissions MUST be scopable similar to OAuth2 scopes
- Scopes define granular permissions (e.g., `users:read`, `users:write`, `reports:read`, `analytics:admin`)
- Users and API clients receive tokens with specific scope sets
- Endpoints check requested operation against available scopes
- Scopes are hierarchical and composable

**Role-Based Access Control with Scopes:**

Implement three-tier role system at multiple levels:

1. **Global Level** - Organization-wide roles:
   - **Admin**: Full system access, user management, all scopes
   - **Maintainer**: Read/write access to resources, no user management, limited scopes
   - **Viewer**: Read-only access, minimal scopes (e.g., `:read` only)
   - **Custom Roles**: User-defined with selected scopes

2. **Container/Team Level** - Per service/team access:
   - **Team Admin**: Full access within container/team
   - **Team Maintainer**: Read/write within container/team
   - **Team Viewer**: Read-only within container/team
   - **Custom Roles**: Selected scopes for container context

3. **Resource Level** - Per-resource permissions:
   - **Owner**: Full control over specific resource
   - **Editor**: Read/write on specific resource
   - **Viewer**: Read-only on specific resource
   - **Custom Roles**: Specific scopes for resource

**Implementation Pattern:**

```python
# Define scopes for API endpoints
SCOPES = {
    'users:read': 'Read user data',
    'users:write': 'Create/update users',
    'users:admin': 'Delete users, manage roles',
    'reports:read': 'Read reports',
    'reports:write': 'Create/update reports',
    'analytics:read': 'Read analytics',
    'analytics:admin': 'Configure analytics',
}

# Role definitions with scope mappings
ROLE_SCOPES = {
    'global': {
        'admin': ['users:read', 'users:write', 'users:admin', 'reports:read', 'reports:write', 'analytics:read', 'analytics:admin'],
        'maintainer': ['users:read', 'users:write', 'reports:read', 'reports:write', 'analytics:read'],
        'viewer': ['users:read', 'reports:read', 'analytics:read'],
    },
    'container': {
        'admin': ['users:read', 'users:write', 'reports:read', 'reports:write'],
        'maintainer': ['users:read', 'reports:read', 'reports:write'],
        'viewer': ['users:read', 'reports:read'],
    },
}

from flask import Flask, request
from functools import wraps

app = Flask(__name__)

def require_scope(*required_scopes):
    """Decorator to check if user has required scopes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from request context (from JWT token)
            user = request.user  # Set by authentication middleware
            user_scopes = user.get_scopes()

            # Check if user has at least one of required scopes
            has_scope = any(scope in user_scopes for scope in required_scopes)
            if not has_scope:
                return {'error': 'Insufficient permissions', 'required_scopes': required_scopes}, 403
>>>>>>> origin/v1.0.X

            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/api/v1/users', methods=['GET'])
@require_scope('users:read')
def list_users():
<<<<<<< HEAD
    """Only people with 'users:read' can see this"""
    users = db.users.select().fetchall()
    return jsonify({'data': users})
```

**JWT tokens carry scopes:**
```python
import jwt

def create_access_token(user, scopes):
    payload = {
        'sub': user.id,
        'email': user.email,
        'scopes': scopes,  # Include the actual permissions
        'exp': datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

### API Client Scopes

Third-party apps and service accounts get scopes too:

```python
@app.route('/api/v1/clients', methods=['POST'])
@require_scope('users:admin')
def create_api_client():
    """Generate API key with limited permissions"""
    data = request.get_json()
    api_key = generate_secure_key()

    client = {
        'name': data.get('name'),
        'api_key_hash': hash_api_key(api_key),
        'scopes': data.get('scopes', []),  # Limited permissions
    }
    db.api_clients.insert(**client)
    return {'api_key': api_key}  # Only shown once!
```

### Session & Token Security

- JWT tokens expire (1 hour for access, refresh tokens for long-lived access)
- Secure cookies with `HttpOnly`, `Secure`, `SameSite=Strict` flags
- Multi-factor authentication support (2FA codes, biometric, U2F keys)
- Passwords hashed with bcrypt (Flask-Security-Too handles this)

## Encryption & TLS

**What to enforce:**
- **TLS 1.2 minimum** (TLS 1.3 preferred) for all external connections
- HTTPS everywhere—no plain HTTP in production
- HTTP/3 (QUIC) for high-performance scenarios (optional, newer feature)

**Why it matters:** TLS encrypts data in transit, preventing eavesdropping. HTTPS with a valid certificate proves your app is actually your app.

## Input Validation - Trust No One

Every input is potentially dangerous. Validate everything:

```python
from wtforms import StringField, validators

class UserForm:
    email = StringField('Email', [
        validators.Email(),  # Valid email format
        validators.Length(min=5, max=120),
    ])
    username = StringField('Username', [
        validators.Length(min=3, max=20),
        validators.Regexp(r'^[a-zA-Z0-9_]+$'),  # Only alphanumeric + underscore
    ])
    age = IntegerField('Age', [
        validators.NumberRange(min=13, max=120),  # Sensible range
    ])
```

**Server-side always:** Client-side validation is nice for UX, but never trust it. Always validate on the server where attackers can't bypass it.

## Security Scanning Tools

Run these regularly (especially before commits):

### Python Security
```bash
# Check dependencies for known vulnerabilities
pip install safety bandit
safety check                    # CVE database check
bandit -r .                    # Find security issues in code
bandit -r services/flask-backend/
```

### Node.js Security
```bash
# Built-in npm auditing
npm audit                      # List vulnerabilities
npm audit fix                  # Auto-fix what can be fixed
```

### Go Security
```bash
# Install gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...                    # Scan all packages
```

### General - Dependency Monitoring
- **Dependabot**: GitHub automatically checks for outdated packages (enabled by default)
- **Socket.dev**: Advanced threat detection for supply chain attacks
- Check both before committing dependency updates!

## Pre-Deploy Security Checklist

Before every commit and deploy:

- [ ] Run `npm audit` / `safety check` / `gosec` - no vulnerabilities
- [ ] No hardcoded secrets (passwords, API keys, tokens) in code
- [ ] SQL injection protection: Using parameterized queries, not string concatenation
- [ ] XSS protection: User content escaped before display
- [ ] CSRF tokens enabled on all state-changing endpoints
- [ ] Input validation on all endpoints
- [ ] Authentication required for protected endpoints
- [ ] Authorization checked with appropriate scopes/roles
- [ ] TLS enabled for all external communication
- [ ] Passwords hashed (bcrypt, not plaintext)
- [ ] API keys hidden (environment variables, not hardcoded)
- [ ] Error messages don't leak sensitive info (no "user admin@company.com not found")
- [ ] Logs don't contain passwords or secrets
- [ ] Dependencies updated to patched versions

## Found a Vulnerability?

**If you discover a security issue:**

1. **Don't panic** - You found it, that's good!
2. **Don't broadcast it** - Don't post on public channels
3. **Report privately**: Email `security@penguintech.io` with:
   - What you found
   - How to reproduce it
   - What impact it could have
4. **Give us time** - We'll acknowledge within 24 hours, fix ASAP
5. **Coordination** - We'll credit you in security advisories (if you want)

## Learn More

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - The most critical web security risks
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) - Industry standards
- [Flask-Security-Too Docs](https://flask-security-too.readthedocs.io/) - Our auth framework
- [PyDAL Security](https://py4web.io/chapter-13#security) - Database protection
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html) - ORM safety
=======
    """List users - requires users:read scope"""
    users = db.users.select().fetchall()
    return jsonify({'data': users})

@app.route('/api/v1/users', methods=['POST'])
@require_scope('users:write')
def create_user():
    """Create user - requires users:write scope"""
    data = request.get_json()
    user = db.users.insert(**data)
    return jsonify({'data': user}), 201

@app.route('/api/v1/users/<int:user_id>', methods=['DELETE'])
@require_scope('users:admin')
def delete_user(user_id):
    """Delete user - requires users:admin scope"""
    db.users.delete(db.users.id == user_id)
    return '', 204
```

**Custom Roles with Scope Selection:**

```python
# Allow users to create custom roles
@app.route('/api/v1/roles/custom', methods=['POST'])
@require_scope('users:admin')
def create_custom_role():
    """Create custom role with selected scopes"""
    data = request.get_json()
    role_name = data.get('name')
    selected_scopes = data.get('scopes', [])

    # Validate requested scopes
    available_scopes = set(SCOPES.keys())
    if not set(selected_scopes).issubset(available_scopes):
        return {'error': 'Invalid scopes requested'}, 400

    # Create custom role
    custom_role = {
        'name': role_name,
        'scopes': selected_scopes,
        'level': data.get('level', 'container'),  # global, container, or resource
        'created_by': request.user.id,
    }
    db.custom_roles.insert(**custom_role)
    return jsonify({'data': custom_role}), 201

# Assign custom role to user
@app.route('/api/v1/users/<int:user_id>/roles', methods=['POST'])
@require_scope('users:admin')
def assign_role_to_user(user_id):
    """Assign role (standard or custom) to user"""
    data = request.get_json()
    role_id = data.get('role_id')
    scope = data.get('scope', 'global')  # global, container_id, or resource_id

    assignment = {
        'user_id': user_id,
        'role_id': role_id,
        'scope': scope,
    }
    db.role_assignments.insert(**assignment)
    return jsonify({'data': assignment}), 201
```

**JWT Token with Scopes:**

```python
import jwt
from datetime import datetime, timedelta

def create_access_token(user, scopes, expires_in=3600):
    """Create JWT token with scopes"""
    payload = {
        'sub': user.id,
        'user_email': user.email,
        'scopes': scopes,  # Include scopes in token
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

def verify_token(token):
    """Verify token and extract scopes"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.InvalidTokenError:
        return None
```

**API Client Scopes:**

API clients (service accounts, third-party integrations) should also have scope-based permissions:

```python
# Create API client with specific scopes
@app.route('/api/v1/clients', methods=['POST'])
@require_scope('users:admin')
def create_api_client():
    """Create API client with selected scopes"""
    data = request.get_json()
    client_name = data.get('name')
    client_scopes = data.get('scopes', [])

    # Generate API key
    api_key = generate_secure_key()

    client = {
        'name': client_name,
        'api_key': hash_api_key(api_key),
        'scopes': client_scopes,
        'created_by': request.user.id,
        'created_at': datetime.utcnow(),
    }
    db.api_clients.insert(**client)

    # Return plaintext API key only once
    return jsonify({
        'data': client,
        'api_key': api_key,  # Only shown once
    }), 201
```

## TLS/Encryption

- **TLS enforcement**: TLS 1.2 minimum, prefer TLS 1.3
- **Connection security**: Use HTTPS where possible
- **Modern protocols**: HTTP3/QUIC for high-performance
- **Standard security**: JWT, MFA, mTLS where applicable
- **Enterprise SSO**: SAML/OAuth2 as enterprise features

## Dependency Security

- **ALWAYS check Dependabot alerts** before commits
- **Monitor vulnerabilities** via Socket.dev
- **Mandatory security scanning** before dependency changes
- **Fix all security alerts immediately**
- **Version pinning**: Exact versions for security-critical dependencies

## Vulnerability Response Process

1. Identify affected packages and severity
2. Update to patched versions immediately
3. Test updated dependencies thoroughly
4. Document security fixes in commit messages
5. Verify no new vulnerabilities introduced
>>>>>>> origin/v1.0.X
