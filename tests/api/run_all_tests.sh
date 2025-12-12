#!/bin/bash

# Master API Test Runner
# Orchestrates docker-compose startup and runs all API tests

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
VERBOSE="${VERBOSE:-0}"
CLEANUP="${CLEANUP:-1}"

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

# Cleanup function
cleanup() {
    if [ "$CLEANUP" -eq 1 ]; then
        log_info "Cleaning up containers..."
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans 2>/dev/null || true
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

    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    log_info "docker-compose: $(docker-compose --version)"

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
    docker-compose -f "$COMPOSE_FILE" up -d --build

    log_info "Waiting for containers to be healthy..."
    max_wait=120
    elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        # Check if all services are running
        running=$(docker-compose -f "$COMPOSE_FILE" ps --filter "status=running" --services | wc -l)
        total=$(docker-compose -f "$COMPOSE_FILE" config --services | wc -l)

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
        docker-compose -f "$COMPOSE_FILE" ps
        exit 1
    fi

    # Show container status
    log_info "Container status:"
    docker-compose -f "$COMPOSE_FILE" ps
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
            docker-compose -f "$COMPOSE_FILE" logs --tail=50 api
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
            docker-compose -f "$COMPOSE_FILE" logs --tail=50 web
            exit 1
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    log_info "WebUI is healthy"

    log_info "All services are healthy and ready for testing"
}

# Run Flask API tests
run_flask_tests() {
    log_section "Running Flask API Tests"

    export API_HOST="http://localhost:5001"
    export VERBOSE="$VERBOSE"

    if [ -f "$(dirname "$0")/test_flask_api.sh" ]; then
        bash "$(dirname "$0")/test_flask_api.sh"
        flask_result=$?
    else
        log_error "Flask test script not found"
        return 1
    fi

    return $flask_result
}

# Run v0.2.0 API tests
run_v0_2_0_tests() {
    log_section "Running v0.2.0 API Tests"

    export API_HOST="http://localhost:5001"
    export VERBOSE="$VERBOSE"

    if [ -f "$(dirname "$0")/test_flask_api_v0.2.0.sh" ]; then
        bash "$(dirname "$0")/test_flask_api_v0.2.0.sh"
        v0_2_0_result=$?
    else
        log_error "v0.2.0 API test script not found"
        return 1
    fi

    return $v0_2_0_result
}

# Run WebUI tests
run_webui_tests() {
    log_section "Running WebUI Tests"

    export WEBUI_HOST="http://localhost:3000"
    export API_HOST="http://localhost:5001"
    export VERBOSE="$VERBOSE"

    if [ -f "$(dirname "$0")/test_webui.sh" ]; then
        bash "$(dirname "$0")/test_webui.sh"
        webui_result=$?
    else
        log_error "WebUI test script not found"
        return 1
    fi

    return $webui_result
}

# Show logs on failure
show_logs_on_failure() {
    log_section "Container Logs (Last 100 Lines)"

    log_info "=== Flask Backend Logs ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 api

    echo ""
    log_info "=== WebUI Logs ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 web

    echo ""
    log_info "=== PostgreSQL Logs ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 postgres

    echo ""
    log_info "=== Redis Logs ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=100 redis
}

# Main execution
main() {
    log_section "API Test Suite Runner"
    log_info "Starting comprehensive API testing..."
    echo ""

    # Track test results
    flask_tests_passed=0
    v0_2_0_tests_passed=0
    webui_tests_passed=0

    # Check prerequisites
    check_prerequisites

    # Start containers
    start_containers

    # Wait for services
    wait_for_services

    # Run Flask API tests
    if run_flask_tests; then
        flask_tests_passed=1
    else
        log_error "Flask API tests failed"
    fi

    # Run v0.2.0 API tests
    if run_v0_2_0_tests; then
        v0_2_0_tests_passed=1
    else
        log_error "v0.2.0 API tests failed"
    fi

    # Run WebUI tests
    if run_webui_tests; then
        webui_tests_passed=1
    else
        log_error "WebUI tests failed"
    fi

    # Show logs if any tests failed
    if [ $flask_tests_passed -eq 0 ] || [ $v0_2_0_tests_passed -eq 0 ] || [ $webui_tests_passed -eq 0 ]; then
        show_logs_on_failure
    fi

    # Final summary
    log_section "Final Test Summary"

    if [ $flask_tests_passed -eq 1 ]; then
        echo -e "${GREEN}✓${NC} Flask API Tests: PASSED"
    else
        echo -e "${RED}✗${NC} Flask API Tests: FAILED"
    fi

    if [ $v0_2_0_tests_passed -eq 1 ]; then
        echo -e "${GREEN}✓${NC} v0.2.0 API Tests: PASSED"
    else
        echo -e "${RED}✗${NC} v0.2.0 API Tests: FAILED"
    fi

    if [ $webui_tests_passed -eq 1 ]; then
        echo -e "${GREEN}✓${NC} WebUI Tests: PASSED"
    else
        echo -e "${RED}✗${NC} WebUI Tests: FAILED"
    fi

    echo ""

    # Exit with appropriate code
    if [ $flask_tests_passed -eq 1 ] && [ $v0_2_0_tests_passed -eq 1 ] && [ $webui_tests_passed -eq 1 ]; then
        log_info "All test suites passed!"
        exit 0
    else
        log_error "One or more test suites failed"
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
            echo "  -f, --file FILE     Use specific docker-compose file"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  COMPOSE_FILE        Docker compose file (default: docker-compose.yml)"
            echo "  VERBOSE             Enable verbose mode (0 or 1)"
            echo "  CLEANUP             Cleanup after tests (0 or 1)"
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
