# IceCharts CI/CD Workflows

This document describes all GitHub Actions workflows for the IceCharts multi-language template project (Go, Python, Node.js).

## Workflow Overview

IceCharts is a comprehensive multi-language project template supporting Go services, Python backends, and Node.js web UIs. CI/CD automation ensures consistency across all language stacks with path-based job filtering for efficiency.

## Core Workflows

### 1. **Test and Lint (test-and-lint.yml)**

**Purpose**: Comprehensive testing and code quality for Flask backend and WebUI
**Triggers**:
- Push to main, develop, feature/* branches
- Pull requests to main, develop branches
- Daily schedule: 2 AM UTC

**Path Filtering**:
```yaml
flask:
  - 'services/flask-backend/**'
  - 'services/flask-backend/tests/**'
webui:
  - 'services/webui/**'
  - 'services/webui/tests/**'
```

**Flask Backend Tests**:
- Black code formatting
- isort import sorting
- flake8 linting
- mypy type checking
- pytest unit tests with coverage
- bandit security scanning
- Safety dependency checks

**WebUI Tests**:
- ESLint configuration validation
- Prettier formatting
- TypeScript compilation
- Jest unit tests
- npm audit security checks

### 2. **Build Flask Backend (build-flask-backend.yml)**

**Purpose**: Build Flask application with security scanning
**Triggers**: Push to main, develop branches

**Steps**:
- Dependency installation
- Code quality checks
- Type validation
- Security scanning (bandit)
- Build artifact creation

### 3. **Build WebUI (build-webui.yml)**

**Purpose**: Build Node.js web UI
**Triggers**: Push to main, develop branches

**Steps**:
- Node.js setup
- Dependency installation
- Linting checks
- Build optimization
- Asset generation

### 4. **Continuous Integration (ci.yml)**

**Purpose**: Full CI pipeline for Go, Python, and Node.js
**Triggers**:
- Push to main, develop, feature/* branches
- Pull requests to main, develop branches
- Daily schedule: 2 AM UTC

**Environment**:
- Go: 1.23+ with matrix testing
- Python: 3.13
- Node.js: 20

**Path Detection** - Changes job identifies affected services:
```yaml
changes:
  go:
    - 'go.mod'
    - 'go.sum'
    - '**/*.go'
    - 'services/**'
  python:
    - 'requirements.txt'
    - '**/*.py'
    - 'apps/web/**'
  node:
    - 'package.json'
    - 'package-lock.json'
    - 'web/**'
    - '**/*.js'
    - '**/*.ts'
