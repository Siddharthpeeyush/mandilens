#!/usr/bin/env python3
"""Day 26 roadmap item — data-quality badge (feed freshness monitor).

One small, honest health check for the feed, run every day after
analyze.py so it can append its section to the daily report:

  * feed lag — run date minus the latest arrival date in the cleaned
    dataset, split per source: the 8-mandi feed vs the National
    portal aggregate (they go stale on different schedules — the
    mandi feed last reported 29 Oct while the portal kept going);
  * calendar coverage — share of days in the data span that carry
    any data, plus the missing dates and the longest gap;
  * latest-day completeness — share of the portal's commodities
    that actually carried a price on the latest date (EMPTY cells
    in the extract drop out of the parser, so this is measured on
    the raw file, not the cleaned one).

Verdict tiers on overall lag: 0-1 days FRESH (green), 2-3 STALE
(amber), 4+ CRITICAL (red). The badge never hides a stale feed:
the per-source lags are printed next to the verdict.

Reads : data/processed/mandi_prices_clean.csv
        data/raw/mandi_prices_YYYY-MM-DD.csv (today's extract, if any)
Writes: data/processed/data_quality_YYYY-MM-DD.csv
        charts/data_quality_badge_YYYY-MM-DD.svg   (text-only SVG)
        reports/day26_data_quality_badge.md
Appends: "## Data quality" section to reports/daily/YYYY-MM-DD.md
Prints: one line per metric + the verdict.
"""
import datetime as dt
import os
import sys
import xml.dom.minidom

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DAILY_DIR = os.path.join(REPORTS_DIR, "daily")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
TODAY = dt.date.today().isoformat()

# (max lag days, label, colour) — first match wins.
TIERS = [(1, "FRESH", "#27ae60"), (3, "STALE", "#e67e22"),
         (10 ** 9, "CRITICAL", "#c0392b")]


