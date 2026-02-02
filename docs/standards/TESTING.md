<<<<<<< HEAD
# Testing Guide: Trust But Verify

Part of [Development Standards](../STANDARDS.md)

Your code shipped to production needs confidence. Testing is how we build it. Here's your friendly guide to writing tests that actually work—and catching bugs before users do.

## The Testing Pyramid

Think of testing like a pyramid. Test plenty at the bottom (cheap, fast), fewer in the middle (more complex), and only critical paths at the top (expensive, slow).

```
        /\
       /E2E\           Phase 3: Live deployment testing
      /---\
     /Integration\    Phase 2: CI/CD pipeline validation
    /--------\
   /Unit Tests\      Phase 1: Pre-commit local tests
  /____________\
```

Each layer validates different aspects—unit tests catch code bugs, integration tests catch coordination issues, E2E tests catch user workflow problems. You need all three.

### Phase 1: Pre-Commit (Local Development)

**The Gatekeeper**: Runs on your machine before code hits the repo. Think of it as your final self-check before hitting "commit."

- **When**: Every commit (no exceptions!)
- **Where**: Your local dev machine
- **Time**: <2 minutes total
- **Location**: `tests/smoketests/`

**What gets tested**:
- Does the code compile/build?
- Does it actually run?
- Do critical API endpoints respond?
- Does the UI load without crashing?

=======
# Testing Standards

Part of [Development Standards](../STANDARDS.md)

## Testing Phases

Testing is organized into three distinct phases aligned with the development workflow:

### Phase 1: Pre-Commit (Local Development)

**Location**: `tests/smoketests/`
**When**: Before every commit on developer machine
**Duration**: <2 minutes
**Purpose**: Fast validation before code enters repository

**What Runs**:
- Smoke tests (build, run, basic functionality)
- Quick sanity checks
- End-to-end build and runtime verification

**Execution**:
>>>>>>> origin/v1.0.X
```bash
# Run via pre-commit script
./scripts/pre-commit/pre-commit.sh

<<<<<<< HEAD
# Or just the smoke tests directly
=======
# Or manually run smoke tests
>>>>>>> origin/v1.0.X
./tests/smoketests/run-all.sh
```

**Requirements**:
- MUST pass before committing
<<<<<<< HEAD
=======
- Runs on developer's local machine
>>>>>>> origin/v1.0.X
- Uses local Docker containers
- Fast feedback loop (<2 min)

### Phase 2: CI/CD Pipeline (GitHub Actions)

<<<<<<< HEAD
**The Automated Enforcer**: Runs automatically when you push to GitHub. Catches what you missed locally.

- **When**: Every push/PR
- **Where**: GitHub's servers
- **Time**: 5-15 minutes
- **Location**: `.github/workflows/`

**What gets tested**:
- Linters (is code styled correctly?)
- Unit tests (do components work in isolation?)
- Build verification (does it compile for multiple architectures?)
- Security scans (any vulnerabilities?)
- Code quality (does CodeQL approve?)

```yaml
# .github/workflows/ci.yml (example flow)
=======
**Location**: `.github/workflows/`
**When**: On every push/PR to GitHub
**Duration**: 5-15 minutes
**Purpose**: Comprehensive static validation

**What Runs**:
- Linters (flake8, eslint, golangci-lint, etc.)
- Unit tests (all languages)
- Compilation/build verification
- Security scans (gosec, bandit, npm audit, Trivy)
- Code quality checks (CodeQL)
- Multi-arch builds (amd64, arm64)

**Execution**: Automated via GitHub Actions

**Characteristics**:
- **Static analysis only** - no live deployment
- Runs in isolated GitHub Actions runners
- No external dependencies (databases, services)
- Mocked/stubbed external services
- Deterministic and repeatable
- Produces build artifacts (container images)

**Example Workflow Steps**:
```yaml
# .github/workflows/ci.yml
>>>>>>> origin/v1.0.X
jobs:
  test:
    steps:
      - name: Lint
        run: make lint

      - name: Unit Tests
        run: make test-unit

      - name: Build
        run: make docker-build

      - name: Security Scan
        run: trivy image app:latest
