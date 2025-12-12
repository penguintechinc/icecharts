# Google OAuth2 Implementation Guide

## Quick Start

This guide documents the complete implementation of Google OAuth2 authentication for IceCharts.

## Files Created/Modified

### Backend Files

#### Created
1. **`/app/oauth/google_oauth.py`**
   - `GoogleOAuthHandler` class with static methods
   - `GoogleUserInfo` dataclass
   - Methods for OAuth flow management

2. **`/app/oauth/__init__.py`**
   - Package initialization and exports

#### Modified
1. **`/app/models.py`**
   - Added OAuth fields to users table
   - Added `get_user_by_google_id()` function
   - Updated `create_user()` to accept google_id and oauth_provider
   - Updated `update_user()` to support OAuth fields

2. **`/app/api/v1/auth.py`**
   - Added imports for OAuth and secrets
   - Added GET `/auth/google` endpoint
   - Added POST `/auth/google/callback` endpoint

3. **`/app/config.py`**
   - Added Google OAuth configuration variables

### Frontend Files

#### Created
1. **`/services/webui/src/client/components/auth/GoogleLoginButton.tsx`**
   - Styled Google sign-in button component
   - Handles OAuth flow initiation
   - Error handling and loading states

2. **`/services/webui/src/client/components/auth/__init__.ts`**
   - Component export

#### Modified
1. **`/services/webui/src/client/pages/Login.tsx`**
   - Added OAuth callback detection via URL parameters
   - Added `handleOAuthCallback()` function
   - Integrated GoogleLoginButton component
   - Added OAuth loading state UI
   - Updated form to disable inputs during OAuth flow

2. **`/services/webui/src/client/hooks/useAuth.ts`**
   - Added `setUser` and `useAuthStore` returns
   - Allows direct auth store manipulation

3. **`/services/webui/src/lib/api.ts`**
   - Added OAuth endpoints: `google()` and `googleCallback()`

### Documentation Files

#### Created
1. **`/docs/OAUTH_SETUP.md`**
   - Complete setup instructions
   - Google Cloud Console configuration
   - Deployment guidance
   - Troubleshooting section

2. **`/docs/IMPLEMENTATION_GUIDE.md`** (this file)
   - Implementation overview
   - Architecture details
   - Code structure

#### Modified
1. **`/.env.example`**
   - Added Google OAuth configuration section
   - Setup instructions for OAuth variables

## Architecture Overview

### Backend OAuth Flow

```
User -> Frontend                    -> Backend                    -> Google
  |
  +--[1] GET /login
           (shows login page)
           |
           +--[2] POST /api/v1/auth/google
                  (request OAuth URL)
                  |
                  +--[3] Return auth_url with state
                         |
                         +--[4] Redirect to Google
                                |
                                +--[5] User logs in to Google
                                       |
                                       +--[6] Google redirects to /login?code=...&state=...
                                              |
                                              +--[7] POST /api/v1/auth/google/callback
                                                     (with code & state)
                                                     |
                                                     +--[8] Exchange code for tokens
                                                            |
                                                            +--[9] Fetch user info
                                                                   |
                                                                   +--[10] Create/link user
                                                                           |
                                                                           +--[11] Generate JWT
                                                                                  |
                                                                                  +--[12] Return JWT tokens
                                                                                         |
                                                                                         +--[13] Store tokens
                                                                                              Redirect to dashboard
```

### Database Schema

**users table** (additions):
```sql
ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50);
ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR(500);
```

### Key Components

#### GoogleOAuthHandler

Located in `/app/oauth/google_oauth.py`:

```python
class GoogleOAuthHandler:
    # GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    # GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    # GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    @classmethod
    def get_google_auth_url(state: str) -> str

    @classmethod
    def handle_google_callback(code: str) -> tuple[str, dict]

    @classmethod
    def get_google_user_info(access_token: str) -> GoogleUserInfo

    @classmethod
    def create_or_link_user(google_user: GoogleUserInfo) -> tuple[dict, bool]
```

#### API Endpoints

**GET /api/v1/auth/google**
- Generates CSRF state token
- Stores state in session
- Returns Google authorization URL

**POST /api/v1/auth/google/callback**
- Receives authorization code and state
- Validates CSRF state
- Exchanges code for tokens
- Fetches user info
- Creates/links user account
- Returns JWT tokens

#### Frontend Components

**GoogleLoginButton**
- Styled button with Google logo
- Initiates OAuth flow
- Error handling
- Loading state

**Login Page**
- Detects OAuth callback parameters
- Calls backend callback endpoint
- Stores tokens
- Redirects to dashboard

## Security Features

### CSRF Protection
1. Random state token generated server-side
2. State stored in Flask session
3. State validated on callback
4. State cleared after use
5. Prevents cross-site request forgery