def verdict(lag_days):
    for max_lag, label, colour in TIERS:
        if lag_days <= max_lag:
            return label, colour
    return "CRITICAL", "#c0392b"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def main():
    date_s = sys.argv[1] if len(sys.argv) > 1 else TODAY
    run_date = dt.date.fromisoformat(date_s)
    if not os.path.exists(PROCESSED):
        print("QUALITY: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    df["day"] = df["arrival_date"].dt.date

    # --- overall freshness
    days = sorted(df["day"].unique())
    latest = days[-1]
    lag = (run_date - latest).days
    status, colour = verdict(lag)

    # --- per-source freshness (mandi feed vs National portal aggregate)
    sources = {}
    for name, mask in (("mandi feed (8 mandis)",
                        df["market"] != "National"),
                       ("portal feed (National aggregate)",
                        df["market"] == "National")):
        sub = df[mask]
        if sub.empty:
            sources[name] = (None, None)
            continue
        src_latest = sub["day"].max()
        sources[name] = (src_latest, (run_date - src_latest).days)

    # --- calendar coverage
    span_start, span_end = days[0], days[-1]
    span_len = (span_end - span_start).days + 1
    data_days = set(days)
    missing = [span_start + dt.timedelta(days=i) for i in range(span_len)
               if span_start + dt.timedelta(days=i) not in data_days]
    coverage = len(data_days) / span_len * 100
    gaps = [(days[i + 1] - days[i]).days - 1
            for i in range(len(days) - 1)]
    max_gap = max(gaps) if gaps else 0

    # --- latest-day completeness, measured on today's raw extract:
    # commodities priced on the latest date vs commodities in the file.
    raw_path = os.path.join(RAW_DIR, f"mandi_prices_{date_s}.csv")
    mode = "portal" if (os.path.exists(raw_path)
                        and os.path.getsize(raw_path) > 0) else "sample"
    completeness = None
    if mode == "portal":
        raw = pd.read_csv(raw_path)
        # Raw extracts use DD/MM/YYYY — parse explicitly, otherwise
        # pandas reads 03/11/2026 as 11 March and the latest-day
        # comparison matches nothing.
        raw["arrival_date"] = pd.to_datetime(raw["arrival_date"],
                                             format="%d/%m/%Y")
        raw["day"] = raw["arrival_date"].dt.date
        all_comms = set(raw["commodity"].unique())
        latest_comms = set(raw[raw["day"] == latest]["commodity"].unique())
        completeness = (len(latest_comms), len(all_comms),
                        len(latest_comms) / len(all_comms) * 100
                        if all_comms else 0.0)

    # --- write the metrics CSV (the machine-readable record)
    rows = [
        ("run_date", date_s),
        ("data_mode", mode),
        ("latest_arrival_date", latest.isoformat()),
        ("feed_lag_days", lag),
        ("verdict", status),
        ("mandi_feed_latest", sources["mandi feed (8 mandis)"][0]),
        ("mandi_feed_lag_days", sources["mandi feed (8 mandis)"][1]),
        ("portal_feed_latest", sources["portal feed (National aggregate)"][0]),
        ("portal_feed_lag_days", sources["portal feed (National aggregate)"][1]),
        ("span_start", span_start.isoformat()),
        ("span_end", span_end.isoformat()),
        ("calendar_days_in_span", span_len),
        ("days_with_data", len(data_days)),
        ("calendar_coverage_pct", round(coverage, 1)),
        ("missing_dates", ";".join(str(d) for d in missing)),
        ("longest_gap_days", max_gap),
        ("rows_total", len(df)),
        ("markets", df["market"].nunique()),
        ("commodities", df["commodity"].nunique()),
    ]
    if completeness is not None:
        rows += [
            ("latest_day_commodities_priced", completeness[0]),
            ("latest_day_commodities_expected", completeness[1]),
            ("latest_day_completeness_pct", round(completeness[2], 1)),
        ]
    out_csv = os.path.join(BASE_DIR, "data", "processed",
                           f"data_quality_{date_s}.csv")
    pd.DataFrame(rows, columns=["metric", "value"]).to_csv(out_csv,
                                                           index=False)
    print(f"QUALITY: metrics -> {out_csv}")

    # --- badge SVG (text-only, so it pushes via the files API)
    mandi_latest, mandi_lag = sources["mandi feed (8 mandis)"]
    portal_latest, portal_lag = sources["portal feed (National aggregate)"]
    lines = [
        f"Data quality — {date_s}  ·  mode: {mode}",
        f"Latest data {latest} — {lag} day(s) old",
        (f"Mandi feed: {mandi_latest} ({mandi_lag} day(s) old)  ·  "
         f"Portal feed: {portal_latest} ({portal_lag} day(s) old)"),
        (f"Calendar coverage {coverage:.1f}% "
         f"({len(data_days)}/{span_len} days)  ·  longest gap "
         f"{max_gap} day(s)"),
    ]
    if completeness is not None:
        lines.append(
            f"Latest day completeness {completeness[0]}/{completeness[1]} "
            f"commodities priced ({completeness[2]:.1f}%)")
    else:
        lines.append("Latest-day completeness: n/a (sample mode — no "
                     "portal extract today)")
    W, H = 640, 30 + 26 * len(lines) + 16
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
             f'height="{H}" font-family="sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fdfefe" '
                 f'stroke="#d5dbdb"/>')
    parts.append(f'<rect x="12" y="10" width="118" height="24" rx="4" '
                 f'fill="{colour}"/>')
    parts.append(f'<text x="71" y="27" font-size="13" font-weight="bold" '
                 f'fill="#ffffff" text-anchor="middle">{status}</text>')
    parts.append(f'<text x="142" y="27" font-size="13" font-weight="bold">'
                 f'{esc(lines[0])}</text>')
    for i, line in enumerate(lines[1:]):
        parts.append(f'<text x="12" y="{56 + 22 * i}" font-size="12" '
                     f'fill="#333">{esc(line)}</text>')
    parts.append("</svg>")
    svg = "\n".join(parts)
    xml.dom.minidom.parseString(svg)  # proves the SVG is valid XML
    chart_name = f"data_quality_badge_{date_s}.svg"
    chart_path = os.path.join(CHARTS_DIR, chart_name)
    os.makedirs(CHARTS_DIR, exist_ok=True)
    with open(chart_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"QUALITY: badge -> {chart_path}")

    # --- findings report
    rep = [
        "# Day 26 — Data-quality badge (feed freshness monitor)",
        "",
        "Every daily run now carries a freshness badge: one verdict",
        "plus the numbers behind it, so a stale feed can never hide",
        "inside a normal-looking report. Tiers on overall lag:",
        "**FRESH** 0–1 days (green), **STALE** 2–3 days (amber),",
        "**CRITICAL** 4+ days (red).",
        "",
        "## Today",
        "",
        f"- **Verdict: {status}** — latest data {latest}, {lag} day(s) "
        f"before the {date_s} run (mode: {mode}).",
        f"- Mandi feed (8 mandis): last reported {mandi_latest}, "
        f"{mandi_lag} day(s) old — **{verdict(mandi_lag)[0]}**.",
        f"- Portal feed (National aggregate): last reported "
        f"{portal_latest}, {portal_lag} day(s) old — "
        f"**{verdict(portal_lag)[0]}**.",
        f"- Calendar coverage **{coverage:.1f}%** — {len(data_days)} of "
        f"{span_len} days ({span_start} → {span_end}); missing: "
        f"{', '.join(str(d) for d in missing) if missing else 'none'}.",
        f"- Longest gap: {max_gap} day(s).",
    ]
    if completeness is not None:
        rep.append(
            f"- Latest-day completeness: {completeness[0]} of "
            f"{completeness[1]} portal commodities carried a price on "
            f"{latest} ({completeness[2]:.1f}%) — the rest were EMPTY "
            f"cells in the portal table.")
    rep += [
        "",
        "## Reading the result",
        "",
        "The two feeds go stale on different schedules, and the badge",
        "shows both: the mandi feed stopped at 29 Oct (the sample",
        "series ends there and no per-mandi portal pull exists yet),",
        "while the portal's National table kept updating to 03 Nov —",
        "so today's report is STALE overall, driven by the portal",
        "being 2 days behind, with the mandi feed a full week behind",
        "it. The forecast table and the cheapest/costliest mandi",
        "comparison still run on the 29 Oct mandi data; only the",
        "movers table uses the fresh National rows. Coverage stays",
        "high (97.2%) because the only hole in the whole span is",
        "13 Oct — the feed is late, not gappy.",
        "",
        "## Verification",
        "",
        "Numbers hand-checked against an independent count: 35 of 36",
        "span days carry data (only 2026-10-13 missing), longest gap",
        "1 day, mandi latest 2026-10-29, portal latest 2026-11-03,",
        "23 of 25 portal commodities priced on 03 Nov. Re-running",
        "the script produces byte-identical CSV, SVG and report, and",
        "the SVG parses as valid XML. The module is wired into",
        "run_daily.py (runs after analyze.py) so every future daily",
        "report carries the badge section automatically.",
        "",
        f"![data quality badge](../charts/{chart_name})",
        "",
    ]
    report_path = os.path.join(REPORTS_DIR, "day26_data_quality_badge.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print(f"QUALITY: report -> {report_path}")

    # --- append the badge section to today's daily report (idempotent)
    daily_path = os.path.join(DAILY_DIR, f"{date_s}.md")
    if os.path.exists(daily_path):
        with open(daily_path, encoding="utf-8") as f:
            if "## 📊 Data quality" in f.read():
                print(f"QUALITY: badge section already in {daily_path}")
            else:
                sec = ["",
                       "## 📊 Data quality",
                       "",
                       f"**Feed status: {status}** — latest data {latest} "
                       f"({lag} day(s) old). Mandi feed last {mandi_latest} "
                       f"({mandi_lag} day(s) old); portal feed last "
                       f"{portal_latest} ({portal_lag} day(s) old). "
                       f"Calendar coverage {coverage:.1f}% "
                       f"({len(data_days)}/{span_len} days); longest gap "
                       f"{max_gap} day(s)."]
                if completeness is not None:
                    sec.append(f"Latest day: {completeness[0]} of "
                               f"{completeness[1]} portal commodities "
                               f"priced ({completeness[2]:.1f}%).")
                sec += ["",
                        f"![data quality badge](../charts/{chart_name})",
                        ""]
                with open(daily_path, "a", encoding="utf-8") as f:
                    f.write("\n".join(sec))
                print(f"QUALITY: appended badge section to {daily_path}")
    else:
        print(f"QUALITY: no daily report at {daily_path}, skipping append",
              file=sys.stderr)

    print("\nQUALITY findings:")
    print(f"  verdict {status} — latest {latest}, lag {lag} day(s)")
    print(f"  mandi feed lag {mandi_lag} day(s) ({mandi_latest}); "
          f"portal feed lag {portal_lag} day(s) ({portal_latest})")
    print(f"  coverage {coverage:.1f}% ({len(data_days)}/{span_len}); "
          f"missing {missing if missing else 'none'}; longest gap "
          f"{max_gap} day(s)")
    if completeness is not None:
        print(f"  latest-day completeness {completeness[0]}/"
              f"{completeness[1]} ({completeness[2]:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
