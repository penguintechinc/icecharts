#!/bin/bash

# Libraries API Test Script
# Tests Libraries CRUD operations and shape management

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
LIBRARY_ID=""
LIBRARY_ID_2=""
SHAPE_ID=""
SHAPE_ID_2=""
DUPLICATED_LIBRARY_ID=""

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
    log_section "Starting Libraries API Tests"
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
    TEST_EMAIL="test-libraries-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    log_info "Registering test user: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Libraries Test User\"}" \
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
    # Libraries CRUD Tests
    # ========================================
    log_section "Libraries CRUD Tests"
    echo "=== Libraries CRUD Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Create Library 1
        log_info "Testing library creation..."
        create_response=$(test_post "/api/v1/libraries" \
            "{\"name\":\"Network Icons\",\"description\":\"Icons for network diagrams\",\"category\":\"network\",\"is_public\":false}" \
            201 \
            "POST /api/v1/libraries - Create library" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            LIBRARY_ID=$(echo "$create_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('library',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created library with ID: $LIBRARY_ID"
        fi

        # Create Library 2
        log_info "Testing creation of second library..."
        create_response_2=$(test_post "/api/v1/libraries" \
            "{\"name\":\"AWS Icons\",\"description\":\"AWS service icons\",\"category\":\"cloud\",\"is_public\":true}" \
            201 \
            "POST /api/v1/libraries - Create second library" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            LIBRARY_ID_2=$(echo "$create_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('library',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created second library with ID: $LIBRARY_ID_2"
        fi

        # List Libraries
        log_info "Testing library listing..."
        test_get "/api/v1/libraries" 200 "GET /api/v1/libraries - List libraries" "$ACCESS_TOKEN" > /dev/null || true

        # List Libraries with category filter
        log_info "Testing library listing with category filter..."
        test_get "/api/v1/libraries?category=network" 200 \
            "GET /api/v1/libraries?category=network - Filter by category" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Get Library Details
        if [ -n "$LIBRARY_ID" ]; then
            log_info "Testing get library details..."
            test_get "/api/v1/libraries/$LIBRARY_ID" 200 \
                "GET /api/v1/libraries/{id} - Get library" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Update Library
            log_info "Testing library update..."
            test_put "/api/v1/libraries/$LIBRARY_ID" \
                "{\"name\":\"Updated Network Icons\",\"description\":\"Updated description\"}" \
                200 \
                "PUT /api/v1/libraries/{id} - Update library" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    else
        log_warn "Skipping libraries tests (no access token)"
    fi
    echo ""

    # ========================================
    # Shape Management Tests
    # ========================================
    log_section "Shape Management Tests"
    echo "=== Shape Management Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$LIBRARY_ID" ]; then
        # Add Shape to Library
        log_info "Testing add shape to library..."
        add_shape_response=$(test_post "/api/v1/libraries/$LIBRARY_ID/shapes" \
            "{\"name\":\"Router\",\"description\":\"Network router icon\",\"svg_content\":\"<svg><rect width='50' height='50'/></svg>\",\"tags\":[\"network\",\"router\"]}" \
            201 \
            "POST /api/v1/libraries/{id}/shapes - Add shape" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            SHAPE_ID=$(echo "$add_shape_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('shape',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Added shape with ID: $SHAPE_ID"
        fi

        # Add Second Shape
        log_info "Testing add second shape..."
        add_shape_response_2=$(test_post "/api/v1/libraries/$LIBRARY_ID/shapes" \
            "{\"name\":\"Switch\",\"description\":\"Network switch icon\",\"svg_content\":\"<svg><circle r='25'/></svg>\",\"tags\":[\"network\",\"switch\"]}" \
            201 \
            "POST /api/v1/libraries/{id}/shapes - Add second shape" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            SHAPE_ID_2=$(echo "$add_shape_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('shape',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Added second shape with ID: $SHAPE_ID_2"
        fi

        # List Shapes in Library
        log_info "Testing list library shapes..."
        test_get "/api/v1/libraries/$LIBRARY_ID/shapes" 200 \
            "GET /api/v1/libraries/{id}/shapes - List shapes" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Get Shape Details
        if [ -n "$SHAPE_ID" ]; then
            log_info "Testing get shape details..."
            test_get "/api/v1/libraries/$LIBRARY_ID/shapes/$SHAPE_ID" 200 \
                "GET /api/v1/libraries/{id}/shapes/{shape_id} - Get shape" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Update Shape
            log_info "Testing shape update..."
            test_put "/api/v1/libraries/$LIBRARY_ID/shapes/$SHAPE_ID" \
                "{\"name\":\"Updated Router\",\"description\":\"Updated router icon\"}" \
                200 \
                "PUT /api/v1/libraries/{id}/shapes/{shape_id} - Update shape" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Library Duplicate Tests
    # ========================================
    log_section "Library Duplicate Tests"
    echo "=== Library Duplicate Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$LIBRARY_ID" ]; then
        log_info "Testing library duplication..."
        duplicate_response=$(test_post "/api/v1/libraries/$LIBRARY_ID/duplicate" \
            "{\"name\":\"Duplicated Network Icons\"}" \
            201 \
            "POST /api/v1/libraries/{id}/duplicate - Duplicate library" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DUPLICATED_LIBRARY_ID=$(echo "$duplicate_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('library',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Duplicated library with ID: $DUPLICATED_LIBRARY_ID"
        fi
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/libraries" 401 "GET /api/v1/libraries - No auth (401 expected)" > /dev/null || true

    # Test non-existent library
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/libraries/99999" 404 \
            "GET /api/v1/libraries/99999 - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test create with missing required fields
        test_post "/api/v1/libraries" \
            "{}" \
            400 \
            "POST /api/v1/libraries - Missing fields (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test get non-existent shape
        if [ -n "$LIBRARY_ID" ]; then
            test_get "/api/v1/libraries/$LIBRARY_ID/shapes/99999" 404 \
                "GET /api/v1/libraries/{id}/shapes/99999 - Shape not found (404 expected)" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Delete shapes first
        if [ -n "$LIBRARY_ID" ] && [ -n "$SHAPE_ID" ]; then
            log_info "Deleting test shape 1..."
            test_delete "/api/v1/libraries/$LIBRARY_ID/shapes/$SHAPE_ID" 200 \
                "DELETE /api/v1/libraries/{id}/shapes/{shape_id} - Delete shape" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$LIBRARY_ID" ] && [ -n "$SHAPE_ID_2" ]; then
            log_info "Deleting test shape 2..."
            test_delete "/api/v1/libraries/$LIBRARY_ID/shapes/$SHAPE_ID_2" 200 \
                "DELETE /api/v1/libraries/{id}/shapes/{shape_id} - Delete second shape" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Delete libraries
        if [ -n "$DUPLICATED_LIBRARY_ID" ]; then
            log_info "Deleting duplicated library..."
            test_delete "/api/v1/libraries/$DUPLICATED_LIBRARY_ID" 200 \
                "DELETE /api/v1/libraries/{id} - Delete duplicated library" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$LIBRARY_ID" ]; then
            log_info "Deleting test library 1..."
            test_delete "/api/v1/libraries/$LIBRARY_ID" 200 \
                "DELETE /api/v1/libraries/{id} - Delete library" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$LIBRARY_ID_2" ]; then
            log_info "Deleting test library 2..."
            test_delete "/api/v1/libraries/$LIBRARY_ID_2" 200 \
                "DELETE /api/v1/libraries/{id} - Delete second library" \
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
    echo "Test Summary - Libraries API"
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
