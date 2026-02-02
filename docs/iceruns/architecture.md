# IceRuns Architecture

IceRuns implements the Apache OpenWhisk-inspired Controller/Invoker pattern for serverless function execution.

## High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│                          Users/Webhooks                         │
│                    (External Triggers)                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │   IceRuns Controller       │
                  │   (Flask Backend)          │
                  │                            │
                  │ - REST API (/api/v1/...)  │
                  │ - Authentication & Authz  │
                  │ - Function Metadata (DB)  │
                  │ - Webhook Validation      │
                  │ - Package Upload (S3)     │
                  │ - Rate Limiting (Redis)   │
                  │ - Return Activation ID    │
                  │   (non-blocking)          │
                  └────────────────────────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │   Redis Streams Queue      │
                  │   (iceruns:tasks)          │
                  │                            │
                  │ - Persistent task queue    │
                  │ - Survives restarts        │
                  │ - Consumer groups (workers)│
                  │ - Real-time pub/sub events │
                  └────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
         ┌──────────────────────┐  ┌──────────────────────┐
         │  Invoker Worker 1    │  │  Invoker Worker N    │
         │  (Horizontal Scale)  │  │  (Horizontal Scale)  │
         │                      │  │                      │
         │ - Consume from queue │  │ - Consume from queue │
         │ - Download package   │  │ - Download package   │
         │ - Manage containers  │  │ - Manage containers  │
         │ - Execute function   │  │ - Execute function   │
         │ - Capture logs       │  │ - Capture logs       │
         │ - Store results (DB) │  │ - Store results (DB) │
         │ - Update status      │  │ - Update status      │
         └──────────────────────┘  └──────────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               ▼
                  ┌────────────────────────────┐
                  │   Container Execution      │
                  │                            │
                  │  Docker containers with:   │
                  │  - Resource limits         │
                  │  - Filesystem isolation    │
                  │  - Network isolation       │
                  │  - Security constraints    │
                  │  - Warm container reuse    │
                  │  - Cold start (new image)  │
                  └────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
            ┌────────┐   ┌────────┐   ┌────────┐
            │ Python │   │Node.js │   │  Go    │
            │ 3.13   │   │   20   │   │  1.23  │
            └────────┘   └────────┘   └────────┘
```

## Request Flow

### 1. Function Creation/Update
```
User → WebUI or API
  ↓
Controller validates input
  ↓
Package uploaded to S3/MinIO
  ↓
Function metadata stored in PostgreSQL/MySQL
  ↓
Webhook token generated
  ↓
Return function_id and webhook_url
```

### 2. Execution Request
```
User/Webhook/Schedule → Controller
  ↓
1. Validate authentication & authorization
2. Check rate limits (Redis)
3. Validate input data
4. Load function config from DB
5. Create execution record (status: queued)
6. Enqueue task to Redis Stream
7. Return execution_id immediately (non-blocking)
  ↓
[Response sent to caller]
```

### 3. Task Processing (Asynchronous)
```
Invoker pool polls Redis Stream
  ↓
Worker picks up task (least-loaded consumer)
  ↓
1. Update status to "running"
2. Download package from S3
3. Check for warm container (memory pool)
   - If warm: reuse container (50ms)
   - If cold: create new container (500ms-2s)
4. POST to /init endpoint (if cold start)
5. POST to /run endpoint with input
6. Capture stdout/stderr
7. Collect resource metrics
8. Store results in database
9. Update status to "completed" or "failed"
10. Publish completion event to Redis Pub/Sub
11. Clean up container (for reuse or discard)
  ↓
