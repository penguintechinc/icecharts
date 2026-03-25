# IceRuns Security Guide

Security considerations and best practices for IceRuns deployments.

## Overview

IceRuns implements defense-in-depth security with multiple layers:
1. Authentication & Authorization
2. Container Isolation
3. Secrets Management
4. Rate Limiting
5. Network Security
6. Audit Logging

## Authentication & Authorization

### Scope-Based Access Control

All API operations require appropriate scopes:

```
iceruns:read       - View functions and executions
iceruns:write      - Create/update functions
iceruns:delete     - Delete functions
iceruns:execute    - Trigger function executions
iceruns:logs       - View execution logs
iceruns:admin      - Full administrative access
```

### JWT Tokens

- **Issued by:** Flask-Security-Too
- **Format:** JWT with RS256 signature
- **Expiration:** Configurable (default: 24 hours)
- **Refresh:** Use refresh tokens for long-lived access

### Service Account Tokens

For service-to-service integration:

```bash
# Create service account
curl -X POST https://your-icecharts.com/api/v1/service-accounts \
  -H "Authorization: Bearer {admin-token}" \
  -d '{
    "name": "webhook-processor",
    "scopes": ["iceruns:execute", "iceruns:logs"]
  }'

# Returns long-lived token (up to 1 year)
```

### Webhook Tokens

Public tokens for external webhooks:
- Token validates against database
- Rate limited per function
- Optional HMAC signature validation
- Cannot be used for API calls

## Container Isolation

### Process Isolation

Each function execution runs in a separate Docker container:

```yaml
docker run \
  --network none              # No network access
  --read-only                 # Read-only filesystem
  --tmpfs /tmp:size=100M      # Writable temp only
  --user 1000:1000            # Non-root user
  --security-opt \
    no-new-privileges         # No privilege escalation
  [...]
```

### Resource Limits

Hard limits enforced at container level:

| Resource | Limit | Notes |
|----------|-------|-------|
| Memory | 4096 MB | Kill process on exceed |
| CPU | 4.0 vCPU | Throttle on exceed |
| Timeout | 900s (15 min) | Force kill after timeout |

### Filesystem Isolation

```
Readable:
  - /function (function code, read-only)
  - /runtime (language runtime, read-only)

Writable:
  - /tmp (100 MB limit)

No Access:
  - /etc (system files)
  - /sys (kernel interfaces)
  - /proc (process interfaces)
  - Host filesystem
```

### Network Isolation

By default: **No network access**

Optional for specific use cases:
```json
{
  "function_id": "...",
  "allow_network": true,
  "allowed_domains": ["api.example.com", "cdn.example.com"]
}
```

Even with network enabled:
- No DNS rebinding allowed
- Private IP ranges blocked
- Rate limiting per destination

## Secrets Management

### Environment Variables

Secrets stored encrypted in database:

```json
{
  "env_vars": {
    "API_KEY": "encrypted-value-here",
    "DB_PASSWORD": "encrypted-value-here"
  }
}
```

**Encryption:**
- Algorithm: AES-256-GCM
- Key: Derived from `SECRET_KEY`
- Rotated on key change

### Secrets Access

Secrets injected at runtime:

```python
def handler(event):
    import os
    api_key = os.getenv('API_KEY')  # Available at runtime
    # API_KEY never logged or exposed
    return {'status': 'ok'}
```

### Best Practices

1. **Never log secrets:**
   ```python
   # Bad
   print(f"API_KEY={api_key}")

   # Good
   print(f"API_KEY=***")
   ```

2. **Never commit secrets:**
   ```bash
   # Use environment variables only
   API_KEY=$(grep API_KEY .env)
   zip -r function.zip *.py -x ".env"
   ```

3. **Rotate regularly:**
   - Update secrets in function config
   - Re-deploy function
   - Delete old secrets from backups

4. **Audit secret access:**
   - Logs show when secrets accessed
   - Monitor for unexpected access
   - Alert on anomalies

