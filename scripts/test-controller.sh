#!/usr/bin/env bash
# IceCharts Unified Test Controller
# Usage: ./scripts/test-controller.sh <type> [container]
#
# Types:     build | unit | api | integration | e2e | security | lint | functional | smoke
# Containers: flask | webui | icestreams | iceflows | iceruns | all
#
# Examples:
#   ./scripts/test-controller.sh unit flask
#   ./scripts/test-controller.sh unit all
#   ./scripts/test-controller.sh lint webui
#   ./scripts/test-controller.sh smoke
#   ./scripts/test-controller.sh security

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Constants and paths
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

VALID_TYPES="build unit api integration e2e security lint functional smoke"
VALID_CONTAINERS="flask webui icestreams iceflows iceruns all"

# ─────────────────────────────────────────────────────────────────────────────
# Color helpers
# ─────────────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_header() {
    echo ""
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
    echo ""
}

log_step() {
    echo -e "${CYAN}==> $1${NC}"
}

log_pass() {
    echo -e "${GREEN}  ✓ PASS${NC} $1"
}

log_fail() {
    echo -e "${RED}  ✗ FAIL${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}  ⚠ WARN${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}  - SKIP${NC} $1"
}

# ─────────────────────────────────────────────────────────────────────────────
# Usage / help
# ─────────────────────────────────────────────────────────────────────────────
usage() {
    echo ""
    echo -e "${BOLD}IceCharts Test Controller${NC}"
    echo ""
    echo -e "${BOLD}Usage:${NC}"
    echo "  ./scripts/test-controller.sh <type> [container]"
    echo ""
    echo -e "${BOLD}Test Types:${NC}"
    echo -e "  ${YELLOW}build${NC}         Build tests (docker build verification)"
    echo -e "  ${YELLOW}unit${NC}          Unit tests — requires [container]"
    echo -e "  ${YELLOW}api${NC}           API endpoint smoke tests (curl-based)"
    echo -e "  ${YELLOW}integration${NC}   Integration tests via docker-compose.test.yml"
    echo -e "  ${YELLOW}e2e${NC}           End-to-end tests via Playwright"
    echo -e "  ${YELLOW}security${NC}      Security scans (bandit, npm audit, trivy)"
    echo -e "  ${YELLOW}lint${NC}          Linting — requires [container]"
    echo -e "  ${YELLOW}functional${NC}    Functional/page-load tests (curl-based)"
    echo -e "  ${YELLOW}smoke${NC}         Smoke tests — quick pre-commit verification"
    echo ""
    echo -e "${BOLD}Containers (for unit/lint):${NC}"
    echo -e "  ${YELLOW}flask${NC}         services/flask-backend (Python)"
    echo -e "  ${YELLOW}webui${NC}         services/webui (Node.js/React)"
    echo -e "  ${YELLOW}icestreams${NC}    services/icestreams-worker (Python)"
    echo -e "  ${YELLOW}iceflows${NC}      services/iceflows-worker (Python)"
    echo -e "  ${YELLOW}iceruns${NC}       services/iceruns-invoker (Python)"
    echo -e "  ${YELLOW}all${NC}           Run for all containers"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  ./scripts/test-controller.sh unit flask"
    echo "  ./scripts/test-controller.sh unit all"
    echo "  ./scripts/test-controller.sh lint webui"
    echo "  ./scripts/test-controller.sh lint all"
    echo "  ./scripts/test-controller.sh api"
    echo "  ./scripts/test-controller.sh e2e"
    echo "  ./scripts/test-controller.sh e2e headed"
    echo "  ./scripts/test-controller.sh security"
    echo "  ./scripts/test-controller.sh smoke"
    echo "  ./scripts/test-controller.sh build all"
    echo ""
    echo -e "${BOLD}Environment Variables:${NC}"
    echo "  API_URL       API base URL (default: http://localhost:5001)"
    echo "  WEB_URL       Web UI base URL (default: http://localhost:3000)"
    echo "  ADMIN_EMAIL   Admin email for API tests (default: admin@localhost.local)"
    echo "  ADMIN_PASS    Admin password for API tests (default: admin123)"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Argument validation
# ─────────────────────────────────────────────────────────────────────────────
if [[ $# -eq 0 ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    usage
    exit 0
fi

TEST_TYPE="$1"
CONTAINER="${2:-all}"

# Validate test type
valid_type=false
for t in $VALID_TYPES; do
    if [[ "$TEST_TYPE" == "$t" ]]; then
        valid_type=true
        break
    fi
done

if [[ "$valid_type" == false ]]; then
    echo -e "${RED}Error:${NC} Invalid test type '${TEST_TYPE}'"
    echo "Valid types: $VALID_TYPES"
    echo ""
    usage
    exit 1
fi

# Validate container (only when type requires it)
if [[ "$TEST_TYPE" == "unit" ]] || [[ "$TEST_TYPE" == "lint" ]]; then
    valid_container=false
    for c in $VALID_CONTAINERS; do
        if [[ "$CONTAINER" == "$c" ]]; then
            valid_container=true
            break
        fi
    done

    if [[ "$valid_container" == false ]]; then
        echo -e "${RED}Error:${NC} Invalid container '${CONTAINER}' for type '${TEST_TYPE}'"
        echo "Valid containers: $VALID_CONTAINERS"
        echo ""
        usage
        exit 1
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Result tracking
# ─────────────────────────────────────────────────────────────────────────────
OVERALL_EXIT=0
RESULTS=()   # each entry: "PASS|FAIL|SKIP <label>"

record_result() {
    local status="$1"
    local label="$2"
    RESULTS+=("$status $label")
    if [[ "$status" == "FAIL" ]]; then
        OVERALL_EXIT=1
    fi
}

run_cmd() {
    local label="$1"
    shift
    log_step "$label"
    if "$@"; then
        log_pass "$label"
        record_result "PASS" "$label"
    else
        log_fail "$label"
        record_result "FAIL" "$label"
    fi
    echo ""
}

run_cmd_nofail() {
    # Like run_cmd but records WARN instead of FAIL (non-blocking)
    local label="$1"
    shift
    log_step "$label"
    if "$@"; then
        log_pass "$label"
        record_result "PASS" "$label"
    else
        log_warn "$label (non-blocking)"
        record_result "WARN" "$label"
    fi
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Python unit test helper
# ─────────────────────────────────────────────────────────────────────────────
run_python_unit() {
    local service_name="$1"   # e.g. "flask"
    local service_dir="$2"    # e.g. services/flask-backend

    local full_dir="$PROJECT_ROOT/$service_dir"

    if [[ ! -d "$full_dir" ]]; then
        log_skip "Unit tests: $service_name (directory not found: $service_dir)"
        record_result "SKIP" "Unit: $service_name"
        return
    fi

    local tests_dir="$full_dir/tests"
    if [[ ! -d "$tests_dir" ]]; then
        log_skip "Unit tests: $service_name (no tests/ directory)"
        record_result "SKIP" "Unit: $service_name"
        return
    fi

    log_step "Unit tests: $service_name"
    if (cd "$full_dir" && python -m pytest tests/ -v); then
        log_pass "Unit: $service_name"
        record_result "PASS" "Unit: $service_name"
    else
        log_fail "Unit: $service_name"
        record_result "FAIL" "Unit: $service_name"
    fi
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────────────────
run_build() {
    log_header "Build Tests"

    local build_script="$SCRIPT_DIR/test-build.sh"
    if [[ -f "$build_script" ]]; then
        run_cmd "Frontend build (WebUI)" bash "$build_script"
    else
        log_warn "Build script not found: scripts/test-build.sh"
        record_result "SKIP" "Build: WebUI"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# UNIT
# ─────────────────────────────────────────────────────────────────────────────
run_unit_flask() {
    run_python_unit "flask" "services/flask-backend"
}

run_unit_webui() {
    local webui_dir="$PROJECT_ROOT/services/webui"
    if [[ ! -d "$webui_dir" ]]; then
        log_skip "Unit tests: webui (directory not found)"
        record_result "SKIP" "Unit: webui"
        return
    fi
    log_step "Unit tests: webui (Vitest)"
    if (cd "$webui_dir" && npx vitest --run); then
        log_pass "Unit: webui"
        record_result "PASS" "Unit: webui"
    else
        log_fail "Unit: webui"
        record_result "FAIL" "Unit: webui"
    fi
    echo ""
}

run_unit_icestreams() {
    run_python_unit "icestreams" "services/icestreams-worker"
}

run_unit_iceflows() {
    run_python_unit "iceflows" "services/iceflows-worker"
}

run_unit_iceruns() {
    run_python_unit "iceruns" "services/iceruns-invoker"
}

run_unit() {
    log_header "Unit Tests${CONTAINER:+ — $CONTAINER}"

    case "$CONTAINER" in
        flask)      run_unit_flask ;;
        webui)      run_unit_webui ;;
        icestreams) run_unit_icestreams ;;
        iceflows)   run_unit_iceflows ;;
        iceruns)    run_unit_iceruns ;;
        all)
            run_unit_flask
            run_unit_webui
            run_unit_icestreams
            run_unit_iceflows
            run_unit_iceruns
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────────────────────
run_api() {
    log_header "API Tests"

    local api_script="$SCRIPT_DIR/test-api.sh"
    if [[ -f "$api_script" ]]; then
        run_cmd "API endpoint tests" bash "$api_script"
    else
        echo -e "${RED}Error:${NC} API test script not found: scripts/test-api.sh"
        record_result "FAIL" "API tests"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────
run_integration() {
    log_header "Integration Tests"

    local compose_file="$PROJECT_ROOT/docker-compose.test.yml"
    if [[ ! -f "$compose_file" ]]; then
        echo -e "${YELLOW}Warn:${NC} docker-compose.test.yml not found — skipping integration tests"
        record_result "SKIP" "Integration tests"
        return
    fi

    log_step "Integration tests via docker-compose.test.yml"
    if docker-compose -f "$compose_file" up --build --abort-on-container-exit; then
        log_pass "Integration tests"
        record_result "PASS" "Integration tests"
    else
        log_fail "Integration tests"
        record_result "FAIL" "Integration tests"
    fi
    # Always tear down
    docker-compose -f "$compose_file" down 2>/dev/null || true
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# E2E
# ─────────────────────────────────────────────────────────────────────────────
run_e2e() {
    log_header "End-to-End Tests (Playwright)"

    local e2e_dir="$PROJECT_ROOT/tests/e2e"
    if [[ ! -d "$e2e_dir" ]]; then
        echo -e "${YELLOW}Warn:${NC} E2E directory not found: tests/e2e — skipping"
        record_result "SKIP" "E2E tests"
        return
    fi

    # Check for "headed" sub-argument
    local headed_flag=""
    if [[ "${CONTAINER:-}" == "headed" ]]; then
        headed_flag="--headed"
        log_step "E2E tests (headed mode)"
    else
        log_step "E2E tests (headless)"
    fi

    if (cd "$e2e_dir" && npx playwright test $headed_flag); then
        log_pass "E2E tests"
        record_result "PASS" "E2E tests"
    else
        log_fail "E2E tests"
        record_result "FAIL" "E2E tests"
    fi
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────────────────────────────────
run_security() {
    log_header "Security Scans"

    # bandit — Python services
    local python_services=(
        "services/flask-backend/app"
        "services/icestreams-worker"
        "services/iceflows-worker"
        "services/iceruns-invoker"
    )

    for svc in "${python_services[@]}"; do
        local svc_dir="$PROJECT_ROOT/$svc"
        if [[ -d "$svc_dir" ]]; then
            log_step "Bandit scan: $svc"
            if command -v bandit &>/dev/null; then
                if bandit -r "$svc_dir" -ll -q; then
                    log_pass "Bandit: $svc"
                    record_result "PASS" "Security bandit: $svc"
                else
                    log_fail "Bandit: $svc"
                    record_result "FAIL" "Security bandit: $svc"
                fi
            else
                log_warn "bandit not installed — skipping Python security scan for $svc"
                record_result "SKIP" "Security bandit: $svc"
            fi
            echo ""
        fi
    done

    # npm audit — WebUI
    local webui_dir="$PROJECT_ROOT/services/webui"
    if [[ -d "$webui_dir" ]]; then
        log_step "npm audit: services/webui"
        if (cd "$webui_dir" && npm audit --audit-level=high); then
            log_pass "npm audit: webui"
            record_result "PASS" "Security npm audit: webui"
        else
            log_fail "npm audit: webui"
            record_result "FAIL" "Security npm audit: webui"
        fi
        echo ""
    fi

    # trivy — image scans (only if trivy is available and images exist)
    if command -v trivy &>/dev/null; then
        local images=(
            "icecharts-api:latest"
            "icecharts-webui:latest"
        )
        for img in "${images[@]}"; do
            if docker image inspect "$img" &>/dev/null 2>&1; then
                log_step "Trivy scan: $img"
                if trivy image --exit-code 1 --severity HIGH,CRITICAL "$img"; then
                    log_pass "Trivy: $img"
                    record_result "PASS" "Security trivy: $img"
                else
                    log_fail "Trivy: $img"
                    record_result "FAIL" "Security trivy: $img"
                fi
                echo ""
            else
                log_skip "Trivy: $img (image not found)"
                record_result "SKIP" "Security trivy: $img"
            fi
        done
    else
        log_warn "trivy not installed — skipping container image scans"
        record_result "SKIP" "Security trivy"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# LINT
# ─────────────────────────────────────────────────────────────────────────────
run_lint_flask() {
    local flask_dir="$PROJECT_ROOT/services/flask-backend"
    if [[ ! -d "$flask_dir" ]]; then
        log_skip "Lint: flask (directory not found)"
        record_result "SKIP" "Lint: flask"
        return
    fi

    log_step "Lint: flask — flake8"
    if (cd "$flask_dir" && flake8 app tests --count --show-source --statistics); then
        log_pass "Lint flask: flake8"
        record_result "PASS" "Lint flask: flake8"
    else
        log_fail "Lint flask: flake8"
        record_result "FAIL" "Lint flask: flake8"
    fi
    echo ""

    log_step "Lint: flask — black --check"
    if (cd "$flask_dir" && black --check app tests); then
        log_pass "Lint flask: black"
        record_result "PASS" "Lint flask: black"
    else
        log_fail "Lint flask: black"
        record_result "FAIL" "Lint flask: black"
    fi
    echo ""

    log_step "Lint: flask — isort --check-only"
    if (cd "$flask_dir" && isort --check-only app tests); then
        log_pass "Lint flask: isort"
        record_result "PASS" "Lint flask: isort"
    else
        log_fail "Lint flask: isort"
        record_result "FAIL" "Lint flask: isort"
    fi
    echo ""

    log_step "Lint: flask — mypy"
    if (cd "$flask_dir" && mypy app --ignore-missing-imports); then
        log_pass "Lint flask: mypy"
        record_result "PASS" "Lint flask: mypy"
    else
        log_fail "Lint flask: mypy"
        record_result "FAIL" "Lint flask: mypy"
    fi
    echo ""
}

run_lint_webui() {
    local webui_dir="$PROJECT_ROOT/services/webui"
    if [[ ! -d "$webui_dir" ]]; then
        log_skip "Lint: webui (directory not found)"
        record_result "SKIP" "Lint: webui"
        return
    fi

    log_step "Lint: webui — eslint"
    if (cd "$webui_dir" && npm run lint); then
        log_pass "Lint webui: eslint"
        record_result "PASS" "Lint webui: eslint"
    else
        log_fail "Lint webui: eslint"
        record_result "FAIL" "Lint webui: eslint"
    fi
    echo ""

    log_step "Lint: webui — tsc --noEmit"
    if (cd "$webui_dir" && npx tsc --noEmit); then
        log_pass "Lint webui: tsc"
        record_result "PASS" "Lint webui: tsc"
    else
        log_fail "Lint webui: tsc"
        record_result "FAIL" "Lint webui: tsc"
    fi
    echo ""
}

run_lint_python_worker() {
    local service_name="$1"
    local service_dir="$PROJECT_ROOT/$2"

    if [[ ! -d "$service_dir" ]]; then
        log_skip "Lint: $service_name (directory not found)"
        record_result "SKIP" "Lint: $service_name"
        return
    fi

    log_step "Lint: $service_name — flake8"
    if (cd "$service_dir" && flake8 . --count --show-source --statistics --exclude=.venv,__pycache__,*.egg-info); then
        log_pass "Lint $service_name: flake8"
        record_result "PASS" "Lint $service_name: flake8"
    else
        log_fail "Lint $service_name: flake8"
        record_result "FAIL" "Lint $service_name: flake8"
    fi
    echo ""
}

run_lint() {
    log_header "Lint Checks${CONTAINER:+ — $CONTAINER}"

    case "$CONTAINER" in
        flask)      run_lint_flask ;;
        webui)      run_lint_webui ;;
        icestreams) run_lint_python_worker "icestreams" "services/icestreams-worker" ;;
        iceflows)   run_lint_python_worker "iceflows" "services/iceflows-worker" ;;
        iceruns)    run_lint_python_worker "iceruns" "services/iceruns-invoker" ;;
        all)
            run_lint_flask
            run_lint_webui
            run_lint_python_worker "icestreams" "services/icestreams-worker"
            run_lint_python_worker "iceflows" "services/iceflows-worker"
            run_lint_python_worker "iceruns" "services/iceruns-invoker"
            ;;
    esac
}

