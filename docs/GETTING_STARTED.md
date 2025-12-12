# Getting Started with IceCharts

Welcome to IceCharts! This guide will help you set up, configure, and start using IceCharts for creating collaborative diagrams and visualizations.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Initial Configuration](#initial-configuration)
- [First Steps](#first-steps)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10+
- **Docker Compose**: Version 1.29+
- **Disk Space**: 10GB free space
- **RAM**: 4GB minimum (8GB recommended)

### For Local Development
- **Node.js**: 18.x or higher
- **Python**: 3.12 or higher
- **Make**: GNU Make (for build automation)
- **Git**: 2.30+

## Installation

### Option 1: Docker Compose (Recommended)

The quickest way to get IceCharts running with all services:

```bash
# 1. Clone the repository
git clone https://github.com/PenguinCloud/IceCharts.git
cd IceCharts

# 2. Copy environment configuration
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# 5. Wait for services to be healthy (check logs if needed)
docker-compose logs -f api
```

**Access IceCharts**:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:5001/api/v1
- **MinIO Console**: http://localhost:9001
- **Prometheus**: http://localhost:9090 (if monitoring enabled)

### Option 2: Local Development Setup

For development with hot-reload:

```bash
# 1. Install dependencies
make setup

# 2. Create environment file
cp .env.example .env

# 3. Start development servers
make dev

# Services will be available at:
# - Web UI: http://localhost:3000 (React dev server)
# - API: http://localhost:5000 (Flask dev server)
# - Database: localhost:5432
# - Redis: localhost:6379
```

### Option 3: Manual Installation

If you prefer to manage services separately:

```bash
# Start database services
docker-compose up -d postgres redis minio

# Start Flask backend
cd services/flask-backend
pip install -r requirements.txt
python run.py

# In another terminal, start React frontend
cd services/webui
npm install
npm start
```

## Initial Configuration

### Environment Variables

The `.env.example` file contains all configurable settings. Key variables:

```bash
# Flask/API Configuration
FLASK_ENV=production              # development or production
SECRET_KEY=changeme-in-production # Change in production
JWT_SECRET_KEY=changeme-jwt       # Change in production

# Database Configuration
POSTGRES_DB=icecharts
POSTGRES_USER=icecharts_user
POSTGRES_PASSWORD=changeme        # Change in production
DB_TYPE=postgres                  # Support: postgres, mysql, sqlite, etc.

# Redis Configuration
REDIS_PASSWORD=changeme           # Change in production

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Application URLs
REACT_APP_API_URL=http://localhost:5001
REACT_APP_API_BASE_PATH=/api/v1

# License Configuration
LICENSE_KEY=                       # Optional: Add valid license key
LICENSE_SERVER_URL=https://license.penguintech.io
PRODUCT_NAME=icecharts
RELEASE_MODE=false                # Set to true for production
```

### Post-Installation Setup

After starting IceCharts, complete these steps:

1. **Access the Admin Panel**
   - Navigate to http://localhost:3000
   - Login with default credentials:
     - Email: `admin@icecharts.local`
     - Password: `admin123`
   - **Change these credentials immediately in production**

2. **Configure Users**
   - Go to **Admin** → **Users** → **Manage Users**
   - Add your team members
   - Set appropriate roles (Admin, Maintainer, Viewer)

3. **Set Up Teams/Groups** (Optional)
   - Go to **Admin** → **Teams**
   - Create teams for different departments or projects

4. **Configure OAuth/SSO** (Optional)
   - See [OAuth Setup Guide](./OAUTH_SETUP.md) for detailed instructions

5. **Enable License** (Optional)
   - If you have a commercial license, add `LICENSE_KEY` to `.env`
   - Restart services: `docker-compose restart api`

## First Steps

### Creating Your First Diagram

1. **Log In**
   - Open http://localhost:3000
   - Enter your credentials

2. **Create New Diagram**
   - Click **New Diagram** button
   - Enter a title (e.g., "System Architecture")
   - Choose a template or start blank

3. **Add Shapes**
   - Use the shape palette on the left
   - Drag shapes onto the canvas
   - Double-click to edit text

4. **Connect Elements**
   - Select a shape
   - Drag from connection point to another shape
   - Customize connector style in properties panel

5. **Add Comments**
   - Click on a shape
   - Open Comments panel (right sidebar)
   - Click "Add Comment" to provide feedback

6. **Save & Share**
   - Diagram auto-saves
   - Click Share button to generate public link
   - Invite team members to collaborate

### Real-Time Collaboration

When multiple users open the same diagram:

- **See Live Cursors**: Watch where others are editing
- **View Presence**: See active collaborators in top-right
- **Sync Changes**: Changes appear instantly
- **Comment Notifications**: Get alerts on new comments

### Exporting Your Work

1. **Export Diagram**
   - Click **Export** menu
   - Choose format:
     - **PNG**: Raster image, good for sharing
     - **SVG**: Vector format, editable
     - **PDF**: Print-ready format
     - **JSON**: Full diagram data for backup

2. **Configure Export Options**
   - Set canvas size
   - Choose resolution/quality
   - Include metadata if needed

## Common Tasks

### Inviting Team Members

1. Go to **Settings** → **Users**
2. Click **Invite User**
3. Enter email address
4. Select role (Admin/Maintainer/Viewer)
5. User receives invitation email

### Setting Permissions

1. Open a diagram
2. Click **Share** button
3. Toggle sharing:
   - **Private**: Only you and invited users
   - **Public**: Anyone with link can view
4. Set edit permissions for collaborators

### Backing Up Your Data

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U icecharts_user -d icecharts > backup.sql

# Backup MinIO files
docker-compose exec minio mc mirror local/icecharts ./minio-backup

# Full backup (docker volumes)
docker-compose down
tar -czf icecharts-backup.tar.gz -v /var/lib/docker/volumes/
```

### Updating IceCharts

```bash
# Pull latest code
git pull origin main

# Update dependencies and rebuild
make update

# Restart services
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Services Won't Start

**Check logs**:
```bash
docker-compose logs api
docker-compose logs web
docker-compose logs postgres
```

**Common issues**:
- Port already in use: Change ports in `.env` or `docker-compose.yml`
- Database error: Wait for PostgreSQL to initialize (first startup takes 30s)
- Permission error: Ensure Docker daemon is running

### Can't Connect to API

```bash
# Test API connectivity
curl http://localhost:5001/api/v1/health

# Check if services are running
docker-compose ps

# Restart API service
docker-compose restart api
```

### Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose exec postgres psql -U icecharts_user -d icecharts -c "SELECT version();"

# Reset database (WARNING: Deletes all data)
docker-compose down
docker volume rm icecharts_postgres_data
docker-compose up -d postgres
```

### Authentication Issues

- **Forgot password**: Use admin reset:
  ```bash
  docker-compose exec api python -c "from app.models import reset_password; reset_password('admin@icecharts.local')"
  ```
- **Can't log in**: Check credentials in admin panel
- **Token expired**: Log out and log back in

### Performance Issues

- **Slow diagram loading**: Check browser console for errors
- **Collaboration lag**: Ensure network connectivity
- **High CPU usage**: Check Docker resource limits

### Getting More Help

- **Documentation**: See [docs/](../) folder
- **Issues**: Report at https://github.com/PenguinCloud/IceCharts/issues
- **Support**: Email support@penguintech.group

## Next Steps

- [Architecture Overview](ARCHITECTURE.md) - Understand system design
- [Features Guide](FEATURES.md) - Explore all capabilities
- [API Reference](API_REFERENCE.md) - For developers
- [Deployment Guide](DEPLOYMENT.md) - For production setup
- [Contributing](CONTRIBUTING.md) - Help improve IceCharts
