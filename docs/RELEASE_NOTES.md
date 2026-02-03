# Release Notes

## [1.4.0] - January 2026

### Overview

IceCharts v1.4.0 introduces **IceRuns**, a production-ready serverless function execution platform. Execute custom functions in 7 programming languages via webhooks, API calls, scheduled cron jobs, or IceStreams playbooks. Complete container isolation with warm/cold start optimization, real-time execution tracking, and multi-language support.

### New Features

#### IceRuns Platform
- **Multi-language serverless execution**: Python 3.13, Node.js 20, Go 1.23, Ruby 3.3, Bash 5.2, PowerShell 7.4, Rust 1.75
- **Function management**: Upload, version, configure, and manage functions via WebUI or API
- **Multiple trigger types**:
  - Webhooks: Public token-based triggers with optional HMAC signing
  - API: Authenticated REST endpoints
  - Scheduled: Cron expressions with timezone support
  - IceStreams: Execute functions as playbook nodes
- **Container isolation**: Docker-based sandboxing with resource limits (memory, CPU, timeout)
- **Warm/cold start optimization**: Reuse containers for fast subsequent executions
- **Real-time execution tracking**: WebSocket support for live status updates
- **Execution history**: Full logs, metrics, and artifacts for each execution

#### OpenWhisk-Inspired Architecture
- **Controller pattern**: Flask backend REST API + function management
- **Invoker pattern**: Worker service pool for parallel execution
- **Redis Streams**: Async task queue with consumer groups for decoupled processing
- **Horizontal scaling**: Add invokers dynamically with auto-scaling support

#### Webhook Features
- Token-based authentication
- HMAC SHA256 signature validation
- Rate limiting (configurable per function)
- IP whitelisting (CIDR blocks)
- HTTP method restrictions (GET, POST, PUT, etc.)
- Webhook metadata injection (__webhook__ object)

#### Scheduling
- Standard Unix cron expressions
- Timezone support (300+ IANA timezones)
- Static input for scheduled runs
- Next run prediction
- Execution history tracking

#### IceStreams Integration
- IceRun Execute node: Execute functions with input mapping
- IceRun Wait node: Async execution polling
- Function selector dropdown
- Data flow integration
- Parallel execution support

#### Security
- JWT authentication with scope-based authorization
- Secrets encryption at rest (AES-256-GCM)
- Service account tokens (long-lived, scoped)
- Network isolation (no outbound by default)
- Read-only filesystem with writable /tmp
- Non-root container execution
- Security policy: no privilege escalation
- HMAC request signing for webhooks
- Audit logging of all operations

#### Deployment Options
- Docker Compose (development/small)
- Kubernetes with namespace isolation
- Horizontal Pod Autoscaler (HPA) support
- Multi-architecture builds (AMD64 + ARM64)
- Health check endpoints

#### Documentation
- 11 comprehensive guides (README, quickstart, architecture, API reference, etc.)
- 7 complete working examples (one per language)
- Security best practices guide
- Deployment guide (Docker + Kubernetes)
- Troubleshooting guide
- IceStreams integration guide

### API Endpoints (IceRuns)

**Function Management:**
- `GET /api/v1/iceruns` - List all functions
- `POST /api/v1/iceruns` - Create function
- `GET /api/v1/iceruns/{id}` - Get function details
- `PUT /api/v1/iceruns/{id}` - Update function
- `DELETE /api/v1/iceruns/{id}` - Delete function
- `POST /api/v1/iceruns/{id}/package` - Upload package
- `GET /api/v1/iceruns/{id}/package` - Download package

**Execution:**
- `POST /api/v1/iceruns/{id}/execute` - Execute function
- `GET /api/v1/iceruns/executions/{id}` - Get execution details
- `GET /api/v1/iceruns/executions/{id}/logs` - Get execution logs
- `GET /api/v1/iceruns/{id}/stats` - Get function statistics

**Webhooks:**
- `POST /api/v1/iceruns/hook/{token}` - Public webhook trigger
- `GET /api/v1/iceruns/{id}/webhook` - Get webhook config
- `PUT /api/v1/iceruns/{id}/webhook/config` - Update webhook settings
- `POST /api/v1/iceruns/{id}/webhook/regenerate` - Regenerate token

### Scopes (IceRuns)

- `iceruns:read` - View functions and executions
- `iceruns:write` - Create and update functions
- `iceruns:delete` - Delete functions
- `iceruns:execute` - Trigger function executions
- `iceruns:logs` - View execution logs
- `iceruns:admin` - Full administrative access

### Performance

- **Cold start**: 500ms - 2 seconds (language dependent)
- **Warm start**: 50-200 ms (container reuse)
- **Concurrency**: Unlimited with horizontal scaling
- **Throughput**: 10-50 functions/second per invoker
- **Memory overhead**: 50MB (Python) to 3MB (Rust/Go)

### Files Added

**Invoker Service:**
- `services/iceruns-invoker/` - Complete invoker implementation
- `services/iceruns-invoker/app/invoker.py` - Main worker loop
- `services/iceruns-invoker/app/runtimes/` - 7 runtime implementations
- `services/iceruns-invoker/Dockerfile` - Multi-arch containerization

