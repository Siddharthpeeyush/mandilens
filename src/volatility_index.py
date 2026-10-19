#!/usr/bin/env python3
"""Day 9: commodity volatility index — rank commodities by price stability.

Method (per commodity, modal prices pooled across mandis and days):
  CV   = std / mean            (classic coefficient of variation)
  RMD  = IQR / median          (robust spread, secondary check)
  DADC = mean(|daily % change| of the all-mandi median series)
         (day-to-day swing, stability-over-time check)

Volatility index = 100 * CV / max(CV) across commodities (0..100).
Rank 1 = most stable (lowest index).

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/volatility_index_YYYY-MM-DD.svg
        reports/day9_commodity_volatility_index.md
Prints: per-commodity summary table.
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
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()


def commodity_stats(df):
    rows = []
    for comm, g in df.groupby("commodity"):
        x = g["modal_price"].to_numpy(dtype=float)
        x = x[np.isfinite(x) & (x > 0)]
        q1, med, q3 = np.percentile(x, [25, 50, 75])
        iqr = q3 - q1
        mean, std = x.mean(), x.std(ddof=1)
        cv = std / mean if mean > 0 else np.nan
        rmd = iqr / med if med > 0 else np.nan
        # day-to-day swing: daily all-mandi median series -> % changes
        daily = g.groupby("arrival_date")["modal_price"].median().sort_index()
        pct = daily.pct_change().abs()
        dadc = pct.mean(skipna=True)
        rows.append(dict(commodity=comm, n=len(x), median=med,
                         mean=mean, std=std, cv=cv, rmd=rmd, dadc=dadc))
    return pd.DataFrame(rows)


def make_chart(stats, mandi_cv, path):
    stats = stats.sort_values("index").iloc[::-1]  # least stable on top
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                   gridspec_kw={"width_ratios": [1.1, 1]})
    fig.suptitle(f"Commodity volatility index — MandiLens (to {TODAY})",
                 fontsize=12, fontweight="bold")

    # Panel 1: index bars, ranked
    colors = {"Onion": "#e67e22", "Potato": "#8d6e63", "Tomato": "#e53935"}
    y = np.arange(len(stats))
    bars = ax1.barh(y, stats["index"],
                    color=[colors.get(c, "#607d8b") for c in stats["commodity"]])
    ax1.set_yticks(y)
    ax1.set_yticklabels([f"#{i + 1} {c}" for i, c in
                         enumerate(stats["commodity"])])
    ax1.invert_yaxis()
    ax1.set_xlabel("Volatility index (100 = most volatile)")
    ax1.set_xlim(0, 105)
    for bar, cv, dadc in zip(bars, stats["cv"], stats["dadc"]):
        ax1.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                 f"CV {cv:.1%} · daily swing {dadc:.1%}",
                 va="center", fontsize=9)
    ax1.set_title("Rank: most stable → most volatile", fontsize=10)

    # Panel 2: mandi-level CV heatmap
    pivot = mandi_cv.pivot(index="market", columns="commodity", values="cv")
    pivot = pivot.reindex(sorted(pivot.index))
    im = ax2.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
    ax2.set_xticks(range(len(pivot.columns)))
    ax2.set_xticklabels(pivot.columns, fontsize=9)
    ax2.set_yticks(range(len(pivot.index)))
    ax2.set_yticklabels(pivot.index, fontsize=8)
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            v = pivot.values[i, j]
            ax2.text(j, i, f"{v:.1%}" if np.isfinite(v) else "–",
                     ha="center", va="center", fontsize=8,
                     color="white" if v > 0.18 else "black")
    ax2.set_title("Mandi-level CV per commodity", fontsize=10)
    fig.colorbar(im, ax=ax2, label="CV (std/mean)")

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(path, format="svg")
    plt.close(fig)


def write_report(stats, mandi_cv, chart_name, path):
    stats = stats.sort_values("index")
    lines = [
        "# Day 9 — Commodity volatility index: rank commodities by price stability",
        "",
        "Volatility index = 100 × CV / max(CV), where CV = std/mean of modal",
        "prices pooled across all mandis and days. Rank #1 = most stable.",
        "Two cross-checks: robust spread IQR/median, and mean absolute daily",
        "percentage change of the all-mandi median series (day-to-day swing).",
        "",
        "| Rank | Commodity | n | Median (Rs/qtl) | CV | Volatility index | "
        "Robust IQR/median | Daily swing |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for rank, r in enumerate(stats.itertuples(), 1):
        lines.append(
            f"| #{rank} | {r.commodity} | {r.n} | {r.median:,.0f} | "
            f"{r.cv:.1%} | {r.index:.0f} | {r.rmd:.1%} | {r.dadc:.1%} |")
    lines += [
        "",
        "## Reading the result",
        "",
        f"**{stats.iloc[0]['commodity']} is the most price-stable commodity** "
        f"(index {stats.iloc[0]['index']:.0f}), **{stats.iloc[-1]['commodity']} "
        f"the most volatile** (index {stats.iloc[-1]['index']:.0f}). The robust "
        "spread (IQR/median) agrees with the CV ranking for "
        f"{'all three commodities' if list(stats.sort_values('cv')['commodity']) == list(stats.sort_values('rmd')['commodity']) else 'most of the ranking'}, so the "
        "ranking is not an artefact of a few extreme points.",
        "",
        "The day-to-day swing shows how much a typical daily headline move is:",
        f"around {stats.iloc[0]['dadc']:.1%} for {stats.iloc[0]['commodity']} vs "
        f"{stats.iloc[-1]['dadc']:.1%} for {stats.iloc[-1]['commodity']}. "
        "Week-3 forecasting baselines should budget proportionally more "
        "uncertainty for the volatile end of the ranking.",
        "",
        "## Mandi-level view",
        "",
        "| Market | " + " | ".join(stats['commodity']) + " |",
        "|" + "---|" * (len(stats['commodity']) + 1),
    ]
    pv = mandi_cv.pivot(index="market", columns="commodity",
                        values="cv").reindex(sorted(mandi_cv["market"].unique()))
    pv = pv[[c for c in stats["commodity"]]]
    for mkt, row in pv.iterrows():
        cells = " | ".join(f"{v:.1%}" if pd.notna(v) else "–" for v in row)
        lines.append(f"| {mkt} | {cells} |")
    lines += [
        "",
        "CV at mandi level mixes local supply shocks with the national",
        "seasonal pattern — the commodity ranking above pools all of it,",
        "which is the right denominator for a stability comparison.",
        "",
        f"![Volatility index](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df = df[df["modal_price"].notna() & (df["modal_price"] > 0)]
    stats = commodity_stats(df)
    stats["index"] = 100 * stats["cv"] / stats["cv"].max()

    mandi_cv = (df.groupby(["market", "commodity"])["modal_price"]
                  .agg(lambda s: s.std(ddof=1) / s.mean())
                  .reset_index().rename(columns={"modal_price": "cv"}))

    chart_name = f"volatility_index_{TODAY}.svg"
    make_chart(stats, mandi_cv, os.path.join(CHARTS_DIR, chart_name))
    report_name = "day9_commodity_volatility_index.md"
    write_report(stats, mandi_cv, chart_name,
                 os.path.join(REPORTS_DIR, report_name))

    print("Commodity | n | median | CV | index | IQR/med | daily swing")
    for r in stats.sort_values("index").itertuples():
        print(f"{r.commodity:8s} | {r.n:3d} | {r.median:6.0f} | "
              f"{r.cv:.1%} | {r.index:5.0f} | {r.rmd:.1%} | {r.dadc:.1%}")


if __name__ == "__main__":
    main()
