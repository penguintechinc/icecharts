# API Test Scripts

Standalone API test scripts for validating IceCharts Flask backend and WebUI containers.

## Overview

This directory contains bash-based API tests that validate:
- **Flask Backend API**: Health checks, authentication, protected endpoints
- **WebUI/Nginx**: Static file serving, API proxy, security headers

## Test Scripts

### 1. `test_flask_api.sh`
Tests the Flask backend REST API endpoints.

**Endpoints tested:**
- Health & readiness checks
- User registration & login
- JWT token refresh
- Protected endpoints (profile, drawings)
- Error cases (invalid credentials, missing auth)

### 2. `test_webui.sh`
Tests the WebUI/Nginx configuration.

**Tests include:**
- Health endpoint
- Static file serving (index.html)
- SPA routing (fallback to index.html)
- API proxy configuration
- Security headers (CSP, X-Frame-Options, etc.)
- Cache headers

### 3. `run_all_tests.sh`
Master test runner that orchestrates the full test suite.

**Features:**
- Starts containers via docker-compose
- Waits for health checks
- Runs all API tests sequentially
- Provides comprehensive test summary
- Cleans up containers after tests

## Prerequisites

- Docker and docker-compose installed
- `curl` command-line tool
- `jq` (optional, for better JSON parsing)

## Running Tests

### Run All Tests (Recommended)

```bash
# From project root
cd tests/api
./run_all_tests.sh
```

### Run Specific Test Suite

```bash
# Flask API tests only (requires running containers)
API_HOST=http://localhost:5001 ./test_flask_api.sh

# WebUI tests only (requires running containers)
WEBUI_HOST=http://localhost:3000 ./test_webui.sh
```

### Verbose Mode

```bash
# Enable verbose output for debugging
./run_all_tests.sh --verbose

# Or set environment variable
VERBOSE=1 ./test_flask_api.sh
```

### Keep Containers Running After Tests

```bash
# Don't cleanup containers (useful for debugging)
./run_all_tests.sh --no-cleanup
```

### Use Custom Docker Compose File

```bash
# Use a specific compose file
./run_all_tests.sh --file docker-compose.test.yml
```

## Environment Variables

### `run_all_tests.sh`
- `COMPOSE_FILE`: Docker compose file to use (default: `docker-compose.yml`)
- `VERBOSE`: Enable verbose output (default: `0`)
- `CLEANUP`: Cleanup containers after tests (default: `1`)

### `test_flask_api.sh`
- `API_HOST`: Flask backend URL (default: `http://localhost:5001`)
- `VERBOSE`: Enable verbose output (default: `0`)

### `test_webui.sh`
- `WEBUI_HOST`: WebUI URL (default: `http://localhost:3000`)
- `API_HOST`: Backend API URL (default: `http://localhost:5001`)
- `VERBOSE`: Enable verbose output (default: `0`)

## Test Output

Tests use colored output for easy reading:
- 🟢 Green: Passed tests and info messages
- 🔴 Red: Failed tests and error messages
- 🟡 Yellow: Warnings

Example output:
```
========================================
Starting Flask Backend API Tests
========================================

=== Health Check Tests ===
✓ Health endpoint (HTTP 200)
✓ Readiness endpoint (HTTP 200)

=== Authentication Tests ===
✓ User registration (HTTP 201)
✓ User login (HTTP 200)
✓ Token refresh (HTTP 200)

=== Protected Endpoint Tests ===
✓ Get user profile (authenticated) (HTTP 200)
✓ List user drawings (authenticated) (HTTP 200)

=== Error Case Tests ===
✓ Get profile without auth (HTTP 401)
✓ Login with invalid credentials (HTTP 401)

=========================================
Test Summary
=========================================
Passed: 10
Failed: 0
Total:  10
=========================================
```

## CI/CD Integration

These tests are designed to run in GitHub Actions. See `.github/workflows/docker-multiarch.yml` for integration example.

The tests are executed after building multi-arch Docker images to validate that containers are functioning correctly.

## Troubleshooting

### Tests Fail with "Connection Refused"

Ensure containers are running:
```bash
docker-compose ps
```

Check health status:
```bash
curl http://localhost:5001/api/v1/health
curl http://localhost:3000/health
```

### View Container Logs

```bash
# Flask backend
docker-compose logs -f api

# WebUI
docker-compose logs -f web

# All services
docker-compose logs -f
```

### Tests Timeout During Startup

Increase the wait time by editing the scripts or check for resource constraints:
```bash
# Check Docker resources
docker stats
```

### Authentication Tests Fail

Ensure PostgreSQL and Redis are healthy:
```bash
docker-compose ps postgres redis
```

Check database connectivity:
```bash
docker-compose exec api python -c "from app.models import get_db; print(get_db())"
```

## Extending Tests

To add new tests:

1. Add test functions to the appropriate script
2. Follow the existing pattern:
   ```bash
   test_get "/api/v1/new-endpoint" 200 "Test description"
   ```
3. Update the test counters for proper summary

## Contributing

When modifying tests:
- Keep tests idempotent (can run multiple times)
- Use unique identifiers for test data (e.g., timestamps)
- Ensure proper cleanup
- Test both success and error cases
- Update this README with any new functionality