**Flask Backend:**
- `services/flask-backend/app/api/v1/iceruns.py` - Function management API
- `services/flask-backend/app/api/v1/iceruns_executions.py` - Execution tracking
- `services/flask-backend/app/api/v1/iceruns_hooks.py` - Webhook endpoints
- `services/flask-backend/app/services/iceruns_storage_service.py` - S3/MinIO integration

**Documentation:**
- `docs/iceruns/README.md` - Overview and features
- `docs/iceruns/quickstart.md` - 5-minute getting started
- `docs/iceruns/architecture.md` - Deep dive into design
- `docs/iceruns/runtimes.md` - Language-specific guides
- `docs/iceruns/api-reference.md` - Complete REST API
- `docs/iceruns/webhook-guide.md` - Webhook usage
- `docs/iceruns/scheduling.md` - Cron scheduling
- `docs/iceruns/icestreams-integration.md` - Playbook integration
- `docs/iceruns/deployment.md` - Docker & K8s deployment
- `docs/iceruns/security.md` - Security best practices
- `docs/iceruns/troubleshooting.md` - Common issues
- `docs/iceruns/examples/` - 7 language examples

### Breaking Changes

None. IceRuns is a new feature and does not affect existing functionality.

### Migration Guide

No migration required. Existing IceCharts and IceStreams functionality unchanged.

### Upgrading

```bash
# Update to v1.4.0
docker-compose pull
docker-compose up -d

# Or with Kubernetes
kubectl apply -f k8s/iceruns/

# Run migrations if needed
docker exec flask-backend python -m flask db upgrade
```

### Known Issues

None at this time.

### Deprecations

None.

### Contributors

Built with Penguin Tech Inc's enterprise template and community feedback.

---

## [0.3.0] - January 2025

### Overview

IceCharts v0.3.0 introduces the Connector Framework, enabling seamless integration with external services for workflow automation. This release brings WaddleBot integration, a visual workflow editor with connector support, and a modular architecture for adding future integrations.

### New Features

#### Connector Framework
- **Modular plugin architecture** for external service integrations
- **YAML manifest-based connectors** - add new integrations without code changes
- **Dynamic node generation** from manifest definitions
- **Schema-driven configuration** panels for easy node setup
- **Variable interpolation** with `{{input.field}}` syntax
- See [CONNECTORS.md](CONNECTORS.md) for complete documentation

#### WaddleBot Integration
- **4 Triggers**: Chat Command, Stream Event, Chat Message, Incoming Webhook
- **15 Actions**: Send Chat, Reply, Whisper, Display Media, Update Ticker, Show Alert, Shoutout, AI Response, Spotify Play, YouTube Music, Inventory Add, Loyalty Give, Reputation Update, Timeout User, Ban User
- **2 Transforms**: User Lookup, Permission Check
- Full support for Twitch, Discord, Slack, and Kick platforms

#### Elder Integration
- **9 Triggers**: Entity Created/Updated/Deleted, Issue Created/Status Changed, Webhook Event, Discovery Completed, Vulnerability Detected, Dependency Changed
- **18 Actions**: Create/Update/Delete Entity, Create/Remove Dependency, Create/Update Issue, Add Comment, Link Entity to Issue, Create Project/Milestone, Trigger Discovery, Run SBOM Scan, Add Identity, Send Notification, Allocate/Release IP, Create Webhook
- **7 Transforms**: Entity Lookup, Search Entities, Get Dependencies, Graph Traversal, Impact Analysis, Issue Lookup, Check Vulnerabilities
- Infrastructure discovery and dependency mapping integration

#### Enhanced Playbook Editor
- **Connector nodes** appear in left palette under "Connectors" section
- **Collapsible subsections** for triggers, actions, and transforms
- **Connector-colored nodes** for visual distinction
- **Multi-handle support** for nodes with multiple outputs

#### Connector Settings
- New **Connectors** tab in Settings page
- View all installed connectors with node counts
- Expandable cards showing available triggers, actions, and transforms
- Configuration status indicators (placeholder for future auth setup)

### API Additions

New connector endpoints:
- `GET /api/v1/connectors` - List all connectors
- `GET /api/v1/connectors/{id}` - Get specific connector
- `GET /api/v1/connectors/{id}/nodes` - Get connector nodes
- `GET /api/v1/connectors/nodes` - Get all nodes with optional category filter

### Files Added

**Backend:**
- `services/icestreams-worker/connectors/` - Connector framework package
- `services/flask-backend/app/api/v1/connectors.py` - REST API endpoints

**Frontend:**
- `services/webui/src/client/types/connector.ts` - TypeScript types
- `services/webui/src/client/hooks/useConnectors.ts` - React hooks
- `services/webui/src/client/components/playbooks/ConnectorSection.tsx`
- `services/webui/src/client/components/playbooks/panels/ConnectorConfigPanel.tsx`

**Documentation:**
- `docs/CONNECTORS.md` - Complete connector framework documentation

### Migration Guide