## Rate Limiting

### API Rate Limits

**Per User/Token:**
- 1000 requests per hour (default)
- Configurable per scope
- Returns HTTP 429 if exceeded

**Per Function Webhook:**
- 100 requests per hour (default)
- Configurable per function
- Sliding window counter in Redis

**Implementation:**
```python
# Redis sorted set for sliding window
Key: iceruns:ratelimit:{function_id}
Values: Timestamps of requests
TTL: 1 hour
```

### Handling Rate Limits

```bash
# Response includes retry information
HTTP 429 Too Many Requests

{
  "error": "rate_limit_exceeded",
  "limit": 100,
  "window_seconds": 3600,
  "retry_after": 1800
}
```

**Retry Strategy:**
```python
import time

def call_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, ...)
            if response.status_code == 429:
                retry_after = int(response.headers['Retry-After'])
                time.sleep(retry_after)
                continue
            return response
        except Exception as e:
            time.sleep(2 ** attempt)
    raise Exception("Max retries exceeded")
```

## Network Security

### TLS/HTTPS

All communication must use HTTPS:

```bash
# Enforce HTTPS in deployment
curl -H "X-Forwarded-Proto: https" \
  https://your-icecharts.com/api/v1/iceruns
```

**Configuration:**
```yaml
# Kubernetes ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: iceruns-tls
spec:
  tls:
  - hosts:
    - your-icecharts.com
    secretName: tls-secret
  rules:
  - host: your-icecharts.com
    http:
      paths:
      - path: /api/v1/iceruns
        backend:
          service:
            name: flask-backend
            port:
              number: 5000
```

### CORS Policy

Restrict cross-origin requests:

```yaml
CORS:
  allowed_origins: ["https://your-icecharts.com"]
  allowed_methods: ["GET", "POST", "PUT", "DELETE"]
  allowed_headers: ["Authorization", "Content-Type"]
  max_age: 3600
```

### IP Whitelisting

For webhooks, restrict by source IP:

```bash
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/webhook/config \
  -d '{
    "ip_whitelist": [
      "203.0.113.0/24",    # Production servers
      "198.51.100.42/32"   # CI/CD platform
    ]
  }'
```

### VPC/Network Isolation

For private deployments:

```yaml
# Kubernetes network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: iceruns-network-policy
  namespace: iceruns
spec:
  podSelector:
    matchLabels:
      app: iceruns-invoker
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: icecharts
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 9000  # MinIO
```

## Audit Logging

### Logged Events

All operations logged with:
- Timestamp
- User/Service Account
- Action (create, execute, delete, etc.)
- Resource (function_id, execution_id)
- Result (success/failure)
- Source IP

### Log Format

```json
{
  "timestamp": "2026-01-20T12:00:00Z",
  "event": "function_execute",
  "user_id": "user-123",
  "function_id": "f7e8d9c0-...",
  "execution_id": "e1a2b3c4-...",
  "source_ip": "203.0.113.42",
  "user_agent": "curl/7.64.1",
  "result": "success",
  "status_code": 200
}
```

### Audit Trail

Query execution history:
```bash
# Get all executions for function
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/{function_id}/executions?limit=1000"

# Filter by date range
curl -H "Authorization: Bearer {token}" \
  "https://your-icecharts.com/api/v1/iceruns/executions?from=2026-01-01&to=2026-01-31"
```

### Log Aggregation

Send logs to centralized system:

```yaml
# Example: ELK Stack
filebeat:
  prospectors:
  - type: log
    enabled: true
    paths:
      - /var/log/iceruns/*.log
    output.elasticsearch:
      hosts: ["elasticsearch:9200"]
```

## Vulnerability Management

### Dependency Scanning

Regular security updates:

```bash
# Check Python dependencies
cd services/iceruns-invoker
safety check requirements.txt

# Check Docker image vulnerabilities
trivy image icecharts/iceruns-invoker:latest
```

