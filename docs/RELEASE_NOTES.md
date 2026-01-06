# Release Notes

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
