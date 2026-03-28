# Project Template Makefile
# This Makefile provides common development tasks for multi-language projects

.PHONY: help setup dev test build clean lint format docker deploy

# Default target
.DEFAULT_GOAL := help

# Variables
PROJECT_NAME := project-template
VERSION := $(shell cat .version 2>/dev/null || echo "development")
DOCKER_REGISTRY := ghcr.io
DOCKER_ORG := penguintechinc
GO_VERSION := 1.23.5
PYTHON_VERSION := 3.12
NODE_VERSION := 18

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# Help target
help: ## Show this help message
	@echo "$(BLUE)$(PROJECT_NAME) Development Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Setup/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Development Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Development/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Testing Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Testing/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Build Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Build/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Docker Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && /Docker/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)Other Commands:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && !/Setup|Development|Testing|Build|Docker/ {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Setup Commands
setup: ## Setup - Install all dependencies and initialize the project
	@echo "$(BLUE)Setting up $(PROJECT_NAME)...$(RESET)"
	@$(MAKE) setup-env
	@$(MAKE) setup-go
	@$(MAKE) setup-python
	@$(MAKE) setup-node
	@$(MAKE) setup-git-hooks
	@echo "$(GREEN)Setup complete!$(RESET)"

setup-env: ## Setup - Create environment file from template
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from .env.example...$(RESET)"; \
		cp .env.example .env; \
		echo "$(YELLOW)Please edit .env with your configuration$(RESET)"; \
	fi

setup-go: ## Setup - Install Go dependencies and tools
	@echo "$(BLUE)Setting up Go dependencies...$(RESET)"
	@go version || (echo "$(RED)Go $(GO_VERSION) not installed$(RESET)" && exit 1)
	@go mod download
	@go mod tidy
	@go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	@go install github.com/air-verse/air@latest

setup-python: ## Setup - Install Python dependencies and tools
	@echo "$(BLUE)Setting up Python dependencies...$(RESET)"
	@python3 --version || (echo "$(RED)Python $(PYTHON_VERSION) not installed$(RESET)" && exit 1)
	@pip install --upgrade pip
	@pip install -r requirements.txt
	@pip install black isort flake8 mypy pytest pytest-cov

setup-node: ## Setup - Install Node.js dependencies and tools
	@echo "$(BLUE)Setting up Node.js dependencies...$(RESET)"
	@node --version || (echo "$(RED)Node.js $(NODE_VERSION) not installed$(RESET)" && exit 1)
	@npm install
	@cd web && npm install

setup-git-hooks: ## Setup - Install Git pre-commit hooks
	@echo "$(BLUE)Installing Git hooks...$(RESET)"
	@cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@cp scripts/git-hooks/commit-msg .git/hooks/commit-msg
	@chmod +x .git/hooks/commit-msg

# Development Commands
dev: ## Development - Start development environment
	@echo "$(BLUE)Starting development environment...$(RESET)"
	@docker-compose up -d postgres redis
	@sleep 5
	@$(MAKE) dev-services

dev-services: ## Development - Start all services for development
	@echo "$(BLUE)Starting development services...$(RESET)"
	@trap 'docker-compose down' INT; \
	concurrently --names "API,Web-Python,Web-Node" --prefix name --kill-others \
		"$(MAKE) dev-api" \
		"$(MAKE) dev-web-python" \
		"$(MAKE) dev-web-node"

dev-api: ## Development - Start Go API in development mode
	@echo "$(BLUE)Starting Go API...$(RESET)"
	@cd apps/api && air

dev-web-python: ## Development - Start Python web app in development mode
	@echo "$(BLUE)Starting Python web app...$(RESET)"
	@cd apps/web && python3 app.py

dev-web-node: ## Development - Start Node.js web app in development mode
	@echo "$(BLUE)Starting Node.js web app...$(RESET)"
	@cd web && npm run dev

dev-db: ## Development - Start only database services
	@docker-compose up -d postgres redis

dev-monitoring: ## Development - Start monitoring services
	@docker-compose up -d prometheus grafana

dev-full: ## Development - Start full development stack
	@docker-compose up -d

# Testing Commands
test: ## Testing - Run all tests
	@echo "$(BLUE)Running all tests...$(RESET)"
	@$(MAKE) test-go
	@$(MAKE) test-python
	@$(MAKE) test-node
	@echo "$(GREEN)All tests completed!$(RESET)"

