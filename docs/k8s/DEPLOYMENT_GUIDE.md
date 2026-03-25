# IceCharts Kubernetes Deployment Guide

This guide provides complete instructions for deploying IceCharts to Kubernetes using Kustomize manifests without Helm.

## Directory Structure

```
k8s/manifests/
├── base/                          # Base Kustomization (shared configuration)
│   ├── kustomization.yaml        # Main base kustomization file
│   ├── namespace.yaml            # Kubernetes namespace definition
│   ├── configmap.yaml            # Application configuration (non-sensitive)
│   ├── secret.yaml               # Application secrets (base64 encoded)
│   ├── postgres/                 # PostgreSQL database
│   │   ├── kustomization.yaml
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── redis/                    # Redis cache
│   │   ├── kustomization.yaml
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── minio/                    # MinIO object storage
│   │   ├── kustomization.yaml
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── api/                      # Flask API backend
│   │   ├── kustomization.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── web/                      # React frontend
│       ├── kustomization.yaml
│       ├── deployment.yaml
│       └── service.yaml
└── overlays/                      # Environment-specific overlays
    ├── local/                    # Local development
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   ├── resources-patch.yaml
    │   └── ingress-patch.yaml
    ├── aws/                      # AWS EKS production
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   ├── resources-patch.yaml
    │   ├── storage-class-patch.yaml
    │   └── ingress-patch.yaml
    ├── gcp/                      # GCP GKE production
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   ├── resources-patch.yaml
    │   ├── storage-class-patch.yaml
    │   └── ingress-patch.yaml
    └── azure/                    # Azure AKS production
        ├── kustomization.yaml
        ├── replica-patch.yaml
        ├── resources-patch.yaml
        ├── storage-class-patch.yaml
        └── ingress-patch.yaml
```

## Prerequisites

### Required Tools

- `kubectl` >= 1.20 (Kubernetes client)
- `kustomize` >= 4.0 or `kubectl` with built-in kustomize
- Access to a Kubernetes cluster (1.20+)
- Docker images for API and Web services (pre-built or build locally)

### Kubernetes Cluster Requirements

- Minimum 2 nodes with 4 CPU and 8GB RAM each
- Storage provisioner (EBS for AWS, PD for GCP, Managed Disks for Azure)
- Network policies and ingress controller configured

### Installation

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/

# Verify installation
kubectl version --client
kustomize version
```

## Quick Start

### 1. Local Development Deployment

For local testing with Docker Desktop, Minikube, or Kind:

```bash
# Create the namespace and deploy all services
kubectl apply -k k8s/manifests/overlays/local/

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts

# Port forward to access services
kubectl port-forward -n icecharts svc/api 5000:5000
kubectl port-forward -n icecharts svc/web 3000:3000
kubectl port-forward -n icecharts svc/postgres 5432:5432
```

### 2. AWS EKS Production Deployment

```bash
# Prerequisites: EKS cluster created and kubectl configured
# Ensure AWS Load Balancer Controller addon is installed

kubectl apply -k k8s/manifests/overlays/aws/

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts
kubectl get ingress -n icecharts

# Get Load Balancer DNS
kubectl get ingress -n icecharts icecharts-aws -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### 3. GCP GKE Production Deployment

```bash
# Prerequisites: GKE cluster created and kubectl configured
# Configure Cloud Load Balancer with static IP

kubectl apply -k k8s/manifests/overlays/gcp/

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts
kubectl get ingress -n icecharts

# Get Load Balancer IP
kubectl get ingress -n icecharts icecharts-gcp -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 4. Azure AKS Production Deployment

```bash
# Prerequisites: AKS cluster created and kubectl configured
# Ensure Application Gateway Ingress Controller (AGIC) addon is installed

kubectl apply -k k8s/manifests/overlays/azure/

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts
kubectl get ingress -n icecharts

# Get Application Gateway public IP
kubectl get ingress -n icecharts icecharts-azure -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

## Configuration

### ConfigMap (Application Configuration)

The `base/configmap.yaml` contains all non-sensitive configuration values:

- Database connection details (host, port, name)
- Redis cache configuration
- MinIO storage configuration
- API and Web service ports
- Feature flags
- Logging configuration

**Update for your environment:**

```bash
kubectl edit configmap icecharts-config -n icecharts
```

Common variables to customize:

```yaml
POSTGRES_DB: "icecharts"
POSTGRES_USER: "icecharts_user"
REDIS_HOST: "redis.icecharts.svc.cluster.local"
MINIO_ENDPOINT: "minio.icecharts.svc.cluster.local:9000"
VITE_API_URL: "http://api.icecharts.svc.cluster.local:5000"
CORS_ORIGINS: "http://localhost:3000"
```

