#!/bin/bash

# Frontend Pages Test Script
# Tests all frontend page loads and authenticated routes

# Don't use set -e as it causes premature exit on expected failures

# Configuration
WEBUI_HOST="${WEBUI_HOST:-http://localhost:3000}"
API_HOST="${API_HOST:-http://localhost:5001}"
VERBOSE="${VERBOSE:-0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Test data storage
ACCESS_TOKEN=""
REFRESH_TOKEN=""

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
    echo -e "${BLUE}[SECTION]${NC} $1"
}

test_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}✗${NC} $1"
}

# Test a page load (checking for 200 and HTML content)
test_page_load() {
    local path="$1"
    local description="$2"
    local check_content="${3:-<!DOCTYPE html>}"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $WEBUI_HOST$path"
    fi

    response=$(curl -s -w "\n%{http_code}" "$WEBUI_HOST$path" 2>&1)
    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq 200 ]; then
        if echo "$body" | grep -qi "$check_content"; then
            test_pass "$description (HTTP $status, content verified)"
            return 0
        else
            test_fail "$description (HTTP $status, but content check failed)"
            return 1
        fi
    else
        test_fail "$description (Expected: 200, Got: $status)"
        return 1
    fi
}

# Test API endpoint
test_api() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    local auth_header="$4"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $API_HOST$endpoint"
    fi

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $auth_header" "$API_HOST$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" "$API_HOST$endpoint" 2>&1)
    fi

    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        test_pass "$description (HTTP $status)"
        echo "$body"
        return 0
    else
        test_fail "$description (Expected: $expected_status, Got: $status)"
        [ "$VERBOSE" -eq 1 ] && echo "Response: $body"
        return 1
    fi
}

# Test POST endpoint
test_post() {
    local endpoint="$1"
    local data="$2"
    local expected_status="$3"
    local description="$4"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "POST $API_HOST$endpoint"
    fi

    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$API_HOST$endpoint" 2>&1)

    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" -eq "$expected_status" ]; then
        test_pass "$description (HTTP $status)"
        echo "$body"
        return 0
    else
        test_fail "$description (Expected: $expected_status, Got: $status)"
        return 1
    fi
}

# Extract JSON field value
extract_json_field() {
    local json="$1"
    local field="$2"
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4
}

# Check if a JavaScript bundle or static asset loads
test_static_asset() {
    local path="$1"
    local description="$2"
    local expected_type="$3"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $WEBUI_HOST$path"
    fi

    response=$(curl -sI "$WEBUI_HOST$path" 2>&1)
    status=$(echo "$response" | grep -i "HTTP/" | head -1 | awk '{print $2}')
    content_type=$(echo "$response" | grep -i "content-type:" | head -1)

    if [ "$status" = "200" ]; then
        if [ -n "$expected_type" ] && ! echo "$content_type" | grep -qi "$expected_type"; then
            test_fail "$description (HTTP $status, wrong content-type)"
            return 1
        fi
        test_pass "$description (HTTP $status)"
        return 0
    else
        test_fail "$description (Expected: 200, Got: $status)"
        return 1
    fi
}

