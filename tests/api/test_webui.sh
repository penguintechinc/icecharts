#!/bin/bash

# WebUI/Nginx Test Script
# Tests WebUI health, static file serving, and API proxy

set -e

# Configuration
WEBUI_HOST="${WEBUI_HOST:-http://localhost:3000}"
API_HOST="${API_HOST:-http://localhost:5001}"
VERBOSE="${VERBOSE:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

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

test_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} $1"
}

# Test a GET endpoint
test_get() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    local check_content="$4"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $endpoint"
    fi

    response=$(curl -s -w "\n%{http_code}" "$WEBUI_HOST$endpoint" 2>&1)
    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        # Additional content check if provided
        if [ -n "$check_content" ]; then
            if echo "$body" | grep -q "$check_content"; then
                test_pass "$description (HTTP $status, content verified)"
                return 0
            else
                test_fail "$description (HTTP $status, but content check failed)"
                [ "$VERBOSE" -eq 1 ] && echo "Expected content: $check_content"
                return 1
            fi
        else
            test_pass "$description (HTTP $status)"
            return 0
        fi
    else
        test_fail "$description (Expected: $expected_status, Got: $status)"
        [ "$VERBOSE" -eq 1 ] && echo "Response: $body"
        return 1
    fi
}

# Test API proxy
test_api_proxy() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $WEBUI_HOST/api$endpoint (via Nginx proxy)"
    fi

    # Test through Nginx proxy
    response=$(curl -s -w "\n%{http_code}" "$WEBUI_HOST/api$endpoint" 2>&1)
    status=$(echo "$response" | tail -n 1)

    if [ "$status" -eq "$expected_status" ]; then
        test_pass "$description (HTTP $status)"
        return 0
    else
        test_fail "$description (Expected: $expected_status, Got: $status)"
        return 1
    fi
}

# Main Test Suite
main() {
    log_info "Starting WebUI/Nginx Tests"
    log_info "WebUI Host: $WEBUI_HOST"
    echo ""

    # Wait for WebUI to be ready
    log_info "Waiting for WebUI to be ready..."
    max_retries=30
    retry_count=0
    while ! curl -s "$WEBUI_HOST/health" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "WebUI did not become ready in time"
            exit 1
        fi
        sleep 2
    done
    log_info "WebUI is ready!"
    echo ""

    # ========================================
    # Health Check Tests
    # ========================================
    echo "=== Health Check Tests ==="
    test_get "/health" 200 "WebUI health endpoint"
    echo ""

    # ========================================
    # Static File Serving Tests
    # ========================================
    echo "=== Static File Serving Tests ==="
    test_get "/" 200 "Root path (index.html)" "<!DOCTYPE html>"
    test_get "/index.html" 200 "Index.html directly" || true
    echo ""

    # ========================================
    # API Proxy Tests
    # ========================================
    echo "=== Nginx API Proxy Tests ==="
    log_info "Testing that /api/* routes are proxied to backend"

    # Test health endpoint through proxy
    test_api_proxy "/v1/health" 200 "Health endpoint via proxy"

    # Verify proxy headers are set correctly
    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Checking proxy headers..."
        curl -v "$WEBUI_HOST/api/v1/health" 2>&1 | grep -i "x-forwarded" || true
    fi
    echo ""

    # ========================================
    # Static Asset Caching Tests
    # ========================================
    echo "=== Static Asset Caching Tests ==="

    # Check if static assets have proper cache headers
    cache_response=$(curl -sI "$WEBUI_HOST/" | grep -i "cache-control" || echo "")
    if [ -n "$cache_response" ]; then
        test_pass "Cache-Control header present"
        [ "$VERBOSE" -eq 1 ] && echo "$cache_response"
    else
        test_fail "Cache-Control header missing"
    fi
    echo ""

    # ========================================
    # Security Headers Tests
    # ========================================
    echo "=== Security Headers Tests ==="

    headers_response=$(curl -sI "$WEBUI_HOST/")

    # Check for X-Frame-Options
    if echo "$headers_response" | grep -qi "x-frame-options"; then
        test_pass "X-Frame-Options header present"
    else
        log_warn "X-Frame-Options header missing"
    fi

    # Check for X-Content-Type-Options
    if echo "$headers_response" | grep -qi "x-content-type-options"; then
        test_pass "X-Content-Type-Options header present"
    else
        log_warn "X-Content-Type-Options header missing"
    fi

    # Check for Content-Security-Policy
    if echo "$headers_response" | grep -qi "content-security-policy"; then
        test_pass "Content-Security-Policy header present"
    else
        log_warn "Content-Security-Policy header missing"
    fi
    echo ""

    # ========================================
    # SPA Routing Tests
    # ========================================
    echo "=== SPA Routing Tests ==="
    log_info "Testing that unknown routes fallback to index.html"

    # Test non-existent route (should return index.html for SPA routing)
    test_get "/some/random/route" 200 "Unknown route fallback" "<!DOCTYPE html>"
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary"
    echo "========================================="
    echo -e "Passed: ${GREEN}${TESTS_PASSED}${NC}"
    echo -e "Failed: ${RED}${TESTS_FAILED}${NC}"
    echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo "========================================="

    if [ $TESTS_FAILED -eq 0 ]; then
        log_info "All tests passed!"
        exit 0
    else
        log_error "$TESTS_FAILED test(s) failed"
        exit 1
    fi
}

# Run main test suite
main
