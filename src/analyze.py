#!/usr/bin/env python3
"""Daily analysis: price movers, cheapest/costliest mandis, insight of the day.

Reads : data/processed/mandi_prices_clean.csv
Writes: reports/daily/YYYY-MM-DD.md
Prints: one-line summary for the README updater.
"""
import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "daily")

FOCUS = ["Onion", "Potato", "Tomato"]


def _median_by_day(df, day):
    day_df = df[df["arrival_date"] == day]
    return (day_df.groupby(["commodity", "market"])["modal_price"]
            .median().rename("modal"))


def main():
    if not os.path.exists(PROCESSED):
        print("ANALYZE: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    days = sorted(df["arrival_date"].unique())
    latest = days[-1]
    prev = days[-2] if len(days) > 1 else None
    date_s = pd.Timestamp(latest).strftime("%Y-%m-%d")

    cur = _median_by_day(df, latest)
    lines = [f"# MandiLens daily report — {pd.Timestamp(latest):%d %b %Y}",
             "",
             f"- Rows analysed: **{len(df):,}** "
             f"({df[df['arrival_date'] == latest].shape[0]:,} for today)",
             f"- Coverage: **{df['market'].nunique()}** mandis across "
             f"**{df['state'].nunique()}** states",
             f"- Commodities tracked: {', '.join(sorted(df['commodity'].unique()))}",
             ""]

    movers = None
    if prev is not None:
        old = _median_by_day(df, prev)
        movers = pd.DataFrame({"today": cur, "yesterday": old}).dropna()
        movers["pct_change"] = ((movers["today"] - movers["yesterday"])
                                / movers["yesterday"] * 100).round(1)
        top = movers.sort_values("pct_change", ascending=False)
        lines += ["## Biggest movers vs previous trading day", "",
                  "| Commodity | Mandi | Yesterday (₹/q) | Today (₹/q) | Change |",
                  "|---|---|---|---|---|"]
        for (comm, mkt), row in top.head(5).iterrows():
            arrow = "🔺" if row["pct_change"] >= 0 else "🔻"
            lines.append(f"| {comm} | {mkt} | {row['yesterday']:,.0f} | "
                         f"{row['today']:,.0f} | {arrow} {row['pct_change']:+.1f}% |")
        lines += ["", "### Steepest falls",
                  "",
                  "| Commodity | Mandi | Yesterday (₹/q) | Today (₹/q) | Change |",
                  "|---|---|---|---|---|"]
        for (comm, mkt), row in top.tail(5).iloc[::-1].iterrows():
            arrow = "🔺" if row["pct_change"] >= 0 else "🔻"
            lines.append(f"| {comm} | {mkt} | {row['yesterday']:,.0f} | "
                         f"{row['today']:,.0f} | {arrow} {row['pct_change']:+.1f}% |")
        lines.append("")

    lines += ["## Cheapest vs costliest mandi (median modal price today)", "",
              "| Commodity | Cheapest mandi | ₹/q | Costliest mandi | ₹/q |",
              "|---|---|---|---|---|"]
    for comm in FOCUS:
        sub = cur.xs(comm, level="commodity") if comm in cur.index.get_level_values(0) else None
        if sub is None or sub.empty:
            continue
        cheap_mkt, cheap_px = sub.idxmin(), sub.min()
        dear_mkt, dear_px = sub.idxmax(), sub.max()
        lines.append(f"| {comm} | {cheap_mkt} | {cheap_px:,.0f} | "
                     f"{dear_mkt} | {dear_px:,.0f} |")
    lines.append("")

    if movers is not None and not movers.empty:
        (comm, mkt), row = max(movers.iterrows(),
                              key=lambda kv: abs(kv[1]["pct_change"]))
        direction = "rose" if row["pct_change"] >= 0 else "fell"
        lines += ["## 💡 Insight of the day", "",
                  f"{comm} at {mkt} {direction} "
                  f"{abs(row['pct_change']):.1f}% in a day "
                  f"(₹{row['yesterday']:,.0f} → ₹{row['today']:,.0f} per quintal) — "
                  f"the sharpest single-day move in today's data.", ""]

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"{date_s}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    n_movers = 0 if movers is None else len(movers)
    print(f"ANALYZE: report -> {report_path} ({n_movers} market-commodity pairs compared)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
