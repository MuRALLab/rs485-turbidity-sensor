# How to collect data with the current setup

## 1. Network setup

Connect the Raspberry Pi and the PC on the same LAN segment using a switch or direct Ethernet cable.

| Device | IP address | Subnet mask | Mode |
| --- | --- | --- | --- |
| PC | `192.168.1.51` | `255.255.255.0` | Manual (static) |
| Raspberry Pi 4 | `192.168.1.50` | `255.255.255.0` | Static |

Configure the PC network interface manually (no DHCP) with the values above before connecting.

---

## 2. SSH into the Raspberry Pi

```bash
ssh murallab@192.168.1.50
```

Default credentials:

| Field | Value |
| --- | --- |
| Username | `murallab` |
| Password | `murallab` |

> The Pi runs Ubuntu Server 22.04 headless — there is no desktop/GUI environment.

Connect VS Code to the Pi for remote editing and terminal access.

---

## 3. Prepare the Python environment

Navigate to the project directory and synchronise the virtual environment:

```bash
cd ~/rs485-turbidity-sensor
uv sync
source .venv/bin/activate
```

`uv sync` reads `pyproject.toml`, resolves all dependencies (`pymodbus`, `pyserial`, `matplotlib`, `ruff`), and installs them into `.venv/` if not already present. Run it once after cloning or after any dependency change.

---

## 4. Run the data acquisition script

### Run indefinitely (stopped with Ctrl-C)

```bash
python main.py
```

### Run for a fixed duration

```bash
python main.py --duration 300      # stop after 300 seconds
python main.py -d 600              # stop after 600 seconds
```

### Change the poll interval (default 2.0 s = 0.5 Hz)

```bash
python main.py --interval 1.0      # poll every 1 second (1 Hz)
python main.py -i 5.0              # poll every 5 seconds
```

### Combined example

```bash
python main.py --duration 600 --interval 1.0
# or shorthand:
python main.py -d 600 -i 1.0
```

### Full CLI reference

```bash
usage: main.py [-h] [--duration SECONDS] [--interval SECONDS]

Continuous turbidity data acquisition from RS485 sensor.

options:
  -h, --help            show this help message and exit
  --duration, -d SECONDS
                        How long to run in seconds. Omit for indefinite.
                        (default: None)
  --interval, -i SECONDS
                        Poll interval in seconds (0.5 Hz = 2.0 s).
                        (default: 2.0)
```

On startup the script prints the session start time, the path to the data log file, and the active poll interval:

```bash
Session started : 2026-04-01T11:30:00
Data log        : /home/murallab/rs485-turbidity-sensor/data_log/turbidity_log_20260401_113000.csv
Poll interval   : 2.0s
Press Ctrl-C to stop.
```

---

## 5. How data is logged

### File location and naming

Each run creates one new CSV file inside `data_log/`:

```bash
data_log/
└── turbidity_log_YYYYMMDD_HHMMSS.csv
```

The timestamp in the filename is the **session start time** (system clock of the Pi), so every run produces a uniquely named file and no run ever overwrites another.

### CSV format

```csv
timestamp,turbidity_ntu,temperature_c,status
2026-04-01T11:30:02.341,12.3,24.5,ok
2026-04-01T11:30:04.353,12.4,24.5,ok
2026-04-01T11:30:06.401,,,error: [Errno 5] Input/output error
```

| Column | Format | Description |
| --- | --- | --- |
| `timestamp` | ISO 8601, millisecond precision | System clock of the Pi at moment of read |
| `turbidity_ntu` | Float, 1 decimal place | Turbidity in NTU (register 0 ÷ 10) |
| `temperature_c` | Float, 1 decimal place | Temperature in °C (register 1 ÷ 10) |
| `status` | `ok` or `error: <detail>` | `ok` for valid reads; error rows leave sensor fields empty |

### Write behaviour and data integrity

- The file handle stays **open for the entire session** — no open/close overhead per row.
- Every row is **flushed to disk immediately** after writing (`flush()` is called on every `append()` and `append_error()`). This means data is safe even on a hard power loss or `kill -9`.
- Communication errors (Modbus exceptions, serial I/O errors) are written as `error:` rows instead of being silently dropped, so the timeline in the CSV is complete.

### On exit

When the session ends (duration reached, Ctrl-C, or any unhandled exception) the `finally` block:

1. Closes the CSV file cleanly.
2. Generates a two-panel PNG plot (turbidity + temperature vs. time) saved to `plots/turbidity_plot_YYYYMMDD_HHMMSS.png`.
3. Appends a session summary row to `logs/health_metrics.csv`.
4. Prints a session summary to stdout:

```bash
── Session Summary ──────────────────────────────
  duration_s       : 300.1
  total_reads      : 150
  read_errors      : 0
  disconnect_count : 0
  mean_uptime_s    : 300.10
  data_log         : data_log/turbidity_log_20260401_113000.csv
  plot             : plots/turbidity_plot_20260401_113000.png
  health_csv       : logs/health_metrics.csv
─────────────────────────────────────────────────
```

### Copying data back to the PC

From the PC, use `scp` to retrieve the latest log and plot:

```bash
scp murallab@192.168.1.50:~/rs485-turbidity-sensor/data_log/turbidity_log_*.csv ./
scp murallab@192.168.1.50:~/rs485-turbidity-sensor/plots/turbidity_plot_*.png ./
```
