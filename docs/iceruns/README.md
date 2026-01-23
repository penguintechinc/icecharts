# IceRuns - Serverless Function Execution Platform

IceRuns is a production-ready serverless function execution platform for IceCharts, inspired by Apache OpenWhisk architecture. Execute functions in multiple languages via authenticated webhooks, API calls, or scheduled triggers with container-based isolation, warm/cold start optimization, and real-time execution tracking.

## Key Features

- **Multi-Language Support**: Python 3.13, Node.js 20, Go 1.23, Ruby 3.3, Bash 5.2, PowerShell 7.4, Rust 1.75
- **Multiple Trigger Types**: API calls, webhooks, scheduled (cron), and manual execution
- **OpenWhisk-Inspired Architecture**: Controller/Invoker pattern with Redis Streams queue
- **Container Isolation**: Docker-based sandboxing with resource limits and security hardening
- **Warm/Cold Start Optimization**: Container reuse with configurable TTL
- **Real-Time Execution Tracking**: WebSocket support for live status updates
- **Scope-Based Authorization**: Fine-grained `iceruns:*` scopes for multi-tenant security
- **S3/MinIO Storage**: Function packages and execution artifacts
- **IceStreams Integration**: Execute functions as nodes in playbooks
- **Comprehensive Audit Logging**: Full execution history with metrics
- **Multi-Architecture Support**: ARM64 and AMD64 deployments

## Quick Start

### 1. Create Your First Function

```python
# main.py
def handler(event):
    name = event.get('name', 'World')
    return {
        'message': f'Hello, {name}!',
        'status': 'success'
    }
```

### 2. Upload via WebUI

1. Navigate to **IceRuns** → **Create Function**
2. Enter name: "Hello World"
3. Select runtime: **Python 3.13**
4. Set entrypoint: `main.py`
5. Set handler: `main.handler`
6. Upload `main.py`
7. Click **Activate**

### 3. Test via Webhook

