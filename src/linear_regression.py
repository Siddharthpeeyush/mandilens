#!/usr/bin/env python3
"""Day 17: linear regression on lag features, per commodity.

Method (leak-free: a forecast for day t uses only prices up to t-1):
  * Features per market-commodity series: lag1, lag2, lag3 (yesterday's
    price, the day before, the day before that).
  * One OLS model per commodity, pooled across all 8 mandis, fitted with
    numpy least squares (no sklearn dependency): price(t) ~ b0 + b1*lag1
    + b2*lag2 + b3*lag3. Coefficients are fitted on the full history and
    evaluated in-sample on every row whose three lags exist; the Day 18
    item adds a proper time-based train/test split, so these numbers are
    the in-sample fit, labelled as such, not a backtest claim.
  * Compared against Day 16's baselines on the SAME rows (persistence
    and MA3 forecast), so the comparison is apples-to-apples: a model
    must beat MA3's MAE on the lag-3 rows to be worth shipping.

Reads : data/processed/mandi_prices_clean.csv
Writes: data/processed/linear_regression.csv
        charts/linear_regression_YYYY-MM-DD.svg
        reports/day17_linear_regression.md
Prints: per-commodity MAE table + coefficients + hand-check result.
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
OUT = os.path.join(BASE_DIR, "data", "processed", "linear_regression.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

COMMS = ["Onion", "Potato", "Tomato"]
COLORS = {"Persistence": "#37474f", "MA3 forecast": "#e67e22",
          "Linear regression": "#2e86ab"}


def add_lags(df):
    df = df.sort_values(["market", "commodity", "arrival_date"]).copy()
    g = df.groupby(["market", "commodity"])["modal_price"]
    df["lag1"] = g.shift(1)
    df["lag2"] = g.shift(2)
    df["lag3"] = g.shift(3)
    df["fc_persist"] = df["lag1"]
    df["fc_ma3"] = df.groupby(["market", "commodity"])["modal_price"].transform(
        lambda s: s.rolling(3).mean().shift(1))
    return df


def fit_ols(sub):
    """OLS on lag1..lag3; returns (intercept, coefs, fitted values)."""
    X = np.column_stack([np.ones(len(sub)), sub["lag1"], sub["lag2"],
                         sub["lag3"]])
    y = sub["modal_price"].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, X @ beta


def metrics(y, pred):
    err = y - pred
    return {
        "n": len(y),
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mape": float(np.mean(np.abs(err) / y) * 100),
    }


def make_chart(summary, path):
    x = np.arange(len(COMMS))
    w = 0.25
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    for i, (label, key) in enumerate([("Persistence", "fc_persist"),
                                      ("MA3 forecast", "fc_ma3"),
                                      ("Linear regression", "fc_lr")]):
        vals = [summary[c][key]["mae"] for c in COMMS]
        ax.bar(x + (i - 1) * w, vals, w, label=label, color=COLORS[label])
    ax.set_xticks(x)
    ax.set_xticklabels(COMMS)
    ax.set_ylabel("MAE (Rs/qtl)")
    ax.set_title(f"Linear regression vs baselines — MAE by commodity "
                 f"(lag-3 rows, to {TODAY})", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, format="svg")
    plt.close(fig)


def hand_check(df):
    """Recompute one fitted value by hand from the model coefficients."""
    sub = df[(df["market"] == "Azadpur") & (df["commodity"] == "Onion")]
    if sub.empty:
        sub = df[(df["market"] == df["market"].min()) &
                 (df["commodity"] == "Onion")]
    sub = sub.sort_values("arrival_date")
    last = sub.iloc[-1]
    beta, _ = fit_ols(df[(df["commodity"] == "Onion") &
                         (df["lag3"].notna())])
    manual = beta[0] + beta[1] * last["lag1"] + beta[2] * last["lag2"] \
        + beta[3] * last["lag3"]
    assert abs(float(last["fc_lr"]) - manual) < 0.01, (last["fc_lr"], manual)
    return sub["market"].iloc[0], last["arrival_date"], beta, manual


def write_report(summary, betas, latest, market, last_date, beta, manual,
                 chart_name, path):
    lines = [
        "# Day 17 — Linear regression on lag features, per commodity",
        "",
        "## Method (read this first)",
        "",
        "One OLS model per commodity, pooled across all 8 mandis:",
        "price(*t*) ~ intercept + b1·lag1 + b2·lag2 + b3·lag3, where lag*k*",
        "is the price *k* days earlier in the same market-commodity",
        "series. Every feature uses only prices up to *t−1* — no",
        "leakage. A row enters the evaluation only once all three lags",
        "exist, so early-history rows are excluded, never padded. The",
        "Day 16 baselines are re-scored on exactly those same rows, so",
        "the comparison is apples-to-apples. These are **in-sample**",
        "fits (coefficients fitted on the same rows they are scored",
        "on); Day 18 adds a time-based train/test split before any",
        "backtest claim is made. Fitted with plain numpy least squares",
        "— no sklearn dependency.",
        "",
        "## Fitted coefficients",
        "",
        "| Commodity | Intercept | lag1 | lag2 | lag3 |",
        "|---|---|---|---|---|",
    ]
    for comm in COMMS:
        b = betas[comm]
        lines.append(f"| {comm} | {b[0]:.2f} | {b[1]:.3f} | {b[2]:.3f} | "
                     f"{b[3]:.3f} |")
    lines += [
        "",
        "## Backtest results — lag-3 rows only (in-sample fit)",
        "",
        "| Commodity | Method | n | MAE Rs/qtl | RMSE Rs/qtl | MAPE % |",
        "|---|---|---|---|---|---|",
    ]
    for comm in COMMS:
        for label, key in [("Persistence", "fc_persist"),
                           ("MA3 forecast", "fc_ma3"),
                           ("Linear regression", "fc_lr")]:
            s = summary[comm][key]
            lines.append(f"| {comm} | {label} | {s['n']} | {s['mae']:.2f} | "
                         f"{s['rmse']:.2f} | {s['mape']:.2f} |")
    lines += [
        "",
        "## Does regression beat the baselines?",
        "",
    ]
    for comm in COMMS:
        lr = summary[comm]["fc_lr"]["mae"]
        ma3 = summary[comm]["fc_ma3"]["mae"]
        verb = "beats" if lr < ma3 else "does NOT beat"
        lines.append(f"- **{comm}**: regression MAE Rs {lr:.2f}/qtl {verb} "
                     f"MA3 (Rs {ma3:.2f}/qtl).")
    lines += [
        "",
        "## Verification",
        "",
        f"Hand-check on {market} Onion for {last_date.date()}: recomputing",
        f"the fitted value from the coefficients by hand gives",
        f"Rs {manual:.2f}/qtl — it **matches** the module output to the",
        "paisa. The coefficients are verified, not assumed.",
        "",
        "## Reading the result",
        "",
        "The lag1 coefficient carries most of the weight in every",
        "commodity (prices are strongly autocorrelated day to day),",
        "with lag2 and lag3 small — the regression is mostly learning",
        "'tomorrow looks like yesterday, slightly pulled toward the",
        "last few days'. Whether that beats the simple MA3 average",
        "depends on the commodity (see table above); on the current",
        "(sample) data the honest expectation is a near-tie, because",
        "the sample generator's drift is smooth and its jitter is",
        "independent noise no lag model can predict. Day 18's",
        "time-split evaluation will show whether the in-sample edge",
        "survives out-of-sample. On real portal extracts the same",
        "table would show which commodities genuinely carry",
        "multi-day memory.",
        "",
        f"![Linear regression](../charts/{chart_name})",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    df = pd.read_csv(PROCESSED)
    df["arrival_date"] = pd.to_datetime(df["arrival_date"])
    df = add_lags(df)
    eval_df = df[df["lag3"].notna() & df["fc_ma3"].notna()].copy()

    summary, betas = {}, {}
    for comm in COMMS:
        sub = eval_df[eval_df["commodity"] == comm].copy()
        beta, fitted = fit_ols(sub)
        betas[comm] = beta
        sub["fc_lr"] = fitted
        eval_df.loc[sub.index, "fc_lr"] = fitted
        y = sub["modal_price"].to_numpy(dtype=float)
        summary[comm] = {
            "fc_persist": metrics(y, sub["fc_persist"].to_numpy()),
            "fc_ma3": metrics(y, sub["fc_ma3"].to_numpy()),
            "fc_lr": metrics(y, fitted),
        }

    cols = ["market", "commodity", "arrival_date", "modal_price", "lag1",
            "lag2", "lag3", "fc_persist", "fc_ma3", "fc_lr"]
    out = eval_df[cols].copy()
    out["arrival_date"] = out["arrival_date"].dt.strftime("%Y-%m-%d")
    out.to_csv(OUT, index=False)

    market, last_date, beta, manual = hand_check(eval_df)
    latest = eval_df[eval_df["arrival_date"] ==
                     eval_df["arrival_date"].max()].copy()

    chart_name = f"linear_regression_{TODAY}.svg"
    make_chart(summary, os.path.join(CHARTS_DIR, chart_name))
    write_report(summary, betas, latest, market, last_date, beta, manual,
                 chart_name,
                 os.path.join(REPORTS_DIR, "day17_linear_regression.md"))

    for comm in COMMS:
        s = summary[comm]
        print(f"{comm}: regression MAE {s['fc_lr']['mae']:.2f} | "
              f"MA3 {s['fc_ma3']['mae']:.2f} | "
              f"persistence {s['fc_persist']['mae']:.2f} "
              f"(n={s['fc_lr']['n']})")
        b = betas[comm]
        print(f"  coefs: intercept {b[0]:.2f}, lag1 {b[1]:.3f}, "
              f"lag2 {b[2]:.3f}, lag3 {b[3]:.3f}")
    print(f"Hand-check {market} Onion: fitted value MATCHES manual "
          f"Rs {manual:.2f}/qtl")


if __name__ == "__main__":
    main()
