#!/bin/bash

# Flask Backend API Test Script - v0.2.0 Features
# Tests new Collections API, Admin Statistics, Health Checks, and Email Verification
# Validates API compatibility between releases

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
TEST_USER_ID=""
ACCESS_TOKEN=""
ADMIN_TOKEN=""
DRAWING_ID=""
COLLECTION_ID=""
COLLECTION_ID_2=""
SHARE_TOKEN=""

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

# Main Test Suite
main() {
    log_section "Starting Flask Backend API Tests - v0.2.0 Features"
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
    # Health Check Tests
    # ========================================
    log_section "Health Check Tests"
    echo "=== Health Check Tests ==="

    test_get "/api/v1/health" 200 "GET /api/v1/health - Basic health check" || true
    test_get "/api/v1/health/ready" 200 "GET /api/v1/health/ready - Readiness check" || true
    test_get "/api/v1/health/z" 200 "GET /api/v1/health/z - Healthz alias" || true
    echo ""

    # ========================================
    # Authentication Setup
    # ========================================
    log_section "Authentication Setup"
    echo "=== Authentication Setup ==="

    # Generate unique email for this test run
    TIMESTAMP=$(date +%s)
    TEST_EMAIL="test-v0.2.0-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    # Register test user
    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Test User v0.2.0\"}" \
        201 \
        "POST /api/v1/auth/register - User registration")

    if [ $? -eq 0 ]; then
        # Extract user ID from response
        TEST_USER_ID=$(extract_json_field "$register_response" "id")

        # Login to get access token
        log_info "Logging in as: $TEST_EMAIL"
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User login")

        if [ $? -eq 0 ]; then
            # Extract access token from login response
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")

            if [ -n "$ACCESS_TOKEN" ]; then
                log_info "Successfully obtained access token"
            else
                log_warn "Could not extract access token from login response"
            fi
        fi
    fi

    # Login as default admin for admin-specific tests
    log_info "Logging in as admin for admin tests..."
    admin_login_response=$(test_post "/api/v1/auth/login" \
        "{\"email\":\"admin@localhost.local\",\"password\":\"admin123\"}" \
        200 \
        "POST /api/v1/auth/login - Admin login") || true

    if [ $? -eq 0 ]; then
        ADMIN_TOKEN=$(extract_json_field "$admin_login_response" "access_token")
        if [ -n "$ADMIN_TOKEN" ]; then
            log_info "Successfully obtained admin access token"
        fi
    fi
    echo ""

    # ========================================
    # Create Test Drawing (needed for collections)
    # ========================================
    log_section "Create Test Drawing"
    echo "=== Create Test Drawing ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        drawing_response=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Test Drawing for Collections\",\"description\":\"Created for v0.2.0 collection tests\",\"content\":{\"nodes\":[],\"edges\":[]}}" \
            201 \
            "POST /api/v1/drawings - Create test drawing" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID=$(echo "$drawing_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created test drawing with ID: $DRAWING_ID"
        else
            log_warn "Failed to create test drawing - some collection tests may fail"
        fi
    fi
    echo ""

    # ========================================
    # Collections API Tests
    # ========================================
    log_section "Collections API Tests"
    echo "=== Collections API Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Create Collection 1
        log_info "Testing collection creation..."
        create_collection_response=$(test_post "/api/v1/collections" \
            "{\"name\":\"Test Collection 1\",\"description\":\"First test collection\",\"share_mode\":\"private\",\"is_public\":false}" \
            201 \
            "POST /api/v1/collections - Create collection" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            COLLECTION_ID=$(extract_json_field "$create_collection_response" "id")
            log_info "Created collection with ID: $COLLECTION_ID"
        fi

        # Create Collection 2 (for testing multiple collections)
        log_info "Testing creation of second collection..."
        create_collection_2_response=$(test_post "/api/v1/collections" \
            "{\"name\":\"Test Collection 2\",\"description\":\"Second test collection\",\"share_mode\":\"link\",\"is_public\":false}" \
            201 \
            "POST /api/v1/collections - Create second collection" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            COLLECTION_ID_2=$(extract_json_field "$create_collection_2_response" "id")
            log_info "Created second collection with ID: $COLLECTION_ID_2"
        fi

        # List Collections
        log_info "Testing collection listing..."
        test_get "/api/v1/collections" 200 "GET /api/v1/collections - List collections" "$ACCESS_TOKEN" > /dev/null || true

        # Get Collection Details
        if [ -n "$COLLECTION_ID" ]; then
            log_info "Testing get collection details..."
            test_get "/api/v1/collections/$COLLECTION_ID" 200 "GET /api/v1/collections/{id} - Get collection details" "$ACCESS_TOKEN" > /dev/null || true

            # Update Collection
            log_info "Testing collection update..."
            test_put "/api/v1/collections/$COLLECTION_ID" \
                "{\"name\":\"Updated Collection Name\",\"description\":\"Updated description\"}" \
                200 \
                "PUT /api/v1/collections/{id} - Update collection" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Add Drawing to Collection
            if [ -n "$DRAWING_ID" ]; then
                log_info "Testing add drawing to collection..."
                add_drawing_response=$(test_post "/api/v1/collections/$COLLECTION_ID/drawings" \
                    "{\"drawing_id\":$DRAWING_ID,\"order_index\":0}" \
                    201 \
                    "POST /api/v1/collections/{id}/drawings - Add drawing to collection" \
                    "$ACCESS_TOKEN")

                if [ $? -eq 0 ]; then
                    log_info "Successfully added drawing to collection"
                fi

                # Get Collection Drawings
                log_info "Testing get collection drawings..."
                test_get "/api/v1/collections/$COLLECTION_ID/drawings" 200 "GET /api/v1/collections/{id}/drawings - List collection drawings" "$ACCESS_TOKEN" > /dev/null || true

                # Remove Drawing from Collection
                log_info "Testing remove drawing from collection..."
                test_delete "/api/v1/collections/$COLLECTION_ID/drawings/$DRAWING_ID" \
                    200 \
                    "DELETE /api/v1/collections/{id}/drawings/{drawing_id} - Remove from collection" \
                    "$ACCESS_TOKEN" > /dev/null || true
            fi

            # Generate Share Token
            log_info "Testing share token generation..."
            share_token_response=$(test_post "/api/v1/collections/$COLLECTION_ID/share/token" \
                "" \
                200 \
                "POST /api/v1/collections/{id}/share/token - Generate share token" \
                "$ACCESS_TOKEN")

            if [ $? -eq 0 ]; then
                # Extract token from response
                SHARE_TOKEN=$(echo "$share_token_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
                log_info "Generated share token: $SHARE_TOKEN"
            fi

            # Access Collection via Share Token (unauthenticated)
            if [ -n "$SHARE_TOKEN" ]; then
                log_info "Testing shared collection access via token..."
                test_get "/api/v1/collections/shared/$SHARE_TOKEN" 200 "GET /api/v1/collections/shared/{token} - Public access via token" > /dev/null || true

                # Get Shared Collection Drawings
                log_info "Testing get shared collection drawings..."
                test_get "/api/v1/collections/shared/$SHARE_TOKEN/drawings" 200 "GET /api/v1/collections/shared/{token}/drawings - Public drawings access" > /dev/null || true
            fi

            # Test Collection Sharing (share with another user scenario)
            log_info "Testing collection share functionality..."
            test_post "/api/v1/collections/$COLLECTION_ID/share" \
                "{\"permission\":\"viewer\",\"shared_with_id\":null}" \
                400 \
                "POST /api/v1/collections/{id}/share - Share collection (invalid body)" \
                "$ACCESS_TOKEN" > /dev/null || true

            # List Collection Shares
            log_info "Testing list collection shares..."
            test_get "/api/v1/collections/$COLLECTION_ID/shares" 200 "GET /api/v1/collections/{id}/shares - List shares" "$ACCESS_TOKEN" > /dev/null || true
        fi
    else
        log_warn "Skipping collection tests (no access token)"
    fi
    echo ""

    # ========================================
    # Admin Statistics API Tests
    # ========================================
    log_section "Admin Statistics API Tests"
    echo "=== Admin Statistics API Tests ==="

    # Test with admin token (should succeed)
    if [ -n "$ADMIN_TOKEN" ]; then
        log_info "Testing admin statistics with admin token (expecting 200)..."
        test_get "/api/v1/admin/statistics/dashboard?time_range=7d" \
            200 \
            "GET /api/v1/admin/statistics/dashboard - Dashboard stats (admin)" \
            "$ADMIN_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/statistics/top-users?limit=10" \
            200 \
            "GET /api/v1/admin/statistics/top-users - Top users (admin)" \
            "$ADMIN_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/statistics/top-drawings?limit=10" \
            200 \
            "GET /api/v1/admin/statistics/top-drawings - Top drawings (admin)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test latency metrics (admin only)
        test_get "/api/v1/admin/statistics/latency" \
            200 \
            "GET /api/v1/admin/statistics/latency - Latency metrics (admin)" \
            "$ADMIN_TOKEN" > /dev/null || true

        # Test time series (admin only)
        test_get "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=1h" \
            200 \
            "GET /api/v1/admin/statistics/time-series/{metric} - Time series (admin)" \
            "$ADMIN_TOKEN" > /dev/null || true
    fi

    # Test with non-admin token (should fail with 403)
    if [ -n "$ACCESS_TOKEN" ]; then
        # These should fail with 403 for non-admin users
        log_info "Testing admin statistics (expecting 403 for non-admin user)..."
        test_get "/api/v1/admin/statistics/dashboard?time_range=7d" \
            403 \
            "GET /api/v1/admin/statistics/dashboard - Dashboard stats (403 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/statistics/top-users?limit=10" \
            403 \
            "GET /api/v1/admin/statistics/top-users - Top users (403 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        test_get "/api/v1/admin/statistics/top-drawings?limit=10" \
            403 \
            "GET /api/v1/admin/statistics/top-drawings - Top drawings (403 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test latency metrics (admin only)
        test_get "/api/v1/admin/statistics/latency" \
            403 \
            "GET /api/v1/admin/statistics/latency - Latency metrics (403 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test time series (admin only)
        test_get "/api/v1/admin/statistics/time-series/users?time_range=7d&interval=1h" \
            403 \
            "GET /api/v1/admin/statistics/time-series/{metric} - Time series (403 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi

    # Test unauthorized access to admin endpoints (no auth)
    log_info "Testing unauthorized access to admin endpoints..."
    test_get "/api/v1/admin/statistics/dashboard" \
        401 \
        "GET /api/v1/admin/statistics/dashboard - No auth (401 expected)" > /dev/null || true

    test_get "/api/v1/admin/statistics/top-users" \
        401 \
        "GET /api/v1/admin/statistics/top-users - No auth (401 expected)" > /dev/null || true

    test_get "/api/v1/admin/statistics/top-drawings" \
        401 \
        "GET /api/v1/admin/statistics/top-drawings - No auth (401 expected)" > /dev/null || true
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test protected endpoint without auth
    test_get "/api/v1/collections" \
        401 \
        "GET /api/v1/collections - No auth (401 expected)" > /dev/null || true

    # Test invalid collection ID
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/collections/99999" \
            404 \
            "GET /api/v1/collections/99999 - Non-existent collection (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test invalid share token
        test_get "/api/v1/collections/shared/invalid-token-12345" \
            404 \
            "GET /api/v1/collections/shared/invalid-token - Invalid token (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test invalid drawing ID for collection
        test_post "/api/v1/collections/$COLLECTION_ID/drawings" \
            "{\"drawing_id\":99999,\"order_index\":0}" \
            400 \
            "POST /api/v1/collections/{id}/drawings - Invalid drawing (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi

    # Test invalid time range for admin stats
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/admin/statistics/dashboard?time_range=invalid" \
            400 \
            "GET /api/v1/admin/statistics/dashboard?time_range=invalid - Invalid param (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Delete collections
        if [ -n "$COLLECTION_ID" ]; then
            log_info "Deleting test collection 1..."
            test_delete "/api/v1/collections/$COLLECTION_ID" \
                200 \
                "DELETE /api/v1/collections/{id} - Delete collection" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$COLLECTION_ID_2" ]; then
            log_info "Deleting test collection 2..."
            test_delete "/api/v1/collections/$COLLECTION_ID_2" \
                200 \
                "DELETE /api/v1/collections/{id} - Delete second collection" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Delete test drawing
        if [ -n "$DRAWING_ID" ]; then
            log_info "Deleting test drawing..."
            test_delete "/api/v1/drawings/$DRAWING_ID" \
                200 \
                "DELETE /api/v1/drawings/{id} - Delete test drawing" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Logout
        log_info "Logging out test user..."
        test_post "/api/v1/auth/logout" \
            "{}" \
            200 \
            "POST /api/v1/auth/logout - User logout" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - v0.2.0 Features"
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
