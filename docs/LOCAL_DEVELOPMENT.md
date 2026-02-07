# Local Development Guide

## Prerequisites

- Docker
- MicroK8s (for alpha deployment)
- Node.js 20+
- Python 3.13+
- GitHub account with access to `@penguintechinc` organization

## GitHub Package Authentication

This project uses `@penguintechinc/react-libs` from GitHub Packages (private).

### Setup GitHub Token

1. **Create a Personal Access Token (PAT)**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with `read:packages` scope
   - Copy the token (starts with `ghp_`)

2. **Store Token Securely**
   ```bash
   # Option 1: User-level .npmrc (recommended for local dev)
   echo "@penguintechinc:registry=https://npm.pkg.github.com
   //npm.pkg.github.com/:_authToken=YOUR_TOKEN_HERE" > ~/.npmrc

   # Option 2: Project-level (gitignored)
   echo "@penguintechinc:registry=https://npm.pkg.github.com
   //npm.pkg.github.com/:_authToken=YOUR_TOKEN_HERE" > services/webui/.npmrc

   # Option 3: Shared token file (for CI/local builds)
   echo "YOUR_TOKEN_HERE" > ~/code/.gh-token
   ```

3. **For Docker Builds**
   ```bash
   # Export token for Docker build
   export GITHUB_TOKEN=$(cat ~/code/.gh-token)

   # Or pass directly to build
   docker build --build-arg GITHUB_TOKEN="$(cat ~/code/.gh-token)" ...
   ```

### CI/CD (GitHub Actions)

GitHub Actions automatically provides `GITHUB_TOKEN` with appropriate scopes - no manual setup needed.

## Local Development Workflow

### 1. Install Dependencies

```bash
# Frontend
cd services/webui
npm install

# Backend
cd services/flask-backend
pip install -r requirements.txt
```

### 2. Run Development Servers

```bash
# Frontend (with hot reload)
cd services/webui
npm run dev
# Access at http://localhost:5173

# Backend API
cd services/flask-backend
python run.py
# Access at http://localhost:5001
```

### 3. Build Docker Images

```bash
# From project root

# API Image
docker build -t icecharts-api:alpha -f services/flask-backend/Dockerfile .

# Web Image (requires GitHub token)
cd services/webui
TOKEN=$(cat ~/code/.gh-token)
docker build --build-arg GITHUB_TOKEN="$TOKEN" -t icecharts-web:alpha -f Dockerfile.static .
```

## Alpha Deployment (MicroK8s)

### Prerequisites

```bash
# Install MicroK8s
sudo snap install microk8s --classic

# Add your user to microk8s group (IMPORTANT!)
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# Log out and back in for group changes to take effect
# Or run: newgrp microk8s

# Enable required addons (no sudo needed after group add)
microk8s enable dns hostpath-storage helm

# Configure kubectl context
microk8s config > ~/.kube/microk8s-config
kubectl config use-context microk8s

# Verify you can run without sudo
microk8s status
```

### Deploy to Alpha

1. **Build Images**
   ```bash
   # Build both images (see above)
   cd /home/penguin/code/icecharts

   # API
   docker build -t ghcr.io/penguintech/icecharts-api:alpha -f services/flask-backend/Dockerfile .

   # Web
   cd services/webui
   docker build --build-arg GITHUB_TOKEN="$(cat ~/code/.gh-token)" \
     -t ghcr.io/penguintech/icecharts-web:alpha -f Dockerfile.static .
   ```

2. **Import to MicroK8s**
   ```bash
   # Export images to tar
   docker save ghcr.io/penguintech/icecharts-api:alpha \
     ghcr.io/penguintech/icecharts-web:alpha \
     -o /tmp/icecharts-alpha-images.tar

   # Import to MicroK8s (requires sudo)
   sudo microk8s ctr images import /tmp/icecharts-alpha-images.tar

   # Verify import
   sudo microk8s ctr images list | grep icecharts
   ```

3. **Deploy with kubectl**
   ```bash
   # Set context
   kubectl config use-context local-alpha

   # Deploy
   make deploy-alpha

   # Or manually
   kubectl apply -k k8s/manifests/overlays/alpha/
   ```

4. **Access the Application**
   ```bash
   # Port forward to access locally
   kubectl --context local-alpha -n icecharts-alpha port-forward svc/web 8080:80

   # Access at http://localhost:8080
   ```

### Troubleshooting Alpha Deployment

**Images not pulling:**
```bash
# Check if images are in MicroK8s
sudo microk8s ctr images list | grep icecharts

# Re-import if needed
sudo microk8s ctr images import /tmp/icecharts-alpha-images.tar
```

**Pods stuck in Init:**
```bash
# Check init container logs
kubectl --context local-alpha -n icecharts-alpha logs <pod-name> -c wait-for-db

# Check database pod
kubectl --context local-alpha -n icecharts-alpha logs postgres-0
```

**Storage issues:**
```bash
# Verify storage class
kubectl get sc

# Check PVCs
kubectl --context local-alpha -n icecharts-alpha get pvc

# Enable storage if missing
sudo microk8s enable hostpath-storage
```

## Testing

```bash
# Frontend tests
cd services/webui
npm test

# Backend tests
cd services/flask-backend
pytest

# Linting
make lint

# Build tests
./scripts/test-build.sh
```

## Security Best Practices

### ⚠️ DO NOT:
- Commit `.npmrc` files with tokens to git
- Share GitHub tokens in public channels
- Use production tokens for development

### ✅ DO:
- Store tokens in `~/.npmrc` or `~/code/.gh-token`
- Use tokens with minimal required scopes
- Rotate tokens regularly
- Add `.npmrc` to `.gitignore`

## Useful Commands

```bash
# Check alpha deployment status
kubectl --context local-alpha -n icecharts-alpha get pods

# View logs
kubectl --context local-alpha -n icecharts-alpha logs -f <pod-name>

# Shell into pod
kubectl --context local-alpha -n icecharts-alpha exec -it <pod-name> -- /bin/bash

# Delete alpha deployment
kubectl --context local-alpha delete namespace icecharts-alpha

# Rebuild and redeploy
docker build ... && sudo microk8s ctr images import ... && kubectl rollout restart deployment/api deployment/web
```

## Need Help?

- Check the [main README](../README.md)
- Review [CLAUDE.md](../CLAUDE.md) for project context
- See [TESTING.md](./TESTING.md) for testing procedures
- Contact: support@penguintech.io
