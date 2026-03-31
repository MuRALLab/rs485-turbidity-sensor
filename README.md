# Turbidity Transmitter Monitoring System

A Python-based monitoring and data acquisition system for the **RS-ZD-N01-1S-1000-EX** turbidity transmitter communicating over RS485. The system provides real-time sensor data collection, live visualization, health metrics tracking, and robust reconnection handling for reliable long-term sensor monitoring.

---

## Table of Contents

- [Overview](#overview)
- [Hardware Specifications](#hardware-specifications)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Output Artifacts](#output-artifacts)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [References](#references)

---

## Overview

This project provides an integrated monitoring solution for turbidity and temperature data acquisition from RS485-enabled sensors. Key features include:

- **Real-time data visualization** with live-updating dual-axis plots
- **Robust reconnection logic** with exponential backoff and periodic adapter rescanning
- **Health tracking** with disconnect counters and uptime statistics
- **Kernel USB event logging** to diagnose communication failures
- **Modular architecture** for easy extension and integration

---

## Hardware Specifications

### Sensor Model

**RS-ZD-N01-1S-1000-EX** — Turbidity Transmitter

| Specification | Value |
| --- | --- |
| **Output Signal** | RS485 (Modbus RTU) |
| **Measurement Range** | 0.0 – 1000.0 NTU |
| **Power Supply** | 10 – 30 V (DC) |
| **Baud Rate** | 4800 bps (configurable) |
| **Data Format** | 8 data bits, 1 stop bit, no parity (8N1) |
| **Device Address** | 1 (Modbus device ID) |

### Connection Diagram

![Transmitter connection diagram](asset/transmitter_connections.svg "RS485 Cable Connection: Connect A/B differential pair to USB-RS485 adapter; provide 10–30V DC supply")

**Cable Configuration:**

- **Cable 1 (Brown):** Power supply positive (10~30V DC)
- **Cable 2 (Black):** Power supply negative
- **Cable 3 (Blue):** RS485 Data Line A
- **Cable 4 (White):** RS485 Data Line B

![USB-RS485 Adapter Connection](asset/usb-2-rs485_wire_connection.svg "Connect RS485 A/B lines to adapter; adapter connects to PC via USB")

For more details, refer to the official [Turbidity-transmitter-User-Manual.pdf](./Turbidity-transmitter-User-Manual.pdf).

---

## System Architecture

The system is organized into modular, reusable components under the `src/turbidity_monitor` package:

```bash
src/turbidity_monitor/
├── config.py                    # Centralized runtime configuration
├── connection/
│   ├── ports.py                # USB adapter discovery
│   ├── backoff.py              # Exponential reconnect backoff strategy
│   └── usb_event_logger.py     # Kernel USB disconnect event logging
├── health/
│   ├── metrics.py              # Disconnect counters & uptime tracking
│   └── csv_reporter.py         # Health metrics CSV persistence
└── visualization/
    └── live_plot.py            # Real-time dual-axis plotting with save-on-exit
```

### Workflow

1. **Connection & Discovery:** Resolves USB-RS485 adapter via `/dev/serial/by-id` (stable path) or `/dev/ttyUSB*`.
2. **Modbus Read Loop:** Polls turbidity and temperature registers at 2-second intervals.
3. **Data Visualization:** Updates live plot window in real-time.
4. **Failure Handling:** On disconnect, logs kernel USB events, saves plot snapshot, records to health CSV, and enters managed reconnect with exponential backoff.
5. **Session Exit:** Saves final plot, appends session summary to health CSV, and prints end-of-session statistics.

---

## Installation

### Prerequisites

- Python 3.10+
- USB-RS485 adapter (tested with FTDI FT232R)
- 10–30V DC power supply for sensor

### Environment Setup

1. **Clone the repository and navigate to it:**

   ```bash
   cd /path/to/rs485-turbidity-sensor
   ```

2. **Create and activate a virtual environment: use `uv` (optional but recommended):**

   ```bash
   uv sync
   ```

3. **Verify installation:**

   ```bash
   python -c "from turbidity_monitor.config import MonitorConfig; print('Package import successful')"
   ```

---

## Quick Start

### Run the Sensor Monitor

```bash
uv run read_sensor_resolve_adapter.py
# or
python read_sensor_resolve_adapter.py
```

**Expected output:**

```bash
Reading data (Press Ctrl+C to stop)...
Connected on /dev/serial/by-id/usb-FTDI_USB_Serial_Converter_FTB6SPL3-if00-port0
Turbidity: 0.5 NTU | Temperature: 25.3 °C
Turbidity: 0.6 NTU | Temperature: 25.2 °C
...
```

### Run with a Time Limit

```bash
uv run read_sensor_resolve_adapter.py --duration 300  # Run for 5 minutes
# or
python read_sensor_resolve_adapter.py --duration 300
```

---

## Usage

### Command-Line Options

| Option | Description |
| --- | --- |
| `-d`, `--duration <SECONDS>` | Run for a specified duration (seconds), then exit. Omit to run indefinitely. |

### Interactive Controls

- **Ctrl+C:** Stop monitoring, save final plot, and print session summary.
- **Live Plot Window:** The matplotlib window updates in real-time; close it (press `Q`) to dismiss without stopping data collection.

### Configuration

Edit `src/turbidity_monitor/config.py` to customize runtime parameters:

```python
@dataclass(frozen=True)
class MonitorConfig:
    baudrate: int = 4800
    backoff_initial_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    backoff_factor: float = 2.0
    rescan_interval_seconds: float = 5.0
    poll_interval_seconds: float = 2.0
    # ... other settings
```

---

## Output Artifacts

All output files are saved in the repository root under `logs/` and `plots/`:

### Logs Directory (`logs/`)

1. **`usb_events_YYYYMMDD.md`** – Markdown log of USB disconnect incidents with recent kernel USB events.
   - Appended on each disconnect.
   - Human-readable format suitable for troubleshooting.

2. **`health_metrics.csv`** – CSV table tracking session and disconnect statistics.
   - **Columns:** timestamp, event, port, reason, disconnect_count, uptime_seconds, mean_uptime_seconds, total_reads, read_errors
   - One row per disconnect event, plus a session summary row on exit.
   - Useful for trend analysis and reliability audits.

### Plots Directory (`plots/`)

1. **`transmitter_plot_disconnect_YYYYMMDD_HHMMSS.png`** – High-resolution plot snapshot saved on each USB disconnect.
2. **`transmitter_plot_exit_YYYYMMDD_HHMMSS.png`** – Final plot snapshot saved on session exit (Ctrl+C or duration end).

---

## Troubleshooting

### USB Adapter Not Found

**Error:** `No USB-RS485 port found. Waiting...`

**Solutions:**

1. Verify adapter is plugged in: `ls /dev/ttyUSB* /dev/serial/by-id/*`.
2. Check permissions: `ls -l /dev/ttyUSB0` should be readable by your user.
3. If needed, add user to `dialout` group: `sudo usermod -aG dialout $USER` (then log out/in).

### Repeated Disconnects / Kernel USB Errors

**Error:** `Serial I/O error ([Errno 5] Input/output error). Reconnecting...`

**Root causes** (see `logs/usb_events_YYYYMMDD.md`):

- EMI or noise on RS485 cable
- Loose connector or poor wiring
- USB hub power issues
- Weak/damaged cable

**Solutions:**

1. Check kernel logs: `dmesg | grep -i usb` or `journalctl -k | grep -i ftdi`.
2. Use a short, shielded USB cable.
3. Add a powered USB hub between PC and adapter.
4. Ensure proper RS485 termination (120Ω resistor) at cable ends if required.
5. Verify ground connections and A/B cable polarity.

### Modbus Read Failures

**Error:** `Modbus Error: <result>`

**Solutions:**

1. Verify sensor power supply is 10–30V and properly connected.
2. Check Modbus device address (default: 1) in config and sensor settings.
3. Inspect RS485 wiring for proper A/B polarity.
4. Test with a standalone Modbus tool (e.g., `mbpoll`) to isolate the issue.

---

## Project Structure

```bash
turbidity_transmitter/
├── README.md                           # This file
├── pyproject.toml                      # Project metadata & Hatchling build config
├── read_sensor_resolve_adapter.py      # Main entry point (orchestrator)
├── read_sensor.py                      # Legacy minimal reader (reference)
├── Turbidity-transmitter-User-Manual.pdf
├── asset/
│   └── transmitter_connections.svg     # Hardware connection diagram
├── src/
│   └── turbidity_monitor/              # Modular monitoring package
│       ├── __init__.py
│       ├── config.py
│       ├── connection/
│       ├── health/
│       └── visualization/
├── logs/                               # Runtime logs & metrics (auto-created)
├── plots/                              # Plot snapshots (auto-created)
└── .venv/                              # Virtual environment (optional)
```

---

## References

- **Sensor Manual:** [Turbidity-transmitter-User-Manual.pdf](./Turbidity-transmitter-User-Manual.pdf)
- **Modbus RTU Spec:** [Modbus Organization](https://modbus.org/) — [Modbus RTU Protocol](https://www.modbustools.com/modbus.html)
- **PyModbus Documentation:** [pymodbus 3.12+ API](https://pymodbus.readthedocs.io/)
- **PySerial Documentation:** [pyserial 3.5 API](https://pythonhosted.org/pyserial/)

---

## License

This project is provided as-is for educational and field monitoring purposes under the [MIT License](./LICENSE). Refer to the sensor manufacturer's documentation for compliance and regulatory requirements.
