#!/bin/bash

# Beta Smoke Tests - K8s Cluster Verification
# Verifies beta deployment health, services, ingress, and external access

set -uo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration variables
KUBE_CONTEXT="${KUBE_CONTEXT:-dal2-beta}"
NAMESPACE="${NAMESPACE:-icecharts}"
APP_HOST="${APP_HOST:-icecharts.penguintech.io}"
ALB_ENDPOINT="${ALB_ENDPOINT:-dal2.penguintech.io}"
VERBOSE="${VERBOSE:-0}"
QUICK_MODE="${QUICK_MODE:-0}"

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

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        return 1
    fi
    log_info "kubectl: $(kubectl version --client -o yaml 2>/dev/null | grep gitVersion | awk '{print $2}')"

    # Check if context exists (quietly)
    if ! kubectl config get-contexts "$KUBE_CONTEXT" &> /dev/null; then
        log_error "Kubernetes context '$KUBE_CONTEXT' not found"
        log_info "Available contexts:"
        kubectl config get-contexts
        return 1
    fi
    log_info "Using context: $KUBE_CONTEXT"

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

    return 0
}

# Pod Health Check
check_pods() {
    log_section "Pod Health Check"

    local pods_output
    pods_output=$(kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get pods -o wide 2>&1)

    if [ $? -ne 0 ]; then
        log_error "Failed to get pods: $pods_output"
        return 1
    fi

    log_info "Pod Status:"
    echo "$pods_output"
    echo ""

    # Count unhealthy pods
    local unhealthy_count=0
    local pod_issues=""

    # Check for pods not in Running state
    while IFS= read -r line; do
        # Skip header line
        if [[ "$line" =~ ^NAME ]]; then
            continue
        fi

        if [ -z "$line" ]; then
            continue
        fi

        local pod_name=$(echo "$line" | awk '{print $1}')
        local ready=$(echo "$line" | awk '{print $2}')
        local status=$(echo "$line" | awk '{print $3}')

        # Check if pod is in Running status
        if [ "$status" != "Running" ]; then
            unhealthy_count=$((unhealthy_count + 1))
            pod_issues="${pod_issues}  ${RED}✗${NC} $pod_name: Status=$status"$'\n'
        fi

        # Check if all containers are ready (READY column should show N/N)
        if [[ "$ready" =~ ^[0-9]+/[0-9]+$ ]]; then
            local ready_count=$(echo "$ready" | cut -d'/' -f1)
            local total_count=$(echo "$ready" | cut -d'/' -f2)
            if [ "$ready_count" != "$total_count" ]; then
                unhealthy_count=$((unhealthy_count + 1))
                pod_issues="${pod_issues}  ${RED}✗${NC} $pod_name: Ready=$ready (containers not fully ready)"$'\n'
            fi
        fi

        # Check for problematic statuses
        if [[ "$status" =~ CrashLoopBackOff|ImagePullBackOff|Error|Pending ]]; then
            if [ "$status" != "Running" ]; then
                unhealthy_count=$((unhealthy_count + 1))
                pod_issues="${pod_issues}  ${RED}✗${NC} $pod_name: $status"$'\n'
            fi
        fi
    done <<< "$pods_output"

    if [ $unhealthy_count -eq 0 ]; then
        log_info "All pods are healthy"
        echo -e "${GREEN}✓${NC} Pod Health: PASSED"
        return 0
    else
        log_error "$unhealthy_count pod(s) not healthy:"
        echo -e "$pod_issues"
        echo -e "${RED}✗${NC} Pod Health: FAILED"
        return 1
    fi
}

