# IceCharts - Claude Code Context

## Project Overview

IceCharts is a diagramming and infrastructure visualization application based on Penguin Tech Inc's enterprise template. It provides:
- React frontend (services/webui)
- Flask backend with PyDAL (services/flask-backend)
- Multi-database support (PostgreSQL, MySQL, MariaDB, SQLite)
- Redis caching
- MinIO object storage
- Service account authentication for external integrations

**Template Features:**
- Multi-language support (Go 1.23.x, Python 3.12/3.13, Node.js 18+)
- Enterprise security and licensing integration
- Comprehensive CI/CD pipeline
- Production-ready containerization
- Monitoring and observability
- Version management system
- PenguinTech License Server integration

**Key IceCharts Specifics:**
- Diagramming and visualization tools
- Infrastructure management capabilities
- Service account-based integration for external systems (e.g., Elder)
- Multi-tenant capable architecture
- Advanced drawing and export features

## Technology Stack

### Languages & Frameworks

**Language Selection Criteria (Case-by-Case Basis):**
- **Python 3.13**: Default choice for most applications
  - Web applications and APIs
  - Business logic and data processing
  - Integration services and connectors
- **Go 1.23.x**: ONLY for high-traffic/performance-critical applications
  - Applications handling >10K requests/second
  - Network-intensive services
  - Low-latency requirements (<10ms)
  - CPU-bound operations requiring maximum throughput

**Python Stack:**
- **Python**: 3.13 for all applications (3.12+ minimum)
- **Web Framework**: Flask + Flask-Security-Too (mandatory)
- **Database ORM**: PyDAL (mandatory for all Python applications)
- **Performance**: Dataclasses with slots, type hints, async/await required

**Frontend Stack:**
- **React**: ReactJS for all frontend applications
- **Node.js**: 18+ for build tooling and React development
- **JavaScript/TypeScript**: Modern ES2022+ standards

### Infrastructure & DevOps
- **Containers**: Docker with multi-stage builds, Docker Compose
- **Orchestration**: Kubernetes with Helm charts
- **Configuration Management**: Ansible for infrastructure automation
- **CI/CD**: GitHub Actions with comprehensive pipelines
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Logging**: Structured logging with configurable levels

### Databases & Storage

**Hybrid Database Approach:**
- **Initialization**: SQLAlchemy for schema setup and migrations
- **Day-to-Day Operations**: PyDAL for runtime database abstraction
- **Primary**: PostgreSQL (default, configurable via `DB_TYPE` environment variable)
- **Cache**: Redis/Valkey with optional TLS and authentication

**Database Abstraction Layers (DALs):**
- **Python**: PyDAL (mandatory for ALL Python applications)
  - Must support ALL PyDAL-supported databases by default
  - Special support for MariaDB Galera cluster requirements
  - `DB_TYPE` must match PyDAL connection string prefixes exactly
- **Go**: GORM or sqlx (mandatory for cross-database support)
  - Must support PostgreSQL and MySQL/MariaDB
  - Stable, well-maintained library required
- **Migrations**: Automated schema management
- **Database Support**: Design for ALL PyDAL-supported databases from the start

**MariaDB Galera Cluster Requirements:**
- **WSREP Settings**: Handle `wsrep_sync_wait=1` for read-your-writes consistency
- **Primary Keys**: All tables MUST have explicit primary keys (Galera requirement)
- **Auto-increment Handling**: Use auto-increment with Galera-specific settings
- **Transaction Retry Logic**: Implement retry logic for `deadlock_found` and `galera_sync_failed` errors
- **Connection Pooling**: Maintain appropriate pool sizes for Galera clusters
- **Batch Operations**: Avoid overly large batch inserts; break into smaller transactions
- **Conflict Detection**: Implement proper handling for `wsrep_local_index` conflicts

**Supported DB_TYPE Values (PyDAL prefixes):**
- `postgres` / `postgresql` - PostgreSQL (default)
- `mysql` - MySQL/MariaDB
- `sqlite` - SQLite
- `mssql` - Microsoft SQL Server
- `oracle` - Oracle Database
- `db2` - IBM DB2
- `firebird` - Firebird
- `informix` - IBM Informix
- `ingres` - Ingres
- `cubrid` - CUBRID
- `sapdb` - SAP DB/MaxDB

**IMPORTANT: DB_TYPE Restrictions for IceCharts:**
- Only `postgres`, `mysql`, and `sqlite` are officially supported
- Input validation MUST reject unsupported DB_TYPE values
- Other values will cause runtime failures

