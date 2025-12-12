# Google OAuth2 Authentication Setup

This document provides complete instructions for setting up and using Google OAuth2 authentication in IceCharts.

## Overview

IceCharts now supports Google OAuth2 authentication, allowing users to:
- Sign in with their Google account
- Automatic account creation on first sign-in
- Account linking when email already exists
- CSRF protection using state parameters
- Secure token exchange and JWT generation

## Architecture

### Backend Flow
1. Frontend requests Google auth URL from `/api/v1/auth/google`
2. User redirects to Google consent screen
3. User approves access permissions
4. Google redirects to `/login?code=...&state=...`
5. Frontend sends code and state to `/api/v1/auth/google/callback`
6. Backend exchanges code for tokens via Google API
7. Backend fetches user profile from Google
8. Backend creates or links user account
9. Backend returns JWT access/refresh tokens
10. Frontend stores tokens and redirects to dashboard

### Database Changes

Added fields to `users` table for OAuth support:
- `google_id`: Unique Google user ID
- `oauth_provider`: Provider name ('google', future: 'github', etc.)
- `profile_picture_url`: User's profile picture from OAuth provider

All fields are optional to support gradual migration.

## Setup Instructions

### 1. Google Cloud Console Setup

#### Create Project
1. Go to https://console.cloud.google.com/
2. Click on the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter project name: "IceCharts"
5. Click "CREATE"

#### Enable Google+ API
1. Go to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on "Google+ API"
4. Click "ENABLE"

#### Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "CREATE CREDENTIALS" > "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - Select "External" for user type
   - Fill in required fields:
     - App name: "IceCharts"
     - User support email: your email
     - Developer contact: your email
   - Click "SAVE AND CONTINUE"
   - For scopes, add: `openid`, `email`, `profile`
   - Click "SAVE AND CONTINUE"
   - Add test users if desired (optional)
   - Click "SAVE AND CONTINUE"
4. Back to OAuth credentials, select "Web application"
5. Enter application details:
   - Name: "IceCharts Web App"
6. Under "Authorized JavaScript origins", add:
   ```
   http://localhost:3000
   https://yourdomain.com
   ```
7. Under "Authorized redirect URIs", add:
   ```
   http://localhost:3000/login
   https://yourdomain.com/login
   ```
8. Click "CREATE"
9. Copy the Client ID and Client Secret

### 2. Environment Configuration

Update `.env` file with your Google credentials:

```bash
# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/login
```

For production, update `GOOGLE_REDIRECT_URI` to your actual domain:
```bash
GOOGLE_REDIRECT_URI=https://yourdomain.com/login
```

### 3. Update Authorized Origins

If you change your domain or add new environments:

1. Go to Google Cloud Console > APIs & Services > Credentials
2. Click on your OAuth client ID
3. Update "Authorized JavaScript origins" with new domain
4. Update "Authorized redirect URIs" with new login path
5. Click "SAVE"

## Frontend Integration

### Login Page

The login page now includes a "Sign in with Google" button:

```tsx
import { GoogleLoginButton } from '../components/auth';

export default function Login() {
  return (
    <div>
      <GoogleLoginButton className="mb-6" variant="secondary" />
      {/* Email/password login form below */}
    </div>
  );
}
```

### OAuth Callback Handling

When Google redirects back to your app with `?code=...&state=...`:

1. Login page detects the OAuth parameters
2. `useEffect` calls `handleOAuthCallback(code, state)`
3. Frontend sends code and state to backend
4. Backend validates state (CSRF protection)
5. Backend exchanges code for Google access token
6. Backend fetches user profile
7. Backend creates JWT tokens
8. Frontend stores tokens and redirects to dashboard

### Error Handling

The OAuth flow includes comprehensive error handling:
- Invalid authorization code
- Network failures
- CSRF state mismatch
- Google API errors
- User account deactivation

All errors are displayed on the login page.

## Backend API Endpoints

### GET /api/v1/auth/google
Generates a Google authorization URL with CSRF protection.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

### POST /api/v1/auth/google/callback
Exchanges authorization code for user tokens.

**Request:**
```json
{
  "code": "authorization-code-from-google",
  "state": "csrf-protection-token"
}
```

**Success Response:**
```json
{
  "access_token": "jwt-token",
  "refresh_token": "refresh-token",
  "token_type": "Bearer",
  "expires_in": 1800,
  "user": {
    "id": 123,
    "email": "user@gmail.com",
    "full_name": "User Name",
    "role": "viewer"
  },
  "is_new_user": true
}
```

