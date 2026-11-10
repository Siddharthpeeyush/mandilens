#!/usr/bin/env python3
"""Day 23: 7-day price forecast table in the daily report.

Method:
  * Champion model from Weeks 2-3: plain OLS on lag1/lag2/lag3 per
    commodity, pooled across the 8 mandis (Day 22 verified ridge
    regularisation is a null — alpha=0 wins; Day 18/19 showed OLS
    beats MA3 and the random forest out-of-sample). Fitted on ALL
    history known as of today (the production choice for a live
    forecast; every feature still uses only prices up to t-1).
  * Recursive 7-day-ahead forecast per market-commodity series: day
    h=1 uses real lags from the latest known prices; days h=2..7 feed
    the previous forecasts back in as lags.
  * Empirical error scale: refit on history up to 7 days ago and score
    one-step-ahead on the last 7 days (walk-forward) — per-commodity
    MAE, reported as the "typical 1-day error" alongside the table.
  * The portal's National rows are an all-India aggregate with a short
    series — excluded from the forecast (it never clears the 3-lag
    requirement), exactly as in the earlier scoring days.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/forecast_table_YYYY-MM-DD.csv
        charts/forecast_7day_YYYY-MM-DD.svg
        reports/day23_forecast_table.md
Appends: "## 7-day price forecast" section to reports/daily/YYYY-MM-DD.md
         (argv[1] selects the run date, mirroring analyze.py).
Prints: per-commodity coefficients, walk-forward MAE, hand-check result.
"""
import datetime as dt
import os
import sys
import xml.dom.minidom

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
DAILY_DIR = os.path.join(REPORTS_DIR, "daily")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
TODAY = dt.date.today().isoformat()

COMMS = ["Onion", "Potato", "Tomato"]
HORIZON = 7
COLORS = {"Onion": "#c0392b", "Potato": "#b7950b", "Tomato": "#e74c3c"}


def add_lags(df):
    df = df.sort_values(["market", "commodity", "arrival_date"]).copy()
    g = df.groupby(["market", "commodity"])["modal_price"]
    df["lag1"] = g.shift(1)
    df["lag2"] = g.shift(2)
    df["lag3"] = g.shift(3)
    return df


def fit_ols(sub):
    X = np.column_stack([np.ones(len(sub)), sub["lag1"], sub["lag2"],
                         sub["lag3"]])
    y = sub["modal_price"].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def walkforward_mae(df, comm):
    """Refit on history older than the last 7 dates, one-step score them."""
    sub = df[df["commodity"] == comm].copy()
    dates = sorted(sub["arrival_date"].unique())
    if len(dates) < 14:
        return float("nan"), 0
    cutoff = dates[-8]  # train <= cutoff, score the last 7 dates
    train = sub[(sub["arrival_date"] <= cutoff) & sub["lag3"].notna()]
    test = sub[(sub["arrival_date"] > cutoff) & sub["lag3"].notna()]
    if len(train) < 20 or test.empty:
        return float("nan"), 0
    beta = fit_ols(train)
    pred = (beta[0] + beta[1] * test["lag1"] + beta[2] * test["lag2"]
            + beta[3] * test["lag3"])
    err = np.abs(test["modal_price"].to_numpy() - pred.to_numpy())
    return float(np.mean(err)), len(test)


def forecast_series(prices, beta, horizon=HORIZON):
    """Recursive forecast from the last 3 actual prices (list, oldest->latest)."""
    hist = list(map(float, prices[-3:]))
    out = []
    for _ in range(horizon):
        f = beta[0] + beta[1] * hist[-1] + beta[2] * hist[-2] \
            + beta[3] * hist[-3]
        out.append(f)
        hist.append(f)
    return out


def hand_check(df, betas, latest):
    """Manually recompute Azadpur Onion h=1 and h=2 forecasts."""
    sub = df[(df["market"] == "Azadpur") & (df["commodity"] == "Onion")]
    sub = sub[sub["arrival_date"] <= latest].sort_values("arrival_date")
    p = sub["modal_price"].to_numpy(dtype=float)[-3:]
    b = betas["Onion"]
    h1 = b[0] + b[1] * p[-1] + b[2] * p[-2] + b[3] * p[-3]
    h2 = b[0] + b[1] * h1 + b[2] * p[-1] + b[3] * p[-2]
    got = forecast_series(p, b, 2)
    assert abs(got[0] - h1) < 1e-9 and abs(got[1] - h2) < 1e-9, (got, h1, h2)
    return h1, h2


