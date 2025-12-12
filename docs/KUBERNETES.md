# IceCharts Kubernetes Deployment Guide

A comprehensive guide to deploying IceCharts on Kubernetes using Helm or Kustomize with multi-cloud support.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Helm Deployment](#helm-deployment)
6. [Kustomize Deployment](#kustomize-deployment)
7. [Secrets Management](#secrets-management)
8. [Accessing the Application](#accessing-the-application)
9. [Configuration & Customization](#configuration--customization)
10. [Monitoring & Observability](#monitoring--observability)
11. [High Availability](#high-availability)
12. [Backup & Disaster Recovery](#backup--disaster-recovery)
13. [Security Best Practices](#security-best-practices)
14. [Troubleshooting](#troubleshooting)
15. [Production Checklist](#production-checklist)
16. [File Structure](#file-structure)
17. [Additional Resources](#additional-resources)

---

## Overview

### What is This?

IceCharts is a real-time collaborative diagramming platform deployed on Kubernetes with comprehensive multi-cloud support. This guide covers deployment and management on any Kubernetes cluster.

### Deployment Options

IceCharts supports two primary deployment methods:

| Method | Use Case | Complexity | Best For |
|--------|----------|-----------|----------|
| **Helm** | Package manager approach | Low | Users familiar with Helm charts |
| **Kustomize** | Native kubectl templates | Medium | Direct manifest control |

### Cloud Platforms Supported

| Platform | Ingress | Secrets | Storage | Status |
|----------|---------|---------|---------|--------|
| **Local** (Minikube/Kind) | Traefik | Kubernetes Native | Default | ✓ Supported |
| **AWS (EKS)** | AWS ALB | AWS Secrets Manager | GP3 (EBS) | ✓ Supported |
| **GCP (GKE)** | GCE Load Balancer | GCP Secret Manager | PD-SSD | ✓ Supported |
| **Azure (AKS)** | App Gateway | Azure Key Vault | Managed Premium | ✓ Supported |

### Secrets Management Providers

IceCharts supports multiple secrets backends for production deployments:

| Provider | Use Case | Authentication | Refresh |
|----------|----------|-----------------|---------|
| **Kubernetes Native** | Local/Development | File-based | N/A |
| **AWS Secrets Manager** | AWS deployments | IAM/IRSA | 1 hour |
| **GCP Secret Manager** | GCP deployments | Workload Identity | 1 hour |
| **Azure Key Vault** | Azure deployments | Managed Identity | 1 hour |
| **Infisical** | Multi-cloud | Service tokens | 1 hour |

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Ingress Controller                             │  │
│  │ (Traefik/ALB/GCE/App Gateway)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                       │
│      ┌──────────────────┼──────────────────┐                   │
│      │                  │                  │                   │
│  ┌───▼──┐          ┌───▼──┐          ┌───▼──┐                │
│  │ Web  │          │ API  │          │      │                │
│  │React │          │Flask │          │      │                │
│  │ Pods │          │Pods  │          │      │                │
│  └──────┘          └──────┘          │      │                │
│      │                  │            │      │                │
│      │    ┌─────────────┴────────────┤      │                │
│      │    │                          │      │                │
│      │    │                          │      │                │
│  ┌───▼────▼──┐  ┌────────────┐  ┌──▼──────▼──┐              │
│  │PostgreSQL │  │   Redis    │  │   MinIO    │              │
│  │StatefulSet│  │StatefulSet │  │StatefulSet │              │
│  └───────────┘  └────────────┘  └────────────┘              │
│       │               │               │                      │
│  ┌────▼────┐  ┌──────▼────┐  ┌──────▼────┐                 │
│  │ PVC 50G  │  │ PVC 20G   │  │ PVC 50G   │                │
│  └──────────┘  └───────────┘  └───────────┘                │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              External Secrets Operator                   ││
│  │ (Syncs secrets from AWS/GCP/Azure/Infisical)          ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Service Communication

```
Client Request
    │
    ├─→ Ingress Controller (route to service)
    │
    ├─→ API Service (ClusterIP:5000)
    │   ├─→ PostgreSQL Service (database operations)
    │   └─→ Redis Service (caching, sessions)
    │
    ├─→ Web Service (ClusterIP:80)
    │   └─→ React SPA served via nginx
    │
    └─→ MinIO Service (object storage)
```

### Data Flow

1. **Client → Ingress**: HTTPS request routed by ingress controller
2. **Ingress → Web**: Static assets and React SPA
3. **Web → API**: JavaScript fetch/axios calls to `/api` endpoints
4. **API → Database**: Query execution via PostgreSQL
5. **API → Cache**: Session and data cache via Redis
6. **API → Storage**: File storage via MinIO S3-compatible API

---

## Prerequisites

### Universal Requirements

```bash
# Install kubectl (Kubernetes CLI)
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Verify installation
kubectl version --client
```

### For Helm Deployment

```bash
# Install Helm 3.x
# macOS
brew install helm

# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
```

### For Kustomize Deployment

```bash
# Kustomize comes built-in with kubectl (v1.14+)
# Verify kustomize is available
kubectl kustomize --version

# Optional: Install standalone kustomize
curl -s https://api.github.com/repos/kubernetes-sigs/kustomize/releases/latest | \
  grep "browser_download_url.*linux" | cut -d '"' -f 4 | xargs curl -L | tar xz
```

### Local Development (Minikube/Kind)

#### Option 1: Minikube

```bash
# Install Minikube
# macOS
brew install minikube

# Linux
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster with resources
minikube start \
  --cpus=4 \
  --memory=8192 \
  --disk-size=50g \
  --addons=ingress

# Add Traefik (if not using default ingress)
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik -n traefik --create-namespace

# Configure /etc/hosts
echo "127.0.0.1 icecharts.local" | sudo tee -a /etc/hosts
```

#### Option 2: Kind (Kubernetes in Docker)

```bash
# Install Kind
go install sigs.k8s.io/kind@latest

# Create cluster with Traefik
kind create cluster --name icecharts --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
      - containerPort: 443
        hostPort: 443
      - containerPort: 3000
        hostPort: 3000
      - containerPort: 4000
        hostPort: 4000
EOF

# Install Traefik
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik -n traefik --create-namespace
```

### AWS (EKS) Prerequisites

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Install eksctl (EKS cluster management)
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name icecharts-prod \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.large \
  --with-oidc

# Configure kubeconfig
aws eks update-kubeconfig --name icecharts-prod --region us-west-2

# Install AWS ALB Ingress Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system

# Create IAM role for IRSA (secrets access)
eksctl create iamserviceaccount \
  --name icecharts \
  --cluster=icecharts-prod \
  --region=us-west-2 \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve
```

### GCP (GKE) Prerequisites

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Initialize gcloud
gcloud init
gcloud auth login

# Create GKE cluster with Workload Identity
gcloud container clusters create icecharts-prod \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-ip-alias \
  --workload-pool=PROJECT_ID.svc.id.goog

# Configure kubeconfig
gcloud container clusters get-credentials icecharts-prod --region us-central1

# Create Kubernetes service account and link to GCP service account
kubectl create serviceaccount icecharts -n icecharts
gcloud iam service-accounts create icecharts
gcloud iam service-accounts add-iam-policy-binding \
  icecharts@PROJECT_ID.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:PROJECT_ID.svc.id.goog[icecharts/icecharts]"

# Grant Secret Manager Reader role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:icecharts@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Azure (AKS) Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Create resource group
az group create --name icecharts-rg --location westus2

# Create AKS cluster with Managed Identity
az aks create \
  --resource-group icecharts-rg \
  --name icecharts-prod \
  --node-count 3 \
  --vm-set-type VirtualMachineScaleSets \
  --enable-managed-identity \
  --workload-identity-enabled

# Get credentials
az aks get-credentials \
  --resource-group icecharts-rg \
  --name icecharts-prod

# Create Azure Key Vault
az keyvault create \
  --name icecharts-kv \
  --resource-group icecharts-rg

# Create managed identity for Pod
az identity create \
  --resource-group icecharts-rg \
  --name icecharts-pod

# Grant Key Vault access
PRINCIPAL_ID=$(az identity show \
  --name icecharts-pod \
  --resource-group icecharts-rg \
  --query principalId --output tsv)

az keyvault set-policy \
  --name icecharts-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

---

## Quick Start

### Local Development (Single Command)

```bash
# Using Minikube/Kind with Helm and Kubernetes native secrets
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-local.yaml \
  -n icecharts --create-namespace

# Verify deployment
kubectl get pods -n icecharts
kubectl get svc -n icecharts

# Port forward to access application
kubectl port-forward -n icecharts svc/icecharts-web 3000:80 &
kubectl port-forward -n icecharts svc/icecharts-api 4000:80 &

# Access application
# Web: http://localhost:3000
# API: http://localhost:4000
```

### AWS EKS Deployment (Single Command)

```bash
# Prerequisites:
# 1. EKS cluster created with IRSA configured
# 2. AWS Secrets Manager populated with secrets
# 3. ALB controller installed
# 4. Certificate ARN obtained from AWS ACM

helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set ingress.host=icecharts.example.com \
  --set ingress.tls.certificateArn=arn:aws:acm:us-west-2:ACCOUNT_ID:certificate/CERT_ID \
  --set secrets.externalSecrets.aws.roleArn=arn:aws:iam::ACCOUNT_ID:role/icecharts-irsa \
  --set secrets.externalSecrets.aws.region=us-west-2 \
  -n icecharts --create-namespace

# Verify deployment
kubectl get pods -n icecharts
kubectl get ingress -n icecharts

# Get ALB DNS name
kubectl get ingress -n icecharts -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}'
```

### GCP GKE Deployment (Single Command)

```bash
# Prerequisites:
# 1. GKE cluster created with Workload Identity
# 2. GCP Secret Manager secrets created
# 3. Managed certificate created
# 4. Static IP reserved

helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-gcp.yaml \
  --set ingress.host=icecharts.example.com \
  --set ingress.staticIpName=icecharts-ip \
  --set ingress.tls.managedCertificateName=icecharts-cert \
  --set secrets.externalSecrets.gcp.projectId=my-project \
  --set secrets.externalSecrets.gcp.serviceAccountEmail=icecharts@my-project.iam.gserviceaccount.com \
  -n icecharts --create-namespace

# Verify deployment
kubectl get pods -n icecharts
kubectl get ingress -n icecharts

# Get load balancer IP
kubectl get ingress -n icecharts -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
```

### Azure AKS Deployment (Single Command)

```bash
# Prerequisites:
# 1. AKS cluster created with Workload Identity
# 2. Azure Key Vault created with secrets
# 3. Application Gateway configured
# 4. Managed identity linked to service account

helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-azure.yaml \
  --set ingress.host=icecharts.example.com \
  --set secrets.externalSecrets.azure.vaultUrl=https://icecharts-kv.vault.azure.net/ \
  --set secrets.externalSecrets.azure.tenantId=YOUR_TENANT_ID \
  --set secrets.externalSecrets.azure.clientId=YOUR_CLIENT_ID \
  -n icecharts --create-namespace

# Verify deployment
kubectl get pods -n icecharts
kubectl get ingress -n icecharts

# Get Application Gateway IP
kubectl get ingress -n icecharts -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}'
```

---

## Helm Deployment

### Chart Structure

```
k8s/helm/icecharts/
├── Chart.yaml                 # Chart metadata and version
├── values.yaml                # Base configuration with defaults
├── values-local.yaml          # Local development overrides
├── values-aws.yaml            # AWS EKS overrides
├── values-gcp.yaml            # GCP GKE overrides
├── values-azure.yaml          # Azure AKS overrides
└── templates/
    ├── configmap.yaml         # Application configuration
    ├── secret.yaml            # Kubernetes native secrets
    ├── externalsecret-aws.yaml      # AWS Secrets Manager integration
    ├── externalsecret-gcp.yaml      # GCP Secret Manager integration
    ├── externalsecret-azure.yaml    # Azure Key Vault integration
    ├── externalsecret-infisical.yaml # Infisical integration
    ├── statefulset-postgres.yaml    # PostgreSQL database
    ├── statefulset-redis.yaml       # Redis cache
    ├── statefulset-minio.yaml       # MinIO object storage
    ├── deployment-api.yaml          # Flask API backend
    ├── deployment-web.yaml          # React frontend
    ├── service-*.yaml               # Kubernetes services
    ├── ingress-traefik.yaml         # Traefik ingress
    ├── ingress-aws.yaml             # AWS ALB ingress
    ├── ingress-gcp.yaml             # GCP GCE ingress
    ├── ingress-azure.yaml           # Azure App Gateway ingress
    ├── hpa-api.yaml                 # API autoscaling
    ├── hpa-web.yaml                 # Web autoscaling
    ├── networkpolicy-*.yaml         # Network security policies
    ├── prometheus-deployment.yaml   # Prometheus monitoring
    ├── grafana-deployment.yaml      # Grafana dashboards
    ├── servicemonitor-api.yaml      # Prometheus service monitor
    ├── cronjob-backup.yaml          # Database backups
    └── service-*.yaml
```

### Installation

#### Basic Installation

```bash
# Install with default values
helm install icecharts k8s/helm/icecharts/ -n icecharts --create-namespace

# Install with environment-specific values
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  -n icecharts --create-namespace
```

#### Custom Configuration

```bash
# Override specific values
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set api.replicaCount=5 \
  --set web.replicaCount=3 \
  --set postgres.persistence.size=200Gi \
  --set ingress.host=icecharts.mycompany.com \
  -n icecharts --create-namespace
```

#### Using Custom Values File

```bash
# Create custom values file
cat > values-custom.yaml <<EOF
api:
  replicaCount: 5
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"

web:
  replicaCount: 3

ingress:
  host: icecharts.example.com
EOF

# Install with custom values
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  -f values-custom.yaml \
  -n icecharts --create-namespace
```

### Upgrade

```bash
# Upgrade to new version with same values
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  -n icecharts

# Upgrade with new values
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set api.image.tag=v1.0.4 \
  -n icecharts

# Upgrade with rollback capability
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  -n icecharts

# Rollback if needed
helm rollback icecharts 1 -n icecharts
```

### Uninstall

```bash
# Uninstall chart (preserves data by default)
helm uninstall icecharts -n icecharts

# Uninstall and delete persistent volumes
helm uninstall icecharts -n icecharts
kubectl delete pvc -n icecharts --all

# Delete namespace
kubectl delete namespace icecharts
```

---

## Kustomize Deployment

### Directory Structure

```
k8s/manifests/
├── base/
│   ├── namespace.yaml           # Kubernetes namespace
│   ├── configmap.yaml           # Application configuration
│   ├── secret.yaml              # Native K8s secrets
│   ├── kustomization.yaml       # Base kustomization
│   ├── postgres/                # PostgreSQL manifests
│   │   ├── kustomization.yaml
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── redis/                   # Redis manifests
│   ├── minio/                   # MinIO manifests
│   ├── api/                     # API backend manifests
│   └── web/                     # Web frontend manifests
└── overlays/
    ├── local/                   # Local development
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   ├── resources-patch.yaml
    │   └── ingress-patch.yaml
    ├── aws/                     # AWS EKS
    │   ├── kustomization.yaml
    │   ├── replica-patch.yaml
    │   ├── resources-patch.yaml
    │   ├── storage-class-patch.yaml
    │   └── ingress-patch.yaml
    ├── gcp/                     # GCP GKE
    ├── azure/                   # Azure AKS
```

### Deployment

#### Basic Deployment

```bash
# Deploy local environment (Traefik, single replicas)
kubectl apply -k k8s/manifests/overlays/local/

# Deploy AWS environment
kubectl apply -k k8s/manifests/overlays/aws/

# Deploy GCP environment
kubectl apply -k k8s/manifests/overlays/gcp/

# Deploy Azure environment
kubectl apply -k k8s/manifests/overlays/azure/
```

#### Verification

```bash
# Check namespace creation
kubectl get namespace icecharts

# Check all resources
kubectl get all -n icecharts

# Check persistent volumes
kubectl get pvc -n icecharts

# Check pods status
kubectl get pods -n icecharts -w

# Check pod logs
kubectl logs -n icecharts deployment/icecharts-api
```

#### Customization

```bash
# View rendered manifests (preview before applying)
kubectl kustomize k8s/manifests/overlays/aws/ | head -50

# Edit image tag
kubectl -n icecharts set image \
  deployment/icecharts-api \
  icecharts-api=ghcr.io/penguintechinc/icecharts-flask-backend:v1.0.4

# Scale replicas
kubectl scale deployment icecharts-api \
  -n icecharts \
  --replicas=5

# Update resources
kubectl set resources deployment icecharts-api \
  -n icecharts \
  --requests=cpu=500m,memory=1Gi \
  --limits=cpu=2000m,memory=2Gi
```

#### Deletion

```bash
# Delete all resources (preserves data)
kubectl delete -k k8s/manifests/overlays/aws/

# Delete namespace
kubectl delete namespace icecharts
```

---

## Secrets Management

Secrets management is critical for production deployments. IceCharts supports multiple backends.

### Local/Development (Kubernetes Native)

**Use Case**: Single-node clusters, development, testing

#### Setup

```bash
# Default configuration in values-local.yaml
secrets:
  provider: kubernetes

  kubernetes:
    postgresPassword: "changeme-postgres-prod"
    postgresUser: "icecharts_user"
    postgresDb: "icecharts"
    redisPassword: "changeme-redis-prod"
    minioRootUser: "minioadmin"
    minioRootPassword: "changeme-minio-prod"
    secretKey: "changeme-flask-secret-key-in-production"
    securityPasswordSalt: "changeme-salt-in-production"
    jwtSecretKey: "changeme-jwt-secret-in-production"
    defaultAdminEmail: "admin@icecharts.local"
    defaultAdminPassword: "admin123"
```

#### Generate Secure Passwords

```bash
# Generate PostgreSQL password
openssl rand -base64 32

# Generate Redis password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate JWT secret key
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### Update Secrets

```bash
# Edit values file
vim k8s/helm/icecharts/values-local.yaml

# Update Helm installation
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-local.yaml \
  -n icecharts
```

### AWS Secrets Manager

**Use Case**: AWS EKS deployments with IRSA authentication

#### Prerequisites

1. **External Secrets Operator**
```bash
# Add helm repository
helm repo add external-secrets https://charts.external-secrets.io

# Install ESO
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

2. **Create Secrets in AWS Secrets Manager**
```bash
# Create PostgreSQL secret
aws secretsmanager create-secret \
  --name icecharts/prod/postgres-credentials \
  --secret-string '{
    "postgresPassword": "YOUR_SECURE_PASSWORD",
    "postgresUser": "icecharts_user",
    "postgresDb": "icecharts"
  }' \
  --region us-west-2

# Create Redis secret
aws secretsmanager create-secret \
  --name icecharts/prod/redis-credentials \
  --secret-string '{
    "redisPassword": "YOUR_SECURE_PASSWORD"
  }' \
  --region us-west-2

# Create MinIO secret
aws secretsmanager create-secret \
  --name icecharts/prod/minio-credentials \
  --secret-string '{
    "minioRootUser": "minioadmin",
    "minioRootPassword": "YOUR_SECURE_PASSWORD"
  }' \
  --region us-west-2

# Create API secret
aws secretsmanager create-secret \
  --name icecharts/prod/api-secrets \
  --secret-string '{
    "secretKey": "YOUR_SECURE_KEY",
    "securityPasswordSalt": "YOUR_SECURE_SALT",
    "jwtSecretKey": "YOUR_SECURE_JWT_KEY"
  }' \
  --region us-west-2

# Create admin credentials
aws secretsmanager create-secret \
  --name icecharts/prod/admin-credentials \
  --secret-string '{
    "defaultAdminEmail": "admin@example.com",
    "defaultAdminPassword": "YOUR_SECURE_PASSWORD"
  }' \
  --region us-west-2
```

3. **Configure IRSA (IAM Roles for Service Accounts)**
```bash
# Create IAM role with Secrets Manager policy
eksctl create iamserviceaccount \
  --name icecharts \
  --cluster=icecharts-prod \
  --region=us-west-2 \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve

# Get role ARN for use in Helm values
aws iam list-roles --query "Roles[?contains(RoleName, 'icecharts')].Arn" --output text
```

#### Configuration

```bash
# Update values-aws.yaml
cat k8s/helm/icecharts/values-aws.yaml | grep -A 30 "externalSecrets:"

# Install with AWS backend
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=aws \
  --set secrets.externalSecrets.aws.region=us-west-2 \
  --set secrets.externalSecrets.aws.roleArn=arn:aws:iam::ACCOUNT_ID:role/icecharts-irsa \
  -n icecharts --create-namespace
```

#### Verification

```bash
# Check External Secrets SecretStore
kubectl get secretstore -n icecharts

# Check synced secrets
kubectl get secret -n icecharts

# View secret metadata (NOT values for security)
kubectl describe secret icecharts-postgres -n icecharts
```

### GCP Secret Manager

**Use Case**: GCP GKE deployments with Workload Identity

#### Prerequisites

1. **External Secrets Operator**
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

2. **Create Secrets in GCP Secret Manager**
```bash
# Create PostgreSQL secret
gcloud secrets create icecharts-postgres-credentials \
  --data-file=- <<EOF
{
  "postgresPassword": "YOUR_SECURE_PASSWORD",
  "postgresUser": "icecharts_user",
  "postgresDb": "icecharts"
}
EOF

# Create Redis secret
gcloud secrets create icecharts-redis-credentials \
  --data-file=- <<EOF
{
  "redisPassword": "YOUR_SECURE_PASSWORD"
}
EOF

# Create MinIO secret
gcloud secrets create icecharts-minio-credentials \
  --data-file=- <<EOF
{
  "minioRootUser": "minioadmin",
  "minioRootPassword": "YOUR_SECURE_PASSWORD"
}
EOF

# Create API secrets
gcloud secrets create icecharts-api-secrets \
  --data-file=- <<EOF
{
  "secretKey": "YOUR_SECURE_KEY",
  "securityPasswordSalt": "YOUR_SECURE_SALT",
  "jwtSecretKey": "YOUR_SECURE_JWT_KEY"
}
EOF

# Create admin credentials
gcloud secrets create icecharts-admin-credentials \
  --data-file=- <<EOF
{
  "defaultAdminEmail": "admin@example.com",
  "defaultAdminPassword": "YOUR_SECURE_PASSWORD"
}
EOF
```

3. **Configure Workload Identity**
```bash
# Create service account
gcloud iam service-accounts create icecharts

# Grant Secret Manager Reader role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:icecharts@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Link Kubernetes SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  icecharts@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="serviceAccount:PROJECT_ID.svc.id.goog[icecharts/icecharts]"
```

#### Configuration

```bash
# Install with GCP backend
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-gcp.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=gcp \
  --set secrets.externalSecrets.gcp.projectId=my-project \
  --set secrets.externalSecrets.gcp.serviceAccountEmail=icecharts@my-project.iam.gserviceaccount.com \
  -n icecharts --create-namespace
```

#### Verification

```bash
# Check SecretStore status
kubectl describe secretstore -n icecharts

# Verify secrets synced
kubectl get secrets -n icecharts

# Check External Secrets operator logs
kubectl logs -n external-secrets-system -l app=external-secrets
```

### Azure Key Vault

**Use Case**: Azure AKS deployments with Managed Identity

#### Prerequisites

1. **External Secrets Operator**
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

2. **Create Secrets in Azure Key Vault**
```bash
# Create secrets
az keyvault secret set \
  --vault-name icecharts-kv \
  --name postgres-password \
  --value "YOUR_SECURE_PASSWORD"

az keyvault secret set \
  --vault-name icecharts-kv \
  --name postgres-user \
  --value "icecharts_user"

az keyvault secret set \
  --vault-name icecharts-kv \
  --name postgres-db \
  --value "icecharts"

az keyvault secret set \
  --vault-name icecharts-kv \
  --name redis-password \
  --value "YOUR_SECURE_PASSWORD"

az keyvault secret set \
  --vault-name icecharts-kv \
  --name minio-root-user \
  --value "minioadmin"

az keyvault secret set \
  --vault-name icecharts-kv \
  --name minio-root-password \
  --value "YOUR_SECURE_PASSWORD"

# Continue for other secrets...
```

3. **Configure Managed Identity**
```bash
# Create managed identity
az identity create \
  --resource-group icecharts-rg \
  --name icecharts-pod

# Get principal ID
PRINCIPAL_ID=$(az identity show \
  --resource-group icecharts-rg \
  --name icecharts-pod \
  --query principalId --output tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name icecharts-kv \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

# Link to Kubernetes service account
MANAGED_IDENTITY_ID=$(az identity show \
  --resource-group icecharts-rg \
  --name icecharts-pod \
  --query id --output tsv)

kubectl annotate serviceaccount icecharts \
  -n icecharts \
  azure.workload.identity/client-id=$(az identity show --resource-group icecharts-rg --name icecharts-pod --query clientId --output tsv)
```

#### Configuration

```bash
# Get Key Vault URL
VAULT_URL=$(az keyvault show --name icecharts-kv --query properties.vaultUri --output tsv)

# Install with Azure backend
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-azure.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=azure \
  --set secrets.externalSecrets.azure.vaultUrl=$VAULT_URL \
  --set secrets.externalSecrets.azure.tenantId=YOUR_TENANT_ID \
  -n icecharts --create-namespace
```

### Infisical (Multi-Cloud)

**Use Case**: Multi-cloud deployments, centralized secrets management

#### Prerequisites

1. **Create Infisical Account**
   - Sign up at https://app.infisical.com
   - Create project
   - Create environment (prod, staging, dev)
   - Add secrets under `/icecharts` path

2. **Create Service Token**
```bash
# In Infisical UI:
# 1. Settings → Service Tokens
# 2. Create new token with read permissions
# 3. Copy token value
```

3. **Create Kubernetes Secret**
```bash
kubectl create secret generic infisical-service-token \
  -n icecharts \
  --from-literal=token=YOUR_INFISICAL_SERVICE_TOKEN
```

4. **Install External Secrets Operator**
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

#### Configuration

```bash
# Install with Infisical backend
helm install icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=infisical \
  --set secrets.externalSecrets.infisical.projectId=YOUR_PROJECT_ID \
  --set secrets.externalSecrets.infisical.environment=prod \
  --set secrets.externalSecrets.infisical.apiUrl=https://app.infisical.com \
  -n icecharts --create-namespace
```

### Switching Between Providers

```bash
# Switch from Kubernetes to AWS
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=aws \
  -n icecharts

# Switch from AWS to GCP
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-gcp.yaml \
  --set secrets.provider=external-secrets \
  --set secrets.externalSecrets.backend=gcp \
  -n icecharts

# Verify transition
kubectl get secrets -n icecharts
kubectl logs -n icecharts deployment/icecharts-api
```

---

## Accessing the Application

### Local Development

```bash
# Method 1: Port Forwarding (simple access)
kubectl port-forward -n icecharts svc/icecharts-web 3000:80 &
kubectl port-forward -n icecharts svc/icecharts-api 4000:80 &

# Access application
# Web UI: http://localhost:3000
# API: http://localhost:4000

# Method 2: Traefik Ingress (requires /etc/hosts entry)
# Add to /etc/hosts: 127.0.0.1 icecharts.local

# Access via hostname
# Web: http://icecharts.local
# API: http://icecharts.local/api

# Method 3: Minikube tunnel (if using Minikube with LoadBalancer)
minikube tunnel

# Get LoadBalancer IP
kubectl get svc -n icecharts
```

### AWS EKS

```bash
# Get ALB DNS name
ALB_DNS=$(kubectl get ingress -n icecharts \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')

echo "Access application at: http://${ALB_DNS}"

# Or update DNS to point to ALB
# CNAME icecharts.example.com -> ALB_DNS

# Access application
# Web: https://icecharts.example.com
# API: https://icecharts.example.com/api
```

### GCP GKE

```bash
# Get load balancer IP
LB_IP=$(kubectl get ingress -n icecharts \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')

echo "Access application at: http://${LB_IP}"

# Or update DNS A record to point to LB_IP
# A icecharts.example.com -> LB_IP

# Access application
# Web: https://icecharts.example.com
# API: https://icecharts.example.com/api
```

### Azure AKS

```bash
# Get Application Gateway IP
APP_GW_IP=$(kubectl get ingress -n icecharts \
  -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}')

echo "Access application at: http://${APP_GW_IP}"

# Or update DNS A record
# A icecharts.example.com -> APP_GW_IP

# Access application
# Web: https://icecharts.example.com
# API: https://icecharts.example.com/api
```

### WebSocket Connections

IceCharts uses WebSocket for real-time collaboration:

```bash
# WebSocket endpoint (from web UI)
# wss://icecharts.example.com/socket.io

# Verify WebSocket connectivity
# Browser Developer Tools → Network → WS
# Should see socket.io connection established

# If WebSocket fails, ensure:
# 1. Sticky sessions enabled (sessionAffinity: ClientIP)
# 2. Load balancer supports WebSocket
# 3. Firewall allows WebSocket port (443/https or 80/http)
```

---

## Configuration & Customization

### ConfigMap (Non-Sensitive Settings)

```bash
# View current configuration
kubectl get configmap -n icecharts icecharts-config -o yaml

# Edit configuration
kubectl edit configmap -n icecharts icecharts-config

# Set individual configuration
kubectl set env deployment/icecharts-api \
  -n icecharts \
  LOG_LEVEL=debug \
  CACHE_TTL=600
```

### Environment Variables (API)

Key environment variables for Flask API:

```yaml
# Flask Configuration
FLASK_ENV: production
FLASK_APP: app.py

# Database
DB_TYPE: postgres
DB_HOST: icecharts-postgres
DB_PORT: "5432"
DB_POOL_SIZE: "10"

# Redis
REDIS_HOST: icecharts-redis
REDIS_PORT: "6379"

# MinIO
MINIO_ENDPOINT: icecharts-minio:9000
MINIO_BUCKET: icecharts
MINIO_SECURE: "false"

# JWT
JWT_ACCESS_TOKEN_EXPIRES: "3600"
JWT_REFRESH_TOKEN_EXPIRES: "2592000"

# CORS
CORS_ORIGINS: "*"

# Rate Limiting
RATE_LIMIT_ENABLED: "true"
RATE_LIMIT_MAX_REQUESTS: "100"
RATE_LIMIT_WINDOW_MINUTES: "15"

# Logging
LOG_LEVEL: info
LOG_FORMAT: json

# License
PRODUCT_NAME: icecharts
LICENSE_SERVER_URL: "https://license.penguintech.io"
RELEASE_MODE: "false"

# Performance
MAX_CONNECTIONS: "100"
CONNECTION_TIMEOUT: "30s"
IDLE_TIMEOUT: "15m"
```

### Persistent Volume Configuration

```bash
# View current PVC configuration
kubectl get pvc -n icecharts

# Resize PostgreSQL storage (if supported by storage class)
kubectl patch pvc icecharts-postgres-data \
  -n icecharts \
  -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# View storage class details
kubectl get storageclass
kubectl describe storageclass gp3  # AWS example
```

### Resource Limits

```yaml
# Example resource configuration in values file
api:
  resources:
    requests:
      memory: "512Mi"      # Minimum guaranteed memory
      cpu: "250m"          # Minimum guaranteed CPU
    limits:
      memory: "2Gi"        # Maximum allowed memory
      cpu: "1000m"         # Maximum allowed CPU

# Update running deployment
kubectl set resources deployment icecharts-api \
  -n icecharts \
  --requests=cpu=500m,memory=1Gi \
  --limits=cpu=2000m,memory=2Gi
```

### Replicas (Scaling)

```bash
# Scale API deployment
kubectl scale deployment icecharts-api \
  -n icecharts \
  --replicas=5

# Scale Web deployment
kubectl scale deployment icecharts-web \
  -n icecharts \
  --replicas=3

# View current replicas
kubectl get deployment -n icecharts
```

### High Availability Configuration

```yaml
# Enable auto-scaling in values file
api:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80

web:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Enable Pod Disruption Budget
podDisruptionBudget:
  enabled: true
  api:
    minAvailable: 1
  web:
    minAvailable: 1
```

### Monitoring & Observability

```bash
# Enable monitoring in values file
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true

# Deploy monitoring stack
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set monitoring.enabled=true \
  --set monitoring.prometheus.enabled=true \
  --set monitoring.grafana.enabled=true \
  -n icecharts

# Access Grafana
kubectl port-forward -n icecharts svc/icecharts-grafana 3000:3000 &

# Login to Grafana
# URL: http://localhost:3000
# Username: admin
# Password: (from values file or kubectl get secret)
```

### Network Policies

```bash
# Enable network policies (production recommended)
networkPolicies:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  allowDns: true

# Update deployment
helm upgrade icecharts k8s/helm/icecharts/ \
  -f k8s/helm/icecharts/values.yaml \
  -f k8s/helm/icecharts/values-aws.yaml \
  --set networkPolicies.enabled=true \
  -n icecharts

# Verify network policies
kubectl get networkpolicy -n icecharts
```

### Database Backups

```yaml
# Enable automated backups
backup:
  enabled: true
  schedule: "0 2 * * *"      # Daily at 2 AM UTC
  retention: 30               # Keep 30 days
  persistence:
    size: 200Gi
```

---

## Monitoring & Observability

### Prometheus Integration

IceCharts API exposes Prometheus metrics at `/metrics` endpoint.

```bash
# Access Prometheus
kubectl port-forward -n icecharts svc/icecharts-prometheus 9090:9090 &

# Prometheus URL: http://localhost:9090

# Query metrics examples
# - icecharts_http_requests_total
# - icecharts_http_request_duration_seconds
# - icecharts_database_connections_active
# - icecharts_cache_hits_total
```

### Grafana Dashboards

```bash
# Access Grafana
kubectl port-forward -n icecharts svc/icecharts-grafana 3000:3000 &

# Grafana URL: http://localhost:3000
# Default credentials: admin / password (from values)

# Included dashboards:
# - IceCharts Overview
# - API Performance
# - Database Health
# - Redis Cache Statistics
# - Resource Utilization
```

### Service Logs

```bash
# View API logs
kubectl logs -n icecharts deployment/icecharts-api

# View Web logs
kubectl logs -n icecharts deployment/icecharts-web

# View PostgreSQL logs
kubectl logs -n icecharts statefulset/icecharts-postgres

# Real-time log streaming
kubectl logs -n icecharts deployment/icecharts-api -f

# View logs from previous pod restart
kubectl logs -n icecharts deployment/icecharts-api --previous

# View logs with timestamps
kubectl logs -n icecharts deployment/icecharts-api --timestamps=true
```

### Debugging

```bash
# Describe pod for events/status
kubectl describe pod -n icecharts <pod-name>

# Execute command in pod
kubectl exec -it -n icecharts <pod-name> -- /bin/bash

# Copy files from pod
kubectl cp icecharts/<pod-name>:/var/log/app.log ./app.log

# Port forward to specific service for debugging
kubectl port-forward -n icecharts svc/icecharts-api 5000:5000 &

# Check pod readiness/liveness
kubectl get pod -n icecharts <pod-name> -o jsonpath='{.status.conditions[*]}'
```

---

## High Availability

### Multi-Node Cluster

HA requires at least 3 worker nodes:

```bash
# AWS EKS: Create 3-node cluster
eksctl create cluster \
  --name icecharts-prod \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.large

# GCP GKE: Create 3-node cluster
gcloud container clusters create icecharts-prod \
  --num-nodes 3 \
  --machine-type n1-standard-2

# Azure AKS: Create 3-node cluster
az aks create \
  --resource-group icecharts-rg \
  --name icecharts-prod \
  --node-count 3
```

### Pod Anti-Affinity

Spreads pods across different nodes:

```yaml
api:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchExpressions:
                - key: app.kubernetes.io/name
                  operator: In
                  values:
                    - icecharts-api
            topologyKey: kubernetes.io/hostname
```

### PostgreSQL Replication

For critical deployments:

```bash
# Scale PostgreSQL to 3 replicas (requires manual setup)
kubectl scale statefulset icecharts-postgres \
  -n icecharts \
  --replicas=3

# Configure replication (manual - requires PostgreSQL expert)
# This enables read replicas and automatic failover
```

### Redis Sentinel

For Redis high availability:

```yaml
redis:
  replicaCount: 3
  # Requires Sentinel configuration
  # See: https://redis.io/topics/sentinel
```

### MinIO Distributed

For distributed object storage:

```yaml
minio:
  replicaCount: 4  # Minimum 4 for distributed mode
  # Enables erasure coding with fault tolerance
```

### Load Balancer Configuration

```bash
# AWS ALB sticky sessions
kubectl annotate ingress icecharts-web \
  -n icecharts \
  alb.ingress.kubernetes.io/target-group-attributes=stickiness.lb_cookie.enabled=true,stickiness.lb_cookie.duration_seconds=86400

# GCE sticky sessions
kubectl annotate ingress icecharts-web \
  -n icecharts \
  cloud.google.com/session-affinity=CLIENT_IP

# Azure sticky sessions
kubectl patch service icecharts-api \
  -n icecharts \
  -p '{"spec":{"sessionAffinity":"ClientIP"}}'
```

---

## Backup & Disaster Recovery

### Automated PostgreSQL Backups

```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"      # Daily 2 AM UTC
  retention: 30               # Keep 30 days
```

### Manual Database Backup

```bash
# Create backup
kubectl exec -it -n icecharts icecharts-postgres-0 -- \
  pg_dump -U icecharts_user icecharts > backup.sql

# Verify backup
ls -lh backup.sql

# Upload to S3/Cloud Storage
aws s3 cp backup.sql s3://icecharts-backups/
```

### Restore from Backup

```bash
# Copy backup into pod
kubectl cp backup.sql icecharts/icecharts-postgres-0:/tmp/

# Restore backup
kubectl exec -it -n icecharts icecharts-postgres-0 -- \
  psql -U icecharts_user icecharts < /tmp/backup.sql

# Verify restore
kubectl exec -it -n icecharts icecharts-postgres-0 -- \
  psql -U icecharts_user -d icecharts -c "SELECT COUNT(*) FROM users;"
```

### Persistent Volume Snapshots

```bash
# AWS: Create EBS snapshot
aws ec2 create-snapshot \
  --volume-id vol-xxxxx \
  --description "IceCharts DB backup"

# GCP: Create persistent disk snapshot
gcloud compute disks snapshot icecharts-postgres-data \
  --snapshot-names=icecharts-backup-2024-01-01

# Azure: Create snapshot
az snapshot create \
  --resource-group icecharts-rg \
  --name icecharts-backup \
  --source /subscriptions/xxxxx/resourceGroups/icecharts-rg/providers/Microsoft.Compute/disks/icecharts-postgres-data
```

---

## Security Best Practices

### Non-Root Containers

```yaml
# All containers run as non-root user
postgres:
  securityContext:
    runAsUser: 999         # Non-root UID
    runAsNonRoot: true

redis:
  securityContext:
    runAsUser: 999
    runAsNonRoot: true

api:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
```

### Read-Only Filesystems

```yaml
web:
  securityContext:
    readOnlyRootFilesystem: true  # Web server runs read-only

api:
  securityContext:
    readOnlyRootFilesystem: false # API needs write for logs
```

### Network Policies

```yaml
networkPolicies:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  allowDns: true

# Specific policies ensure:
# - API can only connect to database/cache/storage
# - Web can only receive ingress traffic
# - Database only accepts API connections
```

### RBAC (Role-Based Access Control)

```bash
# View default service account
kubectl get serviceaccount -n icecharts

# View role bindings
kubectl get rolebindings -n icecharts

# Limit to least privilege (default provided)
# - API service account: read secrets, write logs
# - No cluster-admin privileges
```

### Secret Encryption

Enable encryption at rest in Kubernetes:

```bash
# AWS: Enable EBS encryption (default in modern versions)
# GCP: Enable Application-level Secrets Encryption (ALSE)
# Azure: Enable Azure Disk Encryption

# Verify encryption
kubectl get secret -n icecharts icecharts-postgres -o yaml | head -10
```

### TLS/HTTPS

```yaml
ingress:
  tls:
    enabled: true
    secretName: icecharts-tls

  # AWS: Certificate from ACM
  certificates:
    certificateArn: "arn:aws:acm:..."

  # GCP: Managed certificate
  managedCertificateName: icecharts-cert

  # Azure: Application Gateway certificate
```

### Service Account Permissions

```bash
# Create service account with minimal permissions
kubectl create serviceaccount icecharts -n icecharts

# Create role with specific permissions
kubectl create role icecharts-role \
  --verb=get,list,watch \
  --resource=secrets \
  --resource=configmaps \
  -n icecharts

# Bind role to service account
kubectl create rolebinding icecharts-binding \
  --clusterrole=icecharts-role \
  --serviceaccount=icecharts:icecharts \
  -n icecharts
```

---

## Troubleshooting

### Pod Won't Start

```bash
# Check pod status
kubectl describe pod -n icecharts <pod-name>

# Common issues:
# 1. Insufficient resources
kubectl top nodes
kubectl top pods -n icecharts

# 2. Image pull errors
kubectl logs -n icecharts <pod-name> | grep -i "pull\|image"

# 3. Pending state (resource constraints)
kubectl get pods -n icecharts
```

### Database Connection Fails

```bash
# Check ConfigMap/Secret
kubectl get configmap -n icecharts -o yaml
kubectl get secret -n icecharts -o yaml | grep -i "host\|user\|password"

# Test database connection
kubectl exec -it -n icecharts icecharts-api-<pod> -- \
  psql -h icecharts-postgres -U icecharts_user -d icecharts -c "SELECT 1"

# Check database pod
kubectl logs -n icecharts statefulset/icecharts-postgres
```

### External Secrets Not Syncing

```bash
# Check SecretStore status
kubectl describe secretstore -n icecharts

# Check External Secrets Operator logs
kubectl logs -n external-secrets-system -l app=external-secrets

# Common issues:
# 1. IAM/authentication misconfigured
# 2. Secret not found in backend
# 3. Refresh interval too long (default 1h)

# Force secret refresh
kubectl annotate secret icecharts-postgres \
  -n icecharts \
  force-sync=$(date +%s) \
  --overwrite
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress -n icecharts icecharts-web

# Check ingress controller logs
kubectl logs -n kube-system -l app=ingress

# Test connectivity
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl http://icecharts-api

# Verify ingress annotations match controller
# Traefik, ALB, GCE, App Gateway have different requirements
```

### WebSocket Connection Issues

```bash
# Check sticky sessions enabled
kubectl get service -n icecharts icecharts-api -o yaml | grep -i affinity

# Check load balancer session stickiness
# AWS: ALB target group → Stickiness enabled
# GCP: Backend service → Session affinity
# Azure: HTTP settings → Cookie-based session affinity

# Monitor WebSocket connections
kubectl logs -n icecharts deployment/icecharts-api | grep -i "socket\|websocket"
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n icecharts

# Describe PVC for details
kubectl describe pvc icecharts-postgres-data -n icecharts

# Check PV status
kubectl get pv

# Resize storage (if supported)
kubectl patch pvc icecharts-postgres-data \
  -n icecharts \
  -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'
```

### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n icecharts

# Check node capacity
kubectl top nodes

# Scale up if constrained
kubectl scale deployment icecharts-api \
  -n icecharts \
  --replicas=5

# Increase limits if appropriate
kubectl set resources deployment icecharts-api \
  -n icecharts \
  --limits=memory=4Gi,cpu=2000m
```

---

## Production Checklist

### Pre-Deployment Checklist

- [ ] Kubernetes cluster created and accessible
- [ ] kubectl configured and authenticated
- [ ] Helm 3.x installed (if using Helm)
- [ ] Storage class available and tested
- [ ] Ingress controller deployed and working
- [ ] Secrets backend configured (AWS/GCP/Azure/Infisical)
- [ ] IAM roles/service accounts created with proper permissions
- [ ] SSL/TLS certificates obtained and configured
- [ ] Domain name purchased and DNS configured
- [ ] Backup storage provisioned
- [ ] Monitoring tools (Prometheus/Grafana) available
- [ ] Firewall rules configured for ingress/egress
- [ ] Load balancer health checks configured
- [ ] Database replication configured (if HA required)
- [ ] Network policies reviewed and approved
- [ ] Security scanning enabled (Trivy, vulnerability scan)
- [ ] Logging aggregation configured (ELK, Stackdriver, etc.)
- [ ] Alerting rules defined and tested
- [ ] Disaster recovery plan documented
- [ ] Team trained on operational procedures

### Post-Deployment Verification

- [ ] All pods running and healthy
- [ ] Services accessible via ingress
- [ ] Database connectivity verified
- [ ] Redis cache operational
- [ ] MinIO object storage working
- [ ] API health endpoint responding
- [ ] Web UI loads without errors
- [ ] Real-time collaboration (WebSocket) functional
- [ ] Login/authentication working
- [ ] API rate limiting active
- [ ] Monitoring stack collecting metrics
- [ ] Log aggregation receiving logs
- [ ] Backup jobs executing successfully
- [ ] Network policies enforcing traffic rules
- [ ] TLS certificates valid and auto-renewable
- [ ] Secret rotation mechanism working
- [ ] Auto-scaling policies tested (if enabled)
- [ ] Pod disruption budgets honored
- [ ] Performance baseline established
- [ ] Security scanning passing without critical issues

### Monitoring Checklist

- [ ] Prometheus collecting API metrics
- [ ] Grafana dashboards displaying data
- [ ] Alert rules defined for:
  - [ ] Pod restart/crash loops
  - [ ] High memory/CPU usage
  - [ ] Database connection failures
  - [ ] API response time degradation
  - [ ] Failed requests (HTTP 5xx)
  - [ ] Disk space utilization
- [ ] Notification channels configured (email/Slack/PagerDuty)
- [ ] Alert thresholds appropriate for workload
- [ ] Log retention policies set
- [ ] Metrics retention configured

### Backup Verification

- [ ] Automated backup jobs running on schedule
- [ ] Backup storage capacity sufficient
- [ ] Backup retention policy enforced
- [ ] Backup integrity verified regularly
- [ ] Restore procedure tested monthly
- [ ] Backup monitoring configured (failure alerts)
- [ ] Backup encryption enabled
- [ ] Recovery time objective (RTO) documented
- [ ] Recovery point objective (RPO) documented

---

## File Structure

```
k8s/
├── docs/
│   └── (This file) KUBERNETES.md
│
├── helm/
│   └── icecharts/
│       ├── Chart.yaml                    # Chart metadata
│       ├── values.yaml                   # Base values with defaults
│       ├── values-local.yaml             # Local dev overrides
│       ├── values-aws.yaml               # AWS EKS overrides
│       ├── values-gcp.yaml               # GCP GKE overrides
│       ├── values-azure.yaml             # Azure AKS overrides
│       └── templates/
│           ├── configmap.yaml            # Application config
│           ├── secret.yaml               # K8s native secrets
│           ├── externalsecret-aws.yaml   # AWS Secrets integration
│           ├── externalsecret-gcp.yaml   # GCP Secret Manager
│           ├── externalsecret-azure.yaml # Azure Key Vault
│           ├── externalsecret-infisical.yaml # Infisical
│           │
│           ├── statefulset-postgres.yaml # PostgreSQL database
│           ├── statefulset-redis.yaml    # Redis cache
│           ├── statefulset-minio.yaml    # MinIO storage
│           │
│           ├── deployment-api.yaml       # Flask API backend
│           ├── deployment-web.yaml       # React frontend
│           │
│           ├── service-postgres.yaml     # PostgreSQL service
│           ├── service-redis.yaml        # Redis service
│           ├── service-minio.yaml        # MinIO service
│           ├── service-api.yaml          # API service
│           ├── service-web.yaml          # Web service
│           ├── service-prometheus.yaml   # Prometheus service
│           ├── service-grafana.yaml      # Grafana service
│           │
│           ├── ingress-traefik.yaml      # Traefik ingress
│           ├── ingress-aws.yaml          # AWS ALB ingress
│           ├── ingress-gcp.yaml          # GCP GCE ingress
│           ├── ingress-azure.yaml        # Azure App Gateway
│           │
│           ├── hpa-api.yaml              # API autoscaling
│           ├── hpa-web.yaml              # Web autoscaling
│           │
│           ├── networkpolicy-postgres.yaml
│           ├── networkpolicy-redis.yaml
│           ├── networkpolicy-minio.yaml
│           ├── networkpolicy-api.yaml
│           ├── networkpolicy-web.yaml
│           │
│           ├── prometheus-deployment.yaml
│           ├── grafana-deployment.yaml
│           ├── servicemonitor-api.yaml
│           │
│           └── cronjob-backup.yaml       # Database backups
│
└── manifests/
    ├── base/
    │   ├── namespace.yaml                # Kubernetes namespace
    │   ├── configmap.yaml                # Application config
    │   ├── secret.yaml                   # K8s native secrets
    │   ├── kustomization.yaml            # Base kustomization
    │   │
    │   ├── postgres/
    │   │   ├── kustomization.yaml
    │   │   ├── statefulset.yaml
    │   │   ├── service.yaml
    │   │   └── pvc.yaml
    │   │
    │   ├── redis/
    │   │   ├── kustomization.yaml
    │   │   ├── statefulset.yaml
    │   │   ├── service.yaml
    │   │   └── pvc.yaml
    │   │
    │   ├── minio/
    │   │   ├── kustomization.yaml
    │   │   ├── statefulset.yaml
    │   │   ├── service.yaml
    │   │   └── pvc.yaml
    │   │
    │   ├── api/
    │   │   ├── kustomization.yaml
    │   │   ├── deployment.yaml
    │   │   └── service.yaml
    │   │
    │   └── web/
    │       ├── kustomization.yaml
    │       ├── deployment.yaml
    │       └── service.yaml
    │
    └── overlays/
        ├── local/                        # Local development
        │   ├── kustomization.yaml
        │   ├── replica-patch.yaml        # Single replicas
        │   ├── resources-patch.yaml      # Reduced resources
        │   └── ingress-patch.yaml        # Traefik ingress
        │
        ├── aws/                          # AWS EKS
        │   ├── kustomization.yaml
        │   ├── replica-patch.yaml        # 3+ replicas
        │   ├── resources-patch.yaml      # Production resources
        │   ├── storage-class-patch.yaml  # GP3 storage
        │   └── ingress-patch.yaml        # ALB ingress
        │
        ├── gcp/                          # GCP GKE
        │   ├── kustomization.yaml
        │   ├── replica-patch.yaml
        │   ├── resources-patch.yaml
        │   ├── storage-class-patch.yaml  # PD-SSD storage
        │   └── ingress-patch.yaml        # GCE ingress
        │
        └── azure/                        # Azure AKS
            ├── kustomization.yaml
            ├── replica-patch.yaml
            ├── resources-patch.yaml
            ├── storage-class-patch.yaml  # Managed premium
            └── ingress-patch.yaml        # App Gateway
```

---

## Additional Resources

### Official Documentation

- **Kubernetes**: https://kubernetes.io/docs/
- **Helm**: https://helm.sh/docs/
- **Kustomize**: https://kustomize.io/
- **kubectl**: https://kubernetes.io/docs/reference/kubectl/

### Cloud Provider Documentation

**AWS EKS**:
- https://docs.aws.amazon.com/eks/
- https://docs.aws.amazon.com/secretsmanager/
- https://docs.aws.amazon.com/elasticloadbalancing/

**GCP GKE**:
- https://cloud.google.com/kubernetes-engine/docs
- https://cloud.google.com/secret-manager/docs
- https://cloud.google.com/load-balancing/docs

**Azure AKS**:
- https://docs.microsoft.com/azure/aks/
- https://docs.microsoft.com/azure/key-vault/
- https://docs.microsoft.com/azure/application-gateway/

### Related Tools

- **External Secrets Operator**: https://external-secrets.io/
- **Traefik Ingress**: https://traefik.io/traefik/
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/

### IceCharts Documentation

- **Deployment Guide**: `/docs/DEPLOYMENT.md`
- **Docker Setup**: `/docs/DOCKER_SETUP.md`
- **Architecture**: `/docs/ARCHITECTURE.md`
- **API Reference**: `/docs/API_REFERENCE.md`

### Support

- **GitHub Issues**: https://github.com/penguintechinc/IceCharts/issues
- **Email**: support@penguintech.io
- **Website**: https://icecharts.penguintech.io

---

## Quick Reference Commands

```bash
# General
kubectl version                               # Check kubectl version
kubectl cluster-info                          # Cluster information
kubectl get nodes                             # List all nodes

# Helm
helm repo update                              # Update Helm repos
helm search repo icecharts                    # Search for chart
helm list -n icecharts                        # List releases
helm status icecharts -n icecharts            # Release status
helm rollback icecharts 1 -n icecharts        # Rollback release

# Kustomize
kubectl kustomize k8s/manifests/overlays/aws/ # Preview manifests
kubectl apply -k k8s/manifests/overlays/aws/  # Apply manifests
kubectl diff -k k8s/manifests/overlays/aws/   # Diff manifests

# Debugging
kubectl logs -n icecharts -l app=api -f       # Stream API logs
kubectl describe pod -n icecharts <pod>       # Pod details
kubectl exec -it -n icecharts <pod> -- bash   # Shell into pod
kubectl get events -n icecharts               # Recent events

# Monitoring
kubectl get pods -n icecharts                 # Pod status
kubectl top pods -n icecharts                 # Pod resource usage
kubectl top nodes                             # Node resource usage

# Scaling
kubectl scale deployment icecharts-api --replicas=5 -n icecharts
kubectl autoscale deployment icecharts-api --min=3 --max=10 -n icecharts

# Secrets
kubectl get secrets -n icecharts              # List secrets
kubectl get secret icecharts-postgres -o yaml # View secret

# Port Forwarding
kubectl port-forward -n icecharts svc/icecharts-web 3000:80
kubectl port-forward -n icecharts svc/icecharts-prometheus 9090:9090

# Cleanup
kubectl delete all -n icecharts               # Delete all resources
kubectl delete namespace icecharts            # Delete namespace
```

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-12
**Maintained by**: Penguin Tech Inc
**License**: Limited AGPL3

This guide provides comprehensive Kubernetes deployment and management for IceCharts across multiple cloud platforms. For additional support, visit the GitHub repository or contact support@penguintech.io.
