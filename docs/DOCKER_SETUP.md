# IceCharts Docker Setup

## Quick Start

### 1. Create Environment File
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Start Core Services Only (without monitoring)
```bash
docker-compose up -d postgres redis minio api web
```

### 4. Start with Monitoring
```bash
docker-compose --profile monitoring up -d
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         IceCharts Stack                         │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React Web  │────▶│  Flask API   │────▶│  PostgreSQL  │
│  Port 3000   │     │  Port 4000   │     │  Port 5432   │
│              │     │              │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────┴───────┐
                     │              │
              ┌──────▼─────┐ ┌─────▼──────┐
              │   Redis    │ │   MinIO    │
              │ Port 6379  │ │ Port 9000  │
              │            │ │ Port 9001  │
              └────────────┘ └────────────┘
```

## Services

### Core Services (Always Running)

| Service | Port Mapping | Purpose |
|---------|--------------|---------|
| **postgres** | 5432:5432 | PostgreSQL 17 database |
| **redis** | 6379:6379 | Redis 7 cache with password auth |
| **minio** | 9000:9000, 9001:9001 | MinIO object storage (API & Console) |
| **api** | 4000:5000 | Flask backend API |
| **web** | 3000:80 | React frontend |

### Optional Services (--profile monitoring)

| Service | Port Mapping | Purpose |
|---------|--------------|---------|
| **prometheus** | 9090:9090 | Metrics collection |
| **grafana** | 3001:3000 | Dashboards and visualization |

## Port Configuration

All ports can be customized via environment variables:

```bash
# Core Service Ports
POSTGRES_PORT=5432
REDIS_PORT=6379
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
API_PORT=4000
WEB_PORT=3000

# Monitoring Ports
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
```

## Health Checks

All services include health checks for reliable startup:

- **PostgreSQL**: `pg_isready` check every 10s
- **Redis**: `redis-cli ping` check every 10s
- **MinIO**: `mc ready local` check every 30s
- **API**: HTTP check on `/healthz` every 30s
- **Web**: HTTP check on root every 30s

## Volume Persistence

Data is persisted in Docker volumes:

```bash
# View volumes
docker volume ls | grep icecharts

# Volumes:
# - icecharts_postgres_data
# - icecharts_redis_data
# - icecharts_minio_data
# - icecharts_prometheus_data (monitoring profile)
# - icecharts_grafana_data (monitoring profile)
```

## Common Commands

### Start Services
```bash
# Start all core services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start specific service
docker-compose up -d postgres redis
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DATA LOSS!)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Service Management
```bash
# Restart a service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build api

# Check service status
docker-compose ps
```

### Access Containers
```bash
# Execute command in container
docker-compose exec api bash
docker-compose exec postgres psql -U icecharts_user -d icecharts
docker-compose exec redis redis-cli -a changeme

# View container stats
docker stats
```

## Database Access

### Connect to PostgreSQL
```bash
# From host
psql -h localhost -p 5432 -U icecharts_user -d icecharts

# From container
docker-compose exec postgres psql -U icecharts_user -d icecharts
```

### Connect to Redis
```bash
# From host
redis-cli -p 6379 -a changeme

# From container
docker-compose exec redis redis-cli -a changeme
```

## MinIO Access

### Web Console
- URL: http://localhost:9001
- Username: `minioadmin` (or `MINIO_ROOT_USER`)
- Password: `minioadmin` (or `MINIO_ROOT_PASSWORD`)

### API Endpoint
- URL: http://localhost:9000
- Access Key: `minioadmin`
- Secret Key: `minioadmin`

## API Access

### Health Check
```bash
curl http://localhost:4000/healthz
```

### API Endpoints
- Base URL: http://localhost:4000
- API Path: /api/v1
- Full URL: http://localhost:4000/api/v1

## Web Access

- URL: http://localhost:3000
- Default Admin: `admin@localhost.local` / `admin123`

## Environment Variables

### Critical Security Variables
```bash
# MUST change in production!
SECRET_KEY=changeme-in-production
SECURITY_PASSWORD_SALT=changeme-salt-in-production
JWT_SECRET_KEY=changeme-jwt-secret
POSTGRES_PASSWORD=changeme
REDIS_PASSWORD=changeme
DEFAULT_ADMIN_PASSWORD=admin123
```

### MinIO Configuration
```bash
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_BUCKET=icecharts
MINIO_SECURE=false  # Set to true with TLS
```

### Database Configuration (PyDAL)
```bash
DB_TYPE=postgres  # postgres, mysql, sqlite, etc.
DB_POOL_SIZE=10
```

### License Configuration
```bash
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
PRODUCT_NAME=icecharts
LICENSE_SERVER_URL=https://license.penguintech.io
RELEASE_MODE=false  # false=dev, true=prod
```

## Networking

All services are connected via the `icecharts-network` bridge network:

```bash
# View network
docker network inspect icecharts_icecharts-network

