#!/bin/bash
# Test page/tab loads for both alpha (local) and beta (k8s) environments
set -e

# Environment detection
TEST_ENV="${TEST_ENV:-alpha}"

if [ "$TEST_ENV" = "beta" ]; then
  # Beta environment (k8s cluster at icecharts.penguintech.io)
  WEB_URL="${WEB_URL:-https://icecharts.penguintech.io}"
else
  # Alpha environment (local docker-compose)
  WEB_URL="${WEB_URL:-http://localhost:3000}"
fi

echo "=== Page Load Smoke Tests ==="
echo "Environment: $TEST_ENV"
echo "Target: $WEB_URL"
echo ""

PAGES="/ /login /register /drawings /playbooks /collections /settings"

for PAGE in $PAGES; do
  echo -n "   $PAGE: "
  STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$WEB_URL$PAGE" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    echo "✓ OK"
  else
    echo "✗ Failed ($STATUS)"
  fi
done

echo ""
echo "=== Page Tests Complete ==="
