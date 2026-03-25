# Pre-Commit Checklist for IceCharts

**CRITICAL: This checklist MUST be followed before every commit.**

IceCharts is a collaborative diagramming and visualization platform with three main components: React WebUI (Node.js), Flask API Backend (Python/PyDAL), and optional Go backend services. All code changes must pass comprehensive checks before committing.

## Automated Pre-Commit Script

**Run the automated pre-commit script to execute all checks:**

```bash
./scripts/pre-commit/pre-commit.sh
```

This script will:
1. Run all checks in the correct order
2. Log output to `/tmp/pre-commit-icecharts-<epoch>.log`
3. Provide a summary of pass/fail status
4. Echo the log file location for review

**Individual check scripts** (run separately if needed):
- `./scripts/pre-commit/check-python.sh` - Python linting & security (Flask backend)
- `./scripts/pre-commit/check-node.sh` - Node.js/React linting, audit & build (WebUI)
- `./scripts/pre-commit/check-security.sh` - All security scans
- `./scripts/pre-commit/check-secrets.sh` - Secret detection
- `./scripts/pre-commit/check-docker.sh` - Docker build & validation
- `./scripts/pre-commit/check-tests.sh` - Unit tests

## Required Steps (In Order)

Before committing, run in this order (or use `./scripts/pre-commit/pre-commit.sh`):

### Foundation Checks

- [ ] **Linters (Language-specific)**:
  - **Node.js/TypeScript (WebUI)**: `cd services/webui && npm run lint`
  - **Python (Flask Backend)**: `cd services/flask-backend && flake8 . && black --check . && isort --check .`
  - **Type checking**: `mypy .` (Python)
- [ ] **Security scans**:
  - **Node.js**: `npm audit` (in webui service)
  - **Python**: `bandit -r .` and `safety check` (in flask-backend service)
- [ ] **No secrets**: Verify no credentials, API keys, tokens, or database passwords in code
  - Search for hardcoded PostgreSQL/MySQL connection strings
  - Check for embedded Firebase/MinIO keys
  - Verify no license keys in code

### Build & Integration Verification

- [ ] **Build & Run**: Verify code compiles and containers start successfully
  - **WebUI**: `cd services/webui && npm run build`
  - **Flask Backend**: `cd services/flask-backend && python -m py_compile *.py`
  - **Docker Build**: Verify Dockerfile builds for each modified service
