#!/bin/bash

# Deploy to Beta - Automated Helm Deployment
# Deploys to beta K8s cluster with rollback capability

set -uo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
KUBE_CONTEXT="${KUBE_CONTEXT:-dal2-beta}"
NAMESPACE="${NAMESPACE:-icecharts-beta}"
RELEASE_NAME="icecharts"
CHART_PATH="$PROJECT_ROOT/k8s/helm/icecharts"
VALUES_FILE="$PROJECT_ROOT/k8s/helm/icecharts/values-beta.yaml"
IMAGE_REGISTRY="registry-dal2.penguintech.io"
VERSION_FILE="$PROJECT_ROOT/.version"
APP_HOST="icecharts.penguintech.io"
ALB_ENDPOINT="dal2.penguintech.io"

# Default flags
DRY_RUN=0
ROLLBACK=0
SHOW_LOGS=0
VERBOSE=0
FORCE_CONFLICTS=0
BUILD_IMAGES=1
SERVICE=""
IMAGE_TAG=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        return 1
    fi
    log_info "kubectl: $(kubectl version --client -o yaml 2>/dev/null | grep gitVersion | awk '{print $2}')"

    # Check helm v3+
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed or not in PATH"
        return 1
    fi
    local helm_major
    helm_major=$(helm version --short 2>/dev/null | grep -oP '(?<=v)\d+')
    if [ -z "$helm_major" ] || [ "$helm_major" -lt 3 ]; then
        log_error "helm v3+ is required (found: $(helm version --short 2>/dev/null))"
        return 1
    fi
    log_info "helm: $(helm version --short)"

    # Check context exists
    if ! kubectl config get-contexts "$KUBE_CONTEXT" &> /dev/null; then
        log_error "Kubernetes context not found: $KUBE_CONTEXT"
        return 1
    fi
    log_info "Kubernetes context: $KUBE_CONTEXT"

    # Check chart path
    if [ ! -d "$CHART_PATH" ]; then
        log_error "Helm chart not found: $CHART_PATH"
        return 1
    fi
    log_info "Helm chart path: $CHART_PATH"

    # Check values file
    if [ ! -f "$VALUES_FILE" ]; then
        log_error "Values file not found: $VALUES_FILE"
        return 1
    fi
    log_info "Values file: $VALUES_FILE"

    # For non-dry-run, check if namespace exists
    if [ "$DRY_RUN" -eq 0 ]; then
        if ! kubectl --context="$KUBE_CONTEXT" get namespace "$NAMESPACE" &> /dev/null; then
            log_warn "Namespace '$NAMESPACE' does not exist, will be created"
        else
            log_info "Namespace exists: $NAMESPACE"
        fi
    fi

    return 0
}

# Verify images
verify_images() {
    log_section "Image Verification"

    if [ "$DRY_RUN" -eq 1 ]; then
        log_info "Dry-run mode: skipping registry verification"
        return 0
    fi

    log_info "Image registry: $IMAGE_REGISTRY"
    log_info "Image tag: $IMAGE_TAG"

    if [ -z "$SERVICE" ]; then
        log_info "Services to deploy: web, api"
        log_info "  - $IMAGE_REGISTRY/icecharts-web:$IMAGE_TAG"
        log_info "  - $IMAGE_REGISTRY/icecharts-api:$IMAGE_TAG"
    else
        log_info "Service to deploy: $SERVICE"
        log_info "  - $IMAGE_REGISTRY/icecharts-$SERVICE:$IMAGE_TAG"
    fi

    return 0
}

# Perform rollback
do_rollback() {
    log_section "Rolling Back Deployment"

    log_info "Rolling back release '$RELEASE_NAME' in namespace '$NAMESPACE'..."

    if ! helm rollback "$RELEASE_NAME" \
        --kube-context="$KUBE_CONTEXT" \
        -n "$NAMESPACE" 2>&1 | grep -v "^$"; then
        log_error "Helm rollback failed"
        return 1
    fi

    # Check rollback succeeded
    sleep 5
    log_info "Checking pod status after rollback..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get pods

    log_info "Rollback completed successfully"
    return 0
}

