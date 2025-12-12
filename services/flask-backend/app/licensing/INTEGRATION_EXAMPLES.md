# License Server Integration Examples

Complete examples for integrating license-gated features in IceCharts.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Flask Endpoint Gating](#flask-endpoint-gating)
3. [Advanced SSO Integration](#advanced-sso-integration)
4. [Error Handling](#error-handling)
5. [Testing](#testing)

## Basic Usage

### Checking License Status on Startup

```python
# In app/__init__.py or a startup script
from .licensing import initialize_licensing, get_client

def create_app():
    app = Flask(__name__)

    # Initialize licensing during app startup
    try:
        if initialize_licensing():
            print("License validation successful")
        else:
            print("License not configured (running in development mode)")
    except Exception as e:
        print(f"License initialization warning: {e}")
        # Continue anyway - licensing is optional

    return app
```

### Checking Individual Features

```python
from app.licensing import check_feature, get_client

# Simple boolean check
if check_feature('saml_sso'):
    print("SAML SSO is available")
else:
    print("SAML SSO not available - upgrade license")

# Get all features
client = get_client()
if client:
    features = client.get_all_features()
    for name, available in features.items():
        print(f"{name}: {'Available' if available else 'Not Available'}")
```

## Flask Endpoint Gating

### Feature-Required Decorator

#### Basic Usage

```python
from flask import Flask, jsonify
from app.licensing.decorators import feature_required

app = Flask(__name__)

@app.route('/api/v1/sso/saml/login', methods=['POST'])
@feature_required('saml_sso')
def saml_login():
    """This endpoint requires the 'saml_sso' feature."""
    return jsonify({'status': 'SAML login initiated'}), 200
```

Response when feature is available:
```
HTTP 200 OK
{
    "status": "SAML login initiated"
}
```

Response when feature is not available:
```
HTTP 403 Forbidden
{
    "error": "Feature not available",
    "message": "Feature 'saml_sso' requires license upgrade"
}
```

#### Multiple Feature Requirements

```python
from functools import wraps
from app.licensing.decorators import feature_required

@app.route('/api/v1/advanced/export', methods=['POST'])
@feature_required('advanced_export')
@feature_required('audit_logging')
def export_with_audit():
    """Requires both features."""
    return jsonify({'export': 'complete'}), 200
```

#### Conditional Feature Gating

```python
from flask import request, jsonify
from app.licensing import check_feature

@app.route('/api/v1/export', methods=['POST'])
def export_data():
    """Export with optional advanced features."""
    export_type = request.json.get('type', 'basic')

    if export_type == 'advanced':
        if not check_feature('advanced_export'):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Advanced export requires professional tier',
                'upgrade_url': 'https://penguintech.io/upgrade'
            }), 403

    # Perform export
    return jsonify({'status': 'exported'}), 200
```

### License Tier Decorator

```python
from app.licensing.decorators import license_required

@app.route('/api/v1/enterprise/settings', methods=['GET'])
@license_required(minimum_tier='enterprise')
def get_enterprise_settings():
    """Only accessible with enterprise license."""
    return jsonify({'settings': {...}}), 200
```

## Advanced SSO Integration

### SAML Implementation

```python
# In app/api/v1/sso.py
from flask import request, jsonify, session
from app.licensing.decorators import feature_required
from app.auth import create_access_token, create_refresh_token
from app.models import get_user_by_email, create_user

@sso_v1_bp.route('/saml/login', methods=['POST'])
@feature_required('saml_sso')
def saml_login():
    """
    Production SAML login implementation.
    """
    from onelogin.saml2.auth import OneLogin_Saml2_Auth

    try:
        # Initialize SAML auth
        saml_settings = load_saml_settings()  # Your settings loader
        saml_auth = OneLogin_Saml2_Auth(request, saml_settings)

        # Generate SAML AuthnRequest
        return jsonify({
            'redirect_url': saml_auth.login(),
            'request_id': saml_auth.get_last_request_id()
        }), 200

    except Exception as e:
        logger.error(f"SAML login failed: {e}")
        return jsonify({'error': 'SAML login failed'}), 500


@sso_v1_bp.route('/saml/callback', methods=['POST'])
@feature_required('saml_sso')
def saml_callback():
    """
    Production SAML callback handler.
    """
    from onelogin.saml2.auth import OneLogin_Saml2_Auth

    try:
        saml_settings = load_saml_settings()
        saml_auth = OneLogin_Saml2_Auth(request, saml_settings)

        # Process SAML response
        saml_auth.process_response()

        if not saml_auth.is_authenticated():
            return jsonify({'error': 'SAML authentication failed'}), 401

        # Extract user attributes
        email = saml_auth.get_attributes().get('email', [None])[0]
        full_name = saml_auth.get_attributes().get('name', [None])[0]

        if not email:
            return jsonify({'error': 'Email not provided in SAML response'}), 400

        # Create or update user
        user = get_user_by_email(email)
        if not user:
            user = create_user(
                email=email,
                password_hash='',  # SSO users don't use passwords
                full_name=full_name or email,
                role='viewer'
            )

        # Generate JWT tokens
        access_token = create_access_token(user['id'], user['role'])
        refresh_token, _ = create_refresh_token(user['id'])

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user.get('full_name'),
                'role': user['role']
            }
        }), 200

    except Exception as e:
        logger.error(f"SAML callback failed: {e}")
        return jsonify({'error': 'SAML callback failed'}), 500
```

### OIDC Implementation

```python
from authlib.integrations.flask_client import OAuth
from app.auth import create_access_token, create_refresh_token
from app.models import get_user_by_email, create_user

oauth = OAuth()

def configure_oidc(app):
    """Configure OIDC provider."""
    oauth.init_app(app)
    oauth.register(
        name='oidc_provider',
        server_metadata_url=os.getenv('OIDC_PROVIDER_URL') + '/.well-known/openid-configuration',
        client_id=os.getenv('OIDC_CLIENT_ID'),
        client_secret=os.getenv('OIDC_CLIENT_SECRET'),
        client_kwargs={'scope': 'openid email profile'}
    )


@sso_v1_bp.route('/oidc/login', methods=['POST'])
@feature_required('oidc_sso')
def oidc_login():
    """
    Production OIDC login implementation.
    """
    try:
        data = request.get_json() or {}
        redirect_uri = data.get('redirect_uri')

        if not redirect_uri:
            return jsonify({'error': 'redirect_uri required'}), 400

        client = oauth.oidc_provider
        return client.authorize_redirect(redirect_uri)

    except Exception as e:
        logger.error(f"OIDC login failed: {e}")
        return jsonify({'error': 'OIDC login failed'}), 500


@sso_v1_bp.route('/oidc/callback', methods=['GET'])
@feature_required('oidc_sso')
def oidc_callback():
    """
    Production OIDC callback handler.
    """
    try:
        client = oauth.oidc_provider
        token = client.authorize_access_token()

        # Get user info
        user_info = token.get('userinfo')
        if not user_info:
            user_info = client.parse_id_token(token)

        email = user_info.get('email')
        full_name = user_info.get('name')

        if not email:
            return jsonify({'error': 'Email not provided by OIDC provider'}), 400

        # Create or update user
        user = get_user_by_email(email)
        if not user:
            user = create_user(
                email=email,
                password_hash='',  # SSO users don't use passwords
                full_name=full_name or email,
                role='viewer'
            )

        # Generate JWT tokens
        access_token = create_access_token(user['id'], user['role'])
        refresh_token, _ = create_refresh_token(user['id'])

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user.get('full_name'),
                'role': user['role']
            }
        }), 200

    except Exception as e:
        logger.error(f"OIDC callback failed: {e}")
        return jsonify({'error': 'OIDC callback failed'}), 500
```

## Error Handling

### Graceful Degradation

```python
from app.licensing import check_feature, LicenseValidationError

@app.route('/api/v1/reports')
def generate_report():
    """Generate report with advanced features if available."""

    try:
        basic_report = generate_basic_report()

        # Add advanced features if available
        if check_feature('advanced_analytics'):
            basic_report['analytics'] = generate_advanced_analytics()

        if check_feature('audit_logging'):
            log_audit_event('report_generated')

        return jsonify(basic_report), 200

    except LicenseValidationError as e:
        logger.warning(f"License check failed: {e}")
        # Continue with basic features
        return jsonify(generate_basic_report()), 200
```

### Detailed Error Responses

```python
from app.licensing import FeatureNotAvailableError

@app.errorhandler(FeatureNotAvailableError)
def handle_feature_error(error):
    """Handle feature availability errors."""
    return jsonify({
        'error': 'Feature not available',
        'feature': error.feature,
        'message': str(error),
        'actions': [
            {
                'type': 'upgrade_license',
                'url': 'https://penguintech.io/upgrade'
            },
            {
                'type': 'contact_sales',
                'email': 'sales@penguintech.io'
            }
        ]
    }), 403
```

### Logging

```python
import logging
from app.licensing import get_client

logger = logging.getLogger(__name__)

@app.before_request
def log_license_status():
    """Log license status for monitoring."""
    client = get_client()
    if client:
        features = client.get_all_features()
        logger.debug(f"Available features: {list(features.keys())}")
```

## Testing

### Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from app.licensing import check_feature, LicenseValidationError

class TestLicenseIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_saml_endpoint_without_feature(self):
        """Test SAML endpoint returns 403 without license."""
        with patch('app.licensing.check_feature') as mock_check:
            mock_check.return_value = False

            response = self.client.post('/api/v1/sso/saml/login')
            self.assertEqual(response.status_code, 403)
            self.assertIn('Feature not available', response.json['error'])

    def test_saml_endpoint_with_feature(self):
        """Test SAML endpoint works with license."""
        with patch('app.licensing.check_feature') as mock_check:
            mock_check.return_value = True

            response = self.client.post('/api/v1/sso/saml/login')
            self.assertEqual(response.status_code, 200)

    def test_feature_check_without_license(self):
        """Test feature check returns False without license."""
        with patch('app.licensing.get_client') as mock_get_client:
            mock_get_client.return_value = None

            result = check_feature('saml_sso')
            self.assertFalse(result)
```

### Integration Tests

```python
import unittest
from app import create_app

class TestLicenseIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_license_initialization(self):
        """Test license initializes on app startup."""
        with self.app.app_context():
            from app.licensing import get_client
            # Client may be None if no license key set
            client = get_client()
            # Just verify no exceptions raised
            self.assertTrue(True)

    def test_sso_endpoint_authorization(self):
        """Test SSO endpoints check authorization."""
        # Without license, should return 403
        response = self.client.post('/api/v1/sso/saml/login')
        self.assertIn(response.status_code, [403, 401])
```

### Mock License Server for Testing

```python
import unittest
from unittest.mock import Mock, patch
from app.licensing.client import PenguinTechLicenseClient

class TestLicenseClient(unittest.TestCase):
    def test_validate_with_mock_server(self):
        """Test license validation with mocked server."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'valid': True,
            'customer': 'Test Corp',
            'tier': 'professional',
            'features': [
                {'name': 'saml_sso', 'entitled': True},
                {'name': 'oidc_sso', 'entitled': True},
            ],
            'metadata': {'server_id': 'test_server_id'}
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.Session.post') as mock_post:
            mock_post.return_value = mock_response

            client = PenguinTechLicenseClient(
                'PENG-TEST-TEST-TEST-TEST-TEST',
                'icecharts'
            )

            result = client.validate()
            self.assertTrue(result['valid'])
            self.assertEqual(result['customer'], 'Test Corp')
```

## Complete Example: Custom Report Endpoint

```python
from flask import request, jsonify
from app.licensing.decorators import feature_required
from app.licensing import check_feature
from app.middleware import auth_required
from app.models import get_current_user

@app.route('/api/v1/reports/custom', methods=['POST'])
@auth_required
def create_custom_report():
    """
    Create a custom report with optional advanced features.

    Basic report: Always available
    Advanced analytics: Requires 'advanced_analytics' feature
    Scheduled delivery: Requires 'scheduled_reports' feature
    """

    user = get_current_user()
    data = request.get_json() or {}

    report = {
        'id': generate_id(),
        'created_by': user['id'],
        'type': data.get('type', 'basic')
    }

    # Check for advanced features
    if data.get('include_analytics'):
        if not check_feature('advanced_analytics'):
            return jsonify({
                'error': 'Advanced analytics not available',
                'feature': 'advanced_analytics',
                'tier_required': 'professional'
            }), 403

        report['analytics'] = generate_analytics()

    if data.get('schedule'):
        if not check_feature('scheduled_reports'):
            return jsonify({
                'error': 'Scheduled reports not available',
                'feature': 'scheduled_reports',
                'tier_required': 'enterprise'
            }), 403

        report['schedule'] = data['schedule']

    # Save report
    save_report(report)

    return jsonify(report), 201
```

## Best Practices

1. **Always check license gracefully** - Don't let license checks crash your app
2. **Provide upgrade paths** - Include links to upgrade in error messages
3. **Log license events** - Monitor feature usage for sales insights
4. **Cache feature checks** - Use the built-in 5-minute cache
5. **Handle offline gracefully** - Support 7-day grace period for network issues
6. **Test with mock licenses** - Use mocking in unit tests
7. **Document tier requirements** - Include in API documentation
