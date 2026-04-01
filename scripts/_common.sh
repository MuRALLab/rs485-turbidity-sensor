#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# scripts/_common.sh — shared output formatting helpers
#
# Source this file AFTER config.sh:
#   source "$(dirname "$0")/_common.sh"
# ---------------------------------------------------------------------------

# ── ANSI colours (disabled automatically when stdout is not a terminal) ────
if [[ -t 1 ]]; then
    C_RESET=$'\033[0m'
    C_BOLD=$'\033[1m'
    C_GREEN=$'\033[0;32m'
    C_YELLOW=$'\033[0;33m'
    C_RED=$'\033[0;31m'
    C_CYAN=$'\033[0;36m'
    C_DIM=$'\033[2m'
else
    C_RESET="" C_BOLD="" C_GREEN="" C_YELLOW="" C_RED="" C_CYAN="" C_DIM=""
fi

# ── Print helpers ──────────────────────────────────────────────────────────

# Section header  ── ○ My Section ────────────────────
section() {
    local title="$1"
    printf '\n%s%s── %s %s%s\n' \
        "${C_BOLD}" "${C_CYAN}" \
        "${title}" "$(printf '%.0s─' {1..50} | head -c $((50 - ${#title})))" \
        "${C_RESET}"
}

ok()   { printf '  %s✔%s  %s\n'    "${C_GREEN}"  "${C_RESET}" "$*"; }
warn() { printf '  %s⚠%s  %s\n'    "${C_YELLOW}" "${C_RESET}" "$*"; }
fail() { printf '  %s✘%s  %s\n'    "${C_RED}"    "${C_RESET}" "$*"; }
info() { printf '  %s→%s  %s\n'    "${C_DIM}"    "${C_RESET}" "$*"; }
kv()   { printf '  %s%-22s%s %s\n' "${C_BOLD}" "$1" "${C_RESET}" "$2"; }

die() {
    fail "$*"
    exit 1
}

# ── Dependency check ───────────────────────────────────────────────────────
require_cmd() {
    local cmd="$1"
    if ! command -v "${cmd}" &>/dev/null; then
        die "Required command not found: ${cmd}"
    fi
}

# ── Serial device helpers ──────────────────────────────────────────────────

# Resolve the best available port (preferred by-id path first, then fallback)
resolve_port() {
    if [[ -e "${SENSOR_PORT}" ]]; then
        echo "${SENSOR_PORT}"
        return 0
    fi
    if [[ -e "${SENSOR_PORT_FALLBACK}" ]]; then
        echo "${SENSOR_PORT_FALLBACK}"
        return 0
    fi
    return 1
}

# Assert device exists and current user can read/write it; print diagnostics
assert_device_accessible() {
    local port
    port=$(resolve_port) || {
        fail "Serial device not found."
        info "Expected  : ${SENSOR_PORT}"
        info "Fallback  : ${SENSOR_PORT_FALLBACK}"
        info "Check USB connection and run:  lsusb | grep FTDI"
        return 1
    }

    if [[ ! -r "${port}" || ! -w "${port}" ]]; then
        fail "Permission denied: ${port}"
        info "Add your user to the 'dialout' group:"
        info "  sudo usermod -aG dialout \$USER && newgrp dialout"
        return 1
    fi

    echo "${port}"
}

# ── Python PYTHONPATH helper ───────────────────────────────────────────────
# Ensure src/ is on PYTHONPATH so wrappers can import turbidity_monitor
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
