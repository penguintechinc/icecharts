# IceRuns Webhooks Guide

Complete guide to using IceRuns webhooks for external function triggers.

## Quick Start

### Generate Webhook URL

1. Create or open a function in IceRuns
2. Go to **Webhook** tab
3. Copy your webhook URL:
   ```
   https://your-icecharts.com/api/v1/iceruns/hook/{token}
   ```

### Trigger Via Webhook

```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

## Webhook Features

### 1. Public Token Authentication
- No JWT token required
- Token embedded in URL
- Suitable for external services

### 2. Rate Limiting
- Default: 100 requests per hour
- Configurable per function
- Returns HTTP 429 if exceeded

### 3. IP Whitelisting (Optional)
- Restrict by source IP CIDR blocks
- Multiple IPs supported
- Useful for production integrations

### 4. HMAC Signature Validation (Optional)
- Request signing for security
- SHA256-based
- Prevents tampering

### 5. HTTP Method Restrictions
- Configure allowed methods (GET, POST, PUT, etc.)
- Default: POST only
- GET useful for health checks

## Request Formats

### JSON Payload
```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/photo.jpg", "width": 800}'
```

### Form Data
```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -F "file=@photo.jpg" \
  -F "width=800"
```

### Query Parameters
```bash
curl -X GET "https://your-icecharts.com/api/v1/iceruns/hook/{token}?url=https://example.com/photo.jpg&width=800"
```

### Custom Headers
```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -H "X-Custom-Header: value" \
  -d '{"data": "value"}'
```

## HMAC Signature Validation

### Enabling HMAC Validation

1. Open function → **Webhook** tab
2. Toggle **Validate Signature** ON
3. Function will provide webhook secret

### Request Signing

Calculate HMAC SHA256 of request body:

```bash
# Bash example
webhook_secret="your-webhook-secret"
request_body='{"name": "Alice"}'

signature=$(echo -n "$request_body" | openssl dgst -sha256 -hmac "$webhook_secret" -hex | cut -d' ' -f2)

curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "X-IceRuns-Signature: sha256=$signature" \
  -d "$request_body"
```

### Signature Header Format
```
X-IceRuns-Signature: sha256={hex_encoded_signature}
```

### Python Example
```python
import hmac
import hashlib

def sign_request(body, secret):
    return hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

# Usage
body = '{"name": "Alice"}'
secret = "your-webhook-secret"
signature = sign_request(body, secret)

headers = {
    "X-IceRuns-Signature": f"sha256={signature}"
}
```

### Node.js Example
```javascript
const crypto = require('crypto');

function signRequest(body, secret) {
  return crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
}

// Usage
const signature = signRequest('{"name": "Alice"}', 'your-webhook-secret');
const header = `sha256=${signature}`;
```

## Advanced Configuration

### IP Whitelisting

Restrict webhooks to specific source IPs:

```bash
# Via API
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{function_id}/webhook/config \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_whitelist": [
      "203.0.113.0/24",
      "198.51.100.42/32"
    ]
  }'
```

### Rate Limiting

Configure requests per hour:

```bash
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{function_id}/webhook/config \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rate_limit": 1000
  }'
```

### Allowed HTTP Methods

Enable specific methods:

```bash
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{function_id}/webhook/config \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_methods": ["GET", "POST", "PUT"]
  }'
```

## Webhook Metadata

Functions receive enriched input with webhook information:

```json
{
  "__webhook__": {
    "method": "POST",
    "headers": {
      "content-type": "application/json",
      "user-agent": "curl/7.64.1"
    },
    "ip": "203.0.113.42",
    "timestamp": "2026-01-20T12:00:00Z",
    "signature_valid": true
  },
  "name": "Alice"
}
```

### Python Example
```python
def handler(event):
    # Access webhook metadata
    method = event.get('__webhook__', {}).get('method')
    source_ip = event.get('__webhook__', {}).get('ip')
    original_data = {k: v for k, v in event.items() if k != '__webhook__'}

    return {
        'received_from': source_ip,
        'method': method,
        'data': original_data
    }
```

### Node.js Example
```javascript
exports.handler = (event) => {
  const webhookInfo = event.__webhook__ || {};
  const { method, ip } = webhookInfo;

  // Process data
  const data = Object.fromEntries(
    Object.entries(event).filter(([k]) => k !== '__webhook__')
  );

  return {
    received_from: ip,
    method: method,
    data: data
  };
};
```

## Integration Examples

### GitHub Webhook

Trigger function on push events:

```python
# GitHub function that processes push events
def handler(event):
    webhook_info = event.get('__webhook__', {})

    if webhook_info.get('method') != 'POST':
        return {'error': 'POST only', 'success': False}

    # Process GitHub payload
    repository = event.get('repository', {}).get('name')
    pushed_at = event.get('pushed_at')

    return {
        'repository': repository,
        'pushed_at': pushed_at,
        'processed': True,
        'success': True
    }
