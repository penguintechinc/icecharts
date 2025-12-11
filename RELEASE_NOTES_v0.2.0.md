# IceCharts v0.2.0 Release Notes

**Release Date:** December 2024

## Overview

IceCharts v0.2.0 introduces significant enhancements to team collaboration, content organization, and platform administration. This release brings powerful features for managing diagram collections, individual diagram sharing, enhanced validation, real-time collaboration improvements, and comprehensive admin statistics. The update focuses on improving the user experience for teams and providing administrators with better visibility into platform usage.

## New Features

### 1. Enhanced Diagram Export
- Improved export functionality with multiple format support (SVG, PNG, PDF, JSON)
- Customizable export options including scaling and resolution settings
- Better handling of complex diagrams with layers and groups
- Enhanced rendering quality for production-ready exports

### 2. Collections Feature
- Organize diagrams into custom collections for better project management
- Create, update, and delete collections with granular access control
- Add and remove diagrams from collections with drag-and-drop reordering
- Share entire collections with users and groups
- View collection-level analytics and statistics
- Public collection sharing via tokens for easy collaboration

**New API Endpoints:**
- `POST /api/v1/collections` - Create a new collection
- `GET /api/v1/collections` - List user's collections
- `GET /api/v1/collections/<id>` - Get collection details
- `PUT /api/v1/collections/<id>` - Update collection
- `DELETE /api/v1/collections/<id>` - Delete collection
- `POST /api/v1/collections/<id>/drawings` - Add drawing to collection
- `GET /api/v1/collections/<id>/drawings` - Get collection drawings
- `DELETE /api/v1/collections/<id>/drawings/<drawing_id>` - Remove drawing
- `PUT /api/v1/collections/<id>/drawings/reorder` - Reorder drawings
- `POST /api/v1/collections/<id>/share` - Share collection
- `GET /api/v1/collections/<id>/shares` - List collection shares
- `DELETE /api/v1/collections/<id>/shares/<share_id>` - Revoke share
- `POST /api/v1/collections/<id>/share/token` - Generate public share token
- `GET /api/v1/collections/shared/<token>` - Access shared collection (public)
- `GET /api/v1/collections/<id>/analytics` - Get collection statistics

### 3. Individual Diagram Sharing
- Share individual diagrams directly with users and groups
- Fine-grained permission control (viewer, editor, admin)
- Generate public share tokens for diagrams
- Track who has access to each diagram
- Revoke shares instantly to maintain security

**Updated API Endpoints:**
- `GET /api/v1/drawings/<id>/shares` - List diagram shares
- `POST /api/v1/drawings/<id>/shares` - Create new share
- `DELETE /api/v1/drawings/<id>/shares/<share_id>` - Revoke share

### 4. Signup Controls & Email Verification
- Admin-configurable signup settings (allow/disable user registration)
- Email verification workflow for new accounts
- Customizable email templates for verification messages
- One-click verification links with expiration
- Prevent unverified accounts from accessing system features
- SMTP, SendGrid, AWS SES, Mailgun, and Gmail email provider support

### 5. Input Validation Enhancement
- Comprehensive Pydantic schema validation for all API endpoints
- Standardized error responses with clear validation messages
- Request body validation decorator pattern
- Database constraint validation with user-friendly error messages
- Type-safe request/response handling throughout API

### 6. Real-Time Collaboration Enhancements
- Improved WebSocket connection handling for simultaneous editing
- Enhanced presence awareness with user status indicators
- Better conflict resolution for concurrent edits
- Optimized real-time synchronization for better performance
- Reduced network bandwidth for collaboration messages

### 7. Admin Statistics Dashboard
- Comprehensive platform-wide statistics and metrics
- Real-time dashboard with key performance indicators
- Time-series data analysis for trends (1h, 24h, 7d, 30d, 90d)
- Top active users and most shared drawings reports
- API latency monitoring
- Customizable time ranges and intervals

**New API Endpoints:**
- `GET /api/v1/admin/statistics/dashboard` - Get dashboard statistics
- `GET /api/v1/admin/statistics/time-series/<metric>` - Get time series data
- `GET /api/v1/admin/statistics/latency` - Get API latency metrics
- `GET /api/v1/admin/statistics/top-users` - Get most active users
- `GET /api/v1/admin/statistics/top-drawings` - Get most shared drawings

## Breaking Changes

None. This release is fully backward compatible with v0.1.0.

## Migration Guide

### Upgrading from v0.1.0

#### 1. Database Migrations

Run the migration scripts to add new tables for collections and enhanced sharing:

```bash
# From the project root directory
python scripts/migrate.py

# Or with Flask CLI
flask db upgrade
```

New tables created:
- `collections` - Store user-created diagram collections
- `collection_drawings` - Map drawings to collections
- `collection_shares` - Manage collection-level sharing
- `email_verifications` - Track email verification tokens
- `statistics_snapshots` - Store historical statistics data

