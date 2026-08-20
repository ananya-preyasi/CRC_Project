# plot_style.py
#
# Shared matplotlib styling for 07_generate_figures.py, built from the
# repository's validated default data-viz palette (categorical hues in
# fixed order, one-hue sequential blue ramp, neutral chart chrome).

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
AXIS = "#c3c2b7"

# Fixed categorical order (slots 1-7 of the validated 8-hue palette).
CATEGORICAL = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
CATEGORICAL_ORDER = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]

BLUE_SEQUENTIAL_STOPS = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
]
BLUE_SEQUENTIAL_CMAP = LinearSegmentedColormap.from_list("blue_seq", BLUE_SEQUENTIAL_STOPS)


def year_color_map(years):
    """Fixed color per year, assigned in order across the 7 usable years."""
    return {y: CATEGORICAL[CATEGORICAL_ORDER[i % len(CATEGORICAL_ORDER)]] for i, y in enumerate(years)}


def apply_base_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_PRIMARY,
        "axes.titlecolor": INK_PRIMARY,
        "text.color": INK_PRIMARY,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "grid.color": GRIDLINE,
        "grid.linewidth": 0.8,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.family": "sans-serif",
        "font.size": 11,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "legend.frameon": False,
    })
