#!/usr/bin/env python3
"""sensor-latency Python backend.

Performs N Modbus reads back-to-back and reports per-read latency statistics.
Called by the sensor-latency bash script.

Usage
-----
    python latency.py <samples>

Exit codes
----------
0  at least one successful read
1  device/connection/all-reads-failed
"""

import sys
import time

from pymodbus.client import ModbusSerialClient

from turbidity_monitor.config import MonitorConfig
from turbidity_monitor.connection.ports import resolve_port


def main() -> int:
    if len(sys.argv) != 2:
        print("USAGE: latency.py <samples>")
        return 1

    try:
        samples = int(sys.argv[1])
    except ValueError:
        print("ERROR: samples must be an integer")
        return 1

    if samples < 1 or samples > 1000:
        print("ERROR: samples must be between 1 and 1000")
        return 1

    config = MonitorConfig()

    port = resolve_port()
    if port is None:
        print("ERROR: no_serial_device")
        return 1

    print(f"PORT: {port}")
    print(f"SAMPLES: {samples}")

    client = ModbusSerialClient(
        port=port,
        baudrate=config.baudrate,
        parity=config.parity,
        stopbits=config.stopbits,
        bytesize=config.bytesize,
        timeout=config.timeout,
    )

    if not client.connect():
        print("ERROR: connect_failed")
        return 1

    latencies_ms: list[float] = []
    errors = 0

    try:
        for n in range(1, samples + 1):
            t_start = time.perf_counter()
            try:
                result = client.read_holding_registers(
                    address=config.register_address,
                    count=config.register_count,
                    device_id=config.device_id,
                )
                elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                if result.isError():
                    errors += 1
                    print(f"SAMPLE {n:>4}: ERROR  modbus_error")
                else:
                    latencies_ms.append(elapsed_ms)
                    turbidity   = result.registers[0] / 10.0
                    temperature = result.registers[1] / 10.0
                    print(
                        f"SAMPLE {n:>4}: OK  "
                        f"{elapsed_ms:7.1f} ms  "
                        f"turbidity={turbidity:.1f} NTU  "
                        f"temp={temperature:.1f} °C"
                    )
            except Exception as exc:
                errors += 1
                print(f"SAMPLE {n:>4}: ERROR  {exc}")
    finally:
        client.close()

    if not latencies_ms:
        print("STATS: no_successful_reads")
        return 1

    avg_ms = sum(latencies_ms) / len(latencies_ms)
    min_ms = min(latencies_ms)
    max_ms = max(latencies_ms)
    success = len(latencies_ms)

    print(f"STATS_SAMPLES_OK: {success}")
    print(f"STATS_SAMPLES_ERR: {errors}")
    print(f"STATS_AVG_MS: {avg_ms:.2f}")
    print(f"STATS_MIN_MS: {min_ms:.2f}")
    print(f"STATS_MAX_MS: {max_ms:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
