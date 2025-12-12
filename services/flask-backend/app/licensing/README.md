# PenguinTech License Server Integration

This module provides integration with the PenguinTech License Server for IceCharts enterprise features.

## Overview

The licensing system validates licenses, manages feature entitlements, and maintains server connectivity through keepalive messages. It operates in two modes:

- **Development Mode**: All features available, no license checks (default)
- **Production Mode**: License validation required, feature gating active

## Architecture

### Components

- **`client.py`**: Core license client implementing server API interactions
- **`decorators.py`**: Flask decorators for feature gating
- **`__init__.py`**: Initialization and global client management

### Features

- License validation with 5-minute caching
- Feature entitlement checking
- Automatic keepalive heartbeat (5-minute intervals)
- Grace period support (7 days for offline operation)
- Thread-safe background keepalive process

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LICENSE_KEY` | No | None | License key (format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD) |
| `PRODUCT_NAME` | No* | None | Product identifier (e.g., 'icecharts') |
| `LICENSE_SERVER_URL` | No | https://license.penguintech.io | License server endpoint |
| `RELEASE_MODE` | No | false | Enable license enforcement in production |

*Required only if `LICENSE_KEY` is set

## Initialization

The licensing system is automatically initialized when the Flask app starts:

```python
from app import create_app

app = create_app()
# Licensing initialized automatically during app creation
```

The initialization process:

1. Creates license client from environment variables
2. Validates license with server
3. Starts background keepalive thread
4. Caches feature entitlements

If license key is not configured, licensing is disabled and all features are available.

## Usage

### Checking License Status

```python
from app.licensing import get_client, check_feature, get_all_features

# Get client instance
client = get_client()

# Check single feature
if check_feature('saml_sso'):
    print("SAML SSO is available")

# Get all features
features = get_all_features()
for feature_name, enabled in features.items():
    print(f"{feature_name}: {enabled}")
```

### Gating Endpoints with Decorators

#### Feature-Based Gating

```python
from flask import jsonify
from app.licensing.decorators import feature_required

@app.route('/api/advanced/analytics')
@feature_required('advanced_analytics')
def generate_report():
    """Requires 'advanced_analytics' feature."""
    return jsonify({'report': 'data'})
```

#### License Tier-Based Gating

```python
from app.licensing.decorators import license_required

@app.route('/api/enterprise/audit-log')
@license_required(minimum_tier='enterprise')
def get_audit_log():
    """Requires enterprise or higher tier."""
    return jsonify({'audit_log': []})
```

### Sending Usage Data

```python
client = get_client()

# Send keepalive with usage statistics
usage_data = {
    'active_users': 42,
    'documents_processed': 1000,
    'api_calls': 50000
}

try:
    response = client.keepalive(usage_data)
    print(f"Keepalive sent: {response}")
except LicenseValidationError as e:
    print(f"Keepalive failed: {e}")
```

## Enterprise Features (SSO)

The SSO endpoints are gated behind license features:

### SAML 2.0 (Single Sign-On)

Requires `saml_sso` feature:

```python
# Endpoint: POST /api/v1/sso/saml/login
# Endpoint: POST /api/v1/sso/saml/callback
```

### OpenID Connect (OIDC)

Requires `oidc_sso` feature:

```python
# Endpoint: POST /api/v1/sso/oidc/login
# Endpoint: GET /api/v1/sso/oidc/callback
```

### SSO Status

Check available SSO methods:

```python
# Endpoint: GET /api/v1/sso/status
# Requires authentication
```

## License Key Format

```
PENG-XXXX-XXXX-XXXX-XXXX-ABCD
```

Where:
- `PENG` = Product prefix
- `XXXX` = Alphanumeric segments (4 characters each)
- `ABCD` = Checksum segment (4 characters)

Example: `PENG-A1B2-C3D4-E5F6-G7H8-I9J0`

## API Integration

### Validate License

```
POST /api/v2/validate
Authorization: Bearer LICENSE_KEY
Content-Type: application/json

{
    "product": "icecharts"
}

Response:
{
    "valid": true,
    "customer": "ACME Corp",
    "tier": "professional",
    "features": [
        {
            "name": "saml_sso",
            "entitled": true
        },
        {
            "name": "oidc_sso",
            "entitled": false
        }
    ],
    "metadata": {
        "server_id": "server_uuid",
        "expires_at": "2025-12-31"
    }
}
```

### Check Feature

```
POST /api/v2/features
Authorization: Bearer LICENSE_KEY
Content-Type: application/json

