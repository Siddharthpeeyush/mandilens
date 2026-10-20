#!/usr/bin/env python3
"""Day 10: MSP gap analysis — market price vs MSP per commodity.

Method:
  1. Load the curated notified MSP table (src/msp_data.py, 2026-27 season,
     copied from the PIB press releases).
  2. Coverage audit: for each commodity in the MandiLens dataset, look up
     its notified MSP via alias matching. Report covered vs not-covered.
  3. Gap computation (only where an MSP exists): per mandi-day,
       gap = modal_price - MSP, gap_pct = gap / MSP;
     summary: median gap, share of mandi-days below MSP ("under support").
  4. Chart: notified MSPs by crop group + a panel showing dataset commodities
     with their market median and a "no notified MSP" mark. The panels are
     deliberately separate so nobody reads a vegetable price as a "gap".

Reads : data/processed/mandi_prices_clean.csv, src/msp_data.py
Writes: charts/msp_gap_YYYY-MM-DD.svg
        reports/day10_msp_gap_analysis.md
Prints: coverage audit table + key findings.
"""
import datetime as dt
import os

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"  # keep text as <text>: smaller, selectable
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from msp_data import MSP_TABLE, msp_for

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

GROUP_OF = {
    "Paddy (Common)": "Cereals", "Paddy (Grade A)": "Cereals",
    "Jowar (Hybrid)": "Cereals", "Jowar (Maldandi)": "Cereals",
    "Bajra": "Cereals", "Ragi": "Cereals", "Maize": "Cereals",
    "Wheat": "Cereals", "Barley": "Cereals",
    "Tur / Arhar": "Pulses", "Moong": "Pulses", "Urad": "Pulses",
    "Gram": "Pulses", "Lentil (Masur)": "Pulses",
    "Groundnut": "Oilseeds", "Sunflower Seed": "Oilseeds",
    "Soybean (Yellow)": "Oilseeds", "Sesamum": "Oilseeds",
    "Nigerseed": "Oilseeds", "Rapeseed & Mustard": "Oilseeds",
    "Safflower": "Oilseeds",
    "Cotton (Medium Staple)": "Commercial", "Jute": "Commercial",
    "Copra (Milling)": "Commercial",
}
GROUP_COLORS = {"Cereals": "#f6b73c", "Pulses": "#4caf50",
                "Oilseeds": "#7b6cf6", "Commercial": "#ef6c00"}


def coverage_audit(df):
    rows = []
    for comm in sorted(df["commodity"].unique()):
        hit = msp_for(comm)
        median = df.loc[df["commodity"] == comm, "modal_price"].median()
        if hit is None:
            rows.append({"commodity": comm, "covered": False, "crop": None,
                         "msp": None, "season": None, "median_modal": median})
        else:
            canonical, msp, season = hit
            rows.append({"commodity": comm, "covered": True, "crop": canonical,
                         "msp": msp, "season": season, "median_modal": median})
    return pd.DataFrame(rows)


def gap_summary(df, audit):
    """Gap stats for covered commodities only; empty frame when none."""
    out = []
    for r in audit[audit["covered"]].itertuples():
        g = df[df["commodity"] == r.commodity].copy()
        g["gap"] = g["modal_price"] - r.msp
        g["gap_pct"] = g["gap"] / r.msp
        below = float((g["gap"] < 0).mean())
        out.append({"commodity": r.commodity, "crop": r.crop, "msp": r.msp,
                    "n_mandi_days": len(g),
                    "median_gap_rs": g["gap"].median(),
                    "median_gap_pct": g["gap_pct"].median(),
                    "share_days_below_msp": below})
    return pd.DataFrame(out)


def make_chart(audit, path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 6.6),
                                   gridspec_kw={"width_ratios": [1.35, 1]})
    fig.suptitle(f"Day 10 — MSP gap analysis, MandiLens (to {TODAY})",
                 fontsize=12, fontweight="bold")

    # Panel 1: notified MSPs 2026-27 by crop group
    order = sorted(MSP_TABLE, key=lambda t: (GROUP_OF.get(t[0], "ZZZ"), t[0]))
    names = [t[0] for t in order]
    values = [t[1] for t in order]
    colors = [GROUP_COLORS.get(GROUP_OF.get(t[0], ""), "#607d8b") for t in order]
    y = np.arange(len(names))
    ax1.barh(y, values, color=colors, alpha=0.85)
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlabel("Notified MSP (Rs/quintal)")
    ax1.set_title("Notified MSPs, marketing season 2026-27 (22 mandated crops)",
                  fontsize=10)
    for bar, v in zip(ax1.patches, values):
        ax1.text(v + 120, bar.get_y() + bar.get_height() / 2, f"{v:,}",
                 va="center", fontsize=7, color="#444")
    import matplotlib.patches as mpatches
    handles = [mpatches.Patch(color=c, label=g)
               for g, c in GROUP_COLORS.items()]
    ax1.legend(handles=handles, fontsize=8, loc="lower right")

    # Panel 2: dataset commodities — market medians, no-MSP mark
    audit2 = audit.sort_values("median_modal")
    y2 = np.arange(len(audit2))
    ax2.barh(y2, audit2["median_modal"], color="#90a4ae", alpha=0.9)
    ax2.set_yticks(y2)
    ax2.set_yticklabels(audit2["commodity"], fontsize=10)
    ax2.invert_yaxis()
    ax2.set_xlabel("Median modal market price (Rs/quintal)")
    ax2.set_title("MandiLens commodities — MSP coverage audit", fontsize=10)
    for i, r in enumerate(audit2.itertuples()):
        label = (f"median Rs {r.median_modal:,.0f}/qtl\n"
                 f"MSP: notified ({r.crop}, Rs {r.msp:,} — {r.season})"
                 if r.covered else
                 f"median Rs {r.median_modal:,.0f}/qtl\n"
                 "NO NOTIFIED MSP — gap undefined")
        color = "#2e7d32" if r.covered else "#c62828"
        ax2.text(r.median_modal + 60, i, label, va="center", fontsize=8,
                 color=color, fontweight="bold")
    ax2.text(0.98, 0.02,
             "Vegetables are not in the 22 mandated MSP crops — shown for\n"
             "scale only. A market-price-vs-MSP gap is not computable for them.",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=7.5,
             style="italic", color="#555")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(path, format="svg")
    plt.close(fig)


