#!/usr/bin/env python3
import glob
import os
import matplotlib.pyplot as plt
import mesa_reader as mr
import numpy as np
from matplotlib.animation import FuncAnimation

def get_phase_info_from_mesa(md):
    """Get evolutionary phase information using MESA's phase_of_evolution."""

    # Check if phase_of_evolution exists in the data
    if hasattr(md, "phase_of_evolution"):
        phase_codes = md.phase_of_evolution
    else:
        print("Warning: phase_of_evolution not found in history file.")
        print("Make sure to add 'phase_of_evolution' to your history_columns.list")
        # Fallback to unknown phase
        n_models = len(md.model_number)
        phase_codes = np.full(n_models, -1)

    phases = []
    phase_colors = []

    for code in phase_codes:
        phase_name, color = get_mesa_phase_info(int(code))
        phases.append(phase_name)
        phase_colors.append(color)

    return phases, phase_colors


def get_mesa_phase_info(phase_code):
    """
    Map MESA's phase_of_evolution integer codes to phase names and colors.
    Based on MESA's exact internal phase definitions from star_data_def.inc
    """
    # MESA phase codes (exact from source code)
    phase_map = {
        -1: ("Relax", "#C0C0C0"),  # Silver - Relaxation phase
        1: ("Starting", "#E6E6FA"),  # Lavender - Starting phase
        2: ("Pre-MS", "#FF69B4"),  # Hot pink - Pre-main sequence
        3: ("ZAMS", "#00FF00"),  # Bright green - Zero-age main sequence
        4: ("IAMS", "#0000FF"),  # Blue - Intermediate-age main sequence
        5: ("TAMS", "#FF8C00"),  # Dark orange - Terminal-age main sequence
        6: ("He-Burn", "#8A2BE2"),  # Blue violet - Helium burning (general)
        7: ("ZACHeB", "#9932CC"),  # Dark orchid - Zero-age core helium burning
        8: ("TACHeB", "#BA55D3"),  # Medium orchid - Terminal-age core helium burning
        9: ("TP-AGB", "#8B0000"),  # Dark red - Thermally pulsing AGB
        10: ("C-Burn", "#FF4500"),  # Orange red - Carbon burning
        11: ("Ne-Burn", "#FF6347"),  # Tomato - Neon burning
        12: ("O-Burn", "#FF8C00"),  # Dark orange - Oxygen burning
        13: ("Si-Burn", "#FFA500"),  # Orange - Silicon burning
        14: ("WDCS", "#708090"),  # Slate gray - White dwarf cooling sequence
    }

    return phase_map.get(phase_code, ("Unknown", "#808080"))



def read_header_columns(history_file):
    """Read column headers from history file."""
    header_line = None
    with open(history_file, "r") as fp:
        for line in fp:
            if "model_number" in line:
                header_line = line.strip()
                break

    if header_line is None:
        print("Warning: Could not find header line with 'model_number'")
        return [], []

    # Split the header line on whitespace
    all_cols = header_line.split()

    # Find the index of Flux_bol
    try:
        flux_index = all_cols.index("Flux_bol")
        filter_columns = all_cols[flux_index + 1 :]
    except ValueError:
        print("Warning: Could not find 'Flux_bol' column in header")
        filter_columns = []

    return all_cols, filter_columns


def setup_hr_diagram_params(md, filter_columns):
    """Set up parameters for HR diagram based on available filters."""
    if "Gbp" in filter_columns and "Grp" in filter_columns and "G" in filter_columns:
        hr_color = md.Gbp - md.Grp
        hr_mag = md.G
        hr_xlabel = "Gbp - Grp"
        hr_ylabel = "G"
        color_index = hr_color
    else:
        if len(filter_columns) >= 2:
            # Use the first two filters
            f1 = filter_columns[0]
            f2 = filter_columns[1]

            # Retrieve the data using getattr or data method
            try:
                col1 = getattr(md, f1)
                col2 = getattr(md, f2)
            except AttributeError:
                col1 = md.data(f1)
                col2 = md.data(f2)

            hr_color = col1 - col2
            hr_mag = col1
            hr_xlabel = f"{f1} - {f2}"
            hr_ylabel = f1
            color_index = hr_color
        else:
            # Default values if not enough filters
            print("Warning: Not enough filter columns to construct color index")
            hr_color = np.zeros_like(md.Teff)
            hr_mag = np.zeros_like(md.Teff)
            hr_xlabel = "Color Index"
            hr_ylabel = "Magnitude"
            color_index = hr_color

    return hr_color, hr_mag, hr_xlabel, hr_ylabel, color_index