# Perform deployment
do_deploy() {
    log_section "Deploying with Helm"

    local helm_cmd_args=("upgrade")

    # Check if namespace already exists to avoid --create-namespace conflicts
    local ns_flag=""
    if ! kubectl --context="$KUBE_CONTEXT" get namespace "$NAMESPACE" &> /dev/null; then
        ns_flag="--create-namespace"
    fi

    if [ -z "$SERVICE" ]; then
        # Deploy all services - use --install to create if not exists
        helm_cmd_args+=(
            "--install"
            "$RELEASE_NAME"
            "$CHART_PATH"
            "--kube-context=$KUBE_CONTEXT"
            "--namespace=$NAMESPACE"
            "--values=$VALUES_FILE"
            "--set=image.tag=$IMAGE_TAG"
            "--wait"
            "--timeout=10m"
        )
        if [ -n "$ns_flag" ]; then
            helm_cmd_args+=("$ns_flag")
        fi
        if [ "$FORCE_CONFLICTS" -eq 1 ]; then
            helm_cmd_args+=("--force-conflicts")
        fi
    else
        # Deploy single service - reuse existing values, update only one image
        helm_cmd_args+=(
            "$RELEASE_NAME"
            "$CHART_PATH"
            "--kube-context=$KUBE_CONTEXT"
            "--namespace=$NAMESPACE"
            "--reuse-values"
            "--set=${SERVICE}.image.tag=$IMAGE_TAG"
            "--wait"
            "--timeout=10m"
        )
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        helm_cmd_args+=("--dry-run")
    fi

    # Log the full command
    log_info "Executing: helm ${helm_cmd_args[*]}"
    echo ""

    if ! helm "${helm_cmd_args[@]}"; then
        log_error "Helm deployment failed"
        return 1
    fi

    log_info "Helm deployment completed"
    return 0
}

# Verify deployment
verify_deployment() {
    if [ "$DRY_RUN" -eq 1 ]; then
        log_info "Dry-run mode: skipping deployment verification"
        return 0
    fi

    log_section "Verifying Deployment"

    if [ -z "$SERVICE" ]; then
        # Check both services
        log_info "Checking rollout status for 'web'..."
        if ! kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout status deployment/web --timeout=300s; then
            log_error "Web service rollout failed"
            return 1
        fi

        log_info "Checking rollout status for 'api'..."
        if ! kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout status deployment/api --timeout=300s; then
            log_error "API service rollout failed"
            return 1
        fi
    else
        # Check single service
        log_info "Checking rollout status for '$SERVICE'..."
        if ! kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout status deployment/"$SERVICE" --timeout=300s; then
            log_error "$SERVICE service rollout failed"
            return 1
        fi
    fi

    log_info "Showing pod status..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get pods

    return 0
}

