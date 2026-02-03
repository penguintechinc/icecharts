# 📝 Documentation Guide - Write Docs People Actually Read

Part of [Development Standards](../STANDARDS.md)

## Why Documentation Matters (Even Though It's Boring)

Good docs = happy developers = fewer "why doesn't this work?!" Slack messages = everyone's sanity stays intact. Think of docs as your future self's love letter—be nice to them.

## 📁 Where Things Go

```
docs/
├── README.md            ← Everyone reads this first
├── DEVELOPMENT.md       ← How to set up locally
├── TESTING.md          ← Mock data & smoke tests
├── DEPLOYMENT.md       ← Production setup
├── RELEASE_NOTES.md    ← What's new (dated entries)
├── APP_STANDARDS.md    ← Your app-specific rules
├── standards/          ← Deep dives on patterns
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   └── ...
└── screenshots/        ← Real feature screenshots
```

## README.md - Your App's First Impression

**Your README is not optional bling.** It's the first thing people (including future-you) see.

**REQUIRED Elements:**
- Build status badges (GitHub Actions, Codecov, License)
- Catchy ASCII art
- Link to www.penguintech.io
- Quick Start (under 2 minutes to "hello world")
- Default dev credentials clearly marked as dev-only
- Key features (3-5 bullet points)
- Links to detailed docs (DEVELOPMENT.md, TESTING.md, etc.)

**Example Quick Start:**
```markdown
## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose | Git

### Get Running (60 seconds)
```bash
make dev
# Opens http://localhost:3000
```

**Default Dev Credentials:**
- Email: `admin@localhost.local` | Password: `admin123`
⚠️ Development only—change immediately in production!

### Next Steps
- Read [DEVELOPMENT.md](docs/DEVELOPMENT.md) for local setup
- Check [TESTING.md](docs/TESTING.md) for testing patterns
```

## ✍️ Writing Docs People Actually Read

**Keep It Short:** Your reader has 30 seconds. Respect that.
- Headings tell the story
- One idea per paragraph
- Use lists instead of paragraphs
- Short sentences

**Show, Don't Tell:**
- Code examples beat explanations
- Screenshot + caption > thousand words
- Real feature screenshots (with mock data) showcase what works

**Be Conversational:**
- Write like you're explaining to a colleague
- Use "we" and "you"—not the robot voice
- Humor is fine. Sarcasm too.

**Structure for Scanning:**
- Emojis in headings ✅
- Bold key terms
- Bullet points everywhere
- Table of contents for long docs

## 💬 Code Comments - Comments That Help

**Good comments answer "WHY"—not "WHAT"**
```python
# ❌ Bad: Explains what the code does
age = (today - birth_date).days // 365

# ✅ Good: Explains why this matters
# Using integer division to avoid fractional ages in age-gated features
age = (today - birth_date).days // 365
```

**Document the gotchas:**
```python
# NOTE: PyDAL doesn't support HAVING without GROUP BY in SQLite
# Use Python filtering for complex aggregations
```

## 📋 Release Notes Template

Create `docs/RELEASE_NOTES.md` and add new releases to the top:

```markdown
# Release Notes

## [v1.2.0] - 2025-01-22

### ✨ New Features
- Feature description

### 🐛 Bug Fixes
- Bug fix description

### 📚 Documentation
- Doc improvement description

## [v1.1.0] - 2025-01-15
...
```

## 🚨 Mistakes to Avoid

| ❌ Wrong | ✅ Right |
|---------|---------|
| "Call the API" (no endpoint) | "POST /api/v1/users with email, password" |
| Outdated screenshots | Fresh screenshots with mock data |
| Assumes prior knowledge | Links to background material |
| Steps with no context | Explains why each step matters |
| One giant wall of text | Short sections with headings |
| Typos and bad grammar | Proofread (spell-check helps!) |

## 📚 CLAUDE.md Management

- **Max 35,000 characters**
- **Stays high-level:** Point to detailed docs, don't repeat them
- **Focus:** Context, workflow rules, architecture decisions
- **Everything else:** Lives in docs/ with proper structure

---

**Golden Rule:** If you wouldn't want to read it, your team won't either. Make docs so clear they're almost impossible to misunderstand.
# Documentation Standards

Part of [Development Standards](../STANDARDS.md)

## README.md Standards

**ALWAYS include build status badges:**
- CI/CD pipeline status (GitHub Actions)
- Test coverage status (Codecov)
- Go Report Card (for Go projects)
- Version badge
- License badge (Limited AGPL3)

**ALWAYS include catchy ASCII art** below badges

**Company homepage**: Point to **www.penguintech.io**

**Quick Start Section - DEFAULT CREDENTIALS DOCUMENTATION:**

The README.md MUST include a Quick Start section documenting default credentials for development:

```markdown
## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Development Environment

Start all services:
```bash
make dev
```

Access the application at `http://localhost:3000`

**Default Development Credentials:**
- **Email**: `admin@localhost.local`
- **Password**: `admin123`

⚠️ **IMPORTANT**: Change these credentials in production. The default admin user is automatically created on first startup.

### Login
1. Navigate to `http://localhost:3000`
2. Enter default email: `admin@localhost.local`
3. Enter default password: `admin123`
4. Click Login

### Change Default Password
After first login, immediately change the admin password in Settings → Security.

### Production Deployment
See [Deployment Guide](docs/DEPLOYMENT.md) for production setup without default credentials.
```

**Key Points:**
- Default credentials MUST be documented in README Quick Start
- Default credentials MUST NOT be displayed on the login page itself
- Clearly mark credentials as for development only
- Warn about changing passwords in production
- Link to production deployment guide

## CLAUDE.md File Management

- **Maximum**: 35,000 characters
- **High-level approach**: Reference detailed docs
- **Documentation strategy**: Create detailed docs in `docs/` folder
- **Keep focused**: Critical context and workflow instructions only

## API Documentation

- Comprehensive endpoint documentation
- Request/response examples
- Error codes and handling
- Authentication requirements
- Rate limiting information

## Architecture Documentation

- System architecture diagrams
- Component interaction patterns
- Data flow documentation
- Decision records (ADRs)
