#!/usr/bin/env python3
"""Day 4: geographic spread — state-wise median price heatmap.

Reads data/processed/mandi_prices_clean.csv, computes the median modal price
per (state, commodity) over the full history, and draws an annotated heatmap.

Writes: charts/state_heatmap_YYYY-MM-DD.png + .svg (run date via argv[1]).
"""
import datetime as dt
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")


def main():
    if not os.path.exists(PROCESSED):
        print("GEO: no processed data", file=sys.stderr)
        return 1
    date_s = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    df = pd.read_csv(PROCESSED)
    pivot = (df.groupby(["state", "commodity"])["modal_price"]
               .median().unstack("commodity"))
    if pivot.shape[0] < 2:
        print("GEO: fewer than 2 states in dataset — skipping heatmap")
        return 0
    # Order states by mean price (cheapest at top) for readability.
    order = pivot.mean(axis=1).sort_values().index
    pivot = pivot.loc[order]
    short = [s.replace("NCT of Delhi", "Delhi") for s in pivot.index]

    fig, ax = plt.subplots(figsize=(8, max(3.5, 0.65 * len(pivot))))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(pivot.columns)), pivot.columns)
    ax.set_yticks(range(len(pivot.index)), short)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            ax.text(j, i, f"₹{v:,.0f}", ha="center", va="center",
                    fontsize=9, color="black" if v < pivot.values.max() * 0.75
                    else "white")
    ax.set_title(f"Median modal price by state (₹/quintal) — {len(df)} rows")
    fig.colorbar(im, ax=ax, label="₹/quintal")
    fig.tight_layout()
    os.makedirs(CHARTS_DIR, exist_ok=True)
    for ext in ("png", "svg"):
        p = os.path.join(CHARTS_DIR, f"state_heatmap_{date_s}.{ext}")
        fig.savefig(p, format=ext, dpi=130)
        print(f"GEO: {p}")

    print("\nGEO insights:")
    for comm in pivot.columns:
        s = pivot[comm]
        print(f"  {comm}: cheapest {s.idxmin().replace('NCT of Delhi', 'Delhi')} "
              f"(₹{s.min():,.0f}) vs costliest "
              f"{s.idxmax().replace('NCT of Delhi', 'Delhi')} (₹{s.max():,.0f}) "
              f"— spread {s.max() / s.min() - 1:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
