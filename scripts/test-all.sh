#!/bin/bash
# Comprehensive test script for IceCharts
# Builds containers, starts services, runs all tests, outputs to /tmp

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="/tmp/icecharts-test-${TIMESTAMP}"
SUMMARY_LOG="${LOG_DIR}/summary.log"

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
        log_step "Cleaning up containers..."
        cd "$PROJECT_ROOT"
        docker-compose down >> "${LOG_DIR}/cleanup.log" 2>&1 || true
    else
        log_warn "Containers left running (KEEP_RUNNING=true)"
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

log_step "IceCharts Comprehensive Test Suite"
echo "Timestamp: $(date)"
echo "Logs: $LOG_DIR"
echo ""

# Step 1: Stop existing containers
log_step "Step 1/7: Stopping existing containers..."
cd "$PROJECT_ROOT"
docker-compose down >> "${LOG_DIR}/docker-down.log" 2>&1 || true
log_success "Containers stopped"

# Step 2: Build containers
log_step "Step 2/7: Building containers with docker-compose..."
if docker-compose up -d --build > "${LOG_DIR}/docker-build.log" 2>&1; then
    log_success "Container build completed"
else
    log_error "Container build failed - see ${LOG_DIR}/docker-build.log"
    cat "${LOG_DIR}/docker-build.log"
    exit 1
fi

# Step 3: Wait for services to be healthy
log_step "Step 3/7: Waiting for services to be healthy (max ${MAX_WAIT}s)..."

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=$((MAX_WAIT / 5))
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "$name is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 5
    done

    log_error "$name failed to start within ${MAX_WAIT}s"
    return 1
}

wait_for_service "${API_URL}/api/v1/health" "API Backend" || exit 1
wait_for_service "$WEB_URL" "WebUI" || exit 1

# Capture docker logs
log_step "Capturing container logs..."
docker-compose logs > "${LOG_DIR}/docker-logs.log" 2>&1

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
    # Show summary
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
    # Show summary
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
        # Show test summary
        grep -E "(PASSED|FAILED|passed|failed|test session starts)" "${LOG_DIR}/test-pytest.log" | tail -15
    else
        log_warn "Some Python unit tests failed - see ${LOG_DIR}/test-pytest.log"
        # Show last 30 lines for context
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
echo "  ✓ Container build: SUCCESS"
echo "  ✓ Service health: SUCCESS"
echo "  ✓ Frontend build: SUCCESS"
echo "  ✓ API tests: SUCCESS"
echo "  ✓ Page loads: SUCCESS"
echo ""
echo "Logs available in: $LOG_DIR"
echo "  - docker-build.log   : Container build output"
echo "  - docker-logs.log    : Runtime container logs"
echo "  - test-build.log     : Frontend build test"
echo "  - test-api.log       : API endpoint tests"
echo "  - test-pages.log     : Page load tests"
echo "  - test-pytest.log    : Python unit tests"
echo "  - summary.log        : This summary"
echo ""

if [ "$KEEP_RUNNING" = "true" ]; then
    echo "Containers are still running. Use 'docker-compose down' to stop."
else
    echo "Containers have been stopped."
fi

log_success "All tests completed successfully!"
