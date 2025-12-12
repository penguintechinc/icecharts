#!/bin/bash

# Flask Backend API Test Script
# Tests Flask backend API endpoints with expected responses

set -e

# Configuration
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
    local auth_header="$4"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "GET $endpoint"
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
        return 0
    else
        test_fail "$description (Expected: $expected_status, Got: $status)"
        [ "$VERBOSE" -eq 1 ] && echo "Response: $body"
        return 1
    fi
}

# Test a POST endpoint
test_post() {
    local endpoint="$1"
    local data="$2"
    local expected_status="$3"
    local description="$4"
    local auth_header="$5"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "POST $endpoint"
        log_info "Data: $data"
    fi

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth_header" \
            -d "$data" \
            "$API_HOST$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_HOST$endpoint" 2>&1)
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

# Main Test Suite
main() {
    log_info "Starting Flask Backend API Tests"
    log_info "API Host: $API_HOST"
    echo ""

    # Wait for API to be ready
    log_info "Waiting for API to be ready..."
    max_retries=30
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
    # Health Check Tests
    # ========================================
    echo "=== Health Check Tests ==="
    test_get "/api/v1/health" 200 "Health endpoint"
    test_get "/api/v1/health/ready" 200 "Readiness endpoint" || true
    echo ""

    # ========================================
    # Authentication Tests
    # ========================================
    echo "=== Authentication Tests ==="

    # Generate unique email for this test run
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="test-${TIMESTAMP}@example.com"
    TEST_PASSWORD="TestPassword123!"

    # Test user registration
    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Test User\"}" \
        201 \
        "User registration")

    if [ $? -eq 0 ]; then
        # Test user login
        log_info "Logging in as: $TEST_EMAIL"
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "User login")

        if [ $? -eq 0 ]; then
            # Extract access token from login response
            ACCESS_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
            REFRESH_TOKEN=$(echo "$login_response" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)

            if [ -n "$ACCESS_TOKEN" ]; then
                log_info "Successfully obtained access token"

                # Test token refresh
                if [ -n "$REFRESH_TOKEN" ]; then
                    test_post "/api/v1/auth/refresh" \
                        "{\"refresh_token\":\"$REFRESH_TOKEN\"}" \
                        200 \
                        "Token refresh" || true
                fi
            else
                log_warn "Could not extract access token from login response"
            fi
        fi
    fi
    echo ""

    # ========================================
    # Protected Endpoint Tests
    # ========================================
    echo "=== Protected Endpoint Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Test profile endpoint with valid token
        test_get "/api/v1/profile/me" 200 "Get user profile (authenticated)" "$ACCESS_TOKEN"

        # Test drawings endpoint with valid token
        test_get "/api/v1/drawings" 200 "List user drawings (authenticated)" "$ACCESS_TOKEN"

        # Test logout
        test_post "/api/v1/auth/logout" "{}" 200 "User logout" "$ACCESS_TOKEN" || true
    else
        log_warn "Skipping protected endpoint tests (no access token)"
    fi
    echo ""

    # ========================================
    # Error Case Tests
    # ========================================
    echo "=== Error Case Tests ==="

    # Test protected endpoint without auth
    test_get "/api/v1/profile/me" 401 "Get profile without auth"

    # Test with invalid credentials
    test_post "/api/v1/auth/login" \
        "{\"email\":\"invalid@example.com\",\"password\":\"wrongpass\"}" \
        401 \
        "Login with invalid credentials"

    # Test with invalid JWT
    test_get "/api/v1/profile/me" 401 "Get profile with invalid token" "invalid.jwt.token"
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