### Secret (Application Credentials)

The `base/secret.yaml` contains sensitive values (base64 encoded):

- Database passwords
- Redis password
- MinIO credentials
- JWT secrets
- API keys

**WARNING: The provided secret.yaml contains default development credentials only. For production:**

1. Generate secure random values:

```bash
# Generate secure credentials
openssl rand -base64 32  # For passwords
```

2. Create a secret from your values:

```bash
kubectl create secret generic icecharts-secret \
  --from-literal=POSTGRES_PASSWORD=<your-password> \
  --from-literal=REDIS_PASSWORD=<your-password> \
  --from-literal=MINIO_ROOT_PASSWORD=<your-password> \
  --from-literal=JWT_SECRET_KEY=<your-secret> \
  -n icecharts --dry-run=client -o yaml | kubectl apply -f -
```

3. Or use external secret management:
   - AWS Secrets Manager
   - Azure Key Vault
   - GCP Secret Manager
   - HashiCorp Vault

### Docker Images

Update the image references in the deployments to point to your container registry:

```bash
# For local development (build locally)
docker build -t icecharts-api:latest ./services/flask-backend
docker build -t icecharts-web:latest ./services/webui

# For production (push to registry)
docker tag icecharts-api:latest your-registry.azurecr.io/icecharts-api:v1.0.3
docker tag icecharts-web:latest your-registry.azurecr.io/icecharts-web:v1.0.3

docker push your-registry.azurecr.io/icecharts-api:v1.0.3
docker push your-registry.azurecr.io/icecharts-web:v1.0.3
```

Then update the deployment files:

```yaml
# In base/api/deployment.yaml and base/web/deployment.yaml
containers:
- name: api
  image: your-registry.azurecr.io/icecharts-api:v1.0.3
```

Or use image pull secrets for private registries:

```bash
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.azurecr.io \
  --docker-username=<username> \
  --docker-password=<password> \
  -n icecharts
```

## Customization

### View Generated Manifests

To preview what Kustomize will deploy without applying:

```bash
# Local environment
kustomize build k8s/manifests/overlays/local/ | less

# AWS environment
kustomize build k8s/manifests/overlays/aws/ | less

# GCP environment
kustomize build k8s/manifests/overlays/gcp/ | less

# Azure environment
kustomize build k8s/manifests/overlays/azure/ | less
```

### Modify Overlays

Each overlay allows customization through patches:

1. **replica-patch.yaml** - Adjust number of replicas for scaling
2. **resources-patch.yaml** - Modify CPU/memory limits
3. **storage-class-patch.yaml** - Use different storage classes
4. **ingress-patch.yaml** - Configure ingress for your domain/DNS

Example: Scale API to 5 replicas in AWS

```yaml
# overlays/aws/replica-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 5
```

Then redeploy:

```bash
kubectl apply -k k8s/manifests/overlays/aws/
```

### Custom Ingress Configuration

**For AWS with custom domain:**

```bash
kubectl edit ingress icecharts-aws -n icecharts

# Add host rule
spec:
  rules:
  - host: icecharts.yourdomain.com
    http:
      paths: [...]
```

**For GCP with static IP:**

```bash
# Reserve static IP
gcloud compute addresses create icecharts-ip --global

# Update ingress annotation
kubectl edit ingress icecharts-gcp -n icecharts
# alb.ingress.kubernetes.io/listen-ports: 'icecharts-ip'
```

## Monitoring and Troubleshooting

### Check Pod Status

```bash
# List all pods
kubectl get pods -n icecharts

# Describe a pod
kubectl describe pod <pod-name> -n icecharts

# View pod logs
kubectl logs -n icecharts <pod-name>
kubectl logs -n icecharts <pod-name> -c <container-name>

# Stream logs
kubectl logs -n icecharts <pod-name> -f
```

### Database Connection Issues

```bash
# Test PostgreSQL connectivity
kubectl exec -it postgres-0 -n icecharts -- psql -U icecharts_user -d icecharts

# Check database logs
kubectl logs -n icecharts postgres-0
```

### Redis Connection Issues

```bash
# Test Redis connectivity
kubectl exec -it redis-0 -n icecharts -- redis-cli -a <password> ping

# Check Redis logs
kubectl logs -n icecharts redis-0
```

### API Service Issues

