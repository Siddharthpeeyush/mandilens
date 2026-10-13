#!/usr/bin/env python3
"""Day 3: price distributions per commodity — histograms, skew, IQR outliers.

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/distributions_<latest-date>.svg
        (appends a "Price distributions" section to the matching daily report)
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as <text>, not glyph paths
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "daily")

FOCUS = ["Onion", "Potato", "Tomato"]


def _iqr_outliers(s):
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return s[(s < lo) | (s > hi)], lo, hi


def main():
    if not os.path.exists(PROCESSED):
        print("DIST: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    latest = sorted(df["arrival_date"].unique())[-1]
    date_s = pd.Timestamp(latest).strftime("%Y-%m-%d")

    rows = []
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=False)
    fig.suptitle(f"Modal price distribution (Rs/quintal) — {date_s}",
                 fontsize=13, fontweight="bold")
    for ax, comm in zip(axes, FOCUS):
        prices = df[df["commodity"] == comm]["modal_price"].dropna()
        skew = prices.skew()
        out, lo, hi = _iqr_outliers(prices)
        rows.append({"commodity": comm, "n": len(prices),
                     "min": prices.min(), "max": prices.max(),
                     "median": prices.median(), "skew": round(skew, 2),
                     "outliers": len(out)})
        counts, edges = __import__("numpy").histogram(prices, bins=12)
        ax.stairs(counts, edges, fill=True, color="#4a9d5d", alpha=0.9)
        ax.axvline(prices.median(), color="#d94f3d", ls="--", lw=1.5,
                   label=f"median {prices.median():,.0f}")
        ax.set_title(f"{comm}  (skew {skew:+.2f}, outliers {len(out)})",
                     fontsize=11)
        ax.set_xlabel("Rs / quintal")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("observations")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = os.path.join(CHARTS_DIR, f"distributions_{date_s}.svg")
    fig.savefig(out_path, format="svg")
    plt.close(fig)

    # Append findings to today's daily report
    report = os.path.join(REPORTS_DIR, f"{date_s}.md")
    if os.path.exists(report):
        with open(report, "a") as fh:
            fh.write("\n## Price distributions (Day 3 analysis)\n\n")
            fh.write("| Commodity | n | Min ₹/q | Median ₹/q | Max ₹/q "
                     "| Skew | IQR outliers |\n")
            fh.write("|---|---|---|---|---|---|---|\n")
            for r in rows:
                fh.write(f"| {r['commodity']} | {r['n']} | "
                         f"{r['min']:,.0f} | {r['median']:,.0f} | "
                         f"{r['max']:,.0f} | {r['skew']:+.2f} | "
                         f"{r['outliers']} |\n")
            fh.write(f"\n![price distributions](../charts/distributions_"
                     f"{date_s}.svg)\n")

    print(f"DIST: {out_path} ({len(rows)} commodities)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
