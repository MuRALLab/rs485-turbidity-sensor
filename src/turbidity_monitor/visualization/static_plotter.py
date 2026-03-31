"""Headless-safe plot generation using the non-interactive Agg backend.

This module must NOT be imported in the same process as live_plot.py, as that
module uses the interactive backend.  main.py (headless entry point) imports
only this plotter, never LivePlotter.
"""

import csv
import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # must be set before importing pyplot

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402


class StaticPlotter:
    """Renders turbidity + temperature plots from a session CSV and saves to disk."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_from_csv(self, csv_path: Path, session_start: dt.datetime) -> Path:
        """Read a SensorDataLogger CSV and write a two-panel PNG plot.

        Parameters
        ----------
        csv_path:
            Path to the session CSV produced by SensorDataLogger.
        session_start:
            Session start datetime, used to derive the output filename.

        Returns
        -------
        Path to the saved PNG file.
        """
        timestamps, turbidity_values, temperature_values = self._load_csv(csv_path)

        plt.style.use("seaborn-v0_8-whitegrid")
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(11, 7), sharex=True, constrained_layout=True
        )
        fig.suptitle(
            "RS485 Turbidity and Temperature — "
            + session_start.strftime("%Y-%m-%d %H:%M:%S"),
            fontsize=13,
            fontweight="bold",
        )

        if timestamps:
            ax1.plot(
                timestamps, turbidity_values, color="#0072B2", linewidth=1.8, label="Turbidity"
            )
            ax2.plot(
                timestamps, temperature_values, color="#D55E00", linewidth=1.8, label="Temperature"
            )
            ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            fig.autofmt_xdate(rotation=30)
        else:
            for ax in (ax1, ax2):
                ax.text(
                    0.5, 0.5, "No data collected", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, color="grey"
                )

        ax1.set_ylabel("Turbidity (NTU)")
        ax1.legend(loc="upper left")
        ax1.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))

        ax2.set_ylabel("Temperature (°C)")
        ax2.set_xlabel("Time")
        ax2.legend(loc="upper left")
        ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))

        plot_path = self.output_dir / f"turbidity_plot_{session_start:%Y%m%d_%H%M%S}.png"
        fig.savefig(plot_path, dpi=180)
        plt.close(fig)
        return plot_path

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_csv(
        csv_path: Path,
    ) -> tuple[list[dt.datetime], list[float], list[float]]:
        """Parse valid 'ok' rows from a SensorDataLogger CSV."""
        timestamps: list[dt.datetime] = []
        turbidity_values: list[float] = []
        temperature_values: list[float] = []

        if not csv_path.exists():
            return timestamps, turbidity_values, temperature_values

        with csv_path.open("r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("status") != "ok":
                    continue
                try:
                    timestamps.append(dt.datetime.fromisoformat(row["timestamp"]))
                    turbidity_values.append(float(row["turbidity_ntu"]))
                    temperature_values.append(float(row["temperature_c"]))
                except (ValueError, KeyError):
                    continue

        return timestamps, turbidity_values, temperature_values
