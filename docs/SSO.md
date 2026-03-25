# Enterprise SSO (Single Sign-On) Documentation

## Overview

IceCharts includes comprehensive SAML 2.0 and OpenID Connect (OIDC) support for enterprise single sign-on. Both protocols are license-gated features requiring `saml_sso` and `oidc_sso` license features respectively.

## Quick Start

### For Developers

#### Installation

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

#### Basic Testing

##### Test SAML with Metadata URL
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

##### Test OIDC with Auto-Discovery
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

### For System Administrators

#### Okta Configuration

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

#### Azure AD Configuration

1. Go to Azure Portal → App registrations
2. Create new app registration
3. Configure Redirect URI: `https://your-domain.com/api/v1/sso/oidc/callback`
4. In IceCharts Admin Panel:
   - Go to Settings → SSO Configuration → OpenID Connect
   - Issuer: `https://login.microsoftonline.com/{tenant-id}/v2.0`
   - Client ID: From App registration
   - Client Secret: Generate in Certificates & secrets
   - Save

#### Google Workspace Configuration

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

### API Testing

#### Using cURL

##### Get SAML Metadata
```bash
curl -s https://your-domain.com/api/v1/sso/saml/metadata \
  -H "Accept: application/xml" | head -20
```

##### Configure SAML
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

##### Check SAML Status
```bash
curl -s https://your-domain.com/api/v1/sso/saml/config \
  -H "Authorization: Bearer {access_token}" | jq
```

##### Configure OIDC
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

#### Using Python Requests

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

### Frontend Integration

#### Add SSO to Login Page

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

#### Add SSO Configuration Page

1. Navigate to Settings/Admin Panel
2. SSO Configuration tab appears if you have `saml_sso` or `oidc_sso` features
3. Fill in IdP details and save

## Architecture

### Backend Components

**Location**: `/services/flask-backend/app/auth/`

1. **`saml_handler.py`** - SAML 2.0 implementation
   - `SAMLConfig`: SAML IdP configuration dataclass
   - `SAMLHandler`: Handles SAML request/response processing
   - Supports metadata URL or manual configuration
   - Validates signatures and extracts user attributes

2. **`oidc_handler.py`** - OpenID Connect implementation
   - `OIDCConfig`: OIDC provider configuration with discovery
   - `OIDCHandler`: Handles OAuth2 authorization flow with PKCE
   - JWT validation with JWKS support
   - Automatic configuration discovery

3. **`jit_provisioning.py`** - Just-In-Time user provisioning
   - `JITProvisioner`: Automatically creates users on first login
   - `AttributeMapping`: Maps IdP attributes to user fields
   - Group-to-role mapping for automatic role assignment

### API Endpoints

**Location**: `/services/flask-backend/app/api/v1/sso.py`

All endpoints are license-gated with `@feature_required()` decorator.

#### SAML Endpoints

- `GET /api/v1/sso/saml/metadata` - Returns SP metadata XML (no auth required)
- `GET /api/v1/sso/saml/login` - Initiates SAML login flow
- `POST /api/v1/sso/saml/acs` - Assertion Consumer Service (receives SAML response)
- `POST /api/v1/sso/saml/logout` - Initiates logout flow

#### OIDC Endpoints

- `GET /api/v1/sso/oidc/login` - Initiates OIDC login flow
- `GET /api/v1/sso/oidc/callback` - OAuth2 callback handler

#### Admin Configuration Endpoints

- `GET /api/v1/sso/saml/config` - Get current SAML configuration (admin only)
- `POST /api/v1/sso/saml/config` - Configure SAML (admin only)
- `GET /api/v1/sso/oidc/config` - Get current OIDC configuration (admin only)
- `POST /api/v1/sso/oidc/config` - Configure OIDC (admin only)

### Frontend Components

**Location**: `/services/webui/src/client/`

1. **`components/SSOLoginButtons.tsx`** - SSO provider buttons on login page
   - Displays configured SSO options
   - Initiates SSO flows
   - Responsive design

2. **`pages/SSOConfiguration.tsx`** - Admin configuration UI
   - Tab-based interface (SAML / OIDC)
   - Metadata URL or manual configuration
   - JIT provisioning settings
   - Default role assignment

## Configuration

### SAML Configuration

#### Using Metadata URL (Recommended)

