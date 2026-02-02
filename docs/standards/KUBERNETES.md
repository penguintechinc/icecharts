<<<<<<< HEAD
# ☸️ Kubernetes Guide - Container Orchestration Made Human

Part of [Development Standards](../STANDARDS.md)

## What is K8s, Really?

Think of Kubernetes like a smart manager for your containers. You tell it "I need 3 copies of my app running," and it makes sure exactly 3 are always up. If one crashes? K8s spins up a new one. Need to update your code? K8s rolls it out without breaking anything. That's the magic.

**Key concepts you'll use:**
- **Pods**: Smallest unit (one or more containers)
- **Deployments**: Manage running multiple pod copies with updates
- **Services**: Network access to your pods
- **Ingress**: Route external traffic to your services
- **Namespaces**: Separate environments (dev, staging, prod)

## 🚀 Your First Deployment (Step-by-Step)

**1. Set up your K8s files:**

Create the directory structure:
```
k8s/
├── helm/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── ingress.yaml
└── kustomize/
    ├── base/
    │   ├── kustomization.yaml
    │   ├── deployment.yaml
    │   └── service.yaml
    └── overlays/
        ├── dev/
        ├── staging/
        └── prod/
```

**2. Deploy to dev (super simple):**

```bash
# Using Helm
=======
# Kubernetes Deployment Standards

Part of [Development Standards](../STANDARDS.md)

## Kubernetes Deployment Structure

**CRITICAL: All Kubernetes deployments MUST be in the `{PROJECT_ROOT}/k8s/` directory**

This standardized location ensures everyone knows where to find deployment manifests and configurations.

### Standard Directory Structure

```
k8s/
├── helm/                           # Helm v3 charts
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml            # Development overrides
│   ├── values-staging.yaml        # Staging overrides
│   ├── values-prod.yaml           # Production overrides
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── configmap.yaml
│       ├── secret.yaml
│       └── _helpers.tpl
├── kustomize/                     # Kustomize manifests
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── namespace.yaml
│   ├── overlays/
│   │   ├── dev/
│   │   │   ├── kustomization.yaml
│   │   │   └── patches/
│   │   ├── staging/
│   │   │   ├── kustomization.yaml
│   │   │   └── patches/
│   │   └── prod/
│   │       ├── kustomization.yaml
│   │       └── patches/
│   └── components/              # Reusable components
└── manifests/                    # Raw kubectl manifests (optional)
    ├── namespace.yaml
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

## Deployment Methods

Projects MUST support BOTH Helm and Kustomize deployment methods:

### Method 1: Helm v3 (Preferred)

**Why Helm**: Package management, versioning, rollback capabilities, templating

**Installation**:
```bash
# Deploy to development
>>>>>>> origin/v1.0.X
helm install myapp ./k8s/helm \
  --namespace myapp-dev \
  --create-namespace \
  --values ./k8s/helm/values-dev.yaml

<<<<<<< HEAD
# Check it worked
kubectl get pods -n myapp-dev
```

**3. Update your app:**

```bash
helm upgrade myapp ./k8s/helm \
  --namespace myapp-dev \
  --values ./k8s/helm/values-dev.yaml
```

**4. Oops, roll back if needed:**

```bash
helm rollback myapp 1 --namespace myapp-dev
```

## 📦 Helm Charts Explained Simply

Helm is like npm for Kubernetes. You write a template once, then customize it with different values for different environments.

**Chart.yaml** - Your app's ID card:
```yaml
apiVersion: v2
name: myapp
description: My awesome app
version: 1.0.0
appVersion: "1.0.0"
```

**values.yaml** - Configuration knobs you can twist:
```yaml
replicaCount: 2                    # Run 2 copies
image:
  repository: ghcr.io/penguintechinc/myapp
  tag: "latest"

=======
# Deploy to staging
helm install myapp ./k8s/helm \
  --namespace myapp-staging \
  --create-namespace \
  --values ./k8s/helm/values-staging.yaml

# Deploy to production
helm install myapp ./k8s/helm \
  --namespace myapp-prod \
  --create-namespace \
  --values ./k8s/helm/values-prod.yaml
```

**Upgrade**:
```bash
helm upgrade myapp ./k8s/helm \
  --namespace myapp-prod \
  --values ./k8s/helm/values-prod.yaml
```

