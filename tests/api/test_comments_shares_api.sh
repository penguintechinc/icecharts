#!/bin/bash

# Comments and Shares API Test Script
# Tests Comments CRUD, replies, and Drawing Shares functionality

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
USER_ID_2=""
DRAWING_ID=""
COMMENT_ID=""
REPLY_ID=""
SHARE_ID=""
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
    log_section "Starting Comments & Shares API Tests"
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
    TEST_EMAIL="test-comments-${TIMESTAMP}@example.com"
    TEST_EMAIL_2="test-commenter-${TIMESTAMP}@example.com"
    TEST_PASSWORD="Admin123"

    # Register first user (drawing owner)
    log_info "Registering test user 1: $TEST_EMAIL"
    register_response=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Comments Test User\"}" \
        201 \
        "POST /api/v1/auth/register - User 1 registration")

    if [ $? -eq 0 ]; then
        login_response=$(test_post "/api/v1/auth/login" \
            "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}" \
            200 \
            "POST /api/v1/auth/login - User 1 login")

        if [ $? -eq 0 ]; then
            ACCESS_TOKEN=$(extract_json_field "$login_response" "access_token")
            log_info "User 1 access token obtained"
        fi
    fi

    # Register second user (commenter)
    log_info "Registering test user 2: $TEST_EMAIL_2"
    register_response_2=$(test_post "/api/v1/auth/register" \
        "{\"email\":\"$TEST_EMAIL_2\",\"password\":\"$TEST_PASSWORD\",\"full_name\":\"Commenter User\"}" \
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
    # Create Test Drawing
    # ========================================
    log_section "Create Test Drawing"
    echo "=== Create Test Drawing ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        log_info "Creating test drawing..."
        drawing_response=$(test_post "/api/v1/drawings" \
            "{\"name\":\"Drawing for Comments\",\"description\":\"Test drawing\",\"content\":{\"nodes\":[],\"edges\":[]},\"visibility\":\"private\"}" \
            201 \
            "POST /api/v1/drawings - Create drawing" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            DRAWING_ID=$(echo "$drawing_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('drawing',{}).get('id',''))" 2>/dev/null)
            log_info "Created drawing with ID: $DRAWING_ID"
        fi
    fi
    echo ""

    # ========================================
    # Comments CRUD Tests
    # ========================================
    log_section "Comments CRUD Tests"
    echo "=== Comments CRUD Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$DRAWING_ID" ]; then
        # Create comment
        log_info "Testing create comment..."
        create_comment_response=$(test_post "/api/v1/drawings/$DRAWING_ID/comments" \
            "{\"content\":\"This is a test comment\",\"position_x\":100,\"position_y\":200}" \
            201 \
            "POST /api/v1/drawings/{id}/comments - Create comment" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            COMMENT_ID=$(echo "$create_comment_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('comment',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created comment with ID: $COMMENT_ID"
        fi

        # List comments
        log_info "Testing list comments..."
        test_get "/api/v1/drawings/$DRAWING_ID/comments" 200 \
            "GET /api/v1/drawings/{id}/comments - List comments" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Get comment details
        if [ -n "$COMMENT_ID" ]; then
            log_info "Testing get comment..."
            test_get "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID" 200 \
                "GET /api/v1/drawings/{id}/comments/{comment_id} - Get comment" \
                "$ACCESS_TOKEN" > /dev/null || true

            # Update comment
            log_info "Testing update comment..."
            test_put "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID" \
                "{\"content\":\"Updated comment content\"}" \
                200 \
                "PUT /api/v1/drawings/{id}/comments/{comment_id} - Update comment" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi
    fi
    echo ""

    # ========================================
    # Comment Replies Tests
    # ========================================
    log_section "Comment Replies Tests"
    echo "=== Comment Replies Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$DRAWING_ID" ] && [ -n "$COMMENT_ID" ]; then
        # Create reply
        log_info "Testing create reply..."
        reply_response=$(test_post "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID/replies" \
            "{\"content\":\"This is a reply to the comment\"}" \
            201 \
            "POST /api/v1/drawings/{id}/comments/{comment_id}/replies - Create reply" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            REPLY_ID=$(echo "$reply_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reply',{}).get('id', d.get('id','')))" 2>/dev/null)
            log_info "Created reply with ID: $REPLY_ID"
        fi

        # List replies
        log_info "Testing list replies..."
        test_get "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID/replies" 200 \
            "GET /api/v1/drawings/{id}/comments/{comment_id}/replies - List replies" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Resolve comment
        log_info "Testing resolve comment..."
        test_post "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID/resolve" \
            "{}" \
            200 \
            "POST /api/v1/drawings/{id}/comments/{comment_id}/resolve - Resolve comment" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Shares Tests
    # ========================================
    log_section "Shares Tests"
    echo "=== Shares Tests ==="

    if [ -n "$ACCESS_TOKEN" ] && [ -n "$DRAWING_ID" ] && [ -n "$USER_ID_2" ]; then
        # Create share
        log_info "Testing create share..."
        share_response=$(test_post "/api/v1/drawings/$DRAWING_ID/shares" \
            "{\"user_id\":$USER_ID_2,\"permission\":\"view\"}" \
            201 \
            "POST /api/v1/drawings/{id}/shares - Create share" \
            "$ACCESS_TOKEN")

        if [ $? -eq 0 ]; then
            SHARE_ID=$(echo "$share_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share',{}).get('id', d.get('id','')))" 2>/dev/null)
            SHARE_TOKEN=$(echo "$share_response" | grep -o '{.*}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('share',{}).get('token', d.get('token','')))" 2>/dev/null)
            log_info "Created share with ID: $SHARE_ID"
        fi

        # List shares
        log_info "Testing list shares..."
        test_get "/api/v1/drawings/$DRAWING_ID/shares" 200 \
            "GET /api/v1/drawings/{id}/shares - List shares" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Update share permission
        if [ -n "$SHARE_ID" ]; then
            log_info "Testing update share permission..."
            test_put "/api/v1/drawings/$DRAWING_ID/shares/$SHARE_ID" \
                "{\"permission\":\"edit\"}" \
                200 \
                "PUT /api/v1/drawings/{id}/shares/{share_id} - Update share" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Access via share token
        if [ -n "$SHARE_TOKEN" ]; then
            log_info "Testing access via share token..."
            test_get "/api/v1/drawings/share/$SHARE_TOKEN" 200 \
                "GET /api/v1/drawings/share/{token} - Access via token" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Get share analytics
        log_info "Testing share analytics..."
        test_get "/api/v1/drawings/$DRAWING_ID/analytics" 200 \
            "GET /api/v1/drawings/{id}/analytics - Share analytics" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Error Cases Tests
    # ========================================
    log_section "Error Cases Tests"
    echo "=== Error Cases Tests ==="

    # Test without auth
    test_get "/api/v1/drawings/$DRAWING_ID/comments" 401 \
        "GET /api/v1/drawings/{id}/comments - No auth (401 expected)" > /dev/null || true

    if [ -n "$ACCESS_TOKEN" ]; then
        # Non-existent drawing
        test_get "/api/v1/drawings/99999/comments" 404 \
            "GET /api/v1/drawings/99999/comments - Not found (404 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Non-existent comment
        if [ -n "$DRAWING_ID" ]; then
            test_get "/api/v1/drawings/$DRAWING_ID/comments/99999" 404 \
                "GET /api/v1/drawings/{id}/comments/99999 - Comment not found (404 expected)" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Create comment with missing content
        test_post "/api/v1/drawings/$DRAWING_ID/comments" \
            "{}" \
            400 \
            "POST /api/v1/drawings/{id}/comments - Missing content (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true

        # Create share with invalid user
        test_post "/api/v1/drawings/$DRAWING_ID/shares" \
            "{\"user_id\":99999,\"permission\":\"view\"}" \
            400 \
            "POST /api/v1/drawings/{id}/shares - Invalid user (400 expected)" \
            "$ACCESS_TOKEN" > /dev/null || true
    fi
    echo ""

    # ========================================
    # Cleanup
    # ========================================
    log_section "Cleanup"
    echo "=== Cleanup ==="

    if [ -n "$ACCESS_TOKEN" ]; then
        # Delete share
        if [ -n "$DRAWING_ID" ] && [ -n "$SHARE_ID" ]; then
            log_info "Deleting share..."
            test_delete "/api/v1/drawings/$DRAWING_ID/shares/$SHARE_ID" 200 \
                "DELETE /api/v1/drawings/{id}/shares/{share_id} - Delete share" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Delete comment (this should cascade delete replies)
        if [ -n "$DRAWING_ID" ] && [ -n "$COMMENT_ID" ]; then
            log_info "Deleting comment..."
            test_delete "/api/v1/drawings/$DRAWING_ID/comments/$COMMENT_ID" 200 \
                "DELETE /api/v1/drawings/{id}/comments/{comment_id} - Delete comment" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Delete drawing
        if [ -n "$DRAWING_ID" ]; then
            log_info "Deleting test drawing..."
            test_delete "/api/v1/drawings/$DRAWING_ID" 200 \
                "DELETE /api/v1/drawings/{id} - Delete drawing" \
                "$ACCESS_TOKEN" > /dev/null || true
        fi

        # Logout users
        log_info "Logging out users..."
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
    echo "Test Summary - Comments & Shares API"
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