### Security & Authentication

- **Flask-Security-Too**: Mandatory for all Flask applications
  - Role-based access control (RBAC)
  - User authentication and session management
  - Password hashing with bcrypt
  - Email confirmation and password reset
  - Two-factor authentication (2FA)
- **TLS**: Enforce TLS 1.2 minimum, prefer TLS 1.3
- **HTTP3/QUIC**: Utilize UDP with TLS for high-performance connections where possible
- **Authentication**: JWT and MFA (standard), mTLS where applicable
- **SSO**: SAML/OAuth2 SSO as enterprise-only features
- **Secrets**: Environment variable management
- **Scanning**: Trivy vulnerability scanning, CodeQL analysis
- **Code Quality**: All code must pass CodeQL security analysis

## PenguinTech License Server Integration

All projects integrate with the centralized PenguinTech License Server at `https://license.penguintech.io` for feature gating and enterprise functionality.

**IMPORTANT: License enforcement is ONLY enabled when project is marked as release-ready**
- Development phase: All features available, no license checks
- Release phase: License validation required, feature gating active

**License Key Format**: `PENG-XXXX-XXXX-XXXX-XXXX-ABCD`

**Core Endpoints**:
- `POST /api/v2/validate` - Validate license
- `POST /api/v2/features` - Check feature entitlements
- `POST /api/v2/keepalive` - Report usage statistics

**Environment Variables**:
```bash
# License configuration
LICENSE_KEY=PENG-XXXX-XXXX-XXXX-XXXX-ABCD
LICENSE_SERVER_URL=https://license.penguintech.io
PRODUCT_NAME=your-product-identifier

# Release mode (enables license enforcement)
RELEASE_MODE=false  # Development (default)
RELEASE_MODE=true   # Production (explicitly set)
```

📚 **Detailed Documentation**: [License Server Integration Guide](docs/licensing/license-server-integration.md)

## WaddleAI Integration (Optional)

For projects requiring AI capabilities, integrate with WaddleAI located at `~/code/WaddleAI`.

**When to Use WaddleAI:**
- Natural language processing (NLP)
- Machine learning model inference
- AI-powered features and automation
- Intelligent data analysis
- Chatbots and conversational interfaces

**Integration Pattern:**
- WaddleAI runs as separate microservice container
- Communicate via REST API or gRPC
- Environment variable configuration for API endpoints
- License-gate AI features as enterprise functionality

📚 **WaddleAI Documentation**: See WaddleAI project at `~/code/WaddleAI` for integration details

## Project Structure

```
IceCharts/
├── .github/             # CI/CD pipelines and templates
│   └── workflows/       # GitHub Actions for each container
├── services/            # Microservices (separate containers by default)
│   ├── flask-backend/   # Flask + PyDAL backend (auth, users, standard APIs)
│   ├── webui/           # Node.js + React frontend shell
│   └── connector/       # Integration services (placeholder)
├── shared/              # Shared libraries (py_libs, go_libs, node_libs)
│   ├── py_libs/         # Python shared library (pip installable)
│   ├── go_libs/         # Go shared library (Go module)
│   ├── node_libs/       # TypeScript shared library (npm package)
│   └── README.md        # Shared libraries overview
├── k8s/                 # Kubernetes deployment templates
│   ├── helm/            # Helm v3 charts per service
│   ├── manifests/       # Raw K8s manifests (kubectl apply)
│   └── kustomize/       # Kustomize overlays (dev/staging/prod)
├── infrastructure/      # Infrastructure as code
├── scripts/             # Utility scripts
├── tests/               # Test suites (unit, integration, e2e, performance)
├── docs/                # Documentation
├── config/              # Configuration files
├── docker-compose.yml   # Production environment
├── docker-compose.dev.yml # Local development
├── Makefile             # Build automation
├── .version             # Version tracking
└── CLAUDE.md            # This file
```

### Three-Container Architecture

This project uses three base containers representing the core architecture:

| Container | Purpose | When to Use |
|-----------|---------|-------------|
| **flask-backend** | Standard APIs, auth, CRUD | <10K req/sec, business logic |
| **webui** | Node.js + React frontend | All frontend applications |
| **go-backend** | High-performance networking | >10K req/sec, <10ms latency |

### Microservices Architecture

**ALWAYS use microservices architecture** - decompose into specialized, independently deployable containers:

