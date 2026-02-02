# IceRuns Deployment Guide

Deploy IceRuns to production environments.

## Deployment Options

### Option 1: Docker Compose (Development/Small)

```yaml
# docker-compose.yml
services:
  iceruns-invoker:
    build:
      context: ./services/iceruns-invoker
      platforms:
        - linux/amd64
        - linux/arm64
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DB_TYPE=postgres
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=icecharts
      - DB_USER=icecharts
      - DB_PASSWORD=${DB_PASSWORD}
      - STORAGE_PROVIDER=minio
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - STORAGE_SECRET_KEY=${MINIO_SECRET_KEY}
      - STORAGE_BUCKET=icecharts
      - INVOKER_CONCURRENCY=5
      - LOG_LEVEL=INFO
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - redis
      - postgres
      - minio
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 2G
```

**Start:**
```bash
docker-compose up -d iceruns-invoker
```

**Check Status:**
```bash
docker-compose logs -f iceruns-invoker
```

### Option 2: Kubernetes (Production)

#### Prerequisites
- Kubernetes 1.24+
- Docker socket access on nodes (or use containerd)
- PostgreSQL/MySQL database
- Redis cluster
- MinIO or S3 bucket

#### Create Namespace

```bash
kubectl create namespace iceruns
```

#### Create Secrets

```bash
kubectl create secret generic iceruns-secrets \
  -n iceruns \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=db-password="<password>" \
  --from-literal=storage-access-key="<key>" \
  --from-literal=storage-secret-key="<secret>"
```

#### Deploy Invoker

```yaml
# k8s/iceruns/invoker-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iceruns-invoker
  namespace: iceruns
  labels:
    app: iceruns-invoker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: iceruns-invoker
  template:
    metadata:
      labels:
        app: iceruns-invoker
    spec:
      serviceAccountName: iceruns
      containers:
      - name: invoker
        image: icecharts/iceruns-invoker:latest
        imagePullPolicy: Always
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: iceruns-secrets
              key: redis-url
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: iceruns-secrets
              key: db-password
        - name: STORAGE_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: iceruns-secrets
              key: storage-access-key
        - name: STORAGE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: iceruns-secrets
              key: storage-secret-key
        - name: DB_TYPE
          value: "postgres"
        - name: DB_HOST
          value: "postgres.icecharts"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          value: "icecharts"
        - name: DB_USER
          value: "icecharts"
        - name: STORAGE_ENDPOINT
          value: "minio.icecharts:9000"
        - name: STORAGE_BUCKET
          value: "icecharts"
        - name: INVOKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: INVOKER_CONCURRENCY
          value: "5"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: docker-socket
        hostPath:
          path: /var/run/docker.sock
          type: Socket
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - iceruns-invoker
              topologyKey: kubernetes.io/hostname
```

**Deploy:**
```bash
kubectl apply -f k8s/iceruns/invoker-deployment.yaml
```

#### Horizontal Pod Autoscaler

```yaml
# k8s/iceruns/invoker-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: iceruns-invoker-hpa
  namespace: iceruns
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: iceruns-invoker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

**Deploy:**
```bash
kubectl apply -f k8s/iceruns/invoker-hpa.yaml
```

#### Monitor Deployment

```bash
# Check pods
kubectl get pods -n iceruns

# View logs
kubectl logs -f deployment/iceruns-invoker -n iceruns

# Check HPA status
kubectl get hpa -n iceruns

# Get deployment details
kubectl describe deployment iceruns-invoker -n iceruns
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | - | Redis connection string |
| `DB_TYPE` | postgres | Database type (postgres, mysql, sqlite) |
| `DB_HOST` | localhost | Database hostname |
| `DB_PORT` | 5432 | Database port |
| `DB_NAME` | icecharts | Database name |
| `DB_USER` | icecharts | Database user |
| `DB_PASSWORD` | - | Database password |
| `STORAGE_PROVIDER` | minio | Storage provider (minio, s3) |
| `STORAGE_ENDPOINT` | minio:9000 | MinIO/S3 endpoint |
| `STORAGE_ACCESS_KEY` | - | Access key |
| `STORAGE_SECRET_KEY` | - | Secret key |
| `STORAGE_BUCKET` | icecharts | Bucket name |
| `INVOKER_ID` | auto | Unique invoker identifier |
| `INVOKER_CONCURRENCY` | 5 | Max concurrent executions |
| `WARM_CONTAINER_TTL` | 600 | Container reuse TTL (seconds) |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Resource Requirements

**Minimum:**
```
CPU: 1.0 vCPU
Memory: 2 GB
Disk: 10 GB (for container images)
```

**Recommended:**
```
CPU: 2-4 vCPU
Memory: 4-8 GB
Disk: 50 GB (buffer for images and logs)
```

**For 1000 req/min:**
```
CPU: 4-8 vCPU
Memory: 8-16 GB
Invoker replicas: 5-10
```

## Database Setup

### PostgreSQL

