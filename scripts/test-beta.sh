#!/bin/bash

# Beta Smoke Tests - K8s Cluster Verification
# Verifies beta deployment health, services, ingress, and external access

set -uo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration variables
KUBE_CONTEXT="${KUBE_CONTEXT:-dal2-beta}"
NAMESPACE="${NAMESPACE:-icecharts-beta}"
APP_HOST="${APP_HOST:-icecharts.penguintech.io}"
ALB_ENDPOINT="${ALB_ENDPOINT:-dal2.penguintech.io}"
VERBOSE="${VERBOSE:-0}"
QUICK_MODE="${QUICK_MODE:-0}"

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
    log_info "kubectl: $(kubectl version --client --short 2>/dev/null | head -n 1)"

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

    local ingress_output
    ingress_output=$(kubectl --context="$KUBE_CONTEXT" -n "$NAMESPACE" get ingress 2>&1)

    if [ $? -ne 0 ]; then
        log_error "Failed to get ingress: $ingress_output"
        return 2
    fi

    log_info "Ingress:"
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

# Main execution
main() {
    log_section "Beta Cluster Smoke Tests"
    log_info "Testing beta deployment at $APP_HOST"
    echo ""

    # Track test results (0 = failed, 1 = passed)
    declare -A test_results
    test_results["Prerequisites"]=0
    test_results["Pod Health"]=0
    test_results["Services"]=0
    test_results["Ingress"]=0
    test_results["External Access"]=0
    test_results["API Tests"]=0
    test_results["Page Loads"]=0
    test_results["Logs"]=0

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

    # Count results
    local total_passed=0
    local total_failed=0
    local first_failure_code=0

    for key in "Prerequisites" "Pod Health" "Services" "Ingress" "External Access" "API Tests" "Page Loads" "Logs"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
            total_passed=$((total_passed + 1))
        else
            total_failed=$((total_failed + 1))
            # Capture first failure exit code for final exit
            if [ $first_failure_code -eq 0 ]; then
                case "$key" in
                    "Prerequisites") first_failure_code=1 ;;
                    "Pod Health") first_failure_code=1 ;;
                    "Services"|"Ingress") first_failure_code=2 ;;
                    "External Access") first_failure_code=3 ;;
                    "API Tests") first_failure_code=4 ;;
                    "Page Loads") first_failure_code=5 ;;
                    *) first_failure_code=1 ;;
                esac
            fi
        fi
    done

    # Final summary
    log_section "Final Test Summary"

    for key in "Prerequisites" "Pod Health" "Services" "Ingress" "External Access" "API Tests" "Page Loads" "Logs"; do
        if [ "${test_results[$key]}" -eq 1 ]; then
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
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick               Skip API integration tests (health checks only)"
            echo "  --context CONTEXT     Kubernetes context (default: dal2-beta)"
            echo "  --namespace NS        Kubernetes namespace (default: icecharts-beta)"
            echo "  --host HOST           Application host (default: icecharts.penguintech.io)"
            echo "  --alb ENDPOINT        ALB endpoint (default: dal2.penguintech.io)"
            echo "  -v, --verbose         Enable verbose output"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  KUBE_CONTEXT          Kubernetes context (default: dal2-beta)"
            echo "  NAMESPACE             Kubernetes namespace (default: icecharts-beta)"
            echo "  APP_HOST              Application host (default: icecharts.penguintech.io)"
            echo "  ALB_ENDPOINT          ALB endpoint (default: dal2.penguintech.io)"
            echo "  VERBOSE               Enable verbose mode (0 or 1)"
            echo "  QUICK_MODE            Skip API tests (0 or 1)"
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