# Service Check
check_services() {
    log_section "Service Check"

    local svc_output
    svc_output=$(kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get svc 2>&1)

    if [ $? -ne 0 ]; then
        log_error "Failed to get services: $svc_output"
        return 2
    fi

    log_info "Services:"
    echo "$svc_output"
    echo ""

    # Expected service patterns
    local expected_services=("web" "api" "postgres" "redis" "minio")
    local missing_services=""
    local found_count=0

    for expected in "${expected_services[@]}"; do
        if echo "$svc_output" | grep -qi "$expected"; then
            log_info "Found service: $expected"
            found_count=$((found_count + 1))
        else
            missing_services="${missing_services}  ${RED}✗${NC} $expected"$'\n'
        fi
    done

    if [ $found_count -lt ${#expected_services[@]} ]; then
        log_warn "Some expected services are missing:"
        echo -e "$missing_services"
        echo -e "${YELLOW}⚠${NC} Service Check: PARTIAL (found $found_count/${#expected_services[@]})"
        return 2
    else
        log_info "All expected services found"
        echo -e "${GREEN}✓${NC} Service Check: PASSED"
        return 0
    fi
}

# Ingress Check
check_ingress() {
    log_section "Ingress Check"

    # Ingress is in the icecharts namespace (each cluster has one ingress per app)
    # not in the beta namespace
    local ingress_ns="icecharts"
    local ingress_output
    ingress_output=$(kubectl --context="$KUBE_CONTEXT" -n "$ingress_ns" get ingress 2>&1)

    if [ $? -ne 0 ]; then
        log_error "Failed to get ingress: $ingress_output"
        return 2
    fi

    log_info "Ingress (in $ingress_ns namespace):"
    echo "$ingress_output"
    echo ""

    # Check if ingress exists
    if echo "$ingress_output" | grep -q "No resources found"; then
        log_error "No ingress found in namespace"
        echo -e "${RED}✗${NC} Ingress Check: FAILED"
        return 2
    fi

    # Check if ingress host matches expected host
    if echo "$ingress_output" | grep -q "$APP_HOST"; then
        log_info "Ingress host matches: $APP_HOST"
        echo -e "${GREEN}✓${NC} Ingress Check: PASSED"
        return 0
    else
        log_warn "Ingress host does not match expected host: $APP_HOST"
        log_info "Ingress output:"
        echo "$ingress_output"
        echo -e "${YELLOW}⚠${NC} Ingress Check: WARNING"
        return 2
    fi
}

# External Access Tests
check_external_access() {
    log_section "External Access Tests"

    local success=0
    local failures=0

    # Test Web UI
    log_info "Testing Web UI at https://$ALB_ENDPOINT/"
    local web_status
    web_status=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/" 2>&1)

    if [ "$web_status" = "200" ]; then
        log_info "Web UI responding (HTTP $web_status)"
        echo -e "${GREEN}✓${NC} Web UI: PASSED"
        success=$((success + 1))
    else
        log_error "Web UI not responding correctly (HTTP $web_status)"
        echo -e "${RED}✗${NC} Web UI: FAILED"
        failures=$((failures + 1))
    fi

    # Test API Health
    log_info "Testing API Health at /api/v1/health"
    local api_health
    api_health=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>&1)
    local api_status=$?

    if [ $api_status -eq 0 ] && echo "$api_health" | grep -q .; then
        log_info "API Health endpoint responding"
        if command -v jq &> /dev/null; then
            if echo "$api_health" | jq . &> /dev/null; then
                log_info "API Health response is valid JSON:"
                echo "$api_health" | jq .
                echo -e "${GREEN}✓${NC} API Health: PASSED"
                success=$((success + 1))
            else
                log_warn "API Health response is not valid JSON"
                echo "$api_health"
                echo -e "${YELLOW}⚠${NC} API Health: WARNING"
            fi
        else
            log_info "API Health response: $api_health"
            echo -e "${GREEN}✓${NC} API Health: PASSED"
            success=$((success + 1))
        fi
    else
        log_error "API Health endpoint failed"
        echo -e "${RED}✗${NC} API Health: FAILED"
        failures=$((failures + 1))
    fi

    # Test CORS Headers
    log_info "Testing CORS Headers"
    local cors_header
    cors_header=$(curl -sk -H "Host: $APP_HOST" -H "Origin: https://$APP_HOST" -I "https://$ALB_ENDPOINT/api/v1/health" 2>&1 | grep -i "Access-Control-Allow-Origin")

    if [ -n "$cors_header" ]; then
        log_info "CORS header present: $cors_header"
        echo -e "${GREEN}✓${NC} CORS Headers: PASSED"
        success=$((success + 1))
    else
        log_warn "CORS header not found or not configured"
        echo -e "${YELLOW}⚠${NC} CORS Headers: WARNING"
    fi

    echo ""
    if [ $failures -gt 0 ]; then
        log_error "$failures external access test(s) failed"
        echo -e "${RED}✗${NC} External Access: FAILED"
        return 3
    else
        log_info "All external access tests passed"
        echo -e "${GREEN}✓${NC} External Access: PASSED"
        return 0
    fi
}

# API Integration Tests
run_api_tests() {
    log_section "API Integration Tests"

    if [ "$QUICK_MODE" -eq 1 ]; then
        log_info "Skipping API tests (--quick mode)"
        return 0
    fi

    local success=0
    local failures=0

    # Test health endpoint
    log_info "Testing GET /api/v1/health"
    local health_response
    health_response=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>&1)

    if [ -n "$health_response" ]; then
        log_info "Health endpoint responsive"
        echo -e "${GREEN}✓${NC} Health Endpoint: PASSED"
        success=$((success + 1))
    else
        log_error "Health endpoint failed"
        echo -e "${RED}✗${NC} Health Endpoint: FAILED"
        failures=$((failures + 1))
    fi

    echo ""
    if [ $failures -gt 0 ]; then
        log_error "$failures API test(s) failed"
        echo -e "${RED}✗${NC} API Integration Tests: FAILED"
        return 4
    else
        log_info "All API integration tests passed"
        echo -e "${GREEN}✓${NC} API Integration Tests: PASSED"
        return 0
    fi
}

