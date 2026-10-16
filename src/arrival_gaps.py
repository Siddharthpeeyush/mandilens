#!/usr/bin/env python3
"""Day 5 roadmap item — arrival-date gaps: how "daily" is the feed really?

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/arrival_gaps_YYYY-MM-DD.svg   (calendar strip per market)
        reports/day5_arrival_date_gaps.md     (findings)
Prints: summary lines to stdout.
"""
import datetime as dt
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FOCUS = ["Onion", "Potato", "Tomato"]
CELL, LABW, TOP = 30, 170, 46


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def main():
    if not os.path.exists(PROCESSED):
        print("GAPS: no processed data", file=sys.stderr)
        return 1
    date_s = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    df["day"] = df["arrival_date"].dt.date
    markets = sorted(df["market"].unique())

    # --- calendar-level coverage
    days_with_data = sorted(df["day"].unique())
    span_start, span_end = days_with_data[0], days_with_data[-1]
    calendar = []
    d = span_start
    while d <= span_end:
        calendar.append(d)
        d += dt.timedelta(days=1)
    data_days = set(days_with_data)
    missing_dates = [d for d in calendar if d not in data_days]
    coverage = len(data_days) / len(calendar) * 100

    # --- largest gap between consecutive data days
    gaps = [(days_with_data[i + 1] - days_with_data[i]).days - 1
            for i in range(len(days_with_data) - 1)]
    max_gap = max(gaps) if gaps else 0
    gap_idx = gaps.index(max_gap) if gaps else None

    # --- freshness: run date vs latest arrival date
    run_date = dt.date.fromisoformat(date_s)
    freshness = (run_date - span_end).days

    # --- weekday pattern
    df["weekday"] = df["arrival_date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    wd_days = (pd.Series([x.strftime("%A") for x in calendar])
               .value_counts())
    wd_data = (pd.Series([x.strftime("%A") for x in data_days])
               .value_counts())
    wd_rows = df["weekday"].value_counts()

    # --- per-market max gap (consecutive data days)
    mkt_gaps = {}
    for m in markets:
        md = sorted(df[df["market"] == m]["day"].unique())
        g = max(((md[i + 1] - md[i]).days - 1 for i in range(len(md) - 1)),
                default=0)
        mkt_gaps[m] = g

    # --- arrival_tonnes availability (portal schema vs legacy sample schema)
    has_tonnes = ("arrival_tonnes" in df.columns
                  and df["arrival_tonnes"].notna().sum())
    tonnes_days = sorted(df[df["arrival_tonnes"].notna()]["day"].unique()) \
        if has_tonnes else []

    # --- chart: calendar strip, one row per market
    W = LABW + CELL * len(calendar) + 24
    H = TOP + 24 * len(markets) + 56
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
             f'height="{H}" font-family="sans-serif">']
    parts.append(f'<text x="8" y="20" font-size="14" font-weight="bold">'
                 f'Feed freshness — reports received per mandi and calendar '
                 f'day (Day 5, {esc(date_s)})</text>')
    parts.append('<text x="8" y="38" font-size="11" fill="#555">'
                 'green = reported · red = feed gap (no mandi reported) · '
                 'orange = this mandi missed a reported day</text>')
    hit = set(zip(df["day"], df["market"]))
    for j, cal in enumerate(calendar):
        x = LABW + j * CELL
        lab = cal.strftime("%d")
        wd = cal.strftime("%a")
        parts.append(f'<text x="{x + CELL / 2}" y="{TOP - 24}" font-size="9" '
                     f'text-anchor="middle" fill="#333">{lab}</text>')
        parts.append(f'<text x="{x + CELL / 2}" y="{TOP - 12}" font-size="8" '
                     f'text-anchor="middle" fill="#888">{wd}</text>')
        parts.append(f'<rect x="{x + 2}" y="{TOP - 4}" width="{CELL - 4}" '
                     f'height="8" fill="{"#2ecc71" if cal in data_days else "#e74c3c"}"/>')
    for i, m in enumerate(markets):
        y = TOP + i * 24
        parts.append(f'<text x="8" y="{y + 16}" font-size="10">{esc(m)}</text>')
        for j, cal in enumerate(calendar):
            x = LABW + j * CELL
            if cal not in data_days:
                fill = "#e74c3c"      # feed-wide gap
            elif (cal, m) in hit:
                fill = "#2ecc71"      # reported
            else:
                fill = "#f39c12"      # this mandi missed a live day
            parts.append(f'<rect x="{x + 2}" y="{y + 4}" width="{CELL - 4}" '
                         f'height="16" fill="{fill}">'
                         f'<title>{esc(m)} · {cal} · '
                         f'{"reported" if (cal, m) in hit else "missing"}'
                         f'</title></rect>')
    parts.append(f'<text x="8" y="{H - 12}" font-size="11" fill="#333">'
                 f'{len(data_days)}/{len(calendar)} calendar days covered '
                 f'({coverage:.1f}%) · longest gap {max_gap} day(s) · '
                 f'latest data {span_end} ({freshness} day(s) before run date)'
                 f'</text>')
    parts.append("</svg>")
    os.makedirs(CHARTS_DIR, exist_ok=True)
    chart_path = os.path.join(CHARTS_DIR, f"arrival_gaps_{date_s}.svg")
    with open(chart_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"GAPS: chart -> {chart_path}")

    # --- report
    lines = [f"# Day 5 — Arrival-date gaps: how \"daily\" is the feed?",
             "",
             f"Checked {len(df):,} reports across {len(markets)} mandis × "
             f"{df['commodity'].nunique()} commodities, "
             f"{span_start} → {span_end}.",
             "",
             f"- **Calendar coverage: {coverage:.1f}%** — "
             f"{len(data_days)} of {len(calendar)} calendar days carry data.",
             f"- **Missing dates:** "
             f"{', '.join(str(x) for x in missing_dates) if missing_dates else '— none'}",
             f"- **Longest gap:** {max_gap} day(s)" +
             (f" ({days_with_data[gap_idx]} → {days_with_data[gap_idx + 1]})"
              if gap_idx is not None else ""),
             f"- **Feed freshness:** latest data is {span_end}; "
             f"that's {freshness} day(s) before the {date_s} run.",
             "",
             "## Weekday pattern",
             ""]
    for wd in order:
        have = int(wd_data.get(wd, 0))
        total = int(wd_days.get(wd, 0))
        rows = int(wd_rows.get(wd, 0))
        lines.append(f"- {wd}: data on {have}/{total} occurrences "
                     f"({rows:,} rows)")
    sundays_missing = wd_days.get("Sunday", 0) > wd_data.get("Sunday", 0)
    if sundays_missing:
        lines += ["", "Sundays are the weak spot — consistent with mandis "
                  "staying closed on Sundays."]
    lines += ["",
              "## Per-mandi longest gap",
              ""]
    for m in sorted(mkt_gaps, key=mkt_gaps.get, reverse=True):
        lines.append(f"- {m}: {mkt_gaps[m]} day(s)")
    if has_tonnes:
        lines += ["",
                  f"Arrival tonnages (portal schema) are present for "
                  f"{len(tonnes_days)} day(s): "
                  f"{', '.join(str(x) for x in tonnes_days)}; "
                  f"earlier days use the legacy sample schema without them."]
    lines += ["",
              f"![arrival gaps](../charts/arrival_gaps_{date_s}.svg)",
              ""]
    report_path = os.path.join(REPORTS_DIR, "day5_arrival_date_gaps.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"GAPS: report -> {report_path}")

    print("\nGAPS findings:")
    print(f"  calendar coverage {coverage:.1f}% ({len(data_days)}/{len(calendar)})")
    print(f"  missing dates: {missing_dates if missing_dates else 'none'}")
    print(f"  longest gap: {max_gap} day(s); per-mandi worst: "
          f"{max(mkt_gaps.values())} day(s)")
    print(f"  freshness: latest data {span_end}, {freshness} day(s) old")
    return 0


if __name__ == "__main__":
    sys.exit(main())
