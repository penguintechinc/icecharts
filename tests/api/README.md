# API Test Scripts

Comprehensive smoke tests for validating IceCharts Flask backend and WebUI containers.

## Overview

This directory contains bash-based API tests that validate all API endpoints and frontend pages:
- **Flask Backend API**: Health checks, authentication, CRUD operations for all resources
- **WebUI**: Static file serving, API proxy, SPA routing, security headers
- **Frontend Pages**: Page load verification, authentication flows

## Test Scripts

### Core API Tests

#### `test_flask_api.sh`
Tests core Flask backend REST API endpoints.
- Health & readiness checks
- User registration & login
- JWT token refresh
- Protected endpoints (profile, drawings)
- Error cases (invalid credentials, missing auth)

#### `test_flask_api_v0.2.0.sh`
Tests v0.2.0 API features including enhanced authentication and versioning.

### Feature API Tests

#### `test_drawings_api.sh`
Tests Drawings CRUD operations and exports.
- Create, read, update, delete drawings
- Export to JSON, SVG, PNG, PDF formats
- Async export job handling
- Drawing versioning

#### `test_groups_api.sh`
Tests Groups and team management.
- Create, read, update, delete groups
- Add/remove group members
- Member role management
- Group permissions

#### `test_templates_api.sh`
Tests Template management.
- Create, read, delete templates
- Use templates to create new drawings
- Template listing and filtering

#### `test_libraries_api.sh`
Tests Shape Libraries management.
- Create, read, update, delete libraries
- Add/remove shapes from libraries
- Library duplication
- Public/private library access

#### `test_profile_api.sh`
Tests User Profile operations.
- Get and update profile
- Avatar upload and removal
- Password change
- User preferences

#### `test_comments_shares_api.sh`
Tests Comments and Sharing functionality.
- Create, read, update, delete comments
- Comment replies and threading
- Resolve/unresolve comments
- Drawing shares management
- Public link generation

### Admin Tests

#### `test_admin_api.sh`
Tests Admin API endpoints.
- User management (list, create, update, delete)
- User activation/deactivation
- Dashboard statistics
- System settings management
- SSO configuration
- Audit logs

#### `test_service_accounts.sh`
Tests Service Account management.
- Create service accounts
- Token generation and rotation
- Scope management
- Service account authentication

### UI Tests

#### `test_webui.sh`
Tests the WebUI/Nginx configuration.
- Health endpoint
- Static file serving
- SPA routing fallback
- API proxy configuration
- Security headers

#### `test_frontend_pages.sh`
Tests frontend page loads.
- Public pages (login, register)
- Authenticated pages (dashboard, drawings, settings)
- Admin pages (users, statistics)
- Error handling (404, unauthorized)

### Test Runner

#### `run_all_tests.sh`
Master test runner that orchestrates the full test suite.

**Features:**
- Supports both `docker compose` (v2) and `docker-compose` (v1)
- Starts containers or uses existing running containers
- Waits for health checks
- Runs all 12 test suites sequentially
- Provides comprehensive test summary
- Optional cleanup after tests

## Prerequisites

- Docker and docker compose installed
- `curl` command-line tool
- `jq` (optional, for better JSON parsing)

## Running Tests

### Run All Tests (Recommended)

```bash
# From tests/api directory
./run_all_tests.sh

# Skip container startup (use existing containers)
./run_all_tests.sh --skip-containers

# Keep containers running after tests
./run_all_tests.sh --no-cleanup
```

### Run Specific Test Suite

```bash
# Set environment variables
export API_HOST=http://localhost:5001
export WEBUI_HOST=http://localhost:3000

# Run individual test scripts
./test_flask_api.sh
./test_drawings_api.sh
./test_groups_api.sh
./test_admin_api.sh
./test_frontend_pages.sh
```

### Verbose Mode

```bash
# Enable verbose output for debugging
./run_all_tests.sh -v

# Or set environment variable
VERBOSE=1 ./test_flask_api.sh
```

### Use Custom Docker Compose File

```bash
./run_all_tests.sh --file docker-compose.test.yml
```

## Environment Variables

### `run_all_tests.sh`
| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_FILE` | `docker-compose.yml` | Docker compose file to use |
| `VERBOSE` | `0` | Enable verbose output |
| `CLEANUP` | `1` | Cleanup containers after tests |
| `SKIP_CONTAINERS` | `0` | Skip container startup |

### Individual Test Scripts
| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `http://localhost:5001` | Flask backend URL |
| `WEBUI_HOST` | `http://localhost:3000` | WebUI URL |
| `VERBOSE` | `0` | Enable verbose output |

## Test Coverage

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| Flask API | 9 | Health, auth, protected endpoints |
| v0.2.0 API | 15+ | Enhanced auth, versioning |
| Drawings API | 20+ | CRUD, exports, versions |
| Groups API | 20+ | CRUD, members, permissions |
| Templates API | 18+ | CRUD, template usage |
| Libraries API | 25+ | CRUD, shapes, duplication |
| Profile API | 22+ | Profile, avatar, preferences |
| Comments & Shares | 25+ | Comments, replies, shares |
| Admin API | 35+ | Users, stats, settings, SSO |
| Service Accounts | 15+ | CRUD, tokens, scopes |
| WebUI | 10+ | Static files, proxy, headers |
| Frontend Pages | 25+ | Page loads, auth flows |

**Total: 200+ test cases**

## Test Output

Tests use colored output for easy reading:
- 🟢 Green (`✓`): Passed tests
- 🔴 Red (`✗`): Failed tests
- 🟡 Yellow: Warnings
- 🔵 Blue: Section headers

Example output:
```
========================================
Running Flask API Tests
========================================

=== Health Check Tests ===
✓ Health endpoint (HTTP 200)
✓ Readiness endpoint (HTTP 200)

=== Authentication Tests ===
✓ User registration (HTTP 201)
✓ User login (HTTP 200)

=========================================
Final Test Summary
=========================================
✓ Flask API Tests: PASSED
✓ Drawings API Tests: PASSED
✓ Groups API Tests: PASSED
...

Total: 12 passed, 0 failed
=========================================
```

## CI/CD Integration

These tests run in GitHub Actions after building Docker images. See `.github/workflows/docker-multiarch.yml`.

```yaml
- name: Run API Tests
  run: |
    cd tests/api
    ./run_all_tests.sh --skip-containers
```

## Troubleshooting

### Tests Fail with "Connection Refused"

```bash
# Check container status
docker compose ps

# Check health endpoints
curl http://localhost:5001/api/v1/health
curl http://localhost:3000/health
```

### View Container Logs

```bash
docker compose logs -f api   # Flask backend
docker compose logs -f web   # WebUI
docker compose logs -f       # All services
```

### Database Errors

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Verify database connection
docker compose exec api python -c "from app.models import get_db; print('OK')"
```

### Authentication Tests Fail

```bash
# Ensure dependent services are healthy
docker compose ps postgres redis

# Reset database if needed
docker compose down -v
docker compose up -d
```

## Extending Tests

To add new tests:

1. Create a new test script or add to existing one
2. Follow the existing pattern:
   ```bash
   test_get "/api/v1/endpoint" 200 "Description"
   test_post "/api/v1/endpoint" '{"data":"value"}' 201 "Description"
   ```
3. Add the script to `run_all_tests.sh` if it's a new file
4. Update this README with the new coverage

## Contributing

When modifying tests:
- Keep tests idempotent (can run multiple times)
- Use unique identifiers with timestamps
- Test both success and error cases
- Ensure proper cleanup of test data
- Update documentation for new functionality
