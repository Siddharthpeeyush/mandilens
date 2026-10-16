#!/usr/bin/env python3
"""Day 6 — variety & grade price premiums.

Question: do different varieties of the same commodity (Red vs White onion,
Jyoti vs Chipsona potato, Desi vs Hybrid tomato) trade at systematically
different modal prices, and does grade matter?

Method (all on clean data, variety != "Aggregate"):
  - raw premium: (median(V1) - median(V2)) / median(V2) per commodity
  - market-adjusted premium: within each market, mean(V1) vs mean(V2) across
    all days -> per-market premium %, then median + IQR across markets.
    This strips out the market-level effect (Azadpur is dearer than
    Yeshwanthpur regardless of variety).
  - grade audit: how many distinct grades exist in the feed?

Outputs: charts/variety_premiums_<date>.svg and
reports/day6_variety_grade_premiums.md
"""
import datetime as dt
import os
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep SVG text as text: smaller, selectable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS = os.path.join(BASE_DIR, "charts")
REPORTS = os.path.join(BASE_DIR, "reports")


def market_adjusted_premium(df, commodity, v1, v2):
    """Median across markets of (mean_v1 - mean_v2)/mean_v2 within a market."""
    sub = df[df["commodity"] == commodity]
    premiums = []
    for _market, g in sub.groupby("market"):
        means = g.groupby("variety")["modal_price"].mean()
        if v1 in means.index and v2 in means.index and means[v2] > 0:
            premiums.append((means[v1] - means[v2]) / means[v2] * 100)
    if not premiums:
        return None
    return {
        "median": float(np.median(premiums)),
        "q1": float(np.percentile(premiums, 25)),
        "q3": float(np.percentile(premiums, 75)),
        "n_markets": len(premiums),
    }


def main():
    date_s = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    df = pd.read_csv(CLEAN, parse_dates=["arrival_date"])
    df = df[df["variety"] != "Aggregate"]  # portal benchmark rows carry no variety

    grades = sorted(df["grade"].dropna().unique())
    results = []
    for commodity in sorted(df["commodity"].unique()):
        varieties = sorted(df[df["commodity"] == commodity]["variety"].unique())
        if len(varieties) < 2:
            continue
        v1, v2 = varieties[0], varieties[1]
        med = df[df["commodity"] == commodity].groupby("variety")["modal_price"]
        medians = med.median()
        counts = med.count()
        raw_prem = (medians[v1] - medians[v2]) / medians[v2] * 100
        adj = market_adjusted_premium(df, commodity, v1, v2)
        results.append({
            "commodity": commodity, "v1": v1, "v2": v2,
            "median_v1": float(medians[v1]), "median_v2": float(medians[v2]),
            "n_v1": int(counts[v1]), "n_v2": int(counts[v2]),
            "raw_premium_pct": float(raw_prem), "adj": adj,
        })

    # ---- chart: median modal price by variety per commodity ----
    os.makedirs(CHARTS, exist_ok=True)
    n = len(results)
    fig, axes = plt.subplots(1, max(n, 1), figsize=(4.5 * max(n, 1), 4.2),
                             sharey=False)
    if n == 1:
        axes = [axes]
    fig.suptitle("Median modal price by variety (₹/quintal)", fontsize=13,
                 fontweight="bold")
    for ax, r in zip(axes, results):
        ax.bar([r["v1"], r["v2"]], [r["median_v1"], r["median_v2"]],
               color=["#2e7d32", "#f9a825"], edgecolor="black")
        for i, val in enumerate([r["median_v1"], r["median_v2"]]):
            ax.text(i, val, f"₹{val:,.0f}", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")
        ax.set_title(f"{r['commodity']}\n{r['v1']} vs {r['v2']}: "
                     f"{r['raw_premium_pct']:+.1f}%", fontsize=11)
        ax.set_ylabel("₹/quintal")
    fig.tight_layout()
    chart_path = os.path.join(CHARTS, f"variety_premiums_{date_s}.svg")
    fig.savefig(chart_path, format="svg")
    plt.close(fig)

    # ---- report ----
    lines = [
        f"# Day 6 — variety & grade price premiums ({date_s})",
        "",
        "Do varieties of the same commodity trade at systematically different "
        "prices? Red vs White onion, Jyoti vs Chipsona potato, Desi vs Hybrid "
        "tomato — compared on median modal price, with a market-adjusted "
        "check that strips out mandi-level price differences.",
        "",
        "## Variety premiums",
        "",
        "| Commodity | Pair | Median ₹/q (V1 / V2) | n (V1 / V2) | Raw premium | "
        "Market-adjusted premium (median across mandis, IQR) |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        if r["adj"]:
            adj_s = (f"{r['adj']['median']:+.1f}% "
                     f"[{r['adj']['q1']:+.1f}%, {r['adj']['q3']:+.1f}%] "
                     f"({r['adj']['n_markets']} mandis)")
        else:
            adj_s = "n/a (no mandi quotes both varieties)"
        lines.append(
            f"| {r['commodity']} | {r['v1']} vs {r['v2']} | "
            f"₹{r['median_v1']:,.0f} / ₹{r['median_v2']:,.0f} | "
            f"{r['n_v1']} / {r['n_v2']} | {r['raw_premium_pct']:+.1f}% | {adj_s} |")
    lines += [
        "",
        "## Grade audit",
        "",
        f"Distinct grades in the feed: **{', '.join(grades)}**. "
        "With a single grade (FAQ) reported across every row, a grade-based "
        "premium cannot be measured from this feed — a grade premium study "
        "needs data that actually varies grade.",
        "",
        "## Reading the result",
        "",
        "The raw premium is the simple median-to-median gap; the "
        "market-adjusted premium compares the two varieties *inside each "
        "mandi first* (each mandi's own mean for V1 vs V2), then takes the "
        "median of those per-mandi premiums — so a mandi that is simply "
        "expensive for everything can't fake a variety effect.",
        "",
        f"![Variety premiums](../charts/variety_premiums_{date_s}.svg)",
    ]
    os.makedirs(REPORTS, exist_ok=True)
    report_path = os.path.join(REPORTS, "day6_variety_grade_premiums.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    for r in results:
        adj_s = (f"{r['adj']['median']:+.1f}% IQR "
                 f"[{r['adj']['q1']:+.1f},{r['adj']['q3']:+.1f}]"
                 if r["adj"] else "n/a")
        print(f"{r['commodity']}: {r['v1']} vs {r['v2']} raw "
              f"{r['raw_premium_pct']:+.1f}% | market-adjusted {adj_s}")
    print(f"GRADES: {grades} -> grade premium not measurable")
    print(f"DAY6 DONE: {chart_path}, {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
