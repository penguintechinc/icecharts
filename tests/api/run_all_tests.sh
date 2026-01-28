#!/bin/bash

# Master API Test Runner
# Orchestrates docker-compose startup and runs all API tests

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_ROOT/docker-compose.yml}"
VERBOSE="${VERBOSE:-0}"
CLEANUP="${CLEANUP:-1}"
SKIP_CONTAINERS="${SKIP_CONTAINERS:-0}"

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

# Cleanup function
cleanup() {
    if [ "$SKIP_CONTAINERS" -eq 1 ]; then
        log_warn "Skipping cleanup (--skip-containers mode)"
    elif [ "$CLEANUP" -eq 1 ]; then
        log_info "Cleaning up containers..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
        log_info "Cleanup complete"
    else
        log_warn "Skipping cleanup (CLEANUP=0)"
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
        exit 1
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
        exit 1
    fi
    log_info "Using compose file: $COMPOSE_FILE"
}

# Start containers
start_containers() {
    log_section "Starting Containers"

    log_info "Building and starting containers..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build

    log_info "Waiting for containers to be healthy..."
    max_wait=120
    elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        # Check if all services are running
        running=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps --filter "status=running" --services | wc -l)
        total=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" config --services | wc -l)

        if [ "$running" -eq "$total" ]; then
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
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
        exit 1
    fi

    # Show container status
    log_info "Container status:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
}

# Wait for services to be healthy
wait_for_services() {
    log_section "Waiting for Services Health Checks"

    # Wait for Flask backend
    log_info "Waiting for Flask backend..."
    max_retries=60
    retry_count=0
    while ! curl -s http://localhost:5001/api/v1/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "Flask backend did not become healthy in time"
            log_info "Flask backend logs:"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=50 api
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    log_info "Flask backend is healthy"

    # Wait for WebUI
    log_info "Waiting for WebUI..."
    retry_count=0
    while ! curl -s http://localhost:3000/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "WebUI did not become healthy in time"
            log_info "WebUI logs:"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=50 web
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    log_info "WebUI is healthy"

    log_info "All services are healthy and ready for testing"
}

# Generic test runner function
run_test_script() {
    local script_name="$1"
    local test_name="$2"

    log_section "Running $test_name"

    export API_HOST="http://localhost:5001"
    export WEBUI_HOST="http://localhost:3000"
    export VERBOSE="$VERBOSE"

    local script_path="$(dirname "$0")/$script_name"
    if [ -f "$script_path" ]; then
        bash "$script_path"
        return $?
    else
        log_error "$test_name script not found: $script_path"
        return 1
    fi
}

# Run Flask API tests
run_flask_tests() {
    run_test_script "test_flask_api.sh" "Flask API Tests"
}

# Run v0.2.0 API tests
run_v0_2_0_tests() {
    run_test_script "test_flask_api_v0.2.0.sh" "v0.2.0 API Tests"
}

# Run WebUI tests
run_webui_tests() {
    run_test_script "test_webui.sh" "WebUI Tests"
}

# Run Drawings API tests
run_drawings_tests() {
    run_test_script "test_drawings_api.sh" "Drawings API Tests"
}

# Run Groups API tests
run_groups_tests() {
    run_test_script "test_groups_api.sh" "Groups API Tests"
}

# Run Templates API tests
run_templates_tests() {
    run_test_script "test_templates_api.sh" "Templates API Tests"
}

# Run Libraries API tests
run_libraries_tests() {
    run_test_script "test_libraries_api.sh" "Libraries API Tests"
}

# Run Profile API tests
run_profile_tests() {
    run_test_script "test_profile_api.sh" "Profile API Tests"
}

# Run Comments & Shares API tests
run_comments_shares_tests() {
    run_test_script "test_comments_shares_api.sh" "Comments & Shares API Tests"
}

# Run Admin API tests
run_admin_tests() {
    run_test_script "test_admin_api.sh" "Admin API Tests"
}

# Run Service Accounts tests
run_service_accounts_tests() {
    run_test_script "test_service_accounts.sh" "Service Accounts Tests"
}

# Run Frontend Pages tests
run_frontend_tests() {
    run_test_script "test_frontend_pages.sh" "Frontend Pages Tests"
}

# Show logs on failure
show_logs_on_failure() {
    log_section "Container Logs (Last 100 Lines)"

    log_info "=== Flask Backend Logs ==="
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=100 api

    echo ""
    log_info "=== WebUI Logs ==="
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=100 web

    echo ""
    log_info "=== PostgreSQL Logs ==="
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=100 postgres

    echo ""
    log_info "=== Redis Logs ==="
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=100 redis
}