**Rollback**:
```bash
helm rollback myapp 1 --namespace myapp-prod
```

### Method 2: Kustomize

**Why Kustomize**: Built into kubectl, declarative, no templating, patch-based

**Installation**:
```bash
# Deploy to development
kubectl apply -k k8s/kustomize/overlays/dev

# Deploy to staging
kubectl apply -k k8s/kustomize/overlays/staging

# Deploy to production
kubectl apply -k k8s/kustomize/overlays/prod
```

**Delete**:
```bash
kubectl delete -k k8s/kustomize/overlays/dev
```

### Method 3: Raw Manifests (kubectl)

**Why Raw Manifests**: Simple, explicit, no abstractions

**Installation**:
```bash
kubectl apply -f k8s/manifests/ --namespace myapp
```

## Helm Chart Standards

### Chart.yaml

```yaml
apiVersion: v2
name: myapp
description: My Application Helm Chart
type: application
version: 1.0.0  # Chart version
appVersion: "1.0.0"  # Application version
keywords:
  - myapp
  - flask
  - react
maintainers:
  - name: Penguin Tech Inc
    email: support@penguintech.io
```

### values.yaml

```yaml
# Global settings
replicaCount: 2

image:
  repository: ghcr.io/penguintechinc/myapp
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations: {}
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: false

service:
  type: ClusterIP
  port: 80
  targetPort: 5000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: myapp.penguintech.io
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: myapp-tls
      hosts:
        - myapp.penguintech.io

>>>>>>> origin/v1.0.X
resources:
  limits:
    cpu: 500m
    memory: 512Mi
<<<<<<< HEAD
=======
  requests:
    cpu: 250m
    memory: 256Mi
>>>>>>> origin/v1.0.X

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
<<<<<<< HEAD
```

**values-dev.yaml** - Override for development:
```yaml
replicaCount: 1              # Save resources, run just 1
autoscaling:
  enabled: false
app:
  env: development
  debug: true
```

**values-prod.yaml** - Override for production:
```yaml
replicaCount: 3              # More copies for reliability
autoscaling:
  enabled: true
  maxReplicas: 20
app:
  env: production
  debug: false
```

Templates use these values: `{{ .Values.replicaCount }}` becomes the actual number.

## 🎯 Common K8s Patterns We Use

### Deployments - Keep Your App Running

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: ghcr.io/penguintechinc/myapp:v1.0.0
        ports:
        - containerPort: 5000
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

### Services - Expose Your App Internally

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 5000
```

### Ingress - Route External Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.penguintech.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp
            port:
              number: 80
```

## 🔧 Troubleshooting K8s (Common Fixes)

**Pod stuck in "Pending"?**
```bash
kubectl describe pod myapp-xyz -n myapp-prod
# Check: resource limits, node capacity, node affinity
```

**Pod crashing repeatedly?**
```bash
kubectl logs myapp-xyz -n myapp-prod
kubectl logs myapp-xyz -n myapp-prod --previous  # See last run
```

**Can't reach my service?**
```bash
# Test from inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://myapp.myapp-prod.svc.cluster.local
```

**Deployment not rolling out?**
```bash
kubectl rollout status deployment/myapp -n myapp-prod
kubectl rollout history deployment/myapp -n myapp-prod
```

## 📊 Monitoring Your Pods

**Check pod status at a glance:**
```bash
kubectl get pods -n myapp-prod
kubectl get pods -n myapp-prod -o wide  # More details
```

**Watch pod events in real-time:**
```bash
kubectl get events -n myapp-prod --sort-by='.lastTimestamp'
```

**View logs:**
```bash
kubectl logs -n myapp-prod -l app=myapp --tail=100 -f
```

**Resource usage:**
```bash
kubectl top pods -n myapp-prod
kubectl top nodes
```

## 💻 Local Development (Testing Before Real K8s)

**Minikube** - Kubernetes on your laptop:
```bash
minikube start
# Your local K8s cluster is ready!

minikube stop    # Clean up when done
```

**Kind** - Docker-based K8s (lighter):
```bash
kind create cluster --name dev
kubectl cluster-info --context kind-dev
```

