# Alpha Deployment - Final Steps

## Current Status

✅ Images built and ready:
- `ghcr.io/penguintech/icecharts-api:alpha` (667MB)
- `ghcr.io/penguintech/icecharts-web:alpha` (248MB)
- Exported to: `/tmp/icecharts-alpha-images.tar` (908MB)

✅ Kubernetes resources created in `icecharts-alpha` namespace

⏸️ Waiting for: Image import to MicroK8s

## Fix Group Membership (One-Time Setup)

To run MicroK8s commands without sudo:

```bash
# Add your user to microk8s group
sudo usermod -a -G microk8s $USER
sudo chown -f -R $USER ~/.kube

# Apply group changes (choose one):
# Option 1: Log out and back in
# Option 2: Run in new shell
newgrp microk8s
```

## Complete Image Import

Once you're in the microk8s group:

```bash
# Import images (no sudo needed!)
microk8s ctr images import /tmp/icecharts-alpha-images.tar

# Verify import
microk8s ctr images list | grep icecharts

# Expected output:
# ghcr.io/penguintech/icecharts-api:alpha
# ghcr.io/penguintech/icecharts-web:alpha
```

## Restart Deployments

```bash
# Set kubectl context
kubectl config use-context local-alpha

# Restart to use local images
kubectl -n icecharts-alpha rollout restart deployment/api deployment/web

# Watch pods come up
kubectl -n icecharts-alpha get pods -w

# Expected: All pods Running within 1-2 minutes
```

## Verify Deployment

```bash
# Check all pods are running
kubectl -n icecharts-alpha get pods

# Expected output:
# NAME                   READY   STATUS    RESTARTS   AGE
# api-xxx-yyy            1/1     Running   0          1m
# web-xxx-yyy            1/1     Running   0          1m
# postgres-0             1/1     Running   0          5m
# redis-0                1/1     Running   0          5m
# minio-0                1/1     Running   0          5m

# Port forward to access
kubectl -n icecharts-alpha port-forward svc/web 8080:80
```

## Access Application

Open browser to: **http://localhost:8080**

### Test Unified Approval Center

1. Login with admin credentials
2. Navigate to sidebar → **"Approval Center"** (should show badge if approvals pending)
3. View unified approvals from:
   - IceFlows (pipeline promotions)
   - IceStreams (playbook execution gates)
4. Test approve/reject functionality

## Troubleshooting

### Images not found in MicroK8s
```bash
# Check Docker has images
docker images | grep "ghcr.io.*alpha"

# Re-export if needed
docker save ghcr.io/penguintech/icecharts-api:alpha \
  ghcr.io/penguintech/icecharts-web:alpha \
  -o /tmp/icecharts-alpha-images.tar

# Import again
microk8s ctr images import /tmp/icecharts-alpha-images.tar
```

### Pods still showing ImagePullBackOff
```bash
# Delete old pods to force recreation
kubectl -n icecharts-alpha delete pod -l app.kubernetes.io/name=icecharts

# Wait for new pods
kubectl -n icecharts-alpha get pods -w
```

### Database connection issues
```bash
# Check postgres logs
kubectl -n icecharts-alpha logs postgres-0

# Check API init container
kubectl -n icecharts-alpha logs <api-pod-name> -c wait-for-db

# Restart postgres if needed
kubectl -n icecharts-alpha rollout restart statefulset/postgres
```

## Clean Up (If Needed)

```bash
# Remove deployment
kubectl delete namespace icecharts-alpha

# Remove images
microk8s ctr images rm ghcr.io/penguintech/icecharts-api:alpha
microk8s ctr images rm ghcr.io/penguintech/icecharts-web:alpha

# Remove tar file
rm /tmp/icecharts-alpha-images.tar
```

## Next Steps

Once verified:
1. Commit any outstanding changes
2. Test the unified approval center functionality
3. Run smoke tests: `make test-alpha`
4. Consider deploying to beta: `make deploy-beta`