# Main execution
main() {
    log_section "API Test Suite Runner"
    log_info "Starting comprehensive API testing..."
    echo ""

    # Track test results (0 = failed, 1 = passed)
    declare -A test_results
    test_results["Flask API"]=0
    test_results["v0.2.0 API"]=0
    test_results["WebUI"]=0
    test_results["Drawings API"]=0
    test_results["Groups API"]=0
    test_results["Templates API"]=0
    test_results["Libraries API"]=0
    test_results["Profile API"]=0
    test_results["Comments & Shares API"]=0
    test_results["Admin API"]=0
    test_results["Service Accounts"]=0
    test_results["Frontend Pages"]=0

    # Check prerequisites
    check_prerequisites

    if [ "$SKIP_CONTAINERS" -eq 1 ]; then
        log_info "Skipping container startup (--skip-containers)"
        log_info "Verifying services are accessible..."
        # Just verify services are running
        if ! curl -s http://localhost:5001/api/v1/health > /dev/null 2>&1; then
            log_error "API is not accessible at http://localhost:5001"
            exit 1
        fi
        if ! curl -s http://localhost:3000/ > /dev/null 2>&1; then
            log_error "WebUI is not accessible at http://localhost:3000"
            exit 1
        fi
        log_info "Services are accessible"
    else
        # Start containers
        start_containers

        # Wait for services
        wait_for_services
    fi

    # Run all test suites
    log_section "Running Test Suites"

    # Core API tests
    if run_flask_tests; then
        test_results["Flask API"]=1
    else
        log_error "Flask API tests failed"
    fi

    if run_v0_2_0_tests; then
        test_results["v0.2.0 API"]=1
    else
        log_error "v0.2.0 API tests failed"
    fi

    # Feature API tests
    if run_drawings_tests; then
        test_results["Drawings API"]=1
    else
        log_error "Drawings API tests failed"
    fi

    if run_groups_tests; then
        test_results["Groups API"]=1
    else
        log_error "Groups API tests failed"
    fi

    if run_templates_tests; then
        test_results["Templates API"]=1
    else
        log_error "Templates API tests failed"
    fi

    if run_libraries_tests; then
        test_results["Libraries API"]=1
    else
        log_error "Libraries API tests failed"
    fi

    if run_profile_tests; then
        test_results["Profile API"]=1
    else
        log_error "Profile API tests failed"
    fi

    if run_comments_shares_tests; then
        test_results["Comments & Shares API"]=1
    else
        log_error "Comments & Shares API tests failed"
    fi

    # Admin & Service Account tests
    if run_admin_tests; then
        test_results["Admin API"]=1
    else
        log_error "Admin API tests failed"
    fi

    if run_service_accounts_tests; then
        test_results["Service Accounts"]=1
    else
        log_error "Service Accounts tests failed"
    fi

    # UI tests
    if run_webui_tests; then
        test_results["WebUI"]=1
    else
        log_error "WebUI tests failed"
    fi

    if run_frontend_tests; then
        test_results["Frontend Pages"]=1
    else
        log_error "Frontend Pages tests failed"
    fi

    # Count results
    total_passed=0
    total_failed=0
    for key in "${!test_results[@]}"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            total_passed=$((total_passed + 1))
        else
            total_failed=$((total_failed + 1))
        fi
    done

    # Show logs if any tests failed
    if [ $total_failed -gt 0 ]; then
        show_logs_on_failure
    fi

    # Final summary
    log_section "Final Test Summary"

    for key in "Flask API" "v0.2.0 API" "Drawings API" "Groups API" "Templates API" "Libraries API" "Profile API" "Comments & Shares API" "Admin API" "Service Accounts" "WebUI" "Frontend Pages"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            echo -e "${GREEN}✓${NC} $key Tests: PASSED"
        else
            echo -e "${RED}✗${NC} $key Tests: FAILED"
        fi
    done

    echo ""
    echo "========================================="
    echo -e "Total: ${GREEN}$total_passed passed${NC}, ${RED}$total_failed failed${NC}"
    echo "========================================="

    # Exit with appropriate code
    if [ $total_failed -eq 0 ]; then
        log_info "All test suites passed!"
        exit 0
    else
        log_error "$total_failed test suite(s) failed"
        exit 1
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
        --skip-containers)
            SKIP_CONTAINERS=1
            shift
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose       Enable verbose output"
            echo "  --no-cleanup        Don't cleanup containers after tests"
            echo "  --skip-containers   Skip container startup (use existing running containers)"
            echo "  -f, --file FILE     Use specific docker-compose file"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  COMPOSE_FILE        Docker compose file (default: docker-compose.yml)"
            echo "  VERBOSE             Enable verbose mode (0 or 1)"
            echo "  CLEANUP             Cleanup after tests (0 or 1)"
            echo "  SKIP_CONTAINERS     Skip container startup (0 or 1)"
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
