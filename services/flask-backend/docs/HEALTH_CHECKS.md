# System Health Checks Documentation

## Overview

The IceCharts Flask backend includes a comprehensive health check system that monitors all critical components of the application. The health check endpoint provides detailed status information about each component, including response times and error details.

## Health Check Endpoint

### Endpoint
```
GET /api/v1/admin/system/health
```

### Authentication
- Requires valid JWT token in `Authorization` header
- Admin role required

### Response Format

#### Healthy Response (200 OK)
```json
{
  "health": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:45.123456",
    "uptime_seconds": 3600,
    "components": {
      "database": {
        "status": "healthy",
        "message": "Database connection OK",
        "response_time_ms": 5.23,
        "type": "postgresql",
        "details": {
          "host": "localhost",
          "port": 5432,
          "database": "icecharts"
        }
      },
      "redis": {
        "status": "healthy",
        "message": "Redis connection OK",
        "response_time_ms": 2.15,
        "details": {
          "version": "7.0.0",
          "connected_clients": 5,
          "memory_usage_mb": 2.45,
          "uptime_seconds": 86400
        }
      },
      "storage": {
        "status": "healthy",
        "message": "1 storage provider(s) configured",
        "response_time_ms": 15.67,
        "providers": [
          {
            "provider": "AWS S3",
            "type": "s3",
            "status": "healthy",
            "message": "S3 bucket accessible",
            "response_time_ms": 12.34,
            "details": {
              "bucket": "icecharts-prod",
              "region": "us-east-1"
            }
          }
        ]
      },
      "api": {
        "status": "healthy",
        "message": "API service operational",
        "response_time_ms": 0,
        "details": {
          "version": "0.2.0",
          "environment": "production",
          "debug": false
        }
      },
      "system": {
        "status": "healthy",
        "message": "System resources: CPU 25.5%, Memory 45.2%, Disk 62.3%",
        "response_time_ms": 0,
        "details": {
          "cpu": {
            "usage_percent": 25.5,
            "count": 8
          },
          "memory": {
            "usage_percent": 45.2,
            "total_gb": 16.0,
            "available_gb": 8.76,
            "used_gb": 7.24,
            "status": "healthy"
          },
          "disk": {
            "usage_percent": 62.3,
            "total_gb": 200.0,
            "used_gb": 124.6,
            "free_gb": 75.4,
            "status": "healthy"
          }
        }
      }
    }
  }
}
```

#### Degraded Response (200 OK)
```json
{
  "health": {
    "status": "degraded",
    "timestamp": "2024-01-15T10:30:45.123456",
    "uptime_seconds": 3600,
    "components": {
      "database": {
        "status": "healthy",
        ...
      },
      "redis": {
        "status": "healthy",
        ...
      },
      "storage": {
        "status": "degraded",
        "message": "1 storage provider(s) configured",
        "providers": [
          {
            "provider": "AWS S3",
            "type": "s3",
            "status": "unhealthy",
            "message": "S3 error: InvalidAccessKeyId",
            "error": "The Access Key Id you provided does not exist in our records"
          }
        ]
      },
      "api": {
        "status": "healthy",
        ...
      },
      "system": {
        "status": "degraded",
        "message": "System resources: CPU 45%, Memory 85%, Disk 78%",
        "details": {
          "memory": {
            "usage_percent": 85.0,
            "status": "degraded"
          },
          ...
        }
      }
    }
  }
}
```

#### Unhealthy Response (503 Service Unavailable)
```json
{
  "health": {
    "status": "unhealthy",
    "timestamp": "2024-01-15T10:30:45.123456",
    "components": {
      "database": {
        "status": "unhealthy",
        "message": "Database connection failed: connection refused",
        "response_time_ms": 5000.45,
        "error": "connection refused"
      },
      ...
    }
  }
}
```

## Component Health Checks

### 1. Database Check

Verifies PostgreSQL (or configured database) connectivity and responsiveness.

**What it checks:**
- Connection to database server
- Ability to execute queries
- Connection response time

**Status indicators:**
- `healthy`: Database connection works, query successful
- `unhealthy`: Cannot connect or query fails

**Error scenarios:**
- Connection refused
- Invalid credentials
- Database not accessible
- Network timeout

### 2. Redis Cache Check

Verifies Redis connectivity and retrieves cache statistics.

**What it checks:**
- Connection to Redis server
- PING command response
- Redis version and memory usage
- Connected clients count
- Server uptime

**Status indicators:**
- `healthy`: Redis responsive and accessible
- `unhealthy`: Cannot connect to Redis
- `unknown`: Redis not configured

**Error scenarios:**
- Connection refused
- Authentication failure
- Network timeout
- Redis shutdown

### 3. Storage Check

Verifies connectivity to all configured storage providers (S3, MinIO, Google Drive, OneDrive).

**What it checks:**
- Storage provider accessibility
- Bucket/folder existence
- Authentication credentials
- Provider-specific connectivity

**Storage providers supported:**
- **S3 (AWS)**: Bucket accessibility check
- **MinIO**: Bucket existence verification
- **Google Drive**: OAuth configuration check (credentials cached)
- **OneDrive**: OAuth configuration check (credentials cached)

**Status indicators:**
- `healthy`: Provider accessible and functional
- `degraded`: Multiple providers have issues
- `unhealthy`: All providers failed or not configured
- `configured`: OAuth-based provider configured but not immediately testable
- `unknown`: Provider type not recognized

