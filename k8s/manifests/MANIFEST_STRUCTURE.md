# IceCharts Kubernetes Manifest Structure

## Overview

This directory contains complete Kustomize manifests for deploying IceCharts to Kubernetes without Helm. The manifests are organized into base configurations and environment-specific overlays.

## Directory Layout

### Base Manifests (`/base`)

Contains the common configuration shared across all environments:

```
base/
├── kustomization.yaml           (Main base kustomization file)
├── namespace.yaml               (icecharts namespace)
├── configmap.yaml              (Non-sensitive application configuration)
├── secret.yaml                 (Sensitive credentials - base64 encoded)
├── postgres/                   (PostgreSQL StatefulSet)
│   ├── kustomization.yaml
│   ├── statefulset.yaml
│   ├── service.yaml            (Headless service for StatefulSet)
│   └── pvc.yaml                (Template for PVC, created by StatefulSet)
├── redis/                      (Redis StatefulSet)
│   ├── kustomization.yaml
│   ├── statefulset.yaml
│   ├── service.yaml            (Headless service for StatefulSet)
│   └── pvc.yaml
├── minio/                      (MinIO Object Storage StatefulSet)
│   ├── kustomization.yaml
│   ├── statefulset.yaml
│   ├── service.yaml            (LoadBalancer/ClusterIP service)
│   └── pvc.yaml
├── api/                        (Flask Backend Deployment)
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml            (ClusterIP service)
└── web/                        (React Frontend Deployment)
    ├── kustomization.yaml
    ├── deployment.yaml
    └── service.yaml            (ClusterIP service)
```

### Overlay Manifests (`/overlays`)

Environment-specific configurations that extend the base:

```
overlays/
├── local/                      (Development environment)
│   ├── kustomization.yaml      (Local config - 1 replica, small resources)
│   ├── replica-patch.yaml      (1 replica per service)
│   └── resources-patch.yaml    (Reduced resource limits for laptop)
│
├── aws/                        (AWS EKS production)
│   ├── kustomization.yaml      (Production config)
│   ├── replica-patch.yaml      (3 replicas per service)
│   ├── resources-patch.yaml    (Production resource limits)
│   ├── storage-class-patch.yaml (AWS EBS GP3 storage class)
│   └── ingress-patch.yaml      (AWS ALB ingress controller)
│
├── gcp/                        (Google Cloud GKE production)
│   ├── kustomization.yaml
│   ├── replica-patch.yaml
│   ├── resources-patch.yaml
│   ├── storage-class-patch.yaml (GCP PD-SSD storage class)
│   └── ingress-patch.yaml      (GCP Cloud Load Balancer)
│
└── azure/                      (Azure AKS production)
    ├── kustomization.yaml
    ├── replica-patch.yaml
    ├── resources-patch.yaml
    ├── storage-class-patch.yaml (Azure Managed Disks)
    └── ingress-patch.yaml      (Azure Application Gateway)
```

## Component Breakdown

### 1. PostgreSQL Database
- **Type**: StatefulSet (1 replica)
- **Image**: `postgres:17-alpine`
- **Storage**: PVC created by volumeClaimTemplates
  - Local/Dev: 10Gi
  - AWS: 50Gi
  - GCP: 50Gi
  - Azure: 50Gi
- **Service**: Headless service for DNS-based discovery
- **Configuration**: Via ConfigMap (host, port, database, user)
- **Credentials**: Via Secret (password)

### 2. Redis Cache
- **Type**: StatefulSet (1 replica)
- **Image**: `redis:7-alpine`
- **Storage**: PVC with persistent append-only file
  - Local/Dev: 5Gi
  - AWS: 20Gi
  - GCP: 20Gi
  - Azure: 20Gi
- **Service**: Headless service for DNS-based discovery
- **Configuration**: Via ConfigMap (host, port)
- **Credentials**: Via Secret (password)
- **Health Check**: Redis PING command

### 3. MinIO Object Storage
- **Type**: StatefulSet (1 replica)
- **Image**: `minio/minio:latest`
- **Ports**: 9000 (API), 9001 (Console)
- **Storage**: PVC with data persistence
  - Local/Dev: 20Gi
  - AWS: 100Gi
  - GCP: 100Gi
  - Azure: 100Gi
- **Service**: ClusterIP service with two ports
- **Configuration**: Via ConfigMap (endpoint, bucket, secure mode)
- **Credentials**: Via Secret (root user, root password)
- **Health Check**: MinIO health endpoints

### 4. Flask API Backend
- **Type**: Deployment (1-3 replicas depending on environment)
- **Image**: `icecharts-api:latest`
- **Port**: 5000 (HTTP)
- **Service**: ClusterIP service
- **Configuration**: Via ConfigMap (all non-sensitive config)
- **Credentials**: Via Secret (all sensitive keys and tokens)
- **Init Container**: Waits for PostgreSQL connectivity
- **Health Checks**:
  - Liveness: `/api/v1/health` endpoint
  - Readiness: `/api/v1/health` endpoint
- **Resource Scaling**: Pod Anti-affinity for distribution
- **Security**: Non-root user, read-only filesystem (except /tmp)

### 5. React Frontend
- **Type**: Deployment (1-3 replicas depending on environment)
- **Image**: `icecharts-web:latest`
- **Port**: 3000 (HTTP)
- **Service**: ClusterIP service
- **Configuration**: Via ConfigMap (API URL, base path)
- **Health Checks**:
  - Liveness: HTTP GET to root path
  - Readiness: HTTP GET to root path
- **Resource Scaling**: Pod Anti-affinity for distribution
- **Security**: Non-root user, read-only filesystem (except /tmp)

