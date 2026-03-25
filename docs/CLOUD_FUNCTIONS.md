# IceStreams Cloud Function Integration Guide

Complete guide for integrating cloud functions, webhooks, and external services with IceStreams playbooks.

## Table of Contents

1. [Overview](#overview)
2. [Webhook Integration](#webhook-integration)
3. [Authentication Methods](#authentication-methods)
4. [Cloud Provider Setup](#cloud-provider-setup)
5. [Example Playbooks](#example-playbooks)
6. [Troubleshooting](#troubleshooting)

---

## Overview

IceStreams supports calling external cloud functions and webhooks from playbook workflows using the **HTTP Request** and **Webhook Out** action nodes. These nodes support:

- Multiple authentication methods (OAuth2, OIDC, API keys, Bearer tokens)
- Cloud provider integrations (AWS Lambda, GCP Cloud Run, Azure Functions, OpenWhisk)
- Request/response transformation
- Automatic retries with exponential backoff
- Comprehensive error handling

### Supported Cloud Providers

| Provider | Service | Authentication | URL Pattern |
|----------|---------|---------------|-------------|
| AWS | Lambda Function URLs | IAM (SigV4), API Key | `https://<id>.lambda-url.<region>.on.aws/` |
| GCP | Cloud Run | OIDC, API Key | `https://<service>-<hash>-<region>.run.app` |
| Azure | Functions | Code/Key, OAuth2 | `https://<app>.azurewebsites.net/api/<function>` |
| Apache OpenWhisk | Actions | Basic Auth, API Key | `https://<host>/api/v1/namespaces/<ns>/actions/<action>` |

---

## Webhook Integration

### Basic Webhook Request

Use the **HTTP Request** node to call external webhooks:

```json
{
  "nodeType": "http_request",
  "config": {
    "method": "POST",
    "url": "https://api.example.com/webhook",
    "headers": {
      "Content-Type": "application/json",
      "X-Custom-Header": "value"
    },
    "body": {
      "event": "{{trigger.event}}",
      "data": "{{input.data}}"
    },
    "timeout": 30,
    "retries": 3,
    "retry_delay": 1
  }
}
```

### Webhook Payload Format

Standard webhook payload structure sent by IceStreams:

```json
{
  "event": "workflow.executed",
  "timestamp": "2025-12-19T14:30:00Z",
  "execution_id": "exec-uuid-1234",
  "playbook_id": "pb-uuid-5678",
  "data": {
    "result": "success",
    "outputs": {
      "processed_items": 42,
      "status": "completed"
    }
  },
  "metadata": {
    "source": "icestreams",
    "version": "1.0"
  }
}
```

### Response Handling

IceStreams expects webhook responses in the following format:

```json
{
  "success": true,
  "data": {
    "confirmation_id": "conf-123",
    "message": "Webhook processed successfully"
  },
  "errors": []
}
```

**Status Codes:**
- `200-299`: Success (data extracted from response body)
- `400-499`: Client error (workflow continues or fails based on configuration)
- `500-599`: Server error (automatic retry with exponential backoff)

---

## Authentication Methods

### 1. API Key Authentication

**Header-based API Key:**

```json
{
  "nodeType": "http_request",
  "config": {
    "url": "https://api.example.com/endpoint",
    "auth": {
      "type": "api_key",
      "api_key": "{{secrets.api_key}}",
      "header_name": "X-API-Key"
    }
  }
}
```

**Query Parameter API Key:**

```json
{
  "auth": {
    "type": "api_key",
    "api_key": "{{secrets.api_key}}",
    "param_name": "apikey"
  }
}
```

### 2. Bearer Token Authentication

```json
{
  "auth": {
    "type": "bearer",
    "token": "{{secrets.bearer_token}}"
  }
}
```

### 3. Basic Authentication

```json
{
  "auth": {
    "type": "basic",
    "username": "{{secrets.username}}",
    "password": "{{secrets.password}}"
  }
}
```

### 4. OAuth2 Client Credentials

For service-to-service authentication:

```json
{
  "auth": {
    "type": "oauth2_client_credentials",
    "client_id": "{{secrets.oauth_client_id}}",
    "client_secret": "{{secrets.oauth_client_secret}}",
    "token_url": "https://oauth.example.com/token",
    "scopes": ["read", "write"]
  }
}
```

### 5. OAuth2 Authorization Code (with refresh)

```json
{
  "auth": {
    "type": "oauth2_code",
    "client_id": "{{secrets.oauth_client_id}}",
    "client_secret": "{{secrets.oauth_client_secret}}",
    "access_token": "{{secrets.access_token}}",
    "refresh_token": "{{secrets.refresh_token}}",
    "token_url": "https://oauth.example.com/token"
  }
}
```

### 6. OIDC (OpenID Connect)

For Google Cloud Run and similar services:

```json
{
  "auth": {
    "type": "oidc",
    "audience": "https://my-service-abc123.run.app",
    "service_account_json": "{{secrets.gcp_service_account}}"
  }
}
```

### 7. AWS Signature V4 (IAM)

For AWS Lambda and API Gateway:

```json
{
  "auth": {
    "type": "aws_sigv4",
    "access_key_id": "{{secrets.aws_access_key_id}}",
    "secret_access_key": "{{secrets.aws_secret_access_key}}",
    "region": "us-east-1",
    "service": "lambda"
  }
}
```

---

## Cloud Provider Setup

### AWS Lambda Function URLs

#### 1. Enable Function URL

```bash
aws lambda create-function-url-config \
  --function-name my-function \
  --auth-type AWS_IAM
```

#### 2. Configure IceStreams Node

```json
{
  "nodeType": "http_request",
  "config": {
    "method": "POST",
    "url": "https://abc123def.lambda-url.us-east-1.on.aws/",
    "auth": {
      "type": "aws_sigv4",
      "access_key_id": "{{secrets.aws_access_key}}",
      "secret_access_key": "{{secrets.aws_secret_key}}",
      "region": "us-east-1",
      "service": "lambda"
    },
    "body": {
      "event": "playbook_executed",
      "data": "{{input.data}}"
    }
  }
}
```

#### 3. Lambda Handler Example (Python)

```python
import json

def lambda_handler(event, context):
    """Handle IceStreams webhook."""
    body = json.loads(event.get('body', '{}'))

    # Process the IceStreams data
    event_type = body.get('event')
    data = body.get('data', {})

    # Your processing logic here
    result = process_data(data)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'success': True,
            'data': result
        })
    }
```

---

### Google Cloud Run

#### 1. Deploy Cloud Run Service

```bash
gcloud run deploy my-service \
  --image gcr.io/my-project/my-image \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated  # Or use --no-allow-unauthenticated for auth
```

#### 2. Create Service Account (for authenticated calls)

```bash
# Create service account
gcloud iam service-accounts create icestreams-caller \
  --display-name="IceStreams Service Account"

# Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding my-service \
  --member="serviceAccount:icestreams-caller@my-project.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region=us-central1

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account=icestreams-caller@my-project.iam.gserviceaccount.com
```

#### 3. Configure IceStreams Node (Authenticated)

```json
{
  "nodeType": "http_request",
  "config": {
    "method": "POST",
    "url": "https://my-service-abc123-uc.run.app/webhook",
    "auth": {
      "type": "oidc",
      "audience": "https://my-service-abc123-uc.run.app",
      "service_account_json": "{{secrets.gcp_service_account}}"
    },
    "body": {
      "event": "{{trigger.event}}",
      "data": "{{input.data}}"
    }
  }
}
```

#### 4. Cloud Run Service Example (Python/Flask)

```python
from flask import Flask, request, jsonify
import google.auth.transport.requests
import google.oauth2.id_token

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify OIDC token (if using authentication)
    auth_req = google.auth.transport.requests.Request()
    id_token = request.headers.get('Authorization', '').replace('Bearer ', '')

    try:
        claims = google.oauth2.id_token.verify_token(id_token, auth_req)
        print(f"Authenticated request from: {claims.get('email')}")
    except Exception as e:
        return jsonify({'error': 'Authentication failed'}), 401

    # Process webhook data
    data = request.json
    event = data.get('event')
    payload = data.get('data', {})

    # Your processing logic
    result = process_webhook(event, payload)

    return jsonify({
        'success': True,
        'data': result
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

---

### Azure Functions

#### 1. Create Function App

```bash
az functionapp create \
  --resource-group myResourceGroup \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name my-function-app \
  --storage-account mystorageaccount
```

#### 2. Get Function Key

```bash
az functionapp function keys list \
  --name my-function-app \
  --resource-group myResourceGroup \
  --function-name MyHttpTrigger
```

#### 3. Configure IceStreams Node

```json
{
  "nodeType": "http_request",
  "config": {
    "method": "POST",
    "url": "https://my-function-app.azurewebsites.net/api/MyHttpTrigger",
    "auth": {
      "type": "api_key",
      "api_key": "{{secrets.azure_function_key}}",
      "param_name": "code"
    },
    "body": {
      "event": "{{trigger.event}}",
      "data": "{{input.data}}"
    }
  }
}
```

#### 4. Azure Function Example (Python)

```python
import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle IceStreams webhook."""
    try:
        req_body = req.get_json()
        event = req_body.get('event')
        data = req_body.get('data', {})

        # Process webhook
        result = process_data(event, data)

        return func.HttpResponse(
            json.dumps({
                'success': True,
                'data': result
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            mimetype="application/json",
            status_code=500
        )
```

---

### Apache OpenWhisk

#### 1. Create Action

```bash
# Create action from code
wsk action create myAction myAction.js

# Or from Docker image
wsk action create myAction --docker myimage:latest
```

#### 2. Create Web Action (for HTTP access)

```bash
wsk action update myAction --web true
```

#### 3. Get Action URL

```bash
wsk action get myAction --url
# Returns: https://openwhisk.example.com/api/v1/web/namespace/default/myAction
```

#### 4. Configure IceStreams Node

```json
{
  "nodeType": "http_request",
  "config": {
    "method": "POST",
    "url": "https://openwhisk.example.com/api/v1/web/myorg/default/myAction.json",
    "auth": {
      "type": "basic",
      "username": "{{secrets.openwhisk_user}}",
      "password": "{{secrets.openwhisk_password}}"
    },
    "body": {
      "event": "{{trigger.event}}",
      "data": "{{input.data}}"
    }
  }
}
```

#### 5. OpenWhisk Action Example (Node.js)

```javascript
function main(params) {
  const event = params.event;
  const data = params.data || {};

  // Process IceStreams webhook
  const result = processData(event, data);

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: {
      success: true,
      data: result
    }
  };
}

exports.main = main;
```

---

## Example Playbooks

### Example 1: Trigger Lambda on Schedule

```json
{
  "name": "Daily Lambda Execution",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger_schedule",
      "config": {
        "cron": "0 9 * * *",
        "timezone": "America/New_York"
      }
    },
    {
      "id": "lambda-1",
      "type": "http_request",
      "config": {
        "method": "POST",
        "url": "https://abc123.lambda-url.us-east-1.on.aws/",
        "auth": {
          "type": "aws_sigv4",
          "access_key_id": "{{secrets.aws_key}}",
          "secret_access_key": "{{secrets.aws_secret}}",
          "region": "us-east-1",
          "service": "lambda"
        },
        "body": {
          "task": "daily_report",
          "timestamp": "{{trigger.timestamp}}"
        }
      }
    },
    {
      "id": "log-1",
      "type": "log",
      "config": {
        "level": "info",
        "message": "Lambda invoked: {{lambda-1.response.data}}"
      }
    }
  ],
  "edges": [
    { "source": "trigger-1", "target": "lambda-1" },
    { "source": "lambda-1", "target": "log-1" }
  ]
}
```

### Example 2: Call GCP Cloud Run with Authentication

```json
{
  "name": "Process Data with Cloud Run",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger_webhook",
      "config": {
        "path": "/process"
      }
    },
    {
      "id": "cloudrun-1",
      "type": "http_request",
      "config": {
        "method": "POST",
        "url": "https://data-processor-xyz.run.app/process",
        "auth": {
          "type": "oidc",
          "audience": "https://data-processor-xyz.run.app",
          "service_account_json": "{{secrets.gcp_sa}}"
        },
        "body": {
          "records": "{{trigger.body.records}}"
        },
        "timeout": 60
      }
    },
    {
      "id": "response-1",
      "type": "webhook_response",
      "config": {
        "status_code": 200,
        "body": {
          "processed": "{{cloudrun-1.response.data.count}}",
          "result": "{{cloudrun-1.response.data.result}}"
        }
      }
    }
  ],
  "edges": [
    { "source": "trigger-1", "target": "cloudrun-1" },
    { "source": "cloudrun-1", "target": "response-1" }
  ]
}
```

### Example 3: Multi-Cloud Function Chain

```json
{
  "name": "Multi-Cloud Processing Pipeline",
  "nodes": [
    {
      "id": "trigger-1",
      "type": "trigger_webhook"
    },
    {
      "id": "aws-validate",
      "type": "http_request",
      "config": {
        "method": "POST",
        "url": "https://validator.lambda-url.us-east-1.on.aws/",
        "auth": { "type": "aws_sigv4", "...": "..." },
        "body": { "data": "{{trigger.body}}" }
      }
    },
    {
      "id": "gcp-process",
      "type": "http_request",
      "config": {
        "method": "POST",
        "url": "https://processor.run.app/process",
        "auth": { "type": "oidc", "...": "..." },
        "body": { "validated": "{{aws-validate.response.data}}" }
      }
    },
    {
      "id": "azure-store",
      "type": "http_request",
      "config": {
        "method": "POST",
        "url": "https://storage-func.azurewebsites.net/api/store",
        "auth": { "type": "api_key", "...": "..." },
        "body": { "result": "{{gcp-process.response.data}}" }
      }
    }
  ],
  "edges": [
    { "source": "trigger-1", "target": "aws-validate" },
    { "source": "aws-validate", "target": "gcp-process" },
    { "source": "gcp-process", "target": "azure-store" }
  ]
}
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

**Symptom:** `401 Unauthorized` or `403 Forbidden` responses

**Solutions:**

- **AWS SigV4**: Verify IAM permissions and credentials
  ```bash
  aws lambda get-function-url-config --function-name my-function
  ```

- **GCP OIDC**: Check service account has `roles/run.invoker`
  ```bash
  gcloud run services get-iam-policy my-service --region=us-central1
  ```

- **API Keys**: Verify key is active and has correct permissions

#### 2. Timeout Errors

**Symptom:** Request times out before completion

**Solutions:**

- Increase `timeout` in node configuration (default: 30s)
- Check cloud function cold start time
- Implement async processing with callback pattern
- Enable keep-alive for connection reuse

#### 3. Certificate/SSL Errors

**Symptom:** SSL verification failures

**Solutions:**

- Ensure valid SSL certificate on endpoint
- Add `verify_ssl: true` to config (enabled by default)
- Check certificate chain and intermediate certificates

#### 4. Payload Size Limits

**Symptom:** `413 Payload Too Large` errors

**Limits by Provider:**
- AWS Lambda: 6 MB (synchronous), 256 KB (async)
- GCP Cloud Run: 32 MB
- Azure Functions: 100 MB

**Solutions:**
- Compress payload data
- Use multipart uploads for large data
- Store large data in object storage, pass reference

#### 5. Rate Limiting

**Symptom:** `429 Too Many Requests` responses

**Solutions:**

- Implement exponential backoff (built into HTTP Request node)
- Configure `retry_delay` and `max_retries`
- Add delay nodes between requests
- Use cloud provider quotas and rate limit configurations

### Debug Logging

Enable detailed logging in playbook configuration:

```json
{
  "config": {
    "debug_mode": true,
    "log_level": "DEBUG"
  }
}
```

### Testing Cloud Functions Locally

Use local emulators for testing:

```bash
# AWS SAM Local
sam local start-api

# GCP Functions Framework
functions-framework --target=my_function --debug

# Azure Functions Core Tools
func start
```

### Webhook Testing Tools

- **ngrok**: Expose local services for webhook testing
  ```bash
  ngrok http 5000
  ```

- **Postman**: Test webhook payloads and responses

- **RequestBin**: Inspect webhook requests
  ```
  https://requestbin.com/
  ```

---

## Security Best Practices

1. **Store credentials in secrets manager**
   - Use `{{secrets.key_name}}` template syntax
   - Never hardcode credentials in playbooks

2. **Use least privilege IAM policies**
   - Grant only required permissions
   - Use service accounts with limited scope

3. **Enable SSL verification**
   - Always use HTTPS endpoints
   - Verify SSL certificates (default: enabled)

4. **Implement request signing**
   - Use AWS SigV4 for AWS services
   - Use OIDC tokens for GCP

5. **Validate webhook signatures**
   - Verify incoming webhook authenticity
   - Use HMAC signatures or JWT tokens

6. **Rate limit webhook endpoints**
   - Prevent abuse and DDoS
   - Use cloud provider rate limiting

7. **Monitor and audit**
   - Log all external function calls
   - Track authentication attempts
   - Set up alerting for failures

---

## Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Azure Functions Documentation](https://docs.microsoft.com/azure/azure-functions/)
- [Apache OpenWhisk Documentation](https://openwhisk.apache.org/documentation.html)
- [IceStreams Node Reference](./NODE_REFERENCE.md)
- [IceStreams Security Guide](./SECURITY.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
**Maintained by:** Penguin Tech Inc
