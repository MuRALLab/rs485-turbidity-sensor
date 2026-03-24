import time


class ReconnectBackoff:
    def __init__(
        self,
        initial_seconds: float,
        max_seconds: float,
        factor: float,
        rescan_interval_seconds: float,
    ):
        self.initial_seconds = max(initial_seconds, 0.1)
        self.max_seconds = max(max_seconds, self.initial_seconds)
        self.factor = max(factor, 1.0)
        self.rescan_interval_seconds = max(rescan_interval_seconds, 0.1)
        self.current_seconds = self.initial_seconds
        self.last_scan_at = 0.0

    def should_rescan(self) -> bool:
        now = time.monotonic()
        if (now - self.last_scan_at) >= self.rescan_interval_seconds:
            self.last_scan_at = now
            return True
        return False

    def register_failure(self) -> float:
        wait = self.current_seconds
        self.current_seconds = min(self.current_seconds * self.factor, self.max_seconds)
        return wait

    def reset(self) -> None:
        self.current_seconds = self.initial_seconds
