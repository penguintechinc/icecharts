#!/bin/bash

# Service Accounts API Test Script
# Tests service account management, token generation, and scoped access
# Part of the External App Integration feature

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
SERVICE_ACCOUNT_ID=""
SERVICE_TOKEN=""
TOKEN_JTI=""
DRAWING_ID=""

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
        log_info "Data: $data"
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
    # Try string format first: "field":"value"
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 && return 0
    # Then try number format: "field":123
    echo "$json" | grep -o "\"$field\":[0-9]*" | cut -d':' -f2 && return 0
    # If both fail, return empty
    return 1
}

# Extract nested JSON field
extract_nested_json_field() {
    local json="$1"
    local field="$2"
    echo "$json" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$field', d.get('service_account',{}).get('$field','')))" 2>/dev/null || echo ""
}

# Main Test Suite
main() {
    log_section "Starting Service Accounts API Tests"
    log_info "API Host: $API_HOST"
    log_info "Verbose: $VERBOSE"
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
    # Admin Authentication Setup
    # ========================================
    log_section "Admin Authentication Setup"
    echo "=== Admin Authentication Setup ==="

    # Use default admin credentials (created automatically on first startup)
    # Note: Self-registration always assigns 'viewer' role, so we use the default admin
    ADMIN_EMAIL="admin@localhost.local"
    ADMIN_PASSWORD="admin123"

    log_info "Logging in as default admin: $ADMIN_EMAIL"
    login_response=$(test_post "/api/v1/auth/login" \
        "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
        200 \
        "POST /api/v1/auth/login - Admin login")

    if [ $? -eq 0 ]; then
        ADMIN_TOKEN=$(extract_json_field "$login_response" "access_token")
        if [ -n "$ADMIN_TOKEN" ]; then
            log_info "Successfully obtained admin access token"
        else
            log_error "Could not extract admin access token"
            exit 1
        fi
    else
        log_error "Failed to login as admin"
        exit 1
    fi
    echo ""

    # ========================================
    # Service Account Admin Endpoints Tests
    # ========================================
    log_section "Service Account Admin Endpoints"
    echo "=== Service Account Admin Endpoints ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Test listing available scopes
        log_info "Testing get available scopes..."
        test_get "/api/v1/admin/service-accounts/scopes" 200 \
            "GET /api/v1/admin/service-accounts/scopes - List available scopes" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test creating a service account
        log_info "Testing service account creation..."
        create_sa_response=$(test_post "/api/v1/admin/service-accounts" \
            "{\"name\":\"Test Integration\",\"description\":\"Test service account for API tests\",\"scopes\":[\"drawings:read\",\"drawings:write\",\"exports:create\"],\"rate_limit\":500}" \
            201 \
            "POST /api/v1/admin/service-accounts - Create service account" \
            "$ADMIN_TOKEN")

        if [ $? -eq 0 ]; then
            SERVICE_ACCOUNT_ID=$(echo "$create_sa_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('service_account',{}).get('id',''))" 2>/dev/null)
            log_info "Created service account with ID: $SERVICE_ACCOUNT_ID"
        fi

        # Test listing service accounts
        log_info "Testing list service accounts..."
        test_get "/api/v1/admin/service-accounts" 200 \
            "GET /api/v1/admin/service-accounts - List service accounts" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test getting service account details
        if [ -n "$SERVICE_ACCOUNT_ID" ]; then
            log_info "Testing get service account details..."
            test_get "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID" 200 \
                "GET /api/v1/admin/service-accounts/{id} - Get service account" \
                "$ADMIN_TOKEN" > /dev/null || true

            # Test updating service account
            log_info "Testing service account update..."
            test_put "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID" \
                "{\"name\":\"Updated Integration\",\"rate_limit\":1000}" \
                200 \
                "PUT /api/v1/admin/service-accounts/{id} - Update service account" \
                "$ADMIN_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Token Management Tests
    # ========================================
    log_section "Token Management Tests"
    echo "=== Token Management Tests ==="

    if [ -n "$ADMIN_TOKEN" ] && [ -n "$SERVICE_ACCOUNT_ID" ]; then
        # Generate a service token
        log_info "Testing token generation..."
        token_response=$(test_post "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID/tokens" \
            "{\"name\":\"Test Token\",\"expires_days\":30}" \
            201 \
            "POST /api/v1/admin/service-accounts/{id}/tokens - Generate token" \
            "$ADMIN_TOKEN")

        if [ $? -eq 0 ]; then
            SERVICE_TOKEN=$(echo "$token_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',''))" 2>/dev/null)
            TOKEN_JTI=$(echo "$token_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token_info',{}).get('token_jti',''))" 2>/dev/null)
            log_info "Generated service token (JTI: $TOKEN_JTI)"
        fi

        # List tokens for service account
        log_info "Testing list tokens..."
        test_get "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID/tokens" 200 \
            "GET /api/v1/admin/service-accounts/{id}/tokens - List tokens" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Service Token Authentication Tests
    # ========================================
    log_section "Service Token Authentication Tests"
    echo "=== Service Token Authentication Tests ==="

    if [ -n "$SERVICE_TOKEN" ]; then
        # Test using service token to access drawings (should work - has drawings:read scope)
        log_info "Testing service token access to drawings..."
        test_get "/api/v1/drawings" 200 \
            "GET /api/v1/drawings - Service token access (drawings:read)" \
            "$SERVICE_TOKEN" > /dev/null || true

        # Create a drawing with service token
        log_info "Testing create drawing with service token..."
        drawing_response=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Service Account Drawing\",\"description\":\"Created by service account\",\"content\":{\"nodes\":[],\"edges\":[]},\"visibility\":\"private\"}" \
            201 \
            "POST /api/v1/drawings - Service token create (drawings:write)" \
            "$SERVICE_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID=$(echo "$drawing_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id',''))" 2>/dev/null)
            log_info "Created drawing with ID: $DRAWING_ID"
        fi

        # Test service token access to templates (should work - has templates:read if granted)
        log_info "Testing service token access to templates..."
        # This may fail with 403 since we didn't grant templates:read scope
        test_get "/api/v1/templates" 403 \
            "GET /api/v1/templates - Service token (no templates:read scope - 403 expected)" \
            "$SERVICE_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Scope Enforcement Tests
    # ========================================
    log_section "Scope Enforcement Tests"
    echo "=== Scope Enforcement Tests ==="

    if [ -n "$SERVICE_TOKEN" ] && [ -n "$DRAWING_ID" ]; then
        # Test delete drawing (should fail - no drawings:delete scope)
        log_info "Testing scope enforcement - delete without scope..."
        test_delete "/api/v1/drawings/$DRAWING_ID" 403 \
            "DELETE /api/v1/drawings/{id} - No drawings:delete scope (403 expected)" \
            "$SERVICE_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Test creating service account with invalid scopes
        log_info "Testing invalid scope validation..."
        test_post "/api/v1/admin/service-accounts" \
            "{\"name\":\"Invalid\",\"scopes\":[\"invalid:scope\"]}" \
            400 \
            "POST /api/v1/admin/service-accounts - Invalid scope (400 expected)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test creating service account without scopes
        log_info "Testing missing scopes validation..."
        test_post "/api/v1/admin/service-accounts" \
            "{\"name\":\"NoScopes\"}" \
            400 \
            "POST /api/v1/admin/service-accounts - No scopes (400 expected)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test non-existent service account
        log_info "Testing non-existent service account..."
        test_get "/api/v1/admin/service-accounts/99999" 404 \
            "GET /api/v1/admin/service-accounts/99999 - Not found (404 expected)" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi

    # Test unauthenticated access to admin endpoints
    log_info "Testing unauthenticated admin access..."
    test_get "/api/v1/admin/service-accounts" 401 \
        "GET /api/v1/admin/service-accounts - No auth (401 expected)" > /dev/null || true

    test_post "/api/v1/admin/service-accounts" \
        "{\"name\":\"Test\"}" \
        401 \
        "POST /api/v1/admin/service-accounts - No auth (401 expected)" > /dev/null || true
    echo ""

    # ========================================
    # Token Revocation Tests
    # ========================================
    log_section "Token Revocation Tests"
    echo "=== Token Revocation Tests ==="

    if [ -n "$ADMIN_TOKEN" ] && [ -n "$SERVICE_ACCOUNT_ID" ] && [ -n "$TOKEN_JTI" ]; then
        # Revoke token
        log_info "Testing token revocation..."
        test_delete "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID/tokens/$TOKEN_JTI" 200 \
            "DELETE /api/v1/admin/service-accounts/{id}/tokens/{jti} - Revoke token" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test using revoked token (should fail)
        if [ -n "$SERVICE_TOKEN" ]; then
            log_info "Testing revoked token access..."
            test_get "/api/v1/drawings" 401 \
                "GET /api/v1/drawings - Revoked token (401 expected)" \
                "$SERVICE_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ADMIN_TOKEN" ]; then
        # Delete test drawing
        if [ -n "$DRAWING_ID" ]; then
            log_info "Deleting test drawing..."
            test_delete "/api/v1/drawings/$DRAWING_ID" 200 \
                "DELETE /api/v1/drawings/{id} - Delete test drawing" \
                "$ADMIN_TOKEN" > /dev/null || true
        fi

        # Delete service account (cascades to tokens)
        if [ -n "$SERVICE_ACCOUNT_ID" ]; then
            log_info "Deleting test service account..."
            test_delete "/api/v1/admin/service-accounts/$SERVICE_ACCOUNT_ID" 200 \
                "DELETE /api/v1/admin/service-accounts/{id} - Delete service account" \
                "$ADMIN_TOKEN" > /dev/null || true
        fi

        # Logout admin
        log_info "Logging out admin user..."
        test_post "/api/v1/auth/logout" \
            "{}" \
            200 \
            "POST /api/v1/auth/logout - Admin logout" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - Service Accounts"
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
