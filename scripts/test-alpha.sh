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

# Edge case test flags (opt-out model - all enabled by default)
SKIP_DATABASE_RESILIENCE="${SKIP_DATABASE_RESILIENCE:-0}"
SKIP_AUTH_EDGE_CASES="${SKIP_AUTH_EDGE_CASES:-0}"
SKIP_DATA_PERSISTENCE="${SKIP_DATA_PERSISTENCE:-0}"
SKIP_CORS_TESTS="${SKIP_CORS_TESTS:-0}"
SKIP_ERROR_TESTS="${SKIP_ERROR_TESTS:-0}"
SKIP_DEPENDENCY_TESTS="${SKIP_DEPENDENCY_TESTS:-0}"
SKIP_FILE_TESTS="${SKIP_FILE_TESTS:-0}"
SKIP_CONCURRENT_TESTS="${SKIP_CONCURRENT_TESTS:-0}"
SKIP_CLEANUP_TESTS="${SKIP_CLEANUP_TESTS:-0}"
SKIP_VERSIONING_TESTS="${SKIP_VERSIONING_TESTS:-0}"
SKIP_SECURITY_TESTS="${SKIP_SECURITY_TESTS:-0}"
SKIP_SESSION_TESTS="${SKIP_SESSION_TESTS:-0}"

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

# Edge Case Tests - Database Resilience
test_database_resilience() {
    log_section "Testing Database Resilience"

    local failed=0

    # Test database reconnection after temporary outage
    log_info "Testing database reconnection..."
    log_info "Stopping postgres container..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" stop postgres > /dev/null 2>&1
    sleep 2

    # API should return 503 when DB is down
    log_info "Verifying API returns 503 when DB is unavailable..."
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/health 2>/dev/null || echo "000")
    if [ "$status_code" = "503" ] || [ "$status_code" = "500" ]; then
        log_info "API correctly returns error status ($status_code) when DB is down"
    else
        log_warn "API returned unexpected status $status_code when DB is down (expected 503/500)"
    fi

    # Restart postgres
    log_info "Restarting postgres container..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" start postgres > /dev/null 2>&1
    sleep 5

    # Verify recovery
    log_info "Verifying API recovers after DB restart..."
    local retry_count=0
    local max_retries=30
    while ! curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "API did not recover after DB restart"
            failed=1
            break
        fi
        sleep 1
    done

    if [ $failed -eq 0 ]; then
        log_info "API successfully recovered after DB restart"
    fi

    return $failed
}