#### 2. New Environment Variables Required

Add these to your `.env` file:

```env
# Email Configuration
EMAIL_PROVIDER=smtp                    # Options: smtp, sendgrid, ses, mailgun, gmail
EMAIL_FROM=noreply@icecharts.local
EMAIL_FROM_NAME=IceCharts

# SMTP Settings (if using SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Or use other providers
SENDGRID_API_KEY=your-sendgrid-key
AWS_SES_REGION=us-east-1
MAILGUN_API_KEY=your-mailgun-key
MAILGUN_DOMAIN=mg.yourdomain.com
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Admin Settings
SIGNUP_ENABLED=true                    # Allow new user registration
EMAIL_VERIFICATION_REQUIRED=true       # Require email verification
EMAIL_VERIFICATION_EXPIRY=86400        # Token expiry in seconds (default 24 hours)

# Redis and Celery (for background jobs)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### 3. Configuration Changes

**Authentication Settings:**
- Email verification is now configurable per admin settings
- Signup flow includes verification step before account activation

**API Changes:**
- All request bodies now validated against Pydantic schemas
- Response format for errors standardized
- New collection and sharing endpoints available

**Database Considerations:**
- Existing data is fully preserved
- New collection functionality is opt-in
- Sharing permissions are backward compatible

#### 4. Optional: Enable Background Jobs

To use email verification and scheduled statistics collection:

```bash
# Start Celery worker in separate terminal
celery -A app.celery worker --loglevel=info

# Start Celery beat for scheduled tasks
celery -A app.celery beat --loglevel=info
```

## Dependencies

### New Dependencies Added

**Backend (Flask):**
- `pydantic==2.10.5` - Request/response validation
- `celery==5.4.0` - Background task queue
- `sendgrid==6.10.0` - SendGrid email integration
- `mailgun2==2.0.1` - Mailgun email integration
- `email-validator==2.2.0` - Email validation

**Frontend (React):**
- `recharts==2.10.0` - React charting library for admin dashboard

### Updated Dependencies

- `Flask[async]==3.1.0` - Async support for better performance
- `redis==5.2.1` - Enhanced Redis client
- `prometheus-client==0.21.1` - Improved monitoring

### Python Version Requirements

- **Minimum:** Python 3.12+
- **Recommended:** Python 3.13+ (optimized for new performance features)

### Node.js Version Requirements

- **Minimum:** Node.js 20.0.0+
- **Recommended:** Node.js 22.0.0+

## API Changes

### New Endpoints

**Collections Management:**
```
POST   /api/v1/collections
GET    /api/v1/collections
GET    /api/v1/collections/<collection_id>
PUT    /api/v1/collections/<collection_id>
DELETE /api/v1/collections/<collection_id>
```

**Collection Items:**
```
POST   /api/v1/collections/<collection_id>/drawings
GET    /api/v1/collections/<collection_id>/drawings
DELETE /api/v1/collections/<collection_id>/drawings/<drawing_id>
PUT    /api/v1/collections/<collection_id>/drawings/reorder
```

**Collection Sharing:**
```
POST   /api/v1/collections/<collection_id>/share
GET    /api/v1/collections/<collection_id>/shares
DELETE /api/v1/collections/<collection_id>/shares/<share_id>
POST   /api/v1/collections/<collection_id>/share/token
GET    /api/v1/collections/shared/<token>
GET    /api/v1/collections/shared/<token>/drawings
GET    /api/v1/collections/<collection_id>/analytics
```

**Admin Statistics:**
```
GET /api/v1/admin/statistics/dashboard
GET /api/v1/admin/statistics/time-series/<metric>
GET /api/v1/admin/statistics/latency
GET /api/v1/admin/statistics/top-users
GET /api/v1/admin/statistics/top-drawings
```

**Authentication (Enhanced):**
```
POST /api/v1/auth/verify-email
POST /api/v1/auth/resend-verification
```

### Modified Endpoints

All existing endpoints maintain backward compatibility. Enhanced error handling and validation:
```
All /api/v1/* endpoints now return standardized validation error responses
```

## Known Issues

None at this time.

## Roadmap

Planned features for upcoming releases:

- **v0.3.0:**
  - Advanced diagram templates
  - Diagram versioning and rollback
  - Enhanced collaboration presence (cursors, selections)

- **v0.4.0:**
  - Team workspaces
  - Diagram approval workflows
  - Custom diagram themes

## Support & Feedback

- **Issues & Bugs:** [GitHub Issues](https://github.com/PenguinCloud/IceCharts/issues)
- **Feature Requests:** [GitHub Discussions](https://github.com/PenguinCloud/IceCharts/discussions)
- **Email Support:** support@penguintech.group
- **Documentation:** [docs/](../../docs/)

## Contributors

This release includes contributions from the IceCharts community. Special thanks to all contributors and users who provided feedback.

---

**Upgrade Instructions:** See [GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed installation and upgrade instructions.