- [ ] **Smoke tests** (mandatory, <2 min): `make smoke-test`
  - All containers build without errors
  - All containers start and remain healthy
  - All API health endpoints respond with 200 status
  - WebUI page and diagram canvas load without JavaScript errors
  - Database connections established successfully
  - Redis/cache connectivity verified
  - See: [Testing Documentation - Smoke Tests](TESTING.md#smoke-tests)

### Diagram & Visualization Specific Checks

- [ ] **Canvas & Drawing Components** (if modified):
  - Ensure shape rendering tests pass
  - Verify connector routing logic works correctly
  - Test export formats (SVG, PNG, PDF, JSON)
  - Check grid and snap-to-grid alignment
  - Validate diagram undo/redo functionality
- [ ] **Real-time Collaboration** (if modified):
  - WebSocket connection establishment works
  - Multi-user editing synchronization functions correctly
  - Presence awareness updates properly
  - Comment threading and resolution tracking work
- [ ] **Export & Sharing Features** (if modified):
  - All export format handlers produce valid output
  - File download/upload mechanisms work
  - Public sharing link generation functions
  - Customizable export options are applied correctly

### Feature Testing & Documentation

- [ ] **Mock data** (for testing features): Ensure 3-4 test diagrams per feature via `make seed-mock-data`
  - Populate development database with realistic test diagrams
  - Create sample infrastructure diagrams, flowcharts, and organizational charts
  - Needed before capturing screenshots and UI testing
  - See: [Testing Documentation - Mock Data Scripts](TESTING.md#mock-data-scripts)
- [ ] **Screenshots** (for UI changes): `node scripts/capture-screenshots.cjs` (or `npm run screenshots`)
  - Requires running `make dev` and `make seed-mock-data` first
  - Screenshots should showcase features with realistic mock data
  - Automatically removes old screenshots, captures fresh ones
  - **Diagram screenshots must show**:
    - Canvas with drawn shapes and connectors
    - Comments panel with threaded discussions
    - Export dialog with various format options
    - Dashboard with list of created diagrams
  - Commit updated screenshots with feature/UI changes

### Comprehensive Testing

- [ ] **Unit tests**: `npm test` (WebUI), `pytest` (Flask Backend)
  - Network isolated, mocked dependencies
  - Canvas rendering tests pass
  - API endpoint tests pass
  - Database model tests pass
  - Must pass before committing
- [ ] **Integration tests**: Component interaction verification
  - WebUI ↔ Flask Backend API communication
  - Database ↔ Flask Backend operations
  - Real-time collaboration (WebSocket) functionality
  - Export service file generation
  - See: [Testing Documentation - Integration Tests](TESTING.md#integration-tests)
- [ ] **Diagram export tests**: Verify all export formats
  - SVG export with proper scaling
  - PNG/PDF export with correct resolution
  - JSON export with complete diagram state

### Finalization

- [ ] **Version updates**: Update `.version` if releasing new version
- [ ] **Documentation**: Update docs if adding/changing features
  - FEATURES.md if adding visualization capabilities
  - ARCHITECTURE.md if changing component interactions
  - API_REFERENCE.md if adding API endpoints
  - COLLABORATION.md if modifying real-time features
- [ ] **Docker builds**: Verify Dockerfile uses debian-slim base (no alpine)
  - Check WebUI Dockerfile for Node.js debian-slim base
  - Check Flask backend Dockerfile for Python debian-slim base
- [ ] **Database migrations**: If modifying database schema
  - PyDAL migrations applied successfully
  - No schema conflicts with existing data
  - Rollback procedure documented
- [ ] **Cross-architecture** (Optional): Test alternate architecture with QEMU
  - `docker buildx build --platform linux/arm64 .` (if on amd64)
  - `docker buildx build --platform linux/amd64 .` (if on arm64)
  - See: [Testing Documentation - Cross-Architecture Testing](TESTING.md#cross-architecture-testing)

## Language-Specific Commands

### Node.js / TypeScript / React (WebUI)

```bash
cd services/webui

# Linting
npm run lint
# or
npx eslint .

# Type checking
npx tsc --noEmit

# Code formatting
npx prettier --check .

# Security (REQUIRED)
npm audit                          # Check for vulnerabilities
npm audit fix                      # Auto-fix if possible

# Build & Run
npm run build                      # Compile/bundle
npm run dev &                      # Verify it starts (then kill)

# Tests
npm test                           # Run unit tests with Vitest
npm run test:integration          # Run integration tests
npm run test:e2e                  # Run end-to-end tests
npm run test:coverage             # Generate coverage report

# Screenshots
npm run screenshots               # Capture UI screenshots
```

### Python (Flask Backend)

```bash
cd services/flask-backend

# Linting
flake8 .
black --check .
isort --check .

# Type checking
mypy .

# Security
bandit -r .
safety check

# Build & Run
python -m py_compile *.py          # Syntax check
pip install -r requirements.txt    # Dependencies
python app.py &                    # Verify it starts (then kill)

# Tests
pytest                             # Run unit tests
pytest -v --cov                   # With coverage
pytest tests/integration/          # Integration tests only
```

### Docker / Containers

```bash
# Lint Dockerfiles
hadolint Dockerfile

# Verify base image (debian-slim, NOT alpine)
grep -E "^FROM.*slim" Dockerfile

# Build & Run
docker build -t icecharts-webui:test services/webui          # Build WebUI
docker build -t icecharts-backend:test services/flask-backend # Build Backend
docker run -d --name test-container icecharts-webui:test     # Start container
docker logs test-container                                    # Check for errors
docker stop test-container && docker rm test-container       # Cleanup

# Docker Compose (if applicable)
docker-compose -f docker-compose.dev.yml build  # Build all services
docker-compose -f docker-compose.dev.yml up -d  # Start all services
docker-compose -f docker-compose.dev.yml logs   # Check for errors
docker-compose -f docker-compose.dev.yml down   # Cleanup
```

## Commit Rules

- **NEVER commit automatically** unless explicitly requested by the user
- **NEVER push to remote repositories** under any circumstances
- **ONLY commit when explicitly asked** - never assume commit permission
- **Wait for approval** before running `git commit`

## Security Scanning Requirements

### Before Every Commit

- **Run security audits on all modified packages**:
  - **Node.js packages** (WebUI): Run `npm audit` on modified Node.js services
  - **Python packages** (Flask Backend): Run `bandit -r .` and `safety check` on modified Python services
  - **Dockerfile security**: Use `hadolint` to check Dockerfile best practices
- **Do NOT commit if security vulnerabilities are found** - fix all issues first
- **Document vulnerability fixes** in commit message if applicable

### Vulnerability Response

1. Identify affected packages and severity
2. Update to patched versions immediately
3. Test updated dependencies thoroughly
4. Document security fixes in commit messages
5. Verify no new vulnerabilities introduced

## API Testing Requirements

Before committing changes to container services:

- **Create and run API testing scripts** for each modified container service
- **Testing scope**: All new endpoints and modified functionality
- **Test files location**: `tests/api/` directory with service-specific subdirectories
  - `tests/api/flask-backend/` - Flask backend API tests
  - `tests/api/webui/` - WebUI container tests
- **Run before commit**: Each test script should be executable and pass completely
- **Test coverage**: Health checks, authentication, CRUD operations, error cases

### IceCharts-Specific API Tests

For diagram/visualization features:
- Canvas drawing endpoints (create, update, delete shapes)
- Export endpoints (SVG, PNG, PDF, JSON formats)
- Collaboration endpoints (WebSocket connections, presence updates)
- Comment endpoints (create, resolve, delete)
- Share endpoints (generate links, manage permissions)

```bash
# Run Flask Backend API tests
cd services/flask-backend
pytest tests/api/ -v

# Run WebUI API tests (if backend integration tests exist)
cd services/webui
npm run test:api
```

## Screenshot & Mock Data Requirements

### Prerequisites

Before capturing screenshots, ensure development environment is running with mock data:

```bash
make dev                   # Start all services
make seed-mock-data       # Populate with 3-4 test diagrams per feature
```

### Capture Screenshots

For all UI changes, update screenshots to show current application state with realistic data:

```bash
node scripts/capture-screenshots.cjs
# Or via npm script if configured:
npm run screenshots
```

### What to Screenshot (IceCharts-Specific)

- **Login page** (unauthenticated state)
- **Dashboard** (overview with 3-4 recent diagrams)
- **Drawings list** (organized by type: infrastructure, flowchart, organizational chart)
- **Canvas editor** (showing drawn diagram with shapes, connectors, and grid)
- **Collaboration features** (multiple cursors, presence awareness, comments panel)
- **Export dialog** (with various export format options)
- **Collections/Templates** (if adding new diagram types)
- **Settings** (user preferences, export settings)

### Commit Guidelines

- Automatically removes old screenshots and captures fresh ones
- Commit updated screenshots with relevant feature/UI/documentation changes
- Screenshots demonstrate feature purpose and functionality
- Helpful error message if login fails: "Ensure mock data is seeded"

## Pre-Commit Checklist Summary

Before running `git commit`:

- [ ] All linters pass (ESLint, Prettier, flake8, black, isort, mypy)
- [ ] All security scans pass (npm audit, bandit, safety check)
- [ ] No hardcoded secrets or credentials in code
- [ ] All code compiles and builds successfully
- [ ] Smoke tests pass (build, run, API health, UI loads)
- [ ] Unit tests pass with good coverage
- [ ] Integration tests pass
- [ ] Mock data seeded and screenshots captured
- [ ] Diagram-specific features tested (canvas, export, collaboration)
- [ ] Docker images build without warnings
- [ ] Database migrations (if applicable) tested
- [ ] Version updated (if releasing)
- [ ] Documentation updated (if changing features)
- [ ] No cross-architecture build failures (optional QEMU test)

## Coverage Check

Before committing, verify coverage does not drop below thresholds:

- [ ] `cd services/flask-backend && pytest tests/ --cov=app --cov-fail-under=95 -q`
- [ ] `cd services/icestreams-worker && pytest tests/ --cov=. --cov-fail-under=90 -q`
- [ ] `cd services/iceflows-worker && pytest tests/ --cov=. --cov-fail-under=90 -q`
- [ ] `cd services/iceruns-invoker && pytest tests/ --cov=. --cov-fail-under=90 -q`
- [ ] `cd services/webui && npm run test:coverage`

## Resources

- **Testing Guide**: [Testing Documentation](TESTING.md)
- **Development Guide**: [Development Setup](DEVELOPMENT.md)
- **Architecture Details**: [Architecture Documentation](ARCHITECTURE.md)
- **API Reference**: [API Reference](API_REFERENCE.md)
- **Features Overview**: [Features Documentation](FEATURES.md)

---

**Last Updated**: 2026-01-06
**Maintained by**: IceCharts Team
**Based on**: Penguin Tech Inc Project Template