# ─────────────────────────────────────────────────────────────────────────────
# FUNCTIONAL
# ─────────────────────────────────────────────────────────────────────────────
run_functional() {
    log_header "Functional Tests (Page Loads)"

    local pages_script="$SCRIPT_DIR/test-pages.sh"
    if [[ -f "$pages_script" ]]; then
        run_cmd "Page load tests" bash "$pages_script"
    else
        echo -e "${RED}Error:${NC} Page test script not found: scripts/test-pages.sh"
        record_result "FAIL" "Functional tests"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# SMOKE
# ─────────────────────────────────────────────────────────────────────────────
run_smoke() {
    log_header "Smoke Tests (Quick Pre-Commit Verification)"

    local smoke_script="$SCRIPT_DIR/test-alpha-smoke.sh"
    if [[ -f "$smoke_script" ]]; then
        run_cmd "Alpha smoke tests" bash "$smoke_script"
    else
        echo -e "${RED}Error:${NC} Smoke test script not found: scripts/test-alpha-smoke.sh"
        record_result "FAIL" "Smoke tests"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Summary output
# ─────────────────────────────────────────────────────────────────────────────
print_summary() {
    echo ""
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  Test Summary${NC}"
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
    echo ""

    local pass_count=0
    local fail_count=0
    local skip_count=0
    local warn_count=0

    for result in "${RESULTS[@]}"; do
        local status="${result%% *}"
        local label="${result#* }"
        case "$status" in
            PASS)
                echo -e "  ${GREEN}✓ PASS${NC}  $label"
                pass_count=$((pass_count + 1))
                ;;
            FAIL)
                echo -e "  ${RED}✗ FAIL${NC}  $label"
                fail_count=$((fail_count + 1))
                ;;
            SKIP)
                echo -e "  ${YELLOW}- SKIP${NC}  $label"
                skip_count=$((skip_count + 1))
                ;;
            WARN)
                echo -e "  ${YELLOW}⚠ WARN${NC}  $label"
                warn_count=$((warn_count + 1))
                ;;
        esac
    done

    echo ""
    echo -e "  ${BOLD}Passed:${NC}  $pass_count"
    [[ $fail_count -gt 0 ]] && echo -e "  ${RED}${BOLD}Failed:${NC}  $fail_count${NC}" || echo -e "  ${BOLD}Failed:${NC}  $fail_count"
    [[ $warn_count -gt 0 ]] && echo -e "  ${YELLOW}${BOLD}Warned:${NC}  $warn_count${NC}" || true
    [[ $skip_count -gt 0 ]] && echo -e "  ${BOLD}Skipped:${NC} $skip_count" || true
    echo ""

    if [[ $OVERALL_EXIT -eq 0 ]]; then
        echo -e "  ${GREEN}${BOLD}All checks passed!${NC}"
    else
        echo -e "  ${RED}${BOLD}Some checks failed. Review output above.${NC}"
    fi
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Main dispatch
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}${BOLD}IceCharts Test Controller${NC}"
echo -e "  Type: ${YELLOW}$TEST_TYPE${NC}  Container: ${YELLOW}$CONTAINER${NC}"
echo -e "  Project root: $PROJECT_ROOT"

case "$TEST_TYPE" in
    build)       run_build ;;
    unit)        run_unit ;;
    api)         run_api ;;
    integration) run_integration ;;
    e2e)         run_e2e ;;
    security)    run_security ;;
    lint)        run_lint ;;
    functional)  run_functional ;;
    smoke)       run_smoke ;;
esac

print_summary

exit $OVERALL_EXIT
