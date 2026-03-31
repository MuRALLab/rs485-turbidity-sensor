from dataclasses import dataclass
from pathlib import Path

# Stable persistent path for the FTDI USB-RS485 adapter (prefer over /dev/ttyUSBx).
PREFERRED_PORT = "/dev/serial/by-id/usb-FTDI_USB_Serial_Converter_FTB6SPL3-if00-port0"


@dataclass(frozen=True)
class MonitorConfig:
    baudrate: int = 4800
    parity: str = "N"
    stopbits: int = 1
    bytesize: int = 8
    timeout: float = 2.0
    device_id: int = 1
    register_address: int = 0x0000
    register_count: int = 2
    poll_interval_seconds: float = 2.0
    backoff_initial_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    backoff_factor: float = 2.0
    rescan_interval_seconds: float = 5.0


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def logs_dir() -> Path:
    path = repo_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def plots_dir() -> Path:
    path = repo_root() / "plots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_log_dir() -> Path:
    path = repo_root() / "data_log"
    path.mkdir(parents=True, exist_ok=True)
    return path
