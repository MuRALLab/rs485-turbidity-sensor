#!/usr/bin/env bash
# sensor-latency — Modbus communication latency and stability measurement
#
# Usage:
#   sensor-latency [--samples N]
#   sensor-latency -n N
#
# Default: 10 samples
set -euo pipefail
# shellcheck source-path=SCRIPTDIR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/config.sh
source "${SCRIPT_DIR}/config.sh"
# shellcheck source=scripts/_common.sh
source "${SCRIPT_DIR}/_common.sh"

# ── Argument parsing ───────────────────────────────────────────────────────
SAMPLES=10

usage() {
    printf "Usage: %s [--samples N]\n" "$(basename "$0")"
    printf "  -n, --samples  Number of Modbus reads to perform, 1-1000 (default: %s)\n" "${SAMPLES}"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--samples) SAMPLES="$2"; shift 2 ;;
        -h|--help)    usage ;;
        *) fail "Unknown argument: $1"; usage ;;
    esac
done

# ── Header ─────────────────────────────────────────────────────────────────
printf '%s%s╔═════════════════════════════════════════════════╗%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s║      RS485 Turbidity Sensor — Latency Test       ║%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '%s%s╚═════════════════════════════════════════════════╝%s\n' "${C_BOLD}" "${C_CYAN}" "${C_RESET}"
printf '  %s%s%s\n' "${C_DIM}" "$(date '+%Y-%m-%d %H:%M:%S %Z')" "${C_RESET}"

section "Parameters"
kv "samples"   "${SAMPLES}"
kv "baudrate"  "${SENSOR_BAUDRATE}"
kv "slave ID"  "${SENSOR_SLAVE_ID}"

# ── Device accessibility ───────────────────────────────────────────────────
section "Device Check"

active_port=$(assert_device_accessible) || exit 1
ok "Device accessible: ${active_port}"

# ── Latency run via Python backend ─────────────────────────────────────────
section "Performing ${SAMPLES} Reads"

lat_output=$("${PYTHON}" "${PY_DIR}/latency.py" "${SAMPLES}" 2>&1) || true
lat_exit=$?

error_line=$(echo "${lat_output}" | grep "^ERROR:" | head -1 || true)

# Print per-sample lines
while IFS= read -r line; do
    if [[ "${line}" == SAMPLE\ *:\ OK* ]]; then
        n=$(echo "${line}"     | awk '{print $2}' | tr -d ':')
        ms=$(echo "${line}"    | grep -oP '[0-9]+\.[0-9]+ ms' | head -1)
        turb=$(echo "${line}"  | grep -oP 'turbidity=\K[0-9.]+')
        temp=$(echo "${line}"  | grep -oP 'temp=\K[0-9.]+')
        printf '  %s✔%s  sample %-4s  %s  turbidity=%-8s NTU  temp=%s °C\n' \
            "${C_GREEN}" "${C_RESET}" "${n}" "${ms}" "${turb}" "${temp}"
    elif [[ "${line}" == SAMPLE\ *:\ ERROR* ]]; then
        n=$(echo "${line}" | awk '{print $2}' | tr -d ':')
        err="${line#*ERROR  }"
        printf '  %s✘%s  sample %-4s  %s\n' "${C_RED}" "${C_RESET}" "${n}" "${err}"
    fi
done <<< "${lat_output}"

# ── Statistics summary ─────────────────────────────────────────────────────
if [[ ${lat_exit} -ne 0 || -n "${error_line}" ]]; then
    section "Result"
    err_detail="${error_line#ERROR: }"
    err_detail="${err_detail:-unknown}"
    fail "Latency test failed: ${err_detail}"
    printf '  %s%sFAILED%s\n\n' "${C_RED}" "${C_BOLD}" "${C_RESET}"
    exit 1
fi

stats_ok=$(echo "${lat_output}"  | grep "^STATS_SAMPLES_OK:"  | awk '{print $2}' || echo "0")
stats_err=$(echo "${lat_output}" | grep "^STATS_SAMPLES_ERR:" | awk '{print $2}' || echo "0")
avg_ms=$(echo "${lat_output}"    | grep "^STATS_AVG_MS:"      | awk '{print $2}' || echo "N/A")
min_ms=$(echo "${lat_output}"    | grep "^STATS_MIN_MS:"      | awk '{print $2}' || echo "N/A")
max_ms=$(echo "${lat_output}"    | grep "^STATS_MAX_MS:"      | awk '{print $2}' || echo "N/A")

section "Latency Statistics"
kv "samples OK"    "${stats_ok} / ${SAMPLES}"
kv "samples ERR"   "${stats_err}"
kv "avg latency"   "${avg_ms} ms"
kv "min latency"   "${min_ms} ms"
kv "max latency"   "${max_ms} ms"

section "Result"
if [[ "${stats_ok}" -eq "${SAMPLES}" ]]; then
    printf '  %s%sPASS%s  — all reads succeeded\n\n' "${C_GREEN}" "${C_BOLD}" "${C_RESET}"
    exit 0
elif [[ "${stats_ok}" -gt 0 ]]; then
    printf '  %s%sPARTIAL%s  — %s read(s) failed out of %s\n\n' "${C_YELLOW}" "${C_BOLD}" "${C_RESET}" "${stats_err}" "${SAMPLES}"
    exit 0
else
    printf '  %s%sFAIL%s  — no successful reads\n\n' "${C_RED}" "${C_BOLD}" "${C_RESET}"
    exit 1
fi
