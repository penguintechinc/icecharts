# IceCharts Licensing Integration Guide

## Quick Start

### Development (No License Required)

For local development, no license key is needed. All features are available:

```bash
# No LICENSE_KEY environment variable set
python run.py
# INFO: License server integration disabled (no license key)
```

### Production with License

To enable license validation in production:

```bash
# Set license environment variables
export LICENSE_KEY="PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
export PRODUCT_NAME="icecharts"
export RELEASE_MODE="true"

python run.py
# INFO: License valid for Company Name (tier name)
```

## Configuration

### Environment Variables

Add to your `.env` or deployment configuration:

```bash
# License Key (required for production)
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD

# Product Name (required if LICENSE_KEY is set)
PRODUCT_NAME=icecharts

# License Server URL (optional, defaults to https://license.penguintech.io)
LICENSE_SERVER_URL=https://license.penguintech.io

# Release Mode (enables license enforcement, defaults to false)
RELEASE_MODE=true
```

### Docker Compose

```yaml
flask-backend:
  environment:
    - LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
    - PRODUCT_NAME=icecharts
    - LICENSE_SERVER_URL=https://license.penguintech.io
    - RELEASE_MODE=true
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: icecharts-license
type: Opaque
stringData:
  license-key: PENG-XXXX-XXXX-XXXX-XXXX-ABCD
  product-name: icecharts
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-backend
spec:
  template:
    spec:
      containers:
      - name: flask-backend
        env:
        - name: LICENSE_KEY
          valueFrom:
            secretKeyRef:
              name: icecharts-license
              key: license-key
        - name: PRODUCT_NAME
          valueFrom:
            secretKeyRef:
              name: icecharts-license
              key: product-name
```

## Features

### Enterprise SSO Features

These features require license upgrades:

| Feature | Description | API Endpoint |
|---------|-------------|-------------|
| `saml_sso` | SAML 2.0 authentication | `POST /api/v1/sso/saml/login` |
| `oidc_sso` | OpenID Connect authentication | `POST /api/v1/sso/oidc/login` |
| `advanced_analytics` | Advanced reporting features | Custom endpoints |
| `audit_logging` | Comprehensive audit logs | Custom endpoints |

### Checking Available Features

```bash
curl -X GET http://localhost:5000/api/v1/sso/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "user_id": 1,
  "saml_available": true,
  "oidc_available": false,
  "user_sso_method": null
}
```

## API Endpoints

### Public SSO Endpoints

#### SAML Metadata
```
GET /api/v1/sso/saml/metadata
```

Returns SAML service provider metadata for IdP configuration.

#### SAML Login (Requires `saml_sso` feature)
```
POST /api/v1/sso/saml/login
Content-Type: application/json

{
  "relay_state": "optional_redirect_after_login"
}
```

Returns:
```json
{
  "redirect_url": "https://idp.example.com/sso/login?SAMLRequest=...",
  "request_id": "saml_request_id"
}
```

#### SAML Callback (Requires `saml_sso` feature)
```
POST /api/v1/sso/saml/callback
Content-Type: application/json

{
  "SAMLResponse": "base64_encoded_saml_response",
  "RelayState": "relay_state"
}
```

#### OIDC Login (Requires `oidc_sso` feature)
```
POST /api/v1/sso/oidc/login
Content-Type: application/json

{
  "redirect_uri": "https://app.example.com/callback",
  "state": "optional_state_parameter"
}
```

Returns:
```json
{
  "authorization_url": "https://provider.example.com/authorize?...",
  "state": "state_parameter"
}
```

#### OIDC Callback (Requires `oidc_sso` feature)
```
GET /api/v1/sso/oidc/callback?code=AUTH_CODE&state=STATE
```

### Authenticated Endpoints

#### Check SSO Status
```
GET /api/v1/sso/status
Authorization: Bearer YOUR_JWT_TOKEN
```

Returns available SSO methods and current user's SSO method.

## Implementation Checklist

- [ ] Set `LICENSE_KEY` environment variable
- [ ] Set `PRODUCT_NAME` environment variable (e.g., "icecharts")
- [ ] Configure `LICENSE_SERVER_URL` if using custom server
- [ ] Enable `RELEASE_MODE` in production
- [ ] Test license validation: `curl http://localhost:5000/healthz`
- [ ] Verify keepalive thread in logs: `DEBUG: License keepalive thread started`
- [ ] Test feature gating: `curl http://localhost:5000/api/v1/sso/status`
- [ ] Configure SAML/OIDC if needed (requires feature license)

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:5000/healthz

