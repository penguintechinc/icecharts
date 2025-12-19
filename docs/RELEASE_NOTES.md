# Release Notes

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