```bash
curl -X POST http://localhost:5000/api/v1/sso/saml/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "metadata_url": "https://idp.example.com/metadata",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

#### Manual Configuration

```bash
curl -X POST http://localhost:5000/api/v1/sso/saml/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "idp_name": "Okta",
    "idp_entity_id": "https://okta.example.com",
    "sso_url": "https://okta.example.com/app/amazon_aws/exk1234567890/sso/saml",
    "slo_url": "https://okta.example.com/app/amazon_aws/exk1234567890/slo/saml",
    "x509_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

### OIDC Configuration

```bash
curl -X POST http://localhost:5000/api/v1/sso/oidc/config \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {access_token}" \
  -d '{
    "issuer": "https://accounts.google.com",
    "client_id": "your-client-id.apps.googleusercontent.com",
    "client_secret": "your-client-secret",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

## Authentication Flows

### SAML 2.0 Flow

```
1. User clicks "Sign in with SAML"
2. Frontend redirects to /api/v1/sso/saml/login
3. Backend generates SAML AuthnRequest
4. Backend redirects user to IdP
5. User authenticates with IdP
6. IdP POSTs SAML response to /api/v1/sso/saml/acs
7. Backend validates signature and extracts attributes
8. JIT provisioning creates user if needed
9. Backend generates JWT tokens
10. Frontend receives tokens and redirects to dashboard
```

### OIDC Flow (with PKCE)

```
1. User clicks "Sign in with OIDC"
2. Frontend redirects to /api/v1/sso/oidc/login
3. Backend generates PKCE code_verifier and code_challenge
4. Backend stores code_verifier in session
5. Backend redirects user to authorization endpoint with code_challenge
6. User authenticates and grants consent
7. Provider redirects to /api/v1/sso/oidc/callback?code=...
8. Backend exchanges code + code_verifier for tokens
9. Backend validates ID token and gets userinfo
10. JIT provisioning creates user if needed
11. Backend returns JWT tokens
12. Frontend receives tokens and redirects to dashboard
```

## Security Features

### SAML 2.0

- XML signature validation (ensures IdP authenticity)
- TLS 1.2+ encryption for all communications
- Support for encrypted assertions
- Automatic metadata parsing and validation
- Name ID verification
- Conditions validation (NotBefore, NotOnOrAfter)

### OpenID Connect

- PKCE (Proof Key for Code Exchange) for native/SPA apps
- JWT validation with cryptographic verification
- JWKS endpoint support for key rotation
- ID token audience validation
- Access token validation
- TLS 1.2+ required for all endpoints

### General Security

- All tokens include expiration times
- Refresh token rotation on use
- Role-based access control (RBAC) in JWT
- Admin-only configuration endpoints
- Audit logging of SSO events
- Session protection with CSRF tokens

## Just-In-Time (JIT) Provisioning

Automatically creates users on first SSO login:

```python
# Configuration
{
  "jit_enabled": true,
  "auto_assign_role": "viewer",  # Default role for new users
  "attribute_mapping": {
    "email_field": "email",
    "name_field": "name",
    "groups_field": "groups"
  },
  "group_role_mapping": {
    "admin_group": "admin",
    "maintainers_group": "maintainer"
  }
}
```

### Attribute Mapping

Common attribute names are automatically detected:

**Email**: `email`, `emailAddress`, `mail`, `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`

**Name**: `displayName`, `cn`, `commonName`, `given_name`, `family_name`

**Groups**: `groups`, `memberOf`, `roles`, `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/groups`

## IdP-Specific Configuration

### Azure AD / Entra ID

**Metadata URL**: `https://login.microsoftonline.com/{tenant-id}/federationmetadata/2007-06/federationmetadata.xml`

**OIDC Issuer**: `https://login.microsoftonline.com/{tenant-id}/v2.0`

### Okta

**Metadata URL**: `https://{org}.okta.com/app/{app-id}/sso/saml/metadata`

**OIDC Issuer**: `https://{org}.okta.com`

### Google Workspace / Google Cloud Identity

**OIDC Issuer**: `https://accounts.google.com`

**SAML Metadata URL**: Configured in Google Cloud Console

### Keycloak

**Metadata URL**: `https://{keycloak-server}/auth/realms/{realm}/protocol/saml/descriptor`