**Test your Helm chart before deploying:**
```bash
helm lint ./k8s/helm                    # Check syntax
helm template myapp ./k8s/helm          # See final YAML
helm install myapp ./k8s/helm --dry-run --debug  # Mock deploy
```

## ✅ Before Deploying to Production

1. **Validate your YAML**
   ```bash
   helm lint ./k8s/helm
   kubectl kustomize k8s/kustomize/overlays/prod
   ```

2. **Set resource limits** (always!)
   ```yaml
   resources:
     requests:
       cpu: 250m
       memory: 256Mi
     limits:
       cpu: 500m
       memory: 512Mi
   ```

3. **Add health checks** (liveness & readiness probes)
   ```yaml
   livenessProbe:
     httpGet:
       path: /healthz
       port: 5000
     initialDelaySeconds: 30
     periodSeconds: 10

   readinessProbe:
     httpGet:
       path: /healthz
       port: 5000
     initialDelaySeconds: 5
     periodSeconds: 5
   ```

4. **Security matters**
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     allowPrivilegeEscalation: false
   ```

5. **Never commit secrets** - use external secret stores (Vault, Sealed Secrets)

## 📚 Quick Reference

| Task | Command |
|------|---------|
| Deploy | `helm install myapp ./k8s/helm --namespace myapp-prod --values ./k8s/helm/values-prod.yaml` |
| Update | `helm upgrade myapp ./k8s/helm --namespace myapp-prod --values ./k8s/helm/values-prod.yaml` |
| Rollback | `helm rollback myapp 1 --namespace myapp-prod` |
| View logs | `kubectl logs -n myapp-prod -l app=myapp -f` |
| Check status | `kubectl get pods -n myapp-prod` |
| Delete release | `helm uninstall myapp --namespace myapp-prod` |

## 🎯 Key Principles

1. **One location**: All K8s files live in `k8s/` directory
2. **Support both**: Helm (preferred) + Kustomize (alternatives)
3. **Environment isolation**: Separate namespaces for dev/staging/prod
4. **Always set limits**: CPU and memory requests/limits required
5. **Always health check**: Liveness + readiness probes mandatory
6. **Secure by default**: Non-root users, no privilege escalation
7. **Test first**: Lint + dry-run before deploying
8. **Keep it simple**: K8s is powerful, but don't overcomplicate
=======
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}
tolerations: []
affinity: {}

# Application-specific configuration
app:
  env: production
  debug: false
  logLevel: info

database:
  type: postgresql
  host: postgres.default.svc.cluster.local
  port: 5432
  name: myapp
  # Secrets should be in external secret store
  existingSecret: myapp-db-secret

redis:
  enabled: true
  host: redis.default.svc.cluster.local
  port: 6379
```

### Environment-Specific Values

**values-dev.yaml**:
```yaml
replicaCount: 1

image:
  tag: "beta-1234567890"

ingress:
  hosts:
    - host: myapp.penguintech.io

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: false

app:
  env: development
  debug: true
  logLevel: debug
```

**values-prod.yaml**:
```yaml
replicaCount: 3

image:
  tag: "v1.0.0"

ingress:
  hosts:
    - host: myapp.penguincloud.io

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20

app:
  env: production
  debug: false
  logLevel: warning
```

## Kustomize Standards

### base/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp

resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  app: myapp
  managed-by: kustomize

images:
  - name: myapp
    newName: ghcr.io/penguintechinc/myapp
    newTag: latest
```

### overlays/dev/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp-dev

bases:
  - ../../base

namePrefix: dev-

replicas:
  - name: myapp
    count: 1

images:
  - name: myapp
    newTag: beta-1234567890

patchesStrategicMerge:
  - patches/deployment-patch.yaml

configMapGenerator:
  - name: myapp-config
    literals:
      - ENV=development
      - DEBUG=true
      - LOG_LEVEL=debug
```

### overlays/prod/kustomization.yaml

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: myapp-prod

bases:
  - ../../base

namePrefix: prod-

replicas:
  - name: myapp
    count: 3

images:
  - name: myapp
    newTag: v1.0.0

patchesStrategicMerge:
  - patches/deployment-patch.yaml
  - patches/ingress-patch.yaml

configMapGenerator:
  - name: myapp-config
    literals:
      - ENV=production
      - DEBUG=false
      - LOG_LEVEL=warning