## Configuration Management

### ConfigMap (`base/configmap.yaml`)

Contains non-sensitive application configuration:
- Database connection details (host, port, database name, user)
- Cache configuration (Redis host, port, TTL)
- Storage configuration (MinIO endpoint, bucket, secure mode)
- Application ports (API, Web, Monitoring)
- Feature flags (analytics, reports, user management)
- Logging configuration (level, format, file paths)
- Performance settings (connection limits, timeouts)
- Rate limiting configuration
- And 50+ other application settings

**Size**: ~4KB
**Update Strategy**: Edit ConfigMap and restart pods for changes to take effect

### Secret (`base/secret.yaml`)

Contains sensitive values (base64 encoded):
- Database password
- Redis password
- MinIO credentials
- JWT secrets
- Flask secrets
- Admin credentials
- OAuth configuration (optional)
- Email SMTP credentials (optional)
- TLS certificates (optional)

**Security Warning**: The provided secret.yaml contains development credentials only. For production, use:
- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager
- External Secrets Operator
- HashiCorp Vault

## Storage Configuration

### Stateful Components

All persistent data is managed through StatefulSets with volumeClaimTemplates:

1. **PostgreSQL**
   - Default: Local storage class
   - AWS: EBS GP3 (3000 IOPS, 125 MB/s)
   - GCP: PD-SSD with regional redundancy
   - Azure: Premium Managed Disk (Premium_LRS)

2. **Redis**
   - Same storage configuration as PostgreSQL
   - Uses append-only file mode for durability

3. **MinIO**
   - Same storage configuration as PostgreSQL
   - Requires larger storage size for object data

## Network Configuration

### Services

| Component | Type | Port | Purpose |
|-----------|------|------|---------|
| postgres | Headless | 5432 | Database (internal only) |
| redis | Headless | 6379 | Cache (internal only) |
| minio | ClusterIP | 9000,9001 | Object storage |
| api | ClusterIP | 5000 | API backend |
| web | ClusterIP | 3000 | Frontend |

### Ingress

**Local Development**: Optional NGINX ingress (icecharts.local)
**AWS**: ALB ingress controller with health checks
**GCP**: Cloud Load Balancer ingress
**Azure**: Application Gateway ingress controller

## Resource Allocation

### Development (Local)

```
api:       256Mi memory, 100m CPU (requests)  | 512Mi memory, 250m CPU (limits)
web:       128Mi memory, 50m CPU (requests)   | 256Mi memory, 100m CPU (limits)
postgres:  256Mi memory, 100m CPU (requests)  | 512Mi memory, 250m CPU (limits)
redis:     64Mi memory, 50m CPU (requests)    | 256Mi memory, 100m CPU (limits)
minio:     256Mi memory, 100m CPU (requests)  | 512Mi memory, 250m CPU (limits)
```

### Production (AWS/GCP/Azure)

```
api:       512Mi memory, 250m CPU (requests) | 2Gi memory, 1000m CPU (limits)
web:       256Mi memory, 100m CPU (requests) | 1Gi memory, 500m CPU (limits)
postgres:  1Gi memory, 500m CPU (requests)   | 4Gi memory, 2000m CPU (limits)
redis:     512Mi memory, 250m CPU (requests) | 2Gi memory, 1000m CPU (limits)
minio:     512Mi memory, 250m CPU (requests) | 2Gi memory, 1000m CPU (limits)
```

## Replication

### Development (Local)
- All stateless services: 1 replica
- Stateful services: 1 replica (not scalable)

### Production (All Cloud Providers)
- API: 3 replicas (configurable)
- Web: 3 replicas (configurable)
- Database: 1 replica (StatefulSet)
- Cache: 1 replica (StatefulSet)
- Storage: 1 replica (StatefulSet)

## Deployment Instructions

See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

## Testing Manifests

All manifests have been validated with `kubectl kustomize`:

```bash
# Validate base
kubectl kustomize k8s/manifests/base/ > /dev/null

# Validate each overlay
kubectl kustomize k8s/manifests/overlays/local/ > /dev/null
kubectl kustomize k8s/manifests/overlays/aws/ > /dev/null
kubectl kustomize k8s/manifests/overlays/gcp/ > /dev/null
kubectl kustomize k8s/manifests/overlays/azure/ > /dev/null
```

## Total Files

- **41 YAML manifest files**
- **Base**: 22 files (kustomizations, deployments, services, PVCs)
- **Overlays**: 19 files (patches and ingress configurations)
- **Documentation**: 3 files (this guide + deployment guide + quick reference)

## Key Features

1. **No Templating**: Pure YAML manifests, no template variables
2. **Kustomize Native**: Full strategic merge patch support
3. **Multi-Cloud**: Optimized configurations for AWS, GCP, Azure, and local
4. **Production Ready**: Includes health checks, resource limits, security contexts
5. **Scalable**: Easy to adjust replicas and resources via patches
6. **Secure**: Secrets management, non-root containers, read-only filesystems
7. **Observable**: Prometheus scrape annotations, health endpoints

## File Statistics

```
Total YAML Files:        41
Base Manifests:          22
Overlay Manifests:       19
Documentation Files:     3
Total Size:              ~500KB (including comments and formatting)
```

## Notes

- All manifests default to the `icecharts` namespace
- ConfigMap and Secret are shared across all environments
- Environment-specific configuration is applied via patches
- Storage classes are created only when needed by overlays
- Ingress resources are optional (local overlay provides example)
- All containers use non-root users with reduced privileges
- Pod anti-affinity ensures distribution across nodes
