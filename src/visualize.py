#!/usr/bin/env python3
"""Regenerate the daily charts.

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/price_trends_YYYY-MM-DD.png
        charts/top_movers_YYYY-MM-DD.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

FOCUS = ["Onion", "Potato", "Tomato"]
COLORS = {"Onion": "#c0392b", "Potato": "#b7950b", "Tomato": "#e74c3c"}


def main():
    if not os.path.exists(PROCESSED):
        print("VISUALIZE: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    latest = df["arrival_date"].max()
    # Output files are named for the RUN date (argv) so the README links always
    # resolve, even when the data's latest date lags behind.
    date_s = (sys.argv[1] if len(sys.argv) > 1
              else pd.Timestamp(latest).strftime("%Y-%m-%d"))
    os.makedirs(CHARTS_DIR, exist_ok=True)

    # 1) 14-day median modal-price trend per focus commodity
    trend = (df[df["commodity"].isin(FOCUS)]
             .groupby(["arrival_date", "commodity"])["modal_price"]
             .median().unstack())
    trend = trend.tail(14)
    fig, ax = plt.subplots(figsize=(10, 5))
    for comm in FOCUS:
        if comm in trend.columns:
            ax.plot(trend.index, trend[comm], marker="o",
                    label=comm, color=COLORS[comm], linewidth=2)
    ax.set_title("Median modal price across tracked mandis (₹/quintal)",
                 fontsize=13, fontweight="bold")
    ax.set_ylabel("₹ per quintal")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    trend_path = os.path.join(CHARTS_DIR, f"price_trends_{date_s}.png")
    fig.savefig(trend_path, dpi=130)
    trend_svg = os.path.join(CHARTS_DIR, f"price_trends_{date_s}.svg")
    fig.savefig(trend_svg, format="svg")
    plt.close(fig)

    # 2) Top day-on-day movers
    days = sorted(df["arrival_date"].unique())
    movers_path = None
    if len(days) > 1:
        prev = days[-2]
        cur = df[df["arrival_date"] == latest].groupby(["commodity", "market"])["modal_price"].median()
        old = df[df["arrival_date"] == prev].groupby(["commodity", "market"])["modal_price"].median()
        both = pd.DataFrame({"today": cur, "yesterday": old}).dropna()
        both["pct"] = (both["today"] - both["yesterday"]) / both["yesterday"] * 100
        top = both.sort_values("pct", ascending=False).head(8)
        labels = [f"{c} · {m}" for c, m in top.index]
        vals = top["pct"].values
        colors = ["#27ae60" if v >= 0 else "#c0392b" for v in vals]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.barh(labels[::-1], vals[::-1], color=colors[::-1])
        ax.set_title(f"Biggest single-day price moves — {pd.Timestamp(latest):%d %b %Y}",
                     fontsize=13, fontweight="bold")
        ax.set_xlabel("Change in modal price (%)")
        ax.axvline(0, color="black", linewidth=0.8)
        fig.tight_layout()
        movers_path = os.path.join(CHARTS_DIR, f"top_movers_{date_s}.png")
        fig.savefig(movers_path, dpi=130)
        movers_svg = os.path.join(CHARTS_DIR, f"top_movers_{date_s}.svg")
        fig.savefig(movers_svg, format="svg")
        plt.close(fig)

    print(f"VISUALIZE: {trend_path}" + (f", {movers_path}" if movers_path else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
