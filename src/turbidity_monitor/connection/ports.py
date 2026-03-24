import glob


def resolve_port() -> str | None:
    """Resolve a USB-RS485 adapter path, preferring stable by-id paths."""
    by_id = sorted(glob.glob("/dev/serial/by-id/*"))
    if by_id:
        return by_id[0]

    usb = sorted(glob.glob("/dev/ttyUSB*"))
    return usb[0] if usb else None
