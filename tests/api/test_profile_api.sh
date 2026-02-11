#!/bin/bash

# Profile API Test Script
# Tests Profile operations: avatar, preferences, password change

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
ACCESS_TOKEN=""

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

# Test a PATCH endpoint
test_patch() {
    local endpoint="$1"
    local data="$2"
    local expected_status="$3"
    local description="$4"
    local auth_header="$5"

    if [ "$VERBOSE" -eq 1 ]; then
        log_info "Testing: $description"
        log_info "PATCH $endpoint"
    fi

    if [ -n "$auth_header" ]; then
        response=$(curl -s -w "\n%{http_code}" -X PATCH \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $auth_header" \
            -d "$data" \
            "$API_HOST$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X PATCH \
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
    # Try string format first: "field":"value"
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 && return 0
    # Then try number format: "field":123
    echo "$json" | grep -o "\"$field\":[0-9]*" | cut -d':' -f2 && return 0
    # If both fail, return empty
    return 1
}

# Main Test Suite
main() {
    log_section "Starting Profile API Tests"
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
    TEST_EMAIL="test-profile-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"
    NEW_PASSWORD="NewAdmin456"

    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Profile Test User\"}" \
        201 \
        "POST /api/v1/auth/register - User registration")

    if [ $? -eq 0 ]; then
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User login")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
            log_info "Successfully obtained access token"
        fi
    fi
    echo ""

    # ========================================
    # Profile Read Tests
    # ========================================
    log_section "Profile Read Tests"
    echo "=== Profile Read Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Get current profile
        log_info "Testing get profile..."
        test_get "/api/v1/profile/me" 200 \
            "GET /api/v1/profile/me - Get profile" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Profile Update Tests
    # ========================================
    log_section "Profile Update Tests"
    echo "=== Profile Update Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Update profile with PATCH
        log_info "Testing profile update (PATCH)..."
        test_patch "/api/v1/profile/me" \
            "{\"full_name\":\"Updated Profile User\",\"bio\":\"Test bio for smoke testing\"}" \
            200 \
            "PATCH /api/v1/profile/me - Update profile" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Verify update
        log_info "Verifying profile update..."
        test_get "/api/v1/profile/me" 200 \
            "GET /api/v1/profile/me - Verify profile update" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Preferences Tests
    # ========================================
    log_section "Preferences Tests"
    echo "=== Preferences Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Get preferences
        log_info "Testing get preferences..."
        test_get "/api/v1/profile/preferences" 200 \
            "GET /api/v1/profile/preferences - Get preferences" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Update preferences (PUT - full replace)
        log_info "Testing update preferences (PUT)..."
        test_put "/api/v1/profile/preferences" \
            "{\"theme\":\"dark\",\"language\":\"en\",\"notifications\":{\"email\":true,\"push\":false},\"auto_save\":true}" \
            200 \
            "PUT /api/v1/profile/preferences - Update preferences (full)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Update preferences (PATCH - partial)
        log_info "Testing update preferences (PATCH)..."
        test_patch "/api/v1/profile/preferences" \
            "{\"theme\":\"light\"}" \
            200 \
            "PATCH /api/v1/profile/preferences - Update preferences (partial)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Verify preferences
        log_info "Verifying preferences update..."
        test_get "/api/v1/profile/preferences" 200 \
            "GET /api/v1/profile/preferences - Verify preferences" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Avatar Tests
    # ========================================
    log_section "Avatar Tests"
    echo "=== Avatar Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Upload avatar (using base64 encoded small image)
        log_info "Testing avatar upload..."
        # Using a minimal PNG (1x1 pixel transparent)
        MINI_PNG_BASE64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        test_put "/api/v1/profile/avatar" \
            "{\"image\":\"data:image/png;base64,$MINI_PNG_BASE64\"}" \
            200 \
            "PUT /api/v1/profile/avatar - Upload avatar" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Delete avatar
        log_info "Testing avatar deletion..."
        test_delete "/api/v1/profile/avatar" 200 \
            "DELETE /api/v1/profile/avatar - Delete avatar" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Password Change Tests
    # ========================================
    log_section "Password Change Tests"
    echo "=== Password Change Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Change password
        log_info "Testing password change..."
        test_put "/api/v1/profile/password" \
            "{\"current_password\":\"$TEST_PASSWORD\",\"new_password\":\"$NEW_PASSWORD\"}" \
            200 \
            "PUT /api/v1/profile/password - Change password" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Verify new password works by logging in again
        log_info "Verifying new password works..."
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$NEW_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - Login with new password")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
            log_info "New password verified successfully"
        fi
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/profile/me" 401 "GET /api/v1/profile/me - No auth (401 expected)" > /dev/null || true
    test_get "/api/v1/profile/preferences" 401 "GET /api/v1/profile/preferences - No auth (401 expected)" > /dev/null || true

    if [ -n "$ACCESS_TOKEN" ]; then
        # Test password change with wrong current password
        test_put "/api/v1/profile/password" \
            "{\"current_password\":\"wrongpassword\",\"new_password\":\"$TEST_PASSWORD\"}" \
            400 \
            "PUT /api/v1/profile/password - Wrong current password (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test password change with weak password
        test_put "/api/v1/profile/password" \
            "{\"current_password\":\"$NEW_PASSWORD\",\"new_password\":\"weak\"}" \
            400 \
            "PUT /api/v1/profile/password - Weak new password (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test invalid preferences format
        test_put "/api/v1/profile/preferences" \
            "{\"theme\":123}" \
            400 \
            "PUT /api/v1/profile/preferences - Invalid format (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        log_info "Logging out test user..."
        test_post "/api/v1/auth/logout" "{}" 200 \
            "POST /api/v1/auth/logout - Logout" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - Profile API"
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