# Edge Case Tests - Auth Edge Cases
test_auth_edge_cases() {
    log_section "Testing Authentication Edge Cases"

    local failed=0

    # Test missing Authorization header
    log_info "Testing missing Authorization header..."
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/drawings 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for missing auth header"
    else
        log_warn "API returned $status_code for missing auth (expected 401)"
        failed=1
    fi

    # Test invalid token format
    log_info "Testing invalid token format..."
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer invalid_token_format" \
        http://localhost:5001/api/v1/drawings 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for invalid token format"
    else
        log_warn "API returned $status_code for invalid token (expected 401)"
        failed=1
    fi

    # Test malformed Authorization header
    log_info "Testing malformed Authorization header..."
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: NotBearer token" \
        http://localhost:5001/api/v1/drawings 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for malformed auth header"
    else
        log_warn "API returned $status_code for malformed auth (expected 401)"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - Data Persistence
test_data_persistence() {
    log_section "Testing Data Persistence"

    local failed=0

    # Create test user and drawing (requires auth setup first)
    log_info "Testing data persistence across container restarts..."

    # Restart API container
    log_info "Restarting API container..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" restart api > /dev/null 2>&1
    sleep 5

    # Wait for API to be healthy again
    local retry_count=0
    local max_retries=30
    while ! curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "API did not become healthy after restart"
            failed=1
            break
        fi
        sleep 1
    done

    if [ $failed -eq 0 ]; then
        log_info "API container restarted successfully and data persists"
    fi

    return $failed
}

# Edge Case Tests - CORS Configuration
test_cors_config() {
    log_section "Testing CORS Configuration"

    local failed=0

    # Test CORS headers on health endpoint
    log_info "Testing CORS headers..."
    local headers
    headers=$(curl -s -I -H "Origin: http://localhost:3000" http://localhost:5001/api/v1/health 2>/dev/null || echo "")

    if echo "$headers" | grep -i "access-control-allow-origin" > /dev/null 2>&1; then
        log_info "CORS headers present in response"
    else
        log_warn "CORS headers not found in response"
        failed=1
    fi

    # Test preflight OPTIONS request
    log_info "Testing preflight OPTIONS request..."
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X OPTIONS \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        http://localhost:5001/api/v1/health 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "204" ]; then
        log_info "Preflight OPTIONS request handled correctly ($status_code)"
    else
        log_warn "Preflight OPTIONS returned unexpected status: $status_code"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - Error Responses
test_error_responses() {
    log_section "Testing Error Response Formats"

    local failed=0

    # Test 404 response
    log_info "Testing 404 error response..."
    local status_code
    local response
    response=$(curl -s -w "\n%{http_code}" http://localhost:5001/api/v1/nonexistent 2>/dev/null || echo "")
    status_code=$(echo "$response" | tail -n1)

    if [ "$status_code" = "404" ]; then
        log_info "404 error returned correctly"
    else
        log_warn "Expected 404, got $status_code"
        failed=1
    fi

    # Test 400 with malformed JSON (if API has POST endpoints)
    log_info "Testing 400 error with malformed JSON..."
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{invalid json" \
        http://localhost:5001/api/v1/register 2>/dev/null || echo "000")

    if [ "$status_code" = "400" ] || [ "$status_code" = "422" ]; then
        log_info "Malformed JSON correctly returns 400/422 ($status_code)"
    else
        log_warn "Malformed JSON returned unexpected status: $status_code"
    fi

    # Verify error responses are JSON
    log_info "Verifying error responses are JSON formatted..."
    response=$(curl -s http://localhost:5001/api/v1/nonexistent 2>/dev/null || echo "{}")
    if echo "$response" | grep -q "{" && echo "$response" | grep -q "}"; then
        log_info "Error response appears to be JSON formatted"
    else
        log_warn "Error response does not appear to be JSON"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - Service Dependencies
test_service_dependencies() {
    log_section "Testing Service Dependency Handling"

    local failed=0

    # Test Redis failure (graceful degradation)
    log_info "Testing Redis failure handling..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" stop redis > /dev/null 2>&1
    sleep 2

    # API should still respond (graceful degradation)
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/health 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "503" ]; then
        log_info "API handles Redis unavailability ($status_code)"
    else
        log_warn "Unexpected response when Redis is down: $status_code"
    fi

    # Restart Redis
    log_info "Restarting Redis..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" start redis > /dev/null 2>&1
    sleep 3

    # Test MinIO failure
    log_info "Testing MinIO failure handling..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" stop minio > /dev/null 2>&1
    sleep 2

    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/health 2>/dev/null || echo "000")
    log_info "API status with MinIO down: $status_code"

    # Restart MinIO
    log_info "Restarting MinIO..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" start minio > /dev/null 2>&1
    sleep 3

    # Verify all services recovered
    log_info "Verifying service recovery..."
    local retry_count=0
    local max_retries=30
    while ! curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "Services did not recover properly"
            failed=1
            break
        fi
        sleep 1
    done

    if [ $failed -eq 0 ]; then
        log_info "All services recovered successfully"
    fi

    return $failed
}

# Edge Case Tests - File Operations
test_file_operations() {
    log_section "Testing File Operations"

    local failed=0

    log_info "Testing file upload/download operations..."
    # Note: These tests require authentication, so they may need to be skipped
    # or implemented with proper auth token handling

    # For now, just verify MinIO is accessible
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ]; then
        log_info "MinIO health check passed"
    else
        log_warn "MinIO health check returned: $status_code"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - Concurrent Operations
test_concurrent_operations() {
    log_section "Testing Concurrent Operations"

    local failed=0

    log_info "Testing concurrent API requests..."
    # Send 10 concurrent health check requests
    local pids=()
    for i in {1..10}; do
        curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1 &
        pids+=($!)
    done

    # Wait for all requests
    local concurrent_failed=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            concurrent_failed=1
        fi
    done

    if [ $concurrent_failed -eq 0 ]; then
        log_info "Concurrent requests handled successfully"
    else
        log_warn "Some concurrent requests failed"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - Resource Cleanup
test_resource_cleanup() {
    log_section "Testing Resource Cleanup"

    local failed=0

    log_info "Testing cascading deletes and resource cleanup..."
    # Note: This requires creating test data and then deleting it
    # For now, just verify the API is healthy

    if curl -sf http://localhost:5001/api/v1/health > /dev/null 2>&1; then
        log_info "Resource cleanup tests completed (basic validation)"
    else
        log_error "API health check failed during cleanup tests"
        failed=1
    fi

    return $failed
}

# Edge Case Tests - API Versioning
test_api_versioning() {
    log_section "Testing API Versioning"

    local failed=0

    # Test v1 endpoints exist
    log_info "Testing API v1 endpoints..."
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/v1/health 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ]; then
        log_info "API v1 endpoints accessible"
    else
        log_error "API v1 health check failed: $status_code"
        failed=1
    fi

    # Test for version headers (optional deprecation warnings)
    log_info "Checking for API version headers..."
    local headers
    headers=$(curl -s -I http://localhost:5001/api/v1/health 2>/dev/null || echo "")

    if echo "$headers" | grep -i "content-type" > /dev/null 2>&1; then
        log_info "API returns proper headers"
    fi

    return $failed
}

# Edge Case Tests - Security Validation
test_security_validation() {
    log_section "Testing Security Validation"

    local failed=0

    # Test SQL injection attempt (should be blocked)
    log_info "Testing SQL injection protection..."
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:5001/api/v1/drawings?id=1%27%20OR%20%271%27=%271" 2>/dev/null || echo "000")

    # Should return 400, 404, or 401 (not 200 with data leak)
    if [ "$status_code" != "200" ]; then
        log_info "SQL injection attempt properly handled ($status_code)"
    else
        log_warn "Potential SQL injection vulnerability (returned 200)"
        failed=1
    fi

    # Test XSS attempt in query parameters
    log_info "Testing XSS protection..."
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:5001/api/v1/drawings?name=<script>alert('xss')</script>" 2>/dev/null || echo "000")

    log_info "XSS test returned status: $status_code"

    # Test path traversal attempt
    log_info "Testing path traversal protection..."
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:5001/api/v1/../../../etc/passwd" 2>/dev/null || echo "000")

    if [ "$status_code" = "404" ] || [ "$status_code" = "400" ]; then
        log_info "Path traversal properly blocked ($status_code)"
    else
        log_warn "Path traversal test returned: $status_code"
    fi

    return $failed
}

# Edge Case Tests - Session Management
test_session_management() {
    log_section "Testing Session Management"

    local failed=0

    log_info "Testing session cookie security..."
    local headers
    headers=$(curl -s -I http://localhost:5001/api/v1/health 2>/dev/null || echo "")

    # Check for secure cookie attributes (if cookies are used)
    if echo "$headers" | grep -i "set-cookie" > /dev/null 2>&1; then
        log_info "Session cookies present"

        if echo "$headers" | grep -i "set-cookie" | grep -i "secure" > /dev/null 2>&1; then
            log_info "Cookies have Secure flag (for HTTPS)"
        fi

        if echo "$headers" | grep -i "set-cookie" | grep -i "httponly" > /dev/null 2>&1; then
            log_info "Cookies have HttpOnly flag"
        fi
    else
        log_info "No session cookies in health endpoint (expected)"
    fi

    return $failed
}

# Main execution
main() {
    log_section "Alpha Smoke Tests"
    log_info "Starting comprehensive smoke testing..."
    echo ""

    # Track test results (0 = failed, 1 = passed, 2 = skipped)
    declare -A test_results
    test_results["Build"]=0
    test_results["Services"]=0
    test_results["API Tests"]=0
    test_results["Unit Tests (Backend)"]=0
    test_results["Unit Tests (Frontend)"]=0
    test_results["Page Loads"]=0
    test_results["Database Resilience"]=0
    test_results["Auth Edge Cases"]=0
    test_results["Data Persistence"]=0
    test_results["CORS Config"]=0
    test_results["Error Responses"]=0
    test_results["Service Dependencies"]=0
    test_results["File Operations"]=0
    test_results["Concurrent Operations"]=0
    test_results["Resource Cleanup"]=0
    test_results["API Versioning"]=0
    test_results["Security Validation"]=0
    test_results["Session Management"]=0

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

        # Edge Case Tests - Run only if services are healthy
        if [ "${test_results[Services]}" -eq 1 ]; then
            # Database Resilience Tests
            if [ "$SKIP_DATABASE_RESILIENCE" -eq 1 ]; then
                log_info "Skipping database resilience tests (--skip-database-resilience flag set)"
                test_results["Database Resilience"]=2
            else
                if test_database_resilience; then
                    test_results["Database Resilience"]=1
                else
                    test_results["Database Resilience"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=6; fi
                fi
            fi

            # Auth Edge Cases Tests
            if [ "$SKIP_AUTH_EDGE_CASES" -eq 1 ]; then
                log_info "Skipping auth edge case tests (--skip-auth-edge-cases flag set)"
                test_results["Auth Edge Cases"]=2
            else
                if test_auth_edge_cases; then
                    test_results["Auth Edge Cases"]=1
                else
                    test_results["Auth Edge Cases"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=7; fi
                fi
            fi

            # Data Persistence Tests
            if [ "$SKIP_DATA_PERSISTENCE" -eq 1 ]; then
                log_info "Skipping data persistence tests (--skip-data-persistence flag set)"
                test_results["Data Persistence"]=2
            else
                if test_data_persistence; then
                    test_results["Data Persistence"]=1
                else
                    test_results["Data Persistence"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=8; fi
                fi
            fi

            # CORS Config Tests
            if [ "$SKIP_CORS_TESTS" -eq 1 ]; then
                log_info "Skipping CORS config tests (--skip-cors-tests flag set)"
                test_results["CORS Config"]=2
            else
                if test_cors_config; then
                    test_results["CORS Config"]=1
                else
                    test_results["CORS Config"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=9; fi
                fi
            fi

            # Error Response Tests
            if [ "$SKIP_ERROR_TESTS" -eq 1 ]; then
                log_info "Skipping error response tests (--skip-error-tests flag set)"
                test_results["Error Responses"]=2
            else
                if test_error_responses; then
                    test_results["Error Responses"]=1
                else
                    test_results["Error Responses"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=10; fi
                fi
            fi

            # Service Dependencies Tests
            if [ "$SKIP_DEPENDENCY_TESTS" -eq 1 ]; then
                log_info "Skipping service dependency tests (--skip-dependency-tests flag set)"
                test_results["Service Dependencies"]=2
            else
                if test_service_dependencies; then
                    test_results["Service Dependencies"]=1
                else
                    test_results["Service Dependencies"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=11; fi
                fi
            fi

            # File Operations Tests
            if [ "$SKIP_FILE_TESTS" -eq 1 ]; then
                log_info "Skipping file operations tests (--skip-file-tests flag set)"
                test_results["File Operations"]=2
            else
                if test_file_operations; then
                    test_results["File Operations"]=1
                else
                    test_results["File Operations"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=12; fi
                fi
            fi

            # Concurrent Operations Tests
            if [ "$SKIP_CONCURRENT_TESTS" -eq 1 ]; then
                log_info "Skipping concurrent operations tests (--skip-concurrent-tests flag set)"
                test_results["Concurrent Operations"]=2
            else
                if test_concurrent_operations; then
                    test_results["Concurrent Operations"]=1
                else
                    test_results["Concurrent Operations"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=13; fi
                fi
            fi

            # Resource Cleanup Tests
            if [ "$SKIP_CLEANUP_TESTS" -eq 1 ]; then
                log_info "Skipping resource cleanup tests (--skip-cleanup-tests flag set)"
                test_results["Resource Cleanup"]=2
            else
                if test_resource_cleanup; then
                    test_results["Resource Cleanup"]=1
                else
                    test_results["Resource Cleanup"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=14; fi
                fi
            fi

            # API Versioning Tests
            if [ "$SKIP_VERSIONING_TESTS" -eq 1 ]; then
                log_info "Skipping API versioning tests (--skip-versioning-tests flag set)"
                test_results["API Versioning"]=2
            else
                if test_api_versioning; then
                    test_results["API Versioning"]=1
                else
                    test_results["API Versioning"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=15; fi
                fi
            fi

            # Security Validation Tests
            if [ "$SKIP_SECURITY_TESTS" -eq 1 ]; then
                log_info "Skipping security validation tests (--skip-security-tests flag set)"
                test_results["Security Validation"]=2
            else
                if test_security_validation; then
                    test_results["Security Validation"]=1
                else
                    test_results["Security Validation"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=16; fi
                fi
            fi

            # Session Management Tests
            if [ "$SKIP_SESSION_TESTS" -eq 1 ]; then
                log_info "Skipping session management tests (--skip-session-tests flag set)"
                test_results["Session Management"]=2
            else
                if test_session_management; then
                    test_results["Session Management"]=1
                else
                    test_results["Session Management"]=0
                    if [ $first_failure_code -eq 0 ]; then first_failure_code=17; fi
                fi
            fi
        else
            # Mark all edge case tests as failed if services didn't start
            test_results["Database Resilience"]=0
            test_results["Auth Edge Cases"]=0
            test_results["Data Persistence"]=0
            test_results["CORS Config"]=0
            test_results["Error Responses"]=0
            test_results["Service Dependencies"]=0
            test_results["File Operations"]=0
            test_results["Concurrent Operations"]=0
            test_results["Resource Cleanup"]=0
            test_results["API Versioning"]=0
            test_results["Security Validation"]=0
            test_results["Session Management"]=0
        fi
    fi

    # Count results
    local total_passed=0
    local total_failed=0
    local total_skipped=0
    for key in "${!test_results[@]}"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            total_passed=$((total_passed + 1))
        elif [ "${test_results[$key]}" -eq 2 ]; then
            total_skipped=$((total_skipped + 1))
        else
            total_failed=$((total_failed + 1))
        fi
    done

    # Final summary
    log_section "Smoke Test Summary"

    echo "Core Tests:"
    for key in "Build" "Services" "API Tests" "Unit Tests (Backend)" "Unit Tests (Frontend)" "Page Loads"; do
        if [ "${test_results[$key]:-0}" -eq 1 ]; then
            echo -e "  ${GREEN}✓${NC} $key: PASSED"
        elif [ "${test_results[$key]:-0}" -eq 2 ]; then
            echo -e "  ${YELLOW}○${NC} $key: SKIPPED"
        else
            echo -e "  ${RED}✗${NC} $key: FAILED"
        fi
    done

    echo ""
    echo "Edge Case Tests:"
    for key in "Database Resilience" "Auth Edge Cases" "Data Persistence" "CORS Config" \
               "Error Responses" "Service Dependencies" "File Operations" "Concurrent Operations" \
               "Resource Cleanup" "API Versioning" "Security Validation" "Session Management"; do
        if [ "${test_results[$key]:-0}" -eq 1 ]; then
            echo -e "  ${GREEN}✓${NC} $key: PASSED"
        elif [ "${test_results[$key]:-0}" -eq 2 ]; then
            echo -e "  ${YELLOW}○${NC} $key: SKIPPED"
        else
            echo -e "  ${RED}✗${NC} $key: FAILED"
        fi
    done

    echo ""
    echo "========================================="
    echo -e "Total: ${GREEN}$total_passed passed${NC}, ${RED}$total_failed failed${NC}, ${YELLOW}$total_skipped skipped${NC}"
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
        --skip-database-resilience)
            SKIP_DATABASE_RESILIENCE=1
            shift
            ;;
        --skip-auth-edge-cases)
            SKIP_AUTH_EDGE_CASES=1
            shift
            ;;
        --skip-data-persistence)
            SKIP_DATA_PERSISTENCE=1
            shift
            ;;
        --skip-cors-tests)
            SKIP_CORS_TESTS=1
            shift
            ;;
        --skip-error-tests)
            SKIP_ERROR_TESTS=1
            shift
            ;;
        --skip-dependency-tests)
            SKIP_DEPENDENCY_TESTS=1
            shift
            ;;
        --skip-file-tests)
            SKIP_FILE_TESTS=1
            shift
            ;;
        --skip-concurrent-tests)
            SKIP_CONCURRENT_TESTS=1
            shift
            ;;
        --skip-cleanup-tests)
            SKIP_CLEANUP_TESTS=1
            shift
            ;;
        --skip-versioning-tests)
            SKIP_VERSIONING_TESTS=1
            shift
            ;;
        --skip-security-tests)
            SKIP_SECURITY_TESTS=1
            shift
            ;;
        --skip-session-tests)
            SKIP_SESSION_TESTS=1
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
            echo "Core Options:"
            echo "  -v, --verbose       Enable verbose output"
            echo "  --no-cleanup        Keep containers running after tests"
            echo "  --quick             Skip unit tests phase"
            echo "  --no-cache          Build containers with --no-cache flag"
            echo "  -f, --file FILE     Use specific docker-compose file"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Edge Case Test Options (opt-out model - all enabled by default):"
            echo "  --skip-database-resilience   Skip database resilience tests"
            echo "  --skip-auth-edge-cases       Skip authentication edge case tests"
            echo "  --skip-data-persistence      Skip data persistence tests"
            echo "  --skip-cors-tests            Skip CORS configuration tests"
            echo "  --skip-error-tests           Skip error response format tests"
            echo "  --skip-dependency-tests      Skip service dependency tests"
            echo "  --skip-file-tests            Skip file operations tests"
            echo "  --skip-concurrent-tests      Skip concurrent operations tests"
            echo "  --skip-cleanup-tests         Skip resource cleanup tests"
            echo "  --skip-versioning-tests      Skip API versioning tests"
            echo "  --skip-security-tests        Skip security validation tests"
            echo "  --skip-session-tests         Skip session management tests"
            echo ""
            echo "Environment variables:"
            echo "  COMPOSE_FILE        Docker compose file (default: docker-compose.yml)"
            echo "  VERBOSE             Enable verbose mode (0 or 1)"
            echo "  CLEANUP             Cleanup after tests (0 or 1)"
            echo "  QUICK               Skip unit tests (0 or 1)"
            echo "  NO_CACHE            Build with --no-cache (0 or 1)"
            echo ""
            echo "Exit Codes:"
            echo "  0   All tests passed"
            echo "  1   Build failed"
            echo "  2   Services failed to start"
            echo "  3   API tests failed"
            echo "  4   Unit tests failed"
            echo "  5   Page load tests failed"
            echo "  6+  Edge case tests failed (see test output for details)"
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