**Error scenarios:**
- Invalid credentials
- Bucket/container not found
- Network connectivity issues
- Service temporarily unavailable
- Insufficient permissions

### 4. API Service Check

Verifies the Flask API service is running and operational.

**What it checks:**
- Application version
- Environment configuration
- Debug mode status

**Status indicators:**
- `healthy`: API service operational
- `unhealthy`: API check failed

### 5. System Resources Check

Monitors system resource utilization (CPU, memory, disk).

**What it checks:**
- CPU usage percentage and core count
- Memory usage (total, used, available)
- Disk usage (total, used, free)

**Status indicators:**
- `healthy`: All resources within normal range (< 80%)
- `degraded`: Resources elevated (80-95%)
- `unhealthy`: Resources critical (> 95%)

**Thresholds:**
- Memory: Degraded >= 80%, Unhealthy > 95%
- Disk: Degraded >= 80%, Unhealthy > 95%

## Overall Status Determination

The overall system status is determined by component statuses:

```
unhealthy: Any component is unhealthy
degraded: Multiple components degraded OR one component degraded
healthy: All components healthy
```

## Usage Examples

### Using cURL
```bash
# Get health status (requires admin token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://api.icecharts.app/api/v1/admin/system/health

# Pretty print with jq
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     https://api.icecharts.app/api/v1/admin/system/health | jq '.'
```

### Using Python
```python
import requests

headers = {
    "Authorization": f"Bearer {jwt_token}"
}

response = requests.get(
    "https://api.icecharts.app/api/v1/admin/system/health",
    headers=headers
)

health = response.json()
print(f"Overall Status: {health['health']['status']}")
print(f"Database: {health['health']['components']['database']['status']}")
print(f"Redis: {health['health']['components']['redis']['status']}")
```

### Using JavaScript/Fetch
```javascript
const getHealthStatus = async (jwtToken) => {
  const response = await fetch(
    'https://api.icecharts.app/api/v1/admin/system/health',
    {
      headers: {
        'Authorization': `Bearer ${jwtToken}`
      }
    }
  );

  const data = await response.json();
  return data.health;
};

// Usage
const health = await getHealthStatus(token);
console.log(`System Status: ${health.status}`);
```

## Monitoring and Alerting

### Recommended Monitoring Setup

1. **Liveness Check**: Use `/healthz` endpoint (requires no auth)
   - Interval: 30 seconds
   - Should always return 200 OK

2. **Readiness Check**: Use `/readyz` endpoint (requires database)
   - Interval: 30 seconds
   - Returns 503 if database unavailable

3. **Detailed Health Check**: Use `/api/v1/admin/system/health` endpoint
   - Interval: 5 minutes
   - Requires authentication
   - Provides detailed component status

### Alert Conditions

Set up alerts for:
- Status = "unhealthy" (HTTP 503)
- Database response_time_ms > 1000ms
- Redis response_time_ms > 500ms
- Memory usage > 85%
- Disk usage > 85%
- Any storage provider status = "unhealthy"

### Kubernetes Integration

```yaml
# Liveness Probe
livenessProbe:
  httpGet:
    path: /healthz
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 30

# Readiness Probe
readinessProbe:
  httpGet:
    path: /readyz
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```

## Implementation Details

### HealthCheckService

Located in: `app/services/health_check_service.py`

**Main Methods:**
- `check_all()`: Performs all component health checks
- `_check_database()`: PostgreSQL connectivity check
- `_check_redis()`: Redis cache check
- `_check_storage()`: Storage provider checks
- `_check_api_service()`: API service status
- `_check_system_resources()`: CPU, memory, disk monitoring

**Configuration:**
- All checks use the same configuration as the main application
- Connection details from Flask config (DB_HOST, REDIS_URL, etc.)
- Storage providers retrieved from database configuration

### Performance Considerations

- Each check has its own timeout handling
- Individual check failures don't block other checks
- Response times measured for each component
- Graceful degradation when optional components unavailable

### Dependencies

Required packages:
- `redis`: Redis client library
- `psutil`: System resource monitoring
- `boto3`: AWS S3 support (optional)
- `minio`: MinIO support (optional)

## Troubleshooting

### Database check fails
1. Verify PostgreSQL is running
2. Check DB_HOST, DB_PORT, DB_NAME configuration
3. Verify network connectivity to database

### Redis check fails
1. Verify Redis is running
2. Check REDIS_URL configuration
3. Verify Redis authentication if required

### Storage check fails
1. Verify storage provider configuration in database
2. Check credentials and permissions
3. Verify network connectivity to storage service

### System resources check not available
1. Verify psutil is installed: `pip install psutil`
2. Check system resource availability
3. Verify process permissions for system info

## API Changes

### Before Implementation
```
GET /api/v1/admin/system/health
Response:
{
  "health": {
    "status": "healthy",
    "components": {
      "database": {"status": "healthy", "message": "Database connection OK"},
      "storage": {"status": "healthy", "message": "Storage accessible"},
      "cache": {"status": "healthy", "message": "Cache operational"}
    }
  }
}
```

### After Implementation
Detailed health checks for each component with response times, error details, and resource metrics.

## Future Enhancements

Potential improvements:
1. Health check metrics exported to Prometheus
2. Customizable alert thresholds per component
3. Historical health trends
4. Health check scheduling with automatic remediation
5. Component dependency tracking
6. Custom health check plugins
