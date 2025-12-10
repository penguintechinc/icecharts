# SSO Quick Start Guide

## For Developers

### Installation

1. Install SSO dependencies:
```bash
pip install -r services/flask-backend/requirements.txt
```

Required packages:
- `python3-saml==1.16.0` - SAML 2.0
- `authlib==1.3.1` - OIDC/OAuth2
- `lxml==5.3.0` - XML processing

2. Verify installation:
```bash
python3 -c "from onelogin.saml2.auth import OneLogin_Saml2_Auth; print('SAML OK')"
python3 -c "from authlib.integrations.flask_client import OAuth; print('OIDC OK')"
```

### Basic Testing

#### Test SAML with Metadata URL
```python
from app.auth import SAMLConfig, SAMLHandler

# Load from metadata
url = "https://your-idp.example.com/metadata"
config = SAMLConfig.from_metadata_url(url)
handler = SAMLHandler(config)

# Verify
print(f"IdP Entity ID: {config.idp_entity_id}")
print(f"SSO URL: {config.sso_url}")

# Get login URL
login_url = handler.create_saml_request()
print(f"Login URL: {login_url}")
```

#### Test OIDC with Auto-Discovery
```python
from app.auth import OIDCConfig, OIDCHandler

# Discover configuration
config = OIDCConfig.from_discovery(
    issuer="https://accounts.google.com",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

handler = OIDCHandler(config)

# Verify
print(f"Issuer: {config.issuer}")
print(f"Token Endpoint: {config.token_endpoint}")

# Generate authorization URL
auth_url = handler.build_authorization_url()
print(f"Auth URL: {auth_url}")
```

## For System Administrators

### Okta Configuration

1. Go to Okta Admin Dashboard
2. Applications → Applications
3. Create New App → SAML 2.0
4. Configure:
   - Single sign on URL: `https://your-domain.com/api/v1/sso/saml/acs`
   - Audience URI: `https://your-domain.com/api/v1/sso/saml/metadata`
5. Download metadata URL
6. In IceCharts Admin Panel:
   - Go to Settings → SSO Configuration
   - Paste metadata URL
   - Enable JIT Provisioning
   - Save

### Azure AD Configuration

1. Go to Azure Portal → App registrations
2. Create new app registration
3. Configure Redirect URI: `https://your-domain.com/api/v1/sso/oidc/callback`
4. In IceCharts Admin Panel:
   - Go to Settings → SSO Configuration → OpenID Connect
   - Issuer: `https://login.microsoftonline.com/{tenant-id}/v2.0`
   - Client ID: From App registration
   - Client Secret: Generate in Certificates & secrets
   - Save

### Google Workspace Configuration

1. Go to Google Cloud Console
2. APIs & Services → Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Authorized redirect URIs: `https://your-domain.com/api/v1/sso/oidc/callback`
5. In IceCharts Admin Panel:
   - Go to Settings → SSO Configuration → OpenID Connect
   - Issuer: `https://accounts.google.com`
   - Client ID: From Google Cloud Console
   - Client Secret: From Google Cloud Console
   - Save

## API Testing

### Using cURL

#### Get SAML Metadata
```bash
curl -s https://your-domain.com/api/v1/sso/saml/metadata \
  -H "Accept: application/xml" | head -20
```

#### Configure SAML
```bash
curl -X POST https://your-domain.com/api/v1/sso/saml/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "metadata_url": "https://idp.example.com/metadata",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

#### Check SAML Status
```bash
curl -s https://your-domain.com/api/v1/sso/saml/config \
  -H "Authorization: Bearer {access_token}" | jq
```

#### Configure OIDC
```bash
curl -X POST https://your-domain.com/api/v1/sso/oidc/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "issuer": "https://accounts.google.com",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

### Using Python Requests

```python
import requests
import json

BASE_URL = "https://your-domain.com"
ACCESS_TOKEN = "your-access-token"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Configure SAML
response = requests.post(
    f"{BASE_URL}/api/v1/sso/saml/config",
    headers=headers,
    json={
        "metadata_url": "https://idp.example.com/metadata",
        "jit_enabled": True,
        "auto_assign_role": "viewer"
    }
)
print(json.dumps(response.json(), indent=2))

# Get SAML config
response = requests.get(
    f"{BASE_URL}/api/v1/sso/saml/config",
    headers=headers
)
print(json.dumps(response.json(), indent=2))
```

## Frontend Integration

### Add SSO to Login Page

1. Update login component to import SSO buttons:
```tsx
import SSOLoginButtons from './components/SSOLoginButtons';

export default function Login() {
  return (
    <div className="login-container">
      <h1>Sign In</h1>

      {/* SSO buttons appear here if configured */}
      <SSOLoginButtons />

      {/* Traditional login form */}
      <form>
        {/* ... */}
      </form>
    </div>
  );
}
```

### Add SSO Configuration Page

1. Navigate to Settings/Admin Panel
2. SSO Configuration tab appears if you have `saml_sso` or `oidc_sso` features
3. Fill in IdP details and save

## Troubleshooting

### SAML Issues

**Error: "Signature verification failed"**
- Check X.509 certificate is correct
- Verify certificate hasn't expired
- Ensure metadata URL is accessible

**Error: "Assertion validation failed"**
- Check server time is synchronized
- Verify NotBefore/NotOnOrAfter conditions
- Check IdP sends required attributes

**Issue: Users not auto-created**
- Verify JIT Provisioning is enabled
- Check attribute mapping (especially email)
- Review IdP logs for attribute values

### OIDC Issues

**Error: "Invalid issuer"**
- Check issuer URL exactly matches provider
- Use HTTPS (not HTTP)
- No trailing slashes

**Error: "JWKS endpoint unreachable"**
- Check network/firewall
- Verify provider is operational
- Check IdP JWKS URL is correct

**Issue: Userinfo endpoint fails**
- Verify access token scopes
- Check token hasn't expired
- Ensure userinfo endpoint is enabled

## Security Checklist

Before deploying to production:

- [ ] Enable TLS 1.2+ for all connections
- [ ] Use strong client secrets (32+ characters)
- [ ] Store client secrets in environment variables
- [ ] Enable license gating (`saml_sso`, `oidc_sso`)
- [ ] Configure admin-only SSO settings
- [ ] Test with real IdP
- [ ] Verify JIT provisioning role assignments
- [ ] Enable audit logging
- [ ] Set up monitoring alerts
- [ ] Document IdP configuration
- [ ] Create admin runbook
- [ ] Test failure scenarios

## Performance Notes

- SAML metadata is cached (suggested: 24 hours)
- OIDC JWKS is cached (suggested: 1 hour)
- Database queries should be indexed on email
- Use Redis for session storage in production

## License Requirements

Feature gates for SSO:
- `saml_sso` - SAML 2.0 authentication
- `oidc_sso` - OpenID Connect authentication

Both require valid enterprise license. Without license:
```json
{
  "error": "Feature not available",
  "message": "Feature 'saml_sso' requires license upgrade"
}
```

## Support & Resources

- [Full Documentation](./sso-implementation.md)
- [API Reference](../API.md)
- [Development Standards](./STANDARDS.md)
- [License Integration](./licensing/license-server-integration.md)

## Example IdP Configurations

See [full documentation](./sso-implementation.md#idp-specific-configuration) for:
- Azure AD / Entra ID
- Okta
- Google Workspace
- Keycloak
- Generic SAML 2.0 providers
