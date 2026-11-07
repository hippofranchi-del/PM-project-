"""Shared chart style (colour-blind-safe palette)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#e34948"
INK, MUTED, GRID, MID = "#0b0b0b", "#52514e", "#e6e5e1", "#f0efec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True})


def title(ax, text):
    ax.set_title(text, loc="left", color=INK, fontsize=11, weight="bold")
