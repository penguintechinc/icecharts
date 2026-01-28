#!/bin/bash

# Templates API Test Script
# Tests Templates CRUD operations and template usage

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
TEMPLATE_ID=""
TEMPLATE_ID_2=""
DRAWING_FROM_TEMPLATE_ID=""

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
    log_section "Starting Templates API Tests"
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
    TEST_EMAIL="test-templates-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Templates Test User\"}" \
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
    # Create Test Drawing (needed for templates)
    # ========================================
    log_section "Create Test Drawing"
    echo "=== Create Test Drawing ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        log_info "Creating test drawing for templates..."
        drawing_response=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Test Drawing for Templates\",\"description\":\"Created for template tests\",\"content\":{\"nodes\":[{\"id\":\"n1\",\"type\":\"router\"}],\"edges\":[]}}" \
            201 \
            "POST /api/v1/drawings - Create test drawing" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID=$(echo "$drawing_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created test drawing with ID: $DRAWING_ID"
        fi
    fi
    echo ""

    # ========================================
    # Templates CRUD Tests
    # ========================================
    log_section "Templates CRUD Tests"
    echo "=== Templates CRUD Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$DRAWING_ID" ]; then
        # Create Template 1
        log_info "Testing template creation..."
        create_response=$(test_post "/api/v1/templates" \
            "{\"name\":\"Test Template 1\",\"description\":\"Network diagram template\",\"category\":\"network\",\"drawing_id\":\"$DRAWING_ID\"}" \
            201 \
            "POST /api/v1/templates - Create template" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            TEMPLATE_ID=$(echo "$create_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('template',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created template with ID: $TEMPLATE_ID"
        fi

        # Create Template 2
        log_info "Testing creation of second template..."
        create_response_2=$(test_post "/api/v1/templates" \
            "{\"name\":\"Test Template 2\",\"description\":\"Flowchart template\",\"category\":\"flowchart\",\"drawing_id\":\"$DRAWING_ID\"}" \
            201 \
            "POST /api/v1/templates - Create second template" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            TEMPLATE_ID_2=$(echo "$create_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('template',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created second template with ID: $TEMPLATE_ID_2"
        fi

        # List Templates
        log_info "Testing template listing..."
        test_get "/api/v1/templates" 200 "GET /api/v1/templates - List templates" "$ACCESS_TOKEN" > /dev/null || true

        # List Templates with category filter
        log_info "Testing template listing with category filter..."
        test_get "/api/v1/templates?category=network" 200 \
            "GET /api/v1/templates?category=network - Filter by category" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Get Template Details
        if [ -n "$TEMPLATE_ID" ]; then
            log_info "Testing get template details..."
            test_get "/api/v1/templates/$TEMPLATE_ID" 200 \
                "GET /api/v1/templates/{id} - Get template" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Update Template
            log_info "Testing template update..."
            test_put "/api/v1/templates/$TEMPLATE_ID" \
                "{\"name\":\"Updated Template Name\",\"description\":\"Updated description\",\"tags\":[\"updated\",\"network\"]}" \
                200 \
                "PUT /api/v1/templates/{id} - Update template" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    else
        log_warn "Skipping templates tests (no access token)"
    fi
    echo ""

    # ========================================
    # Template Usage Tests
    # ========================================
    log_section "Template Usage Tests"
    echo "=== Template Usage Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$TEMPLATE_ID" ]; then
        # Use Template to create a new drawing
        log_info "Testing use template to create drawing..."
        use_response=$(test_post "/api/v1/templates/$TEMPLATE_ID/use" \
            "{\"name\":\"Drawing from Template\",\"description\":\"Created from test template\"}" \
            201 \
            "POST /api/v1/templates/{id}/use - Use template" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_FROM_TEMPLATE_ID=$(echo "$use_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created drawing from template with ID: $DRAWING_FROM_TEMPLATE_ID"
        fi
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/templates" 401 "GET /api/v1/templates - No auth (401 expected)" > /dev/null || true

    # Test non-existent template
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/templates/99999" 404 \
            "GET /api/v1/templates/99999 - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test create with missing required fields
        test_post "/api/v1/templates" \
            "{}" \
            400 \
            "POST /api/v1/templates - Missing fields (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test use non-existent template
        test_post "/api/v1/templates/99999/use" \
            "{\"name\":\"Test\"}" \
            404 \
            "POST /api/v1/templates/99999/use - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Delete drawing created from template
        if [ -n "$DRAWING_FROM_TEMPLATE_ID" ]; then
            log_info "Deleting drawing created from template..."
            test_delete "/api/v1/drawings/$DRAWING_FROM_TEMPLATE_ID" 200 \
                "DELETE /api/v1/drawings/{id} - Delete drawing from template" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$TEMPLATE_ID" ]; then
            log_info "Deleting test template 1..."
            test_delete "/api/v1/templates/$TEMPLATE_ID" 200 \
                "DELETE /api/v1/templates/{id} - Delete template" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$TEMPLATE_ID_2" ]; then
            log_info "Deleting test template 2..."
            test_delete "/api/v1/templates/$TEMPLATE_ID_2" 200 \
                "DELETE /api/v1/templates/{id} - Delete second template" \
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
    echo "Test Summary - Templates API"
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
