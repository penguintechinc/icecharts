#!/bin/bash
# Comprehensive lint script for all IceCharts services.
# Runs flake8, black --check, isort --check-only, mypy (Python) and
# ESLint + tsc --noEmit (WebUI).  Prints a summary and exits 1 on any failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

log_info() { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC}  $*"; }
log_fail() { echo -e "${RED}[FAIL]${NC}  $*"; }
log_skip() { echo -e "${YELLOW}[SKIP]${NC}  $*"; }
log_head() { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# Run a single lint step.
# Usage: run_check <label> <working_dir> <command> [args...]
run_check() {
    local label="$1"
    local work_dir="$2"
    shift 2
    local cmd=("$@")
    local log_file="/tmp/lint-$(echo "$label" | tr ' /:' '---').log"

    log_info "Checking $label ..."
    if ( cd "$work_dir" && "${cmd[@]}" > "$log_file" 2>&1 ); then
        log_pass "$label"
        (( PASS++ )) || true
    else
        log_fail "$label"
        # Show last 30 lines of output on failure
        tail -30 "$log_file" | sed 's/^/      /'
        (( FAIL++ )) || true
    fi
}

skip_check() {
    local label="$1"
    local reason="$2"
    log_skip "$label ($reason)"
    (( SKIP++ )) || true
}

# Check whether a command is available on PATH.
has_cmd() { command -v "$1" > /dev/null 2>&1; }

# ─────────────────────────────────────────────────────────────────────────────
log_head "Python Linting — flake8"

# All Python services that have source code to lint.
declare -A PY_SERVICES=(
    ["flask-backend"]="app tests"
    ["icestreams-worker"]="."
    ["iceflows-worker"]="."
    ["iceruns-invoker"]="app tests"
)

for svc in "flask-backend" "icestreams-worker" "iceflows-worker" "iceruns-invoker"; do
    svc_dir="$REPO_ROOT/services/$svc"
    src_paths="${PY_SERVICES[$svc]}"

    if [ ! -d "$svc_dir" ]; then
        skip_check "flake8/$svc" "directory not found"
        continue
    fi

    if ! has_cmd flake8; then
        skip_check "flake8/$svc" "flake8 not installed"
        continue
    fi

    # Build the list of paths to check (filter to those that exist)
    lint_targets=()
    for p in $src_paths; do
        [ -e "$svc_dir/$p" ] && lint_targets+=("$p")
    done

    if [ ${#lint_targets[@]} -eq 0 ]; then
        skip_check "flake8/$svc" "no source paths found"
        continue
    fi

    run_check "flake8/$svc" "$svc_dir" \
        flake8 "${lint_targets[@]}" \
            --max-line-length=99 \
            --extend-ignore=E402,W503 \
            --exclude=__pycache__,node_modules,dist,.venv,venv,.eggs,build,.git
done

# ─────────────────────────────────────────────────────────────────────────────
log_head "Python Formatting — black --check (flask-backend)"

FLASK_DIR="$REPO_ROOT/services/flask-backend"
if [ ! -d "$FLASK_DIR" ]; then
    skip_check "black/flask-backend" "directory not found"
elif ! has_cmd black; then
    skip_check "black/flask-backend" "black not installed"
else
    run_check "black/flask-backend" "$FLASK_DIR" \
        black --check --diff app tests
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Python Import Order — isort --check-only (flask-backend)"

if [ ! -d "$FLASK_DIR" ]; then
    skip_check "isort/flask-backend" "directory not found"
elif ! has_cmd isort; then
    skip_check "isort/flask-backend" "isort not installed"
else
    run_check "isort/flask-backend" "$FLASK_DIR" \
        isort --check-only --diff app tests
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Python Type Checking — mypy (flask-backend)"

if [ ! -d "$FLASK_DIR" ]; then
    skip_check "mypy/flask-backend" "directory not found"
elif ! has_cmd mypy; then
    skip_check "mypy/flask-backend" "mypy not installed"
else
    # mypy is non-blocking in CI (continue-on-error) but we track it here.
    run_check "mypy/flask-backend" "$FLASK_DIR" \
        mypy app --ignore-missing-imports
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "WebUI — ESLint"

WEBUI_DIR="$REPO_ROOT/services/webui"
if [ ! -f "$WEBUI_DIR/package.json" ]; then
    skip_check "eslint/webui" "package.json not found"
elif ! has_cmd npm; then
    skip_check "eslint/webui" "npm not installed"
else
    run_check "eslint/webui" "$WEBUI_DIR" npm run lint
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "WebUI — TypeScript type check (tsc --noEmit)"

if [ ! -f "$WEBUI_DIR/package.json" ]; then
    skip_check "tsc/webui" "package.json not found"
elif ! has_cmd npm; then
    skip_check "tsc/webui" "npm not installed"
else
    run_check "tsc/webui" "$WEBUI_DIR" npx tsc --noEmit
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Lint Summary"

TOTAL=$(( PASS + FAIL + SKIP ))
echo -e "  Total:   ${BOLD}${TOTAL}${NC}"
echo -e "  ${GREEN}Passed:  ${PASS}${NC}"
echo -e "  ${RED}Failed:  ${FAIL}${NC}"
echo -e "  ${YELLOW}Skipped: ${SKIP}${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}${BOLD}Lint FAILED — $FAIL check(s) failed.${NC}"
    exit 1
else
    echo -e "${GREEN}${BOLD}All lint checks passed.${NC}"
    exit 0
fi
