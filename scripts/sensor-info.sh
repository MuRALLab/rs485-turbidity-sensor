#!/usr/bin/env bash
# sensor-info — complete hardware and adapter overview
# Usage: sensor-info
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/config.sh
source "${SCRIPT_DIR}/config.sh"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

# ── Header ─────────────────────────────────────────────────────────────────
printf '%s%s╔═════════════════════════════════════════════════╗%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s║      RS485 Turbidity Sensor — System Info        ║%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s╚═════════════════════════════════════════════════╝%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '  %s%s%s\n' "${C_DIM}" "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${C_RESET}"

# ── 1. USB detection ────────────────────────────────────────────────────────
section "USB / FTDI Adapter"

if command -v lsusb &>/dev/null; then
    ftdi_lines=$(lsusb 2>/dev/null | grep -i "FTDI\|0403:" || true)
    if [[ -n "${ftdi_lines}" ]]; then
        while IFS= read -r line; do
            ok "${line}"
        done <<< "${ftdi_lines}"
    else
        warn "No FTDI device found via lsusb"
        info "Expected: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC"
    fi
else
    warn "lsusb not available — skipping USB detection"
fi

# ── 2. Kernel modules ──────────────────────────────────────────────────────
section "Kernel Modules"

for mod in ftdi_sio usbserial; do
    if lsmod 2>/dev/null | grep -q "^${mod}"; then
        size=$(lsmod | awk -v m="${mod}" '$1==m{print $2}')
        ok "${mod}  (size: ${size} bytes)"
    else
        warn "${mod} — NOT loaded"
        info "Load with:  sudo modprobe ${mod}"
    fi
done

# ── 3. Serial devices ──────────────────────────────────────────────────────
section "Available Serial Devices"

tty_usb_list=$(ls /dev/ttyUSB* 2>/dev/null || true)
if [[ -n "${tty_usb_list}" ]]; then
    while IFS= read -r dev; do
        kv "device" "${dev}"
    done <<< "${tty_usb_list}"
else
    warn "No /dev/ttyUSB* devices found"
fi

by_id_list=$(ls /dev/serial/by-id/ 2>/dev/null || true)
if [[ -n "${by_id_list}" ]]; then
    section "Persistent By-ID Links"
    while IFS= read -r link; do
        target=$(readlink -f "/dev/serial/by-id/${link}" 2>/dev/null || echo "?")
        kv "${link}" "→ ${target}"
    done <<< "${by_id_list}"
fi

# ── 4. Preferred port check ────────────────────────────────────────────────
section "Preferred Port"

kv "configured" "${SENSOR_PORT}"
if [[ -e "${SENSOR_PORT}" ]]; then
    ok "Path exists"
    resolved=$(readlink -f "${SENSOR_PORT}" 2>/dev/null || echo "(unresolved)")
    kv "resolves to" "${resolved}"
else
    warn "Preferred by-id path NOT found"
    if [[ -e "${SENSOR_PORT_FALLBACK}" ]]; then
        warn "Fallback present: ${SENSOR_PORT_FALLBACK}"
    else
        fail "No serial device available at all"
    fi
fi

# ── 5. Permissions ─────────────────────────────────────────────────────────
section "Device Permissions"

port_to_check="${SENSOR_PORT}"
[[ ! -e "${port_to_check}" ]] && port_to_check="${SENSOR_PORT_FALLBACK}"

if [[ -e "${port_to_check}" ]]; then
    perm_line=$(ls -l "${port_to_check}" 2>/dev/null)
    kv "ls -l" "${perm_line}"

    user_groups=$(groups 2>/dev/null || id -Gn)
    kv "current user" "$(id -un)  [groups: ${user_groups}]"

    if [[ -r "${port_to_check}" && -w "${port_to_check}" ]]; then
        ok "Current user can read and write"
    else
        fail "Permission denied for current user"
        info "Fix:  sudo usermod -aG dialout \$USER && newgrp dialout"
    fi
else
    info "No device to check permissions for"
fi

# ── 6. Modbus configuration summary ───────────────────────────────────────
section "Configured Modbus Parameters"

kv "baudrate"    "${SENSOR_BAUDRATE}"
kv "slave ID"    "${SENSOR_SLAVE_ID}"
kv "reg address" "${SENSOR_REG_ADDRESS}  (0x$(printf '%04X' "${SENSOR_REG_ADDRESS}"))"
kv "reg count"   "${SENSOR_REG_COUNT}"
kv "python"      "${PYTHON}"

# ── 7. Recent kernel USB events ───────────────────────────────────────────
section "Recent Kernel USB Events"

if command -v journalctl &>/dev/null; then
    journal_out=$(journalctl -k -n 80 --no-pager 2>/dev/null \
        | grep -iE "(usb|ttyusb|ftdi|disconnect|reset|error)" \
        | tail -20 || true)
    if [[ -n "${journal_out}" ]]; then
        while IFS= read -r line; do
            info "${line}"
        done <<< "${journal_out}"
    else
        info "No relevant kernel USB events found in recent journal"
    fi
elif command -v dmesg &>/dev/null; then
    dmesg_out=$(dmesg --color=never 2>/dev/null \
        | grep -iE "(usb|ttyusb|ftdi|disconnect|reset|error)" \
        | tail -20 || true)
    if [[ -n "${dmesg_out}" ]]; then
        while IFS= read -r line; do
            info "${line}"
        done <<< "${dmesg_out}"
    else
        info "No relevant kernel USB events found in dmesg"
    fi
else
    warn "Neither journalctl nor dmesg available"
fi

printf "\n"
exit 0
