# Development Standards

<<<<<<< HEAD
Welcome to the Penguin Tech standards hub! 🐧 This is your go-to resource for building awesome, production-ready software.

> 🚫 **DO NOT MODIFY** this file or any files in `docs/standards/`. These are centralized template standards that will be overwritten when updated. For app-specific documentation, use [`docs/APP_STANDARDS.md`](APP_STANDARDS.md) instead.

## Getting Started

Ready to build something great? Here's your quick-start checklist:

- Read your language selection criteria (Python vs Go)
- Set up Flask-Security-Too for authentication
- Pick your database (PostgreSQL recommended)
- Design your APIs with versioning in mind
- Run the pre-commit checks before pushing code
- Make sure your tests pass (especially smoke tests!)

## Standards by Category

Here's what you'll find in our comprehensive standards library:

| Icon | Category | Focus Area |
|------|----------|-----------|
| 🐍 | [Language Selection](standards/LANGUAGE_SELECTION.md) | Python 3.13 or Go 1.24.x? We'll help you decide |
| 🔐 | [Authentication](standards/AUTHENTICATION.md) | Flask-Security-Too, RBAC, SSO, password magic |
| ⚛️ | [Frontend](standards/FRONTEND.md) | ReactJS patterns, hooks, components galore |
| 🗄️ | [Database](standards/DATABASE.md) | PyDAL, SQLAlchemy, PostgreSQL + 3 others |
| 🔌 | [API & Protocols](standards/API_PROTOCOLS.md) | REST, gRPC, versioning, deprecation strategies |
| ⚡ | [Performance](standards/PERFORMANCE.md) | Dataclasses, asyncio, threading, blazing fast |
| 🏗️ | [Architecture](standards/ARCHITECTURE.md) | Microservices, Docker, multi-arch builds |
| ☸️ | [Kubernetes](standards/KUBERNETES.md) | Helm, Kustomize, cloud-native deployments |
| 🧪 | [Testing](standards/TESTING.md) | Unit, integration, E2E, smoke tests |
| 🛡️ | [Security](standards/SECURITY.md) | TLS, secrets management, vulnerability scanning |
| 📚 | [Documentation](standards/DOCUMENTATION.md) | READMEs, release notes, keeping it clean |
| 🎨 | [UI Design](standards/UI_DESIGN.md) | Components, patterns, responsive design |
| 🔗 | [Integrations](standards/INTEGRATIONS.md) | WaddleAI, MarchProxy, License Server |

## The Core Five (Most Important)

### 1. Language Selection: Python or Go?
Start with Python 3.13 for most applications. Go is for speed demons only (>10K req/sec). Profile first, switch only when you really need to.

> **Pro tip**: 9 out of 10 times, Python will do the job beautifully and get you to market faster.

[Learn more](standards/LANGUAGE_SELECTION.md)

### 2. Authentication: Flask-Security-Too
All Flask apps get security out of the box. RBAC, JWT, password reset, 2FA, even SSO for enterprise customers. Auto-creates an admin user on startup (credentials: admin@localhost.local / admin123).

> **Remember**: Never skip security. It's not "nice to have" - it's required.

[Learn more](standards/AUTHENTICATION.md)

### 3. Database: Multi-DB Support by Default
Use PyDAL for runtime operations (required) and SQLAlchemy for schema creation. We support PostgreSQL (your default), MySQL, MariaDB Galera, and SQLite. Choose via the `DB_TYPE` environment variable.

> **Key insight**: Pick PostgreSQL unless you have a specific reason not to. It's rock solid.

[Learn more](standards/DATABASE.md)

### 4. API Design: Version Everything
All REST APIs use `/api/v{major}/endpoint`. Inter-container communication prefers gRPC. Support at least 2 previous versions (current + 2 prior). Plan for deprecation from day one.

> **Best practice**: Design APIs for extensibility. Small, flexible inputs. Backward-compatible responses.

[Learn more](standards/API_PROTOCOLS.md)

### 5. Testing: Smoke Tests Are Non-Negotiable
Run smoke tests before every commit. They verify your build works, services start, APIs respond, and the UI loads. Five minutes of testing saves you hours of debugging later.

> **Golden rule**: If smoke tests pass, you can commit with confidence.

[Learn more](standards/TESTING.md)

## Pre-Commit Checklist

