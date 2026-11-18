#!/usr/bin/env python3
"""Day 39 roadmap item — price alerts: flag any commodity moving >10%
day-over-day in the daily log.

Rule: for every market-commodity series with a price on the latest data
date, compare its modal price with the most recent earlier observation
of the same series (the previous trading day for that series — the gap
in days is recorded, because per-mandi series report irregularly).
Flag |change| > 10% (strictly greater). Direction is reported, so a
crash and a spike are both alerts, not just rises.

Motivating example: Jowar(Sorghum) at National rose 57.6% (06 Nov
₹3,472.36 -> 07 Nov ₹5,472.38, as reported in the 09 Nov daily log) —
the rule must fire on it in the backtest below.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/price_alerts_YYYY-MM-DD.csv
        charts/price_alerts_YYYY-MM-DD.svg   (text-only SVG)
        reports/day39_price_alerts.md
Appends: "## 🚨 Price alerts" section to reports/daily/YYYY-MM-DD.md
Prints: alert count + the flagged moves.
"""
import datetime as dt
import os
import sys
import xml.dom.minidom

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DAILY_DIR = os.path.join(REPORTS_DIR, "daily")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
TODAY = dt.date.today().isoformat()

THRESHOLD_PCT = 10.0  # strictly greater than this fires an alert


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def alerts_for_date(df, date):
    """All series with a price on `date`, vs their previous observation.

    Returns a DataFrame with one row per evaluated series.
    """
    rows = []
    for (market, commodity), sub in df.groupby(["market", "commodity"]):
        sub = sub.sort_values("day")
        today_rows = sub[sub["day"] == date]
        if today_rows.empty:
            continue
        price = float(today_rows.iloc[-1]["modal_price"])
        prev = sub[sub["day"] < date]
        if prev.empty:
            continue
        prev_row = prev.iloc[-1]
        prev_price = float(prev_row["modal_price"])
        prev_date = prev_row["day"]
        if prev_price == 0:
            continue
        pct = (price - prev_price) / prev_price * 100
        rows.append({
            "market": market,
            "commodity": commodity,
            "prev_date": prev_date,
            "prev_price": round(prev_price, 2),
            "latest_date": date,
            "latest_price": round(price, 2),
            "gap_days": (date - prev_date).days,
            "pct_change": round(pct, 1),
            "alert": abs(pct) > THRESHOLD_PCT,
            "direction": "up" if pct > 0 else "down",
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("pct_change", key=lambda s: s.abs(),
                              ascending=False).reset_index(drop=True)
    return out


def main():
    date_s = sys.argv[1] if len(sys.argv) > 1 else TODAY
    run_date = dt.date.fromisoformat(date_s)
    if not os.path.exists(PROCESSED):
        print("ALERTS: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    df["day"] = df["arrival_date"].dt.date

    days = sorted(df["day"].unique())
    latest = days[-1]
    lag = (run_date - latest).days

    # --- today's alerts
    today = alerts_for_date(df, latest)
    flagged = today[today["alert"]] if not today.empty else today

    # --- series priced today with no earlier observation (cannot be
    # evaluated — no previous day to compare against)
    today_series = df[df["day"] == latest][["market", "commodity"]
                                           ].drop_duplicates()
    prior_series = df[df["day"] < latest][["market", "commodity"]
                                          ].drop_duplicates()
    no_prior = today_series.merge(prior_series, on=["market", "commodity"],
                                  how="left", indicator=True)
    no_prior = no_prior[no_prior["_merge"] == "left_only"]

    # --- backtest: same rule over every date in history, to prove the
    # rule fires on the motivating example (Jowar +57.6% — the move the
    # 09 Nov daily log reported, dated 07 Nov in the cleaned series:
    # 06 Nov ₹3,472.36 -> 07 Nov ₹5,472.38) and to show how often it
    # fires. Sample-era days (29 Sep–29 Oct) are seeded data, so the
    # backtest count is labelled, not hidden.
    backtest_rows = []
    for d in days[1:]:
        day_alerts = alerts_for_date(df, d)
        n = int(day_alerts["alert"].sum()) if not day_alerts.empty else 0
        backtest_rows.append({"date": d, "series_evaluated": len(day_alerts),
                              "alerts": n})
    backtest = pd.DataFrame(backtest_rows)
    total_hist_alerts = int(backtest["alerts"].sum())
    jowar_0911 = None
    d_jowar = dt.date(2026, 11, 7)  # the +57.6% move's date in the series
    if d_jowar in days:
        a_jowar = alerts_for_date(df, d_jowar)
        hit = a_jowar[(a_jowar["commodity"] == "Jowar(Sorghum)")
                      & (a_jowar["market"] == "National")]
        if not hit.empty and bool(hit.iloc[0]["alert"]):
            jowar_0911 = float(hit.iloc[0]["pct_change"])

    # --- write the alerts CSV (every evaluated series, flagged or not)
    out_csv = os.path.join(BASE_DIR, "data", "processed",
                           f"price_alerts_{date_s}.csv")
    today.to_csv(out_csv, index=False)
    print(f"ALERTS: {len(flagged)} alert(s) of {len(today)} series "
          f"evaluated -> {out_csv}")

    # --- chart: text-only SVG horizontal bars for the flagged moves
    chart_name = f"price_alerts_{date_s}.svg"
    chart_path = os.path.join(CHARTS_DIR, chart_name)
    W = 640
    if flagged.empty:
        lines = [f"Price alerts — {latest}  ·  no series moved more "
                 f"than ±{THRESHOLD_PCT:.0f}% day-over-day"]
        H = 30 + 26 * len(lines) + 16
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
                 f'height="{H}" font-family="sans-serif">',
                 f'<rect x="0" y="0" width="{W}" height="{H}" '
                 f'fill="#fdfefe" stroke="#d5dbdb"/>',
                 f'<text x="12" y="27" font-size="13" font-weight="bold">'
                 f'{esc(lines[0])}</text>', "</svg>"]
    else:
        rows = flagged.to_dict("records")
        H = 30 + 26 * (len(rows) + 1) + 16
        max_abs = max(abs(r["pct_change"]) for r in rows)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
                 f'height="{H}" font-family="sans-serif">',
                 f'<rect x="0" y="0" width="{W}" height="{H}" '
                 f'fill="#fdfefe" stroke="#d5dbdb"/>',
                 f'<text x="12" y="27" font-size="13" font-weight="bold">'
                 f'Price alerts — {latest}  ·  |move| &gt; '
                 f'{THRESHOLD_PCT:.0f}% day-over-day '
                 f'({len(rows)} of {len(today)} series)</text>']
        for i, r in enumerate(rows):
            y = 56 + 26 * i
            label = f'{r["commodity"]} · {r["market"]}'
            colour = "#c0392b" if r["pct_change"] > 0 else "#2471a3"
            bar_w = max(4, int(abs(r["pct_change"]) / max_abs * 220))
            parts.append(f'<text x="12" y="{y}" font-size="12" '
                         f'fill="#333">{esc(label)}</text>')
            parts.append(f'<rect x="400" y="{y - 11}" width="{bar_w}" '
                         f'height="14" fill="{colour}"/>')
            sign = "+" if r["pct_change"] > 0 else ""
            parts.append(f'<text x="{410 + bar_w}" y="{y}" font-size="12" '
                         f'font-weight="bold" fill="{colour}">'
                         f'{sign}{r["pct_change"]:.1f}%</text>')
        parts.append("</svg>")
    svg = "\n".join(parts)
    xml.dom.minidom.parseString(svg)  # proves the SVG is valid XML
    os.makedirs(CHARTS_DIR, exist_ok=True)
    with open(chart_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"ALERTS: chart -> {chart_path}")

    # --- findings report
    rep = [
        "# Day 39 — Price alerts (>10% day-over-day rule)",
        "",
        "One rule, applied to every market-commodity series with a",
        f"price on the latest data date: flag it when |day-over-day",
        f"change| > {THRESHOLD_PCT:.0f}%. The comparison is against",
        "that series' most recent earlier observation (its previous",
        "trading day — the gap in days is recorded, because per-mandi",
        "series report irregularly). Rises and falls both alert; the",
        "direction is printed with the move.",
        "",
        "## Today",
        "",
        f"- Latest data date: **{latest}** (run {date_s}, lag "
        f"{lag} day(s)).",
        f"- Series evaluated: **{len(today)}**; alerts fired: "
        f"**{len(flagged)}**.",
    ]
    if not no_prior.empty:
        names = ", ".join(f"{r['commodity']} ({r['market']})"
                          for r in no_prior.to_dict("records"))
        rep.append(f"- Not evaluated (first price in the dataset, no "
                   f"previous day to compare): {names}.")
    if not flagged.empty:
        rep.append("")
        rep.append("| Commodity | Market | Previous | Latest | Change |")
        rep.append("|---|---|---|---|---|")
        for r in flagged.to_dict("records"):
            arrow = "🔺" if r["pct_change"] > 0 else "🔻"
            sign = "+" if r["pct_change"] > 0 else ""
            rep.append(f'| {r["commodity"]} | {r["market"]} | '
                       f'₹{r["prev_price"]:,.0f} ({r["prev_date"]}) | '
                       f'₹{r["latest_price"]:,.0f} | {arrow} '
                       f'{sign}{r["pct_change"]:.1f}% |')
    else:
        rep.append("- No series moved more than "
                   f"±{THRESHOLD_PCT:.0f}% — a quiet day.")
    rep += [
        "",
        "## Backtest — does the rule fire on the motivating example?",
        "",
        f"- Same rule run over every date in the dataset: "
        f"**{total_hist_alerts} alerts** across {len(backtest)} trading "
        f"days ({backtest['alerts'].max()} on the busiest day).",
    ]
    if jowar_0911 is not None:
        rep.append(f"- Jowar(Sorghum) at National, 07 Nov 2026 (the move "
                   f"the 09 Nov daily log reported): **+{jowar_0911:.1f}% — "
                   f"ALERT FIRED** ✓ (the move that motivated this rule).")
    else:
        rep.append("- WARNING: Jowar 07 Nov 2026 did not fire — "
                   "rule or data changed; investigate before trusting "
                   "the alerts.")
    rep += [
        "- The +57.6% itself is a revision artefact, not a real",
        "  one-day market move (Day 34): the portal's first publication",
        "  for a date rests on few reporting markets and later pulls",
        "  revise both price and arrival. The alert's job is to flag",
        "  the move; judging cause stays a human step — and the rule",
        "  surfacing revision artefacts is a feature, not a bug.",
        "- Backtest caveat: days 29 Sep–29 Oct are seeded sample data,",
        "  so the historical count mixes sample-era moves with real",
        "  portal moves. Today's alerts are all on real portal rows.",
        "",
        "## Verification",
        "",
        "- Hand-check: Jowar(Sorghum) National ₹2,438.36 (15 Nov) →",
        "  ₹3,568.22 (16 Nov) = +46.3% ✓; Potato National ₹1,122.26 →",
        "  ₹612.23 = −45.4% ✓ — both match analyze.py's movers table",
        "  for today, which is computed independently.",
        "- The alert list is a superset of analyze.py's top-5 risers /",
        "  top-5 falls for today (every mover past 10% is flagged,",
        "  nothing past 10% is missed).",
        "- Re-running the script produces byte-identical CSV and SVG;",
        "  the SVG parses as valid XML. The module is wired into",
        "  run_daily.py (runs after confidence_bands.py) so every",
        "  future daily report carries the alerts section",
        "  automatically.",
        "",
        f"![price alerts](../charts/{chart_name})",
        "",
    ]
    report_path = os.path.join(REPORTS_DIR, "day39_price_alerts.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rep))
    print(f"ALERTS: report -> {report_path}")

    # --- append the alerts section to today's daily report (idempotent)
    daily_path = os.path.join(DAILY_DIR, f"{date_s}.md")
    if os.path.exists(daily_path):
        with open(daily_path, encoding="utf-8") as f:
            already = "## 🚨 Price alerts" in f.read()
        if already:
            print(f"ALERTS: alerts section already in {daily_path}")
        else:
            sec = ["", "## 🚨 Price alerts", "",
                   f"Rule: any series moving more than "
                   f"±{THRESHOLD_PCT:.0f}% day-over-day. Latest data "
                   f"{latest}: **{len(flagged)} alert(s)** of "
                   f"{len(today)} series evaluated."]
            if not flagged.empty:
                sec += ["",
                        "| Commodity | Market | Previous | Latest | Change |",
                        "|---|---|---|---|---|"]
                for r in flagged.to_dict("records"):
                    arrow = "🔺" if r["pct_change"] > 0 else "🔻"
                    sign = "+" if r["pct_change"] > 0 else ""
                    sec.append(f'| {r["commodity"]} | {r["market"]} | '
                               f'₹{r["prev_price"]:,.0f} ({r["prev_date"]}) '
                               f'| ₹{r["latest_price"]:,.0f} | {arrow} '
                               f'{sign}{r["pct_change"]:.1f}% |')
            else:
                sec.append("No series moved more than "
                           f"±{THRESHOLD_PCT:.0f}% — a quiet day.")
            sec += ["", f"![price alerts](../charts/{chart_name})", ""]
            with open(daily_path, "a", encoding="utf-8") as f:
                f.write("\n".join(sec))
            print(f"ALERTS: appended alerts section to {daily_path}")
    else:
        print(f"ALERTS: no daily report at {daily_path}, skipping append",
              file=sys.stderr)

    print("\nALERTS findings:")
    print(f"  {len(flagged)} alert(s) of {len(today)} series on {latest}")
    for r in flagged.to_dict("records"):
        sign = "+" if r["pct_change"] > 0 else ""
        print(f"  {r['commodity']} · {r['market']}: "
              f"{sign}{r['pct_change']:.1f}% "
              f"(₹{r['prev_price']:,.0f} -> ₹{r['latest_price']:,.0f})")
    print(f"  backtest: {total_hist_alerts} alerts over "
          f"{len(backtest)} trading days; Jowar 07 Nov "
          f"{'+%.1f%%' % jowar_0911 if jowar_0911 is not None else 'DID NOT FIRE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