test-go: ## Testing - Run Go tests
	@echo "$(BLUE)Running Go tests...$(RESET)"
	@go test -v -race -coverprofile=coverage-go.out ./...

test-python: ## Testing - Run Python tests
	@echo "$(BLUE)Running Python tests...$(RESET)"
	@pytest --cov=shared --cov=apps --cov-report=xml:coverage-python.xml --cov-report=html:htmlcov-python

test-flask: ## Testing - Run Flask backend tests
	@echo "$(BLUE)Running Flask backend tests...$(RESET)"
	@cd services/flask-backend && pytest tests/ --cov=app --cov-report=html --cov-report=term-summary -v

test-flask-cov: ## Testing - Run Flask tests with coverage report
	@echo "$(BLUE)Running Flask backend tests with coverage...$(RESET)"
	@cd services/flask-backend && pytest tests/ --cov=app --cov-report=html --cov-report=xml -v
	@echo "$(GREEN)Coverage report: services/flask-backend/htmlcov/index.html$(RESET)"

test-node: ## Testing - Run Node.js tests
	@echo "$(BLUE)Running Node.js tests...$(RESET)"
	@npm test
	@cd web && npm test

test-webui: ## Testing - Run WebUI tests
	@echo "$(BLUE)Running WebUI tests...$(RESET)"
	@cd services/webui && npm test -- --run

test-webui-watch: ## Testing - Run WebUI tests in watch mode
	@echo "$(BLUE)Running WebUI tests in watch mode...$(RESET)"
	@cd services/webui && npm test

test-webui-cov: ## Testing - Run WebUI tests with coverage
	@echo "$(BLUE)Running WebUI tests with coverage...$(RESET)"
	@cd services/webui && npm test -- --run --coverage

test-alpha: ## Testing - Run local alpha smoke tests (build, run, API, unit, pages)
	@./scripts/test-alpha.sh

test-beta: ## Testing - Run beta cluster smoke tests (pods, services, ingress, access)
	@./scripts/test-beta.sh

smoke-test: test-alpha ## Testing - Alias for test-alpha (local smoke tests)

test-integration: ## Testing - Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down

test-coverage: ## Testing - Generate coverage reports
	@$(MAKE) test
	@echo "$(GREEN)Coverage reports generated:$(RESET)"
	@echo "  Go: coverage-go.out"
	@echo "  Python: coverage-python.xml, htmlcov-python/"
	@echo "  Node.js: coverage/"

# New Testing Commands
.PHONY: test-unit test-icestreams-unit test-iceflows-unit test-iceruns-unit test-e2e test-e2e-headed test-security test-functional test-lint test-all test-controller install-playwright

test-unit: ## Testing - Run all unit tests
	@echo "$(BLUE)Running all unit tests...$(RESET)"
	@./scripts/test-controller.sh unit all

test-icestreams-unit: ## Testing - Run IceStreams worker unit tests
	@echo "$(BLUE)Running IceStreams unit tests...$(RESET)"
	@cd services/icestreams-worker && python3 -m pytest tests/ -v

test-iceflows-unit: ## Testing - Run IceFlows worker unit tests
	@echo "$(BLUE)Running IceFlows unit tests...$(RESET)"
	@cd services/iceflows-worker && python3 -m pytest tests/ -v

test-iceruns-unit: ## Testing - Run IceRuns invoker unit tests
	@echo "$(BLUE)Running IceRuns unit tests...$(RESET)"
	@cd services/iceruns-invoker && python3 -m pytest tests/ -v

test-e2e: ## Testing - Run Playwright E2E tests
	@echo "$(BLUE)Running E2E tests...$(RESET)"
	@cd tests/e2e && npx playwright test

test-e2e-headed: ## Testing - Run Playwright E2E tests in headed mode
	@echo "$(BLUE)Running E2E tests (headed)...$(RESET)"
	@cd tests/e2e && npx playwright test --headed

