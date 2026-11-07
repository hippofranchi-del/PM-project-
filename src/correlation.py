"""
Step 3 – Correlation & historical risk analysis – Quality 130/30 Fund
Input : prices_capiq.xlsx (S&P Capital IQ stock chart export, daily % change since 30 Oct 2023)
        portfolio.csv     (portfolio weights)
Output: chart4_correlation_heatmap.png, chart5_correlation_blocks.png,
        correlation_summary.csv, historical_risk.csv, stock_betas.csv
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BLUE, ORANGE, RED, INK, MUTED, GRID, MID = "#2a78d6", "#eb6834", "#e34948", "#0b0b0b", "#52514e", "#e6e5e1", "#f0efec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.axisbelow": True})
RF = 0.043   # average 3-month T-bill rate Nov 2023 – Oct 2026 (approximation)

# ---------- load & convert to monthly returns ----------
raw = pd.read_excel("data/prices_capiq.xlsx", sheet_name="Data")
raw = raw.set_index("Pricing Date").sort_index()
cols = [c for c in raw.columns if "(%)" in c]
lvl = 1 + raw[cols] / 100                              # cumulative index, start = 1
lvl.columns = [c.split(" |")[0].replace("^SPYZ", "SP500") for c in cols]
monthly = lvl.resample("ME").last().pct_change().dropna()
print("Months:", len(monthly), monthly.index[0].date(), "to", monthly.index[-1].date())

pf = pd.read_csv("output/portfolio.csv")
w = pf.set_index("ticker")["weight"]
order = list(pf.sort_values(["side", "weight"], ascending=[True, False])["ticker"])
longs, shorts = list(pf[pf.side == "Long"].ticker), list(pf[pf.side == "Short"].ticker)

R = monthly[order]; M = monthly["SP500"]
C = R.corr()

# ---------- correlation summary ----------
def avg_off(a, b):
    sub = C.loc[a, b].values
    if a == b: sub = sub[~np.eye(len(a), dtype=bool)]
    return sub.mean()
summary = pd.DataFrame({
    "Pair type": ["Long vs long", "Short vs short", "Long vs short", "All 27 stocks", "Stocks vs S&P 500"],
    "Average correlation": [avg_off(longs, longs), avg_off(shorts, shorts), avg_off(longs, shorts),
                            avg_off(order, order), R.corrwith(M).mean()]}).round(2)
summary.to_csv("output/correlation_summary.csv", index=False); print(summary.to_string(index=False))

# ---------- betas & historical portfolio risk (constant current weights) ----------
beta = R.apply(lambda s: s.cov(M) / M.var())
beta.round(2).rename("Beta (3y monthly)").to_csv("output/stock_betas.csv")
port = (R * w[order]).sum(axis=1)
def stats(x):
    ann_r = (1 + x).prod() ** (12 / len(x)) - 1
    ann_sd = x.std() * np.sqrt(12)
    return ann_r, ann_sd, (ann_r - RF) / ann_sd
pr, psd, psh = stats(port); mr, msd, msh = stats(M)
pbeta = port.cov(M) / M.var()
alpha = pr - (RF + pbeta * (mr - RF))
te = (port - M).std() * np.sqrt(12)
hist = pd.DataFrame({"Measure": ["Annual return", "Annual volatility", "Sharpe ratio", "Beta vs S&P 500",
                                 "Jensen's alpha", "Correlation with S&P 500", "Tracking error"],
                     "Quality 130/30": [f"{pr:.1%}", f"{psd:.1%}", f"{psh:.2f}", f"{pbeta:.2f}", f"{alpha:+.1%}",
                                        f"{port.corr(M):.2f}", f"{te:.1%}"],
                     "S&P 500": [f"{mr:.1%}", f"{msd:.1%}", f"{msh:.2f}", "1.00", "0.0%", "1.00", "–"]})
hist.to_csv("output/historical_risk.csv", index=False); print(hist.to_string(index=False))
avg_sd = (R.std() * np.sqrt(12))
print("Weighted avg stock vol:", f"{(w[order].abs() * avg_sd).sum() / w.abs().sum():.1%}",
      " | portfolio beta from Capital IQ 3y betas was 0.16")
print(beta.round(2).to_string())

# ---------- chart 4: heat map ----------
cmap = LinearSegmentedColormap.from_list("div", [BLUE, MID, RED])
fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(C.values, cmap=cmap, vmin=-1, vmax=1)
ax.set_xticks(range(len(order)), order, rotation=90, fontsize=8)
ax.set_yticks(range(len(order)), order, fontsize=8)
for t in ax.get_xticklabels() + ax.get_yticklabels():
    t.set_color(BLUE if t.get_text() in longs else ORANGE)
nL = len(longs) - 0.5
ax.axhline(nL, color=INK, lw=1.5); ax.axvline(nL, color=INK, lw=1.5)
ax.text(len(longs) / 2, -1.2, "LONGS", ha="center", color=BLUE, weight="bold", fontsize=9)
ax.text(len(longs) + len(shorts) / 2, -1.2, "SHORTS", ha="center", color=ORANGE, weight="bold", fontsize=9)
for s in ax.spines.values(): s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label("Correlation of monthly returns")
cb.outline.set_visible(False)
ax.set_title(f"Low correlations across holdings (average {summary.iloc[3,1]:.2f})",
             loc="left", color=INK, fontsize=12, weight="bold", pad=24)
fig.text(0.01, 0.01, f"Monthly share-price returns, {monthly.index[0]:%b %Y} – {monthly.index[-1]:%b %Y} ({len(monthly)} months). "
         "Source: S&P Capital IQ share prices.", fontsize=8, color=MUTED)
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig("output/chart4_correlation_heatmap.png", dpi=200); plt.close(fig)

# ---------- chart 5: average correlation by block ----------
fig, ax = plt.subplots(figsize=(7.5, 3.6))
labels = summary["Pair type"][::-1]; vals = summary["Average correlation"][::-1]
ax.barh(labels, vals, color=BLUE, height=0.55)
for i, v in enumerate(vals): ax.text(v + 0.01 if v >= 0 else v - 0.01, i, f"{v:.2f}", va="center",
                                     ha="left" if v >= 0 else "right", fontsize=9, color=INK)
ax.axvline(0, color=INK, lw=0.8); ax.set_xlim(min(-0.1, vals.min() - 0.1), 1)
ax.set_xlabel("Average pairwise correlation (monthly returns)"); ax.grid(axis="x", color=GRID)
ax.set_title("Holdings move largely independently", loc="left", color=INK, fontsize=11, weight="bold")
fig.tight_layout(); fig.savefig("output/chart5_correlation_blocks.png", dpi=200); plt.close(fig)