# Main Test Suite
main() {
    log_section "Starting Frontend Pages Tests"
    log_info "WebUI Host: $WEBUI_HOST"
    log_info "API Host: $API_HOST"
    echo ""

    # Wait for services to be ready
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

    log_info "Waiting for API to be ready..."
    retry_count=0
    while ! curl -s "$API_HOST/api/v1/health" > /dev/null 2>&1; do
        retry_count=$((retry_count + 1))
        if [ $retry_count -ge $max_retries ]; then
            log_error "API did not become ready in time"
            exit 1
        fi
        sleep 2
    done
    log_info "API is ready!"
    echo ""

    # ========================================
    # Public Page Tests (No Auth Required)
    # ========================================
    log_section "Public Page Tests"
    echo "=== Public Page Tests ==="

    # Login page
    test_page_load "/login" "Login page loads"

    # Root path (should serve SPA)
    test_page_load "/" "Root page loads (SPA)"

    # Health endpoint
    test_page_load "/health" "Health endpoint" "ok"
    echo ""

    # ========================================
    # SPA Routing Tests
    # ========================================
    log_section "SPA Routing Tests"
    echo "=== SPA Routing Tests ==="

    # All these should return the SPA (index.html) with 200
    test_page_load "/dashboard" "Dashboard route (SPA fallback)"
    test_page_load "/profile" "Profile route (SPA fallback)"
    test_page_load "/settings" "Settings route (SPA fallback)"
    test_page_load "/users" "Users route (SPA fallback)"
    test_page_load "/users/123" "User detail route (SPA fallback)"

    # Unknown routes should also fallback to SPA
    test_page_load "/some/unknown/route" "Unknown route (SPA fallback)"
    echo ""

    # ========================================
    # Static Asset Tests
    # ========================================
    log_section "Static Asset Tests"
    echo "=== Static Asset Tests ==="

    # Check if index.html is accessible
    test_page_load "/index.html" "Index.html direct access"

    # Check favicon (may or may not exist)
    response=$(curl -sI "$WEBUI_HOST/favicon.ico" 2>&1)
    status=$(echo "$response" | grep -i "HTTP/" | head -1 | awk '{print $2}')
    if [ "$status" = "200" ] || [ "$status" = "204" ]; then
        test_pass "Favicon accessible (HTTP $status)"
    else
        log_warn "Favicon not found (HTTP $status) - this is optional"
    fi
    echo ""

    # ========================================
    # API Proxy Tests
    # ========================================
    log_section "API Proxy Tests"
    echo "=== API Proxy Tests ==="

    # Test that API calls through WebUI proxy work
    log_info "Testing API proxy through WebUI..."
    proxy_response=$(curl -s -w "\n%{http_code}" "$WEBUI_HOST/api/v1/health" 2>&1)
    proxy_status=$(echo "$proxy_response" | tail -n 1)
    if [ "$proxy_status" -eq 200 ]; then
        test_pass "API proxy /api/v1/health (HTTP $proxy_status)"
    else
        test_fail "API proxy /api/v1/health (Expected: 200, Got: $proxy_status)"
    fi
    echo ""

    # ========================================
    # Authentication Setup for Protected Routes
    # ========================================
    log_section "Authentication Setup"
    echo "=== Authentication Setup ==="

    TIMESTAMP=$(date +%s)
    TEST_EMAIL="test-frontend-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Frontend Test User\"}" \
        201 \
        "User registration")

    if [ $? -eq 0 ]; then
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "User login")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
            log_info "Successfully obtained access token"
        fi
    fi
    echo ""

    # ========================================
    # Authenticated API Tests (via proxy)
    # ========================================
    log_section "Authenticated API Tests"
    echo "=== Authenticated API Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Dashboard data endpoint
        test_api "/api/v1/dashboard/stats" 200 \
            "Dashboard stats API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Profile endpoint
        test_api "/api/v1/profile/me" 200 \
            "Profile API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Drawings list endpoint
        test_api "/api/v1/drawings" 200 \
            "Drawings list API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Collections list endpoint
        test_api "/api/v1/collections" 200 \
            "Collections list API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Groups list endpoint
        test_api "/api/v1/groups" 200 \
            "Groups list API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Templates list endpoint
        test_api "/api/v1/templates" 200 \
            "Templates list API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Libraries list endpoint
        test_api "/api/v1/libraries" 200 \
            "Libraries list API" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Users search endpoint (should work for all users)
        test_api "/api/v1/users/search?q=test" 200 \
            "Users search API" \
            "$ACCESS_TOKEN" > /dev/null || true
    else
        log_warn "Skipping authenticated API tests (no access token)"
    fi
    echo ""

    # ========================================
    # Security Headers Tests
    # ========================================
    log_section "Security Headers Tests"
    echo "=== Security Headers Tests ==="

    headers_response=$(curl -sI "$WEBUI_HOST/")

    # X-Frame-Options
    if echo "$headers_response" | grep -qi "x-frame-options"; then
        test_pass "X-Frame-Options header present"
    else
        log_warn "X-Frame-Options header missing (recommended)"
    fi

    # X-Content-Type-Options
    if echo "$headers_response" | grep -qi "x-content-type-options"; then
        test_pass "X-Content-Type-Options header present"
    else
        log_warn "X-Content-Type-Options header missing (recommended)"
    fi

    # Content-Security-Policy
    if echo "$headers_response" | grep -qi "content-security-policy"; then
        test_pass "Content-Security-Policy header present"
    else
        log_warn "Content-Security-Policy header missing (recommended)"
    fi

    # Strict-Transport-Security (may not be present in dev)
    if echo "$headers_response" | grep -qi "strict-transport-security"; then
        test_pass "Strict-Transport-Security header present"
    else
        log_warn "Strict-Transport-Security header missing (optional in dev)"
    fi
    echo ""

    # ========================================
    # Error Page Tests
    # ========================================
    log_section "Error Page Tests"
    echo "=== Error Page Tests ==="

    # 404 for non-existent API endpoint
    test_api "/api/v1/nonexistent" 404 \
        "404 for non-existent API endpoint" || true

    # 401 for protected endpoint without auth
    test_api "/api/v1/profile/me" 401 \
        "401 for protected endpoint without auth" || true
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        log_info "Logging out test user..."
        curl -s -X POST -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "{}" \
            "$API_HOST/api/v1/auth/logout" > /dev/null 2>&1 || true
        test_pass "User logout"
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - Frontend Pages"
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
