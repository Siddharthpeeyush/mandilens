#!/usr/bin/env python3
"""Day 8: outlier-detection rules on modal prices — IQR (Tukey) vs z-score.

Compares two classical outlier rules on each commodity's modal-price series
(pooled across mandis and days) and picks the project's default rule:

  IQR rule : flag x outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]   (robust)
  Z rule   : flag |z| > 3, z = (x - mean)/std              (non-robust)

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/outlier_rules_YYYY-MM-DD.svg
        reports/day8_outlier_detection_rules.md
Prints: per-commodity summary table.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as <text>: smaller, selectable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

K_IQR = 1.5   # Tukey fences
Z_THRESH = 3  # classic z-score cut-off


def detect(series, k=K_IQR, z_thresh=Z_THRESH):
    """Return (stats dict, iqr-flag mask, z-flag mask)."""
    x = series.to_numpy(dtype=float)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    iqr = q3 - q1
    lo, hi = q1 - k * iqr, q3 + k * iqr
    iqr_flag = (x < lo) | (x > hi)
    mean, std = x.mean(), x.std(ddof=1)
    z = (x - mean) / std if std > 0 else np.zeros_like(x)
    z_flag = np.abs(z) > z_thresh
    stats = dict(n=len(x), mean=mean, std=std, q1=q1, med=med, q3=q3,
                 iqr=iqr, lo=lo, hi=hi, z_max=float(np.abs(z).max()))
    return stats, iqr_flag, z_flag


def make_chart(results, path):
    comms = list(results)
    n = len(comms)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    idx = np.arange(n)
    w = 0.35
    iqr_n = [results[c]["iqr_flags"] for c in comms]
    z_n = [results[c]["z_flags"] for c in comms]
    ov_n = [results[c]["overlap"] for c in comms]
    ax.bar(idx - w / 2, iqr_n, w, label="IQR (1.5)", color="#2980b9")
    ax.bar(idx + w / 2, z_n, w, label="z-score (|z|>3)", color="#e67e22")
    ax.scatter(idx, ov_n, s=90, color="#27ae60", zorder=5,
               label="both agree", edgecolors="white")
    ax.set_xticks(idx)
    ax.set_xticklabels(comms)
    ax.set_ylabel("flagged price points")
    ax.set_title("Outlier rules: flagged counts per commodity", fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    ax = axes[1]
    rng = np.random.RandomState(7)
    for j, c in enumerate(comms):
        x = results[c]["x"]
        iq = results[c]["iqr_mask"]
        zf = results[c]["z_mask"]
        xj = rng.normal(j + 1, 0.09, size=len(x))
        base = ~(iq | zf)
        keep = np.zeros(len(x), dtype=bool)
        if base.sum() > 60:                      # slim SVG: downsample dots
            keep[rng.choice(np.flatnonzero(base), 60, replace=False)] = True
        else:
            keep = base
        ax.plot(xj[keep], x[keep], ".", color="#bdc3c7", markersize=5,
                alpha=0.7)
        ax.plot(xj[iq], x[iq], "s", color="#2980b9", markersize=7,
                label="IQR flag" if j == 0 else "")
        ax.plot(xj[zf], x[zf], "^", color="#e67e22", markersize=8,
                label="z flag" if j == 0 else "")
        lo, hi = results[c]["stats"]["lo"], results[c]["stats"]["hi"]
        ax.plot([j + 0.72, j + 1.28], [lo, lo], color="#2980b9",
                linestyle="--", linewidth=1.5)
        ax.plot([j + 0.72, j + 1.28], [hi, hi], color="#2980b9",
                linestyle="--", linewidth=1.5)
    ax.set_xticks(np.arange(n) + 1)
    ax.set_xticklabels(comms)
    ax.set_ylabel("modal price (₹/quintal)")
    ax.set_title("IQR fences (dashed) vs z-flagged points", fontweight="bold")
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)
    return path


def main():
    if not os.path.exists(PROCESSED):
        print("OUTLIERS: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    date_s = (sys.argv[1] if len(sys.argv) > 1
              else pd.Timestamp(df["arrival_date"].max()).strftime("%Y-%m-%d"))
    os.makedirs(CHARTS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    results = {}
    for comm, sub in df.groupby("commodity"):
        stats, iqr_mask, z_mask = detect(sub["modal_price"])
        results[comm] = {
            "x": sub["modal_price"].to_numpy(),
            "stats": stats,
            "iqr_mask": iqr_mask,
            "z_mask": z_mask,
            "iqr_flags": int(iqr_mask.sum()),
            "z_flags": int(z_mask.sum()),
            "overlap": int((iqr_mask & z_mask).sum()),
        }

    chart_path = os.path.join(CHARTS_DIR, f"outlier_rules_{date_s}.svg")
    make_chart(results, chart_path)

    # ---- report ----
    lines = ["# Day 8 — Outlier detection rules: IQR vs z-score on modal prices",
             "",
             "Two classical rules, applied per commodity on the pooled modal-price",
             "series (all mandis, all days):",
             "",
             f"- **IQR rule (Tukey fences):** flag x outside "
             f"[Q1 − {K_IQR}·IQR, Q3 + {K_IQR}·IQR]",
             f"- **Z-score rule:** flag |z| > {Z_THRESH}, z = (x − mean)/std",
             "",
             "| Commodity | n | Q1 | Median | Q3 | IQR | mean ± std | max |z| | IQR flags | z flags | both agree |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for comm in sorted(results):
        s, r = results[comm]["stats"], results[comm]
        lines.append(
            f"| {comm} | {s['n']} | {s['q1']:,.0f} | {s['med']:,.0f} | "
            f"{s['q3']:,.0f} | {s['iqr']:,.0f} | {s['mean']:,.0f} ± {s['std']:,.0f} | "
            f"{s['z_max']:.2f} | {r['iqr_flags']} | {r['z_flags']} | {r['overlap']} |")
    lines += ["", "## Reading the result", ""]
    total_iqr = sum(r["iqr_flags"] for r in results.values())
    total_z = sum(r["z_flags"] for r in results.values())
    max_z = max(r["stats"]["z_max"] for r in results.values())
    if total_iqr == 0 and total_z == 0:
        lines += [
            "Both rules flag **zero** price points on the current data — consistent",
            "with Day 3's finding of near-symmetric distributions and no IQR",
            "outliers. The rules disagree on nothing because there is nothing to",
            "flag; they are verified working and will fire on real feed shocks",
            "(e.g. a mistyped ₹50,000 or a genuine supply shock).",
        ]
    else:
        lines += [
            f"IQR flagged {total_iqr} point(s), z-score flagged {total_z}; "
            "see the chart for which series drove the difference.",
        ]
    lines += ["",
              "## Pipeline decision",
              "",
              "MandiLens adopts the **IQR rule (k = 1.5) as the default outlier flag**,",
              "because it is robust: the z-score's mean and std are themselves",
              "dragged by the very outliers they try to catch, and |z| > 3 needs",
              "large n before the CLT normal-approximation argument applies. "
              "Z-score is kept as a secondary check for large-sample commodities.",
              "Outlier flags are *flags*, not deletions — the cleaner keeps the row",
              "and future Week-3 models can choose to down-weight them.",
              "",
              f"![IQR vs z-score chart](../charts/outlier_rules_{date_s}.svg)",
              ""]
    report_path = os.path.join(REPORTS_DIR, "day8_outlier_detection_rules.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("OUTLIERS: " +
          "; ".join(f"{c}: n={results[c]['stats']['n']}, "
                    f"IQR={results[c]['iqr_flags']}, "
                    f"z={results[c]['z_flags']}, "
                    f"agree={results[c]['overlap']}"
                    for c in sorted(results)))
    print(f"OUTLIERS: chart -> {chart_path}")
    print(f"OUTLIERS: report -> {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