### Token Security
1. Authorization codes are single-use
2. Codes expire quickly (~10 minutes)
3. JWT tokens have short expiration (~30 minutes)
4. Refresh tokens have longer expiration (~7 days)
5. All operations use HTTPS in production

### User Validation
1. Email verified by Google
2. Account status checked (active/deactivated)
3. OAuth users get random passwords
4. Profile picture stored from Google

## Error Handling

### Backend Errors
- Invalid authorization code
- Network failures during token exchange
- User info API failures
- Database errors during user creation
- Missing environment variables

### Frontend Errors
- Missing code/state parameters
- CSRF validation failure
- Network timeouts
- Token storage failures
- User deactivation

### User-Facing Messages
All errors displayed on login page with clear descriptions.

## Configuration

### Environment Variables

```bash
# Required
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/login  # or https://yourdomain.com/login
```

### Google Cloud Console
1. Create project
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Add authorized JavaScript origins
5. Add authorized redirect URIs
6. Copy credentials to .env

## Testing

### Manual Testing

1. **Locally:**
   ```bash
   make dev
   # Navigate to http://localhost:3000/login
   # Click "Sign in with Google"
   # Use test Gmail account
   ```

2. **Database Verification:**
   ```bash
   psql -U icecharts -d icecharts
   SELECT id, email, google_id, oauth_provider FROM users;
   ```

3. **Error Testing:**
   - Close browser during OAuth flow
   - Use invalid credentials
   - Block in network inspector
   - Modify state parameter

### Unit Testing

Backend tests for GoogleOAuthHandler:
```python
def test_get_google_auth_url():
    # Generate auth URL
    # Verify state parameter
    # Verify all query parameters present

def test_handle_google_callback():
    # Mock Google API
    # Test token exchange
    # Verify error handling

def test_get_google_user_info():
    # Mock Google API
    # Test user info retrieval
    # Verify dataclass creation

def test_create_or_link_user():
    # Test new user creation
    # Test existing user linking
    # Test error cases
```

Frontend tests for GoogleLoginButton:
```tsx
describe('GoogleLoginButton', () => {
  test('renders button with Google logo')
  test('calls /api/v1/auth/google on click')
  test('stores return path in session storage')
  test('displays error messages')
  test('disables button while loading')
})
```

## Deployment

### Development
```bash
GOOGLE_CLIENT_ID=dev-id
GOOGLE_CLIENT_SECRET=dev-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/login
```

### Staging
```bash
GOOGLE_CLIENT_ID=staging-id
GOOGLE_CLIENT_SECRET=staging-secret
GOOGLE_REDIRECT_URI=https://staging.yourdomain.com/login
```

### Production
```bash
GOOGLE_CLIENT_ID=prod-id
GOOGLE_CLIENT_SECRET=prod-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/login
```

**Important:** Create separate OAuth apps for each environment.

## Future Enhancements

### GitHub OAuth
- Create `github_oauth.py`
- Add `/auth/github` endpoints
- Add `github_id` field to users
- Create GitHubLoginButton component

### Microsoft/Azure OAuth
- Similar implementation pattern
- Update OIDC endpoints

### Account Unlinking
- Allow users to unlink OAuth accounts
- Require password if unlinking last auth method

### Profile Picture Sync
- Download and store Google profile pictures
- Allow users to update profile from OAuth provider

### Scope Extension
- Request additional scopes (calendar, etc.)
- Store and manage scopes per user

## Migration Path

For existing IceCharts installations:

1. **Database Migration:**
   - Run migration to add OAuth fields
   - Fields are nullable - no data loss
   - Existing users unaffected

2. **Configuration:**
   - Update `.env` with Google credentials
   - No code changes needed for existing functionality

3. **Deployment:**
   - Deploy new code
   - Update login page automatically
   - Existing email/password login still works

4. **Rollout:**
   - OAuth disabled until Google credentials provided
   - Email/password login unaffected
   - Can enable/disable OAuth without affecting other auth

## Troubleshooting

See `/docs/OAUTH_SETUP.md` for detailed troubleshooting guide.

Common issues:
1. CSRF validation failures
2. Missing environment variables
3. Invalid Google Cloud configuration
4. Redirect URI mismatches
5. Network connectivity issues

## Code Quality

All code follows IceCharts standards:
- Type hints throughout
- Docstrings on all functions
- Error handling and validation
- Security best practices
- Clear separation of concerns
- No hardcoded secrets
- Environment variable configuration

## Support

For issues or questions:
1. Check `/docs/OAUTH_SETUP.md`
2. Check Flask logs: `docker-compose logs flask-backend`
3. Check browser console for frontend errors
4. Verify Google Cloud configuration
5. Review environment variables
