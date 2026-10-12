#!/usr/bin/env python3
"""Day 2 roadmap item — missing-data audit: which mandis/commodities report irregularly?

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/coverage_matrix_YYYY-MM-DD.svg  (green=reported, red=missing)
        reports/day2_missing_data_audit.md       (findings section)
Prints: summary lines to stdout.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FOCUS = ["Onion", "Potato", "Tomato"]


def main():
    if not os.path.exists(PROCESSED):
        print("AUDIT: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    df["day"] = df["arrival_date"].dt.strftime("%Y-%m-%d")
    all_days = sorted(df["day"].unique())
    markets = sorted(df["market"].unique())

    # present[market, commodity, day] -> bool
    present = (
        df[["day", "market", "commodity"]]
        .drop_duplicates()
        .assign(hit=True)
    )
    full = (
        pd.MultiIndex.from_product(
            [all_days, markets, FOCUS], names=["day", "market", "commodity"]
        ).to_frame(index=False)
        .merge(present, on=["day", "market", "commodity"], how="left")
        .fillna(False)
    )

    # --- coverage table: % of days reported per market-commodity pair
    cov = (
        full.groupby(["market", "commodity"])["hit"]
        .mean().mul(100).round(1).reset_index()
        .rename(columns={"hit": "coverage_pct"})
    )
    missing_days = (
        full[~full["hit"]].groupby(["market", "commodity"])["day"]
        .apply(lambda s: ", ".join(sorted(s.unique()))).reset_index()
        .rename(columns={"day": "missing_dates"})
    )
    cov = cov.merge(missing_days, on=["market", "commodity"], how="left")
    cov["missing_dates"] = cov["missing_dates"].fillna("—")

    per_market = (full.groupby("market")["hit"].mean().mul(100).round(1)
                  .sort_values())
    per_commodity = (full.groupby("commodity")["hit"].mean().mul(100).round(1))
    overall = full["hit"].mean() * 100
    n_missing = int((~full["hit"]).sum())
    worst = cov.sort_values("coverage_pct").iloc[0]

    # --- heatmap chart: hand-rolled compact SVG (matplotlib SVGs bloat here)
    pairs = cov[["market", "commodity"]].sort_values(["market", "commodity"])
    labels = [f"{m} · {c}" for m, c in zip(pairs["market"], pairs["commodity"])]
    cell_w, cell_h = 44, 22
    lab_w, top = 190, 34
    W = lab_w + cell_w * len(all_days) + 30
    H = top + cell_h * len(pairs) + 40
    hitset = set(zip(full[full["hit"]]["day"], full[full["hit"]]["market"],
                      full[full["hit"]]["commodity"]))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}" font-family="sans-serif">']
    parts.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
    parts.append(f'<text x="16" y="24" font-size="15" font-weight="bold">'
                 f'Reporting coverage — {len(all_days)} days '
                 f'({all_days[0]} → {all_days[-1]})</text>')
    parts.append('<text x="%d" y="24" font-size="12">green = reported, '
                 'red = missing</text>' % (W - 230))
    for j, d in enumerate(all_days):
        x = lab_w + j * cell_w
        parts.append(f'<text x="{x + 4}" y="{top - 8}" font-size="11" '
                     f'transform="rotate(45 {x + 4},{top - 8})">{d[5:]}</text>')
    for i, (m, c) in enumerate(zip(pairs["market"], pairs["commodity"])):
        y = top + i * cell_h
        parts.append(f'<text x="16" y="{y + cell_h - 6}" font-size="12">{m} · {c}</text>')
        for j, d in enumerate(all_days):
            fill = "#27ae60" if (d, m, c) in hitset else "#e74c3c"
            x = lab_w + j * cell_w
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 1}" '
                         f'height="{cell_h - 1}" fill="{fill}"/>')
    parts.append('</svg>')
    latest = all_days[-1]
    chart_path = os.path.join(CHARTS_DIR, f"coverage_matrix_{latest}.svg")
    with open(chart_path, "w") as f:
        f.write("\n".join(parts))

    # --- findings markdown
    md_lines = [
        "# Day 2 — Missing-data audit",
        "",
        f"Audited {len(full)} expected market–commodity–day reports across "
        f"{len(markets)} mandis × {len(FOCUS)} commodities × {len(all_days)} "
        f"days ({all_days[0]} → {all_days[-1]}).",
        "",
        f"- **Overall coverage: {overall:.1f}%** "
        f"({n_missing} of {len(full)} expected reports missing)",
        "- Per-mandi coverage:",
    ]
    for m, v in per_market.items():
        md_lines.append(f"  - {m}: {v:.1f}%")
    md_lines += [
        "- Per-commodity coverage:",
    ]
    for c, v in per_commodity.items():
        md_lines.append(f"  - {c}: {v:.1f}%")
    md_lines += [
        "",
        f"**Worst pair:** {worst['market']} · {worst['commodity']} at "
        f"{worst['coverage_pct']:.1f}% coverage "
        f"(missing: {worst['missing_dates']}).",
        "",
        "| Mandi | Commodity | Coverage | Missing dates |",
        "|---|---|---|---|",
    ]
    for _, r in cov.sort_values(["market", "commodity"]).iterrows():
        md_lines.append(f"| {r['market']} | {r['commodity']} | "
                        f"{r['coverage_pct']:.1f}% | {r['missing_dates']} |")
    md_lines += [
        "",
        f"![coverage matrix](../charts/coverage_matrix_{latest}.svg)",
    ]
    md_path = os.path.join(REPORTS_DIR, "day2_missing_data_audit.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"AUDIT: coverage {overall:.1f}% ({n_missing} missing of {len(full)})")
    print(f"AUDIT: chart -> {chart_path}")
    print(f"AUDIT: findings -> {md_path}")
    print(f"AUDIT: worst pair {worst['market']} · {worst['commodity']} "
          f"{worst['coverage_pct']:.1f}% ({worst['missing_dates']})")
    print(f"AUDIT: per-market: " +
          ", ".join(f"{m} {v:.1f}%" for m, v in per_market.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
