#!/usr/bin/env python3
"""Single entry point for continuous turbidity data acquisition.

Usage
-----
    python main.py                        # runs indefinitely
    python main.py --duration 300         # stops after 300 seconds
    python main.py --interval 2.0         # custom poll interval in seconds
    python main.py -d 600 -i 1.0          # 600 s run, 1 Hz polling

On exit (normal, timeout, or Ctrl-C):
  - Open sensor data CSV is flushed and closed.
  - A two-panel PNG plot (turbidity + temperature vs. time) is written to plots/.
  - A health summary row is appended to logs/health_metrics.csv.
  - A session summary is printed to stdout.
"""

import argparse
import datetime as dt
import time

from pymodbus.client import ModbusSerialClient

from turbidity_monitor.config import MonitorConfig, data_log_dir, logs_dir, plots_dir
from turbidity_monitor.connection.backoff import ReconnectBackoff
from turbidity_monitor.connection.ports import resolve_port
from turbidity_monitor.connection.usb_event_logger import KernelUsbEventLogger
from turbidity_monitor.health.csv_reporter import HealthCsvReporter
from turbidity_monitor.health.metrics import HealthMetrics
from turbidity_monitor.logging.data_logger import SensorDataLogger
from turbidity_monitor.visualization.static_plotter import StaticPlotter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(port: str, config: MonitorConfig) -> ModbusSerialClient:
    return ModbusSerialClient(
        port=port,
        baudrate=config.baudrate,
        parity=config.parity,
        stopbits=config.stopbits,
        bytesize=config.bytesize,
        timeout=config.timeout,
    )


# ---------------------------------------------------------------------------
# Acquisition loop
# ---------------------------------------------------------------------------


def run(duration: int | None, poll_interval: float) -> None:
    config = MonitorConfig(poll_interval_seconds=poll_interval)
    session_start = dt.datetime.now()
    start_monotonic = time.monotonic()

    data_logger = SensorDataLogger(data_log_dir(), session_start)
    plotter = StaticPlotter(plots_dir())
    usb_logger = KernelUsbEventLogger(logs_dir())
    health = HealthMetrics()
    csv_reporter = HealthCsvReporter(logs_dir() / "health_metrics.csv")
    backoff = ReconnectBackoff(
        initial_seconds=config.backoff_initial_seconds,
        max_seconds=config.backoff_max_seconds,
        factor=config.backoff_factor,
        rescan_interval_seconds=config.rescan_interval_seconds,
    )

    client: ModbusSerialClient | None = None
    selected_port: str | None = None

    print(f"Session started : {session_start.isoformat(timespec='seconds')}")
    print(f"Data log        : {data_logger.path}")
    print(f"Poll interval   : {poll_interval}s")
    if duration:
        print(f"Duration        : {duration}s")
    print("Press Ctrl-C to stop.\n")

    try:
        while True:
            # ── Duration guard ────────────────────────────────────────────
            if duration is not None and (time.monotonic() - start_monotonic) >= duration:
                print(f"\nTime limit of {duration}s reached. Stopping.")
                break

            # ── Connect / reconnect ───────────────────────────────────────
            if client is None or not client.connected:
                if selected_port is None or backoff.should_rescan():
                    selected_port = resolve_port()

                if not selected_port:
                    wait = backoff.register_failure()
                    print(f"No USB-RS485 port found. Rescanning in {wait:.1f}s...")
                    time.sleep(wait)
                    continue

                client = _make_client(selected_port, config)
                if not client.connect():
                    wait = backoff.register_failure()
                    print(f"Cannot open {selected_port}. Retrying in {wait:.1f}s...")
                    client = None
                    time.sleep(wait)
                    continue

                backoff.reset()
                health.on_connect()
                print(f"Connected on {selected_port}")

            # ── Poll sensor ───────────────────────────────────────────────
            try:
                result = client.read_holding_registers(
                    address=config.register_address,
                    count=config.register_count,
                    device_id=config.device_id,
                )

                if result.isError():
                    health.on_read_error()
                    data_logger.append_error(str(result))
                    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] Modbus error: {result}")
                else:
                    turbidity = result.registers[0] / 10.0
                    temperature = result.registers[1] / 10.0
                    health.on_read_success()
                    data_logger.append(turbidity, temperature)
                    print(
                        f"[{dt.datetime.now().strftime('%H:%M:%S')}]"
                        f"  Turbidity: {turbidity:7.1f} NTU"
                        f"  |  Temperature: {temperature:5.1f} °C"
                    )

            except Exception as exc:
                health.on_read_error()
                uptime = health.on_disconnect()
                log_path = usb_logger.log_disconnect(reason=str(exc), port_hint=selected_port)
                csv_reporter.append_disconnect(
                    port=selected_port,
                    reason=str(exc),
                    uptime_seconds=uptime,
                    metrics=health,
                )
                data_logger.append_error(str(exc))
                print(f"I/O error ({exc}). Reconnecting... [kernel log: {log_path}]")
                if client:
                    client.close()
                client = None
                wait = backoff.register_failure()
                time.sleep(wait)
                continue

            time.sleep(config.poll_interval_seconds)

    except KeyboardInterrupt:
        print("\nStopped by user (Ctrl-C).")

    finally:
        # ── Orderly shutdown ──────────────────────────────────────────────
        if client:
            if health.connected_since is not None:
                health.on_disconnect()
            client.close()

        data_logger.close()
        csv_reporter.append_session_summary(health)

        print("\nGenerating plots...")
        plot_path = plotter.generate_from_csv(data_logger.path, session_start)

        elapsed = time.monotonic() - start_monotonic
        print(
            "\n── Session Summary ──────────────────────────────\n"
            f"  duration_s       : {elapsed:.1f}\n"
            f"  total_reads      : {health.total_reads}\n"
            f"  read_errors      : {health.read_errors}\n"
            f"  disconnect_count : {health.disconnect_count}\n"
            f"  mean_uptime_s    : {health.mean_uptime_seconds:.2f}\n"
            f"  data_log         : {data_logger.path}\n"
            f"  plot             : {plot_path}\n"
            f"  health_csv       : {logs_dir() / 'health_metrics.csv'}\n"
            "─────────────────────────────────────────────────"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Continuous turbidity data acquisition from RS485 sensor.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=None,
        metavar="SECONDS",
        help="How long to run in seconds. Omit for indefinite.",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Poll interval in seconds (0.5 Hz = 2.0 s).",
    )
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be a positive number of seconds.")

    run(duration=args.duration, poll_interval=args.interval)


if __name__ == "__main__":
    main()