```

<<<<<<< HEAD
**Characteristics**:
- Static analysis only (no real deployment)
- No access to live databases
- Deterministic and reproducible
- Creates build artifacts for distribution

### Phase 3: Deployment & Live Testing (Kubernetes)

**The Final Validator**: Confirms your app actually works in production before users see it.

- **When**: After deployment to staging/production
- **Where**: Live Kubernetes cluster
- **Time**: 5-30 minutes
- **Location**: `tests/deployment/` and `tests/live/`

**What gets tested**:
- Are pods running and healthy?
- Can services communicate?
- Do real database operations work?
- Do complete user workflows succeed?
- Does the system handle expected load?

```bash
# Run from your machine to troubleshoot a live deployment
./tests/deployment/validate-k8s-deployment.sh
```

**Example flow**:
=======
### Phase 3: Deployment & Live Testing (K8s)

**Location**: `tests/deployment/` and `tests/live/`
**When**: Post-deployment validation
**Duration**: Variable (5-30 minutes)
**Purpose**: Verify live deployment in Kubernetes

**What Runs**:
- Deployment validation (pods running, services accessible)
- Live integration tests (real services, databases)
- End-to-end workflows (full system)
- Performance/load testing (optional)
- Health check verification

**Execution**:
```bash
# From developer machine (troubleshooting)
./tests/deployment/validate-k8s-deployment.sh

# Eventually in release CI/CD workflow (future)
# .github/workflows/release.yml
```

**Characteristics**:
- Tests against **live Kubernetes deployment**
- Real databases, services, and infrastructure
- Can be run from developer machine for troubleshooting
- Validates actual deployed state
- Currently manual, eventually automated in release workflow

**Use Cases**:
1. **Developer Troubleshooting**: Run from local machine to validate deployed app
2. **Manual QA**: Validate staging/beta deployments
3. **Future CI/CD**: Will be integrated into release workflow

**Example Deployment Test**:
>>>>>>> origin/v1.0.X
```bash
#!/bin/bash
# tests/deployment/validate-k8s-deployment.sh

<<<<<<< HEAD
echo "Validating Kubernetes Deployment..."
=======
echo "=== Validating K8s Deployment ==="
>>>>>>> origin/v1.0.X

# Check pods are running
kubectl get pods -n myapp | grep Running

# Check services are accessible
kubectl get svc -n myapp

<<<<<<< HEAD
# Test the live API
=======
# Test live API endpoint
>>>>>>> origin/v1.0.X
curl -f https://myapp.penguintech.io/healthz

