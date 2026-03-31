#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# scripts/config.sh — shared configuration for the RS485 CLI toolkit
#
# Source this file at the top of every script:
#   source "$(dirname "$0")/config.sh"
#
# All values here must stay in sync with:
#   src/turbidity_monitor/config.py  (PREFERRED_PORT, MonitorConfig)
# ---------------------------------------------------------------------------

# Persistent by-id path for the FTDI USB-RS485 adapter.
# This never changes even if the USB port is re-enumerated.
export SENSOR_PORT="/dev/serial/by-id/usb-FTDI_USB_Serial_Converter_FTB6SPL3-if00-port0"

# Fallback path used only when by-id path is absent (fresh boot race, etc.)
export SENSOR_PORT_FALLBACK="/dev/ttyUSB0"

# Serial / Modbus RTU parameters (must match MonitorConfig defaults)
export SENSOR_BAUDRATE=4800
export SENSOR_SLAVE_ID=1

# Modbus register layout
export SENSOR_REG_ADDRESS=0    # decimal
export SENSOR_REG_COUNT=2

# Python interpreter: prefer the project venv, fall back to system python3
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"

if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    PYTHON="${REPO_ROOT}/.venv/bin/python"
else
    PYTHON="python3"
fi
export PYTHON

# Python wrapper scripts live here
export PY_DIR="${_SCRIPT_DIR}/py"