```bash
# Check API logs
kubectl logs -n icecharts api-<pod-id>

# Port-forward to debug
kubectl port-forward -n icecharts svc/api 5000:5000

# Test health endpoint
curl http://localhost:5000/api/v1/health
```

### Storage Issues

```bash
# Check persistent volumes
kubectl get pv -n icecharts
kubectl get pvc -n icecharts

# Describe a PVC
kubectl describe pvc postgres-storage-postgres-0 -n icecharts

# Check storage class
kubectl get storageclass
```

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Pods stuck in Pending | No storage provisioner | Install storage driver (EBS CSI, GCP PD CSI, Azure Disk CSI) |
| ImagePullBackOff | Image not found | Build and push images, update image references |
| CrashLoopBackOff | Application error | Check logs with `kubectl logs`, verify configuration |
| Database connection refused | Database not ready | Check postgres pod status, ensure service DNS works |
| Redis authentication error | Wrong password | Verify REDIS_PASSWORD in secret matches configuration |

## Production Recommendations

### Security

1. **Use external secrets management:**
   - AWS Secrets Manager
   - Azure Key Vault
   - GCP Secret Manager

2. **Enable RBAC and network policies:**
   ```bash
   # Restrict pod-to-pod communication
   kubectl apply -f network-policies.yaml
   ```

3. **Enable pod security standards:**
   ```bash
   kubectl label namespace icecharts pod-security.kubernetes.io/enforce=restricted
   ```

4. **Use TLS for ingress:**
   - Enable HTTPS on ingress controller
   - Install cert-manager for Let's Encrypt certificates

### High Availability

1. **Increase replicas:**
   ```yaml
   # overlays/aws/replica-patch.yaml
   replicas: 5  # Or higher based on load
   ```

2. **Enable pod disruption budgets:**
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: api-pdb
   spec:
     minAvailable: 1
     selector:
       matchLabels:
         app: api
   ```

3. **Configure horizontal pod autoscaling:**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: api-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: api
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Monitoring

1. **Install Prometheus and Grafana:**
   ```bash
   kubectl apply -f monitoring-manifests/
   ```

2. **Configure metrics collection:**
   - Prometheus scrapes metrics from `/metrics` endpoint
   - Grafana visualizes collected metrics
   - Custom dashboards for application monitoring

3. **Setup alerting:**
   - Configure Alertmanager rules
   - Integrate with PagerDuty, Slack, etc.

### Backup and Recovery

1. **Database backups:**
   ```bash
   # Backup PostgreSQL
   kubectl exec -it postgres-0 -n icecharts -- pg_dump -U icecharts_user icecharts > backup.sql

   # Restore PostgreSQL
   kubectl exec -it postgres-0 -n icecharts -- psql -U icecharts_user icecharts < backup.sql
   ```

2. **Persistent volume snapshots:**
   ```bash
   # AWS EBS snapshots
   # GCP persistent disk snapshots
   # Azure managed disk snapshots
   ```

3. **Velero for cluster backup:**
   ```bash
   velero install --provider aws --bucket icecharts-backup --secret-file credentials-velero
   velero backup create icecharts-backup --include-namespaces icecharts
   ```

## Uninstall

To completely remove IceCharts from Kubernetes:

```bash
# Remove all resources
kubectl delete -k k8s/manifests/overlays/<environment>/

# Or delete namespace (removes all resources in namespace)
kubectl delete namespace icecharts

# List remaining resources (optional)
kubectl get all -n icecharts
```

## Advanced Topics

### Custom Resource Definitions (CRDs)

To add custom resources (e.g., Istio, Knative):

```yaml
# Add to base/kustomization.yaml
resources:
  - custom-resources.yaml
```

### Service Mesh Integration

For Istio integration, add VirtualService and DestinationRule:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: icecharts-api
spec:
  hosts:
  - api
  http:
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: api
        port:
          number: 5000
```

### Multi-Region Deployment

Deploy to multiple regions with GitOps:

1. Create separate overlays for each region
2. Use Flux or ArgoCD for GitOps deployment
3. Configure cross-region replication for data

## Support and References

- Kustomize Documentation: https://kustomize.io/
- Kubernetes Documentation: https://kubernetes.io/docs/
- IceCharts Repository: https://github.com/penguintechinc/IceCharts
- Docker Hub: https://hub.docker.com/

## Changelog

### v1.0.3 (2025-12-12)

- Initial Kustomize manifests
- Support for local, AWS, GCP, Azure environments
- ConfigMap and Secret separation
- Component-based architecture (postgres, redis, minio, api, web)

## License

IceCharts Kubernetes manifests are provided under the same license as IceCharts application.
