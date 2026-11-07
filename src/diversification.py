"""
Step 2 – Diversification by construction: concentration metrics, sector spread, position sizes,
and the Evans & Archer (1968) diversification curve.
"""
import numpy as np
import pandas as pd
from style import plt, BLUE, ORANGE, INK, MUTED, GRID, title

pf = pd.read_csv("output/portfolio.csv")
w = pf["weight"]
g = w.abs() / w.abs().sum()                              # share of gross exposure
n, hhi = len(pf), (g ** 2).sum()
n_eff = 1 / hhi
sect = pf.pivot_table(index="sector", columns="side", values="weight", aggfunc="sum").fillna(0)
sect["Net"] = sect.sum(axis=1)

metrics = pd.DataFrame({
    "Metric": ["Number of stocks", "Effective number of stocks (1/HHI)", "Herfindahl index (HHI)",
               "Largest single position", "Top-5 positions (% of gross)", "Sectors covered",
               "Largest net sector exposure", "Diversifiable variance removed (1 - 1/N_eff)"],
    "Value": [n, round(n_eff, 1), round(hhi, 3), f"{w.abs().max():.0%}",
              f"{g.sort_values(ascending=False).head(5).sum():.0%}", f"{len(sect)} of 11",
              f"{sect['Net'].abs().max():.0%} ({sect['Net'].abs().idxmax()})", f"{1 - 1 / n_eff:.0%}"]})
metrics.to_csv("output/diversification_metrics.csv", index=False)
print(metrics.to_string(index=False))

# Chart 1 – diversification curve
sm, se = 0.16, 0.30
N = np.arange(1, 101)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.plot(N, np.sqrt(sm**2 + se**2 / N) * 100, color=BLUE, lw=2)
ax.axhline(sm * 100, color=MUTED, lw=1, ls="--")
ax.text(100, sm * 100 + 0.6, "Market risk (cannot be diversified)", ha="right", color=MUTED, fontsize=9)
for x, lab, off in [(n, f"Our portfolio: {n} stocks", (12, 22)), (n_eff, f"Effective N ≈ {n_eff:.0f}", (-10, -32))]:
    y = np.sqrt(sm**2 + se**2 / x) * 100
    ax.plot(x, y, "o", ms=8, color=ORANGE, mec="white", mew=2, zorder=3)
    ax.annotate(lab, (x, y), xytext=off, textcoords="offset points", fontsize=9,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set(xlabel="Number of stocks (equally weighted)", ylabel="Portfolio standard deviation (%)", xlim=(0, 100), ylim=(10, 36))
ax.grid(axis="y", color=GRID); title(ax, "Most diversification benefit is captured by 20–30 stocks")
fig.text(0.01, 0.005, "Assumes market vol 16%, average stock-specific vol 30%. After Evans & Archer (1968) and Statman (1987).",
         fontsize=8, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig("output/chart1_diversification_curve.png", dpi=200); plt.close(fig)

# Chart 2 – sector exposure
s = sect.sort_values("Net"); y = np.arange(len(s))
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.barh(y, s["Long"] * 100, color=BLUE, height=0.6, label="Long")
ax.barh(y, s["Short"] * 100, color=ORANGE, height=0.6, label="Short")
for i, v in enumerate(s["Net"]):
    ax.text(s["Long"].iloc[i] * 100 + 0.5, i, f"net {v:+.0%}", va="center", fontsize=8, color=MUTED)
ax.set_yticks(y, s.index); ax.axvline(0, color=INK, lw=0.8); ax.set_xlim(-10, 24)
ax.set_xlabel("Weight (% of capital)"); ax.grid(axis="x", color=GRID); ax.legend(frameon=False, loc="lower right")
title(ax, "All 11 sectors held; no net sector above 18%")
fig.tight_layout(); fig.savefig("output/chart2_sector_exposure.png", dpi=200); plt.close(fig)

# Chart 3 – position sizes
d = pf.assign(w=w * 100).sort_values("w", ascending=False)
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.bar(d["ticker"], d["w"], color=[BLUE if v > 0 else ORANGE for v in d["w"]], width=0.7)
ax.axhline(10, color=MUTED, lw=1, ls="--"); ax.text(26.4, 10.4, "10% cap", ha="right", fontsize=8, color=MUTED)
ax.axhline(0, color=INK, lw=0.8); ax.set_ylabel("Weight (% of capital)")
ax.tick_params(axis="x", rotation=90, labelsize=8); ax.grid(axis="y", color=GRID)
title(ax, "No single stock above 10%: blue = long, orange = short")
fig.tight_layout(); fig.savefig("output/chart3_position_sizes.png", dpi=200); plt.close(fig)
