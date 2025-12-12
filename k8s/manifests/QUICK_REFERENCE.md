# Kustomize Quick Reference

Quick commands for deploying IceCharts to Kubernetes.

## One-Line Deployment

```bash
# Local development
kubectl apply -k k8s/manifests/overlays/local/

# AWS EKS
kubectl apply -k k8s/manifests/overlays/aws/

# GCP GKE
kubectl apply -k k8s/manifests/overlays/gcp/

# Azure AKS
kubectl apply -k k8s/manifests/overlays/azure/
```

## Verify Deployment

```bash
# Watch pod startup
kubectl get pods -n icecharts -w

# Check services
kubectl get svc -n icecharts

# Describe specific pod
kubectl describe pod api-0 -n icecharts

# View logs
kubectl logs -n icecharts api-0
kubectl logs -n icecharts web-0
kubectl logs -n icecharts postgres-0
```

## Access Services Locally

```bash
# API (Flask backend)
kubectl port-forward -n icecharts svc/api 5000:5000
# Access at: http://localhost:5000/api/v1/health

# Web (React frontend)
kubectl port-forward -n icecharts svc/web 3000:3000
# Access at: http://localhost:3000

# PostgreSQL
kubectl port-forward -n icecharts svc/postgres 5432:5432
# Connection: postgresql://icecharts_user:changeme@localhost:5432/icecharts

# Redis
kubectl port-forward -n icecharts svc/redis 6379:6379
# Connection: redis://:changeme@localhost:6379/0

# MinIO Console
kubectl port-forward -n icecharts svc/minio 9001:9001
# Access at: http://localhost:9001 (minioadmin:minioadmin)
```

## Database Operations

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n icecharts -- psql -U icecharts_user -d icecharts

# Backup database
kubectl exec -it postgres-0 -n icecharts -- pg_dump -U icecharts_user icecharts > backup.sql

# Restore database
cat backup.sql | kubectl exec -i postgres-0 -n icecharts -- psql -U icecharts_user icecharts

# Connect to Redis
kubectl exec -it redis-0 -n icecharts -- redis-cli -a changeme

# Redis INFO
kubectl exec -it redis-0 -n icecharts -- redis-cli -a changeme INFO
```

## Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap icecharts-config -n icecharts

# Edit Secret
kubectl edit secret icecharts-secret -n icecharts

# Apply new configuration (pods will restart)
kubectl rollout restart deployment api -n icecharts
kubectl rollout restart deployment web -n icecharts
```

## Scale Services

```bash
# Scale API to 5 replicas
kubectl scale deployment api --replicas=5 -n icecharts

# Scale Web to 3 replicas
kubectl scale deployment web --replicas=3 -n icecharts

# Watch scaling
kubectl get pods -n icecharts -w
```

## Rolling Update

```bash
# Update image
kubectl set image deployment/api api=your-registry/icecharts-api:v1.0.4 -n icecharts

# Check rollout status
kubectl rollout status deployment/api -n icecharts

# Rollback if needed
kubectl rollout undo deployment/api -n icecharts
```

## Check Health

```bash
# API health
curl $(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}'):5000/api/v1/health

# Web status
kubectl get pods -n icecharts -o wide

# Services status
kubectl get svc -n icecharts

# Persistent volumes
kubectl get pvc -n icecharts
```

## Troubleshoot Issues

```bash
# Get all events
kubectl get events -n icecharts --sort-by='.lastTimestamp'

# Describe pod for errors
kubectl describe pod <pod-name> -n icecharts

# Check logs for errors
kubectl logs -n icecharts <pod-name> | grep -i error

# Get pod resource usage
kubectl top pods -n icecharts

# Get node resource usage
kubectl top nodes
```

## Delete and Cleanup

```bash
# Delete all resources
kubectl delete -k k8s/manifests/overlays/<environment>/

# Delete namespace (removes all resources)
kubectl delete namespace icecharts

# Delete only deployments (keep data)
kubectl delete deployment,pod -l app.kubernetes.io/name=icecharts -n icecharts

# Check what would be deleted (dry-run)
kubectl delete -k k8s/manifests/overlays/<environment>/ --dry-run=client
```

## Preview Changes

```bash
# View generated manifests
kustomize build k8s/manifests/overlays/local/ | less

# Generate and save
kustomize build k8s/manifests/overlays/aws/ > deployed-manifests.yaml

# Check differences
kustomize build k8s/manifests/overlays/local/ > local.yaml
kustomize build k8s/manifests/overlays/aws/ > aws.yaml
diff local.yaml aws.yaml
```

## Environment Variables

### Common Environment Variables

```bash
# Database
POSTGRES_DB=icecharts
POSTGRES_USER=icecharts_user
DB_HOST=postgres.icecharts.svc.cluster.local
DB_PORT=5432

# Cache
REDIS_HOST=redis.icecharts.svc.cluster.local
REDIS_PORT=6379

# Storage
MINIO_ENDPOINT=minio.icecharts.svc.cluster.local:9000
MINIO_BUCKET=icecharts

# API
API_PORT=5000
FLASK_ENV=production

# Web
WEB_PORT=3000
NODE_ENV=production

# Logging
LOG_LEVEL=info
LOG_FORMAT=json
```

## Kustomize Commands

```bash
# Build manifests
kustomize build k8s/manifests/base
kustomize build k8s/manifests/overlays/local

# Edit patches
kustomize edit set replicas deployment/api=5 -k overlays/aws

# Edit images
kustomize edit set image api=new-api:latest -k overlays/aws

# Validate manifests
kubectl apply -k overlays/local --validate=true --dry-run=client
```

## Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias k='kubectl'
alias kn='kubectl -n icecharts'
alias km='kustomize build'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias kpf='kubectl port-forward'
alias kgs='kubectl get svc -n icecharts'
alias kgp='kubectl get pods -n icecharts'
alias kgpw='kubectl get pods -n icecharts -w'
```

## Requirements Checklist

- [ ] Kubernetes cluster v1.20+ running
- [ ] kubectl installed and configured
- [ ] kustomize installed (or use `kubectl kustomize`)
- [ ] Storage provisioner available
- [ ] Docker images built/available
- [ ] Credentials and secrets prepared
- [ ] Network/firewall rules configured
- [ ] Ingress controller installed (production)

## Support

For issues or questions:
1. Check logs: `kubectl logs -n icecharts <pod>`
2. Describe pod: `kubectl describe pod <pod> -n icecharts`
3. Check events: `kubectl get events -n icecharts`
4. Review DEPLOYMENT_GUIDE.md for detailed troubleshooting