class HistoryChecker:
    def __init__(self, history_file="../LOGS/history.data", refresh_interval=1):
        """
        Initialize the History checker with auto-refresh capability and MESA phase color coding.

        Args:
            history_file: Path to the MESA history.data file
            refresh_interval: Time in seconds between refresh attempts
        """
        self.history_file = history_file
        self.refresh_interval = refresh_interval
        self.last_modified = None

        # Create the figure and axes
        self.fig, self.axes = plt.subplots(
            2, 2, figsize=(14, 18), gridspec_kw={"hspace": 0.01, "wspace": 0.01}
        )

        self.update_flag = 0
        # Initial setup
        self.filter_columns = []
        self.phases = []
        self.phase_colors = []
        self.update_data()
        self.setup_plot()

    def setup_plot(self):
        """Set up the plot with formatting and labels (titles removed, labels enlarged, top x-axis added)."""
        # Top-left plot: HR Diagram (Color vs. Magnitude)
        self.axes[0, 0].set_xlabel(self.hr_xlabel, fontsize=16)
        self.axes[0, 0].set_ylabel(self.hr_ylabel, fontsize=16)
        self.axes[0, 0].invert_yaxis()
        self.axes[0, 0].xaxis.set_ticks_position("top")
        self.axes[0, 0].xaxis.set_label_position("top")
        self.axes[0, 0].grid(True, alpha=0.3)

        # Top-right plot: Teff vs. Log_L
        self.axes[0, 1].set_xlabel("Teff (K)", fontsize=16)
        self.axes[0, 1].set_ylabel("Log L/L☉", fontsize=16)
        self.axes[0, 1].invert_xaxis()
        self.axes[0, 1].yaxis.set_label_position("right")
        self.axes[0, 1].yaxis.tick_right()
        self.axes[0, 1].xaxis.set_ticks_position("top")
        self.axes[0, 1].xaxis.set_label_position("top")
        self.axes[0, 1].grid(True, alpha=0.3)

        # Bottom-left plot: Age vs. Color Index
        self.axes[1, 0].set_xlabel("Age (years)", fontsize=16)
        self.axes[1, 0].set_ylabel(f"Color ({self.hr_xlabel})", fontsize=16)
        self.axes[1, 0].grid(True, alpha=0.3)

        # Bottom-right plot: Age vs. All Filter Magnitudes
        self.axes[1, 1].set_xlabel("Age (years)", fontsize=16)
        self.axes[1, 1].set_ylabel("Magnitude", fontsize=16)
        self.axes[1, 1].invert_yaxis()
        self.axes[1, 1].yaxis.set_label_position("right")
        self.axes[1, 1].yaxis.tick_right()
        self.axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # Adjust if needed for legend spacing

    def check_for_changes(self):
        """Check if history file has been modified since last check."""
        if not os.path.exists(self.history_file):
            print(f"Warning: History file {self.history_file} not found")
            return False

        current_mtime = os.path.getmtime(self.history_file)

        if self.last_modified is None or current_mtime > self.last_modified:
            self.last_modified = current_mtime
            return True

        return False

    def update_data(self):
        """Read data from history file and extract relevant columns."""
        if not os.path.exists(self.history_file):
            print(f"Warning: History file {self.history_file} not found")
            return

        try:
            # Read the MESA data
            self.md = mr.MesaData(self.history_file)

            # Basic stellar parameters
            self.Teff = self.md.Teff
            self.Log_L = self.md.log_L
            self.Log_g = self.md.log_g
            self.Log_R = self.md.log_R
            self.Star_Age = self.md.star_age
            self.Mag_bol = self.md.Mag_bol
            self.Flux_bol = np.log10(self.md.Flux_bol)

            # Read header columns using imported function
            self.all_cols, self.filter_columns = read_header_columns(self.history_file)

            # Set up HR diagram parameters using imported function
            (
                self.hr_color,
                self.hr_mag,
                self.hr_xlabel,
                self.hr_ylabel,
                self.color_index,
            ) = setup_hr_diagram_params(self.md, self.filter_columns)

            # Get evolutionary phase information using MESA's built-in phases
            self.phases, self.phase_colors = get_phase_info_from_mesa(self.md)

        except Exception as e:
            print(f"Error reading history data: {e}")

    def create_phase_legend(self):
        """Create legend for evolutionary phases."""
        unique_phases = []
        unique_colors = []
        for phase, color in zip(self.phases, self.phase_colors):
            if phase not in unique_phases:
                unique_phases.append(phase)
                unique_colors.append(color)

        legend_elements = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=color,
                markersize=8,
                label=phase,
                markeredgecolor="none",
            )
            for phase, color in zip(unique_phases, unique_colors)
        ]

        return legend_elements

    def update_plot(self, frame):
        """Update the plot with new data if the file has changed."""
        if not self.check_for_changes():
            return

        if self.update_flag < 5:
            print(f"Detected changes in {self.history_file}, updating plot...")
            self.update_flag = self.update_flag + 1
        elif self.update_flag == 5:
            print(
                f"... MESA is clearly running so no more updates about: {self.history_file}"
            )
            self.update_flag = self.update_flag + 1

        # Update data
        self.update_data()

        # Clear all axes
        for ax in self.axes.flatten():
            ax.clear()

        # Reset plot formatting
        self.setup_plot()

        # Top-left plot: HR Diagram with phase colors
        if len(self.phases) > 0:
            self.axes[0, 0].scatter(
                self.hr_color,
                self.hr_mag,
                c=self.phase_colors,
                s=20,
                alpha=0.7,
                edgecolors="none",
            )
        else:
            self.axes[0, 0].plot(self.hr_color, self.hr_mag, "go")

        # Top-right plot: Teff vs. Log_L with phase colors
        if len(self.phases) > 0:
            self.axes[0, 1].scatter(
                self.Teff,
                self.Log_L,
                c=self.phase_colors,
                s=20,
                alpha=0.7,
                edgecolors="none",
            )
        else:
            self.axes[0, 1].plot(self.Teff, self.Log_L, "go")

        # Bottom-left plot: Age vs. Color Index with phase colors
        if len(self.phases) > 0:
            self.axes[1, 0].scatter(
                self.Star_Age,
                self.color_index,
                c=self.phase_colors,
                s=20,
                alpha=0.7,
                edgecolors="none",
            )
        else:
            self.axes[1, 0].plot(self.Star_Age, self.color_index, "kx")

        # Bottom-right plot: Age vs. All Filter Magnitudes
        for filt in self.filter_columns:
            # Retrieve filter magnitude data
            try:
                col_data = getattr(self.md, filt)
            except AttributeError:
                try:
                    col_data = self.md.data(filt)
                except Exception:
                    print(f"Warning: Could not retrieve data for filter {filt}")
                    continue

            self.axes[1, 1].plot(
                self.Star_Age,
                col_data,
                marker="o",
                linestyle="-",
                label=filt,
                markersize=3,
                alpha=0.8,
            )

        # Add legend to filter plot
        self.axes[1, 1].legend()

        # Add evolutionary phase legend at the top of the figure
        if len(self.phases) > 0:
            legend_elements = self.create_phase_legend()
            # Calculate number of columns for max 2 rows
            n_phases = len(legend_elements)
            ncol = max(1, (n_phases + 1) // 2)  # Ceiling division to get max 2 rows

            self.fig.legend(
                handles=legend_elements,
                loc="upper center",
                bbox_to_anchor=(0.5, 0.54),
                ncol=ncol,
                title_fontsize=16,
                fontsize=16,
                frameon=True,
                fancybox=True,
                shadow=True,
            )

        # Adjust layout to make room for top legend
        plt.tight_layout()
        plt.subplots_adjust(top=0.92)

        # Update the figure
        self.fig.canvas.draw_idle()

    def run(self):
        """Start the auto-refreshing display."""
        print(f"Monitoring history file: {self.history_file}")
        print(f"Refresh interval: {self.refresh_interval} seconds")
        print("Using MESA's built-in phase_of_evolution for color coding")
        print("Make sure 'phase_of_evolution' is in your history_columns.list")
        print("\nMESA Phase Definitions:")
        print("  -1: Relax, 1: Starting, 2: Pre-MS, 3: ZAMS, 4: IAMS, 5: TAMS")
        print("  6: He-Burn, 7: ZACHeB, 8: TACHeB, 9: TP-AGB")
        print("  10: C-Burn, 11: Ne-Burn, 12: O-Burn, 13: Si-Burn, 14: WDCS")

        # Initial plot
        self.update_plot(0)

        # Set up animation
        self.animation = FuncAnimation(
            self.fig,
            self.update_plot,
            interval=self.refresh_interval * 1000,  # Convert to milliseconds
            cache_frame_data=False,
        )

        # Show the plot (this will block until window is closed)
        plt.show()


def main():
    # Locate the history.data file
    try:
        history_file = glob.glob("../LOGS/history.data")[0]
    except IndexError:
        history_file = "../LOGS/history.data"  # Default path if not found
        print(f"Warning: No history.data file found, will check for {history_file}")

    checker = HistoryChecker(history_file=history_file, refresh_interval=5)
    checker.run()


if __name__ == "__main__":
    main()
