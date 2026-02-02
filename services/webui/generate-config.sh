#!/bin/sh
# Generate runtime config for frontend
cat > /usr/share/nginx/html/config.js << EOF
window.RUNTIME_CONFIG = {
  API_URL: "${VITE_API_URL:-}",
  API_BASE_PATH: "${VITE_API_BASE_PATH:-/api/v1}"
};
EOF