test-security: ## Testing - Run security scans (bandit, npm audit, trivy)
	@echo "$(BLUE)Running security scans...$(RESET)"
	@if command -v bandit >/dev/null 2>&1; then echo "-- bandit --"; bandit -r . -x ./tests,./venv,./.git,./node_modules,./web/node_modules --quiet || true; fi
	@if command -v pip-audit >/dev/null 2>&1; then echo "-- pip-audit --"; find . -name "requirements.txt" -not -path "*/.git/*" -not -path "*/venv/*" -not -path "*/node_modules/*" | xargs -I{} pip-audit -r {} 2>/dev/null || true; fi
	@if command -v gosec >/dev/null 2>&1; then echo "-- gosec --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && gosec ./... || true'; fi
	@if command -v govulncheck >/dev/null 2>&1; then echo "-- govulncheck --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && govulncheck ./... || true'; fi
	@find . -name "package.json" -not -path "*/.git/*" -not -path "*/node_modules/*" -maxdepth 3 | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && npm audit 2>/dev/null || true'
	@if command -v gitleaks >/dev/null 2>&1; then echo "-- gitleaks --"; gitleaks detect --source . --no-git 2>/dev/null || true; fi

test-functional: ## Testing - Run functional tests (page loads, API responses)
	@echo "$(BLUE)Running functional tests...$(RESET)"
	@./scripts/test-controller.sh functional

test-lint: ## Testing - Run all linters
	@echo "$(BLUE)Running all linters...$(RESET)"
	@./scripts/test-controller.sh lint all

test-all: ## Testing - Run complete test suite
	@echo "$(BLUE)Running complete test suite...$(RESET)"
	@./scripts/test-controller.sh unit all
	@./scripts/test-controller.sh lint all
	@./scripts/test-controller.sh api
	@echo "$(GREEN)Complete test suite finished!$(RESET)"

test-controller: ## Testing - Run test-controller with args (usage: make test-controller ARGS="unit flask")
	@./scripts/test-controller.sh $(ARGS)

install-playwright: ## Testing - Install Playwright browsers
	@echo "$(BLUE)Installing Playwright browsers...$(RESET)"
	@cd tests/e2e && npx playwright install --with-deps

# Build Commands
build: ## Build - Build all applications
	@echo "$(BLUE)Building all applications...$(RESET)"
	@$(MAKE) build-go
	@$(MAKE) build-python
	@$(MAKE) build-node
	@echo "$(GREEN)All builds completed!$(RESET)"

build-go: ## Build - Build Go applications
	@echo "$(BLUE)Building Go applications...$(RESET)"
	@mkdir -p bin
	@go build -ldflags "-X main.version=$(VERSION)" -o bin/api ./apps/api

build-python: ## Build - Build Python applications
	@echo "$(BLUE)Building Python applications...$(RESET)"
	@python3 -m py_compile apps/web/app.py

build-node: ## Build - Build Node.js applications
	@echo "$(BLUE)Building Node.js applications...$(RESET)"
	@npm run build
	@cd web && npm run build

build-production: ## Build - Build for production with optimizations
	@echo "$(BLUE)Building for production...$(RESET)"
	@CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags "-w -s -X main.version=$(VERSION)" -o bin/api ./apps/api
	@cd web && npm run build

# Docker Commands
docker-build: ## Docker - Build all Docker images
	@echo "$(BLUE)Building Docker images...$(RESET)"
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-api:$(VERSION) -f apps/api/Dockerfile .
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-web:$(VERSION) -f web/Dockerfile web/
	@docker build -t $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-python:$(VERSION) -f apps/web/Dockerfile .

docker-push: ## Docker - Push Docker images to registry
	@echo "$(BLUE)Pushing Docker images...$(RESET)"
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-api:$(VERSION)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-web:$(VERSION)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_ORG)/$(PROJECT_NAME)-python:$(VERSION)

docker-run: ## Docker - Run application with Docker Compose
	@docker-compose up --build

docker-clean: ## Docker - Clean up Docker resources
	@echo "$(BLUE)Cleaning up Docker resources...$(RESET)"
	@docker-compose down -v
	@docker system prune -f

# Code Quality Commands
lint: ## Code Quality - Run linting for all languages
	@echo "$(BLUE)Running linting...$(RESET)"
	@$(MAKE) lint-go
	@$(MAKE) lint-python
	@$(MAKE) lint-node

lint-go: ## Code Quality - Run Go linting
	@echo "$(BLUE)Linting Go code...$(RESET)"
	@golangci-lint run

