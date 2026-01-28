#!/bin/bash

# Drawings API Test Script
# Tests Drawings CRUD operations and export functionality

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
DRAWING_ID=""
DRAWING_ID_2=""
EXPORT_JOB_ID=""

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
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 || echo "$json" | grep -o "\"$field\":[0-9]*" | cut -d':' -f2
}

# Main Test Suite
main() {
    log_section "Starting Drawings API Tests"
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
    TEST_EMAIL="test-drawings-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Drawings Test User\"}" \
        201 \
        "POST /api/v1/auth/register - User registration")

    if [ $? -eq 0 ]; then
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User login")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
            if [ -n "$ACCESS_TOKEN" ]; then
                log_info "Successfully obtained access token"
            fi
        fi
    fi
    echo ""

    # ========================================
    # Drawings CRUD Tests
    # ========================================
    log_section "Drawings CRUD Tests"
    echo "=== Drawings CRUD Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Create Drawing 1
        log_info "Testing drawing creation..."
        create_response=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Test Drawing 1\",\"description\":\"First test drawing\",\"content\":{\"nodes\":[],\"edges\":[]},\"visibility\":\"private\",\"tags\":[\"test\",\"smoke\"]}" \
            201 \
            "POST /api/v1/drawings - Create drawing" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID=$(echo "$create_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id',''))" 2>/dev/null)
            log_info "Created drawing with ID: $DRAWING_ID"
        fi

        # Create Drawing 2
        log_info "Testing creation of second drawing..."
        create_response_2=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Test Drawing 2\",\"description\":\"Second test drawing\",\"content\":{\"nodes\":[{\"id\":\"n1\",\"type\":\"rect\"}],\"edges\":[]},\"visibility\":\"public\"}" \
            201 \
            "POST /api/v1/drawings - Create second drawing" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID_2=$(echo "$create_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id',''))" 2>/dev/null)
            log_info "Created second drawing with ID: $DRAWING_ID_2"
        fi

        # List Drawings
        log_info "Testing drawing listing..."
        test_get "/api/v1/drawings" 200 "GET /api/v1/drawings - List drawings" "$ACCESS_TOKEN" > /dev/null || true

        # Get Drawing Details
        if [ -n "$DRAWING_ID" ]; then
            log_info "Testing get drawing details..."
            test_get "/api/v1/drawings/$DRAWING_ID" 200 "GET /api/v1/drawings/{id} - Get drawing" "$ACCESS_TOKEN" > /dev/null || true

            # Update Drawing
            log_info "Testing drawing update..."
            test_put "/api/v1/drawings/$DRAWING_ID" \
                "{\"name\":\"Updated Drawing Name\",\"description\":\"Updated description\",\"status\":\"published\"}" \
                200 \
                "PUT /api/v1/drawings/{id} - Update drawing" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Update Drawing Content
            log_info "Testing drawing content update..."
            test_put "/api/v1/drawings/$DRAWING_ID" \
                "{\"content\":{\"nodes\":[{\"id\":\"n1\",\"type\":\"circle\"}],\"edges\":[]}}" \
                200 \
                "PUT /api/v1/drawings/{id} - Update drawing content" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    else
        log_warn "Skipping drawings tests (no access token)"
    fi
    echo ""

    # ========================================
    # Export Tests
    # ========================================
    log_section "Export Tests"
    echo "=== Export Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$DRAWING_ID" ]; then
        # Export as JSON (synchronous)
        log_info "Testing JSON export..."
        json_response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$API_HOST/api/v1/drawings/$DRAWING_ID/export/json" 2>&1)
        json_status=$(echo "$json_response" | tail -n 1)
        if [ "$json_status" -eq 200 ]; then
            test_pass "GET /api/v1/drawings/{id}/export/json - JSON export (HTTP $json_status)"
        else
            test_fail "GET /api/v1/drawings/{id}/export/json - JSON export (Expected: 200, Got: $json_status)"
        fi

        # Export as SVG
        log_info "Testing SVG export..."
        svg_response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$API_HOST/api/v1/drawings/$DRAWING_ID/export/svg" 2>&1)
        svg_status=$(echo "$svg_response" | tail -n 1)
        if [ "$svg_status" -eq 200 ]; then
            test_pass "GET /api/v1/drawings/{id}/export/svg - SVG export (HTTP $svg_status)"
        else
            test_fail "GET /api/v1/drawings/{id}/export/svg - SVG export (Expected: 200, Got: $svg_status)"
        fi

        # Export as PNG (async - should return 202)
        log_info "Testing PNG export (async)..."
        png_response=$(test_post "/api/v1/drawings/$DRAWING_ID/export" \
            "{\"format\":\"png\",\"width\":800,\"height\":600}" \
            202 \
            "POST /api/v1/drawings/{id}/export - PNG async export" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            EXPORT_JOB_ID=$(echo "$png_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('job_id',''))" 2>/dev/null)
            log_info "Export job ID: $EXPORT_JOB_ID"

            # Check export status
            if [ -n "$EXPORT_JOB_ID" ]; then
                log_info "Testing export status..."
                test_get "/api/v1/drawings/exports/$EXPORT_JOB_ID/status" 200 \
                    "GET /api/v1/drawings/exports/{job_id}/status - Export status" \
                    "$ACCESS_TOKEN" > /dev/null || true
            fi
        fi

        # Export as PDF
        log_info "Testing PDF export..."
        pdf_response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$API_HOST/api/v1/drawings/$DRAWING_ID/export/pdf?page_size=A4" 2>&1)
        pdf_status=$(echo "$pdf_response" | tail -n 1)
        if [ "$pdf_status" -eq 200 ]; then
            test_pass "GET /api/v1/drawings/{id}/export/pdf - PDF export (HTTP $pdf_status)"
        else
            test_fail "GET /api/v1/drawings/{id}/export/pdf - PDF export (Expected: 200, Got: $pdf_status)"
        fi
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/drawings" 401 "GET /api/v1/drawings - No auth (401 expected)" > /dev/null || true

    # Test non-existent drawing
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/drawings/99999" 404 \
            "GET /api/v1/drawings/99999 - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test invalid export format
        test_post "/api/v1/drawings/$DRAWING_ID/export" \
            "{\"format\":\"invalid\"}" \
            400 \
            "POST /api/v1/drawings/{id}/export - Invalid format (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test create with missing required fields
        test_post "/api/v1/drawings" \
            "{}" \
            400 \
            "POST /api/v1/drawings - Missing fields (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        if [ -n "$DRAWING_ID" ]; then
            log_info "Deleting test drawing 1..."
            test_delete "/api/v1/drawings/$DRAWING_ID" 200 \
                "DELETE /api/v1/drawings/{id} - Delete drawing" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$DRAWING_ID_2" ]; then
            log_info "Deleting test drawing 2..."
            test_delete "/api/v1/drawings/$DRAWING_ID_2" 200 \
                "DELETE /api/v1/drawings/{id} - Delete second drawing" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

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
    echo "Test Summary - Drawings API"
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