Before you commit, run this magic command:
=======
**⚠️ Important**: This is a company-wide standards document containing best practices and patterns that apply across all Penguin Tech Inc projects. **Application-specific standards, architecture decisions, requirements, and context should be documented in `docs/APP_STANDARDS.md` instead.** This separation allows the template STANDARDS.md to be updated across all projects without losing app-specific information.

## Overview

This document serves as an index to comprehensive development standards organized by category. Each category has detailed documentation in the `docs/standards/` directory.

## Quick Reference

| Category | File | Key Topics |
|----------|------|------------|
| **Language Selection** | [LANGUAGE_SELECTION.md](standards/LANGUAGE_SELECTION.md) | Python 3.13 vs Go 1.24.x decision criteria, traffic thresholds |
| **Authentication** | [AUTHENTICATION.md](standards/AUTHENTICATION.md) | Flask-Security-Too, RBAC, SSO, password reset, login UI |
| **Frontend** | [FRONTEND.md](standards/FRONTEND.md) | ReactJS patterns, API client, hooks, components |
| **Database** | [DATABASE.md](standards/DATABASE.md) | PyDAL, SQLAlchemy, multi-DB support, MariaDB Galera |
| **API & Protocols** | [API_PROTOCOLS.md](standards/API_PROTOCOLS.md) | REST, gRPC, HTTP/3, API versioning, deprecation |
| **Performance** | [PERFORMANCE.md](standards/PERFORMANCE.md) | Dataclasses, asyncio, threading, XDP/AF_XDP |
| **Architecture** | [ARCHITECTURE.md](standards/ARCHITECTURE.md) | Microservices, Docker, multi-arch builds, MarchProxy |
| **Kubernetes** | [KUBERNETES.md](standards/KUBERNETES.md) | Helm v3, Kustomize, K8s deployments, best practices |
| **Testing** | [TESTING.md](standards/TESTING.md) | Unit, integration, E2E, smoke tests, performance |
| **Security** | [SECURITY.md](standards/SECURITY.md) | TLS, secrets, vulnerability scanning, CodeQL |
| **Documentation** | [DOCUMENTATION.md](standards/DOCUMENTATION.md) | README, docs structure, release notes |
| **UI Design** | [UI_DESIGN.md](standards/UI_DESIGN.md) | Design patterns, components, styling, responsive |
| **Integrations** | [INTEGRATIONS.md](standards/INTEGRATIONS.md) | WaddleAI, MarchProxy, License Server patterns |

## Critical Standards Summary

### Language Selection (Case-by-Case)
- **Python 3.13**: Default for most applications (<10K req/sec)
- **Go 1.24.x**: Only for high-traffic/performance-critical (>10K req/sec)
- **Decision Matrix**: Profile first, start with Python, switch only when necessary

📚 **Details**: [standards/LANGUAGE_SELECTION.md](standards/LANGUAGE_SELECTION.md)

### Authentication (Mandatory)
- **Flask-Security-Too**: Required for ALL Flask applications
- **Features**: RBAC, JWT, password reset, 2FA, SSO (enterprise)
- **Default Admin**: Auto-created on startup (admin@localhost.local / admin123)
- **Password Reset**: Forgot password (SMTP required) + Change password (always available)

📚 **Details**: [standards/AUTHENTICATION.md](standards/AUTHENTICATION.md)

### Frontend (Mandatory)
- **ReactJS**: Required for ALL frontend applications
- **Node.js**: 18+ for build tooling
- **API Client**: Centralized axios client with auth interceptors

📚 **Details**: [standards/FRONTEND.md](standards/FRONTEND.md)

### Database (Mandatory)
- **PyDAL**: Runtime operations and migrations (mandatory)
- **SQLAlchemy**: Database initialization only
- **Multi-DB**: PostgreSQL (default), MySQL, MariaDB Galera, SQLite
- **DB_TYPE**: Environment variable for database selection

📚 **Details**: [standards/DATABASE.md](standards/DATABASE.md)

### API Design Principles
- **Versioning**: ALL APIs use `/api/v{major}/endpoint` format
- **REST**: External communication (clients, third-party)
- **gRPC**: Inter-container communication (preferred for performance)
- **HTTP/3**: Consider for high-performance scenarios (>10K req/sec)
- **Deprecation**: Support N-2 versions minimum (current + 2 previous)

