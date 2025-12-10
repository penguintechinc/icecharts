# Google OAuth2 Module

This module provides secure Google OAuth2 authentication for IceCharts.

## Module Contents

### `google_oauth.py`

Handles the complete Google OAuth2 flow.

#### Classes

**GoogleUserInfo** (dataclass)
- Represents user information from Google
- Fields: `id`, `email`, `name`, `picture`, `verified_email`
- Immutable with slots for memory efficiency

**GoogleOAuthHandler**
- Static methods for OAuth flow management
- No state - all methods are idempotent and thread-safe

#### Key Methods

**`get_google_auth_url(state: str) -> str`**
- Generates OAuth authorization URL
- Includes CSRF state parameter
- Returns full URL to redirect browser

**`handle_google_callback(code: str) -> tuple[str, dict]`**
- Exchanges authorization code for tokens
- Calls Google token endpoint
- Returns access token and full token response

**`get_google_user_info(access_token: str) -> GoogleUserInfo`**
- Fetches user profile from Google
- Calls Google userinfo endpoint
- Returns populated GoogleUserInfo dataclass

**`create_or_link_user(google_user: GoogleUserInfo) -> tuple[dict, bool]`**
- Creates new user or links existing user
- Handles duplicate email scenarios
- Returns (user_dict, is_new_user) tuple

## Usage

### Backend API Integration

In `/api/v1/auth.py`:

```python
from ...oauth import GoogleOAuthHandler

# Step 1: Get authorization URL
state = secrets.token_urlsafe(32)
auth_url = GoogleOAuthHandler.get_google_auth_url(state)
session['oauth_state'] = state
return jsonify({'auth_url': auth_url})

# Step 2: Handle callback
access_token, token_data = GoogleOAuthHandler.handle_google_callback(code)
google_user = GoogleOAuthHandler.get_google_user_info(access_token)
user, is_new = GoogleOAuthHandler.create_or_link_user(google_user)

# Step 3: Generate JWT tokens
jwt_token = create_access_token(user['id'], user['role'])
return jsonify({'access_token': jwt_token, ...})
```

### Configuration

Requires environment variables:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/login
```

## Security Features

### CSRF Protection
- State parameter generated server-side
- State validated on callback
- Prevents cross-site request forgery

### Token Security
- Uses authorization code flow (not implicit)
- Single-use authorization codes
- Access tokens have short expiration
- No secrets exposed in redirect

### User Validation
- Email verified by Google before providing tokens
- Account status checked after creation
- Role-based access still applies
- OAuth users get random passwords

## Error Handling

All methods raise `ValueError` with descriptive messages:

```python
try:
    # OAuth operation
except ValueError as e:
    # Handle error: "Token exchange failed: ...", etc.
    return jsonify({'error': str(e)}), 401
```

## Testing

### Unit Tests

```python
def test_get_google_auth_url():
    """Test authorization URL generation"""
    url = GoogleOAuthHandler.get_google_auth_url("test_state")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "test_state" in url
    assert "client_id" in url

def test_create_or_link_user():
    """Test user creation and linking"""
    google_user = GoogleUserInfo(
        id="123456",
        email="test@example.com",
        name="Test User",
        picture="https://...",
        verified_email=True,
    )
    user, is_new = GoogleOAuthHandler.create_or_link_user(google_user)
    assert user['email'] == 'test@example.com'
    assert user['google_id'] == '123456'
    assert is_new == True
```

### Integration Tests

```python
def test_oauth_flow():
    """Test complete OAuth flow"""
    # 1. Request auth URL
    response = client.get('/api/v1/auth/google')
    assert response.status_code == 200

    # 2. Simulate Google callback
    response = client.post('/api/v1/auth/google/callback', json={
        'code': 'valid_code',
        'state': 'valid_state'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json
```

## Google API Endpoints

**Authorization**: `https://accounts.google.com/o/oauth2/v2/auth`
- User logs in and grants permission
- Redirects back with authorization code

**Token**: `https://oauth2.googleapis.com/token`
- Backend exchanges code for tokens
- Returns access_token and other metadata

**UserInfo**: `https://www.googleapis.com/oauth2/v2/userinfo`
- Fetch user profile with access token
- Returns email, name, picture, etc.

## Extending the Module

### Adding New OAuth Providers

Create similar module for GitHub:

```python
# github_oauth.py
class GitHubOAuthHandler:
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USERINFO_URL = "https://api.github.com/user"

    @classmethod
    def get_github_auth_url(cls, state: str) -> str:
        # Similar implementation
        pass
```

### Custom Claims

Extend GoogleUserInfo for additional claims:

```python
@dataclass(slots=True)
class GoogleUserInfo:
    id: str
    email: str
    name: str
    picture: Optional[str]
    verified_email: bool
    locale: Optional[str] = None  # New field
    hd: Optional[str] = None  # Workspace domain
```

### Custom User Creation

Modify create_or_link_user for additional logic:

```python
# In create_or_link_user
if google_user.hd:  # Workspace account
    new_user = create_user(..., role="viewer")
    # Auto-assign team based on workspace domain
else:
    new_user = create_user(..., role="viewer")
```

## Performance Considerations

- **API Calls**: 2 requests to Google per login (token + userinfo)
- **Typical Time**: 500-1000ms (Google API latency)
- **Database**: Single query for user creation/linking
- **Caching**: State tokens expire in session

## Monitoring

### Logs

Module logs via Flask logger:

```python
current_app.logger.error(f"Google OAuth error: {str(e)}")
```

Check logs:
```bash
docker-compose logs flask-backend | grep "Google OAuth"
```

### Metrics

Track OAuth success/failure:

```python
metrics.counter('google_oauth_success').inc()
metrics.counter('google_oauth_failure').inc()
metrics.histogram('google_oauth_duration_ms').observe(duration)
```

## References

- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Google+ API](https://developers.google.com/identity)
- [OWASP OAuth Security](https://cheatsheetseries.owasp.org/cheatsheets/OAuth_2_Cheat_Sheet.html)