{
    "product": "icecharts",
    "feature": "saml_sso"
}

Response:
{
    "features": [
        {
            "name": "saml_sso",
            "entitled": true
        }
    ]
}
```

### Keepalive

```
POST /api/v2/keepalive
Authorization: Bearer LICENSE_KEY
Content-Type: application/json

{
    "product": "icecharts",
    "server_id": "server_uuid",
    "active_users": 42,
    "documents_processed": 1000
}

Response:
{
    "status": "ok",
    "next_keepalive": "2025-12-10T14:05:00Z"
}
```

## Error Handling

### LicenseValidationError

Raised when license validation or keepalive fails:

```python
from app.licensing import LicenseValidationError

try:
    client.validate()
except LicenseValidationError as e:
    print(f"Validation failed: {e}")
```

### FeatureNotAvailableError

Raised when required feature is not available:

```python
from app.licensing import FeatureNotAvailableError

try:
    if not client.check_feature('saml_sso'):
        raise FeatureNotAvailableError('saml_sso')
except FeatureNotAvailableError as e:
    print(f"Feature unavailable: {e}")
```

## Grace Period

The system supports a 7-day grace period for offline operation:

- If the last successful validation was within 7 days, the system continues operating
- Features remain available during the grace period
- Keepalive failures are logged but don't prevent operation
- Cache is valid for 5 minutes

## Caching

Feature entitlements are cached for 5 minutes to reduce server load:

```python
# Check feature (uses cache if valid)
result = client.check_feature('saml_sso', use_cache=True)

# Force fresh check from server
result = client.check_feature('saml_sso', use_cache=False)
```

## Monitoring

Log messages indicate licensing status:

```
INFO: License valid for ACME Corp (professional tier)
INFO: Feature enabled: saml_sso
INFO: Feature enabled: oidc_sso
DEBUG: License keepalive thread started
DEBUG: License keepalive sent successfully
WARNING: License key not configured - licensing disabled
ERROR: License validation failed: Connection timeout
```

## Testing

### Development Environment

No license key required. All features available:

```bash
# No LICENSE_KEY set
flask run
# INFO: License server integration disabled (no license key)
```

### Testing with License

Set license environment variables:

```bash
export LICENSE_KEY="PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
export PRODUCT_NAME="icecharts"
export LICENSE_SERVER_URL="https://license.penguintech.io"

flask run
# INFO: License valid for Company Name (tier name)
```

### Unit Testing

```python
import unittest
from app.licensing import check_feature

class TestLicensing(unittest.TestCase):
    def test_feature_without_license(self):
        """Test that features are unavailable without license."""
        # When LICENSE_KEY is not set
        result = check_feature('saml_sso')
        self.assertFalse(result)

    def test_feature_with_license(self):
        """Test feature check with valid license."""
        # Requires LICENSE_KEY and PRODUCT_NAME set
        result = check_feature('saml_sso')
        # Result depends on actual license
        self.assertIsInstance(result, bool)
```

## Troubleshooting

### License Validation Fails

**Symptom**: `LicenseValidationError: License validation request failed`

**Solutions**:
1. Verify license key format (must be 29 characters: PENG-XXXX-XXXX-XXXX-XXXX-ABCD)
2. Check network connectivity to license server
3. Verify `LICENSE_SERVER_URL` is correct (default: https://license.penguintech.io)
4. Check license key hasn't expired

### Keepalive Errors Don't Stop Server

**Expected Behavior**: Keepalive failures are logged but don't prevent operation.

The system includes a 7-day grace period. After 7 days without successful keepalive, the system will still operate with cached features.

### Features Not Showing as Available

**Solutions**:
1. Verify license includes required features
2. Clear cache by restarting app (5-minute TTL)
3. Check license tier (some features require specific tiers)
4. Verify `PRODUCT_NAME` matches license registration

## References

- [PenguinTech License Server](https://license.penguintech.io)
- [License Server Status](https://status.penguintech.io)
- [Integration Guide](../../../docs/licensing/license-server-integration.md)

## Support

- **License Issues**: support@penguintech.io
- **Technical Support**: developers@penguintech.io
- **Sales**: sales@penguintech.io