```

## Kubernetes Best Practices

### Resource Limits

**ALWAYS set resource requests and limits**:

```yaml
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi
```

### Health Checks

**ALWAYS define liveness and readiness probes**:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /healthz
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Security

**Run as non-root user**:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

### Secrets Management

**Use external secret stores (Sealed Secrets, External Secrets Operator)**:

```yaml
# NEVER commit secrets to git
# Use external secret management
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: myapp-secrets
spec:
  secretStoreRef:
    name: vault
    kind: SecretStore
  target:
    name: myapp-secrets
  data:
    - secretKey: DB_PASSWORD
      remoteRef:
        key: myapp/database
        property: password
```

### Namespaces

**Use namespaces for environment isolation**:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp-dev
  labels:
    environment: development
    app: myapp
---
apiVersion: v1
kind: Namespace
metadata:
  name: myapp-staging
  labels:
    environment: staging
    app: myapp
---
apiVersion: v1
kind: Namespace
metadata:
  name: myapp-prod
  labels:
    environment: production
    app: myapp
```

### Labels and Annotations

**Use consistent labeling**:

```yaml
metadata:
  labels:
    app: myapp
    component: backend
    environment: production
    version: v1.0.0
    managed-by: helm
  annotations:
    description: "Flask backend service"
    docs: "https://docs.penguintech.io/myapp"
```

## Deployment Validation

### Pre-Deployment Checks

```bash
# Validate Helm chart
helm lint ./k8s/helm

# Dry-run deployment
helm install myapp ./k8s/helm --dry-run --debug

# Template output
helm template myapp ./k8s/helm --values ./k8s/helm/values-prod.yaml

# Validate Kustomize
kubectl kustomize k8s/kustomize/overlays/prod

# Dry-run Kustomize
kubectl apply -k k8s/kustomize/overlays/prod --dry-run=client
```

### Post-Deployment Validation

```bash
# Check pods
kubectl get pods -n myapp-prod

# Check services
kubectl get svc -n myapp-prod

# Check ingress
kubectl get ingress -n myapp-prod

# Check logs
kubectl logs -n myapp-prod -l app=myapp --tail=100

# Describe deployment
kubectl describe deployment myapp -n myapp-prod
```

## CI/CD Integration

### GitHub Actions Deployment

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Helm
        uses: azure/setup-helm@v3
        with:
          version: '3.12.0'

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install myapp ./k8s/helm \
            --namespace myapp-prod \
            --create-namespace \
            --values ./k8s/helm/values-prod.yaml \
            --set image.tag=${{ github.ref_name }}
```

## Makefile Targets

**Add K8s deployment targets to Makefile**:

```makefile
# Kubernetes deployment targets
.PHONY: k8s-deploy-dev k8s-deploy-staging k8s-deploy-prod

k8s-deploy-dev:
	helm upgrade --install myapp ./k8s/helm \
		--namespace myapp-dev \
		--create-namespace \
		--values ./k8s/helm/values-dev.yaml

k8s-deploy-staging:
	helm upgrade --install myapp ./k8s/helm \
		--namespace myapp-staging \
		--create-namespace \
		--values ./k8s/helm/values-staging.yaml

k8s-deploy-prod:
	helm upgrade --install myapp ./k8s/helm \
		--namespace myapp-prod \
		--create-namespace \
		--values ./k8s/helm/values-prod.yaml

k8s-validate:
	helm lint ./k8s/helm
	kubectl kustomize k8s/kustomize/overlays/prod

k8s-delete-dev:
	helm uninstall myapp --namespace myapp-dev
```

## Key Principles

1. **Standardized Location**: All K8s files in `{PROJECT_ROOT}/k8s/` directory
2. **Dual Support**: Provide both Helm and Kustomize deployment options
3. **Environment Separation**: Use namespaces and value files per environment
4. **Resource Limits**: Always set requests and limits
5. **Health Checks**: Always define liveness and readiness probes
6. **Security**: Run as non-root, drop capabilities, use secret stores
7. **Validation**: Lint and dry-run before deployment
8. **Documentation**: Document deployment process in README
>>>>>>> origin/v1.0.X

📚 **Related Standards**: [Architecture](ARCHITECTURE.md) | [Testing Phase 3](TESTING.md#phase-3-deployment--live-testing-k8s)