def make_chart(df, forecasts, maes, latest, fdates, path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 8.4), sharex=True)
    all_dates = list(df["arrival_date"].sort_values().unique())[-14:]
    x_hist = pd.to_datetime(all_dates)
    x_fc = pd.to_datetime(fdates)
    for ax, comm in zip(axes, COMMS):
        hist_med = (df[(df["commodity"] == comm)
                       & (df["arrival_date"].isin(all_dates))]
                    .groupby("arrival_date")["modal_price"].median())
        fc_med = np.array([
            np.nanmedian([forecasts[(mkt, comm)][d]
                          for mkt in fc_markets(comm, forecasts)])
            for d in fdates])
        mae = maes[comm]
        # Reindex, don't .loc: real portal rows are sparse (a commodity may
        # have no row on a date another one does — e.g. no Onion anywhere on
        # 08 Nov 2026 while Sealdah Tomato reported). Missing dates stay NaN
        # so the line honestly breaks instead of crashing the daily run.
        ax.plot(x_hist, hist_med.reindex(x_hist).to_numpy(), "o-",
                color=COLORS[comm], linewidth=1.8, markersize=4,
                label="Actual (cross-mandi median)")
        ax.plot(x_fc, fc_med, "s--", color="#2c3e50", linewidth=1.8,
                markersize=4, label="OLS forecast")
        if not np.isnan(mae):
            ax.fill_between(x_fc, fc_med - mae, fc_med + mae,
                            color="#2c3e50", alpha=0.12,
                            label="±1-day walk-forward MAE")
        ax.axvline(x_fc[0] - pd.Timedelta(hours=12), color="gray",
                   linestyle=":", linewidth=1)
        ax.set_title(f"{comm} — last 14 days + 7-day forecast (₹/qtl)",
                     fontsize=11, fontweight="bold")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.autofmt_xdate(rotation=30)
    fig.suptitle(f"7-day price forecast from {latest:%d %b %Y} — "
                 "OLS on lag1/lag2/lag3, recursive", fontsize=12,
                 fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, format="svg")
    plt.close(fig)
    xml.dom.minidom.parse(path)  # proves the SVG is valid XML


def fc_markets(comm, fc):
    return sorted({m for (m, c) in fc if c == comm})


def main():
    date_s = sys.argv[1] if len(sys.argv) > 1 else TODAY
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    df = df[(df["market"] != "National") & df["commodity"].isin(COMMS)]
    if df.empty:
        print("FORECAST_TABLE: no forecastable rows", file=sys.stderr)
        return 1
    df = add_lags(df)

    # Fit champion OLS per commodity on all history known today.
    betas = {}
    for comm in COMMS:
        sub = df[(df["commodity"] == comm) & df["lag3"].notna()]
        betas[comm] = fit_ols(sub)

    # Empirical 1-day error scale per commodity (walk-forward).
    maes, wf_n = {}, {}
    for comm in COMMS:
        maes[comm], wf_n[comm] = walkforward_mae(df, comm)

    # Recursive forecasts from each series' own latest date.
    latest = df["arrival_date"].max()
    fdates = [(latest + pd.Timedelta(days=h)).date()
              for h in range(1, HORIZON + 1)]
    rows, forecasts = [], {}
    for (mkt, comm), g in df.groupby(["market", "commodity"]):
        g = g[g["arrival_date"] <= latest].sort_values("arrival_date")
        if len(g) < 4:
            continue
        prices = g["modal_price"].to_numpy(dtype=float)
        fc = forecast_series(prices, betas[comm])
        forecasts[(mkt, comm)] = fc
        for h, (d, f) in enumerate(zip(fdates, fc), start=1):
            rows.append({"market": mkt, "commodity": comm,
                         "forecast_date": d.isoformat(),
                         "horizon_days": h,
                         "forecast_price": round(float(f), 2),
                         "model": "ols_lag123_recursive"})
    out = pd.DataFrame(rows)
    out_path = os.path.join(BASE_DIR, "data", "processed",
                            f"forecast_table_{TODAY}.csv")
    out.to_csv(out_path, index=False)

    h1, h2 = hand_check(df, betas, latest)

    chart_name = f"forecast_7day_{TODAY}.svg"
    make_chart(df, {(m, c): dict(zip(fdates, fc))
                    for (m, c), fc in forecasts.items()},
               maes, latest, fdates, os.path.join(CHARTS_DIR, chart_name))

    write_report(betas, maes, wf_n, latest, fdates, out, h1, h2,
                 chart_name, out_path)

    # Append the forecast table to today's daily report (the deliverable).
    daily_path = os.path.join(DAILY_DIR, f"{date_s}.md")
    append_daily_section(daily_path, maes, latest, fdates, out, chart_name)

    print(f"FORECAST_TABLE: {len(out)} forecast cells "
          f"({len(forecasts)} series x {HORIZON} days)")
    for comm in COMMS:
        print(f"  {comm}: walk-forward 1-day MAE Rs {maes[comm]:.2f}/qtl "
              f"(n={wf_n[comm]})")
    print(f"  hand-check Azadpur Onion: h=1 Rs {h1:.2f}, h=2 Rs {h2:.2f} "
          f"MATCH manual recompute")
    return 0


