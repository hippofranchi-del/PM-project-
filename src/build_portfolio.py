"""
Step 1 – Quality scores and portfolio construction (Quality 130/30 Fund)

Method (Asness, Frazzini & Pedersen, 2013 "Quality Minus Junk"):
  Profitability = ROE, gross profit / total assets
  Growth        = 5-year change in gross profit / total assets
  Safety        = beta, total debt / total assets   (sign flipped: lower = safer)
  Payout        = (dividends + buybacks - share issuance) / net income
Each measure is a z-score within its GICS sector; measures -> pillar scores -> composite score.
"""
import numpy as np
import pandas as pd

SECTORS = ["Information Technology", "Health Care", "Financials", "Consumer Discretionary",
           "Consumer Staples", "Communication Services", "Industrials", "Energy", "Utilities",
           "Real Estate", "Materials"]

# Portfolio rules
LONG_EXPOSURE, SHORT_EXPOSURE = 1.30, 0.30
LONG_CAP, SHORT_CAP = 0.10, 0.06
MAX_PER_SECTOR, N_SHORTS = 2, 8
NAV = 100_000


def load_screen(path):
    d = pd.read_excel(path, header=None, skiprows=7)
    d.columns = ["name", "id", "ticker", "industry", "price", "roe", "gp", "beta", "debt", "div",
                 "rep", "iss", "ni", "fpe", "ta", "ta_2020", "gp_2020"]
    d = d.dropna(subset=["ticker"])
    for c in d.columns[4:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["sector"] = d["industry"].astype(str).apply(
        lambda s: min((s.find(x), x) for x in SECTORS if x in s)[1] if any(x in s for x in SECTORS) else "Other")
    d.loc[d["industry"].str.startswith("Media and Entertainment"), "sector"] = "Communication Services"
    d["company"] = d["name"].str.replace(r" \(.*", "", regex=True)
    return d


def quality_scores(d):
    d = d.copy()
    d["gpa"] = d.gp / d.ta
    d["growth"] = d.gpa - d.gp_2020 / d.ta_2020
    d["lev"] = d.debt / d.ta
    payout = -d["div"].fillna(0) - d["rep"].fillna(0) - d["iss"].fillna(0)   # cash-flow signs
    d["payout"] = np.where(d.ni > 0, payout / d.ni, np.nan)                  # undefined if loss-making

    def z(col, sign=1):
        x = d[col].clip(d[col].quantile(.05), d[col].quantile(.95))          # winsorise 5/95%
        g = x.groupby(d.sector)
        return (sign * (x - g.transform("mean")) / g.transform("std")).clip(-3, 3)

    d["profitability"] = pd.concat([z("roe"), z("gpa")], axis=1).mean(axis=1)
    d["growth_z"] = z("growth")
    d["safety"] = pd.concat([z("beta", -1), z("lev", -1)], axis=1).mean(axis=1)
    d["payout_z"] = z("payout")
    d["quality"] = d[["profitability", "growth_z", "safety", "payout_z"]].mean(axis=1)
    d = d.dropna(subset=["quality"])
    d["pct_in_sector"] = d.groupby("sector")["quality"].rank(pct=True)
    d["sector_pe"] = d.groupby("sector")["fpe"].transform("median")
    d["pe_vs_sector"] = d.fpe / d.sector_pe
    return d


def capped_weights(score, total, cap):
    w = score / score.sum() * total
    for _ in range(50):
        over = w > cap
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        w[~over] += excess * w[~over] / w[~over].sum()
    return w


def build(d):
    d = d[d.price < 5000]                                   # untradeable share prices (e.g. BRK.A)
    longs = d[(d.pct_in_sector > 0.8) & (d.fpe > 0) & (d.pe_vs_sector <= 1.5)     # quality at a fair price
              & (d.roe >= 10) & (d.lev <= 0.5) & (d.beta <= 1.3)                 # analyst macro filters
              & ~d.industry.str.contains("Airline")]                               # $114 oil
    longs = longs.sort_values("quality", ascending=False).groupby("sector").head(MAX_PER_SECTOR).copy()
    shorts = d[(d.pct_in_sector <= 0.2) & ((d.pe_vs_sector > 1) | d.fpe.isna() | (d.fpe <= 0))]
    shorts = shorts.sort_values("quality").groupby("sector").head(MAX_PER_SECTOR).head(N_SHORTS).copy()
    longs["side"], shorts["side"] = "Long", "Short"
    longs["weight"] = capped_weights(longs.quality, LONG_EXPOSURE, LONG_CAP)
    shorts["weight"] = -capped_weights(-shorts.quality, SHORT_EXPOSURE, SHORT_CAP)
    p = pd.concat([longs, shorts])
    p["shares"] = (p.weight * NAV / p.price).round().astype(int)
    return p


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    universe = quality_scores(load_screen("data/sp500_screen_capiq.xlsx"))
    port = build(universe)
    out = port[["side", "ticker", "company", "sector", "price", "fpe", "sector_pe", "roe", "gpa", "growth",
                "beta", "lev", "payout", "profitability", "growth_z", "safety", "payout_z", "quality",
                "weight", "shares"]]
    out.round(4).to_csv("output/portfolio.csv", index=False)
    universe[["ticker", "company", "sector", "quality", "pct_in_sector"]].round(4).to_csv(
        "output/quality_scores_sp500.csv", index=False)
    print(out[["side", "ticker", "sector", "quality", "weight", "shares"]].round(3).to_string(index=False))
    print(f"\nLong {out.weight[out.weight > 0].sum():.0%} | Short {out.weight[out.weight < 0].sum():.0%} | "
          f"Net {out.weight.sum():.0%} | Stocks {len(out)}")
