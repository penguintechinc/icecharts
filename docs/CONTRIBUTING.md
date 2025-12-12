# Contributing to IceCharts

Thank you for your interest in contributing to IceCharts! This guide explains the process for contributing code, documentation, and improvements.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Documentation](#documentation)
- [License](#license)

---

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our community standards and be respectful of all contributors.

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.12+
- Docker and Docker Compose
- Git
- Visual Studio Code (recommended) with extensions:
  - Python
  - ESLint
  - Prettier
  - GitLens

### Setup Development Environment

1. **Fork the Repository**
   ```bash
   # Click "Fork" on GitHub to create your own copy
   ```

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/IceCharts.git
   cd IceCharts
   git remote add upstream https://github.com/PenguinCloud/IceCharts.git
   ```

3. **Install Dependencies**
   ```bash
   make setup
   ```

4. **Start Development Servers**
   ```bash
   make dev
   ```

5. **Verify Setup**
   ```bash
   # Test API
   curl http://localhost:5001/api/v1/health

   # Open browser to http://localhost:3000
   ```

---

## Development Workflow

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Example branch names:
# feature/add-export-pdf
# fix/websocket-connection
# docs/update-readme
# refactor/extract-comment-service
```

### During Development

**Keep Your Branch Updated**:
```bash
# Regularly sync with upstream
git fetch upstream
git rebase upstream/main
```

**Commit Regularly**:
```bash
# Make small, logical commits
git add file1.py file2.tsx
git commit -m "Add shape export to PDF"
```

**Run Tests Locally**:
```bash
# Before committing
make test
make lint
```

### Pushing Changes

```bash
# Push to your fork
git push origin feature/your-feature-name

# If rebased, use force push carefully
git push origin feature/your-feature-name --force-with-lease
```

---

## Code Standards

### Python Backend

**File Structure**:
```
services/flask-backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── services/        # Business logic
│   ├── models.py        # Data models
│   └── config.py        # Configuration
└── tests/               # Test files
```

**Style Guide**:
- **Framework**: PEP 8 (with 100-char line limit)
- **Type Hints**: Required on all functions
- **Imports**: Organized (stdlib, third-party, local)
- **Docstrings**: Google-style, required on public functions
- **Naming**: snake_case for variables/functions, PascalCase for classes

**Example Function**:
```python
def create_drawing(owner_id: int, name: str, description: str = "") -> Dict[str, Any]:
    """Create a new drawing for the specified owner.

    Args:
        owner_id: ID of the drawing owner
        name: Name of the drawing
        description: Optional description

    Returns:
        Dictionary containing the created drawing data

    Raises:
        ValueError: If name is empty
        DatabaseError: If database operation fails
    """
    if not name:
        raise ValueError("Drawing name cannot be empty")

    drawing = db.drawings.insert(
        owner_id=owner_id,
        name=name,
        description=description
    )
    return drawing
```

**Linting**:
```bash
# Format code
black services/flask-backend/

# Check style
flake8 services/flask-backend/

# Type check
mypy services/flask-backend/

# Security scan
bandit services/flask-backend/app/

# All checks
make lint
```

### React Frontend

**File Structure**:
```
services/webui/src/
├── pages/               # Page components
├── components/          # Reusable components
├── hooks/              # Custom hooks
├── lib/                # Utilities
├── store/              # State management
└── types/              # TypeScript interfaces
```

**Style Guide**:
- **Framework**: ESLint + Prettier (configured in .eslintrc.json)
- **Type Safety**: Strict TypeScript with no `any`
- **Naming**: camelCase for files/functions, PascalCase for components
- **Imports**: Absolute imports (@ prefix)
- **Components**: Functional components with hooks

**Linting**:
```bash
# Format code
cd services/webui
npm run format

# Check style
npm run lint

# Type check
npm run type-check
```

### General Guidelines

- **No Console Logs**: Use logging framework instead
- **No Magic Numbers**: Define constants with meaningful names
- **DRY Principle**: Don't repeat yourself - extract to functions/components
- **Error Handling**: Proper error handling with try/catch or error boundaries
- **Comments**: Only for WHY, not WHAT (code should be self-documenting)

---

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest services/flask-backend/tests/test_drawings.py

# Frontend tests
cd services/webui
npm test

# Run with coverage
make test-coverage
```

### Test Coverage

- **Minimum**: 70% code coverage
- **Target**: 85%+ code coverage
- **Critical Paths**: 100% coverage required

---

## Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or changes
- `chore`: Build, dependency, or tooling changes

**Examples**:
```
feat(comments): add threaded replies support

Implement threaded comment system allowing users to reply to specific comments.

Closes #123
```

```
fix(export): handle special characters in PDF export

Fix issue where special characters were not rendered correctly in PDF exports.

Closes #456
```

---

## Pull Requests

### Before Submitting

1. **Update from Main**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run All Checks**:
   ```bash
   make lint
   make test
   ```

3. **Update Documentation**:
   - Add/update docstrings
   - Update relevant docs in `docs/`
   - Update CHANGELOG.md if applicable

### Creating Pull Request

**PR Description Template**:
```markdown
## Description
Brief description of changes

## Related Issues
Closes #123

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Added unit tests
- [ ] Added integration tests
- [ ] Tested manually

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Tests pass locally
- [ ] No new warnings generated
```

### Review Process

1. **Automated Checks**:
   - CI/CD pipeline validates tests
   - Linting checks pass
   - Code coverage doesn't decrease

2. **Code Review**:
   - At least 1 maintainer review required
   - Address feedback constructively
   - Request re-review after changes

3. **Approval & Merge**:
   - Maintainer approves changes
   - Branch rebased onto main (if needed)
   - PR merged by maintainer

---

## Documentation

### Adding Documentation

1. **For Features**: Add section to [FEATURES.md](FEATURES.md)
2. **For API**: Update [API_REFERENCE.md](API_REFERENCE.md)
3. **For Architecture**: Update [ARCHITECTURE.md](ARCHITECTURE.md)
4. **For Deployment**: Update [DEPLOYMENT.md](DEPLOYMENT.md)

### Documentation Style

- Clear and concise
- Examples for complex topics
- Links to related documentation
- Code snippets properly formatted

---

## License

By contributing to IceCharts, you agree that your contributions will be licensed under the Limited AGPL3 license - see [LICENSE.md](../LICENSE.md) for details.

---

## Questions?

- **Documentation**: Check [docs/](./) folder
- **Issues**: Open GitHub issue
- **Email**: support@penguintech.group

## Thank You!

We appreciate your contribution to IceCharts!