# Run smoke tests
run_smoke_tests() {
    log_section "Running Smoke Tests"

    local app_http_code
    local api_http_code

    # Test main page
    log_info "Testing main page: https://$ALB_ENDPOINT/"
    app_http_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/")
    if [ "$app_http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Main page: HTTP $app_http_code"
    else
        echo -e "${RED}✗${NC} Main page: HTTP $app_http_code (expected 200)"
    fi

    # Test API health
    log_info "Testing API health: https://$ALB_ENDPOINT/api/v1/health"
    api_http_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health")
    if [ "$api_http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} API health: HTTP $api_http_code"
    else
        echo -e "${RED}✗${NC} API health: HTTP $api_http_code (expected 200)"
    fi

    # Check if any test failed
    if [ "$app_http_code" != "200" ] || [ "$api_http_code" != "200" ]; then
        log_error "Smoke tests failed"
        if [ "$DRY_RUN" -eq 0 ]; then
            log_warn "Attempting automatic rollback..."
            if do_rollback; then
                log_error "Smoke tests failed and rollback was performed"
            else
                log_error "Smoke tests failed and rollback also failed"
            fi
        fi
        return 1
    fi

    log_info "All smoke tests passed"
    return 0
}

# Show deployment logs
show_deployment_logs() {
    log_section "Deployment Logs"

    if [ -z "$SERVICE" ]; then
        log_info "=== Web Service Logs ==="
        kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" logs -l app=web --tail=50 2>/dev/null || true

        echo ""
        log_info "=== API Service Logs ==="
        kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" logs -l app=api --tail=50 2>/dev/null || true
    else
        log_info "=== $SERVICE Service Logs ==="
        kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" logs -l app="$SERVICE" --tail=50 2>/dev/null || true
    fi
}

# Build and push images with epoch64 tag
build_and_push_images() {
    log_section "Building and Pushing Docker Images"

    local EPOCH
    EPOCH=$(date +%s)
    local TAG_WITH_EPOCH="beta-${EPOCH}"

    # Update IMAGE_TAG to include epoch if not explicitly set
    if [ -z "$IMAGE_TAG" ] || [ "$IMAGE_TAG" = "beta" ]; then
        IMAGE_TAG="$TAG_WITH_EPOCH"
        log_info "Generated build tag with epoch: $IMAGE_TAG"
    fi

    # Web image
    log_info "Building web image: $IMAGE_REGISTRY/icecharts-web:$IMAGE_TAG"

    # Copy react_libs into webui context temporarily
    cp -r "$PROJECT_ROOT/shared/react_libs" "$PROJECT_ROOT/services/webui/_react_libs_build" || {
        log_error "Failed to copy react_libs"
        return 1
    }

    # Modify package.json temporarily to use local react_libs path
    local orig_package="$PROJECT_ROOT/services/webui/package.json"
    cp "$orig_package" "$orig_package.bak"

    python3 -c "
import json
with open('$orig_package', 'r') as f:
    data = json.load(f)
if '@penguin/react_libs' in data.get('dependencies', {}):
    data['dependencies']['@penguin/react_libs'] = 'file:./_react_libs_build'
with open('$orig_package', 'w') as f:
    json.dump(data, f, indent=2)
" || {
        log_error "Failed to update package.json"
        mv "$orig_package.bak" "$orig_package"
        rm -rf "$PROJECT_ROOT/services/webui/_react_libs_build"
        return 1
    }

    # Regenerate lock file
    cd "$PROJECT_ROOT/services/webui" || return 1
    rm -f package-lock.json
    if ! npm install 2>&1 | tail -3; then
        log_warn "npm install may have warnings (proceeding)"
    fi
    cd "$PROJECT_ROOT" || return 1

    # Build web image (using sed to replace npm ci with npm install for dependency resolution)
    local docker_file_tmp="$PROJECT_ROOT/services/webui/Dockerfile.static.tmp"
    sed 's/npm ci/npm install/g' "$PROJECT_ROOT/services/webui/Dockerfile.static" > "$docker_file_tmp"

    if ! docker build \
        -t "$IMAGE_REGISTRY/icecharts-web:$IMAGE_TAG" \
        -t "$IMAGE_REGISTRY/icecharts-web:beta" \
        -f "$docker_file_tmp" \
        "$PROJECT_ROOT/services/webui" 2>&1 | tail -5 | grep -E "Successfully tagged|Error|error"; then
        log_error "Web image build failed"
        mv "$orig_package.bak" "$orig_package"
        rm -rf "$PROJECT_ROOT/services/webui/_react_libs_build" "$docker_file_tmp"
        return 1
    fi

    rm -f "$docker_file_tmp"

    # Restore package.json
    mv "$orig_package.bak" "$orig_package"
    rm -rf "$PROJECT_ROOT/services/webui/_react_libs_build"

    # API image
    log_info "Building API image: $IMAGE_REGISTRY/icecharts-api:$IMAGE_TAG"
    if ! docker build \
        -t "$IMAGE_REGISTRY/icecharts-api:$IMAGE_TAG" \
        -t "$IMAGE_REGISTRY/icecharts-api:beta" \
        -f "$PROJECT_ROOT/services/flask-backend/Dockerfile" \
        "$PROJECT_ROOT/services/flask-backend" 2>&1 | grep -E "Successfully tagged|Error|error"; then
        log_error "API image build failed"
        return 1
    fi

    # Push images
    log_info "Pushing images to registry"
    if ! docker push "$IMAGE_REGISTRY/icecharts-web:$IMAGE_TAG" 2>&1 | tail -3; then
        log_error "Failed to push web image"
        return 1
    fi
    if ! docker push "$IMAGE_REGISTRY/icecharts-web:beta" 2>&1 | tail -3; then
        log_error "Failed to push web:beta tag"
        return 1
    fi

    if ! docker push "$IMAGE_REGISTRY/icecharts-api:$IMAGE_TAG" 2>&1 | tail -3; then
        log_error "Failed to push API image"
        return 1
    fi
    if ! docker push "$IMAGE_REGISTRY/icecharts-api:beta" 2>&1 | tail -3; then
        log_error "Failed to push api:beta tag"
        return 1
    fi

    log_info "Images built and pushed successfully: $IMAGE_TAG (and beta tag)"
    return 0
}

# Main execution
main() {
    log_section "Beta Deployment Script"

    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        exit 1
    fi

    # Handle rollback
    if [ "$ROLLBACK" -eq 1 ]; then
        if ! do_rollback; then
            exit 1
        fi
        log_info "Rollback completed successfully"
        exit 0
    fi

    # Build and push images (unless --skip-build)
    if [ "$BUILD_IMAGES" -eq 1 ]; then
        if ! build_and_push_images; then
            log_error "Image build/push failed"
            exit 2
        fi
    fi

    # Verify images
    if ! verify_images; then
        log_error "Image verification failed"
        exit 2
    fi

    # Deploy
    if ! do_deploy; then
        log_error "Deployment failed"
        exit 3
    fi

    # Verify deployment (only for non-dry-run)
    if ! verify_deployment; then
        log_error "Deployment verification failed"
        exit 3
    fi

    # Run smoke tests (only for non-dry-run)
    if [ "$DRY_RUN" -eq 0 ]; then
        if ! run_smoke_tests; then
            exit 4
        fi
    fi

    # Show logs if requested
    if [ "$SHOW_LOGS" -eq 1 ]; then
        show_deployment_logs
    fi

    # Final summary
    log_section "Deployment Summary"
    echo -e "${GREEN}✓${NC} Release: $RELEASE_NAME"
    echo -e "${GREEN}✓${NC} Namespace: $NAMESPACE"
    echo -e "${GREEN}✓${NC} Image tag: $IMAGE_TAG"
    if [ -z "$SERVICE" ]; then
        echo -e "${GREEN}✓${NC} Services: all (web, api)"
    else
        echo -e "${GREEN}✓${NC} Service: $SERVICE"
    fi
    echo -e "${GREEN}✓${NC} Application URL: https://$APP_HOST"

    if [ "$DRY_RUN" -eq 1 ]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} No actual deployment performed"
    fi

    log_info "Deployment completed successfully!"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag=*)
            IMAGE_TAG="${1#*=}"
            shift
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --service=*)
            SERVICE="${1#*=}"
            shift
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --skip-build)
            BUILD_IMAGES=0
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --force-conflicts)
            FORCE_CONFLICTS=1
            shift
            ;;
        --rollback)
            ROLLBACK=1
            shift
            ;;
        --logs)
            SHOW_LOGS=1
            shift
            ;;
        --context=*)
            KUBE_CONTEXT="${1#*=}"
            shift
            ;;
        --context)
            KUBE_CONTEXT="$2"
            shift 2
            ;;
        --namespace=*)
            NAMESPACE="${1#*=}"
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Deploy to beta K8s cluster using Helm"
            echo ""
            echo "Options:"
            echo "  --tag=TAG           Image tag to deploy (default: beta-{EPOCH} timestamp)"
            echo "  --service=SERVICE   Deploy only a specific service: web or api (default: all services)"
            echo "  --skip-build        Skip building and pushing images (use existing tags)"
            echo "  --dry-run           Helm dry-run only, no actual deployment"
            echo "  --force-conflicts   Force adoption of resources with ownership conflicts (Helm v4)"
            echo "  --rollback          Rollback to previous Helm release"
            echo "  --logs              Show pod logs after deployment"
            echo "  --context=CONTEXT   Override kube context (default: dal2-beta)"
            echo "  --namespace=NS      Override namespace (default: icecharts-beta)"
            echo "  -v, --verbose       Verbose output"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Deploy all services with default tag"
            echo "  $0 --tag=v1.0.3-beta                 # Deploy all with specific tag"
            echo "  $0 --service=web                      # Deploy only web service"
            echo "  $0 --service=api --tag=v1.0.3-beta   # Deploy only api with specific tag"
            echo "  $0 --dry-run                          # Helm dry-run only"
            echo "  $0 --rollback                         # Rollback to previous release"
            echo "  $0 --logs                             # Show logs after deployment"
            echo ""
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate service if provided
if [ -n "$SERVICE" ]; then
    case "$SERVICE" in
        web|api)
            ;;
        *)
            log_error "Invalid service: $SERVICE (must be 'web' or 'api')"
            exit 1
            ;;
    esac
fi

# Determine IMAGE_TAG if not provided
if [ -z "$IMAGE_TAG" ]; then
    if [ ! -f "$VERSION_FILE" ]; then
        log_error "Version file not found: $VERSION_FILE"
        exit 1
    fi
    VERSION_CONTENT=$(cat "$VERSION_FILE")
    IMAGE_TAG="v${VERSION_CONTENT}-beta"
    log_info "Using default image tag from .version: $IMAGE_TAG"
fi

# Run main
main
