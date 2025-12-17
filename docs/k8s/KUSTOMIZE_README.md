# IceCharts Kubernetes Kustomize Manifests

## Overview

Complete Kustomize manifests for deploying IceCharts to Kubernetes clusters without Helm. Supports local development, AWS EKS, Google Cloud GKE, and Azure AKS production environments.

## What's Included

### Documentation
- **DEPLOYMENT_GUIDE.md** - Comprehensive deployment and configuration guide
- **QUICK_REFERENCE.md** - Quick command reference for common operations
- **MANIFEST_STRUCTURE.md** - Detailed manifest structure and organization

### Manifests (41 YAML files)

#### Base Configuration
- Kubernetes Namespace definition
- Shared ConfigMap (100+ application settings)
- Shared Secret (sensitive credentials)
- 5 component kustomizations:
  - PostgreSQL 17 StatefulSet with persistent storage
  - Redis 7 StatefulSet with persistent storage
  - MinIO object storage StatefulSet
  - Flask API backend Deployment
  - React frontend Deployment

#### Environment Overlays (4 configurations)
- **Local**: Single-replica development setup
- **AWS**: 3-replica production with EBS GP3 storage and ALB ingress
- **GCP**: 3-replica production with PD-SSD storage and Cloud Load Balancer
- **Azure**: 3-replica production with managed disks and Application Gateway

### Components

Each component is fully configured with:
- Service definitions (Headless for StatefulSets, ClusterIP for Deployments)
- Health checks (liveness and readiness probes)
- Resource limits and requests
- Security contexts (non-root users, read-only filesystem)
- Pod anti-affinity for distribution
- Volume claims and persistence configuration

## Quick Start

### Prerequisites
- Kubernetes 1.20+ cluster
- `kubectl` configured
- Docker images built (`icecharts-api:latest`, `icecharts-web:latest`)

### Deploy to Local Kubernetes

```bash
# Create all resources
kubectl apply -k k8s/manifests/overlays/local/

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts

# Port forward to access services
kubectl port-forward -n icecharts svc/api 5000:5000
kubectl port-forward -n icecharts svc/web 3000:3000
```

### Deploy to Production (AWS)

```bash
# Ensure AWS Load Balancer Controller addon is installed
kubectl apply -k k8s/manifests/overlays/aws/

# Check deployment status
kubectl get pods -n icecharts
kubectl get ingress -n icecharts

# Get load balancer DNS
kubectl get ingress -n icecharts icecharts-aws -o wide
```

### Deploy to Production (GCP)

```bash
# Ensure Cloud Load Balancer integration is configured
kubectl apply -k k8s/manifests/overlays/gcp/

# Check deployment status
kubectl get pods -n icecharts
kubectl get ingress -n icecharts
```

### Deploy to Production (Azure)

```bash
# Ensure Application Gateway Ingress Controller addon is installed
kubectl apply -k k8s/manifests/overlays/azure/

# Check deployment status
kubectl get pods -n icecharts
kubectl get ingress -n icecharts
```

## Configuration

### Build and Push Images

```bash
# Build Docker images
docker build -t icecharts-api:latest ./services/flask-backend
docker build -t icecharts-web:latest ./services/webui

# Push to your registry
docker tag icecharts-api:latest your-registry/icecharts-api:v1.0.3
docker tag icecharts-web:latest your-registry/icecharts-web:v1.0.3

docker push your-registry/icecharts-api:v1.0.3
docker push your-registry/icecharts-web:v1.0.3
```

### Update Image References

Edit `base/api/deployment.yaml` and `base/web/deployment.yaml`:

```yaml
containers:
- name: api
  image: your-registry/icecharts-api:v1.0.3
```

### Configure Secrets

For production, replace the insecure secrets in `base/secret.yaml`:

```bash
kubectl create secret generic icecharts-secret \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=REDIS_PASSWORD=$(openssl rand -base64 32) \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -base64 32) \
  -n icecharts --dry-run=client -o yaml | kubectl apply -f -
```

Or use external secret management:
- AWS Secrets Manager (with External Secrets Operator)
- Azure Key Vault (with Azure Workload Identity)
- GCP Secret Manager
- HashiCorp Vault

### Customize Configuration

Edit `base/configmap.yaml` to customize application settings:

```yaml
kubectl edit configmap icecharts-config -n icecharts
```

Common customizations:
- Database name and user
- Redis host and port
- MinIO endpoint and bucket
- API and Web ports
- Logging levels
- Feature flags
- CORS origins
- Etc.

