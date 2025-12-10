# IceCharts Testing Guide

Comprehensive testing documentation for IceCharts backend and frontend services.

## Table of Contents

- [Overview](#overview)
- [Flask Backend Tests](#flask-backend-tests)
- [WebUI Tests](#webui-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Running Tests Locally](#running-tests-locally)
- [Test Coverage](#test-coverage)
- [Best Practices](#best-practices)

## Overview

IceCharts uses a comprehensive multi-stage testing approach:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Linting & Code Quality**: Automated code style and quality checks
- **Docker Build Tests**: Multi-stage Docker builds with dedicated test stages
- **CI/CD Pipeline**: GitHub Actions for automated testing

### Test Structure

```
services/
├── flask-backend/
│   ├── tests/
│   │   ├── conftest.py          # Pytest fixtures and configuration
│   │   ├── test_auth.py         # Authentication endpoint tests
│   │   ├── test_drawings.py     # Drawing CRUD tests
│   │   ├── test_groups.py       # Group management tests
│   │   └── test_permissions.py  # RBAC and permission tests
│   └── app/
│       └── ... (source code)
│
└── webui/
    ├── tests/
    │   ├── setup.ts             # Vitest configuration
    │   ├── components/
    │   │   └── Canvas.test.tsx  # Canvas component tests
    │   └── hooks/
    │       └── useAuth.test.ts  # Auth hook tests
    └── src/
        └── ... (source code)
```

## Flask Backend Tests

### Test Files

#### conftest.py
Pytest configuration and shared fixtures for all Flask tests:

```python
# Available fixtures:
- app              # Flask test application
- client           # Flask test client
- db               # Database instance
- test_user        # Default test user
- test_admin       # Default admin user
- auth_headers     # JWT auth headers for requests
- admin_auth_headers # Admin JWT auth headers
- valid_jwt_token  # Valid JWT token
- expired_jwt_token # Expired JWT token for testing
- refresh_token    # Valid refresh token
```

#### test_auth.py
Authentication and authorization tests:

- User registration (success, validation, duplicates)
- Login (success, invalid credentials, missing fields)
- Logout and session management
- JWT token refresh and validation
- Token expiration and revocation
- Password reset functionality
- OAuth integration

**Test Classes:**
- `TestAuthRegister` - User registration tests
- `TestAuthLogin` - Login endpoint tests
- `TestAuthLogout` - Logout functionality
- `TestAuthJWTRefresh` - Token refresh tests
- `TestAuthTokenValidation` - Token validation tests
- `TestAuthPasswordReset` - Password reset tests
- `TestAuthRoleBasedAccess` - Role-based access control

#### test_drawings.py
Drawing CRUD operations and management:

- Creating drawings
- Retrieving drawings (single, list, pagination)
- Updating drawing content and metadata
- Deleting drawings
- Version history and restore
- Drawing search functionality
- Drawing sharing and permissions

**Test Classes:**
- `TestDrawingCreate` - Creation tests
- `TestDrawingRead` - Retrieval tests
- `TestDrawingUpdate` - Update tests
- `TestDrawingDelete` - Deletion tests
- `TestDrawingVersionHistory` - Version history tests
- `TestDrawingSearch` - Search functionality
- `TestDrawingSharing` - Sharing and collaboration

#### test_groups.py
Group management and organization:

- Creating groups
- Retrieving groups (single, list, pagination)
- Updating group properties
- Deleting groups
- Managing group members
- Group and drawing relationships

**Test Classes:**
- `TestGroupCreate` - Group creation
- `TestGroupRead` - Group retrieval
- `TestGroupUpdate` - Group updates
- `TestGroupDelete` - Group deletion
- `TestGroupMembers` - Member management
- `TestGroupDrawings` - Group/drawing relationships

#### test_permissions.py
Role-based access control (RBAC) and permissions:

- Admin permissions (user management, all drawings)
- Maintainer permissions (drawing management, sharing)
- Viewer permissions (read-only access)
- Resource ownership (own vs. others' resources)
- Group permissions
- Permission denial and error handling

**Test Classes:**
- `TestAdminPermissions` - Admin role tests
- `TestMaintainerPermissions` - Maintainer role tests
- `TestViewerPermissions` - Viewer role tests
- `TestResourceOwnershipPermissions` - Ownership-based access
- `TestGroupPermissions` - Group-level permissions
- `TestDrawingPermissions` - Drawing sharing and permissions
- `TestPermissionDenial` - Permission denial scenarios

### Running Flask Tests

#### Quick Test Run
```bash
# Run all Flask tests
make test-flask

# Run with coverage report
make test-flask-cov
```

#### Manual Testing
```bash
# Navigate to Flask backend
cd services/flask-backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test class
pytest tests/test_auth.py::TestAuthLogin -v

# Run specific test
pytest tests/test_auth.py::TestAuthLogin::test_login_success -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run with specific markers
pytest tests/ -m "auth" -v

# Run in watch mode (requires pytest-watch)
ptw tests/
```

#### Environment Variables
```bash
export FLASK_ENV=testing
export TESTING=true
export DATABASE_URL="sqlite:///:memory:"
export JWT_SECRET_KEY=test-secret-key
export SECRET_KEY=test-secret-key
export REDIS_URL=redis://localhost:6379/0
```

## WebUI Tests

### Test Files

#### setup.ts
Vitest configuration and setup for all WebUI tests:

- Global mocks (fetch, localStorage, sessionStorage)
- Custom matchers for common assertions
- Window.matchMedia mock for responsive testing

#### tests/components/Canvas.test.tsx
Canvas component tests:

- Component rendering and display
- User interactions (save, drag, etc.)
- Accessibility compliance
- Props handling
- Edge cases and error conditions

**Test Suites:**
- Rendering - Component output tests
- Interactions - User input handling
- Accessibility - A11y compliance
- Props - Prop validation and updates
- Edge cases - Error scenarios

#### tests/hooks/useAuth.test.ts
Authentication hook tests:

- Initial state and setup
- Login functionality
- Logout and cleanup
- Token refresh
- State persistence
- Error handling
- Multiple hook instances

**Test Suites:**
- Initial State - Hook setup
- Login - Authentication flow
- Logout - Cleanup behavior
- Token Refresh - Token management
- State Updates - State synchronization
- Error Handling - Error scenarios
- Persistence - localStorage handling
- Multiple Instances - Independent state

### Running WebUI Tests

#### Quick Test Run
```bash
# Run all WebUI tests
make test-webui

# Run with coverage
make test-webui-cov

# Run in watch mode
make test-webui-watch
```

#### Manual Testing
```bash
# Navigate to WebUI
cd services/webui

# Install dependencies first
npm ci

# Run tests once
npm test -- --run

# Run in watch mode (recommended for development)
npm test

# Run with coverage
npm test -- --run --coverage

# Open UI dashboard
npm run test:ui

# Run specific test file
npm test -- tests/components/Canvas.test.tsx

# Run tests matching pattern
npm test -- --grep "Canvas"
```

#### Environment Variables
```bash
export VITE_API_URL=http://localhost:5000
export NODE_ENV=test
```

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/test-and-lint.yml` workflow provides:

#### 1. Changes Detection
Intelligently skip jobs if no relevant files changed:
- Flask changes trigger Flask tests/linting
- WebUI changes trigger WebUI tests/linting

#### 2. Flask Backend Pipeline
```
flask-lint (parallel)
├── Black (code formatting)
├── isort (import sorting)
├── flake8 (linting)
└── mypy (type checking)

flask-test (parallel, matrix: 3.12, 3.13)
├── pytest with coverage
├── Coverage upload to Codecov
└── Test artifact upload
```

#### 3. WebUI Pipeline
```
webui-lint (parallel)
├── ESLint
└── TypeScript type check

webui-test (parallel, matrix: 18, 20, 22)
├── Vitest with coverage
├── Application build
├── Coverage upload to Codecov
└── Build artifact upload
```

#### 4. Docker Build Tests
- Flask backend test stage
- Flask backend lint stage
- WebUI test stage
- WebUI lint stage

#### 5. Test Summary
- Aggregates all results
- Comments on PRs with test status
- Fails workflow if any required test fails

### Workflow Triggers

Tests run on:
- Push to `main` or `develop` branches
- Feature branch pushes (`feature/*`)
- Pull requests to `main` or `develop`
- Daily schedule (2 AM UTC)

## Running Tests Locally

### Complete Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd IceCharts

# 2. Install dependencies
make setup

# 3. Start databases
make dev-db

# 4. Run all tests
make test
```

### Flask Backend Only

```bash
cd services/flask-backend

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### WebUI Only

```bash
cd services/webui

# Install dependencies
npm ci

# Run tests
npm test -- --run

# Run with coverage
npm test -- --run --coverage
```

### Docker Testing

Build and test within Docker containers:

```bash
# Test Flask backend in Docker
docker build --target test -t icecharts-flask-test services/flask-backend
docker run icecharts-flask-test

# Test WebUI in Docker
docker build --target test -t icecharts-webui-test services/webui
docker run icecharts-webui-test

# Lint Flask backend in Docker
docker build --target lint -t icecharts-flask-lint services/flask-backend
docker run icecharts-flask-lint
```

## Test Coverage

### Coverage Reports

#### Flask Backend
Coverage reports are generated after running tests:

```bash
# View coverage report
cd services/flask-backend
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

**Coverage Goals:**
- Overall: >80% coverage
- Critical paths (auth, permissions): >95% coverage
- Models and core logic: >90% coverage

#### WebUI
Coverage reports after test runs:

```bash
# View coverage report
cd services/webui
npm test -- --run --coverage
open coverage/index.html
```

**Coverage Goals:**
- Overall: >70% coverage
- Components: >80% coverage
- Hooks: >85% coverage

### Codecov Integration

Coverage reports are automatically uploaded to Codecov:
- Flask tests use `coverage.xml`
- WebUI tests use `coverage/coverage-final.json`
- View coverage at: https://codecov.io/gh/penguintechinc/icecharts

## Best Practices

### Writing Tests

#### Naming Conventions
```python
# Test files: test_<module>.py
# Test classes: Test<Feature>
# Test methods: test_<scenario>

# Example
class TestDrawingCreate:
    def test_create_drawing_success(self):
        # Arrange
        # Act
        # Assert
```

#### Arrange-Act-Assert Pattern
```python
def test_create_drawing_success(self, client, auth_headers):
    # Arrange - Setup test data
    drawing_data = {
        "name": "Test Drawing",
        "description": "A test",
        "canvas_data": {"nodes": [], "edges": []},
    }

    # Act - Execute test action
    response = client.post(
        "/api/v1/drawings",
        headers=auth_headers,
        json=drawing_data,
    )

    # Assert - Verify results
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["name"] == "Test Drawing"
```

#### Use Fixtures
```python
# Instead of repeated setup
def test_with_fixture(self, test_user, auth_headers):
    # test_user and auth_headers already available
    response = client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code == 200
```

### Testing Principles

1. **Isolation**: Tests should be independent and not rely on execution order
2. **Clarity**: Test names should clearly describe what is being tested
3. **Coverage**: Test both happy paths and error cases
4. **Mocking**: Mock external dependencies (APIs, databases, etc.)
5. **Speed**: Tests should run quickly; use in-memory databases
6. **Determinism**: Tests should produce consistent results

### Common Testing Patterns

#### Testing Authentication
```python
def test_protected_endpoint(self, client, auth_headers):
    response = client.get("/api/v1/protected", headers=auth_headers)
    assert response.status_code == 200

def test_protected_without_auth(self, client):
    response = client.get("/api/v1/protected")
    assert response.status_code == 401
```

#### Testing Error Cases
```python
def test_invalid_input(self, client, auth_headers):
    response = client.post(
        "/api/v1/drawings",
        headers=auth_headers,
        json={"name": ""},  # Invalid: empty name
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data
```

#### Testing Permissions
```python
def test_user_cannot_delete_others_drawing(self, client, auth_headers):
    # Other user's drawing created
    # Attempt delete with different user's auth
    response = client.delete(
        f"/api/v1/drawings/{other_user_drawing_id}",
        headers=auth_headers,
    )
    assert response.status_code in [403, 401, 404]
```

### Debugging Tests

#### Verbose Output
```bash
# Flask
pytest tests/ -vv -s  # -s shows print statements

# WebUI
npm test -- --reporter=verbose
```

#### Break on Failure
```bash
# Flask - stop on first failure
pytest tests/ -x

# WebUI
npm test -- --bail
```

#### Specific Test Execution
```bash
# Flask - run single test
pytest tests/test_auth.py::TestAuthLogin::test_login_success -vv

# WebUI
npm test -- tests/components/Canvas.test.tsx
```

### Performance Optimization

#### Parallel Execution
Tests run in parallel in CI/CD pipeline using matrix strategy:
- Flask: Python 3.12, 3.13
- WebUI: Node 18, 20, 22

#### Test Order
Test order doesn't matter due to isolation but can be optimized:
```bash
# Run fastest tests first (help catch issues early)
pytest --ff tests/
```

#### Skip Slow Tests (when needed)
```python
@pytest.mark.slow
def test_heavy_operation(self):
    pass

# Run without slow tests
pytest tests/ -m "not slow"
```

## Troubleshooting

### Flask Tests

#### Import Errors
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install in development mode
pip install -e services/flask-backend
```

#### Database Connection Issues
```bash
# Ensure test database is using SQLite in-memory
export DATABASE_URL="sqlite:///:memory:"

# Or use test PostgreSQL
docker-compose up -d postgres
pytest tests/
```

### WebUI Tests

#### Module Resolution Issues
```bash
# Clear node_modules and reinstall
rm -rf services/webui/node_modules
cd services/webui && npm ci
```

#### Test Timeout
```bash
# Increase timeout for slow tests
npm test -- --testTimeout=10000
```

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Flask Testing Guide](https://flask.palletsprojects.com/testing/)
- [React Testing Library](https://testing-library.com/react)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
