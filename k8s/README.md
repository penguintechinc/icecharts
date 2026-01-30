# IceCharts Kubernetes Deployment

Kubernetes deployment manifests for IceCharts, supporting three deployment methods:
Helm v3, Kustomize, and raw kubectl manifests.

## Architecture

| Component  | Image                                              | Port(s)     |
|------------|----------------------------------------------------|-------------|
| Web (nginx)| registry-dal2.penguintech.io/icecharts-web         | 8080        |
| API (Flask)| registry-dal2.penguintech.io/icecharts-api         | 5000        |
| PostgreSQL | postgres:17-alpine                                 | 5432        |
| Redis      | redis:7-alpine                                     | 6379        |
| MinIO      | minio/minio:latest                                 | 9000, 9001  |

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured with cluster access
- Helm v3 (for Helm deployment)
- Kustomize (for Kustomize deployment, or use `kubectl -k`)
- Container images built and pushed to registry

## Quick Start (Beta - dal2.penguintech.io)

### Method 1: Helm (Recommended)

```bash
# Install or upgrade
helm upgrade --install icecharts ./k8s/helm/icecharts \
  --namespace icecharts-beta \
  --create-namespace \
  --values ./k8s/helm/icecharts/values-beta.yaml \
  --set image.tag=v1.0.2-beta

# Check status
helm status icecharts -n icecharts-beta

# Rollback
helm rollback icecharts -n icecharts-beta

# Uninstall
helm uninstall icecharts -n icecharts-beta
```

### Method 2: Kustomize

```bash
# Apply beta overlay
kubectl apply -k k8s/kustomize/overlays/beta

# Preview rendered manifests
kubectl kustomize k8s/kustomize/overlays/beta

# Delete
kubectl delete -k k8s/kustomize/overlays/beta
```

### Method 3: kubectl Raw Manifests

```bash
# Create namespace
kubectl apply -f k8s/manifests/namespace.yaml

# Create config and secrets (edit secret.yaml first!)
kubectl apply -f k8s/manifests/configmap.yaml
kubectl apply -f k8s/manifests/secret.yaml

# Deploy stateful services
kubectl apply -f k8s/manifests/postgres-statefulset.yaml
kubectl apply -f k8s/manifests/postgres-service.yaml
kubectl apply -f k8s/manifests/redis-statefulset.yaml
kubectl apply -f k8s/manifests/redis-service.yaml
kubectl apply -f k8s/manifests/minio-statefulset.yaml
kubectl apply -f k8s/manifests/minio-service.yaml

# Deploy application
kubectl apply -f k8s/manifests/web-deployment.yaml
kubectl apply -f k8s/manifests/web-service.yaml
kubectl apply -f k8s/manifests/api-deployment.yaml
kubectl apply -f k8s/manifests/api-service.yaml

# Create ingress
kubectl apply -f k8s/manifests/ingress.yaml
```

## Configuration

### Secrets

**Before deploying, update secret values.** Never commit real secrets to Git.

For Helm, override in a local values file:
```bash
helm upgrade --install icecharts ./k8s/helm/icecharts \
  --set secrets.SECRET_KEY="your-secret" \
  --set secrets.DB_PASSWORD="your-db-password"
```

For kubectl/Kustomize, edit the `secret.yaml` file or create secrets via CLI:
```bash
kubectl -n icecharts-beta create secret generic icecharts-secret \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=SECURITY_PASSWORD_SALT="$(openssl rand -hex 16)" \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=JWT_ACCESS_TOKEN_EXPIRES="3600" \
  --from-literal=JWT_REFRESH_TOKEN_EXPIRES="2592000" \
  --from-literal=DB_USER="icecharts_user" \
  --from-literal=DB_PASSWORD="$(openssl rand -hex 16)" \
  --from-literal=REDIS_PASSWORD="$(openssl rand -hex 16)" \
  --from-literal=MINIO_ACCESS_KEY="$(openssl rand -hex 16)" \
  --from-literal=MINIO_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=DEFAULT_ADMIN_EMAIL="admin@penguintech.io" \
  --from-literal=DEFAULT_ADMIN_PASSWORD="$(openssl rand -base64 16)" \
  --from-literal=LICENSE_KEY=""
```

### Environment Overlays

| Environment | Namespace       | Host                        | Replicas (web/api) |
|-------------|-----------------|-----------------------------|--------------------|
| dev         | icecharts-dev   | (port-forward)              | 1/1                |
| beta        | icecharts-beta  | icecharts.penguintech.io    | 2/2                |
| prod        | icecharts-prod  | icecharts.penguincloud.io   | 3/3                |

### Resource Limits

| Component  | Requests (CPU/Mem) | Limits (CPU/Mem)  | Storage |
|------------|--------------------|-------------------|---------|
| Web        | 100m / 256Mi       | 500m / 512Mi      | -       |
| API        | 200m / 512Mi       | 1 / 1Gi           | -       |
| PostgreSQL | 200m / 512Mi       | 1 / 2Gi           | 10Gi    |
| Redis      | 50m / 128Mi        | 200m / 256Mi      | 5Gi     |
| MinIO      | 100m / 256Mi       | 500m / 1Gi        | 20Gi    |

## Verification

```bash
# Check all pods
kubectl -n icecharts-beta get pods

# Check services
kubectl -n icecharts-beta get svc

# Check ingress
kubectl -n icecharts-beta get ingress

# Test web UI
curl -I https://icecharts.penguintech.io/

# Test API health
curl https://icecharts.penguintech.io/api/v1/health

# View logs
kubectl -n icecharts-beta logs -l app=web --tail=50
kubectl -n icecharts-beta logs -l app=api --tail=50

# Describe pods (for troubleshooting)
kubectl -n icecharts-beta describe pods
```

## Security

All pods run as non-root users:
- Web (nginx): UID 101
- API (Flask): UID 1000
- PostgreSQL: UID 999
- Redis: UID 999
- MinIO: UID 1000

Security contexts enforce:
- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- `capabilities.drop: ["ALL"]`

## Directory Structure

```
k8s/
├── README.md                    # This file
├── helm/                        # Helm v3 chart
│   └── icecharts/
│       ├── Chart.yaml
│       ├── values.yaml          # Default values
│       ├── values-dev.yaml      # Development overrides
│       ├── values-beta.yaml     # Beta/staging overrides
│       ├── values-prod.yaml     # Production overrides
│       └── templates/           # Helm templates
├── kustomize/                   # Kustomize overlays
│   ├── base/                    # Base resources
│   └── overlays/
│       ├── dev/                 # Development overlay
│       ├── beta/                # Beta/staging overlay
│       └── prod/                # Production overlay
└── manifests/                   # Raw kubectl manifests
```

## Troubleshooting

### Common Issues

**CreateContainerConfigError**: Missing Secret or ConfigMap
```bash
kubectl -n icecharts-beta get secret icecharts-secret
kubectl -n icecharts-beta get configmap icecharts-config
```

**ImagePullBackOff**: Wrong registry or tag
```bash
kubectl -n icecharts-beta describe pod <pod-name> | grep -A5 "Events"
```

**CrashLoopBackOff**: Application error on startup
```bash
kubectl -n icecharts-beta logs <pod-name> --previous
```

**Port issues**: Verify service ports match container ports
```bash
kubectl -n icecharts-beta get svc -o wide
kubectl -n icecharts-beta get endpoints
```
