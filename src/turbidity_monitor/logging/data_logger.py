import csv
import datetime as dt
from pathlib import Path


class SensorDataLogger:
    """Logs turbidity and temperature readings to a per-session CSV file.

    A new file is created for each session using the session start timestamp.
    Every row is flushed immediately so data is preserved on abrupt shutdown.

    CSV columns
    -----------
    timestamp       ISO-8601 with millisecond precision (system clock)
    turbidity_ntu   Turbidity reading in NTU, one decimal place
    temperature_c   Temperature reading in °C, one decimal place
    status          "ok" for valid readings; "error: <detail>" for failures
    """

    COLUMNS = ["timestamp", "turbidity_ntu", "temperature_c", "status"]

    def __init__(self, output_dir: Path, session_start: dt.datetime) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"turbidity_log_{session_start:%Y%m%d_%H%M%S}.csv"
        self._path = output_dir / filename
        self._handle = self._path.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._handle)
        self._writer.writerow(self.COLUMNS)
        self._handle.flush()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, turbidity: float, temperature: float, status: str = "ok") -> None:
        """Write one sensor reading and flush immediately."""
        self._writer.writerow(
            [
                dt.datetime.now().isoformat(timespec="milliseconds"),
                round(turbidity, 1),
                round(temperature, 1),
                status,
            ]
        )
        self._handle.flush()

    def append_error(self, reason: str) -> None:
        """Write an error row (empty sensor fields) and flush immediately."""
        self._writer.writerow(
            [
                dt.datetime.now().isoformat(timespec="milliseconds"),
                "",
                "",
                f"error: {reason}",
            ]
        )
        self._handle.flush()

    def close(self) -> None:
        """Flush and close the underlying file handle."""
        if not self._handle.closed:
            self._handle.flush()
            self._handle.close()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Absolute path to the CSV file for this session."""
        return self._path
