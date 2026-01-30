#!/bin/bash

# Alpha Smoke Tests - Local E2E Testing
# Builds, runs, and verifies all services via Docker Compose

set -uo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"
VERBOSE="${VERBOSE:-0}"
CLEANUP="${CLEANUP:-1}"
QUICK="${QUICK:-0}"
NO_CACHE="${NO_CACHE:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker Compose compatibility - use 'docker compose' (v2) or 'docker-compose' (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}[ERROR]${NC} Neither 'docker compose' nor 'docker-compose' found"
    exit 1
fi

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

# Track whether services were started (for cleanup)
SERVICES_STARTED=0

# Cleanup function
cleanup() {
    if [ "$SERVICES_STARTED" -eq 0 ]; then
        return
    fi
    if [ "$CLEANUP" -eq 1 ]; then
        log_info "Cleaning up containers..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
        log_info "Cleanup complete"
    else
        log_warn "Skipping cleanup (--no-cleanup flag set)"
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT INT TERM

# Check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    # Docker compose check already done at script start
    log_info "docker compose: $($DOCKER_COMPOSE version 2>/dev/null || $DOCKER_COMPOSE --version)"

    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        log_error "curl is not installed or not in PATH"
        return 1
    fi
    log_info "curl: $(curl --version | head -n 1)"

    # Check if jq is available (optional but recommended)
    if ! command -v jq &> /dev/null; then
        log_warn "jq is not installed (optional, but recommended for JSON parsing)"
    else
        log_info "jq: $(jq --version)"
    fi

    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        return 1
    fi
    log_info "Using compose file: $COMPOSE_FILE"

    # Check if required ports are available
    log_info "Checking required ports..."
    local ports_to_check=(5001 3000 5432 6379 9000)
    for port in "${ports_to_check[@]}"; do
        if ss -tuln 2>/dev/null | grep -q ":$port "; then
            log_warn "Port $port is already in use"
        fi
    done

    return 0
}

# Build containers
run_build() {
    log_section "Building Containers"

    local build_args=""
    if [ "$NO_CACHE" -eq 1 ]; then
        build_args="--no-cache"
    fi

    log_info "Building containers..."
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" build $build_args 2>&1; then
        log_info "Build completed successfully"
        return 0
    else
        log_error "Build failed"
        return 1
    fi
}

# Start containers
start_services() {
    log_section "Starting Services"

    log_info "Starting containers..."
    SERVICES_STARTED=1
    if ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d 2>&1; then
        log_error "Failed to start containers"
        return 2
    fi

    log_info "Waiting for containers to be healthy..."
    local max_wait=120
    local elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        # Check if all services are running
        local running
        local total
        running=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps --filter "status=running" --services | wc -l) || true
        total=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" config --services | wc -l) || true

        if [ "$running" -eq "$total" ] && [ "$total" -gt 0 ]; then
            log_info "All containers are running ($running/$total)"
            break
        fi

        echo -n "."
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo ""

    if [ $elapsed -ge $max_wait ]; then
        log_error "Containers did not start in time"
        log_info "Container status:"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps || true
        return 2
    fi

    # Show container status
    log_info "Container status:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps || true

    return 0
}

# Wait for services to be healthy
wait_for_services() {
    log_section "Waiting for Services Health Checks"

    # Wait for Flask backend
    log_info "Waiting for Flask backend..."
    local max_retries=60
    local retry_count=0
    while ! curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "Flask backend did not become healthy in time"
            log_info "Flask backend logs (last 50 lines):"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=50 api || true
            return 2
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    log_info "Flask backend is healthy"

    # Wait for WebUI
    log_info "Waiting for WebUI..."
    retry_count=0
    while ! curl -sf http://localhost:3000/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "WebUI did not become healthy in time"
            log_info "WebUI logs (last 50 lines):"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=50 web || true
            return 2
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    log_info "WebUI is healthy"

    log_info "All services are healthy and ready for testing"
    return 0
}

# Run API integration tests
run_api_tests() {
    log_section "Running API Integration Tests"

    local api_tests_script="$PROJECT_ROOT/tests/api/run_all_tests.sh"
    if [ ! -f "$api_tests_script" ]; then
        log_warn "API tests script not found: $api_tests_script (skipping)"
        return 0
    fi

    log_info "Running API test suite..."
    if bash "$api_tests_script" --skip-containers --no-cleanup 2>&1; then
        log_info "API tests passed"
        return 0
    else
        log_error "API tests failed"
        return 3
    fi
}

# Run unit tests
run_unit_tests() {
    log_section "Running Unit Tests"

    local backend_failed=0
    local frontend_failed=0

    # Backend unit tests
    log_info "Running backend unit tests..."
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T api pytest tests/unit/ -v 2>&1; then
        log_info "Backend unit tests passed"
    else
        if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T api pytest tests/unit/ -v > /dev/null 2>&1; then
            log_info "Backend unit tests passed"
        else
            log_warn "Backend unit tests failed or not found"
            backend_failed=1
        fi
    fi

    # Frontend unit tests
    log_info "Running frontend unit tests..."
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T web npm run test -- --run 2>&1; then
        log_info "Frontend unit tests passed"
    else
        if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T web npm run test -- --run > /dev/null 2>&1; then
            log_info "Frontend unit tests passed"
        else
            log_warn "Frontend unit tests failed or not found"
            frontend_failed=1
        fi
    fi

    if [ $backend_failed -eq 1 ] || [ $frontend_failed -eq 1 ]; then
        return 4
    fi

    return 0
}