📚 **Details**: [standards/API_PROTOCOLS.md](standards/API_PROTOCOLS.md)

### Performance Optimization
- **Dataclasses**: Use slots for 30-50% memory reduction
- **Type Hints**: Required for all Python code
- **Concurrency**:
  - `asyncio` for I/O-bound (>100 concurrent requests)
  - `threading` for blocking I/O and legacy integrations
  - `multiprocessing` for CPU-bound operations
- **Profile First**: Avoid premature optimization

📚 **Details**: [standards/PERFORMANCE.md](standards/PERFORMANCE.md)

### Microservices Architecture
- **Three-Container Pattern**: Flask backend, Go backend (optional), WebUI
- **Independent Deployment**: Each service has own Dockerfile
- **API-First Design**: Well-defined contracts between services
- **MarchProxy**: External API gateway/LB (not in default deployment)

📚 **Details**: [standards/ARCHITECTURE.md](standards/ARCHITECTURE.md)

### Docker Standards
- **Multi-Arch**: Build for amd64 and arm64
- **Base Images**: Debian-slim preferred
- **Cross-Architecture Testing**: Test on alternate arch before commit (QEMU)
- **Multi-Stage Builds**: Minimize image size

📚 **Details**: [standards/ARCHITECTURE.md](standards/ARCHITECTURE.md#docker-standards)

### Testing Requirements
- **Smoke Tests**: Build, run, API health, page loads (mandatory before commit)
- **Unit Tests**: Network isolated, mocked dependencies
- **Integration Tests**: Component interactions
- **E2E Tests**: Critical user workflows
- **Mock Data**: 3-4 items per feature/entity

📚 **Details**: [standards/TESTING.md](standards/TESTING.md)

### Security Standards
- **TLS**: 1.2 minimum, prefer TLS 1.3
- **Input Validation**: Mandatory for all inputs
- **Secrets**: Environment variables, never in code
- **Scanning**: Trivy, CodeQL (mandatory before commit)
- **Dependencies**: Monitor Dependabot, fix all vulnerabilities

📚 **Details**: [standards/SECURITY.md](standards/SECURITY.md)

## Pre-Commit Requirements

**CRITICAL - Run before every commit:**
>>>>>>> origin/v1.0.X

```bash
./scripts/pre-commit/pre-commit.sh
```

<<<<<<< HEAD
Here's what it checks:

- [ ] Linters pass (flake8, eslint, golangci-lint, ansible-lint)
- [ ] Security scans are clean (gosec, bandit, npm audit, Trivy)
- [ ] No secrets leaked into code
- [ ] Smoke tests pass (build, run, API, UI loads)
- [ ] Full test suite passes
- [ ] Version updated if needed
- [ ] Docker builds successfully with debian-slim

> **Important**: Only commit when explicitly asked. Run this script, verify everything passes, then request approval. No shortcuts!

[Full pre-commit guide](PRE_COMMIT.md)

## Keep It Clean: File Size Limits

Files have limits for a reason (keeps things maintainable and fast):

- **Code and markdown**: Max 25,000 characters
- **CLAUDE.md**: Max 39,000 characters (only exception)
- **When you hit the limit**: Split into modules, separate documents, or a new file
- **Documentation strategy**: Detailed docs live in `docs/`, high-level context in CLAUDE.md

## App-Specific Standards

This document covers company-wide best practices. Your app is unique, so app-specific stuff goes in [`docs/APP_STANDARDS.md`](APP_STANDARDS.md):

- Custom architecture patterns
- Business logic requirements
- Domain-specific data models
- App-specific security rules
- Integration requirements unique to you
- Custom API endpoints
- Performance needs specific to your use case

> **Why split them?** So we can update template standards across all projects without losing your app-specific context. Everyone wins!

---

## Need More Details?

Dive into the individual standards documents for the full picture:

- [Language Selection](standards/LANGUAGE_SELECTION.md) - Python vs Go decision matrix
- [Authentication](standards/AUTHENTICATION.md) - Flask-Security-Too, RBAC, SSO
- [Frontend Development](standards/FRONTEND.md) - ReactJS patterns and best practices
- [Database Standards](standards/DATABASE.md) - PyDAL, multi-database support
- [API and Protocols](standards/API_PROTOCOLS.md) - REST, gRPC, versioning
- [Performance](standards/PERFORMANCE.md) - Optimization, concurrency, speed
- [Architecture](standards/ARCHITECTURE.md) - Microservices, Docker
- [Kubernetes](standards/KUBERNETES.md) - Helm, Kustomize, deployments
- [Testing](standards/TESTING.md) - Unit, integration, E2E, smoke tests
- [Security](standards/SECURITY.md) - TLS, secrets, scanning
- [Documentation](standards/DOCUMENTATION.md) - READMEs, release notes
- [UI Design](standards/UI_DESIGN.md) - Components, patterns, styling
- [Integrations](standards/INTEGRATIONS.md) - WaddleAI, MarchProxy, License Server

---

**Happy coding!** These standards exist to help you build reliable, secure, performant software. Questions? Check the docs. Still stuck? Ping your team!

**Template Version**: 1.3.0 | **Last Updated**: 2026-01-22 | **Maintained by**: Penguin Tech Inc
=======
**Checklist:**
1. ✅ All linters pass (flake8, eslint, golangci-lint, ansible-lint, etc.)
2. ✅ Security scans clean (gosec, bandit, npm audit, Trivy)
3. ✅ No secrets in code
4. ✅ Smoke tests pass (build, run, API, UI)
5. ✅ Full test suite passes
6. ✅ Version updated if needed
7. ✅ Docker builds successful (debian-slim base)

**Only commit when explicitly asked** — run pre-commit script, verify all checks pass, then wait for approval.

📚 **Complete checklist**: [PRE_COMMIT.md](PRE_COMMIT.md)

## File Size Limits

- **Maximum file size**: 25,000 characters for ALL code and markdown files
- **CLAUDE.md exception**: Maximum 39,000 characters (only exception)
- **Split large files**: Use modules, libraries, or separate documents
- **Documentation strategy**: Detailed docs in `docs/` folder, high-level context in CLAUDE.md

## Application-Specific Standards

**⚠️ IMPORTANT**: Application-specific standards, architectural decisions, requirements, and context belong in:

📚 **[docs/APP_STANDARDS.md](APP_STANDARDS.md)**

This includes:
- Application-specific architecture patterns
- Custom authentication/authorization rules
- Business logic requirements
- Domain-specific data models
- Integration requirements unique to your app
- Performance characteristics specific to your use case
- Custom API endpoints and contracts
- Application-specific security requirements

The separation between company-wide standards (this document) and app-specific standards (APP_STANDARDS.md) ensures:
- Template standards can be updated across all projects
- Application-specific context is preserved
- Clear separation of concerns
- Easier maintenance and updates

---

## Complete Standards Documentation

For comprehensive details on each category, refer to the individual standards documents in the `docs/standards/` directory:

- **[Language Selection Criteria](standards/LANGUAGE_SELECTION.md)** - Python vs Go decision matrix
- **[Authentication Standards](standards/AUTHENTICATION.md)** - Flask-Security-Too, RBAC, SSO, password reset
- **[Frontend Development Standards](standards/FRONTEND.md)** - ReactJS patterns and best practices
- **[Database Standards](standards/DATABASE.md)** - PyDAL, multi-database support, migrations
- **[API and Protocol Standards](standards/API_PROTOCOLS.md)** - REST, gRPC, versioning, deprecation
- **[Performance Standards](standards/PERFORMANCE.md)** - Optimization, concurrency, high-performance networking
- **[Architecture Standards](standards/ARCHITECTURE.md)** - Microservices, Docker, containerization
- **[Kubernetes Standards](standards/KUBERNETES.md)** - Helm, Kustomize, K8s deployments, best practices
- **[Testing Standards](standards/TESTING.md)** - Unit, integration, E2E, smoke, performance tests
- **[Security Standards](standards/SECURITY.md)** - TLS, secrets, scanning, vulnerability management
- **[Documentation Standards](standards/DOCUMENTATION.md)** - README, docs structure, release notes
- **[Web UI Design Standards](standards/UI_DESIGN.md)** - Design patterns, components, styling
- **[Integration Standards](standards/INTEGRATIONS.md)** - WaddleAI, MarchProxy, License Server

---

**Template Version**: 1.3.0
**Last Updated**: 2026-01-13
**Maintained by**: Penguin Tech Inc
>>>>>>> origin/v1.0.X