# Run live integration tests
kubectl exec -n myapp deploy/flask-backend -- pytest tests/live/
```

<<<<<<< HEAD
### Quick Reference: Three-Phase Strategy

| Phase | Timing | Location | Speed | Focus |
|-------|--------|----------|-------|-------|
| Phase 1: Pre-Commit | Before you commit | Your machine | <2 min | Build, run, smoke tests |
| Phase 2: CI/CD | On push/PR | GitHub | 5-15 min | Linting, units, security |
| Phase 3: Deployment | Post-deploy | K8s cluster | 5-30 min | Live integration, E2E |

## Testing Requirements

### Smoke Tests (MANDATORY): Your Safety Net

**Smoke tests are your safety net.** Before every commit, run them to catch breaking changes in seconds. Think of smoke tests as asking: "Does this still work at all?"

**What smoke tests verify**:
1. Build succeeds (no compile errors)
2. Container starts (no runtime crashes)
3. Health checks pass (API is alive)
4. Core endpoints respond (API contracts intact)
5. Pages load (UI renders without 500 errors)

#### Setting Up Your First Smoke Test

**Directory structure** (one smoke test per container):
```
tests/smoketests/
├── flask-backend.sh       # Your Flask API smoke test
├── go-backend.sh          # Your Go service smoke test
├── webui.sh               # Your React UI smoke test
└── run-all.sh             # Runs everything at once
```

**Each script lives at**: `tests/smoketests/{your-service}.sh`

**What each smoke test needs to check**:
1. ✓ Container builds without errors
2. ✓ Container starts and stays running
3. ✓ Health endpoint returns 200 OK
4. ✓ Basic unit tests pass inside the container
5. ✓ Key API endpoints are reachable
6. ✓ UI pages load without 500 errors (if applicable)

#### Writing Your First Smoke Test

**Flask Backend example** - `tests/smoketests/flask-backend.sh`
=======
### Summary: Three-Phase Testing Strategy

| Phase | When | Where | Duration | Focus | Deployment |
|-------|------|-------|----------|-------|------------|
| **Phase 1: Pre-Commit** | Before commit | Dev machine | <2 min | Smoke tests, quick validation | Local Docker |
| **Phase 2: CI/CD** | On push/PR | GitHub Actions | 5-15 min | Linters, unit tests, builds, static analysis | No deployment |
| **Phase 3: Deployment** | Post-deploy | K8s cluster | 5-30 min | Live integration, E2E, performance | K8s deployment |

## Testing Requirements

### Smoke Tests (MANDATORY)

**CRITICAL: Smoke tests are REQUIRED before every commit**

Smoke tests verify basic functionality: build, run, API health, page/tab loads. These are quick validation tests (<2 minutes) that catch critical regressions.

#### Smoke Test Structure

**Standard Location:** `{PROJECT_ROOT}/tests/smoketests/{container_name}.sh`

Each container MUST have a corresponding smoke test script at this standardized location. Scripts can link to or pull in other test files from anywhere in the repo, but the entry point is always standardized.

**Example Structure:**
```
tests/
├── smoketests/
│   ├── flask-backend.sh      # Flask backend smoke tests
│   ├── go-backend.sh          # Go backend smoke tests
│   ├── webui.sh               # WebUI smoke tests
│   └── run-all.sh             # Runs all smoke tests
├── unit/                      # Unit tests (by language/service)
├── integration/               # Integration tests
└── e2e/                       # End-to-end tests
```

#### Smoke Test Requirements

Each smoke test script MUST verify:

1. **Build Verification**
   - Container builds successfully
   - No compilation errors
   - Dependencies resolve correctly

2. **Runtime Verification**
   - Container starts without errors
   - Process runs and doesn't crash
   - Listens on expected ports

3. **Unit Test Execution**
   - Basic unit tests pass
   - Core functionality validates
   - No critical failures

4. **Integration Test Execution**
   - Service-to-service communication works
   - Database connectivity successful
   - API contracts valid

5. **Page/Tab Load Tests** (for WebUI)
   - Main pages load without errors
   - All tabs/sections render
   - No JavaScript console errors
   - API calls to backend succeed

#### Example Smoke Test Scripts

**Flask Backend:** `tests/smoketests/flask-backend.sh`
>>>>>>> origin/v1.0.X
```bash
#!/bin/bash
set -e

echo "=== Flask Backend Smoke Test ==="

# 1. Build verification
echo "Building container..."
docker build -t flask-backend:test ./services/flask-backend

# 2. Run container
echo "Starting container..."
CONTAINER_ID=$(docker run -d \
  -e DB_TYPE=sqlite \
  -e DB_NAME=test.db \
  flask-backend:test)

# Wait for startup
sleep 5

# 3. Health check
echo "Checking health endpoint..."
docker exec $CONTAINER_ID python3 -c "
import http.client
conn = http.client.HTTPConnection('localhost', 5000)
conn.request('GET', '/healthz')
r = conn.getresponse()
if r.status != 200:
    raise Exception(f'Health check failed: {r.status}')
print('✓ Health check passed')
"

# 4. Run unit tests inside container
echo "Running unit tests..."
docker exec $CONTAINER_ID pytest tests/unit -v

# 5. Run basic integration tests
echo "Running integration tests..."
docker exec $CONTAINER_ID pytest tests/integration/test_api_basic.py -v

# 6. API endpoint smoke tests
echo "Testing API endpoints..."
docker exec $CONTAINER_ID python3 -c "
import http.client, json
conn = http.client.HTTPConnection('localhost', 5000)

# Test auth endpoint
conn.request('GET', '/api/v1/auth/login')
r = conn.getresponse()
assert r.status in [200, 401], f'Auth endpoint failed: {r.status}'
print('✓ Auth endpoint responding')