```bash
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{token} \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

Response:
```json
{
  "execution_id": "e1a2b3c4-...",
  "status": "completed",
  "output": {
    "message": "Hello, Alice!",
    "status": "success"
  }
}
```

## Architecture Overview

```
┌───────────────────────────────────────────────────┐
│             WebUI (React Interface)               │
│                                                   │
│ - Function Management & Upload                    │
│ - Execution History & Logs                        │
│ - Real-time Status Updates                        │
└───────────────────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────┐
│      IceRuns Controller (Flask Backend)           │
│                                                   │
│ - REST API (/api/v1/iceruns/*)                   │
│ - Authentication & Authorization                  │
│ - Function Metadata Management                    │
│ - Webhook Token Handling                          │
└───────────────────────────────────────────────────┘
                         │
                         ▼
                   Redis Streams
                  (Task Queue)
                         │
                         ▼
┌───────────────────────────────────────────────────┐
│    IceRuns Invoker (Worker Pool)                 │
│                                                   │
│ - Consumes tasks from queue                       │
│ - Manages container lifecycle                     │
│ - Executes functions in sandboxed containers     │
│ - Stores results in database                      │
└───────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │ Python │      │ Node.js│      │  Go    │
    │ 3.13   │      │   20   │      │  1.23  │
    └────────┘      └────────┘      └────────┘
```

## Core Concepts

### Functions
User-created, deployable code units that can be triggered via webhooks, APIs, or schedules. Each function has:
- **Runtime**: Language and version (python3.13, nodejs, go, ruby, bash, powershell, rust)
- **Package**: ZIP file or source code uploaded to S3/MinIO
- **Handler**: Entry point function name (e.g., `main.handler`)
- **Configuration**: Memory, CPU, timeout, environment variables, secrets

### Executions
Individual function invocations with complete lifecycle tracking:
- **Status**: queued, running, completed, failed, timeout, cancelled
- **Input/Output**: JSON data and results
- **Logs**: stdout/stderr capture
- **Metrics**: Duration, memory usage, CPU time

### Webhooks
Public, token-authenticated endpoints for triggering functions externally:
- **Token**: Bearer token for authentication
- **HMAC Signature**: Optional request signing
- **Rate Limiting**: Per-function request limits
- **IP Whitelisting**: Restrict by source IP CIDR blocks

### Scopes
Authorization system for multi-tenant security:
- `iceruns:read` - View functions
- `iceruns:write` - Create/update functions
- `iceruns:delete` - Delete functions
- `iceruns:execute` - Trigger executions
- `iceruns:logs` - View execution logs
- `iceruns:admin` - Full administrative access

## Documentation

- **[Quickstart](./quickstart.md)** - 5-minute introduction
- **[Architecture](./architecture.md)** - Deep dive into the OpenWhisk-inspired design
- **[Runtimes](./runtimes.md)** - Language-specific guides and examples
- **[API Reference](./api-reference.md)** - Complete REST API documentation
- **[Webhooks](./webhook-guide.md)** - Webhook integration and security
- **[Scheduling](./scheduling.md)** - Cron scheduling and timezones
- **[IceStreams Integration](./icestreams-integration.md)** - Using IceRuns in playbooks
- **[Deployment](./deployment.md)** - Kubernetes and Docker deployment
- **[Security](./security.md)** - Container isolation and best practices
- **[Troubleshooting](./troubleshooting.md)** - Common issues and solutions

## Examples

Complete working examples in 7 languages in the `examples/` directory:
- [Python Hello World](./examples/python-hello-world/)
- [Node.js Image Resize](./examples/nodejs-image-resize/)
- [Go Data Processing](./examples/go-data-processing/)
- [Ruby API Scraper](./examples/ruby-api-scraper/)
- [Bash File Converter](./examples/bash-file-converter/)
- [PowerShell Azure Automation](./examples/powershell-azure-automation/)
- [Rust High Performance](./examples/rust-high-performance/)

## Authentication

All API calls require authentication via:

**Bearer Token (JWT):**
```bash
curl -H "Authorization: Bearer <token>" \
  https://your-icecharts.com/api/v1/iceruns
```

**Service Account Token:**
```bash
# For service-to-service integration
curl -H "Authorization: Bearer <service-account-token>" \
  https://your-icecharts.com/api/v1/iceruns/{id}/execute
```

**Webhook Token (Public):**
```bash
# No authorization header needed for webhooks
curl -X POST https://your-icecharts.com/api/v1/iceruns/hook/{webhook-token} \
  -d '{"data": "value"}'
```

## Deployment

### Docker Compose (Development)
```bash
docker-compose up -d iceruns-invoker
```

### Kubernetes (Production)
```bash
kubectl create namespace iceruns
kubectl apply -f k8s/iceruns/
```

See [Deployment Guide](./deployment.md) for detailed instructions.

## Monitoring

IceRuns exports Prometheus metrics:
- `iceruns_executions_total` - Total executions by runtime and status
- `iceruns_execution_duration_seconds` - Execution time distribution
- `iceruns_execution_memory_mb` - Memory usage by runtime
- `iceruns_active_executions` - Currently running functions
- `iceruns_queue_size` - Tasks waiting in queue
- `iceruns_execution_errors_total` - Execution failures

Access metrics at `/metrics` endpoint.

## Performance

- **Cold Start**: 500ms - 2s (language dependent)
- **Warm Start**: 50ms - 200ms
- **Max Timeout**: 15 minutes (900 seconds)
- **Max Memory**: 4096 MB
- **Max CPU**: 4.0 vCPUs
- **Concurrent Functions**: Unlimited (scales horizontally)

## Limits & Quotas

| Resource | Default | Max |
|----------|---------|-----|
| Function Package Size | 512 MB | 512 MB |
| Execution Timeout | 60s | 900s (15 min) |
| Memory Per Execution | 128 MB | 4096 MB |
| CPU Per Execution | 0.5 vCPU | 4.0 vCPU |
| Webhook Rate Limit | 100 req/hour | Configurable |
| Concurrent Invokers | Auto-scale | 10+ recommended |

## Support

- **Documentation**: See links above
- **Issues**: Check [Troubleshooting](./troubleshooting.md)
- **Community**: [GitHub Discussions](https://github.com/penguin-tech/icecharts)
- **Email**: support@penguintech.io

## License

IceCharts and IceRuns are licensed under Limited AGPL3 with preamble for fair use.
See LICENSE file in repository root.

---

**IceRuns v1.4.0** | Part of IceCharts serverless platform | [Penguin Tech Inc](https://www.penguintech.io)