lint-python: ## Code Quality - Run Python linting
	@echo "$(BLUE)Linting Python code...$(RESET)"
	@flake8 .
	@mypy . --ignore-missing-imports

lint-flask: ## Code Quality - Lint Flask backend
	@echo "$(BLUE)Linting Flask backend...$(RESET)"
	@cd services/flask-backend && flake8 app tests --count --select=E9,F63,F7,F82 --show-source --statistics
	@cd services/flask-backend && black --check app tests
	@cd services/flask-backend && isort --check-only app tests
	@cd services/flask-backend && mypy app --ignore-missing-imports

lint-flask-fix: ## Code Quality - Auto-fix Flask linting issues
	@echo "$(BLUE)Auto-fixing Flask backend linting issues...$(RESET)"
	@cd services/flask-backend && black app tests
	@cd services/flask-backend && isort app tests

lint: ## Code Quality - Run linting for all languages
	@echo "$(BLUE)Running linting...$(RESET)"
	@if command -v flake8 >/dev/null 2>&1; then echo "-- flake8 --"; python3 -m flake8 . --max-line-length=120 --exclude=.git,__pycache__,venv,node_modules,.env* || true; fi
	@if command -v black >/dev/null 2>&1; then echo "-- black --"; black --check . --exclude '/(\.git|venv|__pycache__|node_modules)/' || true; fi
	@if command -v isort >/dev/null 2>&1; then echo "-- isort --"; isort --check-only . || true; fi
	@if command -v mypy >/dev/null 2>&1; then echo "-- mypy --"; python3 -m mypy . --ignore-missing-imports || true; fi
	@if command -v golangci-lint >/dev/null 2>&1; then echo "-- golangci-lint --"; find . -name "go.mod" -not -path "*/.git/*" -not -path "*/vendor/*" | xargs -I{} dirname {} | xargs -I{} sh -c 'cd {} && golangci-lint run || true'; fi
	@if command -v hadolint >/dev/null 2>&1; then echo "-- hadolint --"; find . -name "Dockerfile*" -not -path "*/.git/*" | xargs hadolint || true; fi
	@if command -v shellcheck >/dev/null 2>&1; then echo "-- shellcheck --"; find . -name "*.sh" -not -path "*/.git/*" -not -path "*/node_modules/*" | xargs shellcheck || true; fi
	@npm run lint || true
	@cd web && npm run lint || true

lint-node: ## Code Quality - Run Node.js linting
	@echo "$(BLUE)Linting Node.js code...$(RESET)"
	@npm run lint
	@cd web && npm run lint

lint-webui: ## Code Quality - Lint WebUI
	@echo "$(BLUE)Linting WebUI...$(RESET)"
	@cd services/webui && npm run lint
	@cd services/webui && npm run typecheck

lint-webui-fix: ## Code Quality - Auto-fix WebUI linting issues
	@echo "$(BLUE)Auto-fixing WebUI linting issues...$(RESET)"
	@cd services/webui && npm run lint:fix

format: ## Code Quality - Format code for all languages
	@echo "$(BLUE)Formatting code...$(RESET)"
	@$(MAKE) format-go
	@$(MAKE) format-python
	@$(MAKE) format-node

format-go: ## Code Quality - Format Go code
	@echo "$(BLUE)Formatting Go code...$(RESET)"
	@go fmt ./...
	@goimports -w .

format-python: ## Code Quality - Format Python code
	@echo "$(BLUE)Formatting Python code...$(RESET)"
	@black .
	@isort .

format-node: ## Code Quality - Format Node.js code
	@echo "$(BLUE)Formatting Node.js code...$(RESET)"
	@npm run format
	@cd web && npm run format

# Database Commands
db-migrate: ## Database - Run database migrations
	@echo "$(BLUE)Running database migrations...$(RESET)"
	@go run scripts/migrate.go

db-seed: ## Database - Seed database with test data
	@echo "$(BLUE)Seeding database...$(RESET)"
	@go run scripts/seed.go

db-reset: ## Database - Reset database (WARNING: destroys data)
	@echo "$(RED)WARNING: This will destroy all data!$(RESET)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker-compose down -v
	@docker-compose up -d postgres redis
	@sleep 5
	@$(MAKE) db-migrate
	@$(MAKE) db-seed

