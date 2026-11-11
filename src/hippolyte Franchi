"""
Step 4 – Report figures for Q5 and Q6 (Quality 130/30 Fund)

  chart6  Selection funnel: how the screen narrows the S&P 500 to 19 longs and 8 shorts
  chart7  Quality score against forward P/E for every holding
  chart8  Fund and S&P 500 against the security market line (Jensen's alpha)

Run from the repository root after build_portfolio.py:  python src/report_figures.py
"""
import os
import numpy as np
import pandas as pd
from style import plt, BLUE, ORANGE, INK, MUTED, GRID, title
from build_portfolio import load_screen, quality_scores, MAX_PER_SECTOR, N_SHORTS

SCREEN = "data/sp500_screen_capiq.xlsx"
SP500_PE = 18.7                                   # S&P 500 forward P/E
RF, MKT, ALPHA, BETA = 3.9, 8.1, 2.0, 0.16        # % p.a.; single-index model inputs (report Table 3)

# Stocks left after each step when the screen was run on the 7 Nov 2026 export.
# Used only if the Capital IQ file is not in data/ (it is licensed and not uploaded).
RECORDED_LONG = [498, 104, 77, 59, 44, 32, 19]
RECORDED_SHORT = [498, 96, 53, 8]
LONG_STEPS = ["All scored S&P 500 stocks", "Top 20% quality in sector", "Fwd P/E ≤ 1.5× sector median",
              "ROE ≥ 10%", "Debt / assets ≤ 0.5", "Beta ≤ 1.3, no airlines", "Two best scores per sector"]
SHORT_STEPS = ["All scored S&P 500 stocks", "Bottom 20% quality in sector", "Priced above sector median P/E",
               "Lowest scores, max two per sector"]


def funnel_counts(d):
    """Apply the filters of build_portfolio.build() one at a time and count the survivors."""
    d = d[d.price < 5000]
    m = d.pct_in_sector > 0.8
    long_counts = [len(d), int(m.sum())]
    for step in [(d.fpe > 0) & (d.pe_vs_sector <= 1.5), d.roe >= 10, d.lev <= 0.5,
                 (d.beta <= 1.3) & ~d.industry.str.contains("Airline")]:
        m = m & step
        long_counts.append(int(m.sum()))
    long_counts.append(len(d[m].sort_values("quality", ascending=False).groupby("sector").head(MAX_PER_SECTOR)))
    junk = d.pct_in_sector <= 0.2
    pricey = junk & ((d.pe_vs_sector > 1) | d.fpe.isna() | (d.fpe <= 0))
    picked = d[pricey].sort_values("quality").groupby("sector").head(MAX_PER_SECTOR).head(N_SHORTS)
    return long_counts, [len(d), int(junk.sum()), int(pricey.sum()), len(picked)]


def chart_funnel(long_counts, short_counts):
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4), gridspec_kw={"wspace": 1.05})
    panels = [(axs[0], LONG_STEPS, long_counts, BLUE, "LONGS"), (axs[1], SHORT_STEPS, short_counts, ORANGE, "SHORTS")]
    for ax, steps, counts, colour, name in panels:
        y = [len(LONG_STEPS) - 1 - i for i in range(len(steps))]
        alphas = [0.35] + [0.6] * (len(steps) - 2) + [1.0]
        for yi, n, a in zip(y, counts, alphas):
            ax.barh(yi, n, color=colour, alpha=a, height=0.68)
            ax.text(n + 10, yi, str(n), va="center", color=INK, weight="bold" if a == 1 else "normal")
        ax.set_yticks(y); ax.set_yticklabels(steps, color=INK)
        ax.set_xlim(0, max(counts) * 1.17); ax.set_ylim(-0.6, len(LONG_STEPS) - 0.4)
        ax.set_xticks([]); ax.tick_params(axis="y", length=0); ax.spines["bottom"].set_visible(False)
        ax.set_title(f"{name}: {counts[0]} → {counts[-1]}", loc="left", color=colour, fontsize=10, weight="bold")
    fig.suptitle("Every holding comes out of the same rule-based screen", x=0.012, y=0.98, ha="left",
                 color=INK, fontsize=12, weight="bold")
    fig.subplots_adjust(left=0.27, right=0.985, top=0.82, bottom=0.03)
    fig.savefig("output/chart6_selection_funnel.png", dpi=200); plt.close(fig)


