#!/bin/bash
# Test page/tab loads
set -e

WEB_URL="${WEB_URL:-http://localhost:3000}"

echo "=== Page Load Tests ==="
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
