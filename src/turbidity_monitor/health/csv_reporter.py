import csv
import datetime as dt
from pathlib import Path

from turbidity_monitor.health.metrics import HealthMetrics


class HealthCsvReporter:
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if self.output_file.exists() and self.output_file.stat().st_size > 0:
            return
        with self.output_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "timestamp",
                    "event",
                    "port",
                    "reason",
                    "disconnect_count",
                    "uptime_seconds",
                    "mean_uptime_seconds",
                    "total_reads",
                    "read_errors",
                ]
            )

    def append_disconnect(
        self,
        port: str | None,
        reason: str,
        uptime_seconds: float,
        metrics: HealthMetrics,
    ) -> None:
        with self.output_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    dt.datetime.now().isoformat(timespec="seconds"),
                    "disconnect",
                    port or "unknown",
                    reason,
                    metrics.disconnect_count,
                    round(uptime_seconds, 3),
                    round(metrics.mean_uptime_seconds, 3),
                    metrics.total_reads,
                    metrics.read_errors,
                ]
            )

    def append_session_summary(self, metrics: HealthMetrics) -> None:
        with self.output_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    dt.datetime.now().isoformat(timespec="seconds"),
                    "session_summary",
                    "-",
                    "exit",
                    metrics.disconnect_count,
                    round(metrics.mean_uptime_seconds, 3),
                    round(metrics.mean_uptime_seconds, 3),
                    metrics.total_reads,
                    metrics.read_errors,
                ]
            )