No database migrations required for this release.

#### New Environment Variables (Optional)
```env
# WaddleBot
WADDLEBOT_URL=http://localhost:8060
WADDLEBOT_API_KEY=your-api-key

# Elder
ELDER_URL=http://localhost:5000
ELDER_API_KEY=your-api-key
```

---

## [0.2.0] - December 2024

### Overview

IceCharts v0.2.0 introduces significant enhancements to team collaboration, content organization, and platform administration. This release brings powerful features for managing diagram collections, individual diagram sharing, enhanced validation, real-time collaboration improvements, and comprehensive admin statistics.

### New Features

#### Enhanced Diagram Export
- Improved export functionality with multiple format support (SVG, PNG, PDF, JSON)
- Customizable export options including scaling and resolution settings
- Better handling of complex diagrams with layers and groups
- Enhanced rendering quality for production-ready exports

#### Collections Feature
- Organize diagrams into custom collections for better project management
- Create, update, and delete collections with granular access control
- Add and remove diagrams from collections with drag-and-drop reordering
- Share entire collections with users and groups
- View collection-level analytics and statistics
- Public collection sharing via tokens

#### Individual Diagram Sharing
- Share individual diagrams directly with users and groups
- Fine-grained permission control (viewer, editor, admin)
- Generate public share tokens for diagrams
- Track who has access to each diagram

#### Signup Controls & Email Verification
- Admin-configurable signup settings (allow/disable user registration)
- Email verification workflow for new accounts
- Customizable email templates for verification messages
- SMTP, SendGrid, AWS SES, Mailgun, and Gmail email provider support

#### Input Validation Enhancement
- Comprehensive Pydantic schema validation for all API endpoints
- Standardized error responses with clear validation messages
- Type-safe request/response handling throughout API

#### Real-Time Collaboration Enhancements
- Improved WebSocket connection handling for simultaneous editing
- Enhanced presence awareness with user status indicators
- Better conflict resolution for concurrent edits
- Optimized real-time synchronization for better performance

#### Admin Statistics Dashboard
- Comprehensive platform-wide statistics and metrics
- Real-time dashboard with key performance indicators
- Time-series data analysis for trends (1h, 24h, 7d, 30d, 90d)
- Top active users and most shared drawings reports

### Migration Guide

#### Database Migrations
```bash
python scripts/migrate.py
# Or with Flask CLI
flask db upgrade
```

New tables: `collections`, `collection_drawings`, `collection_shares`, `email_verifications`, `statistics_snapshots`

#### New Environment Variables
```env
EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@icecharts.local
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SIGNUP_ENABLED=true
EMAIL_VERIFICATION_REQUIRED=true
```

### Dependencies

**New:**
- `pydantic==2.10.5` - Request/response validation
- `celery==5.4.0` - Background task queue
- `sendgrid==6.10.0` - SendGrid email integration
- `recharts==2.10.0` - React charting library

**Requirements:** Python 3.12+, Node.js 20.0.0+

---

## [0.1.0] - December 10, 2024

### Initial Release

IceCharts v0.1.0 marks the initial public release of our collaborative diagramming platform.

### Core Features
- Intuitive canvas editor for creating diagrams with shapes, connectors, and text
- Rich shape library for system components, infrastructure, and flowchart elements
- Smart connectors with automatic routing and customizable styling
- Grid and snap-to-grid functionality for precise alignment

### Real-Time Collaboration
- Multi-user editing with WebSocket-powered real-time synchronization
- Presence awareness showing active users and their editing locations
- Comments and annotations system with threaded discussions
- Resolution tracking for design reviews and feedback

### Export & Sharing
- Multiple export formats: SVG, PNG, PDF, and JSON
- Customizable export options with scaling and resolution settings
- Public sharing links for easy distribution
- Version history with rollback capabilities

### Infrastructure Integration
- Elder API integration for importing infrastructure entities
- Automatic entity mapping with color-coding by component type
- Dependency visualization showing relationships between elements

### Enterprise Security
- User authentication and authorization with role-based access control (RBAC)
- OAuth/SSO integration for enterprise identity management
- Team and group management with granular permissions
- Audit logging for compliance and accountability

### Technical Stack
- **Frontend**: React 18+, TypeScript, Tailwind CSS
- **Backend**: Flask, Python 3.12+, PyDAL ORM
- **Database**: PostgreSQL 17+
- **Cache**: Redis 7+
- **Storage**: MinIO (S3-compatible)
- **Monitoring**: Prometheus, Grafana
- **Deployment**: Docker, Docker Compose

---

## Roadmap

**v0.3.0:**
- Advanced diagram templates
- Diagram versioning and rollback
- Enhanced collaboration presence (cursors, selections)

**v0.4.0:**
- Team workspaces
- Diagram approval workflows
- Custom diagram themes

## Support

- **Issues & Bugs:** [GitHub Issues](https://github.com/PenguinCloud/IceCharts/issues)
- **Feature Requests:** [GitHub Discussions](https://github.com/PenguinCloud/IceCharts/discussions)
- **Email Support:** support@penguintech.group
