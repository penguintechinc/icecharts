# OAuth Dependencies

## Python Backend Dependencies

The Google OAuth2 implementation requires these Python packages (typically already in Flask projects):

```
# requests - HTTP client library (for Google API calls)
requests>=2.28.0

# python-decouple - Environment variable management (already in config.py)
python-decouple>=3.6

# bcrypt - Password hashing (already used for regular auth)
bcrypt>=4.0.0

# PyJWT - JWT token generation (already used for regular auth)
PyJWT>=2.6.0

# Flask - Web framework (core dependency)
Flask>=2.0.0

# Flask-CORS - CORS support
Flask-CORS>=3.0.10
```

## Optional: Flask-Session for Production

For production deployments, consider adding Flask-Session for server-side session storage:

```bash
pip install Flask-Session
```

Current implementation uses Flask's default session (cookie-based), which is sufficient for CSRF protection in development. For production with Redis:

```python
# In app/main.py _init_extensions()
from flask_session import Session

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(app.config['REDIS_URL'])
Session(app)
```

## Frontend Dependencies

The Google OAuth2 button component uses only standard React libraries already in the project:

```json
{
  "react": "^18.0",
  "react-router-dom": "^6.0",
  "zustand": "^4.0"  // Already used for state management
}
```

No additional npm packages needed.

## Installation

### Backend
All required dependencies should already be installed. If starting fresh:

```bash
cd services/flask-backend
pip install -r requirements.txt
```

### Frontend
All dependencies already present:

```bash
cd services/webui
npm install
```

## Verification

### Python Packages
```bash
python -c "import requests; import jwt; import bcrypt; print('All OAuth dependencies installed')"
```

### Node Packages
```bash
npm list react react-router-dom zustand
```

## Configuration

### Environment Files
The implementation uses standard environment variables already configured:

- `GOOGLE_CLIENT_ID` - OAuth app client ID
- `GOOGLE_CLIENT_SECRET` - OAuth app client secret
- `GOOGLE_REDIRECT_URI` - OAuth redirect URL
- `SECRET_KEY` - Flask secret key (for session protection)
- `JWT_SECRET_KEY` - JWT signing key

All configured in `config.py` using python-decouple (existing pattern).

## Docker Setup

The Docker images already include all necessary dependencies:

- Flask backend container: Python with requests, bcrypt, PyJWT, Flask, Flask-CORS
- Frontend container: Node.js with React and routing libraries

No additional image configuration needed.

## Network Requirements

The following external APIs are called:

1. **Google OAuth Endpoints:**
   - `https://accounts.google.com/o/oauth2/v2/auth` - Authorization endpoint
   - `https://oauth2.googleapis.com/token` - Token endpoint
   - `https://www.googleapis.com/oauth2/v2/userinfo` - User info endpoint

All use HTTPS and are publicly available. No proxy configuration needed unless you have network restrictions.

## Security Considerations

### HTTPS in Production
OAuth 2.0 requires HTTPS in production:
- All Google URLs are HTTPS
- Your `GOOGLE_REDIRECT_URI` must use HTTPS in production
- Set `SECURE_COOKIES = True` in production config

### Key Management
- Keep `GOOGLE_CLIENT_SECRET` secure (never commit to Git)
- Use `.env` file or environment variables
- Add `.env` to `.gitignore` (already done)
- Rotate keys periodically

### Token Storage
- Access tokens stored in localStorage (JSON-format vulnerability)
- Consider HTTPOnly cookies for production (requires additional setup)
- Refresh tokens should be HttpOnly and Secure

## Troubleshooting

### Import Errors
```python
# requests not found
pip install requests

# jwt not found (should not happen)
pip install PyJWT
```

### Missing Environment Variables
```bash
# Check variables are set
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET
echo $GOOGLE_REDIRECT_URI
```

### Session Errors (Flask)
If session operations fail:
1. Verify `SECRET_KEY` is set in environment
2. Check Flask version is >= 2.0.0
3. For Redis sessions, verify Redis is running

### Frontend Build Errors
```bash
# Clear node_modules and reinstall
cd services/webui
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Version Compatibility

- Python: 3.8+
- Node.js: 16+ (preferably 18+)
- Flask: 2.0+
- React: 16.8+ (preferably 18+)

The implementation uses standard libraries and should be compatible with modern versions.
