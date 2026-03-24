import time
from dataclasses import dataclass, field


@dataclass
class HealthMetrics:
    disconnect_count: int = 0
    total_reads: int = 0
    read_errors: int = 0
    connected_since: float | None = None
    uptimes: list[float] = field(default_factory=list)

    def on_connect(self) -> None:
        self.connected_since = time.monotonic()

    def on_disconnect(self) -> float:
        self.disconnect_count += 1
        if self.connected_since is None:
            return 0.0
        uptime = max(time.monotonic() - self.connected_since, 0.0)
        self.uptimes.append(uptime)
        self.connected_since = None
        return uptime

    def on_read_success(self) -> None:
        self.total_reads += 1

    def on_read_error(self) -> None:
        self.read_errors += 1

    @property
    def mean_uptime_seconds(self) -> float:
        if not self.uptimes:
            return 0.0
        return sum(self.uptimes) / len(self.uptimes)
