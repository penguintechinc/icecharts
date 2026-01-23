#!/bin/bash
# Deploy IceCharts to Beta Environment (dal2-beta)
#
# This script deploys IceCharts to the beta testing environment.
#
# Usage:
#   ./scripts/deploy-beta.sh [--build] [--test] [--no-push]
#
# Options:
#   --build    Build and push Docker images before deploying
#   --test     Run smoke tests after deployment
#   --no-push  Skip pushing images to registry (for local builds)
#
# Prerequisites:
#   - kubectl configured with dal2-beta context
#   - Docker logged in to ghcr.io (for --build option without --no-push)

set -euo pipefail

# Configuration
KUBE_CONTEXT="${KUBE_CONTEXT:-dal2-beta}"
NAMESPACE="icecharts-beta"
OVERLAY_PATH="k8s/manifests/overlays/beta"
REGISTRY="ghcr.io/penguintech"
IMAGE_TAG="beta"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
BUILD_IMAGES=false
RUN_TESTS=false
PUSH_IMAGES=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_IMAGES=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --no-push)
            PUSH_IMAGES=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  IceCharts Beta Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verify kubectl context exists
if ! kubectl config get-contexts "$KUBE_CONTEXT" &>/dev/null; then
    echo -e "${RED}Error: kubectl context '$KUBE_CONTEXT' not found${NC}"
    echo "Available contexts:"
    kubectl config get-contexts --output=name
    exit 1
fi

echo -e "${GREEN}Using kubectl context: $KUBE_CONTEXT${NC}"

# Function to run kubectl with context
kctl() {
    kubectl --context "$KUBE_CONTEXT" "$@"
}

# Build and push images if requested
if [ "$BUILD_IMAGES" = true ]; then
    echo ""
    echo -e "${YELLOW}Building Docker images...${NC}"

    # Build API image (using Dockerfile.notests for faster builds)
    echo -e "${BLUE}Building API image (no tests)...${NC}"
    docker build -t "$REGISTRY/icecharts-api:$IMAGE_TAG" \
        -f services/flask-backend/Dockerfile.notests \
        services/flask-backend/

    # Build Web image (using Dockerfile.notests for faster builds)
    echo -e "${BLUE}Building Web image (no tests)...${NC}"
    docker build -t "$REGISTRY/icecharts-web:$IMAGE_TAG" \
        -f services/webui/Dockerfile.notests \
        services/webui/

    # Push images (unless --no-push is specified)
    if [ "$PUSH_IMAGES" = true ]; then
        echo -e "${BLUE}Pushing images to registry...${NC}"
        docker push "$REGISTRY/icecharts-api:$IMAGE_TAG"
        docker push "$REGISTRY/icecharts-web:$IMAGE_TAG"
        echo -e "${GREEN}Images built and pushed successfully${NC}"
    else
        echo -e "${YELLOW}Skipping push (--no-push specified)${NC}"
        echo -e "${GREEN}Images built successfully (local only)${NC}"
    fi
fi

# Create namespace if it doesn't exist
echo ""
echo -e "${YELLOW}Ensuring namespace exists...${NC}"
if ! kctl get namespace "$NAMESPACE" &>/dev/null; then
    echo -e "${BLUE}Creating namespace $NAMESPACE...${NC}"
    kctl create namespace "$NAMESPACE"
fi

# Apply kustomize overlay
echo ""
echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"
kctl apply -k "$OVERLAY_PATH"

# Wait for deployments to be ready
echo ""
echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"

echo -e "${BLUE}Waiting for API deployment...${NC}"
kctl rollout status deployment/api -n "$NAMESPACE" --timeout=300s

echo -e "${BLUE}Waiting for Web deployment...${NC}"
kctl rollout status deployment/web -n "$NAMESPACE" --timeout=300s

echo -e "${BLUE}Waiting for PostgreSQL...${NC}"
kctl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=300s

echo -e "${BLUE}Waiting for Redis...${NC}"
kctl rollout status statefulset/redis -n "$NAMESPACE" --timeout=300s

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"

# Show deployment status
echo ""
echo -e "${YELLOW}Deployment Status:${NC}"
kctl get pods -n "$NAMESPACE"

echo ""
echo -e "${YELLOW}Services:${NC}"
kctl get svc -n "$NAMESPACE"

# Get service URLs
API_PORT=$(kctl get svc api -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")
WEB_PORT=$(kctl get svc web -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "")

echo ""
echo -e "${BLUE}Access URLs:${NC}"
if [ -n "$API_PORT" ]; then
    echo "  API: http://localhost:$API_PORT/api/v1/health"
fi
if [ -n "$WEB_PORT" ]; then
    echo "  Web: http://localhost:$WEB_PORT"
fi
echo "  Ingress: http://icecharts-beta.local (add to /etc/hosts)"

# Run smoke tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo ""
    echo -e "${YELLOW}Running smoke tests...${NC}"
    KUBE_CONTEXT="$KUBE_CONTEXT" NAMESPACE="$NAMESPACE" ./scripts/test-alpha-smoke.sh
fi

echo ""
echo -e "${GREEN}Done!${NC}"
