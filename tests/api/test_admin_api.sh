#!/bin/bash

# Admin API Test Script
# Tests Admin user management, settings, SSO config, and statistics

# Don't use set -e as it causes premature exit on expected failures

# Configuration
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
ADMIN_TOKEN=""
USER_TOKEN=""
ADMIN_USER_ID=""
TEST_USER_ID=""

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
        echo "$body"
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

# Test a PUT endpoint
test_put() {
    local endpoint="$1"
    local data="$2"
    local expected_status="$3"
    local description="$4"
    local auth_header="$5"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "PUT $endpoint"
    fi

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PUT \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth_header" \
            -d "$data" \
            "$API_HOST$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X PUT \
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

# Test a DELETE endpoint
test_delete() {
    local endpoint="$1"
    local expected_status="$2"
    local description="$3"
    local auth_header="$4"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "DELETE $endpoint"
    fi

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X DELETE \
            -H "Authorization: Bearer $auth_header" \
            "$API_HOST$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X DELETE "$API_HOST$endpoint" 2>&1)
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

# Extract JSON field value
extract_json_field() {
    local json="$1"
    local field="$2"
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 || echo "$json" | grep -o "\"$field\":[0-9]*" | cut -d':' -f2
}

# Main Test Suite
main() {
    log_section "Starting Admin API Tests"
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
    # Authentication Setup
    # ========================================
    log_section "Authentication Setup"
    echo "=== Authentication Setup ==="

    TIMESTAMP=$(date +%s)
    ADMIN_EMAIL="admin-test-${TIMESTAMP}@example.com"
    USER_EMAIL="regular-user-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    # Register admin user
    log_info "Registering admin user: $ADMIN_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Admin Test User\",\"role\":\"admin\"}" \
        201 \
        "POST /api/v1/auth/register - Admin registration")

    if [ $? -eq 0 ]; then
        ADMIN_USER_ID=$(echo "$register_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('id', d.get('id','')))" 2>/dev/null)
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - Admin login")

        if [ $? -eq 0 ]; then
            ADMIN_TOKEN=$(extract_json_field "$login_response" "access_token")
            log_info "Admin access token obtained"
        fi
    fi

    # Register regular user
    log_info "Registering regular user: $USER_EMAIL"
    user_register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$USER_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Regular Test User\"}" \
        201 \
        "POST /api/v1/auth/register - User registration")

    if [ $? -eq 0 ]; then
        TEST_USER_ID=$(echo "$user_register_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('id', d.get('id','')))" 2>/dev/null)
        user_login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$USER_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User login")

        if [ $? -eq 0 ]; then
            USER_TOKEN=$(extract_json_field "$user_login_response" "access_token")
            log_info "User access token obtained (ID: $TEST_USER_ID)"
        fi
    fi
    echo ""

    # ========================================
    # Admin User Management Tests
    # ========================================
    log_section "Admin User Management Tests"
    echo "=== Admin User Management Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # List all users
        log_info "Testing list users..."
        test_get "/api/v1/admin/users" 200 \
            "GET /api/v1/admin/users - List users" \
            "$ADMIN_TOKEN" > /dev/null || true

        # List users with pagination
        log_info "Testing list users with pagination..."
        test_get "/api/v1/admin/users?page=1&per_page=10" 200 \
            "GET /api/v1/admin/users - List users (paginated)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Get specific user
        if [ -n "$TEST_USER_ID" ]; then
            log_info "Testing get user by ID..."
            test_get "/api/v1/admin/users/$TEST_USER_ID" 200 \
                "GET /api/v1/admin/users/{id} - Get user" \
                "$ADMIN_TOKEN" > /dev/null || true

            # Update user
            log_info "Testing update user..."
            test_put "/api/v1/admin/users/$TEST_USER_ID" \
                "{\"full_name\":\"Updated User Name\",\"role\":\"maintainer\"}" \
                200 \
                "PUT /api/v1/admin/users/{id} - Update user" \
                "$ADMIN_TOKEN" > /dev/null || true

            # Deactivate user
            log_info "Testing deactivate user..."
            test_post "/api/v1/admin/users/$TEST_USER_ID/deactivate" \
                "{}" \
                200 \
                "POST /api/v1/admin/users/{id}/deactivate - Deactivate user" \
                "$ADMIN_TOKEN" > /dev/null || true

            # Activate user
            log_info "Testing activate user..."
            test_post "/api/v1/admin/users/$TEST_USER_ID/activate" \
                "{}" \
                200 \
                "POST /api/v1/admin/users/{id}/activate - Activate user" \
                "$ADMIN_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Admin Statistics Tests
    # ========================================
    log_section "Admin Statistics Tests"
    echo "=== Admin Statistics Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Dashboard statistics
        log_info "Testing dashboard statistics..."
        test_get "/api/v1/admin/statistics/dashboard?time_range=7d" 200 \
            "GET /api/v1/admin/statistics/dashboard - Dashboard stats" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Top users
        log_info "Testing top users..."
        test_get "/api/v1/admin/statistics/top-users?limit=10" 200 \
            "GET /api/v1/admin/statistics/top-users - Top users" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Top drawings
        log_info "Testing top drawings..."
        test_get "/api/v1/admin/statistics/top-drawings?limit=10" 200 \
            "GET /api/v1/admin/statistics/top-drawings - Top drawings" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Latency metrics
        log_info "Testing latency metrics..."
        test_get "/api/v1/admin/statistics/latency" 200 \
            "GET /api/v1/admin/statistics/latency - Latency metrics" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Time series
        log_info "Testing time series statistics..."
        test_get "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=1d" 200 \
            "GET /api/v1/admin/statistics/time-series/{metric} - Time series" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Logins by country
        log_info "Testing logins by country..."
        test_get "/api/v1/admin/statistics/logins-by-country" 200 \
            "GET /api/v1/admin/statistics/logins-by-country - Geo stats" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Admin Settings Tests
    # ========================================
    log_section "Admin Settings Tests"
    echo "=== Admin Settings Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Signup settings
        log_info "Testing get signup settings..."
        test_get "/api/v1/admin/settings/signup" 200 \
            "GET /api/v1/admin/settings/signup - Get signup settings" \
            "$ADMIN_TOKEN" > /dev/null || true

        log_info "Testing update signup settings..."
        test_put "/api/v1/admin/settings/signup" \
            "{\"allow_signups\":true,\"require_email_verification\":true,\"allowed_domains\":[]}" \
            200 \
            "PUT /api/v1/admin/settings/signup - Update signup settings" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Email settings
        log_info "Testing get email settings..."
        test_get "/api/v1/admin/settings/email" 200 \
            "GET /api/v1/admin/settings/email - Get email settings" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Site settings
        log_info "Testing get site settings..."
        test_get "/api/v1/admin/settings/site" 200 \
            "GET /api/v1/admin/settings/site - Get site settings" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Admin Activity & Audit Log Tests
    # ========================================
    log_section "Admin Activity & Audit Log Tests"
    echo "=== Admin Activity & Audit Log Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Activity log
        log_info "Testing activity log..."
        test_get "/api/v1/admin/activity" 200 \
            "GET /api/v1/admin/activity - Activity log" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Audit log
        log_info "Testing audit log..."
        test_get "/api/v1/admin/audit-log" 200 \
            "GET /api/v1/admin/audit-log - Audit log" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Legacy stats endpoint
        log_info "Testing legacy stats endpoint..."
        test_get "/api/v1/admin/stats" 200 \
            "GET /api/v1/admin/stats - Legacy stats" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Admin System Health Tests
    # ========================================
    log_section "Admin System Health Tests"
    echo "=== Admin System Health Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # System health
        log_info "Testing system health..."
        test_get "/api/v1/admin/system/health" 200 \
            "GET /api/v1/admin/system/health - System health" \
            "$ADMIN_TOKEN" > /dev/null || true

        # System config
        log_info "Testing system config..."
        test_get "/api/v1/admin/system/config" 200 \
            "GET /api/v1/admin/system/config - System config" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Admin SSO Config Tests
    # ========================================
    log_section "Admin SSO Config Tests"
    echo "=== Admin SSO Config Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # List SSO providers
        log_info "Testing list SSO providers..."
        test_get "/api/v1/admin/sso/providers" 200 \
            "GET /api/v1/admin/sso/providers - List SSO providers" \
            "$ADMIN_TOKEN" > /dev/null || true

        # List SSO configurations
        log_info "Testing list SSO configurations..."
        test_get "/api/v1/admin/sso" 200 \
            "GET /api/v1/admin/sso - List SSO configs" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Non-Admin Access Tests (should fail with 403)
    # ========================================
    log_section "Non-Admin Access Tests"
    echo "=== Non-Admin Access Tests ==="

    if [ -n "$USER_TOKEN" ]; then
        # Regular user should not access admin endpoints
        log_info "Testing non-admin access to admin endpoints..."
        test_get "/api/v1/admin/users" 403 \
            "GET /api/v1/admin/users - Non-admin (403 expected)" \
            "$USER_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/statistics/dashboard" 403 \
            "GET /api/v1/admin/statistics/dashboard - Non-admin (403 expected)" \
            "$USER_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/settings/signup" 403 \
            "GET /api/v1/admin/settings/signup - Non-admin (403 expected)" \
            "$USER_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Unauthenticated Access Tests
    # ========================================
    log_section "Unauthenticated Access Tests"
    echo "=== Unauthenticated Access Tests ==="

    # No auth should return 401
    test_get "/api/v1/admin/users" 401 \
        "GET /api/v1/admin/users - No auth (401 expected)" > /dev/null || true

    test_get "/api/v1/admin/statistics/dashboard" 401 \
        "GET /api/v1/admin/statistics/dashboard - No auth (401 expected)" > /dev/null || true

    test_get "/api/v1/admin/settings/signup" 401 \
        "GET /api/v1/admin/settings/signup - No auth (401 expected)" > /dev/null || true
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Non-existent user
        test_get "/api/v1/admin/users/99999" 404 \
            "GET /api/v1/admin/users/99999 - Not found (404 expected)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Invalid time range for statistics
        test_get "/api/v1/admin/statistics/dashboard?time_range=invalid" 400 \
            "GET /api/v1/admin/statistics/dashboard?time_range=invalid - Bad request (400 expected)" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    # Delete test user (admin cleanup)
    if [ -n "$ADMIN_TOKEN" ] && [ -n "$TEST_USER_ID" ]; then
        log_info "Deleting test user..."
        test_delete "/api/v1/admin/users/$TEST_USER_ID" 200 \
            "DELETE /api/v1/admin/users/{id} - Delete test user" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi

    # Logout users
    if [ -n "$ADMIN_TOKEN" ]; then
        log_info "Logging out admin user..."
        test_post "/api/v1/auth/logout" "{}" 200 \
            "POST /api/v1/auth/logout - Admin logout" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi

    if [ -n "$USER_TOKEN" ]; then
        log_info "Logging out regular user..."
        test_post "/api/v1/auth/logout" "{}" 200 \
            "POST /api/v1/auth/logout - User logout" \
            "$USER_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - Admin API"
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
