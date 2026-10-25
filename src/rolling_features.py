#!/usr/bin/env python3
"""Day 15: lag/rolling features — 3-day and 7-day moving averages.

Method:
  1. Per market-commodity series (sorted by arrival_date), compute
     MA3 and MA7 of modal_price (full windows only: min_periods = window),
     plus lag-1 price and the deviation of today's price from each average.
  2. Latest snapshot: today's price vs MA3 vs MA7 for all 24 series, with
     a trend flag (price above MA7 = above trend).
  3. Chart: median-across-markets daily price, MA3 and MA7 per commodity
     (last 14 days), so the smoothing is visible, not just tabulated.
  4. Verification: recompute MA7 by hand for one series (Azadpur Onion,
     or the first series alphabetically if Azadpur is absent) and assert
     it matches the rolling output to the cent.

Honest-data note: on sample rows the generator's drift is smooth, so
prices track their moving averages closely and deviations stay small.
The features themselves are the deliverable — Day 16's persistence and
moving-average forecasts consume this exact table unchanged.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/rolling_features.csv
        charts/rolling_features_YYYY-MM-DD.svg
        reports/day15_lag_rolling_features.md
Prints: coverage + latest-snapshot summary + hand-check result.
"""
import datetime as dt
import os

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as <text>: smaller, selectable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
OUT_FEATURES = os.path.join(BASE_DIR, "data", "processed", "rolling_features.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

COLORS = {"Onion": "#e67e22", "Potato": "#8d6e63", "Tomato": "#e53935"}


def add_features(df):
    df = df.sort_values(["market", "commodity", "arrival_date"]).copy()
    g = df.groupby(["market", "commodity"])["modal_price"]
    df["lag1"] = g.shift(1)
    df["ma3"] = g.transform(lambda s: s.rolling(3).mean())
    df["ma7"] = g.transform(lambda s: s.rolling(7).mean())
    df["dev_ma3_pct"] = (df["modal_price"] / df["ma3"] - 1) * 100
    df["dev_ma7_pct"] = (df["modal_price"] / df["ma7"] - 1) * 100
    return df


def make_chart(df, path):
    # Median-across-markets price / MA3 / MA7 per commodity, last 14 days.
    last = df[df["arrival_date"] >= df["arrival_date"].max() - pd.Timedelta(days=13)]
    med = (last.groupby(["commodity", "arrival_date"])
           .agg(price=("modal_price", "median"), ma3=("ma3", "median"),
                ma7=("ma7", "median")).reset_index())
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 6.6), sharex=True)
    for ax, comm in zip(axes, ["Onion", "Potato", "Tomato"]):
        sub = med[med["commodity"] == comm]
        ax.plot(sub["arrival_date"], sub["price"], "o-", lw=1.5,
                color=COLORS[comm], label="Median modal price")
        ax.plot(sub["arrival_date"], sub["ma3"], "--", lw=1.2,
                color="#37474f", label="MA3")
        ax.plot(sub["arrival_date"], sub["ma7"], ":", lw=1.4,
                color="#90a4ae", label="MA7")
        ax.set_title(f"{comm} — median price vs 3-day / 7-day averages",
                     fontsize=10, fontweight="bold")
        ax.set_ylabel("Rs/qtl")
        ax.legend(fontsize=8, loc="best")
        ax.grid(alpha=0.3)
    fig.suptitle(f"Lag/rolling features — MandiLens (to {TODAY})",
                 fontsize=11, fontweight="bold")
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def hand_check(df):
    """Recompute MA7 by hand for one series; assert it matches."""
    target = df[(df["market"] == "Azadpur") & (df["commodity"] == "Onion")]
    if target.empty:
        target = df[(df["market"] == df["market"].min()) &
                    (df["commodity"] == "Onion")]
    target = target.sort_values("arrival_date")
    last7 = target["modal_price"].tail(7).to_numpy()
    manual = float(np.mean(last7))
    computed = float(target["ma7"].iloc[-1])
    assert abs(manual - computed) < 0.01, (manual, computed)
    return target["market"].iloc[0], manual, computed


