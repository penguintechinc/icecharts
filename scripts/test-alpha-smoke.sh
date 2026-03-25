#!/bin/bash
# Alpha Smoke Tests for IceCharts
#
# Runs smoke tests against the alpha deployment on MicroK8s (dal2-alpha)
# Tests basic functionality to verify deployment health.
#
# Usage:
#   ./scripts/test-alpha-smoke.sh [--verbose]
#
# Prerequisites:
#   - Alpha deployment running (./scripts/deploy-alpha.sh)
#   - kubectl configured with dal2-alpha context

set -euo pipefail

# Configuration
KUBE_CONTEXT="${KUBE_CONTEXT:-local-alpha}"
NAMESPACE="icecharts-alpha"
TIMEOUT=10
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to run kubectl with context
kctl() {
    kubectl --context "$KUBE_CONTEXT" "$@"
}

# Function to log verbose output
log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# Function to run a test
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected="${3:-}"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    echo -n "  Testing $test_name... "

    log_verbose "Running: $test_cmd"

    if output=$(eval "$test_cmd" 2>&1); then
        if [ -n "$expected" ]; then
            if echo "$output" | grep -q "$expected"; then
                echo -e "${GREEN}PASS${NC}"
                TESTS_PASSED=$((TESTS_PASSED + 1))
                log_verbose "Output: $output"
                return 0
            else
                echo -e "${RED}FAIL${NC} (expected '$expected')"
                log_verbose "Output: $output"
                TESTS_FAILED=$((TESTS_FAILED + 1))
                return 1
            fi
        else
            echo -e "${GREEN}PASS${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            log_verbose "Output: $output"
            return 0
        fi
    else
        echo -e "${RED}FAIL${NC}"
        log_verbose "Error: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Get API service URL
