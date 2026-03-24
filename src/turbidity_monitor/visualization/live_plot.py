import datetime as dt
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


class LivePlotter:
    def __init__(self, output_dir: Path, max_points: int = 240):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamps = deque(maxlen=max_points)
        self.turbidity_values = deque(maxlen=max_points)
        self.temperature_values = deque(maxlen=max_points)

        plt.style.use("seaborn-v0_8-whitegrid")
        self.figure, (self.ax1, self.ax2) = plt.subplots(
            2,
            1,
            figsize=(11, 7),
            sharex=True,
            constrained_layout=True,
        )

        manager = self.figure.canvas.manager
        if manager is not None and hasattr(manager, "set_window_title"):
            manager.set_window_title("Turbidity Transmitter Live Monitor")

        self.figure.suptitle("RS485 Turbidity and Temperature", fontsize=14, fontweight="bold")

        (self.turbidity_line,) = self.ax1.plot([], [], color="#0072B2", linewidth=2.2, label="Turbidity")
        self.ax1.set_ylabel("NTU")
        self.ax1.legend(loc="upper left")
        self.ax1.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))

        (self.temperature_line,) = self.ax2.plot([], [], color="#D55E00", linewidth=2.2, label="Temperature")
        self.ax2.set_ylabel("°C")
        self.ax2.set_xlabel("Samples")
        self.ax2.legend(loc="upper left")
        self.ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=6))

        plt.ion()
        plt.show(block=False)

    def add_reading(self, turbidity: float, temperature: float) -> None:
        self.timestamps.append(dt.datetime.now())
        self.turbidity_values.append(turbidity)
        self.temperature_values.append(temperature)
        self._refresh()

    def _refresh(self) -> None:
        if not self.timestamps:
            return
        x_values = list(range(len(self.timestamps)))

        self.turbidity_line.set_data(x_values, list(self.turbidity_values))
        self.temperature_line.set_data(x_values, list(self.temperature_values))

        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.ax2.set_xlim(0, max(len(x_values) - 1, 1))

        start_ts = self.timestamps[0].strftime("%H:%M:%S")
        end_ts = self.timestamps[-1].strftime("%H:%M:%S")
        self.ax2.set_xlabel(f"Samples ({start_ts} to {end_ts})")

        self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()
        plt.pause(0.001)

    def save_snapshot(self, reason: str) -> Path:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = self.output_dir / f"transmitter_plot_{reason}_{timestamp}.png"
        self.figure.savefig(plot_path, dpi=180)
        return plot_path

    def close(self) -> None:
        plt.ioff()
        plt.close(self.figure)
