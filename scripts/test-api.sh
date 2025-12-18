#!/bin/bash
# Test API endpoints
set -e

API_URL="${API_URL:-http://localhost:5001}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@localhost}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"

echo "=== API Tests ==="
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

echo -n "   GET /collections: "
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/api/v1/collections" \
  -H "Authorization: Bearer $TOKEN")
[ "$STATUS" = "200" ] && echo "✓ OK" || echo "✗ Failed ($STATUS)"

echo ""
echo "=== API Tests Complete ==="