```sql
-- Create database
CREATE DATABASE icecharts;

-- Create user
CREATE USER icecharts WITH PASSWORD 'secure_password';

-- Grant privileges
ALTER ROLE icecharts WITH CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE icecharts TO icecharts;
```

### MySQL

```sql
-- Create database
CREATE DATABASE icecharts;

-- Create user
CREATE USER 'icecharts'@'localhost' IDENTIFIED BY 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON icecharts.* TO 'icecharts'@'localhost';
FLUSH PRIVILEGES;
```

## Storage Setup

### MinIO

```bash
# Create bucket
mc mb minio/icecharts

# Set access policy
mc policy set public minio/icecharts
```

### AWS S3

```bash
# Create bucket
aws s3 mb s3://icecharts-bucket

# Set bucket policy for application access
aws s3api put-bucket-policy \
  --bucket icecharts-bucket \
  --policy '{...}'
```

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# Liveness probe
curl http://invoker:8081/healthz

# Readiness probe
curl http://invoker:8081/readyz

# Metrics
curl http://invoker:9090/metrics
```

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'iceruns'
    static_configs:
      - targets: ['invoker:9090']
```

### Monitoring Queries

```promql
# Active executions
iceruns_active_executions

# Queue size
iceruns_queue_size

# Execution rate
rate(iceruns_executions_total[5m])

# Success rate
(rate(iceruns_executions_total{status="completed"}[5m])) /
(rate(iceruns_executions_total[5m]))

# P95 latency
histogram_quantile(0.95, iceruns_execution_duration_seconds)

# Error rate
rate(iceruns_execution_errors_total[5m])
```

## Production Checklist

- [ ] Database configured and tested
- [ ] Redis cluster running
- [ ] MinIO/S3 bucket created
- [ ] Environment variables set
- [ ] Docker/container runtime installed
- [ ] Network connectivity verified
- [ ] Resource limits configured
- [ ] Health checks passing
- [ ] Monitoring set up
- [ ] Logs aggregation configured
- [ ] Backup strategy in place
- [ ] Security hardened
- [ ] Load testing completed

## Troubleshooting

### Invoker Won't Start

**Check:**
1. Database connectivity: `telnet db_host db_port`
2. Redis connectivity: `redis-cli -h redis_host ping`
3. Docker socket permissions: `ls -la /var/run/docker.sock`
4. Environment variables: `env | grep ICERUNS`

**Logs:**
```bash
docker logs iceruns-invoker
# or
kubectl logs deployment/iceruns-invoker -n iceruns
```

### Functions Not Executing

**Check:**
1. Queue has tasks: `redis-cli XLEN iceruns:tasks`
2. Invoker is consuming: `redis-cli XINFO STREAM iceruns:tasks`
3. Container images available: `docker images`

### High Memory Usage

**Causes:**
- Too many warm containers
- Memory leak in function
- Invoker concurrency too high

**Solution:**
- Reduce `WARM_CONTAINER_TTL`
- Reduce `INVOKER_CONCURRENCY`
- Check function memory leaks

### Database Connection Pool Exhausted

**Causes:**
- Too many concurrent connections
- Connections not properly closed
- Connection timeout too long

**Solution:**
- Check `DB_POOL_SIZE`
- Increase database max_connections
- Review function connection handling

## Scaling Strategy

### Horizontal Scaling

1. **Monitor queue size:**
   ```bash
   redis-cli XLEN iceruns:tasks
   ```

2. **Scale invokers:**
   - Docker Compose: `docker-compose up -d --scale iceruns-invoker=5`
   - Kubernetes: `kubectl scale deployment iceruns-invoker --replicas=5 -n iceruns`

3. **Verify distribution:**
   ```bash
   redis-cli XINFO STREAM iceruns:tasks
   ```

### Vertical Scaling

1. Increase CPU/memory per invoker
2. Increase `INVOKER_CONCURRENCY`
3. Monitor resource utilization

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump -h db_host -U icecharts icecharts > backup.sql

# MySQL
mysqldump -h db_host -u icecharts -p icecharts > backup.sql
```

### S3/MinIO Backup

```bash
# MinIO
mc mirror --watch minio/icecharts s3/backup-bucket

# AWS S3
aws s3 sync s3://icecharts-bucket s3://backup-bucket
```

### Recovery

```bash
# Restore database
psql -h db_host -U icecharts icecharts < backup.sql

# Restore MinIO
mc mirror --watch s3/backup-bucket minio/icecharts
```

## Security Hardening

### 1. Network Policies

```yaml
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
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 6379
```

### 2. Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
```

### 3. Secret Management

```bash
# Use sealed secrets
kubectl create secret generic iceruns-secrets \
  --from-literal=db-password=... \
  --dry-run=client -o yaml | \
  kubeseal -f - > sealed-secrets.yaml
```

---

See also:
- [Architecture](./architecture.md)
- [Security](./security.md)
- [Troubleshooting](./troubleshooting.md)