**Error Response:**
```json
{
  "error": "Authentication failed: ..."
}
```

## Account Linking

When a user signs in with Google:

1. **First time (new email):** New account created with role `viewer`
2. **Existing email:** Google ID linked to existing account
3. **Deactivated account:** Login rejected with appropriate error

This allows users to:
- Sign up with Google OAuth
- Later log in with email/password if they prefer
- Switch between Google and email/password login freely

## Security Considerations

### CSRF Protection
- State parameter generated server-side
- State stored in Flask session
- State validated on callback
- State cleared after use

### Token Security
- Authorization codes are single-use
- Codes expire quickly (typically 10 minutes)
- Access tokens stored in localStorage (consider HTTPOnly cookies for production)
- Refresh tokens stored securely
- All token operations use HTTPS in production

### User Validation
- Email verified by Google before providing tokens
- User account status (active/deactivated) checked
- Role-based access control still applies to OAuth users
- Password generation for OAuth users prevents password-based login without email verification

## Development vs Production

### Development
```bash
GOOGLE_CLIENT_ID=development-client-id
GOOGLE_CLIENT_SECRET=development-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/login
```

### Production
```bash
GOOGLE_CLIENT_ID=production-client-id
GOOGLE_CLIENT_SECRET=production-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/login
```

Create separate OAuth apps for development and production in Google Cloud Console.

## Troubleshooting

### "Invalid state parameter - CSRF validation failed"
- **Cause:** Session not persisted or state mismatch
- **Fix:** Check that Flask sessions are working (SECRET_KEY configured)
- **Fix:** Ensure state parameter matches between endpoints
- **Fix:** Clear browser cookies and try again

### "Failed to get Google auth URL"
- **Cause:** Missing or invalid environment variables
- **Fix:** Verify GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
- **Fix:** Restart Flask backend after changing env vars

### "Google Sign-in redirects to localhost"
- **Cause:** GOOGLE_REDIRECT_URI set to localhost but accessed from different domain
- **Fix:** Update GOOGLE_REDIRECT_URI to match your actual domain
- **Fix:** Add domain to Google Cloud Console authorized URIs

### "User already registered"
- **Cause:** Email exists in system from previous OAuth or email signup
- **Fix:** User can still sign in - the Google account is linked automatically
- **Fix:** Check user status in admin panel if login fails

### "Authentication failed" with no details
- **Cause:** Backend error (check logs)
- **Fix:** Check Flask logs: `docker-compose logs flask-backend`
- **Fix:** Verify Google API responses in Flask logs
- **Fix:** Check database permissions and connection

## Testing OAuth Flow Locally

1. **Start development server:**
   ```bash
   make dev
   ```

2. **Create test Google account:**
   - Use a test Gmail account for development
   - Keep credentials safe

3. **Configure test credentials:**
   - Add test account email as test user in Google Cloud Console
   - Add localhost OAuth URIs to authorized list

4. **Test the flow:**
   - Navigate to http://localhost:3000/login
   - Click "Sign in with Google"
   - Approve permissions on Google consent screen
   - Should create/link account and redirect to dashboard

5. **Verify in database:**
   ```bash
   psql -U icecharts_user -d icecharts_db
   SELECT id, email, google_id, oauth_provider FROM users;
   ```

## Advanced Features

### Adding More OAuth Providers

The implementation is designed to support multiple providers:

1. **GitHub OAuth:**
   - Create `github_oauth.py` following Google pattern
   - Add `/api/v1/auth/github` and `/api/v1/auth/github/callback`
   - Add `github_id` field to users table
   - Update frontend with GitHubLoginButton

2. **Microsoft/Azure:**
   - Similar pattern to Google
   - Update OIDC endpoints
   - Add provider-specific scopes

### Profile Picture Handling

Google provides profile pictures via `picture` URL in user info:

```python
update_user(user_id, profile_picture_url=google_user.picture)
```

Use in frontend:
```tsx
<img src={user.profile_picture_url} alt={user.full_name} />
```

### Custom OAuth Claims

Extend GoogleUserInfo dataclass for additional claims:

```python
@dataclass(slots=True)
class GoogleUserInfo:
    # ... existing fields
    locale: Optional[str]
    hd: Optional[str]  # Hosted domain for Workspace accounts
```

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Identity Services](https://developers.google.com/identity)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [OWASP OAuth Security](https://cheatsheetseries.owasp.org/cheatsheets/OAuth_2_Cheat_Sheet.html)
