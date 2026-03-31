#!/usr/bin/env python3
"""sensor-probe Python backend.

Attempts a single Modbus register read and prints a structured result.
Called by the sensor-probe bash script.

Exit codes
----------
0  read succeeded
1  device not found, permission error, or Modbus failure
"""

import sys

from pymodbus.client import ModbusSerialClient

# src/ is added to PYTHONPATH by _common.sh before this script is invoked.
from turbidity_monitor.config import MonitorConfig
from turbidity_monitor.connection.ports import resolve_port


def main() -> int:
    config = MonitorConfig()

    port = resolve_port()
    if port is None:
        print("ERROR: no_serial_device")
        return 1

    print(f"PORT: {port}")

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

    try:
        result = client.read_holding_registers(
            address=config.register_address,
            count=config.register_count,
            device_id=config.device_id,
        )
    except Exception as exc:
        print(f"ERROR: exception: {exc}")
        return 1
    finally:
        client.close()

    if result.isError():
        print(f"ERROR: modbus_error: {result}")
        return 1

    turbidity = result.registers[0] / 10.0
    temperature = result.registers[1] / 10.0
    print(f"TURBIDITY: {turbidity:.1f}")
    print(f"TEMPERATURE: {temperature:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
