# IceCharts Deployment Guide

Production deployment guide for IceCharts on various platforms and environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Backup & Recovery](#backup--recovery)
- [Monitoring](#monitoring)
- [Security Hardening](#security-hardening)
- [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] SSL/TLS certificates obtained and configured
- [ ] Database backup strategy defined
- [ ] Password and secrets management in place
- [ ] Email service configured (optional, for notifications)
- [ ] Domain name and DNS configured
- [ ] Monitoring and alerting set up
- [ ] Firewall rules configured
- [ ] Capacity planning completed
- [ ] Disaster recovery plan documented
- [ ] Security audit completed

---

## Docker Compose Deployment

### Recommended Setup

For small to medium deployments (< 1000 concurrent users):

```bash
# 1. Clone repository
git clone https://github.com/PenguinCloud/IceCharts.git
cd IceCharts

# 2. Create production environment file
cp .env.example .env.prod
# Edit .env.prod with production settings

# 3. Start services with production config
docker-compose -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  up -d

# 4. Verify services
docker-compose -f docker-compose.yml \
  -f docker-compose.prod.yml \
  --env-file .env.prod \
  ps
```

### Production Environment File

Create `.env.prod`:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
SECURITY_PASSWORD_SALT=your-secure-salt-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database
POSTGRES_DB=icecharts_prod
POSTGRES_USER=icecharts_user
POSTGRES_PASSWORD=very-secure-password
DB_POOL_SIZE=20

# Redis
REDIS_PASSWORD=very-secure-redis-password

# MinIO
MINIO_ROOT_USER=icecharts_admin
MINIO_ROOT_PASSWORD=very-secure-minio-password
MINIO_BUCKET=icecharts

# API Configuration
API_PORT=5001
CORS_ORIGINS=https://yourdomain.com

# Frontend
WEB_PORT=3000
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_API_BASE_PATH=/api/v1

# License
LICENSE_KEY=your-license-key
RELEASE_MODE=true

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

### Docker Compose Production File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Production PostgreSQL with persistent volume
  postgres:
    image: postgres:17-alpine
    container_name: icecharts-postgres-prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "127.0.0.1:5432:5432"  # Only local connections
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    networks:
      - icecharts-network

  # Production Redis with persistence
  redis:
    image: redis:7-alpine
    container_name: icecharts-redis-prod
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    ports:
      - "127.0.0.1:6379:6379"  # Only local connections
    volumes:
      - redis_prod_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    networks:
      - icecharts-network

  # Production MinIO
  minio:
    image: minio/minio:latest
    container_name: icecharts-minio-prod
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "127.0.0.1:9000:9000"  # Only local connections
    volumes:
      - minio_prod_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 20s
      retries: 3
    restart: always
    networks:
      - icecharts-network

  # Production API with resource limits
  api:
    build:
      context: ./services/flask-backend
      dockerfile: Dockerfile
    container_name: icecharts-api-prod
    environment:
      FLASK_ENV: production
      SECRET_KEY: ${SECRET_KEY}
      DB_HOST: postgres
      REDIS_HOST: redis
      MINIO_ENDPOINT: minio:9000
    ports:
      - "127.0.0.1:5000:5000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    networks:
      - icecharts-network

  # Production WebUI
  web:
    build:
      context: ./services/webui
      dockerfile: Dockerfile
    container_name: icecharts-web-prod
    environment:
      NODE_ENV: production
      REACT_APP_API_URL: ${REACT_APP_API_URL}
      REACT_APP_API_BASE_PATH: ${REACT_APP_API_BASE_PATH}
    ports:
      - "127.0.0.1:3000:80"
    depends_on:
      - api
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    networks:
      - icecharts-network

volumes:
  postgres_prod_data:
  redis_prod_data:
  minio_prod_data:

networks:
  icecharts-network:
    driver: bridge
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3+ installed
- Persistent volume provisioner
- PostgreSQL Operator (optional, for managed DB)

### Namespace Setup

```bash
# Create namespace
kubectl create namespace icecharts

# Create secrets
kubectl create secret generic icecharts-secrets \
  --from-literal=db-password=very-secure-password \
  --from-literal=redis-password=very-secure-redis-password \
  --from-literal=minio-password=very-secure-minio-password \
  -n icecharts
```

### Deployment YAML

Create `k8s/deployment.yaml`:

```yaml
---
# PostgreSQL Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: icecharts
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:17-alpine
        env:
        - name: POSTGRES_DB
          value: icecharts
        - name: POSTGRES_USER
          value: icecharts_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: icecharts-secrets
              key: db-password
        ports:
        - containerPort: 5432
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: postgres-pvc

---
# Redis Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: icecharts
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server"]
        args:
          - "--requirepass"
          - "$(REDIS_PASSWORD)"
          - "--appendonly"
          - "yes"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: icecharts-secrets
              key: redis-password
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: redis-pvc

---
# API Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: icecharts
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: icecharts-api:latest
        imagePullPolicy: Always
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DB_HOST
          value: "postgres"
        - name: REDIS_HOST
          value: "redis"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: icecharts-secrets
              key: db-password
        ports:
        - containerPort: 5000
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
# WebUI Service Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: icecharts
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: icecharts-web:latest
        imagePullPolicy: Always
        env:
        - name: REACT_APP_API_URL
          value: "https://api.yourdomain.com"
        ports:
        - containerPort: 80
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
# API Service
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: icecharts
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP

---
# WebUI Service
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: icecharts
spec:
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: icecharts-ingress
  namespace: icecharts
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    - api.yourdomain.com
    secretName: icecharts-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80

---
# Persistent Volume Claims
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: icecharts
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: icecharts
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

### Deploy to Kubernetes

```bash
# Apply configuration
kubectl apply -f k8s/deployment.yaml

# Monitor rollout
kubectl rollout status deployment/api -n icecharts
kubectl rollout status deployment/web -n icecharts

# Check status
kubectl get all -n icecharts

# View logs
kubectl logs deployment/api -n icecharts -f
kubectl logs deployment/web -n icecharts -f
```

---

## Environment Configuration

### Essential Environment Variables

```bash
# Flask/API
FLASK_ENV=production              # production or development
SECRET_KEY=long-random-string     # Min 32 characters
JWT_SECRET_KEY=jwt-secret         # For token signing
SECURITY_PASSWORD_SALT=salt       # For password hashing

# Database
DB_TYPE=postgres                  # Database type
DB_HOST=postgres                  # Host
DB_PORT=5432                      # Port
DB_NAME=icecharts                # Database name
DB_USER=icecharts_user           # Username
DB_PASS=password                 # Password
DB_POOL_SIZE=20                  # Connection pool size

# Redis
REDIS_HOST=redis                 # Host
REDIS_PORT=6379                  # Port
REDIS_PASSWORD=password          # Password
REDIS_URL=redis://:password@redis:6379/0

# MinIO
MINIO_ENDPOINT=minio:9000       # Endpoint
MINIO_ACCESS_KEY=user            # Access key
MINIO_SECRET_KEY=password        # Secret key
MINIO_BUCKET=icecharts          # Bucket name
MINIO_SECURE=false              # Use SSL

# API
API_PORT=5001                   # External port
CORS_ORIGINS=https://yourdomain.com

# Frontend
WEB_PORT=3000                   # External port
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_API_BASE_PATH=/api/v1

# License
LICENSE_KEY=your-key            # Commercial license
LICENSE_SERVER_URL=https://license.penguintech.io
PRODUCT_NAME=icecharts
RELEASE_MODE=true               # Enable license enforcement

# Logging
LOG_LEVEL=info                  # debug, info, warning, error
LOG_FORMAT=json                 # json or text
```

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT secret
openssl rand -hex 32

# Generate password salt
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Database Setup

### Initial Database Creation

```bash
# Run migrations
docker-compose exec api python -c "from app.models import init_db; init_db()"

# Create default admin user
docker-compose exec api python -c "
from app.models import create_admin_user
create_admin_user('admin@localhost.local', 'SecurePassword123!')
"
```

### Backup Strategy

**Daily Backups**:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/icecharts_$TIMESTAMP.sql.gz"

# PostgreSQL dump
docker-compose exec postgres pg_dump \
  -U icecharts_user \
  -d icecharts \
  | gzip > "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "icecharts_*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE"
```

Schedule with cron:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Decompress and restore
gunzip -c /backups/icecharts_20240101_020000.sql.gz | \
  docker-compose exec -T postgres \
  psql -U icecharts_user -d icecharts
```

---

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:5001/api/v1/health

# Check database
docker-compose exec postgres psql -U icecharts_user -d icecharts -c "SELECT 1"

# Check Redis
docker-compose exec redis redis-cli ping

# Check MinIO
docker-compose exec minio mc admin info local
```

### Enable Prometheus Monitoring

```bash
# Start monitoring stack
docker-compose -f docker-compose.yml \
  -f docker-compose.monitoring.yml \
  up -d prometheus grafana
```

**Access Grafana**:
- URL: http://localhost:3001
- Default: admin / admin
- Import IceCharts dashboard

---

## Security Hardening

### Network Security

```bash
# Only expose necessary ports
- API port: Through reverse proxy/load balancer
- Web UI: Through reverse proxy/load balancer
- Database: No external access
- Redis: No external access
- MinIO: No external access
```

### SSL/TLS Configuration

Using NGINX as reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://web:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    location /api/v1 {
        proxy_pass http://api:5000/api/v1;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### Secrets Management

Use environment variable files with restricted permissions:

```bash
# Create env file with restricted access
touch .env.prod
chmod 600 .env.prod

# Add to .gitignore
echo ".env.prod" >> .gitignore
echo ".env.*.local" >> .gitignore
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs postgres
docker-compose logs api
docker-compose logs web

# Verify ports aren't in use
netstat -tuln | grep 5432
netstat -tuln | grep 6379
```

### Database Connection Errors

```bash
# Test database connection
docker-compose exec api python -c "
from app import db
try:
    db.executesql('SELECT 1')
    print('Connection OK')
except Exception as e:
    print(f'Error: {e}')
"
```

### High Memory Usage

```bash
# Monitor container stats
docker stats

# Adjust resource limits in docker-compose.yml
# Restart with new limits
docker-compose down
docker-compose up -d
```

### WebSocket Connection Issues

Ensure WebSocket upgrade headers in reverse proxy:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

---

## Related Documentation

- [Getting Started](GETTING_STARTED.md) - Local setup
- [Architecture](ARCHITECTURE.md) - System design
- [Environment Configuration](GETTING_STARTED.md#environment-variables) - Configuration details
- [Docker Setup](DOCKER_SETUP.md) - Container-specific info