1. **Web UI Container**: ReactJS frontend (separate container, served via nginx)
2. **Application API Container**: Flask + Flask-Security-Too backend (separate container)
3. **Connector Container**: External system integration (separate container, optional)

**Default Container Separation**: Web UI and API are ALWAYS separate containers by default. This provides:
- Independent scaling of frontend and backend
- Different resource allocation per service
- Separate deployment lifecycles
- Technology-specific optimization

**Benefits**:
- Independent scaling
- Technology diversity
- Team autonomy
- Resilience
- Continuous deployment

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NGINX (optional)                               │
└─────────────────────────────────────────────────────────────────────────────┘
          │                        │                          │
┌─────────┴─────────┐   ┌─────────┴─────────┐   ┌────────────┴────────────┐
│  WebUI Container  │   │  Flask Backend    │   │    Go Backend           │
│  (Node.js/React)  │   │  (Flask/PyDAL)    │   │    (XDP/AF_XDP)         │
│                   │   │                   │   │                         │
│ - React SPA       │   │ - /api/v1/auth/*  │   │ - High-perf networking  │
│ - Proxies to APIs │   │ - /api/v1/users/* │   │ - XDP packet processing │
│ - Static assets   │   │ - /api/v1/hello   │   │ - AF_XDP zero-copy      │
│ - Port 3000       │   │ - Port 5000       │   │ - NUMA-aware memory     │
└───────────────────┘   └───────────────────┘   │ - Port 8080             │
                                 │              └─────────────────────────┘
                        ┌────────┴────────┐
                        │   PostgreSQL    │
                        │ MySQL/MariaDB   │
                        │ SQLite (dev)    │
                        └─────────────────┘
```

### Default Roles (WebUI)

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: user CRUD, settings, all features |
| **Maintainer** | Read/write access to resources, no user management |
| **Viewer** | Read-only access to resources |

## Version Management System

**Format**: `vMajor.Minor.Patch.build`
- **Major**: Breaking changes, API changes, removed features
- **Minor**: Significant new features and functionality additions
- **Patch**: Minor updates, bug fixes, security patches
- **Build**: Epoch64 timestamp of build time

**Update Commands**:
```bash
./scripts/version/update-version.sh          # Increment build timestamp
./scripts/version/update-version.sh patch    # Increment patch version
./scripts/version/update-version.sh minor    # Increment minor version
./scripts/version/update-version.sh major    # Increment major version
```

## Development Workflow

### Local Development Setup
```bash
git clone <repository-url>
cd IceCharts
make setup                    # Install dependencies
make dev                      # Start development environment
```

### Essential Commands
```bash
# Development
make dev                      # Start development services
make test                     # Run all tests
make lint                     # Run linting
make build                    # Build all services
make clean                    # Clean build artifacts

# Production
make docker-build             # Build containers
make docker-push              # Push to registry
make deploy-dev               # Deploy to development
make deploy-prod              # Deploy to production

# Testing
make test-unit               # Run unit tests
make test-integration        # Run integration tests
make test-e2e                # Run end-to-end tests

# License Management
make license-validate        # Validate license
make license-check-features  # Check available features
```

## Key Directories

- `services/webui/` - React frontend application
- `services/flask-backend/` - Flask API backend
- `docs/` - Project documentation
- `k8s/` - Kubernetes deployment manifests (Helm and Kustomize)
- `tests/` - Test suites
- `scripts/` - Utility scripts
- `config/` - Configuration files

## Temporary Files Policy

**IMPORTANT:** Any temporary reports, checklists, implementation summaries, or other transient documents created by Claude or its task agents during development sessions should be stored in `/tmp`, NOT in the repository.

Examples of temporary files that belong in `/tmp`:
- Implementation checklists
- Files modified lists
- Quick start guides generated during implementation
- Session-specific summaries or manifests
- Progress tracking documents
- Completion status reports

These files are useful during active development sessions but provide no long-term value to users, admins, or developers.

**Permanent documentation** (feature guides, API references, architecture docs) should go in the `docs/` folder.

## Critical Development Rules

### Development Philosophy: Safe, Stable, and Feature-Complete

**NEVER take shortcuts or the "easy route" - ALWAYS prioritize safety, stability, and feature completeness**

#### Core Principles
- **No Quick Fixes**: Resist quick workarounds or partial solutions
- **Complete Features**: Fully implemented with proper error handling and validation
- **Safety First**: Security, data integrity, and fault tolerance are non-negotiable
- **Stable Foundations**: Build on solid, tested components
- **Future-Proof Design**: Consider long-term maintainability and scalability
- **No Technical Debt**: Address issues properly the first time

#### Red Flags (Never Do These)
- Skipping input validation "just this once"
- Writing custom validators instead of using shared libraries (py_libs/go_libs/node_libs)
- Hardcoding credentials or configuration
- Ignoring error returns or exceptions
- Commenting out failing tests to make CI pass
- Deploying without proper testing
- Using deprecated or unmaintained dependencies
- Implementing partial features with "TODO" placeholders
- Bypassing security checks for convenience
- Assuming data is valid without verification
- Leaving debug code or backdoors in production

#### Quality Checklist Before Completion
- ✅ All error cases handled properly
- ✅ Unit tests cover all code paths
- ✅ Integration tests verify component interactions
- ✅ Security requirements fully implemented
- ✅ Performance meets acceptable standards
- ✅ Documentation complete and accurate
- ✅ Code review standards met
- ✅ No hardcoded secrets or credentials
- ✅ Logging and monitoring in place
- ✅ Build passes in containerized environment
- ✅ No security vulnerabilities in dependencies
- ✅ Edge cases and boundary conditions tested

### Git Workflow
- **NEVER commit automatically** unless explicitly requested by the user
- **NEVER push to remote repositories** under any circumstances
- **ONLY commit when explicitly asked** - never assume commit permission
- Always use feature branches for development
- Require pull request reviews for main branch
- Automated testing must pass before merge

**Before Every Commit - Security Scanning**:
- **Run security audits on all modified packages**:
  - **Go packages**: Run `gosec ./...` on modified Go services
  - **Node.js packages**: Run `npm audit` on modified Node.js services
  - **Python packages**: Run `bandit -r .` and `safety check` on modified Python services
- **Do NOT commit if security vulnerabilities are found** - fix all issues first
- **Document vulnerability fixes** in commit message if applicable

**Before Every Commit - API Testing**:
- **Create and run API testing scripts** for each modified container service
- **Testing scope**: All new endpoints and modified functionality
- **Test files location**: `tests/api/` directory with service-specific subdirectories
  - `tests/api/flask-backend/` - Flask backend API tests
  - `tests/api/go-backend/` - Go backend API tests
  - `tests/api/webui/` - WebUI container tests
- **Run before commit**: Each test script should be executable and pass completely
- **Test coverage**: Health checks, authentication, CRUD operations, error cases
- **Command pattern**: `cd services/<service-name> && npm run test:api` or equivalent

**Before Every Commit - Screenshots**:
- **Run screenshot tool to update UI screenshots in documentation**
  - Run `cd services/webui && npm run screenshots` to capture current UI state
  - This automatically removes old screenshots and captures fresh ones
  - Commit updated screenshots with relevant feature/documentation changes

### Local State Management (Crash Recovery)
- **ALWAYS maintain local .PLAN and .TODO files** for crash recovery
- **Keep .PLAN file updated** with current implementation plans and progress
- **Keep .TODO file updated** with task lists and completion status
- **Update these files in real-time** as work progresses
- **Add to .gitignore**: Both .PLAN and .TODO files must be in .gitignore
- **File format**: Use simple text format for easy recovery
- **Automatic recovery**: Upon restart, check for existing files to resume work

### Dependency Security Requirements
- **ALWAYS check for Dependabot alerts** before every commit
- **Monitor vulnerabilities via Socket.dev** for all dependencies
- **Mandatory security scanning** before any dependency changes
- **Fix all security alerts immediately** - no commits with outstanding vulnerabilities
- **Regular security audits**: `npm audit`, `go mod audit`, `safety check`

### Linting & Code Quality Requirements
- **ALL code must pass linting** before commit - no exceptions
- **Python**: flake8, black, isort, pytest, pytest-cov, mypy (type checking), bandit (security)
- **JavaScript/TypeScript**: ESLint, Prettier, TypeScript, Vitest, Testing Library
- **Go**: golangci-lint (includes staticcheck, gosec, etc.)
- **Ansible**: ansible-lint
- **Docker**: hadolint, trivy
- **YAML**: yamllint
- **Markdown**: markdownlint
- **Shell**: shellcheck
- **CodeQL**: All code must pass CodeQL security analysis
- **PEP Compliance**: Python code must follow PEP 8, PEP 257 (docstrings), PEP 484 (type hints)

### Build & Deployment Requirements
- **NEVER mark tasks as completed until successful build verification**
- All Go and Python builds MUST be executed within Docker containers
- Use containerized builds for local development and CI/CD pipelines
- Build failures must be resolved before task completion

### Documentation Standards
- **Markdown file locations** (STRICT):
  - `{PROJECT_ROOT}/README.md` - Project overview only
  - `{PROJECT_ROOT}/CLAUDE.md` - Claude Code context only
  - `{PROJECT_ROOT}/docs/` - ALL other markdown documentation
  - **NEVER nest markdown files in subdirectories** outside of `docs/`
- **README.md**: Keep as overview and pointer to comprehensive docs/ folder
- **docs/ folder**: Create comprehensive documentation for all aspects
- **RELEASE_NOTES.md**: Maintain in docs/ folder, prepend new version releases to top
- Update CLAUDE.md when adding significant context
- **Build status badges**: Always include in README.md
- **ASCII art**: Include catchy, project-appropriate ASCII art in README
- **Company homepage**: Point to www.penguintech.io
- **License**: All projects use Limited AGPL3 with preamble for fair use

### File Size Limits
- **Maximum file size**: 25,000 characters for ALL code and markdown files
- **Split large files**: Decompose into modules, libraries, or separate documents
- **CLAUDE.md exception**: Maximum 39,000 characters (only exception to 25K rule)
- **High-level approach**: CLAUDE.md contains high-level context and references detailed docs
- **Documentation strategy**: Create detailed documentation in `docs/` folder and link to them from CLAUDE.md
- **Keep focused**: Critical context, architectural decisions, and workflow instructions only
- **User approval required**: ALWAYS ask user permission before splitting CLAUDE.md files
- **Use Task Agents**: Utilize task agents (subagents) to be more expedient and efficient when making changes to large files, updating or reviewing multiple files, or performing complex multi-step operations
- **Avoid sed/cat**: Use sed and cat commands only when necessary; prefer dedicated Read/Edit/Write tools for file operations

## Development Standards

Comprehensive development standards are documented separately to keep this file concise.

📚 **Complete Standards Documentation**: [Development Standards](docs/STANDARDS.md)

### Quick Reference

**Database Standards**:
- PyDAL mandatory for ALL Python applications
- Thread-safe usage with thread-local connections
- Environment variable configuration for all database settings
- Connection pooling and retry logic required
- Hybrid approach: SQLAlchemy for init, PyDAL for day-to-day operations

**Protocol Support**:
- REST API, gRPC, HTTP/1.1, HTTP/2, HTTP/3 support
- Environment variables for protocol configuration
- Multi-protocol implementation required

**Performance Optimization (Python)**:
- Dataclasses with slots mandatory (30-50% memory reduction)
- Type hints required for all Python code
- asyncio for I/O-bound operations
- threading for blocking I/O
- multiprocessing for CPU-bound operations
- Avoid premature optimization - profile first

**High-Performance Networking (Case-by-Case)**:
- XDP (eXpress Data Path): Kernel-level packet processing
- AF_XDP: Zero-copy socket for user-space packet processing
- Use only for network-intensive applications requiring >100K packets/sec
- Evaluate Python vs Go based on traffic requirements

**Microservices Architecture**:
- Web UI, API, and Connector as **separate containers by default**
- Single responsibility per service
- API-first design
- Independent deployment and scaling
- Each service has its own Dockerfile and dependencies

**Docker Standards**:
- Multi-arch builds (amd64/arm64)
- Debian-slim base images
- Docker Compose for local development
- Minimal host port exposure

**Testing**:
- Unit tests: Network isolated, mocked dependencies
- Integration tests: Component interactions
- E2E tests: Critical workflows
- Performance tests: Scalability validation

**Security**:
- TLS 1.2+ required
- Input validation mandatory
- JWT, MFA, mTLS standard
- SSO as enterprise feature

## External App Integration (Service Accounts)

IceCharts supports service account authentication for external application integration (e.g., Elder).

**Documentation**: [Integration Guide](INTEGRATION.md)

Key Features:
- Long-lived JWT tokens (up to 1 year)
- Fine-grained scoped permissions (drawings:read, exports:create, etc.)
- Configurable rate limits (default: 1000/hour)
- Admin management via API

Quick Example:
```bash
# Using a service account token
curl -X GET "https://your-icecharts.com/api/v1/drawings" \
  -H "Authorization: Bearer <service-account-token>"
```

## Common Integration Patterns

### Flask + Flask-Security-Too + PyDAL
```python
from flask import Flask
from flask_security import Security, auth_required, hash_password
from flask_security.datastore import DataStore, UserDataMixin, RoleDataMixin
from pydal import DAL, Field
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT')

# PyDAL database setup
db = DAL(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
    pool_size=10,
    migrate=True
)

# Define user and role tables
db.define_table('auth_user',
    Field('email', 'string', requires=IS_EMAIL(), unique=True),
    Field('username', 'string', unique=True),
    Field('password', 'string'),
    Field('active', 'boolean', default=True),
    Field('fs_uniquifier', 'string', unique=True),
    Field('confirmed_at', 'datetime'),
    migrate=True
)

db.define_table('auth_role',
    Field('name', 'string', unique=True),
    Field('description', 'text'),
    migrate=True
)

db.define_table('auth_user_roles',
    Field('user_id', 'reference auth_user'),
    Field('role_id', 'reference auth_role'),
    migrate=True
)

# Custom PyDAL datastore for Flask-Security-Too
class PyDALUserDatastore(DataStore):
    def __init__(self, db, user_model, role_model):
        self.db = db
        self.user_model = user_model
        self.role_model = role_model

    def put(self, model):
        self.db.commit()
        return model

    def delete(self, model):
        self.db(self.user_model.id == model.id).delete()
        self.db.commit()

    def find_user(self, **kwargs):
        query = self.db(self.user_model)
        for key, value in kwargs.items():
            if hasattr(self.user_model, key):
                query = query(self.user_model[key] == value)
        row = query.select().first()
        return row

# Initialize Flask-Security-Too
user_datastore = PyDALUserDatastore(db, db.auth_user, db.auth_role)
security = Security(app, user_datastore)

@app.route('/api/protected')
@auth_required()
def protected_resource():
    return {'message': 'This is a protected endpoint'}

@app.route('/healthz')
def health():
    return {'status': 'healthy'}, 200
```

### Database Integration (PyDAL with Multi-Database Support)
```python
from pydal import DAL, Field
from dataclasses import dataclass
import os

# Valid PyDAL DB_TYPE values for input validation
VALID_DB_TYPES = {
    'postgres', 'postgresql', 'mysql', 'sqlite', 'mssql',
    'oracle', 'db2', 'firebird', 'informix', 'ingres',
    'cubrid', 'sapdb'
}

# IceCharts-specific: Only support postgres, mysql, sqlite
ICECHARTS_SUPPORTED_DB_TYPES = {'postgres', 'mysql', 'sqlite'}

@dataclass(slots=True, frozen=True)
class UserModel:
    """User model with slots for memory efficiency"""
    id: int
    email: str
    name: str
    active: bool

def get_db_connection() -> DAL:
    """Initialize PyDAL with environment variables and multi-DB support"""
    db_type = os.getenv('DB_TYPE', 'postgres')

    # Input validation - ensure DB_TYPE matches IceCharts requirements
    if db_type not in ICECHARTS_SUPPORTED_DB_TYPES:
        raise ValueError(
            f"Invalid DB_TYPE: {db_type}. "
            f"IceCharts supports only: {ICECHARTS_SUPPORTED_DB_TYPES}"
        )

    # Build connection URI
    db_uri = f"{db_type}://" \
             f"{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@" \
             f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/" \
             f"{os.getenv('DB_NAME')}"

    # MariaDB Galera specific settings
    galera_mode = os.getenv('GALERA_MODE', 'false').lower() == 'true'

    dal_kwargs = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
        'migrate_enabled': True,
        'check_reserved': ['all'],
        'lazy_tables': True
    }

    # Galera-specific: handle wsrep_sync_wait for read-your-writes consistency
    if galera_mode and db_type == 'mysql':
        dal_kwargs['driver_args'] = {'init_command': 'SET wsrep_sync_wait=1'}

    return DAL(db_uri, **dal_kwargs)
```

### ReactJS Frontend Integration
```javascript
// API client for Flask backend
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Protected component example
import React, { useEffect, useState } from 'react';

function ProtectedComponent() {
  const [data, setData] = useState(null);

  useEffect(() => {
    apiClient.get('/api/protected')
      .then(response => setData(response.data))
      .catch(error => console.error('Error:', error));
  }, []);

  return <div>{data?.message}</div>;
}
```

### License-Gated Features (Python)
```python
from shared.licensing import license_client, requires_feature
from flask_security import auth_required

@app.route('/api/advanced/analytics')
@auth_required()
@requires_feature("advanced_analytics")
def generate_advanced_report():
    """Requires authentication AND professional+ license"""
    return {'report': analytics.generate_report()}
```

### Monitoring Integration
```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.route('/metrics')
def metrics():
    return generate_latest(), {'Content-Type': 'text/plain'}
```

## Website Integration Requirements

**Required websites**: Marketing/Sales (Node.js) + Documentation (Markdown)

**Design**: Multi-page, modern aesthetic, subtle gradients, responsive, performance-focused

**Repository**: Sparse checkout submodule from `github.com/penguintechinc/website` with `icecharts/` and `icecharts-docs/` folders

**IceCharts-Specific Website Components:**

**Marketing Site (icecharts folder):**
- **Feature showcase**: Interactive diagrams and visualization demos
- **Pricing page**: License tier information (Free, Professional, Enterprise)
- **Use cases**: Infrastructure visualization, network diagramming, system architecture
- **Demo/Sandbox**: Live IceCharts editor showing diagram creation capabilities
- **API documentation**: Embed from docs site or link to API reference

**Documentation Site (icecharts-docs folder):**
- **Getting Started**: Installation, basic diagram creation, export options
- **User Guide**: Drawing tools, shapes library, diagram templates, collaboration features
- **API Reference**: REST endpoints, service account integration, webhook support
- **Architecture Docs**: Multi-database setup, clustering, high-availability deployment
- **Integration Guides**: Elder integration, external system connectors, data import/export
- **FAQ**: Common diagramming questions, database selection, deployment options

**Internationalization (i18n)**: Support English (primary) and additional languages as needed

**Performance Requirements:**
- Home page <2s load time (optimized images, lazy loading)
- Demo sandbox <3s interactive
- Docs search indexing (Algolia or similar)

## Troubleshooting & Support

### Common Issues
1. **Port Conflicts**: Check docker-compose port mappings
2. **Database Connections**: Verify connection strings and permissions
3. **License Validation Failures**: Check license key format and network connectivity
4. **Build Failures**: Check dependency versions and compatibility
5. **Test Failures**: Review test environment setup

### Debug Commands
```bash
# Container debugging
docker-compose logs -f service-name
docker exec -it container-name /bin/bash

# Application debugging
make debug                    # Start with debug flags
make logs                     # View application logs
make health                   # Check service health

# License debugging
make license-debug            # Test license server connectivity
make license-validate         # Validate current license
```

### Support Resources
- **Technical Documentation**: [Development Standards](docs/STANDARDS.md)
- **License Integration**: [License Server Guide](docs/licensing/license-server-integration.md)
- **Integration Support**: support@penguintech.io
- **Sales Inquiries**: sales@penguintech.io
- **License Server Status**: https://status.penguintech.io


## License & Legal

**License File**: `LICENSE.md` (located at project root)

**License Type**: Limited AGPL-3.0 with commercial use restrictions and Contributor Employer Exception

The `LICENSE.md` file is located at the project root following industry standards. This project uses a modified AGPL-3.0 license with additional exceptions for commercial use and special provisions for companies employing contributors.


---

**IceCharts Version**: 1.3.0
**Template Version**: 1.5.0
**Last Updated**: 2025-12-18
**Maintained by**: Penguin Tech Inc
**License Server**: https://license.penguintech.io

**Key Features in v1.3.0:**
- Three-container architecture: Flask backend, Go backend, WebUI shell
- WebUI shell with Node.js + React, role-based access (Admin, Maintainer, Viewer)
- Flask backend with PyDAL, JWT auth, user management
- Go backend with XDP/AF_XDP support, NUMA-aware memory pools
- GitHub Actions workflows for multi-arch builds (AMD64, ARM64)
- Multi-database support (PostgreSQL, MySQL, MariaDB, SQLite)
- MariaDB Galera cluster support with WSREP and retry logic
- Hybrid database initialization (SQLAlchemy) and operations (PyDAL)
- Docker Compose updated for new architecture

*This comprehensive context provides IceCharts developers with production-ready foundation for enterprise software development with comprehensive tooling, security, operational capabilities, integrated licensing management, and multi-database support.*
