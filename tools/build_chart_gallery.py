#!/usr/bin/env python3
"""Build CHART_GALLERY.md — a refreshable gallery of every SVG chart in charts/.

Groups charts by their daily-analysis family (trend, movers, and the named
per-day analyses), newest first within each family, and links each chart
image. Re-runnable: `python3 tools/build_chart_gallery.py`.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
OUT = os.path.join(BASE_DIR, "CHART_GALLERY.md")

FAMILIES = [
    ("price_trends", "Daily price trends"),
    ("top_movers", "Daily top movers"),
    ("price_trend_animated", "Animated price trend (Day 13)"),
    ("outlier_rules", "Outlier-detection rules (Day 8)"),
    ("volatility_index", "Commodity volatility index (Day 9)"),
    ("msp_gap", "MSP gap analysis (Day 10)"),
    ("arrival_price_dynamics", "Arrival vs price dynamics (Day 11)"),
    ("weekday_effects", "Weekday effects (Day 12)"),
    ("arrival_gaps", "Arrival-date gaps (Day 5)"),
    ("variety_premiums", "Variety & grade premiums (Day 6)"),
    ("state_heatmap", "Geographic spread heatmap (Day 4)"),
    ("distributions", "Price distributions (Day 3)"),
    ("eda_distributions", "Week-1 EDA distributions (Day 7)"),
    ("eda_rows_per_day", "Week-1 EDA rows per day (Day 7)"),
    ("coverage_matrix", "Missing-data coverage matrix (Day 2)"),
]


def family_of(name):
    stem = name[:-4]  # strip .svg
    for prefix, _ in FAMILIES:
        if stem.startswith(prefix):
            return prefix
    return "other"


def date_of(name):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else ""


def main():
    charts = sorted(
        (f for f in os.listdir(CHARTS_DIR) if f.endswith(".svg")),
        key=lambda f: (family_of(f), date_of(f)),
        reverse=False,
    )
    grouped = {}
    for f in charts:
        grouped.setdefault(family_of(f), []).append(f)

    lines = [
        "# MandiLens — Chart Gallery",
        "",
        "Every SVG chart the pipeline has produced, grouped by analysis family,",
        "newest first within each family. Regenerate with",
        "`python3 tools/build_chart_gallery.py`.",
        "",
    ]
    order = [p for p, _ in FAMILIES] + (["other"] if "other" in grouped else [])
    for prefix in order:
        files = grouped.get(prefix)
        if not files:
            continue
        title = dict(FAMILIES).get(prefix, "Other charts")
        lines.append(f"## {title}")
        lines.append("")
        for f in sorted(files, key=date_of, reverse=True):
            d = date_of(f) or "undated"
            lines.append(f"### {f} ({d})")
            lines.append("")
            lines.append(f"![{f}](charts/{f})")
            lines.append("")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"wrote {OUT} with {len(charts)} charts in {len(grouped)} families")


if __name__ == "__main__":
    main()