```

**Go Testing** (`go-test`):
- Multiple Go versions (1.23, 1.24)
- go test with coverage
- golangci-lint for linting
- gosec for security scanning
- go mod tidy validation

**Go Security Scanning** (`go-security`):
- gosec for Go security issues
- SARIF report generation
- GitHub Security tab integration

**Python Testing** (`python-test`):
- Python 3.13 environment
- Dependency installation
- Pytest unit tests with coverage
- Code coverage reporting

**Python Linting** (`python-lint`):
- flake8 linting
- black formatting
- isort import sorting
- mypy type checking
- bandit security analysis

**Python Security** (`python-security`):
- bandit security scanning
- Safety dependency checking
- SARIF report generation

**Node.js Testing** (`node-test`):
- Node.js 20 environment
- npm dependency installation
- Jest unit tests
- Code coverage reporting

**Node.js Linting** (`node-lint`):
- ESLint configuration
- Prettier formatting
- TypeScript compilation
- npm audit security checks

### 5. **Docker Multi-Architecture Build (docker-multiarch.yml)**

**Purpose**: Build Docker images for multiple architectures
**Triggers**: Push to main with .version changes

**Features**:
- Parallel amd64 and arm64 builds
- .version file monitoring
- Epoch64 timestamp support
- Multi-stage builds
- Debian-slim base images
- Trivy image scanning

**Build Services**:
- Flask backend container
- WebUI container
- API container (if Go services present)

**Version Detection**:
- Monitors .version path
- Extracts epoch64 timestamp
- Tags with semantic version and full timestamp
- Skips release if version is 0.0.0

### 6. **Version Release (version-release.yml)**

**Purpose**: Automated release creation on .version updates
**Triggers**: Push to main with .version path changes

**Features**:
- .version file monitoring
- Epoch64 timestamp parsing
- Semantic version extraction
- Pre-release creation
- Release notes generation
- Duplicate prevention

**Version Format**: `vMajor.Minor.Patch.epoch64`
**Example**: `1.0.0.1737727200`

**Process**:
1. Read .version file
2. Extract semantic version (first 3 segments)
3. Check if version > 0.0.0 (skip if default)
4. Verify release doesn't already exist
5. Generate release notes with version details
6. Create pre-release on GitHub

### 7. **Deployment (deploy.yml)**

**Purpose**: Deploy to target environments
**Triggers**: Manual workflow dispatch

**Features**:
- Environment selection (dev, staging, production)
- Health check validation
- Rollback capabilities
- Database migrations
- Service orchestration

### 8. **Docker Build (deprecated for multi-arch)**

**Legacy workflow** - use `docker-multiarch.yml` instead

### 9. **Release (release.yml)**

**Purpose**: Create tagged releases
**Triggers**: Manual workflow dispatch

### 10. **Push (push.yml)**

**Purpose**: Push artifacts to registry
**Triggers**: After successful builds

### 11. **GitStream (gitstream.yml)**

**Purpose**: Automated code review policies
**Triggers**: Pull request events

### 12. **Cron (cron.yml)**

**Purpose**: Scheduled maintenance
**Triggers**: Daily schedule

## Security Scanning Overview

IceCharts implements comprehensive security scanning across all languages:

### Go Security (gosec)
- Static analysis for Go code
- Detects security patterns
- SARIF output to GitHub Security
- Run: `gosec ./...`

### Python Security (bandit)
- Python security linting
- Vulnerability detection
- Integration with CI pipeline
- Run: `bandit -r apps/ shared/`

### Node.js Security (npm audit)
- Dependency vulnerability scanning
- Automatic fix suggestions
- CI pipeline integration
- Run: `npm audit` or `npm audit --fix`

### Container Scanning (Trivy)
- Image vulnerability scanning
- Filesystem scanning
- SARIF report generation
- GitHub Security integration

## Version Management

### .version File Format
- **Format**: `vMajor.Minor.Patch.epoch64`
- **Example**: `1.0.0.1737727200`
- **epoch64**: Unix timestamp (seconds since epoch, 64-bit)

### Update Process
```bash
# Using scripts
./scripts/version/update-version.sh           # Increment epoch64
./scripts/version/update-version.sh patch     # Increment patch
./scripts/version/update-version.sh minor     # Increment minor
./scripts/version/update-version.sh major     # Increment major
```

## Service Structure

### Services
- **flask-backend** - Python REST API with Flask-RESTX
- **webui** - Node.js React frontend
- **go-api** - Optional Go service (if present in go.mod)

### Shared Components
- Licensing integration
- Database utilities
- Authentication/authorization
- Monitoring and logging

## Path-Based Filtering

Workflows skip jobs when unrelated code changes:
- Go changes don't trigger Python/Node jobs
- Python changes don't trigger Go/Node jobs
- Node changes don't trigger Go/Python jobs
- Reduces CI time and resource usage

## Environment Variables

**Workflow Environment**:
- `PYTHON_VERSION`: 3.13
- `NODE_VERSION`: 20
- `GO_VERSION`: 1.23+ (matrix tested)
- `REGISTRY`: ghcr.io

## Troubleshooting

### Common Issues

**Test Failures**:
1. Check Python 3.13 compatibility
2. Verify npm dependencies
3. Review Go version matrix
4. Check for flaky tests

**Build Failures**:
1. Validate Dockerfile syntax
2. Check base image availability
3. Verify multi-arch support
4. Review build logs

**Security Scan Failures**:
1. Review vulnerability details
2. Update vulnerable packages
3. Check for false positives
4. Use security exception comments if needed

### Debug Commands

```bash
# View workflow logs
gh run view <run-id> --log

# List recent runs
gh run list --limit 10

# Rerun failed workflow
gh run rerun <run-id>

# View specific job
gh run view <run-id> --log --job <job-id>
```

## Best Practices

1. **Monitor .version file** - Changes trigger automated releases
2. **Run tests locally** - Before pushing to avoid CI delays
3. **Use feature branches** - For all development
4. **Test multi-language builds** - Especially if touching go.mod/requirements.txt
5. **Review security reports** - Check GitHub Security tab
6. **Update dependencies regularly** - Use Dependabot alerts

## Manual Workflow Triggers

```bash
# Deploy to environment
gh workflow run deploy.yml \
  -f environment=staging

# Create release
gh workflow run release.yml \
  -f version=1.0.0

# Rebuild Docker images
gh workflow run docker-multiarch.yml \
  -f branch=main
```

## Integration with Version Control

- **main branch**: Production-ready code
- **develop branch**: Development code
- **feature/\*** branches**: Feature development
- **Tags**: Release versions (v1.0.0)

## Related Documentation

- See [docs/STANDARDS.md](STANDARDS.md) for code quality standards
- See [docs/DEPLOYMENT.md](DEPLOYMENT.md) for deployment procedures
- See [CLAUDE.md](../CLAUDE.md) for development context
- See [docs/API_REFERENCE.md](API_REFERENCE.md) for API documentation
