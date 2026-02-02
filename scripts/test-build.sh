#!/bin/bash
# Test frontend build
set -e

echo "=== Frontend Build Test ==="
cd "$(dirname "$0")/../services/webui"

echo "Running TypeScript check and Vite build..."
npm run build

echo ""
echo "✓ Build passed successfully"
