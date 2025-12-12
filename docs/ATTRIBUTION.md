# Attribution and Open Source Acknowledgments

IceCharts is built with gratitude to the many open source projects and libraries that make this application possible. This document acknowledges all third-party libraries, icons, and resources used in this project.

## Project Information

**Organization**: [Penguin Tech Inc](https://www.penguintech.io)
**Support**: [info@penguintech.group](mailto:info@penguintech.group)
**License**: AGPL-3.0 (with commercial licensing available)
**Repository**: https://github.com/penguintechinc/IceCharts

---

## Backend Dependencies (Node.js)

### Core Framework & HTTP

- **Express.js** (^4.19.2) - Web application framework
- **Axios** (^1.7.7) - HTTP client library
- **Compression** (^1.7.4) - HTTP compression middleware
- **CORS** (^2.8.5) - Cross-Origin Resource Sharing middleware

### Authentication & Security

- **jsonwebtoken** (^9.0.3) - JWT implementation
- **bcryptjs** (^2.4.3) - Password hashing
- **Helmet** (^7.1.0) - HTTP security headers
- **dotenv** (^16.4.5) - Environment variable management

### Database

- **pg** (^8.12.0) - PostgreSQL client
- **redis** (^4.7.0) - Redis client

### Input Validation & Schemas

- **Joi** (^17.13.3) - Schema validation library

### Logging & Monitoring

- **Winston** (^3.14.2) - Logging library
- **Morgan** (^1.10.0) - HTTP request logging middleware
- **prom-client** (^15.1.3) - Prometheus metrics client

### Automation & Screenshots

- **Puppeteer** (^24.32.1) - Headless Chrome/Chromium automation

### Development Tools

- **TypeScript** (^5.7.2) - Static type checking
- **ESLint** (^9.16.0) - Linting utility
- **Prettier** (^3.4.2) - Code formatter
- **Jest** (^29.7.0) - Testing framework
- **Playwright** (^1.48.2) - Browser automation testing
- **Nodemon** (^3.1.7) - Development auto-reload
- **Concurrently** (^9.1.0) - Run multiple commands concurrently
- **Supertest** (^7.0.0) - HTTP assertion library
- **ts-node** (^10.9.2) - TypeScript execution for Node.js

---

## Frontend Dependencies (React - Web)

### Core Framework

- **React** (^18.3.1) - UI library
- **React DOM** (^18.3.1) - React rendering
- **React Router DOM** (^6.28.0) - Client-side routing
- **Vite** (^6.4.1) - Build tool and development server

### Form Management & Queries

- **React Hook Form** (^7.53.2) - Efficient form handling
- **TanStack React Query** (^5.62.2) - Server state management

### UI & Styling

- **Tailwind CSS** (^3.4.15) - Utility-first CSS framework
- **Tailwind Merge** (^2.5.4) - Intelligent Tailwind class merging
- **PostCSS** (^8.5.3) - CSS transformations
- **Autoprefixer** (^10.4.20) - Vendor prefix automation
- **clsx** (^2.1.1) - Utility for constructing CSS classes

### Notifications & User Feedback

- **React Hot Toast** (^2.4.1) - Toast notifications

### Development Tools

- **TypeScript** (^5.7.2) - Static type checking
- **ESLint** (^9.16.0) - Linting
- **Prettier** (^3.4.2) - Code formatting
- **Vitest** (^3.2.4) - Unit testing framework

---

## WebUI Dependencies (React - Dashboard)

### Core Framework

- **React** (^18.3.1) - UI library
- **React DOM** (^18.3.1) - React rendering
- **React Router DOM** (^6.28.0) - Client-side routing
- **Vite** (^6.0.3) - Build tool
- **Socket.IO Client** (^4.7.4) - Real-time bidirectional communication

### State Management

- **Zustand** (^5.0.2) - Lightweight state management

### Visualization & Diagramming

- **@xyflow/react** (^12.0.4) - Flow diagram library
- **Recharts** (^2.10.0) - React charting library
- **html2canvas** (^1.4.1) - Screenshot and image conversion

### Icon Libraries (See detailed section below)

- **iconoir-react** (^7.11.0) - MIT licensed icon library
- **@carbon/icons-react** (^11.71.0) - IBM Carbon Design System icons
- **aws-react-icons** (^3.2.0) - AWS icon components
- **@fluentui/react-icons** (^2.0.316) - Microsoft Fluent UI icons

### Development Tools

- **TypeScript** (^5.7.2)
- **ESLint** (^8.56.0)
- **Prettier** (^3.2.5)
- **Vitest** (^4.0.15)
- **Testing Library** (^14.1.2)
- **@svgr/cli** (^8.1.0) - SVG to React component transformer

---

## Icon Libraries & Attributions

### 1. Iconoir Icons

**Source**: [Iconoir Icon Library](https://iconoir.com/)
**Package**: `iconoir-react` (^7.11.0)
**License**: MIT License
**Author**: Daniel Martin
**Repository**: https://github.com/iconoir-icons/iconoir
**Year**: 2021
**Count**: 1,673+ icons

Iconoir provides a beautiful, open-source icon library integrated via the `iconoir-react` package. Icons are auto-generated into categories via our build process and used throughout the UI for interface elements, navigation, and actions.

**Integration**: Auto-generated from npm package via `scripts/generate-iconoir-icons.js`

---

### 2. AWS Architecture Icons

**Source**: Official AWS Architecture Icons
**License**: AWS Terms (see [AWS Icons License](https://aws.amazon.com/architecture/icons/))
**Provider**: Amazon Web Services (AWS)
**Count**: 306+ icons
**Integration**: Auto-generated React components from official SVG files

Official AWS service icons are used for infrastructure diagramming and cloud architecture visualization. Icons are automatically converted to React components and organized by category.

**Integration**: Generated via `services/webui/scripts/process-cloud-icons.js`
**Source Pattern**: Arch_*.svg (48px light versions)
**Brand Color**: #FF9900 (AWS Orange)

---

### 3. Microsoft Azure Service Icons

**Source**: Official Microsoft Azure Icons
**License**: Microsoft Terms (see [Azure Icons License](https://learn.microsoft.com/en-us/azure/architecture/icons/))
**Provider**: Microsoft Corporation
**Count**: 626+ icons
**Integration**: Auto-generated React components from official SVG files

Official Azure service icons provide consistent visual representation of Azure services in infrastructure diagrams. Icons are automatically processed and categorized.

**Integration**: Generated via `services/webui/scripts/process-cloud-icons.js`
**Source Pattern**: Azure_Public_Service_Icons/Icons/icon-service-*.svg
**Brand Color**: #0078D4 (Azure Blue)

---

### 4. Google Cloud Platform (GCP) Icons

**Source**: Official Google Cloud Product Icons
**License**: Google Cloud Terms (see [GCP Icons License](https://cloud.google.com/icons))
**Provider**: Google Cloud
**Count**: 45+ icons
**Integration**: Auto-generated React components from official SVG files

Official Google Cloud service icons for representing GCP services in architecture diagrams. Organized by service category.

**Integration**: Generated via `services/webui/scripts/process-cloud-icons.js`
**Source Paths**:
- `gcp-category/Category Icons`
- `gcp-products/Unique Icons`
**File Pattern**: `*-512-color*.svg`
**Brand Color**: #DB4437 (Google Red)

---

### 5. IBM Carbon Icons

**Source**: [IBM Carbon Design System](https://carbondesignsystem.com/patterns/icon-usage)
**Package**: `@carbon/icons-react` (^11.71.0)
**License**: Apache License 2.0
**Author**: IBM Corp.
**Year**: 2015
**Repository**: https://github.com/carbon-design-system/carbon

IBM's Carbon Design System provides a comprehensive set of icons used for interface elements and system-level representations.

**Integration**: Curated icon selection from `@carbon/icons-react` package
**Brand Color**: #0F62FE (IBM Blue)

---

### 6. Fluent UI Icons

**Source**: [Microsoft Fluent UI](https://github.com/microsoft/fluentui)
**Package**: `@fluentui/react-icons` (^2.0.316)
**License**: MIT License
**Author**: Microsoft Corporation

Microsoft's Fluent Design System icon library providing consistent icon design language.

---

### 7. AWS React Icons Package

**Source**: [aws-react-icons npm package](https://www.npmjs.com/package/aws-react-icons)
**Package**: `aws-react-icons` (^3.2.0)
**License**: MIT License
**Author**: Mohammad Abu Mattar
**Year**: 2023
**Repository**: https://github.com/Muhammad-Usman-Rehan/aws-react-icons

React component wrapper for AWS icons, providing easy integration into React applications.

---

### 8. Internal Custom Icons

Custom icons created specifically for IceCharts to represent internal concepts, custom cloud resources, and specialized infrastructure components.

---

## Python Backend Dependencies

### Web Framework

- **Flask** (3.1.1) - Lightweight WSGI web framework

### Database & ORM

- **SQLAlchemy** (2.0.36) - SQL toolkit and ORM
- **PyDAL** (20251018.1) - Database abstraction layer
- **psycopg2-binary** (2.9.10) - PostgreSQL adapter
- **pymysql** (1.1.1) - MySQL adapter

### Authentication & Security

- **PyJWT** (2.10.1) - JSON Web Token implementation
- **bcrypt** (4.2.1) - Password hashing
- **cryptography** (44.0.1) - Cryptographic recipes
- **authlib** (1.6.5) - Authentication and OAuth library
- **pyotp** (2.9.0) - Two-factor authentication

### Monitoring & Logging

- **prometheus-client** (0.21.1) - Prometheus metrics
- **prometheus-flask-exporter** (0.23.1) - Flask Prometheus exporter
- **structlog** (25.4.0) - Structured logging
- **python-json-logger** (3.2.1) - JSON logging formatter

### Task Queue & Caching

- **redis** (5.2.1) - Redis client
- **celery** (5.4.0) - Distributed task queue

### Cloud Storage

- **boto3** (1.35.90) - AWS SDK for Python
- **google-cloud-storage** (2.19.0) - Google Cloud Storage client

### Image Processing

- **Pillow** (12.0.0) - Python Imaging Library

### WSGI & Server

- **Werkzeug** (3.1.4) - WSGI utilities

---

## Database Support & Drivers

### PyDAL Database Abstraction Layer

IceCharts uses **PyDAL** (20251018.1) as its database abstraction layer, which provides support for multiple database backends. While PostgreSQL is the primary/default database, the application is architected to support any PyDAL-compatible database through the `DB_TYPE` environment variable.

**Supported Databases via PyDAL**:

| Database | DB_TYPE Value | Driver Package | Status | Notes |
|----------|---------------|---|--------|-------|
| PostgreSQL | `postgres` or `postgresql` | psycopg2-binary | Default, fully tested | Recommended for production |
| MySQL/MariaDB | `mysql` | pymysql | Supported, tested | Includes Galera cluster support |
| SQLite | `sqlite` | Built-in | Testing & development | In-memory or file-based |
| Microsoft SQL Server | `mssql` | PyDAL native driver | Supported | Enterprise deployments |
| Oracle Database | `oracle` | PyDAL native driver | Supported | Enterprise deployments |
| IBM DB2 | `db2` | PyDAL native driver | Supported | Enterprise deployments |
| Firebird | `firebird` | PyDAL native driver | Supported | Legacy systems |
| IBM Informix | `informix` | PyDAL native driver | Supported | Legacy systems |
| Ingres | `ingres` | PyDAL native driver | Supported | Legacy systems |
| CUBRID | `cubrid` | PyDAL native driver | Supported | Legacy systems |
| SAP DB/MaxDB | `sapdb` | PyDAL native driver | Supported | Legacy systems |

**Current Production Configuration**:
- **Primary**: PostgreSQL (default via `DB_TYPE=postgres`)
- **Secondary**: MySQL/MariaDB support via pymysql
- **Testing**: SQLite (in-memory databases)

**Database Configuration via Environment**:
```
DB_TYPE=postgres              # Database backend selection
DB_HOST=localhost             # Database server hostname
DB_PORT=5432                  # Database server port
DB_NAME=icecharts             # Database name
DB_USER=icecharts_user        # Database user
DB_PASSWORD=changeme          # Database password
DB_POOL_SIZE=10               # Connection pooling size
```

---

## Operating System & Runtime Dependencies

### Flask Backend Container (Dockerfile-based)

**Build Stage Dependencies** (installed in builder, not in runtime):
- **gcc** - GNU C compiler (compiles psycopg2-binary, cryptography, bcrypt)
- **g++** - GNU C++ compiler
- **libpq-dev** - PostgreSQL development libraries (for psycopg2-binary compilation)
- **libssl-dev** - OpenSSL development libraries (for cryptography, bcrypt compilation)
- **pkg-config** - Package configuration utility (helps find system libraries during build)

**Runtime Stage Dependencies** (actually shipped in production container):
- **libpq5** - PostgreSQL client library (runtime support for PostgreSQL connections)
- **libssl3** - OpenSSL runtime library (required by cryptography and bcrypt at runtime)
- **libxml2** - XML processing library (SAML authentication via xmlsec1)
- **libxmlsec1** - XML security library (SAML signature validation)
- **curl** - HTTP client (healthcheck verification)

**Python Packages** (declared in requirements.txt):
- **psycopg2-binary** (2.9.10) - PostgreSQL adapter (uses libpq5 at runtime)
- **cryptography** (44.0.1) - Cryptographic operations (requires libssl3 at runtime)
- **bcrypt** (4.2.1) - Password hashing (requires libssl3 at runtime)
- **Pillow** (12.0.0) - Python Imaging Library (pure Python, no system libs required)

**MySQL/MariaDB Support**:
- **pymysql** (1.1.1) - Pure Python MySQL driver (no system libraries required)
- No additional system libraries needed for MySQL connectivity

**NOT Included** (optional, commented out in requirements.txt):
- ❌ WeasyPrint / cairosvg - Not included due to heavy system dependencies (gobject, pango, cairo)
- ❌ python3-saml / lxml - SAML support commented out; xmlsec can be installed when needed for enterprise deployments
- ❌ Build tools (gcc, g++) - Stripped from runtime (multi-stage build)

### WebUI Container (Dockerfile-based)

**Build Stage**:
- **Node.js** (20-slim base image)
- **npm** (included with Node.js)
- **Build dependencies**: Installed via npm ci/npm install from package.json

**Production Stage**:
- **nginx** (1.25 slim)
- **curl** (for healthcheck)
- Static assets built by Node.js and served by nginx

**Node Packages**:
- **Vite** (6.0.3+) - Build tool and dev server
- **React** (18.3.1) and related packages
- All packages from `/services/webui/package.json`

### Runtime Services & Infrastructure

**Database Server**:
- **PostgreSQL** (17+ recommended, 15+ minimum)
- Official Debian slim Docker images used in production
- Supports connection pooling via app-level configuration

**Cache & Session Store**:
- **Redis** (7+ recommended)
- Used for session management and caching
- Official Alpine Docker images used in production
- Optional TLS and authentication support

**Object Storage**:
- **MinIO** (latest stable)
- S3-compatible object storage for file uploads and media
- Used as primary storage backend
- Docker container deployment with volume persistence

**Monitoring & Observability**:
- **Prometheus** (optional, for metrics collection)
- Metrics exported via `prom-client` (Node.js) and `prometheus-client` (Python)
- Provides scrape endpoint at `/metrics`

**Dashboarding** (Optional):
- **Grafana** (optional, for visualization)
- Dashboard creation and metrics visualization
- Works with Prometheus backend

---

## Development & Build Tools

### Required for Local Development

- **Git** (2.30+) - Version control system
- **Docker** (20.10+) - Container runtime
- **Docker Compose** (1.29+) - Multi-container orchestration
- **Make** - Build automation
- **Python** (3.12+ minimum, 3.13 recommended) - Backend runtime
- **Node.js** (18+ minimum, 20+ recommended) - Frontend runtime

### Code Quality & Linting Tools

**Python**:
- **flake8** - Style guide enforcement
- **black** - Code formatter
- **isort** - Import statement formatter
- **mypy** - Static type checker
- **bandit** - Security issue scanner
- **pytest** - Unit testing framework
- **pytest-cov** - Code coverage measurement

**JavaScript/TypeScript**:
- **ESLint** - Linting utility
- **Prettier** - Code formatter
- **TypeScript** - Static type checking
- **Vitest** - Unit testing framework (frontend)
- **Testing Library** - React component testing utilities

**Docker**:
- **Trivy** - Container vulnerability scanner
- Used in CI/CD pipelines for security scanning

**General**:
- **CodeQL** - Static analysis security scanning (via GitHub Actions)
- **GitHub Actions** - CI/CD pipeline automation

---

## Third-Party Service Dependencies

### Authentication & Identity Management

- **SAML 2.0** - Enterprise SSO support (via xmlsec1, authlib)
- **OAuth 2.0** - OpenID Connect support (via authlib)
- **JWT (JSON Web Tokens)** - Session-less authentication
- **2FA/MFA** - Two-factor authentication (via pyotp)

### Cloud Provider SDKs (Optional)

- **AWS SDK for Python** (boto3 1.35.90) - AWS S3 integration
- **Google Cloud Storage** (2.19.0) - Google Cloud Storage integration
- Used for cloud storage backends alternative to MinIO

### Monitoring & Metrics

- **Prometheus** (v2.x+) - Time-series metrics database
  - Scrapes `/metrics` endpoint
  - Default storage: 15GB
  - Retention: 15 days
- **Grafana** (v9.x+) - Visualization and dashboarding
  - Creates dashboards from Prometheus data
  - Default storage: 2GB

---

## License Compliance Summary

### Third-Party Dependencies by License

| Category | License Type | Components |
|----------|-------------|-----------|
| **MIT** | Permissive | React, Express, Vite, Zustand, Recharts, Prettier, ESLint, TypeScript, Node.js |
| **Apache 2.0** | Permissive | IBM Carbon Icons, Recharts, PostgreSQL, PyDAL |
| **BSD** | Permissive | Flask, Werkzeug, Pillow, PyDAL |
| **AGPL-3.0** | Copyleft | IceCharts (primary license) |
| **PostgreSQL** | Permissive | PostgreSQL (same as Apache 2.0) |
| **Redis** | BSD-3-Clause | Redis |
| **MinIO** | AGPL-3.0 | MinIO |

### Database Licenses

- **PostgreSQL**: PostgreSQL License (similar to BSD-2-Clause)
- **MySQL/MariaDB**: GPL-2.0 (community edition) / Commercial (enterprise)
- **SQLite**: Public Domain
- **Oracle**: Commercial (separate license required)
- **IBM DB2**: Commercial (separate license required)
- **Microsoft SQL Server**: Commercial (separate license required)



### IceCharts License

IceCharts is licensed under AGPL-3.0 with the following provisions:

- **Open Source Use**: Free for internal and non-commercial individual use
- **Commercial Use**: Requires commercial license
- **SaaS Deployment**: Requires commercial license
- **Contributor Employee Exception**: Companies employing official contributors receive perpetual GPL-2.0 rights for versions where the employee contributed

For more details, see [LICENSE.md](../LICENSE.md).

### Third-Party License Summary

| Library | Version | License | Purpose |
|---------|---------|---------|---------|
| iconoir-react | 7.11.0 | MIT | Icon library |
| @carbon/icons-react | 11.71.0 | Apache 2.0 | IBM icon library |
| aws-react-icons | 3.2.0 | MIT | AWS icon components |
| @fluentui/react-icons | 2.0.316 | MIT | Microsoft icon library |
| React | 18.3.1 | MIT | UI library |
| Express.js | 4.19.2 | MIT | Web framework |
| Tailwind CSS | 3.4.15 | MIT | Styling framework |
| SQLAlchemy | 2.0.36 | MIT | Database ORM |
| Flask | 3.1.1 | BSD-3-Clause | Web framework |
| Vite | 6.0.3+ | MIT | Build tool |
| Zustand | 5.0.2 | MIT | State management |
| Recharts | 2.10.0 | Apache 2.0 | Charting library |
| @xyflow/react | 12.0.4 | MIT | Flow diagrams |

---

## How to Update Attributions

When adding new dependencies, services, or tools:

1. **NPM Dependencies**:
   - Add to the appropriate `package.json` file
   - Update Frontend or WebUI Dependencies section in this document
   - Include version number, purpose, and license

2. **Python Dependencies**:
   - Add to `requirements.txt`
   - Update Python Backend Dependencies section
   - Include version number, purpose, and license
   - If database driver: update Database Support & Drivers section

3. **System-Level Dependencies** (OS packages):
   - Document in Operating System & Runtime Dependencies section
   - Specify if build-time only or runtime requirement
   - Note which component depends on it

4. **Database Support**:
   - If adding new database backend: update Database Support & Drivers table
   - Document PyDAL DB_TYPE value and required driver
   - Note any special requirements (Galera, clustering, etc.)

5. **Icon Libraries**:
   - For cloud providers: Ensure SVG source files are properly tracked
   - For npm icon packages: Update `package.json` and regenerate icons
   - Update Icon Libraries & Attributions section with full attribution

6. **Infrastructure Services** (Redis, PostgreSQL, etc.):
   - Add to Runtime Services & Infrastructure section
   - Document version requirements
   - Note purpose and use case

7. **Development Tools**:
   - Add to Development & Build Tools section
   - Specify minimum version requirements
   - Note if required or optional

8. **Monitoring/Security Tools**:
   - Update Development & Build Tools or Third-Party Service Dependencies
   - Document purpose and integration points

---

## Acknowledgments

IceCharts stands on the shoulders of giants. We are grateful to all the open source maintainers, designers, and communities who have contributed the libraries, tools, and icon sets that make this project possible.

Special thanks to:

- **Iconoir** (Daniel Martin) for the comprehensive, beautiful icon library
- **AWS, Microsoft, and Google** for providing official icon sets
- **IBM Carbon Design System** for thoughtful design standards
- **The React, TypeScript, and Node.js communities** for powerful development tools
- **All open source contributors** whose work is used in this project

---

**Last Updated**: December 2025
**For Questions**: Please contact [info@penguintech.group](mailto:info@penguintech.group)