# Test users endpoint
conn.request('GET', '/api/v1/users')
r = conn.getresponse()
assert r.status in [200, 401], f'Users endpoint failed: {r.status}'
print('✓ Users endpoint responding')
"

# Cleanup
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "✓ Flask Backend Smoke Test PASSED"
```

<<<<<<< HEAD
**WebUI/React example** - `tests/smoketests/webui.sh`
=======
**WebUI:** `tests/smoketests/webui.sh`
>>>>>>> origin/v1.0.X
```bash
#!/bin/bash
set -e

echo "=== WebUI Smoke Test ==="

# 1. Build verification
echo "Building container..."
docker build -t webui:test ./services/webui

# 2. Run container
echo "Starting container..."
CONTAINER_ID=$(docker run -d -p 3000:3000 webui:test)

# Wait for startup
sleep 10

# 3. Health check
echo "Checking health endpoint..."
curl -f http://localhost:3000/healthz || exit 1

# 4. Run unit tests
echo "Running unit tests..."
docker exec $CONTAINER_ID npm run test:unit

# 5. Page load tests
echo "Testing page loads..."
docker exec $CONTAINER_ID node -e "
const http = require('http');

function testPage(path) {
  return new Promise((resolve, reject) => {
    http.get('http://localhost:3000' + path, (res) => {
      if (res.statusCode === 200) {
        console.log('✓ Page loaded:', path);
        resolve();
      } else {
        reject(new Error(\`Page failed: \${path} (Status: \${res.statusCode})\`));
      }
    }).on('error', reject);
  });
}

(async () => {
  await testPage('/');              // Home page
  await testPage('/login');         // Login page
  await testPage('/dashboard');     // Dashboard (may redirect)
  console.log('✓ All pages loaded successfully');
})();
"

# 6. Build production bundle
echo "Testing production build..."
docker exec $CONTAINER_ID npm run build

# Cleanup
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "✓ WebUI Smoke Test PASSED"
```

<<<<<<< HEAD
**Go backend example** - `tests/smoketests/go-backend.sh`
=======
**Go Backend:** `tests/smoketests/go-backend.sh`
>>>>>>> origin/v1.0.X
```bash
#!/bin/bash
set -e

echo "=== Go Backend Smoke Test ==="

# 1. Build verification
echo "Building container..."
docker build -t go-backend:test ./services/go-backend

# 2. Run container
echo "Starting container..."
CONTAINER_ID=$(docker run -d go-backend:test)

# Wait for startup
sleep 5

# 3. Health check
echo "Checking health endpoint..."
docker exec $CONTAINER_ID /usr/local/bin/healthcheck || exit 1

# 4. Run unit tests
echo "Running unit tests..."
docker exec $CONTAINER_ID go test ./... -v

# 5. Run integration tests
echo "Running integration tests..."
docker exec $CONTAINER_ID go test ./tests/integration/... -v

# 6. Performance smoke test
echo "Running performance smoke test..."
docker exec $CONTAINER_ID go test -bench=. -benchtime=1s ./tests/benchmarks/smoke_test.go

# Cleanup
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo "✓ Go Backend Smoke Test PASSED"
```

<<<<<<< HEAD
**Master coordinator** - `tests/smoketests/run-all.sh` (runs all smoke tests)
=======
**Run All:** `tests/smoketests/run-all.sh`
>>>>>>> origin/v1.0.X
```bash
#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "======================================"
echo "Running All Smoke Tests"
echo "======================================"

FAILED=0

for script in tests/smoketests/*.sh; do
  # Skip run-all.sh itself
  if [[ "$script" == *"run-all.sh" ]]; then
    continue
  fi

  echo ""
  echo "Running: $script"
  if bash "$script"; then
    echo "✓ PASSED: $script"
  else
    echo "✗ FAILED: $script"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "======================================"
if [[ $FAILED -eq 0 ]]; then
  echo "✓ ALL SMOKE TESTS PASSED"
  exit 0
else
  echo "✗ $FAILED SMOKE TEST(S) FAILED"
  exit 1
fi
```

<<<<<<< HEAD
**Pro Tips for Smoke Tests**:
- Keep it under 2 minutes (seriously—developers will skip slow tests)
- Fail fast—exit on first error
- Clean up containers when done (no zombie containers!)
- Use simple output—people need to see what passed/failed at a glance
- Make scripts executable: `chmod +x tests/smoketests/*.sh`
- Don't require network—use test databases in Docker
- Tests should be deterministic (pass every time, not randomly flaky)

## Unit Tests: The Foundation

**Location**: `tests/unit/{service_name}/`

Unit tests are the cheapest insurance you can buy. They run instantly and catch bugs before they reach real users.

**The Unit Test Mindset**: Test one piece of code in isolation. No databases. No network. Just pure logic.

**Golden Rules**:
1. No network calls (or mock them)
2. No database access (or mock it)
3. No external dependencies
4. Each test is independent
5. Tests run in milliseconds
6. >80% code coverage minimum

**Quick Start**:

Python (pytest):
=======
#### Integration with Pre-Commit

Smoke tests MUST be executed in the pre-commit checklist:

```bash
# In scripts/pre-commit/pre-commit.sh
echo "Step 5: Smoke Tests"
echo "-------------------"
./tests/smoketests/run-all.sh || exit 1
```

#### Smoke Test Guidelines

1. **Keep it fast**: Smoke tests should complete in <2 minutes total
2. **Comprehensive coverage**: Test all critical paths (build, run, API, UI)
3. **Fail fast**: Exit immediately on first failure
4. **Clear output**: Print progress and results clearly
5. **Cleanup**: Always cleanup containers and resources
6. **Standardized location**: Always use `tests/smoketests/{container_name}.sh`
7. **Executable**: Make scripts executable (`chmod +x`)
8. **Minimal dependencies**: Use only what's available in the container
9. **Mock data**: Use test fixtures, don't require external services
10. **Deterministic**: Tests should pass consistently, not flaky

📚 **Complete testing guide**: [docs/TESTING.md](../../TESTING.md)

### Unit Testing

**All applications MUST have comprehensive unit tests:**

**Location:** `tests/unit/{service_name}/`

- **Network isolation**: Unit tests must NOT require external network connections
- **No external dependencies**: Cannot reach databases, APIs, or external services
- **Use mocks/stubs**: Mock all external dependencies and I/O operations
- **KISS principle**: Keep unit tests simple, focused, and fast
- **Test isolation**: Each test should be independent and repeatable
- **Fast execution**: Unit tests should complete in milliseconds
- **Coverage targets**: Aim for >80% code coverage minimum

**Python (pytest):**
>>>>>>> origin/v1.0.X
```bash
pytest tests/unit/ -v --cov=app --cov-report=term-missing
```

<<<<<<< HEAD
Go:
=======
**Go:**
>>>>>>> origin/v1.0.X
```bash
go test ./... -v -cover
```

<<<<<<< HEAD
Node.js (Jest):
=======
**Node.js (Jest):**
>>>>>>> origin/v1.0.X
```bash
npm run test:unit -- --coverage
```

<<<<<<< HEAD
**Real Example** - Testing a user creation function:

```python
# services/flask-backend/tests/unit/test_user.py
import pytest
from app.models import User
from app.services.user_service import create_user

def test_create_user_with_valid_email():
    """Users can be created with valid email"""
    user = create_user("alice@example.com", "password123")
    assert user.email == "alice@example.com"
    assert user.is_active == True

def test_create_user_with_invalid_email():
    """Invalid emails are rejected"""
    with pytest.raises(ValueError):
        create_user("not-an-email", "password123")

def test_create_user_hashes_password():
    """Passwords are hashed, never stored plaintext"""
    user = create_user("bob@example.com", "secret123")
    assert user.password_hash != "secret123"
    assert len(user.password_hash) > 20  # bcrypt hashes are long
```

Notice: No database, no network, no magic. Just pure function behavior.

## Integration Tests: Making Sure Things Talk

**Location**: `tests/integration/{service_name}/`

Integration tests answer: "Do my services actually work together?" They're slower than unit tests but catch real-world issues.

**Integration Test Goals**:
- Services communicate correctly
- Database operations work with real schema
- API contracts are honored
- Authentication/authorization flows work end-to-end
- Multiple components interact properly

**Typical Structure**:
```
tests/integration/
├── flask-backend/
│   ├── test_api_basic.py        # API endpoints work
│   ├── test_auth.py             # Login flows work
│   └── test_database.py         # Database CRUD works
├── go-backend/
│   └── integration_test.go      # Go service tests
└── docker-compose.test.yml      # Test environment (real database)
```

**Running Integration Tests**:
```bash
# Start test database and services
docker-compose -f tests/integration/docker-compose.test.yml up -d

# Run tests
pytest tests/integration/ -v

# Clean up
docker-compose -f tests/integration/docker-compose.test.yml down -v
```

**Real Example** - Testing user login:

```python
# services/flask-backend/tests/integration/test_auth.py
import pytest
from flask import Flask
from app import create_app
from app.models import User
from app.database import db

@pytest.fixture
def app():
    """Create test app with real database"""
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_can_login(app):
    """Users can login with valid credentials"""
    client = app.test_client()

    # Create user in test database
    with app.app_context():
        user = User(email="alice@test.local", username="alice")
        user.set_password("testpass123")
        db.session.add(user)
        db.session.commit()

    # Test login endpoint
    response = client.post('/api/v1/auth/login', json={
        'email': 'alice@test.local',
        'password': 'testpass123'
    })

    assert response.status_code == 200
    assert 'token' in response.json
```

See the difference? This test uses a real test database and real Flask app.

## End-to-End Tests: The User Journey

**Location**: `tests/e2e/`

E2E tests answer: "Can users actually do the thing they came to do?" This is the highest-level test—it encompasses everything.

**What E2E Tests Cover**:
- Real user workflows (login, create item, export, etc.)
- Full stack from UI to database
- All services working together
- Browser interactions (clicking, typing, navigation)
- Data persistence across screens

**Running E2E Tests**:
```bash
# Start all services (UI, API, database)
docker-compose up -d

# Run tests (uses Playwright for browser automation)
npm run test:e2e

# Or specifically
npx playwright test tests/e2e/
```

**Real Example** - User login and dashboard:

```javascript
// services/webui/tests/e2e/user-login.spec.js
const { test, expect } = require('@playwright/test');

test('user can login and see dashboard', async ({ page }) => {
  // Go to login page
  await page.goto('http://localhost:3000/login');

  // Fill in credentials
  await page.fill('input[type="email"]', 'admin@localhost.local');
  await page.fill('input[type="password"]', 'admin123');

  // Click login button
  await page.click('button[type="submit"]');

  // Check we're redirected to dashboard
  await expect(page).toHaveURL(/\/dashboard/);

  // Verify dashboard loaded (actual data from API)
  await expect(page.locator('h1')).toContainText('Dashboard');
  await expect(page.locator('.user-count')).toBeVisible();
});

test('user can create a new item', async ({ page }) => {
  // Login first
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'admin@localhost.local');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');

  // Click "Create Item" button
  await page.click('text=Create Item');

  // Fill form
  await page.fill('input[name="name"]', 'Test Item');
  await page.fill('textarea[name="description"]', 'A test item');

  // Submit
  await page.click('button[type="submit"]');

  // Verify item appears in list
  await expect(page.locator('text=Test Item')).toBeVisible();
});
```

**Key difference from unit/integration tests**: This runs in a real browser, clicks real buttons, and navigates like a human user.

## Mock Data: Test Without Breaking Things

**Location**: `tests/fixtures/` or `scripts/seed/`

Mock data is fake data that looks real. Use it in tests so you don't accidentally delete production customer data!

**Mock Data Rules**:
- 3-4 items per feature (enough to find patterns, not too many)
- Realistic but obviously fake (admin@localhost.local, not real emails)
- Reuse fixtures across different test types
- Make it easy to reset to clean state
- Use in all test phases (unit, integration, E2E)

**Example Mock Users**:
=======
### Integration Testing

**Location:** `tests/integration/{service_name}/`

Integration tests verify component interactions and system integration:

- **Test component interactions**: Verify services communicate correctly
- **Use test databases**: Spin up test database containers
- **Verify API contracts**: Ensure API requests/responses match contracts
- **Test authentication and authorization**: Verify RBAC, JWT, permissions
- **Service dependencies**: Test with real services in isolated environment
- **Database transactions**: Test CRUD operations with real database
- **Message queues**: Test async communication patterns

**Example Integration Test Structure:**
```
tests/integration/
├── flask-backend/
│   ├── test_api_basic.py       # Basic API tests
│   ├── test_auth.py             # Authentication tests
│   └── test_database.py         # Database integration
├── go-backend/
│   └── integration_test.go      # Go integration tests
└── docker-compose.test.yml      # Test environment
```

**Running Integration Tests:**
```bash
# Start test environment
docker-compose -f tests/integration/docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v

# Cleanup
docker-compose -f tests/integration/docker-compose.test.yml down -v
```

### End-to-End Testing

**Location:** `tests/e2e/`

E2E tests verify critical user workflows through the entire system:

- **Test critical user workflows**: Login, CRUD operations, key features
- **Use staging environment**: Test against staging deployment
- **Verify full system integration**: All services, databases, external APIs
- **Browser automation**: Use Playwright/Selenium for WebUI testing
- **API workflows**: Test complete API request chains
- **User scenarios**: Test from user perspective, not technical perspective

**Example E2E Test:**
```javascript
// tests/e2e/user-login-workflow.spec.js
const { test, expect } = require('@playwright/test');

test('user can login and access dashboard', async ({ page }) => {
  // Navigate to login page
  await page.goto('http://localhost:3000/login');

  // Fill login form
  await page.fill('input[name="email"]', 'admin@localhost.local');
  await page.fill('input[name="password"]', 'admin123');

  // Submit form
  await page.click('button[type="submit"]');

  // Verify redirect to dashboard
  await expect(page).toHaveURL('http://localhost:3000/dashboard');

  // Verify dashboard elements loaded
  await expect(page.locator('h1')).toContainText('Dashboard');

  // Verify API data loaded
  await expect(page.locator('.user-count')).toBeVisible();
});
```

### Performance Testing

**Location:** `tests/performance/`

Performance tests ensure the system meets scalability and latency requirements:

- **Benchmark critical operations**: Measure operation performance
- **Load testing for scalability**: Test under expected load
- **Stress testing**: Find breaking points
- **Regression testing**: Prevent performance degradation
- **Latency measurements**: Track response times
- **Throughput testing**: Measure requests/second capacity

**Tools:**
- **Python**: pytest-benchmark, locust
- **Go**: built-in benchmarking (`go test -bench`)
- **HTTP Load**: Apache Bench (ab), wrk, k6

**Example Go Benchmark:**
```go
// tests/performance/api_benchmark_test.go
func BenchmarkAPIEndpoint(b *testing.B) {
    for i := 0; i < b.N; i++ {
        resp, _ := http.Get("http://localhost:8080/api/v1/users")
        resp.Body.Close()
    }
}
```

### Mock Data Standards

**Location:** `tests/fixtures/` or `scripts/seed/`

All tests and development environments should use consistent mock data:

- **3-4 items per feature/entity**: Enough to show patterns, not too much
- **Realistic data**: Use plausible names, emails, values
- **Consistent fixtures**: Reuse same fixtures across test types
- **Seed scripts**: Automate mock data population
- **Reset capability**: Easy to reset to clean state

**Example Fixture:**
>>>>>>> origin/v1.0.X
```python
# tests/fixtures/users.py
MOCK_USERS = [
    {
        "email": "admin@localhost.local",
        "username": "admin",
        "role": "admin"
    },
    {
        "email": "maintainer@localhost.local",
        "username": "maintainer",
        "role": "maintainer"
    },
    {
        "email": "viewer@localhost.local",
        "username": "viewer",
        "role": "viewer"
<<<<<<< HEAD
    },
    {
        "email": "guest@localhost.local",
        "username": "guest",
        "role": "guest"
=======
>>>>>>> origin/v1.0.X
    }
]
```

<<<<<<< HEAD
**Seed Script** (populate test database):
```bash
# scripts/seed/seed-test-data.sh
#!/bin/bash
echo "Seeding test database..."

docker exec flask-backend python3 -c "
from app import create_app, db
from app.models import User
from tests.fixtures import users

app = create_app()
with app.app_context():
    for user_data in users.MOCK_USERS:
        user = User(**user_data)
        db.session.add(user)
    db.session.commit()
    print('✓ Seeded 4 test users')
"
```

## Performance Testing: Speed Matters

**Location**: `tests/performance/`

Is your API fast enough? Performance tests answer that question with numbers.

**Tools**:
- Python: `pytest-benchmark`, `locust`
- Go: built-in `go test -bench`
- HTTP: `wrk`, `k6`, Apache Bench

**Go Example**:
```go
// services/go-backend/tests/performance/api_benchmark_test.go
func BenchmarkAPIEndpoint(b *testing.B) {
    for i := 0; i < b.N; i++ {
        resp, _ := http.Get("http://localhost:8080/api/v1/users")
        resp.Body.Close()
    }
}

// Run: go test -bench=. ./tests/performance
```

## Running Tests in Order

**Run faster tests first** (fail quickly):

1. **Linting** (1 min) — Code style check
2. **Unit Tests** (2 min) — Individual pieces
3. **Smoke Tests** (1 min) — Does it build and run?
4. **Integration Tests** (5 min) — Do services work together?
5. **E2E Tests** (10 min) — Can users do their job?
6. **Performance Tests** (variable) — Is it fast enough?

```bash
# Run in order (fail fast approach)
make lint && \
make test-unit && \
make smoke-test && \
make test-integration && \
make test-e2e && \
make test-performance
```

## Debugging Failed Tests

**Test failed? Here's how to fix it**:

1. **Read the error message** (seriously, it usually tells you what's wrong)
2. **Run just that test** (not the whole suite)
3. **Add print statements** (or use a debugger)
4. **Check test data** (is your mock data correct?)
5. **Verify dependencies** (is the database running?)
6. **Check logs** (what did the service actually do?)

**Common issues**:

| Problem | Solution |
|---------|----------|
| "Connection refused" | Is the service running? `docker-compose ps` |
| "Table doesn't exist" | Did you run migrations? `make migrate` |
| "Timeout" | Is the test too slow? Increase timeout or optimize code |
| "Random failures" | Test is flaky—make it more deterministic |
| "Works locally, fails in CI" | Different environment? Check env vars |

## Coverage Goals: What's "Good Enough"?

**Target**: 80% code coverage minimum

Why 80% and not 100%?
- 100% coverage takes forever and has diminishing returns
- 80% gets most bugs, especially in business logic
- Some code is hard to test (error recovery, rare edge cases)
- Focus on testing what matters: user workflows and business rules

**Check coverage**:
```bash
# Python
pytest tests/unit/ --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# JavaScript
npm run test:unit -- --coverage
# Open coverage/index.html in browser

# Go
go test ./... -cover
```

## Cross-Architecture Testing

**Before final commit**: Test on both amd64 and arm64

```bash
# If on amd64, test on arm64
docker buildx build --platform linux/arm64 -t app:test-arm64 .

# If on arm64, test on amd64
docker buildx build --platform linux/amd64 -t app:test-amd64 .
```

This catches architecture-specific bugs (endianness, pointer sizes, etc.).
=======
### Test Execution Order

**Recommended execution order in CI/CD:**

1. **Linting** (fastest) - Catch style issues immediately
2. **Unit Tests** (fast) - Verify individual components
3. **Smoke Tests** (quick) - Verify build and basic functionality
4. **Integration Tests** (medium) - Verify component interactions
5. **E2E Tests** (slow) - Verify critical workflows
6. **Performance Tests** (slowest) - Verify scalability

### Cross-Architecture Testing

**Before final commit, test on alternate architecture using QEMU:**

```bash
# If developing on amd64, test on arm64:
docker buildx build --platform linux/arm64 -t app:test-arm64 .
docker run --platform linux/arm64 app:test-arm64 npm test

# If developing on arm64, test on amd64:
docker buildx build --platform linux/amd64 -t app:test-amd64 .
docker run --platform linux/amd64 app:test-amd64 npm test
```

This ensures multi-architecture compatibility and prevents platform-specific bugs.
>>>>>>> origin/v1.0.X