**OIDC Issuer**: `https://{keycloak-server}/auth/realms/{realm}`

## API Response Examples

### SAML Login Success

```json
{
  "message": "SAML authentication successful",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "viewer",
    "is_new": false
  },
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "Bearer",
    "expires_in": 14400
  }
}
```

### Configuration Retrieval

```json
{
  "config": {
    "idp_name": "Okta",
    "idp_entity_id": "https://okta.example.com",
    "sso_url": "https://okta.example.com/app/amazon_aws/exk/sso/saml",
    "slo_url": "https://okta.example.com/app/amazon_aws/exk/slo/saml",
    "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    "metadata_url": "https://okta.example.com/app/amazon_aws/exk/sso/saml/metadata"
  }
}
```

## Error Handling

### Common Errors

**SAML not configured**
```json
{
  "error": "SAML not configured",
  "message": "No SAML IdP configuration found"
}
```

**Invalid SAML response**
```json
{
  "error": "SAML validation failed",
  "message": "Assertion validation failed: signature verification failed"
}
```

**OIDC provider unreachable**
```json
{
  "error": "Invalid configuration",
  "message": "Could not discover OIDC configuration"
}
```

**License not available**
```json
{
  "error": "Feature not available",
  "message": "Feature 'saml_sso' requires license upgrade"
}
```

## Troubleshooting

### SAML Issues

1. **"Signature verification failed"**
   - Check that X.509 certificate matches IdP
   - Verify certificate is not expired
   - Ensure metadata URL is correct

2. **"Assertion validation failed"**
   - Check NotBefore/NotOnOrAfter conditions
   - Verify server clock is synchronized
   - Check SAML response has required attributes

3. **"No matching users"**
   - Enable JIT provisioning
   - Check attribute mapping (especially email field)
   - Verify IdP sends required attributes

### OIDC Issues

1. **"Invalid issuer"**
   - Check issuer URL matches provider
   - Use HTTPS, not HTTP
   - Verify no trailing slashes

2. **"JWKS endpoint unreachable"**
   - Verify network connectivity
   - Check firewall rules
   - Ensure provider supports JWKS

3. **"Userinfo request failed"**
   - Verify access token is valid
   - Check token scopes include `profile` and `email`
   - Ensure provider supports userinfo endpoint

## Deployment Considerations

### Database Storage

For production, SSO configurations should be stored in the database:

```python
# Add to models.py
db.define_table(
    'sso_configurations',
    Field('type', 'string', requires=IS_IN_SET(['saml', 'oidc'])),
    Field('name', 'string', unique=True),
    Field('enabled', 'boolean', default=True),
    Field('config', 'json'),
    Field('jit_enabled', 'boolean', default=True),
    Field('auto_assign_role', 'string', default='viewer'),
    Field('created_at', 'datetime', default=datetime.utcnow),
    Field('updated_at', 'datetime', default=datetime.utcnow, update=datetime.utcnow),
)
```

### Redis Caching

Cache IdP metadata for 24 hours:

```python
cache.set(f'saml:metadata:{idp_id}', metadata_xml, timeout=86400)
```

### Environment Variables

```bash
# Flask configuration
SAML_ENABLED=true
OIDC_ENABLED=true
SESSION_TYPE=redis
SESSION_REDIS=redis://localhost:6379/0

# License
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-XXXX
LICENSE_SERVER_URL=https://license.penguintech.io
```

## License Gating

SSO features are gated behind license features:

```python
from app.licensing.decorators import feature_required

@app.route('/api/v1/sso/saml/login')
@feature_required('saml_sso')
def saml_login():
    ...

@app.route('/api/v1/sso/oidc/login')
@feature_required('oidc_sso')
def oidc_login():
    ...
```

When features are not available, users receive a 403 error with message:
```json
{
  "error": "Feature not available",
  "message": "Feature 'saml_sso' requires license upgrade"
}
```

## Performance Notes

- SAML metadata is cached (suggested: 24 hours)
- OIDC JWKS is cached (suggested: 1 hour)
- Database queries should be indexed on email
- Use Redis for session storage in production

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

## Related Documentation

- [Development Standards](./STANDARDS.md) - General development guidelines
- [License Server Integration](./licensing/license-server-integration.md) - License management
- [API Documentation](./API.md) - Complete API reference
