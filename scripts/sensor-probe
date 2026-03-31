#!/usr/bin/env bash
# sensor-probe — end-to-end connectivity verification
# Usage: sensor-probe
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/config.sh
source "${SCRIPT_DIR}/config.sh"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

# ── Header ─────────────────────────────────────────────────────────────────
printf '%s%s╔═════════════════════════════════════════════════╗%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s║      RS485 Turbidity Sensor — Probe              ║%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s╚═════════════════════════════════════════════════╝%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '  %s%s%s\n' "${C_DIM}" "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${C_RESET}"

OVERALL_OK=true

# ── 1. Device existence ────────────────────────────────────────────────────
section "Serial Device Check"

active_port=""
if [[ -e "${SENSOR_PORT}" ]]; then
    active_port="${SENSOR_PORT}"
    ok "Preferred by-id path exists"
    kv "path" "${active_port}"
elif [[ -e "${SENSOR_PORT_FALLBACK}" ]]; then
    active_port="${SENSOR_PORT_FALLBACK}"
    warn "Preferred by-id path absent; using fallback"
    kv "path" "${active_port}"
else
    fail "Serial device not found"
    info "Expected : ${SENSOR_PORT}"
    info "Fallback : ${SENSOR_PORT_FALLBACK}"
    info "Check cable/USB and run:  sensor-info"
    exit 1
fi

# ── 2. Permission check ────────────────────────────────────────────────────
section "Permission Check"

if [[ -r "${active_port}" && -w "${active_port}" ]]; then
    ok "Read/write access confirmed"
else
    fail "Permission denied: ${active_port}"
    info "Fix:  sudo usermod -aG dialout \$USER && newgrp dialout"
    exit 1
fi

# ── 3. Modbus probe via Python backend ────────────────────────────────────
section "Modbus Connection + Register Read"

kv "port"      "${active_port}"
kv "baudrate"  "${SENSOR_BAUDRATE}"
kv "slave ID"  "${SENSOR_SLAVE_ID}"

probe_output=$("${PYTHON}" "${PY_DIR}/probe.py" 2>&1) || true
probe_exit=$?

# Parse structured output lines from probe.py
turb_line=$(echo "${probe_output}"     | grep "^TURBIDITY:"   | head -1 || true)
temp_line=$(echo "${probe_output}"     | grep "^TEMPERATURE:" | head -1 || true)
error_line=$(echo "${probe_output}"    | grep "^ERROR:"       | head -1 || true)

if [[ ${probe_exit} -eq 0 && -n "${turb_line}" ]]; then
    turbidity=$(echo "${turb_line}"  | awk '{print $2}')
    temperature=$(echo "${temp_line}" | awk '{print $2}')
    ok "Modbus read succeeded"
    kv "turbidity"   "${turbidity} NTU"
    kv "temperature" "${temperature} °C"
else
    OVERALL_OK=false
    err_detail="${error_line#ERROR: }"
    err_detail="${err_detail:-unknown}"
    fail "Modbus probe failed: ${err_detail}"
    case "${err_detail}" in
        no_serial_device)
            info "Device disappeared — check USB connection"
            ;;
        connect_failed)
            info "Could not open port — check baud rate (${SENSOR_BAUDRATE}), parity, cabling"
            ;;
        modbus_error*)
            info "Device responded but returned a Modbus exception"
            info "Check slave ID (${SENSOR_SLAVE_ID}) and register address (${SENSOR_REG_ADDRESS})"
            ;;
        exception*)
            info "Serial I/O exception — check cable polarity (A/B swapped?)"
            ;;
    esac
fi

# ── Summary ────────────────────────────────────────────────────────────────
section "Result"

if ${OVERALL_OK}; then
    printf '  %s%sPASS%s  — sensor is reachable and responding\n' "${C_GREEN}" "${C_BOLD}" "${C_RESET}"
    printf '\n'
    exit 0
else
    printf '  %s%sFAIL%s  — sensor probe unsuccessful\n' "${C_RED}" "${C_BOLD}" "${C_RESET}"
    printf '\n'
    exit 1
fi