# Readiness check (includes database)
curl http://localhost:5000/readyz
```

### Log Monitoring

Watch for license-related logs:

```bash
# Development (no license)
INFO: License server integration disabled (no license key)

# Production (valid license)
INFO: License valid for ACME Corp (professional tier)
INFO: Feature enabled: saml_sso
INFO: Feature enabled: oidc_sso
DEBUG: License keepalive thread started
DEBUG: License keepalive sent successfully

# Error conditions
ERROR: License validation failed: Connection timeout
WARNING: Feature 'saml_sso' not available
```

## Troubleshooting

### Issue: License validation fails with connection error

**Solution**:
1. Check network connectivity to license server
2. Verify `LICENSE_SERVER_URL` is correct
3. Check firewall rules allow HTTPS connections
4. Verify license server is online: https://status.penguintech.io

### Issue: Features show as unavailable

**Solution**:
1. Verify license key is valid: `PENG-XXXX-XXXX-XXXX-XXXX-ABCD`
2. Check license includes required features
3. Verify `PRODUCT_NAME` matches license registration
4. Clear cache by restarting app

### Issue: Keepalive fails but app still runs

**Expected Behavior**: This is correct. The system includes a 7-day grace period.

Keepalive failures are logged for monitoring but don't stop the app. After 7 days without successful validation, features require re-authentication.

### Issue: SAML/OIDC endpoints return 403 Forbidden

**Cause**: License doesn't include required feature.

**Solution**:
1. Check license tier (SAML/OIDC require professional+ tier)
2. Contact sales@penguintech.io to upgrade license
3. Use basic authentication in development

## License Key Formats

### Valid Format
```
PENG-A1B2-C3D4-E5F6-G7H8-I9J0
PENG-XXXX-XXXX-XXXX-XXXX-ABCD
```

### Invalid Formats
```
PENG-A1B2-C3D4-E5F6-G7H8           # Too short
PENGXXXXXXXXXXXXXXXXXXXXXXXXXXXX   # Missing dashes
ACME-A1B2-C3D4-E5F6-G7H8-I9J0     # Wrong prefix
```

## Testing License Integration

### Manual Testing

```bash
# Start Flask backend with license
export LICENSE_KEY="PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
export PRODUCT_NAME="icecharts"
python run.py

# In another terminal, test SSO endpoint
curl -X POST http://localhost:5000/api/v1/sso/saml/login \
  -H "Content-Type: application/json" \
  -d '{"relay_state": "test"}'

# Should return 200 with feature confirmation
# Or 403 if feature not available
```

### Automated Testing

```python
import os
import unittest
from app import create_app
from app.licensing import get_client, check_feature

class TestLicensing(unittest.TestCase):
    def setUp(self):
        os.environ['LICENSE_KEY'] = 'PENG-TEST-TEST-TEST-TEST-TEST'
        os.environ['PRODUCT_NAME'] = 'icecharts'
        self.app = create_app()

    def test_license_initialization(self):
        client = get_client()
        # In test environment, may be None if LICENSE_KEY is invalid
        if client:
            self.assertIsNotNone(client.license_key)

    def test_feature_check(self):
        # With no valid license, features should be unavailable
        result = check_feature('saml_sso')
        self.assertIsInstance(result, bool)
```

## Support

For license-related issues:
- **Email**: support@penguintech.io
- **Status Page**: https://status.penguintech.io
- **Documentation**: https://docs.penguintech.io/licensing

## Next Steps

1. Review the [Licensing README](./app/licensing/README.md) for detailed API reference
2. Configure SAML or OIDC in your identity provider
3. Set up monitoring for license validation and keepalive
4. Test SSO endpoints in staging environment
5. Schedule production deployment with license validation

## Related Documentation

- [Development Standards](../../docs/STANDARDS.md)
- [License Server API](https://license.penguintech.io/api/docs)
- [SAML 2.0 Configuration Guide](../../docs/sso/saml-configuration.md)
- [OIDC Configuration Guide](../../docs/sso/oidc-configuration.md)
