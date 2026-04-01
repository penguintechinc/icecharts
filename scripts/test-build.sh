#!/bin/bash
# Comprehensive Docker and frontend build test for IceCharts services
# Tests that all service images build successfully, then cleans up test images.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'  # No color

PASS=0
FAIL=0
SKIP=0
BUILT_IMAGES=()

log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC}  $*"; }
log_fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }
log_skip()  { echo -e "${YELLOW}[SKIP]${NC}  $*"; }
log_head()  { echo -e "\n${BOLD}${CYAN}=== $* ===${NC}"; }

# Build a Docker image from a Dockerfile and context directory.
# Usage: build_image <label> <dockerfile> <context_dir> [extra_args...]
build_image() {
    local label="$1"
    local dockerfile="$2"
    local context="$3"
    shift 3
    local extra_args=("$@")
    local tag="icecharts-build-test-$(echo "$label" | tr '[:upper:] /' '[:lower:]-'):latest"

    log_info "Building $label ..."
    if docker build \
        -f "$dockerfile" \
        "${extra_args[@]}" \
        -t "$tag" \
        "$context" \
        > /tmp/docker-build-"$(echo "$label" | tr ' /' '--')".log 2>&1; then
        log_pass "$label"
        BUILT_IMAGES+=("$tag")
        (( PASS++ )) || true
    else
        log_fail "$label"
        echo "    Build log (last 20 lines):"
        tail -20 /tmp/docker-build-"$(echo "$label" | tr ' /' '--')".log | sed 's/^/      /'
        (( FAIL++ )) || true
    fi
}

# Skip a test with a reason.
skip_build() {
    local label="$1"
    local reason="$2"
    log_skip "$label ($reason)"
    (( SKIP++ )) || true
}

# ─────────────────────────────────────────────────────────────────────────────
log_head "Docker Build Tests — IceCharts Services"

# 1. Flask Backend
FLASK_DIR="$REPO_ROOT/services/flask-backend"
if [ -f "$FLASK_DIR/Dockerfile" ]; then
    build_image "flask-backend" "$FLASK_DIR/Dockerfile" "$FLASK_DIR"
else
    skip_build "flask-backend" "Dockerfile not found"
fi

# 2. WebUI
WEBUI_DIR="$REPO_ROOT/services/webui"
if [ -f "$WEBUI_DIR/Dockerfile" ]; then
    build_image "webui" "$WEBUI_DIR/Dockerfile" "$WEBUI_DIR"
else
    skip_build "webui" "Dockerfile not found"
fi

# 3. IceStreams Worker
ICESTREAMS_DIR="$REPO_ROOT/services/icestreams-worker"
if [ -f "$ICESTREAMS_DIR/Dockerfile" ]; then
    build_image "icestreams-worker" "$ICESTREAMS_DIR/Dockerfile" "$ICESTREAMS_DIR"
else
    skip_build "icestreams-worker" "Dockerfile not found"
fi

# 4. IceFlows Worker
ICEFLOWS_DIR="$REPO_ROOT/services/iceflows-worker"
if [ -f "$ICEFLOWS_DIR/Dockerfile" ]; then
    build_image "iceflows-worker" "$ICEFLOWS_DIR/Dockerfile" "$ICEFLOWS_DIR"
else
    skip_build "iceflows-worker" "Dockerfile not found"
fi

# 5. IceRuns Invoker
ICERUNS_DIR="$REPO_ROOT/services/iceruns-invoker"
if [ -f "$ICERUNS_DIR/Dockerfile" ]; then
    build_image "iceruns-invoker" "$ICERUNS_DIR/Dockerfile" "$ICERUNS_DIR"
else
    skip_build "iceruns-invoker" "Dockerfile not found"
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Runtime Image Builds — iceruns-invoker"

RUNTIME_IMAGES_DIR="$ICERUNS_DIR/runtime-images"
if [ -d "$RUNTIME_IMAGES_DIR" ]; then
    # Discover all *.dockerfile files in the runtime-images directory
    shopt -s nullglob
    runtime_dockerfiles=("$RUNTIME_IMAGES_DIR"/*.dockerfile)
    shopt -u nullglob

    if [ ${#runtime_dockerfiles[@]} -eq 0 ]; then
        skip_build "runtime-images" "no *.dockerfile found in runtime-images/"
    else
        for dockerfile in "${runtime_dockerfiles[@]}"; do
            filename=$(basename "$dockerfile")
            lang="${filename%.dockerfile}"   # extract the language name
            build_image "runtime-image/$lang" "$dockerfile" "$RUNTIME_IMAGES_DIR"
        done
    fi
else
    skip_build "runtime-images" "services/iceruns-invoker/runtime-images/ not found"
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "WebUI Frontend Build (npm run build)"

if [ -f "$WEBUI_DIR/package.json" ]; then
    log_info "Running npm run build in $WEBUI_DIR ..."
    if ( cd "$WEBUI_DIR" && npm run build > /tmp/webui-npm-build.log 2>&1 ); then
        log_pass "webui npm build"
        (( PASS++ )) || true
    else
        log_fail "webui npm build"
        echo "    Build log (last 20 lines):"
        tail -20 /tmp/webui-npm-build.log | sed 's/^/      /'
        (( FAIL++ )) || true
    fi
else
    skip_build "webui npm build" "package.json not found"
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Cleanup — Removing Test Images"

if [ ${#BUILT_IMAGES[@]} -gt 0 ]; then
    for img in "${BUILT_IMAGES[@]}"; do
        if docker rmi "$img" > /dev/null 2>&1; then
            log_info "Removed $img"
        else
            log_info "Could not remove $img (may already be gone)"
        fi
    done
else
    log_info "No test images to remove."
fi

# ─────────────────────────────────────────────────────────────────────────────
log_head "Build Test Summary"

TOTAL=$(( PASS + FAIL + SKIP ))
echo -e "  Total:  ${BOLD}${TOTAL}${NC}"
echo -e "  ${GREEN}Passed: ${PASS}${NC}"
echo -e "  ${RED}Failed: ${FAIL}${NC}"
echo -e "  ${YELLOW}Skipped: ${SKIP}${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}${BOLD}Build test FAILED — $FAIL build(s) failed.${NC}"
    exit 1
else
    echo -e "${GREEN}${BOLD}All builds passed.${NC}"
    exit 0
fi
