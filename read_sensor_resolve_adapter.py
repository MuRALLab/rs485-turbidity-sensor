import argparse
import time

from pymodbus.client import ModbusSerialClient

from turbidity_monitor.config import MonitorConfig, logs_dir, plots_dir
from turbidity_monitor.connection.backoff import ReconnectBackoff
from turbidity_monitor.connection.ports import resolve_port
from turbidity_monitor.connection.usb_event_logger import KernelUsbEventLogger
from turbidity_monitor.health.csv_reporter import HealthCsvReporter
from turbidity_monitor.health.metrics import HealthMetrics
from turbidity_monitor.visualization.live_plot import LivePlotter

def make_client(port: str, config: MonitorConfig) -> ModbusSerialClient:
    return ModbusSerialClient(
        port=port,
        baudrate=config.baudrate,
        parity=config.parity,
        stopbits=config.stopbits,
        bytesize=config.bytesize,
        timeout=config.timeout,
    )

def read_sensor(duration: int | None) -> None:
    config = MonitorConfig()
    client = None
    selected_port = None
    start_time = time.monotonic()

    usb_logger = KernelUsbEventLogger(logs_dir())
    backoff = ReconnectBackoff(
        initial_seconds=config.backoff_initial_seconds,
        max_seconds=config.backoff_max_seconds,
        factor=config.backoff_factor,
        rescan_interval_seconds=config.rescan_interval_seconds,
    )
    health = HealthMetrics()
    csv_reporter = HealthCsvReporter(logs_dir() / "health_metrics.csv")
    plotter = LivePlotter(plots_dir())

    print("Reading data (Press Ctrl+C to stop)...")
    if duration:
        print(f"Running for {duration} seconds.")

    try:
        while True:
            # Check if duration has been reached
            if duration and (time.monotonic() - start_time) > duration:
                print(f"Reached time limit of {duration} seconds. Exiting.")
                break

            # Handle connection/reconnection
            if client is None or not client.connected:
                if selected_port is None or backoff.should_rescan():
                    selected_port = resolve_port()

                if not selected_port:
                    wait_seconds = backoff.register_failure()
                    print(f"No USB-RS485 port found. Re-scan in {wait_seconds:0.1f}s...")
                    time.sleep(wait_seconds)
                    continue

                client = make_client(selected_port, config)
                if not client.connect():
                    wait_seconds = backoff.register_failure()
                    print(f"Failed to open {selected_port}. Retrying in {wait_seconds:0.1f}s...")
                    client = None
                    time.sleep(wait_seconds)
                    continue
                backoff.reset()
                health.on_connect()
                print(f"Connected on {selected_port}")

            try:
                # Read 2 registers starting at 0x0000
                result = client.read_holding_registers(
                    address=config.register_address,
                    count=config.register_count,
                    device_id=config.device_id,
                )

                if not result.isError():
                    # Turbidity is register 0, Temperature is register 1
                    turbidity = result.registers[0] / 10.0
                    temperature = result.registers[1] / 10.0
                    health.on_read_success()
                    plotter.add_reading(turbidity=turbidity, temperature=temperature)
                    print(f"Turbidity: {turbidity:0.1f} NTU | Temperature: {temperature:0.1f} °C")
                else:
                    health.on_read_error()
                    print(f"Modbus Error: {result}")
            except Exception as exc:
                health.on_read_error()
                uptime_seconds = health.on_disconnect()
                plot_path = plotter.save_snapshot("disconnect")
                log_path = usb_logger.log_disconnect(reason=str(exc), port_hint=selected_port)
                csv_reporter.append_disconnect(
                    port=selected_port,
                    reason=str(exc),
                    uptime_seconds=uptime_seconds,
                    metrics=health,
                )

                print(f"Serial I/O error ({exc}). Reconnecting...")
                print(f"Disconnect snapshot: {plot_path}")
                print(f"Kernel USB event log: {log_path}")
                if client:
                    client.close()
                client = None
                wait_seconds = backoff.register_failure()
                time.sleep(wait_seconds)
                continue

            time.sleep(config.poll_interval_seconds)

    except KeyboardInterrupt:
        print("\nStopped reading by user.")
    finally:
        if client and health.connected_since is not None:
            health.on_disconnect()
        if client:
            client.close()

        final_plot = plotter.save_snapshot("exit")
        csv_reporter.append_session_summary(health)
        plotter.close()

        print("Session summary:")
        print(f"- disconnect_count: {health.disconnect_count}")
        print(f"- mean_uptime_seconds: {health.mean_uptime_seconds:0.2f}")
        print(f"- total_reads: {health.total_reads}")
        print(f"- read_errors: {health.read_errors}")
        print(f"- health_csv: {logs_dir() / 'health_metrics.csv'}")
        print(f"- final_plot: {final_plot}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read data from Turbidity Transmitter.")
    parser.add_argument(
        "--duration",
        "-d",
        type=int, 
        help="Time in seconds to run the script. If not set, runs indefinitely."
    )
    
    args = parser.parse_args()
    read_sensor(args.duration)