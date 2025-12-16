# Health Check Quick Reference

## API Endpoint

```
GET /api/v1/admin/system/health
```

**Authentication:** JWT token + Admin role required

## Quick Test

```bash
# Using curl
curl -s -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/v1/admin/system/health | jq .

# Using Python
python3 << 'EOF'
import requests
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
r = requests.get("http://localhost:5000/api/v1/admin/system/health", headers=headers)
print(r.json())
EOF
```

## Response Status Meanings

| Status | HTTP Code | Meaning |
|--------|-----------|---------|
| `healthy` | 200 | All systems operational |
| `degraded` | 200 | Some systems elevated/compromised but serviceable |
| `unhealthy` | 503 | Critical system failure |

## Components Checked

1. **database** - PostgreSQL connectivity (response_time_ms, details)
2. **redis** - Redis cache connectivity (version, memory, clients)
3. **storage** - All configured storage providers (per-provider status)
4. **api** - API service status (version, environment)
5. **system** - Resource usage (CPU, memory, disk)

## Component Status Values

- `healthy` - Working normally
- `degraded` - Resources elevated but functional
- `unhealthy` - Not working
- `unknown` - Cannot determine (not configured)
- `configured` - OAuth provider configured but not testable

## Quick Response Example

```json
{
  "health": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:45.123456",
    "uptime_seconds": 3600,
    "components": {
      "database": {
        "status": "healthy",
        "response_time_ms": 5.23,
        "message": "Database connection OK"
      },
      "redis": {
        "status": "healthy",
        "response_time_ms": 2.15,
        "message": "Redis connection OK"
      },
      "storage": {
        "status": "healthy",
        "providers": [{"provider": "AWS S3", "status": "healthy"}]
      },
      "api": {
        "status": "healthy",
        "details": {"version": "0.2.0", "environment": "production"}
      },
      "system": {
        "status": "healthy",
        "details": {
          "cpu": {"usage_percent": 25.5, "count": 8},
          "memory": {"usage_percent": 45.2, "status": "healthy"},
          "disk": {"usage_percent": 62.3, "status": "healthy"}
        }
      }
    }
  }
}
```

## Status Determination Logic

```
System Status = Determined by:
├─ If ANY component unhealthy → "unhealthy" (HTTP 503)
├─ Else if 2+ components degraded → "degraded" (HTTP 200)
├─ Else if 1 component degraded → "degraded" (HTTP 200)
└─ Else all healthy → "healthy" (HTTP 200)
```

## Resource Thresholds

| Resource | Degraded | Unhealthy |
|----------|----------|-----------|
| Memory | ≥80% | >95% |
| Disk | ≥80% | >95% |

## Implementation Files

| File | Purpose |
|------|---------|
| `app/services/health_check_service.py` | Health check logic |
| `app/api/v1/admin.py` | Admin endpoint (/system/health) |
| `tests/test_health_check_service.py` | Test coverage |
| `docs/HEALTH_CHECKS.md` | Full documentation |
| `requirements.txt` | Dependencies (psutil, minio) |

## Key Features

✓ Real-time component health checks
✓ Response time tracking per component
✓ Detailed error messages
✓ System resource monitoring
✓ Graceful handling of missing dependencies
✓ Storage provider support (S3, MinIO, Google Drive, OneDrive)
✓ Redis cache verification
✓ Database connectivity testing
✓ No database migrations needed
✓ Backward compatible

## Dependencies Added

```
psutil==6.1.0         # System monitoring
minio==7.2.8          # MinIO/S3 support
```

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Redis not configured" | Set REDIS_URL env variable |
| "No storage providers" | Configure storage in admin panel |
| "psutil not installed" | `pip install psutil` |
| "401 Unauthorized" | Check JWT token validity |
| "403 Forbidden" | Ensure user has admin role |
| Database connection timeout | Check DB_HOST, DB_PORT, network |

## Monitoring Integration

### Kubernetes
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 5000
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /readyz
    port: 5000
  periodSeconds: 10
```

### Prometheus
```yaml
- job_name: 'icecharts'
  metrics_path: '/metrics'
  static_configs:
    - targets: ['localhost:5000']
```

### Alerting Rules
- Alert if status = "unhealthy"
- Alert if database response_time_ms > 1000
- Alert if memory usage > 85%
- Alert if disk usage > 85%

## Related Endpoints

- `GET /healthz` - Basic health check (no auth required)
- `GET /readyz` - Readiness check (database required)
- `GET /api/v1/admin/system/health` - Detailed health check (auth required)
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/system/config` - System configuration

## Testing

```bash
# Run test suite
pytest tests/test_health_check_service.py -v

# Run specific test
pytest tests/test_health_check_service.py::TestHealthCheckService::test_check_all_returns_required_fields -v

# Run with coverage
pytest tests/test_health_check_service.py --cov=app.services.health_check_service
```

## Documentation

For complete documentation, see:
- `/docs/HEALTH_CHECKS.md` - Full implementation guide
- `/IMPLEMENTATION_SUMMARY.md` - Technical details
- `/app/services/health_check_service.py` - Source code with docstrings
- `/app/api/v1/admin.py` - Endpoint implementation

## Support

For issues or questions:
1. Check logs: `docker logs icecharts-flask`
2. Test endpoint: `curl http://localhost:5000/healthz`
3. Verify configuration: Check environment variables
4. Review documentation: See `/docs/HEALTH_CHECKS.md`
