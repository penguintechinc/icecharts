# IceCharts - Claude Code Context

## Temporary Files Policy

**IMPORTANT:** Any temporary reports, checklists, implementation summaries, or other transient documents created by Claude or its task agents during development sessions should be stored in `/tmp`, NOT in the repository.

Examples of temporary files that belong in `/tmp`:
- Implementation checklists (e.g., `IMPLEMENTATION_CHECKLIST.md`)
- Files modified lists (e.g., `FILES_MODIFIED.md`)
- Quick start guides generated during implementation
- Session-specific summaries or manifests
- Progress tracking documents
- Completion status reports

These files are useful during active development sessions but provide no long-term value to users, admins, or developers.

**Permanent documentation** (feature guides, API references, architecture docs) should go in the `docs/` folder.

## Project Overview

IceCharts is a diagramming and infrastructure visualization application with:
- React frontend (services/webui)
- Flask backend with PyDAL (services/flask-backend)
- PostgreSQL database
- Redis caching
- MinIO object storage

## Key Directories

- `services/webui/` - React frontend application
- `services/flask-backend/` - Flask API backend
- `docs/` - Project documentation
- `k8s/` - Kubernetes deployment manifests (Helm and Kustomize)
- `tests/` - Test suites

## Development Commands

```bash
docker-compose up -d          # Start all services
docker-compose logs -f api    # View API logs
npm run build                 # Build frontend
npm run typecheck             # TypeScript type checking
```

## For Detailed Context

See `docs/CLAUDE.md` for comprehensive project template context including:
- Technology stack details
- Development standards
- License server integration
- Database patterns
- Security requirements