get_api_url() {
    local api_pod=$(kctl get pods -n "$NAMESPACE" -l app=api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$api_pod" ]; then
        echo "kctl exec -n $NAMESPACE $api_pod -- curl -s localhost:5000"
    else
        # Try NodePort
        local node_port=$(kctl get svc api -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null)
        if [ -n "$node_port" ]; then
            echo "curl -s --connect-timeout $TIMEOUT http://localhost:$node_port"
        else
            echo ""
        fi
    fi
}

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  IceCharts Alpha Smoke Tests${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verify context exists
if ! kubectl config get-contexts "$KUBE_CONTEXT" &>/dev/null; then
    echo -e "${RED}Error: kubectl context '$KUBE_CONTEXT' not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Context:${NC} $KUBE_CONTEXT"
echo -e "${YELLOW}Namespace:${NC} $NAMESPACE"
echo ""

# ===========================================
# Section 1: Kubernetes Resource Tests
# ===========================================
echo -e "${YELLOW}1. Kubernetes Resources${NC}"

run_test "Namespace exists" \
    "kctl get namespace $NAMESPACE -o name" \
    "namespace/$NAMESPACE"

run_test "API deployment ready" \
    "kctl get deployment api -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'" \
    "1"

run_test "Web deployment ready" \
    "kctl get deployment web -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'" \
    "1"

run_test "PostgreSQL ready" \
    "kctl get statefulset postgres -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'" \
    "1"

run_test "Redis ready" \
    "kctl get statefulset redis -n $NAMESPACE -o jsonpath='{.status.readyReplicas}'" \
    "1"

run_test "API service exists" \
    "kctl get svc api -n $NAMESPACE -o name" \
    "service/api"

run_test "Web service exists" \
    "kctl get svc web -n $NAMESPACE -o name" \
    "service/web"

echo ""

# ===========================================
# Section 2: Pod Health Tests
# ===========================================
echo -e "${YELLOW}2. Pod Health${NC}"

run_test "API pods running" \
    "kctl get pods -n $NAMESPACE -l app=api -o jsonpath='{.items[*].status.phase}'" \
    "Running"

run_test "Web pods running" \
    "kctl get pods -n $NAMESPACE -l app=web -o jsonpath='{.items[*].status.phase}'" \
    "Running"

run_test "No pod restarts (API)" \
    "kctl get pods -n $NAMESPACE -l app=api -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'" \
    "0"

run_test "No pod restarts (Web)" \
    "kctl get pods -n $NAMESPACE -l app=web -o jsonpath='{.items[0].status.containerStatuses[0].restartCount}'" \
    "0"

echo ""

# ===========================================
# Section 3: API Endpoint Tests
# ===========================================
echo -e "${YELLOW}3. API Endpoints${NC}"

# Get API pod for exec-based tests
API_POD=$(kctl get pods -n "$NAMESPACE" -l app=api -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$API_POD" ]; then
    run_test "Health endpoint" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/v1/health" \
        "200"

    run_test "Health response valid" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s http://localhost:5000/api/v1/health" \
        "healthy"

    run_test "Auth endpoint accessible" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/v1/auth/status" \
        "401"

    run_test "Drawings endpoint accessible" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/v1/drawings" \
        "401"

    # IceFlows endpoint test
    run_test "IceFlows endpoint accessible" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/v1/iceflows" \
        "401"

    # IceRuns endpoint test
    run_test "IceRuns endpoint accessible" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:5000/api/v1/iceruns" \
        "401"
else
    echo -e "  ${YELLOW}Skipping API endpoint tests - no API pod found${NC}"
fi

echo ""

# ===========================================
# Section 4: Web UI Tests
# ===========================================
echo -e "${YELLOW}4. Web UI${NC}"

WEB_POD=$(kctl get pods -n "$NAMESPACE" -l app=web -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$WEB_POD" ]; then
    run_test "Web UI responds" \
        "kctl exec -n $NAMESPACE $WEB_POD -- curl -s -o /dev/null -w '%{http_code}' http://localhost:3000" \
        "200"

    run_test "Web UI serves HTML" \
        "kctl exec -n $NAMESPACE $WEB_POD -- curl -s http://localhost:3000 | head -1" \
        "<!DOCTYPE html>"
else
    echo -e "  ${YELLOW}Skipping Web UI tests - no Web pod found${NC}"
fi

echo ""

# ===========================================
# Section 5: Database Connectivity
# ===========================================
echo -e "${YELLOW}5. Database Connectivity${NC}"

POSTGRES_POD=$(kctl get pods -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$POSTGRES_POD" ]; then
    run_test "PostgreSQL accepting connections" \
        "kctl exec -n $NAMESPACE $POSTGRES_POD -- pg_isready -U icecharts_user -d icecharts" \
        "accepting connections"
else
    echo -e "  ${YELLOW}Skipping PostgreSQL tests - no pod found${NC}"
fi

REDIS_POD=$(kctl get pods -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$REDIS_POD" ]; then
    run_test "Redis responding to PING" \
        "kctl exec -n $NAMESPACE $REDIS_POD -- redis-cli PING" \
        "PONG"
else
    echo -e "  ${YELLOW}Skipping Redis tests - no pod found${NC}"
fi

echo ""

# ===========================================
# Section 6: Integration Tests
# ===========================================
echo -e "${YELLOW}6. Integration Tests${NC}"

if [ -n "$API_POD" ]; then
    # Test API can connect to database
    run_test "API database connection" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s http://localhost:5000/api/v1/health | grep -o 'database.*ok'" \
        "ok"

    # Test API can connect to Redis
    run_test "API Redis connection" \
        "kctl exec -n $NAMESPACE $API_POD -- curl -s http://localhost:5000/api/v1/health | grep -o 'redis.*ok'" \
        "ok"
fi

echo ""

# ===========================================
# Summary
# ===========================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "  Total Tests:  $TESTS_TOTAL"
echo -e "  ${GREEN}Passed:${NC}       $TESTS_PASSED"
echo -e "  ${RED}Failed:${NC}       $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Review output above.${NC}"
    exit 1
fi