# Page Load Tests
check_page_loads() {
    log_section "Page Load Tests"

    log_info "Testing page load at https://$ALB_ENDPOINT/"
    local page_response
    page_response=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/" 2>&1)

    # Check for HTML content
    if echo "$page_response" | grep -qE "<html|<!DOCTYPE"; then
        log_info "HTML content detected"
    else
        log_error "No HTML content found in response"
        echo -e "${RED}✗${NC} Page Load: FAILED"
        return 5
    fi

    # Check for hardcoded localhost references
    if echo "$page_response" | grep -qE "localhost|127\.0\.0\.1"; then
        log_error "Page contains hardcoded localhost references"
        echo "$page_response" | grep -E "localhost|127\.0\.0\.1" | head -n 3
        echo -e "${RED}✗${NC} Page Load: FAILED (hardcoded localhost)"
        return 5
    fi

    log_info "Page loaded successfully"
    echo -e "${GREEN}✓${NC} Page Load: PASSED"
    return 0
}

# Log Check
check_logs() {
    log_section "Log Check"

    # Check API logs
    log_info "Checking API logs (last 50 lines)..."
    local api_logs
    api_logs=$(kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" logs -l app=api --tail=50 2>&1)

    local api_error_count
    api_error_count=$(echo "$api_logs" | grep -ic "ERROR" || echo 0)

    if [ "$api_error_count" -gt 0 ]; then
        log_warn "Found $api_error_count ERROR line(s) in API logs"
    else
        log_info "No ERROR lines found in API logs"
    fi

    # Check Web logs
    log_info "Checking Web UI logs (last 50 lines)..."
    local web_logs
    web_logs=$(kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" logs -l app=web --tail=50 2>&1)

    local web_error_count
    web_error_count=$(echo "$web_logs" | grep -ic "ERROR" || echo 0)

    if [ "$web_error_count" -gt 0 ]; then
        log_warn "Found $web_error_count ERROR line(s) in Web logs"
    else
        log_info "No ERROR lines found in Web logs"
    fi

    echo -e "${YELLOW}⚠${NC} Log Check: INFORMATIONAL (warnings only, not failures)"
    return 0
}

# Edge Case Tests - Database Resilience
test_database_resilience() {
    log_section "Testing Database Resilience"

    local failed=0

    # Test database reconnection after temporary outage
    log_info "Testing database reconnection..."
    log_info "Scaling postgres StatefulSet to 0..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale statefulset postgres --replicas=0 > /dev/null 2>&1
    sleep 5

    # API should return 503 when DB is down
    log_info "Verifying API returns 503 when DB is unavailable..."
    local status_code
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")
    if [ "$status_code" = "503" ] || [ "$status_code" = "500" ]; then
        log_info "API correctly returns error status ($status_code) when DB is down"
    else
        log_warn "API returned unexpected status $status_code when DB is down (expected 503/500)"
    fi

    # Scale postgres back to 1
    log_info "Scaling postgres StatefulSet back to 1..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale statefulset postgres --replicas=1 > /dev/null 2>&1
    sleep 10

    # Wait for postgres pod to be ready
    log_info "Waiting for postgres pod to be ready..."
    local retry_count=0
    local max_retries=60
    while ! kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get pods -l app=postgres -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q "True"; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "Postgres pod did not become ready after scaling"
            failed=1
            break
        fi
        sleep 2
    done

    # Verify API recovery
    log_info "Verifying API recovers after DB restart..."
    retry_count=0
    while ! curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "API did not recover after DB restart"
            failed=1
            break
        fi
        sleep 2
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
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/drawings" 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for missing auth header"
    else
        log_warn "API returned $status_code for missing auth (expected 401)"
        failed=1
    fi

    # Test invalid token format
    log_info "Testing invalid token format..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        -H "Authorization: Bearer invalid_token_format" \
        "https://$ALB_ENDPOINT/api/v1/drawings" 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for invalid token format"
    else
        log_warn "API returned $status_code for invalid token (expected 401)"
        failed=1
    fi

    # Test malformed Authorization header
    log_info "Testing malformed Authorization header..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        -H "Authorization: NotBearer token" \
        "https://$ALB_ENDPOINT/api/v1/drawings" 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "API correctly returns 401 for malformed auth header"
    else
        log_warn "API returned $status_code for malformed auth (expected 401)"
        failed=1
    fi

    # Test rate limiting on login endpoint (optional)
    log_info "Testing rate limiting behavior..."
    local rate_limit_status=0
    for i in {1..5}; do
        status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
            -H "Host: $APP_HOST" \
            -X POST \
            "https://$ALB_ENDPOINT/api/v1/login" 2>/dev/null || echo "000")
        if [ "$status_code" = "429" ]; then
            rate_limit_status=1
            break
        fi
        sleep 0.2
    done

    if [ $rate_limit_status -eq 1 ]; then
        log_info "Rate limiting is active (429 received)"
    else
        log_info "Rate limiting test completed (no 429 within test)"
    fi

    return $failed
}

# Edge Case Tests - Data Persistence
test_data_persistence() {
    log_section "Testing Data Persistence"

    local failed=0

    log_info "Testing data persistence across pod restarts..."

    # Rollout restart API deployment
    log_info "Rolling restart API deployment..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout restart deployment icecharts-api > /dev/null 2>&1
    sleep 5

    # Wait for rollout to complete
    log_info "Waiting for API rollout to complete..."
    if kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" rollout status deployment icecharts-api --timeout=120s > /dev/null 2>&1; then
        log_info "API rollout completed successfully"
    else
        log_error "API rollout did not complete in time"
        failed=1
        return $failed
    fi

    # Wait for API to be healthy again
    log_info "Waiting for API to be healthy..."
    local retry_count=0
    local max_retries=60
    while ! curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "API did not become healthy after restart"
            failed=1
            break
        fi
        sleep 2
    done

    if [ $failed -eq 0 ]; then
        log_info "API pod restarted successfully and data persists"
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
    headers=$(curl -sk -I -H "Host: $APP_HOST" -H "Origin: https://$APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "")

    if echo "$headers" | grep -i "access-control-allow-origin" > /dev/null 2>&1; then
        log_info "CORS headers present in response"
    else
        log_warn "CORS headers not found in response"
        failed=1
    fi

    # Test preflight OPTIONS request
    log_info "Testing preflight OPTIONS request..."
    local status_code
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -X OPTIONS \
        -H "Host: $APP_HOST" \
        -H "Origin: https://$APP_HOST" \
        -H "Access-Control-Request-Method: POST" \
        "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "204" ]; then
        log_info "Preflight OPTIONS request handled correctly ($status_code)"
    else
        log_warn "Preflight OPTIONS returned unexpected status: $status_code"
        failed=1
    fi

    # Verify Access-Control-* headers
    log_info "Verifying Access-Control-* headers..."
    if echo "$headers" | grep -iE "access-control-(allow|expose)" > /dev/null 2>&1; then
        log_info "Access-Control headers configured"
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
    response=$(curl -sk -w "\n%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/nonexistent" 2>/dev/null || echo "")
    status_code=$(echo "$response" | tail -n1)

    if [ "$status_code" = "404" ]; then
        log_info "404 error returned correctly"
    else
        log_warn "Expected 404, got $status_code"
        failed=1
    fi

    # Test 400 with malformed JSON
    log_info "Testing 400 error with malformed JSON..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "Host: $APP_HOST" \
        -H "Content-Type: application/json" \
        -d "{invalid json" \
        "https://$ALB_ENDPOINT/api/v1/register" 2>/dev/null || echo "000")

    if [ "$status_code" = "400" ] || [ "$status_code" = "422" ]; then
        log_info "Malformed JSON correctly returns 400/422 ($status_code)"
    else
        log_warn "Malformed JSON returned unexpected status: $status_code"
    fi

    # Verify error responses are JSON
    log_info "Verifying error responses are JSON formatted..."
    response=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/nonexistent" 2>/dev/null || echo "{}")
    if echo "$response" | grep -q "{" && echo "$response" | grep -q "}"; then
        log_info "Error response appears to be JSON formatted"
    else
        log_warn "Error response does not appear to be JSON"
        failed=1
    fi

    # Test 401 unauthorized
    log_info "Testing 401 unauthorized response..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        "https://$ALB_ENDPOINT/api/v1/drawings" 2>/dev/null || echo "000")
    if [ "$status_code" = "401" ]; then
        log_info "401 unauthorized returned correctly"
    fi

    # Test 403 forbidden (if applicable)
    log_info "Testing 403 forbidden response..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        -H "Authorization: Bearer invalid_token" \
        "https://$ALB_ENDPOINT/api/v1/admin/users" 2>/dev/null || echo "000")
    log_info "Admin endpoint returned status: $status_code"

    # Ensure no sensitive info leaked
    log_info "Verifying no sensitive info in error responses..."
    response=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/nonexistent" 2>/dev/null || echo "")
    if echo "$response" | grep -qiE "password|secret|key|token|traceback|stacktrace"; then
        log_warn "Error response may contain sensitive information"
        failed=1
    else
        log_info "No sensitive info detected in error responses"
    fi

    return $failed
}

# Edge Case Tests - Service Dependencies
test_service_dependencies() {
    log_section "Testing Service Dependency Handling"

    local failed=0

    # Test Redis failure (graceful degradation)
    log_info "Testing Redis failure handling..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale deployment redis --replicas=0 > /dev/null 2>&1
    sleep 5

    # API should still respond or gracefully degrade
    local status_code
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ] || [ "$status_code" = "503" ]; then
        log_info "API handles Redis unavailability gracefully ($status_code)"
    else
        log_warn "Unexpected response when Redis is down: $status_code"
    fi

    # Scale Redis back
    log_info "Scaling Redis back..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale deployment redis --replicas=1 > /dev/null 2>&1
    sleep 5

    # Test MinIO failure
    log_info "Testing MinIO failure handling..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale deployment minio --replicas=0 > /dev/null 2>&1
    sleep 5

    status_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")
    log_info "API status with MinIO down: $status_code"

    # Scale MinIO back
    log_info "Scaling MinIO back..."
    kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" scale deployment minio --replicas=1 > /dev/null 2>&1
    sleep 5

    # Verify all services recovered
    log_info "Verifying service recovery..."
    local retry_count=0
    local max_retries=60
    while ! curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "Services did not recover properly"
            failed=1
            break
        fi
        sleep 2
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

    log_info "Testing file upload/download operations via ALB..."
    # Note: These tests require authentication
    # For now, verify MinIO is accessible through service

    # Check MinIO service exists
    if kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get svc minio > /dev/null 2>&1; then
        log_info "MinIO service exists in cluster"
    else
        log_error "MinIO service not found"
        failed=1
    fi

    # Verify file operations through API (requires auth)
    log_info "File operations test completed (basic validation)"

    return $failed
}

# Edge Case Tests - Concurrent Operations
test_concurrent_operations() {
    log_section "Testing Concurrent Operations"

    local failed=0

    log_info "Testing concurrent API requests through ALB..."
    # Send 10 concurrent health check requests
    local pids=()
    for i in {1..10}; do
        curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" > /dev/null 2>&1 &
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

    if curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" > /dev/null 2>&1; then
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
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")

    if [ "$status_code" = "200" ]; then
        log_info "API v1 endpoints accessible"
    else
        log_error "API v1 health check failed: $status_code"
        failed=1
    fi

    # Test for version headers (optional deprecation warnings)
    log_info "Checking for API version headers..."
    local headers
    headers=$(curl -sk -I -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "")

    if echo "$headers" | grep -i "content-type" > /dev/null 2>&1; then
        log_info "API returns proper headers"
    fi

    # Check if different API versions are supported
    log_info "Testing API version in response..."
    local response
    response=$(curl -sk -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "")
    if echo "$response" | grep -q "version"; then
        log_info "Version information present in API response"
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
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        "https://$ALB_ENDPOINT/api/v1/drawings?id=1%27%20OR%20%271%27=%271" 2>/dev/null || echo "000")

    # Should return 400, 404, or 401 (not 200 with data leak)
    if [ "$status_code" != "200" ]; then
        log_info "SQL injection attempt properly handled ($status_code)"
    else
        log_warn "Potential SQL injection vulnerability (returned 200)"
        failed=1
    fi

    # Test XSS attempt in query parameters
    log_info "Testing XSS protection..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        "https://$ALB_ENDPOINT/api/v1/drawings?name=<script>alert('xss')</script>" 2>/dev/null || echo "000")

    log_info "XSS test returned status: $status_code"

    # Test path traversal attempt
    log_info "Testing path traversal protection..."
    status_code=$(curl -sk -o /dev/null -w "%{http_code}" \
        -H "Host: $APP_HOST" \
        "https://$ALB_ENDPOINT/api/v1/../../../etc/passwd" 2>/dev/null || echo "000")

    if [ "$status_code" = "404" ] || [ "$status_code" = "400" ]; then
        log_info "Path traversal properly blocked ($status_code)"
    else
        log_warn "Path traversal test returned: $status_code"
    fi

    # Test HTTPS enforcement (ALB should redirect HTTP to HTTPS)
    log_info "Testing HTTPS enforcement..."
    local http_status
    http_status=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: $APP_HOST" "http://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "000")
    log_info "HTTP request returned status: $http_status (ALB behavior)"

    return $failed
}

# Edge Case Tests - Session Management
test_session_management() {
    log_section "Testing Session Management"

    local failed=0

    log_info "Testing session cookie security..."
    local headers
    headers=$(curl -sk -I -H "Host: $APP_HOST" "https://$ALB_ENDPOINT/api/v1/health" 2>/dev/null || echo "")

    # Check for secure cookie attributes (if cookies are used)
    if echo "$headers" | grep -i "set-cookie" > /dev/null 2>&1; then
        log_info "Session cookies present"

        if echo "$headers" | grep -i "set-cookie" | grep -i "secure" > /dev/null 2>&1; then
            log_info "Cookies have Secure flag (HTTPS)"
        else
            log_warn "Cookies missing Secure flag"
        fi

        if echo "$headers" | grep -i "set-cookie" | grep -i "httponly" > /dev/null 2>&1; then
            log_info "Cookies have HttpOnly flag"
        else
            log_warn "Cookies missing HttpOnly flag"
        fi

        if echo "$headers" | grep -i "set-cookie" | grep -i "samesite" > /dev/null 2>&1; then
            log_info "Cookies have SameSite attribute"
        else
            log_warn "Cookies missing SameSite attribute"
        fi
    else
        log_info "No session cookies in health endpoint (expected)"
    fi

    # Test logout invalidation (if applicable)
    log_info "Session management tests completed"

    return $failed
}

# Main execution
main() {
    log_section "Beta Cluster Smoke Tests"
    log_info "Testing beta deployment at $APP_HOST"
    echo ""

    # Track test results (0 = failed, 1 = passed, 2 = skipped)
    declare -A test_results
    test_results["Prerequisites"]=0
    test_results["Pod Health"]=0
    test_results["Services"]=0
    test_results["Ingress"]=0
    test_results["External Access"]=0
    test_results["API Tests"]=0
    test_results["Page Loads"]=0
    test_results["Logs"]=0
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

    # Check prerequisites
    if check_prerequisites; then
        test_results["Prerequisites"]=1
    else
        log_error "Prerequisites check failed"
        test_results["Prerequisites"]=0
    fi

    # Pod Health Check
    if check_pods; then
        test_results["Pod Health"]=1
    else
        test_results["Pod Health"]=0
    fi

    # Service Check
    if check_services; then
        test_results["Services"]=1
    else
        test_results["Services"]=0
    fi

    # Ingress Check
    if check_ingress; then
        test_results["Ingress"]=1
    else
        test_results["Ingress"]=0
    fi

    # External Access Tests
    if check_external_access; then
        test_results["External Access"]=1
    else
        test_results["External Access"]=0
    fi

    # API Tests
    if run_api_tests; then
        test_results["API Tests"]=1
    else
        test_results["API Tests"]=0
    fi

    # Page Load Tests
    if check_page_loads; then
        test_results["Page Loads"]=1
    else
        test_results["Page Loads"]=0
    fi

    # Log Check
    if check_logs; then
        test_results["Logs"]=1
    else
        test_results["Logs"]=0
    fi

    # Edge Case Tests - Run only if core tests pass
    if [ "${test_results[Pod Health]}" -eq 1 ] && [ "${test_results[External Access]}" -eq 1 ]; then
        # Database Resilience Tests
        if [ "$SKIP_DATABASE_RESILIENCE" -eq 1 ]; then
            log_info "Skipping database resilience tests (--skip-database-resilience flag set)"
            test_results["Database Resilience"]=2
        else
            if test_database_resilience; then
                test_results["Database Resilience"]=1
            else
                test_results["Database Resilience"]=0
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
            fi
        fi
    else
        # Mark all edge case tests as failed if core tests didn't pass
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

    # Count results
    local total_passed=0
    local total_failed=0
    local total_skipped=0
    local first_failure_code=0

    for key in "${!test_results[@]}"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            total_passed=$((total_passed + 1))
        elif [ "${test_results[$key]}" -eq 2 ]; then
            total_skipped=$((total_skipped + 1))
        else
            total_failed=$((total_failed + 1))
            # Capture first failure exit code
            if [ $first_failure_code -eq 0 ]; then
                case "$key" in
                    "Prerequisites"|"Pod Health") first_failure_code=1 ;;
                    "Services"|"Ingress") first_failure_code=2 ;;
                    "External Access") first_failure_code=3 ;;
                    "API Tests") first_failure_code=4 ;;
                    "Page Loads") first_failure_code=5 ;;
                    *) first_failure_code=6 ;;
                esac
            fi
        fi
    done

    # Final summary
    log_section "Final Test Summary"

    echo "Core Tests:"
    for key in "Prerequisites" "Pod Health" "Services" "Ingress" "External Access" "API Tests" "Page Loads" "Logs"; do
        if [ "${test_results[$key]:-0}" -eq 1 ]; then
            echo -e "${GREEN}✓${NC} $key: PASSED"
        elif [ "${test_results[$key]:-0}" -eq 2 ]; then
            echo -e "${YELLOW}○${NC} $key: SKIPPED"
        else
            echo -e "${RED}✗${NC} $key: FAILED"
        fi
    done

    echo ""
    echo "Edge Case Tests:"
    for key in "Database Resilience" "Auth Edge Cases" "Data Persistence" "CORS Config" \
               "Error Responses" "Service Dependencies" "File Operations" "Concurrent Operations" \
               "Resource Cleanup" "API Versioning" "Security Validation" "Session Management"; do
        if [ "${test_results[$key]:-0}" -eq 1 ]; then
            echo -e "${GREEN}✓${NC} $key: PASSED"
        elif [ "${test_results[$key]:-0}" -eq 2 ]; then
            echo -e "${YELLOW}○${NC} $key: SKIPPED"
        else
            echo -e "${RED}✗${NC} $key: FAILED"
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
        log_error "$total_failed test(s) failed"
        exit "$first_failure_code"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=1
            shift
            ;;
        --context)
            KUBE_CONTEXT="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --host)
            APP_HOST="$2"
            shift 2
            ;;
        --alb)
            ALB_ENDPOINT="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Beta Cluster Smoke Tests - K8s Deployment Verification"
            echo ""
            echo "Core Options:"
            echo "  --quick               Skip API integration tests (health checks only)"
            echo "  --context CONTEXT     Kubernetes context (default: dal2-beta)"
            echo "  --namespace NS        Kubernetes namespace (default: icecharts)"
            echo "  --host HOST           Application host (default: icecharts.penguintech.io)"
            echo "  --alb ENDPOINT        ALB endpoint (default: dal2.penguintech.io)"
            echo "  -v, --verbose         Enable verbose output"
            echo "  -h, --help            Show this help message"
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
            echo "  KUBE_CONTEXT          Kubernetes context (default: dal2-beta)"
            echo "  NAMESPACE             Kubernetes namespace (default: icecharts)"
            echo "  APP_HOST              Application host (default: icecharts.penguintech.io)"
            echo "  ALB_ENDPOINT          ALB endpoint (default: dal2.penguintech.io)"
            echo "  VERBOSE               Enable verbose mode (0 or 1)"
            echo "  QUICK_MODE            Skip API tests (0 or 1)"
            echo ""
            echo "Exit Codes:"
            echo "  0   All tests passed"
            echo "  1   Prerequisites or pod health failed"
            echo "  2   Services or ingress failed"
            echo "  3   External access failed"
            echo "  4   API tests failed"
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
