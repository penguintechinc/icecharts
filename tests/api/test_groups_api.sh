#!/bin/bash

# Groups API Test Script
# Tests Groups CRUD operations and member management

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
ACCESS_TOKEN_2=""
USER_ID=""
USER_ID_2=""
GROUP_ID=""
GROUP_ID_2=""
MEMBER_ID=""

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
    # Try string format first: "field":"value"
    echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4 && return 0
    # Then try number format: "field":123
    echo "$json" | grep -o "\"$field\":[0-9]*" | cut -d':' -f2 && return 0
    # If both fail, return empty
    return 1
}

# Main Test Suite
main() {
    log_section "Starting Groups API Tests"
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

    # Use default admin for group owner (group creation requires admin/maintainer role)
    ADMIN_EMAIL="admin@localhost.local"
    ADMIN_PASSWORD="admin123"
    TEST_PASSWORD="Admin123"

    # Login as admin (group owner)
    log_info "Logging in as admin: $ADMIN_EMAIL"
    login_response=$(test_post "/api/v1/auth/login" \
        "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" \
        200 \
        "POST /api/v1/auth/login - Admin login")

    if [ $? -eq 0 ]; then
        ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
        log_info "Admin access token obtained"
    else
        log_error "Failed to login as admin"
        exit 1
    fi

    # Register second user (group member) - regular user
    TIMESTAMP=$(date +%s)
    TEST_EMAIL_2="test-groups-member-${TIMESTAMP}@example.com"
    log_info "Registering test user 2: $TEST_EMAIL_2"
    register_response_2=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL_2\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Groups Member User\"}" \
        201 \
        "POST /api/v1/auth/register - User 2 registration")

    if [ $? -eq 0 ]; then
        USER_ID_2=$(echo "$register_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('id', d.get('id','')))" 2>/dev/null)
        login_response_2=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL_2\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User 2 login")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN_2=$(extract_json_field "$login_response_2" "access_token")
            log_info "User 2 access token obtained (ID: $USER_ID_2)"
        fi
    fi
    echo ""

    # ========================================
    # Groups CRUD Tests
    # ========================================
    log_section "Groups CRUD Tests"
    echo "=== Groups CRUD Tests ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Create Group 1
        log_info "Testing group creation..."
        create_response=$(test_post "/api/v1/groups" \
            "{\"name\":\"Test Group 1\",\"description\":\"First test group\"}" \
            201 \
            "POST /api/v1/groups - Create group" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            GROUP_ID=$(echo "$create_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('group',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created group with ID: $GROUP_ID"
        fi

        # Create Group 2
        log_info "Testing creation of second group..."
        create_response_2=$(test_post "/api/v1/groups" \
            "{\"name\":\"Test Group 2\",\"description\":\"Second test group\"}" \
            201 \
            "POST /api/v1/groups - Create second group" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            GROUP_ID_2=$(echo "$create_response_2" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('group',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created second group with ID: $GROUP_ID_2"
        fi

        # List Groups
        log_info "Testing group listing..."
        test_get "/api/v1/groups" 200 "GET /api/v1/groups - List groups" "$ACCESS_TOKEN" > /dev/null || true

        # Get Group Details
        if [ -n "$GROUP_ID" ]; then
            log_info "Testing get group details..."
            test_get "/api/v1/groups/$GROUP_ID" 200 "GET /api/v1/groups/{id} - Get group" "$ACCESS_TOKEN" > /dev/null || true

            # Update Group
            log_info "Testing group update..."
            test_put "/api/v1/groups/$GROUP_ID" \
                "{\"name\":\"Updated Group Name\",\"description\":\"Updated description\"}" \
                200 \
                "PUT /api/v1/groups/{id} - Update group" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    else
        log_warn "Skipping groups tests (no access token)"
    fi
    echo ""

    # ========================================
    # Member Management Tests
    # ========================================
    log_section "Member Management Tests"
    echo "=== Member Management Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$GROUP_ID" ] && [ -n "$USER_ID_2" ]; then
        # Add Member to Group
        log_info "Testing add member to group..."
        add_member_response=$(test_post "/api/v1/groups/$GROUP_ID/members" \
            "{\"user_id\":$USER_ID_2,\"role\":\"member\"}" \
            201 \
            "POST /api/v1/groups/{id}/members - Add member" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            MEMBER_ID=$(echo "$add_member_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('member',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Added member with ID: $MEMBER_ID"
        fi

        # List Group Members
        log_info "Testing list group members..."
        test_get "/api/v1/groups/$GROUP_ID/members" 200 \
            "GET /api/v1/groups/{id}/members - List members" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Update Member Role
        if [ -n "$MEMBER_ID" ]; then
            log_info "Testing update member role..."
            test_put "/api/v1/groups/$GROUP_ID/members/$MEMBER_ID" \
                "{\"role\":\"admin\"}" \
                200 \
                "PUT /api/v1/groups/{id}/members/{member_id} - Update role" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Remove Member
            log_info "Testing remove member from group..."
            test_delete "/api/v1/groups/$GROUP_ID/members/$MEMBER_ID" 200 \
                "DELETE /api/v1/groups/{id}/members/{member_id} - Remove member" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/groups" 401 "GET /api/v1/groups - No auth (401 expected)" > /dev/null || true

    # Test non-existent group
    if [ -n "$ACCESS_TOKEN" ]; then
        test_get "/api/v1/groups/99999" 404 \
            "GET /api/v1/groups/99999 - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test create with missing required fields
        test_post "/api/v1/groups" \
            "{}" \
            400 \
            "POST /api/v1/groups - Missing name (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Test add invalid user as member
        if [ -n "$GROUP_ID" ]; then
            test_post "/api/v1/groups/$GROUP_ID/members" \
                "{\"user_id\":99999,\"role\":\"member\"}" \
                400 \
                "POST /api/v1/groups/{id}/members - Invalid user (400 expected)" \
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
        if [ -n "$GROUP_ID" ]; then
            log_info "Deleting test group 1..."
            test_delete "/api/v1/groups/$GROUP_ID" 200 \
                "DELETE /api/v1/groups/{id} - Delete group" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        if [ -n "$GROUP_ID_2" ]; then
            log_info "Deleting test group 2..."
            test_delete "/api/v1/groups/$GROUP_ID_2" 200 \
                "DELETE /api/v1/groups/{id} - Delete second group" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        log_info "Logging out test users..."
        test_post "/api/v1/auth/logout" "{}" 200 \
            "POST /api/v1/auth/logout - User 1 logout" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi

    if [ -n "$ACCESS_TOKEN_2" ]; then
        test_post "/api/v1/auth/logout" "{}" 200 \
            "POST /api/v1/auth/logout - User 2 logout" \
            "$ACCESS_TOKEN_2" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Summary
    # ========================================
    echo "========================================="
    echo "Test Summary - Groups API"
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