Caller can poll status API or WebSocket for results
```

## Components

### Controller (Flask Backend)

**Responsibilities:**
- REST API endpoint (`/api/v1/iceruns/*`)
- Authentication & authorization via JWT/scopes
- Function CRUD operations
- Webhook token management
- Rate limiting enforcement
- Package upload to S3
- Execution request validation
- Redis Streams message publishing
- Non-blocking response to callers

**Key Files:**
- `services/flask-backend/app/api/v1/iceruns.py` - Function management
- `services/flask-backend/app/api/v1/iceruns_executions.py` - Execution tracking
- `services/flask-backend/app/api/v1/iceruns_hooks.py` - Webhook handling

**Database Tables:**
- `iceruns` - Function definitions
- `iceruns_executions` - Execution history
- `iceruns_schedules` - Cron schedules (optional)
- `iceruns_versions` - Function versions

### Invoker (Worker Service)

**Responsibilities:**
- Consume tasks from Redis Streams
- Download function packages from S3
- Manage container lifecycle (warm/cold starts)
- Execute functions inside Docker
- Capture logs and metrics
- Handle timeouts and errors
- Store results in database
- Publish status updates to Redis Pub/Sub

**Key Files:**
- `services/iceruns-invoker/app/invoker.py` - Main worker loop
- `services/iceruns-invoker/app/action_runtime.py` - Container abstraction
- `services/iceruns-invoker/app/runtimes/` - Runtime implementations
- `services/iceruns-invoker/app/sandbox.py` - Security sandboxing

**Scalability:**
- Horizontal scaling: Add more invoker instances
- Consumer groups: Each worker is a consumer in `iceruns-workers` group
- Load balancing: Least-loaded worker picks up next task
- Auto-scaling: Kubernetes HPA scales based on queue size/CPU

### Storage (S3/MinIO)

**Object Structure:**
```
iceruns/
├── {function_id}/
│   ├── package.zip          # Current version
│   └── versions/
│       ├── v1.zip
│       ├── v2.zip
│       └── ...
├── logs/
│   ├── {execution_id}.log   # Full stdout+stderr
│   └── ...
└── artifacts/
    ├── {execution_id}/
    │   ├── output.json
    │   ├── report.pdf
    │   └── ...
    └── ...
```

**Access Methods:**
- Internal: Direct MinIO client from invoker
- External: Presigned URLs for authenticated downloads

### Redis (Message Queue & State)

**Data Structures:**

1. **Task Queue (Stream)**
   ```
   Stream: iceruns:tasks
   Message: {
     execution_id: "...",
     function_id: "...",
     input_data: {...},
     config: {...},
     timestamp: "..."
   }
   ```

2. **Status Tracking (Hash)**
   ```
   Key: iceruns:status:{execution_id}
   Value: {
     status: "running",
     started_at: "...",
     progress_percent: 45,
     stdout: "...",
     stderr: "...",
     worker_id: "...",
     error: null
   }
   ```

3. **Real-Time Events (Pub/Sub)**
   ```
   Channel: iceruns:events:{execution_id}
   Messages: Status updates published in real-time
   ```

4. **Rate Limiting (Sorted Set)**
   ```
   Key: iceruns:ratelimit:{function_id}
   Values: Timestamps of recent executions (sliding window)
   ```

### Docker Containers

**Runtime Images (Debian 12 Slim Base):**
- `python:3.13-slim` + Python 3.13
- `node:20-slim` + Node.js 20
- `golang:1.23-alpine` → custom slim image
- `ruby:3.3-slim` + Ruby 3.3
- `debian:12-slim` + Bash 5.2
- `mcr.microsoft.com/powershell:7.4-alpine` → custom slim
- `rust:1.75-slim` + Rust 1.75

**Security Configuration:**
```dockerfile
docker run \
  --network none                    # No network access
  --read-only                       # Read-only filesystem
  --tmpfs /tmp:size=100M            # Writable temp
  --memory 512m                     # Memory limit
  --memory-swap 512m                # No swap
  --cpus 0.5                        # CPU limit
  --security-opt no-new-privileges  # No privilege escalation
  -u 1000:1000                      # Non-root user
  [IMAGE] [COMMAND]
```

**Action Container Protocol (OpenWhisk):**

1. **Initialization (/init)**
   ```json
   POST /init
   {
     "code": "function source",
     "handler": "main.handler",
     "runtime": "python3.13"
   }
   Response: { "status": "ready" }
   ```

2. **Invocation (/run)**
   ```json
   POST /run
   {
     "value": {
       "param1": "value1",
       "param2": "value2"
     }
   }
   Response: {
     "result": {
       "output": "data"
     }
   }
   ```

## Warm vs Cold Starts

### Cold Start (First Execution)
1. Pull runtime image from registry (~500ms-2s)
2. Extract function package from S3
3. Create container
4. Execute /init endpoint
5. Execute /run endpoint
6. Keep container in memory for reuse

**Typical Duration:** 1-2 seconds

### Warm Start (Reused Container)
1. Check memory pool for idle container
2. If found: reuse without restart (~50ms)
3. If not: pull from registry (cold start)

**Typical Duration:** 50-200 milliseconds

**Container Reuse Policy:**
- TTL: 10 minutes (configurable)
- Memory pool: Per-worker local storage
- Cleanup: Remove when TTL expires or memory needed

## Execution Lifecycle

```
[State Machine]

1. queued
   └─> 2. running
       ├─> 3a. completed (exit_code 0)
       │   └─> 4. success
       └─> 3b. failed (exit_code != 0)
           └─> 4. error
       └─> 3c. timeout
           └─> 4. error
       └─> 3d. memory_exceeded
           └─> 4. error
```

## Authentication & Authorization

### Token Types

1. **JWT (User Token)**
   - Issued by Flask-Security-Too
   - Contains roles and scopes
   - Used for API calls
   - Scopes: iceruns:read, iceruns:write, iceruns:execute, iceruns:logs

2. **Service Account Token**
   - Long-lived (up to 1 year)
   - Scoped to specific permissions
   - Used for external integration
   - Subject to rate limiting

3. **Webhook Token**
   - Public, function-specific
   - No authentication header needed
   - Rate limited per function
   - Optional HMAC signing

### Scope Enforcement

```python
# Example: Only users with iceruns:execute can trigger functions
@auth_required()
@require_scopes(['iceruns:execute'])
def execute_function():
    ...

# Webhook calls bypass JWT but require valid token
# Rate limiting applied at function level
```

## Performance Characteristics

### Latency
- **Cold Start:** 1-2 seconds (first execution)
- **Warm Start:** 50-200 ms (reused container)
- **API Overhead:** 50-100 ms
- **Database Lookup:** 10-20 ms
- **Package Download:** 100-500 ms (depends on size)

### Throughput
- **Single Invoker:** 10-50 functions/second
- **Horizontally Scaled:** 1000s of concurrent executions
- **Queue Processing:** Automatic load balancing

### Resource Usage
- **Per Function (Memory):** 128-4096 MB
- **Per Function (CPU):** 0.1-4.0 vCPU
- **Invoker Memory:** 2-8 GB (container overhead)
- **Invoker CPU:** 1-4 vCPU (depends on concurrency)

## Failure Handling

### Timeout
- Hard kill after configured timeout (default: 60s)
- Grace period: None (immediate termination)
- Status: `timeout`
- Execution record stored with error

### Out of Memory
- Docker enforces memory limit
- Process killed by kernel
- Status: `failed`
- Error: "Out of memory"

### Container Crash
- Invoker detects non-zero exit
- Captures stderr as error
- Status: `failed`
- Full logs stored in S3

### Network Error
- Function has no network access (by default)
- If needed, configure per-function
- Errors captured in stderr

## Scalability

### Horizontal Scaling
1. **Add Invoker Instances**
   - Each becomes consumer in group
   - Auto-discovers Redis Streams
   - No configuration needed

2. **Redis Streams Load Balancing**
   - Multiple consumers in group
   - Automatic message distribution
   - No message loss (persisted)

3. **Database Replication**
   - PostgreSQL or MySQL replication
   - Connection pooling on invoker
   - Automatic failover

4. **S3/MinIO Scaling**
   - Object storage auto-scales
   - No bottleneck for package downloads
   - Presigned URLs for direct access

### Vertical Scaling
- Increase invoker concurrency setting
- Increase worker thread pool
- Increase memory/CPU per invoker

## Monitoring & Observability

### Prometheus Metrics
- `iceruns_executions_total` - Total by runtime/status
- `iceruns_execution_duration_seconds` - Latency
- `iceruns_execution_memory_mb` - Memory usage
- `iceruns_active_executions` - Current count
- `iceruns_queue_size` - Pending tasks
- `iceruns_errors_total` - Failures by type

### Structured Logging
- Function logs: stdout + stderr captured
- Execution logs: Stored in S3 for large outputs
- Error logs: Full stack traces in database
- Access logs: Audit trail in database

### Health Checks
- Invoker liveness: `/healthz` endpoint
- Database connectivity: Connection pool health
- Redis connectivity: Stream consumer lag
- S3 connectivity: Periodic upload test

---

See also:
- [Runtimes Guide](./runtimes.md) - Language-specific implementation
- [API Reference](./api-reference.md) - Endpoint documentation
- [Security](./security.md) - Security considerations
- [Deployment](./deployment.md) - Production setup