def chart_quality_vs_valuation(pf):
    pf = pf.dropna(subset=["fpe"])                      # Moderna has no forward earnings
    fig, ax = plt.subplots(figsize=(6.2, 4))
    ax.axhline(SP500_PE, color=MUTED, ls="--", lw=0.8)
    ax.text(-0.72, SP500_PE * 1.05, f"S&P 500: {SP500_PE}x", fontsize=8.5, color=MUTED, va="bottom")
    ax.axvline(0, color=GRID, lw=0.8)
    for side, colour in (("Long", BLUE), ("Short", ORANGE)):
        s = pf[pf.side == side]
        ax.scatter(s.quality, s.fpe, s=34, color=colour, label=side, zorder=3, edgecolor="white", lw=0.5)
    labels = {"ADBE": (6, -4, "left"), "IT": (6, 3, "left"), "GWW": (6, 3, "left"), "HST": (-6, 4, "right"),
              "FISV": (-6, -8, "right"), "TSLA": (7, -3, "left"), "ECHO": (0, -13, "center"),
              "BE": (0, 8, "center"), "INTC": (7, 3, "left"), "OKE": (7, -4, "left")}
    for _, r in pf[pf.ticker.isin(labels)].iterrows():
        dx, dy, ha = labels[r.ticker]
        ax.annotate(r.ticker, (r.quality, r.fpe), (dx, dy), textcoords="offset points", fontsize=8.5, ha=ha,
                    color=BLUE if r.side == "Long" else ORANGE,
                    weight="bold" if r.ticker in ("ADBE", "TSLA") else "normal")
    ax.set_yscale("log"); ax.set_yticks([5, 10, 20, 50, 100, 200])
    ax.set_yticklabels(["5x", "10x", "20x", "50x", "100x", "200x"]); ax.minorticks_off()
    ax.set_ylim(5, 260); ax.set_xlim(-2, 1.6)
    ax.set_xlabel("Quality score (z-score within sector)"); ax.set_ylabel("Forward P/E (log scale)")
    ax.legend(frameon=False, loc="upper right", handletextpad=0.2)
    title(ax, "We buy quality cheaply and short expensive junk")
    fig.tight_layout(); fig.savefig("output/chart7_quality_vs_valuation.png", dpi=200); plt.close(fig)


def chart_security_market_line():
    sml = lambda b: RF + b * (MKT - RF)                 # CAPM expected return for a given beta
    fund = sml(BETA) + ALPHA
    fig, ax = plt.subplots(figsize=(6.2, 4))
    x = np.array([0, 1.25]); ax.plot(x, sml(x), color=MUTED, lw=1.3)
    ax.text(0.62, sml(0.62) - 0.2, "Security market line", fontsize=8.5, color=MUTED, va="top")
    ax.plot([1], [MKT], "o", color=MUTED, ms=7)
    ax.annotate(f"S&P 500\nβ = 1.00, {MKT}%", (1, MKT), (-7, 7), textcoords="offset points", fontsize=9,
                ha="right", va="bottom", color=INK)
    ax.annotate("", (BETA, fund - 0.07), (BETA, sml(BETA) + 0.03), arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))
    ax.plot([BETA], [fund], "o", color=BLUE, ms=8, zorder=5)
    ax.annotate(f"130/30 fund\nβ = {BETA}, {fund:.1f}%", (BETA, fund), (8, 4), textcoords="offset points",
                fontsize=9, va="bottom", color=BLUE, weight="bold")
    ax.text(BETA + 0.03, fund - 0.8, f"α = +{ALPHA:.1f}%", fontsize=9.5, color=ORANGE, va="center", weight="bold")
    ax.plot([0], [RF], "o", color=MUTED, ms=5, clip_on=False, zorder=5)
    ax.annotate(f"Risk-free {RF}%", (0, RF), (7, -11), textcoords="offset points", fontsize=8.5, color=MUTED)
    ax.set_xlim(0, 1.25); ax.set_ylim(3, 9.5); ax.set_xlabel("Beta"); ax.set_ylabel("Expected 12-month return (%)")
    title(ax, "The fund sits above the security market line")
    fig.tight_layout(); fig.savefig("output/chart8_security_market_line.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    if os.path.exists(SCREEN):
        long_counts, short_counts = funnel_counts(quality_scores(load_screen(SCREEN)))
    else:
        long_counts, short_counts = RECORDED_LONG, RECORDED_SHORT
    print("Longs :", " -> ".join(map(str, long_counts)))
    print("Shorts:", " -> ".join(map(str, short_counts)))
    chart_funnel(long_counts, short_counts)
    chart_quality_vs_valuation(pd.read_csv("output/portfolio.csv"))
    chart_security_market_line()