def write_report(audit, gaps, chart_name, path):
    n = len(audit)
    n_cov = int(audit["covered"].sum())
    lines = [
        "# Day 10 — MSP gap analysis: market price vs MSP per commodity",
        "",
        "Question: for each tracked commodity, is the market price above or",
        "below the government-notified Minimum Support Price — and where is the",
        "MSP floor actually biting?",
        "",
        "## The verified answer first",
        "",
        f"**{n_cov} of {n} tracked commodities have a notified MSP.** Onion,",
        "Potato and Tomato are vegetables; MSP is notified only for the 22",
        "mandated crops (14 Kharif + 6 Rabi + 2 commercial, Marketing Season",
        "2026-27, per the PIB press releases of 13 May 2026 and Oct 2025).",
        "Vegetables are covered instead by price-stabilisation schemes, not by",
        "an MSP floor — so **the market-price-vs-MSP gap is undefined for every",
        "commodity MandiLens currently tracks**. Reporting a 'gap' for them",
        "would mean inventing a benchmark that does not exist.",
        "",
        "## Coverage audit (alias-checked against the mandated list)",
        "",
        "| Commodity | Notified MSP? | Mandated crop | MSP (Rs/qtl) | Season | "
        "Median modal (Rs/qtl) |",
        "|---|---|---|---|---|---|",
    ]
    for r in audit.itertuples():
        lines.append(
            f"| {r.commodity} | {'YES' if r.covered else 'NO'} | "
            f"{r.crop or '—'} | "
            f"{f'{r.msp:,}' if r.msp else '—'} | {r.season or '—'} | "
            f"{r.median_modal:,.0f} |")
    lines += [""]

    if gaps.empty:
        lines += [
            "## Gap computation (skipped — no covered commodities)",
            "",
            "The gap machinery is built and ready: for any commodity with a",
            "notified MSP, it computes per mandi-day `gap = modal − MSP`,",
            "`gap_pct = gap / MSP`, the median gap, and the share of mandi-days",
            "trading below MSP ('under support'). It runs the moment a",
            "mandated crop enters the tracked set. See",
            "`src/msp_gap_analysis.py::gap_summary`.",
            "",
            "## How to make Day 10 live",
            "",
            "Add **one mandated crop to the MandiLens tracked set** — e.g.",
            "Tur/Arhar (MSP Rs 8,450/qtl) or Wheat (Rs 2,585/qtl), both routinely",
            "published in the Agmarknet tables. Then: today's portal 403 block",
            "aside, portal rows carry an `msp_rs` column that feeds this module",
            "directly. Recommended: Tur/Arhar, because pulses trade near their",
            "floor often enough to make the 'share of days under support'",
            "statistic meaningful.",
            "",
        ]
    else:
        lines += [
            "## Gap results (Rs/quintal, per mandi-day)",
            "",
            "| Commodity | MSP | Mandi-days | Median gap (Rs) | Median gap (%) | "
            "Days below MSP |",
            "|---|---|---|---|---|---|",
        ]
        for r in gaps.itertuples():
            lines.append(
                f"| {r.commodity} | {r.msp:,} | {r.n_mandi_days} | "
                f"{r.median_gap_rs:+,.0f} | {r.median_gap_pct:+.1%} | "
                f"{r.share_days_below_msp:.0%} |")
        lines += [""]

    lines += [
        "## Sources",
        "",
        "- Notified MSPs: PIB press release PRID 2260617 (Kharif 2026-27,",
        "  13 May 2026) and PIB PRID 2177219 (Rabi 2026-27). Copied exactly;",
        "  see `src/msp_data.py`.",
        "- Market prices: MandiLens cleaned dataset to",
        f"  {TODAY} ({n} commodities).",
        "- Data mode note: today's Agmarknet portal fetch was blocked (site-wide",
        "  403 bot-wall), so the pipeline ran on the seeded sample fallback —",
        "  the coverage audit is unaffected since MSPs are a published table,",
        "  not portal-derived.",
        "",
        f"![MSP gap analysis](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    audit = coverage_audit(df)
    gaps = gap_summary(df, audit)

    print("== MSP coverage audit ==")
    for r in audit.itertuples():
        hit = f"{r.crop} Rs {r.msp:,}/qtl ({r.season})" if r.covered else "NO NOTIFIED MSP"
        print(f"{r.commodity:8s} | median Rs {r.median_modal:,.0f}/qtl | {hit}")

    if gaps.empty:
        print("\nNo covered commodities — gap computation skipped (by design).")
    else:
        print("\n== Gap summary (modal - MSP, per mandi-day) ==")
        print(gaps.to_string(index=False))

    chart_name = f"msp_gap_{TODAY}.svg"
    make_chart(audit, os.path.join(CHARTS_DIR, chart_name))
    write_report(audit, gaps, chart_name,
                 os.path.join(REPORTS_DIR, "day10_msp_gap_analysis.md"))
    print(f"\nWROTE charts/{chart_name}, reports/day10_msp_gap_analysis.md")


if __name__ == "__main__":
    main()
