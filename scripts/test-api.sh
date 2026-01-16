#!/bin/bash
# Test API endpoints for both alpha (local) and beta (k8s) environments
set -e

# Environment detection
TEST_ENV="${TEST_ENV:-alpha}"

if [ "$TEST_ENV" = "beta" ]; then
  # Beta environment (k8s cluster at icecharts.penguintech.io)
  API_URL="${API_URL:-https://icecharts.penguintech.io}"
  ADMIN_EMAIL="${ADMIN_EMAIL:-admin@localhost.local}"
  ADMIN_PASS="${ADMIN_PASS:-admin123}"
else
  # Alpha environment (local docker-compose)
  API_URL="${API_URL:-http://localhost:5001}"
  ADMIN_EMAIL="${ADMIN_EMAIL:-admin@localhost.local}"
  ADMIN_PASS="${ADMIN_PASS:-admin123}"
fi

echo "=== API Smoke Tests ==="
echo "Environment: $TEST_ENV"
echo "Target: $API_URL"
echo ""

# Health check
echo "1. Health endpoint..."
curl -sf "$API_URL/api/v1/health" | head -c 200
echo ""
echo "   ✓ Health OK"
echo ""

# Login
echo "2. Authentication..."
TOKEN=$(curl -sf -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "   ✗ Login failed"
  exit 1
fi
echo "   ✓ Login OK (token obtained)"
echo ""

# Test protected endpoints
echo "3. Protected endpoints..."

echo -n "   GET /drawings: "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/api/v1/drawings" \
  -H "Authorization: Bearer $TOKEN")
[ "$STATUS" = "200" ] && echo "✓ OK" || echo "✗ Failed ($STATUS)"

echo -n "   GET /playbooks: "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/api/v1/playbooks" \
  -H "Authorization: Bearer $TOKEN")
[ "$STATUS" = "200" ] && echo "✓ OK" || echo "✗ Failed ($STATUS)"

echo ""
echo "=== API Tests Complete ==="