```

GitHub webhook setup:
1. Go to repository → Settings → Webhooks
2. Add webhook with your IceRuns webhook URL
3. Content type: `application/json`
4. Events: `push`

### AWS SNS Integration

Trigger function from SNS messages:

```python
import json

def handler(event):
    # SNS sends message as JSON string
    if 'Message' in event:
        message = json.loads(event['Message'])
    else:
        message = event

    return {
        'notification': 'received',
        'message': message,
        'success': True
    }
```

Configure SNS:
1. Create SNS topic
2. Add HTTP(S) subscription
3. Use IceRuns webhook URL
4. Acknowledge subscription confirmation

### Stripe Payment Events

Process Stripe webhooks:

```python
import hmac
import hashlib
import json

def handler(event):
    webhook_info = event.get('__webhook__', {})

    # Stripe signature already validated by IceRuns
    # Just process the event

    event_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    if event_type == 'payment_intent.succeeded':
        return {
            'amount': data.get('amount'),
            'currency': data.get('currency'),
            'processed': True
        }

    return {'event_type': event_type, 'processed': False}
```

Stripe setup:
1. Dashboard → Developers → Webhooks
2. Add endpoint with IceRuns webhook URL
3. Enable events: `payment_intent.succeeded`, etc.

## Error Handling

### Rate Limit Exceeded

```json
HTTP 429 Too Many Requests

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit: 100 requests per hour",
  "retry_after": 3600
}
```

### Invalid Signature

```json
HTTP 400 Bad Request

{
  "error": "invalid_signature",
  "message": "Signature validation failed"
}
```

### IP Not Whitelisted

```json
HTTP 403 Forbidden

{
  "error": "ip_not_whitelisted",
  "message": "Source IP 203.0.113.99 is not allowed"
}
```

### Method Not Allowed

```json
HTTP 405 Method Not Allowed

{
  "error": "method_not_allowed",
  "message": "GET method is not allowed",
  "allowed_methods": ["POST"]
}
```

## Testing Webhooks

### Test via WebUI

1. Function detail → **Webhook** tab
2. Click **Test Webhook**
3. Enter sample payload
4. View execution result

### Test via curl

```bash
# Simple test
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -d '{"test": true}' \
  -v

# With timing
time curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### Monitor Webhook Calls

View execution history:
```bash
# Get recent executions
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/{function_id}/executions?limit=10"

# Check specific execution
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}"

# View logs
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/executions/{execution_id}/logs"
```

## Best Practices

### 1. Always Use HTTPS
- Webhooks work over HTTP, but HTTPS recommended
- Never transmit sensitive data unencrypted

### 2. Enable HMAC Signing
- Validate requests came from IceRuns
- Prevents spoofing from malicious sources

### 3. Whitelist IPs
- Restrict to known services
- Added security layer

### 4. Handle Rate Limits
- Implement exponential backoff
- Cache results when possible
- Use async triggers

### 5. Idempotent Processing
- Handle duplicate requests gracefully
- Store execution IDs to detect duplicates
- Don't assume exactly-once delivery

### 6. Monitor Failed Webhooks
- Set up alerts for failures
- Log all webhook calls
- Review error rates regularly

### 7. Set Appropriate Timeouts
- Configure function timeout for expected duration
- Leave headroom for network latency
- Plan for cold starts

### 8. Validate Input
- Never trust webhook input
- Validate data types and ranges
- Sanitize if used in queries

## Security Considerations

### Token Security
- Treat webhook token like password
- Store securely if shared with others
- Regenerate if compromised
- Use separate tokens per environment

### Signature Validation
- Always verify signatures in production
- Use timing-safe comparison
- Keep webhook secret safe
- Rotate secrets periodically

### IP Whitelisting
- Use narrowest CIDR blocks possible
- Document which IPs have access
- Review quarterly

### Rate Limiting
- Set appropriate limits (not too high)
- Monitor for unusual traffic patterns
- Adjust based on legitimate usage

---

See also:
- [API Reference](./api-reference.md)
- [Security](./security.md)
- [Troubleshooting](./troubleshooting.md)
