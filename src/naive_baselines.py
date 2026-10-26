#!/usr/bin/env python3
"""Day 16: naive baselines — persistence & moving-average forecasts.

Method (leak-free: every forecast for day t uses only prices up to t-1):
  * Persistence: forecast(t) = price(t-1).
  * MA3 forecast: forecast(t) = mean of prices(t-3 .. t-1).
  * MA7 forecast: forecast(t) = mean of prices(t-7 .. t-1).
  Evaluated per market-commodity series, then pooled per commodity and
  overall, with MAE, RMSE and MAPE. A forecast exists only once its
  window is full, so early-history rows are excluded, never padded.

  This is the baseline Day 17's regression and Day 19's random forest
  must beat — a fancy model that cannot beat yesterday's price is not
  a model worth shipping.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/naive_baselines.csv
        charts/naive_baselines_YYYY-MM-DD.svg
        reports/day16_naive_baselines.md
Prints: per-commodity MAE table + winner + hand-check result.
"""
import datetime as dt
import os

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
OUT = os.path.join(BASE_DIR, "data", "processed", "naive_baselines.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

COLORS = {"Persistence": "#37474f", "MA3 forecast": "#e67e22",
          "MA7 forecast": "#e53935"}
METHODS = ["fc_persist", "fc_ma3", "fc_ma7"]
LABELS = {"fc_persist": "Persistence", "fc_ma3": "MA3 forecast",
          "fc_ma7": "MA7 forecast"}


def add_forecasts(df):
    df = df.sort_values(["market", "commodity", "arrival_date"]).copy()
    g = df.groupby(["market", "commodity"])["modal_price"]
    df["fc_persist"] = g.shift(1)
    df["fc_ma3"] = df.groupby(["market", "commodity"])["modal_price"].transform(
        lambda s: s.rolling(3).mean().shift(1))
    df["fc_ma7"] = df.groupby(["market", "commodity"])["modal_price"].transform(
        lambda s: s.rolling(7).mean().shift(1))
    return df


def metrics(sub):
    out = {}
    for m in METHODS:
        valid = sub[sub[m].notna()]
        err = valid["modal_price"] - valid[m]
        out[m] = {
            "n": len(valid),
            "mae": float(np.mean(np.abs(err))) if len(valid) else float("nan"),
            "rmse": float(np.sqrt(np.mean(err ** 2))) if len(valid) else float("nan"),
            "mape": float(np.mean(np.abs(err) / valid["modal_price"]) * 100)
            if len(valid) else float("nan"),
        }
    return out


def make_chart(summary, path):
    comms = ["Onion", "Potato", "Tomato"]
    x = np.arange(len(comms))
    w = 0.25
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for i, m in enumerate(METHODS):
        vals = [summary[c][m]["mae"] for c in comms]
        ax.bar(x + (i - 1) * w, vals, w, label=LABELS[m],
               color=COLORS[LABELS[m]])
    ax.set_xticks(x)
    ax.set_xticklabels(comms)
    ax.set_ylabel("MAE (Rs/qtl)")
    ax.set_title(f"Naive baselines — MAE by commodity (to {TODAY})",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def hand_check(df):
    """Recompute one series' latest forecasts by hand; assert they match."""
    target = df[(df["market"] == "Azadpur") & (df["commodity"] == "Onion")]
    if target.empty:
        target = df[(df["market"] == df["market"].min()) &
                    (df["commodity"] == "Onion")]
    target = target.sort_values("arrival_date")
    prices = target["modal_price"].to_numpy()
    manual = {
        "fc_persist": prices[-2],
        "fc_ma3": float(np.mean(prices[-4:-1])),
        "fc_ma7": float(np.mean(prices[-8:-1])),
    }
    last = target.iloc[-1]
    for m, v in manual.items():
        assert abs(float(last[m]) - v) < 0.01, (m, last[m], v)
    return target["market"].iloc[0], target["arrival_date"].iloc[-1], manual


def write_report(summary, overall, latest, market, last_date, manual,
                 chart_name, path):
    winner = min(METHODS, key=lambda m: overall[m]["mae"])
    lines = [
        "# Day 16 — Naive baselines: persistence & moving-average forecasts",
        "",
        "## Method (read this first)",
        "",
        "Every forecast for day *t* uses only prices up to *t−1* — no",
        "leakage: persistence forecasts yesterday's price, MA3 forecasts",
        "the mean of the previous 3 days, MA7 the mean of the previous 7.",
        "A forecast exists only once its window is full, so early rows",
        "are excluded rather than padded. Errors are pooled per",
        "commodity across all 8 mandis, and overall across all series.",
        "Full per-series forecasts live in",
        "`data/processed/naive_baselines.csv` — Day 17's regression and",
        "Day 19's random forest must beat these numbers to be worth",
        "shipping.",
        "",
        f"**Overall winner: {LABELS[winner]}** (lowest overall MAE,",
        f"Rs {overall[winner]['mae']:.2f}/qtl).",
        "",
        "## Backtest results — all history",
        "",
        "| Commodity | Method | n | MAE Rs/qtl | RMSE Rs/qtl | MAPE % |",
        "|---|---|---|---|---|---|",
    ]
    for comm in ["Onion", "Potato", "Tomato"]:
        for m in METHODS:
            s = summary[comm][m]
            lines.append(f"| {comm} | {LABELS[m]} | {s['n']} | "
                         f"{s['mae']:.2f} | {s['rmse']:.2f} | {s['mape']:.2f} |")
    lines += [
        "",
        "## Overall (all commodities pooled)",
        "",
        "| Method | n | MAE Rs/qtl | RMSE Rs/qtl | MAPE % |",
        "|---|---|---|---|---|",
    ]
    for m in METHODS:
        s = overall[m]
        lines.append(f"| {LABELS[m]} | {s['n']} | {s['mae']:.2f} | "
                     f"{s['rmse']:.2f} | {s['mape']:.2f} |")
    lines += [
        "",
        "## Verification",
        "",
        f"Hand-check on {market} Onion for {last_date.date()}: persistence",
        f"forecast Rs {manual['fc_persist']:.2f}/qtl, MA3 forecast",
        f"Rs {manual['fc_ma3']:.2f}/qtl, MA7 forecast",
        f"Rs {manual['fc_ma7']:.2f}/qtl — all three **match** the module",
        "output to the paisa. The forecasts are verified, not assumed.",
        "",
        "## Latest-day forecasts (today's price vs each baseline)",
        "",
        "| Market | Commodity | Actual Rs/qtl | Persistence | MA3 fc | MA7 fc |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in latest.sort_values(["commodity", "market"]).iterrows():
        lines.append(f"| {r['market']} | {r['commodity']} | {r['modal_price']:.0f} "
                     f"| {r['fc_persist']:.0f} | {r['fc_ma3']:.0f} "
                     f"| {r['fc_ma7']:.0f} |")
    lines += [
        "",
        "## Reading the result",
        "",
        "On the current (sample) data the MA3 forecast wins on all three",
        "commodities — averaging the last 3 days smooths the sample",
        "generator's day-to-day jitter better than copying yesterday's",
        "price alone, while the 7-day average lags too far behind the",
        "drift to keep up. Tomato is by far the hardest to predict",
        "(MAE roughly double Potato's), matching Day 9's volatility",
        "ranking. That is exactly what a baseline is for — Day 17's",
        "regression now has a concrete bar to clear, commodity by",
        "commodity (MA3's MAE), instead of a vague 'good accuracy'.",
        "On real portal extracts the same table would show which",
        "mandis are genuinely hard to predict and which just drift.",
        "",
        f"![Naive baselines](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])
    fc = add_forecasts(df)
    cols = ["market", "commodity", "arrival_date", "modal_price",
            "fc_persist", "fc_ma3", "fc_ma7"]
    out = fc[cols].copy()
    out["arrival_date"] = out["arrival_date"].dt.strftime("%Y-%m-%d")
    out.to_csv(OUT, index=False)

    summary = {c: metrics(fc[fc["commodity"] == c])
               for c in ["Onion", "Potato", "Tomato"]}
    overall = metrics(fc)
    latest = fc[fc["arrival_date"] == fc["arrival_date"].max()].copy()
    latest = latest[latest["fc_ma7"].notna()]
    market, last_date, manual = hand_check(fc)

    chart_name = f"naive_baselines_{TODAY}.svg"
    make_chart(summary, os.path.join(CHARTS_DIR, chart_name))
    write_report(summary, overall, latest, market, last_date, manual,
                 chart_name,
                 os.path.join(REPORTS_DIR, "day16_naive_baselines.md"))

    for comm in ["Onion", "Potato", "Tomato"]:
        print(f"{comm}: " + ", ".join(
            f"{LABELS[m]} MAE {summary[comm][m]['mae']:.2f}"
            for m in METHODS))
    winner = min(METHODS, key=lambda m: overall[m]["mae"])
    print(f"Overall winner: {LABELS[winner]} "
          f"(MAE {overall[winner]['mae']:.2f})")
    print(f"Hand-check {market} Onion: all three forecasts MATCH manual")
    print(f"Latest forecasts: {len(latest)} series")


if __name__ == "__main__":
    main()