## Directory Structure

```
k8s/manifests/
├── base/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   ├── api/
│   └── web/
└── overlays/
    ├── local/
    ├── aws/
    ├── gcp/
    └── azure/
```

See `k8s/manifests/MANIFEST_STRUCTURE.md` for detailed structure.

## Features

### Security
- Non-root container users
- Read-only root filesystem (except /tmp)
- No privileged containers
- Pod security policies ready
- Namespace isolation
- RBAC compatible

### High Availability
- Multi-replica deployments
- Pod anti-affinity
- Health checks
- Graceful shutdown
- Rolling updates

### Observability
- Prometheus scrape annotations
- Health check endpoints
- Log configuration
- Resource monitoring
- Event tracking

### Storage
- Persistent volumes for databases
- Cloud-specific storage classes
- Automatic PVC creation via StatefulSets
- Data retention policies

### Networking
- Headless services for StatefulSets
- ClusterIP services for Deployments
- Ingress configurations per cloud provider
- Service discovery via DNS

## Customization

### Scaling Replicas

```bash
# Modify overlay replica-patch.yaml
# Or use kubectl
kubectl scale deployment api --replicas=5 -n icecharts
```

### Resource Limits

Edit `overlays/{env}/resources-patch.yaml` to adjust:
- Memory requests/limits
- CPU requests/limits
- For all components

### Storage Size

Edit `base/{component}/pvc.yaml` to adjust storage sizes.

### Ingress Configuration

Edit `overlays/{env}/ingress-patch.yaml` to customize:
- DNS names
- TLS certificates
- Health check paths
- WAF rules (cloud-specific)

## Monitoring and Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n icecharts
kubectl describe pod -n icecharts api-0
kubectl logs -n icecharts api-0
```

### Port Forward
```bash
kubectl port-forward -n icecharts svc/api 5000:5000
kubectl port-forward -n icecharts svc/postgres 5432:5432
```

### Database Access
```bash
kubectl exec -it postgres-0 -n icecharts -- psql -U icecharts_user -d icecharts
```

### Redis Access
```bash
kubectl exec -it redis-0 -n icecharts -- redis-cli -a <password>
```

## Differences from Helm Chart

This Kustomize implementation provides:

1. **Transparency**: Plain YAML manifests, easy to understand and modify
2. **No Template Engine**: Pure YAML strategic merge patches
3. **Environment Isolation**: Complete overlay separation per environment
4. **Direct kubectl**: Deploy with `kubectl apply -k`, no additional tools
5. **Git-Friendly**: All manifests in version control, no runtime generation
6. **Patch-Based**: Changes via Kustomize patches, base remains unchanged

## Production Checklist

- [ ] Build and push Docker images to your registry
- [ ] Update image references in base/api/deployment.yaml and base/web/deployment.yaml
- [ ] Generate secure credentials for all Secrets
- [ ] Configure external secret management
- [ ] Set up persistent volume provisioning
- [ ] Install ingress controller (ALB, Cloud LB, or App Gateway)
- [ ] Configure DNS records for ingress hosts
- [ ] Set up TLS certificates (Let's Encrypt or cloud-managed)
- [ ] Configure backup strategy for databases
- [ ] Set up monitoring and alerting
- [ ] Configure network policies
- [ ] Test disaster recovery procedures
- [ ] Document any environment-specific changes
- [ ] Schedule regular security updates

## Versioning

- **Manifest Version**: v1.0.3
- **Kubernetes Minimum**: v1.20
- **Kustomize Version**: v4.0+

## Support

For detailed deployment instructions, see:
- `k8s/manifests/DEPLOYMENT_GUIDE.md` - Complete guide
- `k8s/manifests/QUICK_REFERENCE.md` - Command reference
- `k8s/manifests/MANIFEST_STRUCTURE.md` - Technical details

## License

These Kubernetes manifests are provided as part of IceCharts application and are subject to the same license as the IceCharts project.

## Next Steps

1. Read `k8s/manifests/DEPLOYMENT_GUIDE.md` for detailed setup instructions
2. Review `k8s/manifests/MANIFEST_STRUCTURE.md` to understand component architecture
3. Customize `base/configmap.yaml` and `base/secret.yaml` for your environment
4. Update Docker image references to your registry
5. Deploy to your Kubernetes cluster with `kubectl apply -k`

---

**Created**: December 12, 2025
**Status**: Production Ready
**Tested**: All overlays validated with kubectl kustomize