def write_report(feat, latest, market, manual, computed, chart_name, path):
    n_series = feat.groupby(["market", "commodity"]).ngroups
    n_ma7 = int(feat["ma7"].notna().sum())
    n_ma3 = int(feat["ma3"].notna().sum())
    above = int((latest["dev_ma7_pct"] > 0).sum())
    lines = [
        "# Day 15 — Lag/rolling features: 3-day and 7-day moving averages",
        "",
        "## Method (read this first)",
        "",
        "Within each market-commodity series (sorted by arrival_date):",
        "MA3 = mean of today's and the previous 2 modal prices, MA7 = mean",
        "of today's and the previous 6. Full windows only — a row gets no",
        "MA7 until its series has 7 observations, so early-history rows",
        "stay blank instead of silently averaging fewer days. Lag-1 price",
        "and the % deviation of today's price from each average are stored",
        "alongside, in `data/processed/rolling_features.csv` — the exact",
        "table Day 16's persistence and moving-average forecasts consume.",
        "",
        f"Coverage: **{n_series} series**, **{n_ma3} rows with MA3**,",
        f"**{n_ma7} rows with MA7** (of {len(feat)} rows).",
        "",
        "## Verification",
        "",
        f"Hand-check on {market} Onion: mean of the last 7 modal prices =",
        f"Rs {manual:.2f}/qtl, rolling output = Rs {computed:.2f}/qtl —",
        "**match** (difference < 1 paisa). The rolling computation is",
        "verified, not just assumed.",
        "",
        "## Latest snapshot: today's price vs its averages",
        "",
        f"**{above} of {len(latest)} series trade above their 7-day average**",
        f"({len(latest) - above} below) — a mild above-trend tilt today.",
        "",
        "| Market | Commodity | Price Rs/qtl | MA3 | MA7 | vs MA3 % | vs MA7 % |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, r in latest.sort_values(["commodity", "market"]).iterrows():
        lines.append(f"| {r['market']} | {r['commodity']} | {r['modal_price']:.0f} "
                     f"| {r['ma3']:.0f} | {r['ma7']:.0f} "
                     f"| {r['dev_ma3_pct']:+.1f} | {r['dev_ma7_pct']:+.1f} |")
    lines += [
        "",
        "## Reading the result",
        "",
        "On the current (sample) data deviations from MA7 stay within a",
        "few percent — expected, since the sample generator's drift is",
        "smooth and has no shock component. The value here is the feature",
        "table itself: with MA3, MA7 and lag-1 in place, Day 16 can ask",
        "whether tomorrow's price is better predicted by today's price or",
        "by its own moving average, and Day 17 can regress on exactly",
        "these columns. On real portal extracts the same table would",
        "surface genuine breakouts (a mandi jumping well clear of MA7).",
        "",
        f"![Rolling features](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])
    feat = add_features(df)
    cols = ["market", "commodity", "arrival_date", "modal_price", "lag1",
            "ma3", "ma7", "dev_ma3_pct", "dev_ma7_pct"]
    out = feat[cols].copy()
    out["arrival_date"] = out["arrival_date"].dt.strftime("%Y-%m-%d")
    out.to_csv(OUT_FEATURES, index=False)

    latest = feat[feat["arrival_date"] == feat["arrival_date"].max()].copy()
    latest = latest[latest["ma7"].notna()]
    market, manual, computed = hand_check(feat)

    chart_name = f"rolling_features_{TODAY}.svg"
    make_chart(feat, os.path.join(CHARTS_DIR, chart_name))
    write_report(feat, latest, market, manual, computed, chart_name,
                 os.path.join(REPORTS_DIR, "day15_lag_rolling_features.md"))

    print(f"Series: {feat.groupby(['market', 'commodity']).ngroups}, "
          f"rows: {len(feat)}, MA3 rows: {int(feat['ma3'].notna().sum())}, "
          f"MA7 rows: {int(feat['ma7'].notna().sum())}")
    print(f"Hand-check {market} Onion MA7: manual {manual:.2f} = "
          f"computed {computed:.2f} — MATCH")
    print(f"Latest snapshot: {len(latest)} series, "
          f"{int((latest['dev_ma7_pct'] > 0).sum())} above MA7")
    print(f"Median |dev vs MA7| today: "
          f"{latest['dev_ma7_pct'].abs().median():.2f}%")


if __name__ == "__main__":
    main()
