#!/usr/bin/env python3
"""sensor-raw Python backend.

Performs a raw Modbus holding-register read with caller-supplied parameters
and prints results. Called by the sensor-raw bash script.

Usage
-----
    python raw_read.py <register_address> <register_count> <slave_id>

All arguments are integers.  register_address may be hex (0x..) or decimal.

Exit codes
----------
0  read succeeded
1  any failure
"""

import sys

from pymodbus.client import ModbusSerialClient

from turbidity_monitor.config import MonitorConfig
from turbidity_monitor.connection.ports import resolve_port


def main() -> int:
    if len(sys.argv) != 4:
        print("USAGE: raw_read.py <register_address> <register_count> <slave_id>")
        return 1

    try:
        reg_address = int(sys.argv[1], 0)   # supports 0x.. notation
        reg_count   = int(sys.argv[2], 0)
        slave_id    = int(sys.argv[3], 0)
    except ValueError as exc:
        print(f"ERROR: invalid_argument: {exc}")
        return 1

    if reg_count < 1 or reg_count > 125:
        print("ERROR: register_count must be 1-125")
        return 1

    config = MonitorConfig()

    port = resolve_port()
    if port is None:
        print("ERROR: no_serial_device")
        return 1

    print(f"PORT: {port}")
    print(f"REG_ADDRESS: {reg_address} (0x{reg_address:04X})")
    print(f"REG_COUNT: {reg_count}")
    print(f"SLAVE_ID: {slave_id}")

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
            address=reg_address,
            count=reg_count,
            device_id=slave_id,
        )
    except Exception as exc:
        print(f"ERROR: exception: {exc}")
        return 1
    finally:
        client.close()

    if result.isError():
        print(f"ERROR: modbus_error: {result}")
        return 1

    print(f"REGISTER_COUNT: {len(result.registers)}")
    for i, val in enumerate(result.registers):
        print(f"REG[{reg_address + i}] DEC={val}  HEX=0x{val:04X}  SCALED={val / 10.0:.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