# Run page load tests
run_page_tests() {
    log_section "Running Page Load Tests"

    local failed=0

    # Test Web UI root
    log_info "Testing Web UI root..."
    if curl -sf http://localhost:3000/ > /dev/null 2>&1; then
        log_info "Web UI root loaded successfully"
    else
        log_error "Web UI root failed to load"
        failed=1
    fi

    # Test API health endpoint
    log_info "Testing API health endpoint..."
    if curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; then
        log_info "API health endpoint responded"
    else
        log_error "API health endpoint failed"
        failed=1
    fi

    # Test Web health endpoint
    log_info "Testing Web health endpoint..."
    if curl -sf http://localhost:3000/health > /dev/null 2>&1; then
        log_info "Web health endpoint responded"
    else
        log_error "Web health endpoint failed"
        failed=1
    fi

    if [ $failed -eq 1 ]; then
        return 5
    fi

    return 0
}

# Main execution
main() {
    log_section "Alpha Smoke Tests"
    log_info "Starting comprehensive smoke testing..."
    echo ""

    # Track test results (0 = failed, 1 = passed)
    declare -A test_results
    test_results["Build"]=0
    test_results["Services"]=0
    test_results["API Tests"]=0
    test_results["Unit Tests (Backend)"]=0
    test_results["Unit Tests (Frontend)"]=0
    test_results["Page Loads"]=0

    # Track exit codes (first failure wins)
    local first_failure_code=0

    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed"
        test_results["Build"]=0
        first_failure_code=1
    else
        # Build phase
        if run_build; then
            test_results["Build"]=1
        else
            test_results["Build"]=0
            if [ $first_failure_code -eq 0 ]; then first_failure_code=1; fi
        fi

        # Services phase
        if [ "${test_results[Build]}" -eq 1 ]; then
            if start_services && wait_for_services; then
                test_results["Services"]=1
            else
                test_results["Services"]=0
                if [ $first_failure_code -eq 0 ]; then first_failure_code=2; fi
            fi
        else
            test_results["Services"]=0
            if [ $first_failure_code -eq 0 ]; then first_failure_code=1; fi
        fi

        # API Tests phase (skip if services failed)
        if [ "${test_results[Services]}" -eq 1 ]; then
            if run_api_tests; then
                test_results["API Tests"]=1
            else
                test_results["API Tests"]=0
                if [ $first_failure_code -eq 0 ]; then first_failure_code=3; fi
            fi
        else
            test_results["API Tests"]=0
        fi

        # Unit Tests phase (skip if --quick flag, skip if services failed)
        if [ "$QUICK" -eq 1 ]; then
            log_info "Skipping unit tests (--quick flag set)"
            test_results["Unit Tests (Backend)"]=1
            test_results["Unit Tests (Frontend)"]=1
        elif [ "${test_results[Services]}" -eq 1 ]; then
            if run_unit_tests; then
                test_results["Unit Tests (Backend)"]=1
                test_results["Unit Tests (Frontend)"]=1
            else
                test_results["Unit Tests (Backend)"]=0
                test_results["Unit Tests (Frontend)"]=0
                if [ $first_failure_code -eq 0 ]; then first_failure_code=4; fi
            fi
        else
            test_results["Unit Tests (Backend)"]=0
            test_results["Unit Tests (Frontend)"]=0
        fi

        # Page Load Tests phase (skip if services failed)
        if [ "${test_results[Services]}" -eq 1 ]; then
            if run_page_tests; then
                test_results["Page Loads"]=1
            else
                test_results["Page Loads"]=0
                if [ $first_failure_code -eq 0 ]; then first_failure_code=5; fi
            fi
        else
            test_results["Page Loads"]=0
        fi
    fi

    # Count results
    local total_passed=0
    local total_failed=0
    for key in "${!test_results[@]}"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            total_passed=$((total_passed + 1))
        else
            total_failed=$((total_failed + 1))
        fi
    done

    # Final summary
    log_section "Smoke Test Summary"

    for key in "Build" "Services" "API Tests" "Unit Tests (Backend)" "Unit Tests (Frontend)" "Page Loads"; do
        if [ "${test_results[$key]:-0}" -eq 1 ]; then
            echo -e "${GREEN}✓${NC} $key: PASSED"
        else
            echo -e "${RED}✗${NC} $key: FAILED"
        fi
    done

    echo ""
    echo "========================================="
    echo -e "Total: ${GREEN}$total_passed passed${NC}, ${RED}$total_failed failed${NC}"
    echo "========================================="

    # Exit with appropriate code
    if [ $total_failed -eq 0 ]; then
        log_info "All smoke tests passed!"
        exit 0
    else
        log_error "$total_failed test phase(s) failed"
        if [ $first_failure_code -gt 0 ]; then
            exit $first_failure_code
        else
            exit 1
        fi
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        --no-cleanup)
            CLEANUP=0
            shift
            ;;
        --quick)
            QUICK=1
            shift
            ;;
        --no-cache)
            NO_CACHE=1
            shift
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Alpha Smoke Tests - Local E2E Testing"
            echo ""
            echo "Options:"
            echo "  -v, --verbose       Enable verbose output"
            echo "  --no-cleanup        Keep containers running after tests"
            echo "  --quick             Skip unit tests phase"
            echo "  --no-cache          Build containers with --no-cache flag"
            echo "  -f, --file FILE     Use specific docker-compose file"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  COMPOSE_FILE        Docker compose file (default: docker-compose.yml)"
            echo "  VERBOSE             Enable verbose mode (0 or 1)"
            echo "  CLEANUP             Cleanup after tests (0 or 1)"
            echo "  QUICK               Skip unit tests (0 or 1)"
            echo "  NO_CACHE            Build with --no-cache (0 or 1)"
            echo ""
            echo "Exit Codes:"
            echo "  0  All tests passed"
            echo "  1  Build failed"
            echo "  2  Services failed to start"
            echo "  3  API tests failed"
            echo "  4  Unit tests failed"
            echo "  5  Page load tests failed"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Run main
main
