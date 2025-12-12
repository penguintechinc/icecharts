# Release Notes

## [0.1.0] - 2025-12-10

### Initial Release

IceCharts v0.1.0 marks the initial public release of our collaborative diagramming platform.

#### Added

**Core Features**
- Intuitive canvas editor for creating diagrams with shapes, connectors, and text
- Rich shape library for system components, infrastructure, and flowchart elements
- Smart connectors with automatic routing and customizable styling
- Grid and snap-to-grid functionality for precise alignment

**Real-Time Collaboration**
- Multi-user editing with WebSocket-powered real-time synchronization
- Presence awareness showing active users and their editing locations
- Comments and annotations system with threaded discussions
- Resolution tracking for design reviews and feedback

**Export & Sharing**
- Multiple export formats: SVG, PNG, PDF, and JSON
- Customizable export options with scaling and resolution settings
- Public sharing links for easy distribution
- Version history with rollback capabilities

**Infrastructure Integration**
- Elder API integration for importing infrastructure entities
- Automatic entity mapping with color-coding by component type
- Dependency visualization showing relationships between elements
- Live synchronization with infrastructure definitions

**Enterprise Security**
- User authentication and authorization with role-based access control (RBAC)
- OAuth/SSO integration for enterprise identity management
- Team and group management with granular permissions
- Audit logging for compliance and accountability

**Performance & Monitoring**
- PostgreSQL database with optimized queries and indexing
- Redis caching for instant response times
- MinIO object storage for efficient file management
- Prometheus monitoring with optional Grafana dashboards

#### Technical Stack

- **Frontend**: React 18+, TypeScript, Tailwind CSS
- **Backend**: Flask, Python 3.12+, PyDAL ORM
- **Database**: PostgreSQL 17+
- **Cache**: Redis 7+
- **Storage**: MinIO (S3-compatible)
- **Monitoring**: Prometheus, Grafana
- **Deployment**: Docker, Docker Compose

#### Getting Started

See [Getting Started](GETTING_STARTED.md) for installation and setup instructions.

#### Known Limitations

- This is an initial release with core features. Additional advanced features are planned for future releases.

#### Support

For issues, feature requests, or questions, please visit our [GitHub Issues](https://github.com/PenguinCloud/IceCharts/issues) page or contact support@penguintech.group.

---

For detailed documentation, visit the [docs/](.) directory.