# Services can communicate using service names:
# - postgres:5432
# - redis:6379
# - minio:9000
# - api:5000
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs service-name

# Check health status
docker-compose ps

# Restart service
docker-compose restart service-name
```

### Database Connection Issues
```bash
# Verify PostgreSQL is ready
docker-compose exec postgres pg_isready -U icecharts_user

# Check connection from API
docker-compose exec api wget -q -O- http://localhost:5000/healthz
```

### Port Conflicts
If ports are already in use, customize them in `.env`:
```bash
API_PORT=4001  # Change from 4000
WEB_PORT=3001  # Change from 3000
```

### Reset Everything
```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Development Workflow

### Hot Reload Development
For development with hot reload, use `docker-compose.dev.yml`:
```bash
docker-compose -f docker-compose.dev.yml up
```

### Build Specific Service
```bash
# Rebuild API after code changes
docker-compose build api
docker-compose up -d api

# Rebuild without cache
docker-compose build --no-cache api
```

### Update Dependencies
```bash
# Python (Flask API)
docker-compose exec api pip install -r requirements.txt

# Node.js (React Web)
docker-compose exec web npm install
```

## Monitoring

### Enable Monitoring Stack
```bash
# Start with Prometheus and Grafana
docker-compose --profile monitoring up -d

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3001
```

### Grafana Setup
- URL: http://localhost:3001
- Username: `admin` (from `GRAFANA_USER`)
- Password: `admin` (from `GRAFANA_PASSWORD`)

## Production Deployment

### Security Checklist
- [ ] Change all passwords in `.env`
- [ ] Set `RELEASE_MODE=true` for license enforcement
- [ ] Configure `LICENSE_KEY` for production
- [ ] Enable TLS (`TLS_ENABLED=true`)
- [ ] Configure SMTP for email notifications
- [ ] Set `FLASK_ENV=production`
- [ ] Set `NODE_ENV=production`
- [ ] Configure backup schedule
- [ ] Enable monitoring profile
- [ ] Set up external PostgreSQL for HA
- [ ] Configure external Redis for HA
- [ ] Set up MinIO with TLS

### Production Startup
```bash
# Ensure .env is configured for production
docker-compose --profile monitoring up -d
```

## Backup and Restore

### Backup PostgreSQL
```bash
# Backup database
docker-compose exec -T postgres pg_dump -U icecharts_user icecharts > backup.sql

# With compression
docker-compose exec -T postgres pg_dump -U icecharts_user icecharts | gzip > backup.sql.gz
```

### Restore PostgreSQL
```bash
# Restore from backup
docker-compose exec -T postgres psql -U icecharts_user icecharts < backup.sql

# From compressed backup
gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U icecharts_user icecharts
```

### Backup MinIO
```bash
# Export bucket data
docker-compose exec minio mc mirror /data/icecharts ./minio-backup
```

## Performance Tuning

### PostgreSQL
```bash
# Increase connections (in PostgreSQL config)
# Add to postgresql.conf:
# max_connections = 200
# shared_buffers = 256MB
# effective_cache_size = 1GB
```

### Redis
```bash
# Configure maxmemory policy
# Add to redis.conf:
# maxmemory 1gb
# maxmemory-policy allkeys-lru
```

### Connection Pooling
```bash
# Adjust pool sizes in .env
DB_POOL_SIZE=20
MAX_CONNECTIONS=200
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-10
**Project**: IceCharts