db-backup: ## Database - Create database backup
	@echo "$(BLUE)Creating database backup...$(RESET)"
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U postgres project_template > backups/backup-$(shell date +%Y%m%d-%H%M%S).sql

db-restore: ## Database - Restore database from backup (requires BACKUP_FILE)
	@echo "$(BLUE)Restoring database from $(BACKUP_FILE)...$(RESET)"
	@docker-compose exec -T postgres psql -U postgres project_template < $(BACKUP_FILE)

# License Commands
license-validate: ## License - Validate license configuration
	@echo "$(BLUE)Validating license configuration...$(RESET)"
	@go run scripts/license-validate.go

license-test: ## License - Test license server integration
	@echo "$(BLUE)Testing license server integration...$(RESET)"
	@curl -f $${LICENSE_SERVER_URL:-https://license.penguintech.io}/api/v2/validate \
		-H "Authorization: Bearer $${LICENSE_KEY}" \
		-H "Content-Type: application/json" \
		-d '{"product": "'$${PRODUCT_NAME:-project-template}'"}'

# Version Management Commands
version-update: ## Version - Update version (patch by default)
	@./scripts/version/update-version.sh

version-update-minor: ## Version - Update minor version
	@./scripts/version/update-version.sh minor

version-update-major: ## Version - Update major version
	@./scripts/version/update-version.sh major

version-show: ## Version - Show current version
	@echo "Current version: $(VERSION)"

# Deployment Commands
deploy-staging: ## Deploy - Deploy to staging environment
	@echo "$(BLUE)Deploying to staging...$(RESET)"
	@$(MAKE) docker-build
	@$(MAKE) docker-push
	# Add staging deployment commands here

deploy-beta: ## Deploy - Deploy to beta K8s cluster via Helm
	@./scripts/deploy-beta.sh

deploy-production: ## Deploy - Deploy to production environment
	@echo "$(BLUE)Deploying to production...$(RESET)"
	@$(MAKE) docker-build
	@$(MAKE) docker-push
	# Add production deployment commands here

# Alpha Deployment Commands (Local Kubernetes - local-alpha)
KUBE_CONTEXT ?= local-alpha

deploy-alpha: ## Deploy - Deploy to alpha environment (local-alpha context)
	@echo "$(BLUE)Deploying to alpha ($(KUBE_CONTEXT))...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/deploy-alpha.sh

deploy-alpha-build: ## Deploy - Build and deploy to alpha environment
	@echo "$(BLUE)Building and deploying to alpha ($(KUBE_CONTEXT))...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/deploy-alpha.sh --build

deploy-alpha-test: ## Deploy - Deploy to alpha and run smoke tests
	@echo "$(BLUE)Deploying to alpha with smoke tests...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/deploy-alpha.sh --test

deploy-alpha-full: ## Deploy - Build, deploy and test alpha environment
	@echo "$(BLUE)Full alpha deployment (build + deploy + test)...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/deploy-alpha.sh --build --test

deploy-alpha-local: ## Deploy - Build and deploy alpha locally (no push)
	@echo "$(BLUE)Local alpha deployment (build only, no push)...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/deploy-alpha.sh --build --no-push

test-alpha: ## Testing - Run alpha smoke tests
	@echo "$(BLUE)Running alpha smoke tests...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/test-alpha-smoke.sh

test-alpha-verbose: ## Testing - Run alpha smoke tests (verbose)
	@echo "$(BLUE)Running alpha smoke tests (verbose)...$(RESET)"
	@KUBE_CONTEXT=$(KUBE_CONTEXT) ./scripts/test-alpha-smoke.sh --verbose

alpha-status: ## Alpha - Show alpha deployment status
	@echo "$(BLUE)Alpha deployment status...$(RESET)"
	@kubectl --context $(KUBE_CONTEXT) get pods -n icecharts-alpha
	@echo ""
	@kubectl --context $(KUBE_CONTEXT) get svc -n icecharts-alpha

alpha-logs: ## Alpha - Show alpha deployment logs
	@kubectl --context $(KUBE_CONTEXT) logs -n icecharts-alpha -l app=api --tail=100 -f

alpha-logs-web: ## Alpha - Show alpha web logs
	@kubectl --context $(KUBE_CONTEXT) logs -n icecharts-alpha -l app=web --tail=100 -f

# Health Check Commands
health: ## Health - Check service health
	@echo "$(BLUE)Checking service health...$(RESET)"
	@curl -f http://localhost:8080/health || echo "$(RED)API health check failed$(RESET)"
	@curl -f http://localhost:8000/health || echo "$(RED)Python web health check failed$(RESET)"
	@curl -f http://localhost:3000/health || echo "$(RED)Node web health check failed$(RESET)"

logs: ## Logs - Show service logs
	@docker-compose logs -f

logs-api: ## Logs - Show API logs
	@docker-compose logs -f api

logs-web: ## Logs - Show web logs
	@docker-compose logs -f web-python web-node

logs-db: ## Logs - Show database logs
	@docker-compose logs -f postgres redis

# Cleanup Commands
clean: ## Clean - Clean build artifacts and caches
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	@rm -rf bin/
	@rm -rf dist/
	@rm -rf node_modules/
	@rm -rf web/node_modules/
	@rm -rf web/dist/
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf htmlcov-python/
	@rm -rf coverage-*.out
	@rm -rf coverage-*.xml
	@go clean -cache -modcache

clean-docker: ## Clean - Clean Docker resources
	@$(MAKE) docker-clean

clean-all: ## Clean - Clean everything (build artifacts, Docker, etc.)
	@$(MAKE) clean
	@$(MAKE) clean-docker

# Security Commands
security-scan: ## Security - Run security scans
	@echo "$(BLUE)Running security scans...$(RESET)"
	@go list -json -m all | nancy sleuth
	@safety check --json

audit: ## Security - Run security audit
	@echo "$(BLUE)Running security audit...$(RESET)"
	@npm audit
	@cd web && npm audit
	@$(MAKE) security-scan

# Monitoring Commands
metrics: ## Monitoring - Show application metrics
	@echo "$(BLUE)Application metrics:$(RESET)"
	@curl -s http://localhost:8080/metrics | grep -E '^# (HELP|TYPE)' | head -20

monitor: ## Monitoring - Open monitoring dashboard
	@echo "$(BLUE)Opening monitoring dashboard...$(RESET)"
	@open http://localhost:3001  # Grafana

# Documentation Commands
docs-serve: ## Documentation - Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(RESET)"
	@cd docs && python -m http.server 8080

docs-build: ## Documentation - Build documentation
	@echo "$(BLUE)Building documentation...$(RESET)"
	@echo "Documentation build not implemented yet"

# Git Commands
git-hooks-install: ## Git - Install Git hooks
	@$(MAKE) setup-git-hooks

git-hooks-test: ## Git - Test Git hooks
	@echo "$(BLUE)Testing Git hooks...$(RESET)"
	@.git/hooks/pre-commit
	@echo "$(GREEN)Git hooks test completed$(RESET)"

# Info Commands
info: ## Info - Show project information
	@echo "$(BLUE)Project Information:$(RESET)"
	@echo "Name: $(PROJECT_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Go Version: $(GO_VERSION)"
	@echo "Python Version: $(PYTHON_VERSION)"
	@echo "Node Version: $(NODE_VERSION)"
	@echo ""
	@echo "$(BLUE)Service URLs:$(RESET)"
	@echo "API: http://localhost:8080"
	@echo "Python Web: http://localhost:8000"
	@echo "Node Web: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001"

env: ## Info - Show environment variables
	@echo "$(BLUE)Environment Variables:$(RESET)"
	@env | grep -E "^(LICENSE_|POSTGRES_|REDIS_|NODE_|GIN_|PY4WEB_)" | sort

# Deployment Targets
deploy-dev: ## Deploy - Deploy to development environment (alias for deploy-staging)
	@$(MAKE) deploy-staging

deploy-prod: ## Deploy - Deploy to production environment
	@$(MAKE) deploy-production

# Mock Data
seed-mock-data: ## Development - Populate with 3-4 test items per feature
	@echo "$(BLUE)Seeding mock data...$(RESET)"
	@echo "$(YELLOW)No mock data seeding defined$(RESET)"

# Pre-Commit
pre-commit: ## Code Quality - Run pre-commit checks (lint + security + test)
	@echo "$(BLUE)=== Pre-commit checks ===$(RESET)"
	@$(MAKE) lint
	@$(MAKE) test-security
	@$(MAKE) test
	@echo "$(GREEN)=== Pre-commit complete ===$(RESET)"