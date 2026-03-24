import datetime as dt
import subprocess
from pathlib import Path


class KernelUsbEventLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _kernel_usb_lines(self, max_lines: int = 180) -> list[str]:
        commands = [
            ["journalctl", "-k", "-n", str(max_lines), "--no-pager"],
            ["dmesg", "--color=never"],
        ]
        for command in commands:
            try:
                proc = subprocess.run(command, check=False, capture_output=True, text=True)
                if proc.returncode != 0 or not proc.stdout:
                    continue
                lines = proc.stdout.splitlines()
                return [
                    line
                    for line in lines
                    if any(
                        token in line.lower()
                        for token in (
                            "usb",
                            "ttyusb",
                            "ftdi",
                            "disconnect",
                            "reset",
                            "error",
                            "emi",
                            "over-current",
                        )
                    )
                ][-80:]
            except FileNotFoundError:
                continue
        return ["Kernel USB log command unavailable on this system."]

    def log_disconnect(self, reason: str, port_hint: str | None) -> Path:
        now = dt.datetime.now()
        log_path = self.output_dir / f"usb_events_{now:%Y%m%d}.md"
        lines = self._kernel_usb_lines()
        section = [
            f"## {now:%Y-%m-%d %H:%M:%S}",
            "- event: disconnect_detected",
            f"- port_hint: {port_hint or 'unknown'}",
            f"- reason: {reason}",
            "- recent_kernel_usb_events:",
            "```text",
            *lines,
            "```",
            "",
        ]
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(section))
        return log_path
