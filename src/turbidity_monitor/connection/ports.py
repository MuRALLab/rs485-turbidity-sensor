import glob
from pathlib import Path

from turbidity_monitor.config import PREFERRED_PORT


def resolve_port() -> str | None:
    """Resolve a USB-RS485 adapter path, preferring the known FTDI by-id path."""
    if Path(PREFERRED_PORT).exists():
        return PREFERRED_PORT

    by_id = sorted(glob.glob("/dev/serial/by-id/*"))
    if by_id:
        return by_id[0]

    usb = sorted(glob.glob("/dev/ttyUSB*"))
    return usb[0] if usb else None