### Container Image Security

```dockerfile
# Use specific version tags (not 'latest')
FROM debian:12.1-slim

# Run as non-root user
RUN useradd -u 1000 -m iceruns
USER 1000:1000

# Remove unnecessary tools
RUN apt-get remove -y curl wget
```

### Code Security

```bash
# Python code security scan
bandit -r app/

# Static analysis
mypy app/
pylint app/
```

## Secrets Rotation

### Scheduled Rotation

1. **Database Secrets:**
   - Rotate database password quarterly
   - Update connection strings
   - Test before deployment

2. **Webhook Tokens:**
   - Regenerate quarterly
   - Update external systems
   - Remove old tokens after grace period

3. **TLS Certificates:**
   - Rotate annually
   - Use short-lived certificates (90 days)
   - Automate renewal (Let's Encrypt)

### Emergency Rotation

```bash
# Immediately disable function
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/pause \
  -H "Authorization: Bearer {token}"

# Regenerate webhook token
curl -X POST https://your-icecharts.com/api/v1/iceruns/{id}/webhook/regenerate \
  -H "Authorization: Bearer {token}"

# Update external systems with new token

# Re-enable function
curl -X PUT https://your-icecharts.com/api/v1/iceruns/{id}/activate \
  -H "Authorization: Bearer {token}"
```

## Threat Model

### Threats Mitigated

| Threat | Mitigation |
|--------|-----------|
| Function code injection | Input validation, sandboxing |
| Secret exposure | Encryption, restricted access, audit logs |
| Unauthorized execution | Authentication, authorization, rate limiting |
| Resource exhaustion | Memory limits, CPU limits, timeout |
| Container escape | Security options, read-only filesystem |
| Network-based attacks | TLS encryption, IP whitelisting, CORS |
| DDoS | Rate limiting, load balancing, IP filtering |
| Privilege escalation | Non-root execution, no new privileges |

### Defense Layers

```
1. Network Layer
   - TLS encryption
   - IP whitelisting
   - CORS policy

2. API Layer
   - Authentication (JWT/tokens)
   - Authorization (scopes)
   - Rate limiting
   - Input validation

3. Execution Layer
   - Container isolation
   - Resource limits
   - Filesystem restrictions
   - Network isolation

4. Data Layer
   - Secrets encryption
   - Secure storage
   - Audit logging

5. Operations Layer
   - Security scanning
   - Vulnerability management
   - Access control
   - Incident response
```

## Security Checklist

- [ ] HTTPS/TLS enabled
- [ ] JWT tokens configured
- [ ] Scopes enforced
- [ ] Database password secured
- [ ] Redis password configured
- [ ] MinIO credentials secure
- [ ] Webhook tokens generated
- [ ] HMAC validation enabled
- [ ] IP whitelisting configured
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] Security scanning running
- [ ] Secrets rotation scheduled
- [ ] Backup encryption enabled
- [ ] Access control documented

## Incident Response

### Security Incident

1. **Identify**: Monitor alerts for suspicious activity
2. **Contain**: Disable function/token if necessary
3. **Investigate**: Check audit logs, execution history
4. **Remediate**: Rotate secrets, update code
5. **Verify**: Test fix, monitor for recurrence
6. **Communicate**: Document incident, notify users

### Common Incidents

**Leaked Webhook Token:**
```bash
# Immediately regenerate
curl -X POST .../webhook/regenerate

# Update external systems
# Monitor for unauthorized access
```

**Compromised Service Account:**
```bash
# Revoke compromised token
# Create new token with audit
# Review execution history
# Update systems using token
```

**Unauthorized API Access:**
```bash
# Review audit logs for IP/user
# Revoke suspicious tokens
# Update firewall rules
# Force password reset
```

---

See also:
- [Architecture](./architecture.md)
- [Deployment](./deployment.md)
- [Troubleshooting](./troubleshooting.md)