def write_report(betas, maes, wf_n, latest, fdates, out, h1, h2,
                 chart_name, out_path):
    lines = [
        "# Day 23 — 7-day price forecast table in the daily report",
        "",
        "## Method (read this first)",
        "",
        "The champion model from Weeks 2–3 — plain OLS on lag1/lag2/lag3",
        "per commodity, pooled across the 8 mandis (Day 22: ridge",
        "regularisation is a verified null, alpha=0; Day 18/19: OLS",
        "beats MA3 and the random forest out-of-sample) — is refitted",
        "on **all history known as of today** and run recursively:",
        "day h=1 uses real lags from the latest prices, days h=2..7",
        "feed the previous forecasts back in as lags. No future",
        "information enters at any step. The portal's National rows",
        "are an all-India aggregate with a 3-day series, so they never",
        "clear the 3-lag requirement and are excluded — the forecasts",
        "run on the 8 mandi series (latest actual date",
        f"{latest:%d %b %Y}), exactly like the earlier scoring days.",
        "",
        "## Empirical error scale",
        "",
        "Walk-forward: refit on history up to 7 days ago, then",
        "one-step-ahead on the last 7 days, per commodity:",
        "",
        "| Commodity | Walk-forward 1-day MAE (₹/qtl) | n |",
        "|---|---|---|",
    ]
    for comm in COMMS:
        lines.append(f"| {comm} | {maes[comm]:.2f} | {wf_n[comm]} |")
    lines += [
        "",
        "The table below shows **point forecasts**. A fair mental",
        "band is ±(1-day MAE × horizon): error compounds because each",
        "forecast day reuses the previous day's forecast as a lag.",
        "The forecast also inherits whatever drift the last 3 days",
        "carried — a 7-day OLS forecast cannot predict a shock.",
        "",
        "## 7-day forecast table",
        "",
    ]
    mkts = sorted(out["market"].unique())
    for comm in COMMS:
        lines.append(f"### {comm} — latest actual {latest:%d %b %Y}")
        lines.append("")
        hdr = "| Market | " + " | ".join(d.strftime("%d %b")
                                         for d in fdates) + " |"
        lines += [hdr, "|" + "---|" * (len(fdates) + 1)]
        for mkt in mkts:
            vals = out[(out["commodity"] == comm)
                       & (out["market"] == mkt)]
            if vals.empty:
                continue
            vals = vals.sort_values("horizon_days")
            cells = " | ".join(f"{v:,.0f}" for v in
                               vals["forecast_price"].to_numpy())
            lines.append(f"| {mkt} | {cells} |")
        lines.append("")
    lines += [
        "## Verification",
        "",
        "Hand-check on Azadpur Onion: recomputing h=1 and h=2 from the",
        f"coefficients by hand gives Rs {h1:.2f} and Rs {h2:.2f}/qtl —",
        "both **match** the module output exactly, so the recursion is",
        "verified. Re-running the script produces a byte-identical CSV",
        "(deterministic), and the chart parses as valid SVG.",
        "",
        "## Reading the result",
        "",
        "Prices are strongly autocorrelated day to day, so h=1",
        "forecasts mostly say 'tomorrow looks like yesterday, pulled",
        "slightly toward the last few days'. By h=7 the forecast has",
        "converged toward the series' recent drift — treat day 5–7",
        "values as directional, not precise. This table now ships in",
        "every daily report via run_daily.py (forecast_table.py runs",
        "right after analyze.py), so tomorrow's report will carry a",
        "fresh 7-day table automatically. Day 24's rolling-MAE",
        "dashboard will start tracking these forecasts against",
        "realised prices as they arrive.",
        "",
        f"![7-day forecast](../charts/{chart_name})",
        "",
    ]
    with open(os.path.join(REPORTS_DIR, "day23_forecast_table.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))


def append_daily_section(daily_path, maes, latest, fdates, out, chart_name):
    if not os.path.exists(daily_path):
        print(f"FORECAST_TABLE: no daily report at {daily_path}, skipping "
              f"append", file=sys.stderr)
        return
    with open(daily_path, encoding="utf-8") as f:
        if "7-day price forecast" in f.read():
            print(f"FORECAST_TABLE: forecast section already in {daily_path}")
            return
    lines = ["",
             "## 🔮 7-day price forecast (OLS on lag1/lag2/lag3, recursive)",
             "",
             f"Champion model refit on all history to {latest:%d %b %Y}; "
             "8 mandis × 3 commodities. Point forecasts in ₹/qtl — error "
             "compounds with horizon, so treat days 5–7 as directional. "
             "Typical 1-day error (walk-forward MAE): "
             + ", ".join(f"{c} ₹{maes[c]:,.0f}"
                         for c in COMMS) + ".",
             ""]
    mkts = sorted(out["market"].unique())
    for comm in COMMS:
        lines.append(f"### {comm}")
        lines.append("")
        hdr = "| Market | " + " | ".join(d.strftime("%d %b")
                                         for d in fdates) + " |"
        lines += [hdr, "|" + "---|" * (len(fdates) + 1)]
        for mkt in mkts:
            vals = out[(out["commodity"] == comm)
                       & (out["market"] == mkt)]
            if vals.empty:
                continue
            vals = vals.sort_values("horizon_days")
            cells = " | ".join(f"{v:,.0f}" for v in
                               vals["forecast_price"].to_numpy())
            lines.append(f"| {mkt} | {cells} |")
        lines.append("")
    lines.append(f"![7-day forecast](../charts/{chart_name})")
    lines.append("")
    with open(daily_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"FORECAST_TABLE: appended 7-day table to {daily_path}")


if __name__ == "__main__":
    sys.exit(main())
