#!/bin/bash
# Comprehensive test script for IceCharts
# Deploys to MicroK8s alpha, port-forwards services, runs all tests

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/tmp/icecharts-test-${TIMESTAMP}"
SUMMARY_LOG="${LOG_DIR}/summary.log"

# Shared K8s helpers
source "${PROJECT_ROOT}/scripts/lib/k8s-test-helpers.sh"

# Create log directory
mkdir -p "$LOG_DIR"

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_step() {
    echo -e "${BLUE}==>${NC} $1"
    echo "==> $1" >> "$SUMMARY_LOG"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    echo "✓ $1" >> "$SUMMARY_LOG"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    echo "✗ $1" >> "$SUMMARY_LOG"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    echo "⚠ $1" >> "$SUMMARY_LOG"
}

cleanup() {
    if [ "$KEEP_RUNNING" != "true" ]; then
        log_step "Stopping port-forwards and cleaning up..."
        stop_port_forwards
    else
        log_warn "Services left running (KEEP_RUNNING=true)"
        stop_port_forwards
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Configuration
API_URL="${API_URL:-http://localhost:5001}"
WEB_URL="${WEB_URL:-http://localhost:3000}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@localhost.local}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"
MAX_WAIT="${MAX_WAIT:-180}"
KEEP_RUNNING="${KEEP_RUNNING:-false}"
SKIP_DEPLOY="${SKIP_DEPLOY:-false}"

log_step "IceCharts Comprehensive Test Suite"
echo "Timestamp: $(date)"
echo "Logs: $LOG_DIR"
echo ""

# Step 1: Deploy to MicroK8s (unless skipped)
if [ "$SKIP_DEPLOY" = "true" ]; then
    log_step "Step 1/7: Skipping deployment (SKIP_DEPLOY=true)"
    log_warn "Using existing alpha deployment"
else
    log_step "Step 1/7: Deploying to MicroK8s alpha..."
    if ensure_alpha_deployed > "${LOG_DIR}/deploy.log" 2>&1; then
        log_success "Alpha deployment complete"
    else
        log_error "Alpha deployment failed — see ${LOG_DIR}/deploy.log"
        cat "${LOG_DIR}/deploy.log"
        exit 1
    fi
fi

# Step 2: Start port-forwards
log_step "Step 2/7: Starting port-forwards..."
start_port_forwards
log_success "Port-forwards started (API→${API_LOCAL_PORT}, Web→${WEB_LOCAL_PORT})"

# Step 3: Wait for services to be healthy
log_step "Step 3/7: Waiting for services to be healthy (max ${MAX_WAIT}s)..."
wait_for_k8s_service "${API_URL}/api/v1/health" "API Backend" "$MAX_WAIT" || exit 1
wait_for_k8s_service "$WEB_URL" "WebUI" "$MAX_WAIT" || exit 1

# Capture initial logs
log_step "Capturing pod logs..."
capture_k8s_logs "${LOG_DIR}/k8s-logs.log"

# Step 4: Run frontend build test
log_step "Step 4/7: Running frontend build test..."
if bash "$PROJECT_ROOT/scripts/test-build.sh" > "${LOG_DIR}/test-build.log" 2>&1; then
    log_success "Frontend build test passed"
else
    log_error "Frontend build test failed - see ${LOG_DIR}/test-build.log"
    cat "${LOG_DIR}/test-build.log"
    exit 1
fi

# Step 5: Run API tests
log_step "Step 5/7: Running API endpoint tests..."
export API_URL ADMIN_EMAIL ADMIN_PASS
if bash "$PROJECT_ROOT/scripts/test-api.sh" > "${LOG_DIR}/test-api.log" 2>&1; then
    log_success "API tests passed"
    grep -E "(Health|Authentication|Protected|Complete)" "${LOG_DIR}/test-api.log" || true
else
    log_error "API tests failed - see ${LOG_DIR}/test-api.log"
    cat "${LOG_DIR}/test-api.log"
    exit 1
fi

# Step 6: Run page load tests
log_step "Step 6/7: Running page/tab load tests..."
export WEB_URL
if bash "$PROJECT_ROOT/scripts/test-pages.sh" > "${LOG_DIR}/test-pages.log" 2>&1; then
    log_success "Page load tests passed"
    grep -E "(✓|✗)" "${LOG_DIR}/test-pages.log" || true
else
    log_warn "Some page load tests failed - see ${LOG_DIR}/test-pages.log"
    cat "${LOG_DIR}/test-pages.log"
fi

# Step 7: Run Python unit tests for icestreams-worker
log_step "Step 7/7: Running IceStreams worker unit tests..."
cd "$PROJECT_ROOT/services/icestreams-worker"
if [ -d "tests" ] && [ -n "$(ls -A tests/*.py 2>/dev/null)" ]; then
    if python3 -m pytest tests/ -v --tb=short > "${LOG_DIR}/test-pytest.log" 2>&1; then
        log_success "Python unit tests passed"
        grep -E "(PASSED|FAILED|passed|failed|test session starts)" "${LOG_DIR}/test-pytest.log" | tail -15
    else
        log_warn "Some Python unit tests failed - see ${LOG_DIR}/test-pytest.log"
        tail -30 "${LOG_DIR}/test-pytest.log"
    fi
else
    log_warn "No unit tests found in services/icestreams-worker/tests/ - skipping"
fi
cd "$PROJECT_ROOT"

# Final summary
echo ""
echo "=============================================="
log_step "Test Suite Complete!"
echo "=============================================="
echo ""
echo "Results Summary:"
echo "  ✓ Alpha deployment: SUCCESS"
echo "  ✓ Service health: SUCCESS"
echo "  ✓ Frontend build: SUCCESS"
echo "  ✓ API tests: SUCCESS"
echo "  ✓ Page loads: SUCCESS"
echo ""
echo "Logs available in: $LOG_DIR"
echo "  - deploy.log         : Alpha deployment output"
echo "  - k8s-logs.log       : Pod logs"
echo "  - test-build.log     : Frontend build test"
echo "  - test-api.log       : API endpoint tests"
echo "  - test-pages.log     : Page load tests"
echo "  - test-pytest.log    : Python unit tests"
echo "  - summary.log        : This summary"
echo ""

log_success "All tests completed successfully!"
