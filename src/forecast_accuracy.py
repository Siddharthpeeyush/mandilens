#!/usr/bin/env python3
"""Day 24: forecast accuracy dashboard (rolling MAE).

Method:
  * Score every stored 7-day forecast (data/processed/forecast_table_*.csv,
    24 market-commodity series x horizons 1..7) against the actual modal
    price in data/processed/mandi_prices_clean.csv.
  * Origin date is derived exactly as the model used it:
    origin = forecast_date - horizon_days (the base date whose prices fed
    the recursive forecast). The filename run-date is NOT the origin.
  * For each (origin, horizon, commodity): MAE, n scored, persistence
    baseline (persist the base date's price forward) MAE on the same rows.
  * Rolling MAE: trailing h=1 MAE per commodity across origins to date
    (grows by one origin each day).
  * Horizons targeting future dates are PENDING — counted, shown, never
    silently dropped.
  * Honest caveat: actuals dated on days the pipeline ran in SAMPLE mode
    include seeded rows. Each scored row's actual is tagged with its day's
    data mode, derived from the raw file for that date (a raw file with no
    "National" market rows is sample-mode; the portal publishes the
    National benchmark table).

Reads : data/processed/forecast_table_*.csv
        data/processed/mandi_prices_clean.csv
        data/raw/mandi_prices_*.csv (mode tagging only)
Writes: data/processed/forecast_accuracy_YYYY-MM-DD.csv
        charts/forecast_accuracy_YYYY-MM-DD.svg (slim, push-API safe)
        reports/day24_forecast_accuracy.md
Prints: per-horizon MAE, rolling h=1 MAE, baseline comparison, hand-check.
"""
import datetime as dt
import glob
import os
import re
import sys
import xml.dom.minidom

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
TODAY = dt.date.today().isoformat()

COMMS = ["Onion", "Potato", "Tomato"]
HORIZON = 7


def load_actuals():
    df = pd.read_csv(os.path.join(PROCESSED, "mandi_prices_clean.csv"),
                     usecols=["market", "commodity", "arrival_date",
                              "modal_price", "source_file"])
    df = df[df["commodity"].isin(COMMS)].copy()
    df["arrival_date"] = pd.to_datetime(df["arrival_date"]).dt.date
    return df


def load_forecasts():
    frames = []
    for path in sorted(glob.glob(os.path.join(PROCESSED, "forecast_table_*.csv"))):
        m = re.search(r"forecast_table_(\d{4}-\d{2}-\d{2})\.csv", path)
        f = pd.read_csv(path)
        f["run_date"] = m.group(1) if m else "unknown"
        f["forecast_date"] = pd.to_datetime(f["forecast_date"]).dt.date
        f["base_date"] = (f["forecast_date"] -
                          pd.to_timedelta(f["horizon_days"], unit="D"))
        frames.append(f)
    if not frames:
        return pd.DataFrame()
    fc = pd.concat(frames, ignore_index=True)
    # Portal days re-baseline forecasts on the same last per-mandi date;
    # keep only the latest run for identical (base, series, date, horizon)
    # cells so pooled MAE never double-counts a duplicated forecast.
    fc = fc.sort_values("run_date").drop_duplicates(
        subset=["base_date", "market", "commodity", "forecast_date",
                "horizon_days"], keep="last")
    return fc.reset_index(drop=True)


def day_mode(date_s):
    """portal if that day's raw file carries the National benchmark table."""
    path = os.path.join(RAW_DIR, f"mandi_prices_{date_s}.csv")
    if not os.path.exists(path):
        return "unknown"
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    return "portal" if re.search(r"\bNational\b", content) else "sample"


def score(fc, actuals):
    merged = fc.merge(
        actuals.rename(columns={"arrival_date": "forecast_date"}),
        how="left", on=["market", "commodity", "forecast_date"])
    merged["scored"] = merged["modal_price"].notna()
    merged["abs_err"] = (merged["forecast_price"] -
                         merged["modal_price"]).abs()
    # Persistence baseline: carry the BASE date's price forward.
    base = actuals.rename(columns={"arrival_date": "base_date",
                                   "modal_price": "persist_price"})
    merged = merged.merge(base[["market", "commodity", "base_date",
                                "persist_price"]],
                          on=["market", "commodity", "base_date"], how="left")
    merged["persist_err"] = (merged["persist_price"] -
                             merged["modal_price"]).abs()
    merged["actual_mode"] = merged["forecast_date"].apply(
        lambda d: day_mode(d.isoformat()))
    return merged


def summarize(scored):
    rows = []
    for (base, horizon, comm), g in scored.groupby(["base_date",
                                                    "horizon_days",
                                                    "commodity"]):
        s = g[g["scored"]]
        rows.append({
            "origin": base.isoformat(), "horizon_days": horizon,
            "commodity": comm, "n_series": len(g),
            "n_scored": int(s["scored"].sum()),
            "mae": round(float(s["abs_err"].mean()), 2) if len(s) else np.nan,
            "persist_mae": (round(float(s["persist_err"].mean()), 2)
                            if len(s) and s["persist_err"].notna().any()
                            else np.nan),
            "n_actual_sample": int((s["actual_mode"] == "sample").sum()),
        })
    return pd.DataFrame(rows).sort_values(["origin", "horizon_days",
                                           "commodity"]).reset_index(drop=True)


def rolling_h1(summary):
    h1 = summary[(summary["horizon_days"] == 1)].copy()
    h1 = h1.dropna(subset=["mae"]).sort_values(["commodity", "origin"])
    out = []
    for comm, g in h1.groupby("commodity"):
        for i in range(len(g)):
            win = g.iloc[: i + 1]
            out.append({"commodity": comm, "origin": win["origin"].iloc[-1],
                        "n_origins": i + 1,
                        "rolling_mae": round(float(win["mae"].mean()), 2),
                        "n_scored": int(win["n_scored"].sum())})
    return pd.DataFrame(out)


def hand_check(scored):
    """Pure-Python recompute of one scored row end-to-end."""
    s = scored[scored["scored"]].sort_values(["base_date", "horizon_days",
                                              "market", "commodity"])
    if s.empty:
        return "SKIP: no scored rows at all"
    r = s.iloc[0]
    manual = abs(float(r["forecast_price"]) - float(r["modal_price"]))
    ok = abs(manual - float(r["abs_err"])) < 1e-9
    base_ok = (r["forecast_date"] - dt.timedelta(days=int(r["horizon_days"]))
               == r["base_date"])
    return (f"{r['market']} {r['commodity']} base {r['base_date']} "
            f"h={int(r['horizon_days'])}: forecast "
            f"{r['forecast_price']:.2f} vs actual {r['modal_price']:.2f}"
            f" -> abs err {manual:.2f}; script {r['abs_err']:.2f} -> "
            f"{'MATCH' if ok else 'MISMATCH'}; "
            f"origin derivation {'OK' if base_ok else 'WRONG'}")


def chart(summary, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    scored = summary.dropna(subset=["mae"])
    piv = scored.pivot_table(index="horizon_days", columns="commodity",
                             values="mae", aggfunc="mean")
    ax = axes[0]
    for comm in COMMS:
        if comm in piv.columns:
            ax.plot(piv.index, piv[comm], marker="o", label=comm)
    ax.set_xlabel("Forecast horizon (days ahead)")
    ax.set_ylabel("MAE (Rs/quintal)")
    ax.set_title("Accuracy by horizon (pooled scored origins)")
    ax.set_xticks(range(1, HORIZON + 1))
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    roll = rolling_h1(summary)
    ax = axes[1]
    if roll.empty:
        ax.text(0.5, 0.5, "No scored h=1 origins yet", ha="center",
                va="center", transform=ax.transAxes, fontsize=12,
                color="gray")
    for comm, g in roll.groupby("commodity") if not roll.empty else []:
        ax.plot(g["origin"], g["rolling_mae"], marker="o", label=comm)
    ax.set_xlabel("Forecast origin (base date)")
    ax.set_ylabel("Rolling h=1 MAE (Rs/quintal)")
    ax.set_title("Rolling 1-day-ahead MAE (all origins to date)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.xticks(rotation=25)
    fig.suptitle("MandiLens forecast accuracy dashboard — Day 24")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    dom = xml.dom.minidom.parse(path)  # proves valid XML
    with open(path, "w", encoding="utf-8") as f:
        f.write(dom.toxml())


def write_report(summary, roll, hand, path, pending):
    total = int(summary["n_series"].sum())
    scored_n = int(summary["n_scored"].sum())
    sample_n = int(summary["n_actual_sample"].sum())
    lines = ["# Day 24 — Forecast accuracy dashboard (rolling MAE)",
             "",
             f"Date: {TODAY}. Every stored 7-day forecast is scored against",
             "actual modal prices. Origin = forecast_date − horizon_days,",
             "exactly the base date the recursive model ran from.",
             "",
             "## Coverage",
             "",
             f"- Forecast origins: {summary['origin'].nunique()} "
             f"({', '.join(sorted(summary['origin'].unique()))})",
             f"- Forecast cells: {total}; scored: {scored_n}; "
             f"pending: {total - scored_n}",
             f"- Of scored rows, {sample_n} scored against actuals dated on "
             "sample-mode days (seeded data — see Limits)",
             "",
             "## MAE by horizon (Rs/quintal, scored rows only)",
             ""]
    piv = summary.dropna(subset=["mae"]).pivot_table(
        index="horizon_days", columns="commodity", values="mae", aggfunc="mean")
    lines.append("| Horizon | " + " | ".join(COMMS) + " |")
    lines.append("|---:|" + "---:|" * len(COMMS))
    for h in range(1, HORIZON + 1):
        cells = []
        for comm in COMMS:
            v = (piv.loc[h, comm] if h in piv.index and comm in piv.columns
                 and not pd.isna(piv.loc[h, comm]) else None)
            cells.append(f"{v:.2f}" if v is not None else "pending")
        lines.append(f"| h={h} | " + " | ".join(cells) + " |")
    lines += ["", "## OLS vs persistence (same scored rows)", ""]
    sc = summary.dropna(subset=["mae"])
    for comm in COMMS:
        g = sc[sc["commodity"] == comm]
        if g.empty:
            lines.append(f"- {comm}: no scored rows yet")
            continue
        lines.append(f"- {comm}: OLS MAE {g['mae'].mean():.2f} vs "
                     f"persistence {g['persist_mae'].mean():.2f} "
                     f"(n={int(g['n_scored'].sum())})")
    lines += ["", "## Rolling 1-day-ahead MAE", ""]
    for _, r in roll.iterrows():
        lines.append(f"- {r['commodity']} @ {r['origin']}: "
                     f"{r['rolling_mae']:.2f} (from {r['n_origins']} origin(s), "
                     f"{r['n_scored']} scored rows)")
    lines += ["", "## Hand check", "", f"- {hand}", "",
              "## Limits", "",
              "- The 7-day table started on Day 23; the dashboard accumulates one "
              "origin per day, and duplicate runs re-baselined on the same "
              "date (portal days add no per-mandi actuals) are deduped to the "
              "latest run so pooled MAE never double-counts.",
              "- Recent origins' longer horizons are pending future actuals.",
              "- Scored rows whose actual date fell on a sample-mode day used "
              "seeded (synthetic) actuals — the n_actual_sample column counts "
              "them; today's real portal pull (if it lands) will steadily "
              "replace sample actuals with real ones.",
              ""]
    if pending:
        lines += ["## Pending (not yet scoreable)", ""]
        lines += [f"- {p}" for p in pending]
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    actuals = load_actuals()
    fc = load_forecasts()
    if fc.empty:
        print("NO FORECASTS: no forecast_table_*.csv files found")
        return 1
    scored = score(fc, actuals)
    summary = summarize(scored)
    roll = rolling_h1(summary)
    pend = summary[summary["n_scored"] == 0]
    pending = [f"{r['origin']} {r['commodity']} h={r['horizon_days']}: "
               f"targets {(dt.date.fromisoformat(r['origin']) + dt.timedelta(days=int(r['horizon_days'])))} "
               f"({int(r['n_series'])} series)"
               for _, r in pend.iterrows()]
    summary_path = os.path.join(PROCESSED, f"forecast_accuracy_{TODAY}.csv")
    summary.to_csv(summary_path, index=False)
    chart_path = os.path.join(CHARTS_DIR, f"forecast_accuracy_{TODAY}.svg")
    chart(summary, chart_path)
    hand = hand_check(scored)
    write_report(summary, roll, hand,
                 os.path.join(REPORTS_DIR, "day24_forecast_accuracy.md"),
                 pending)

    print(f"origins={summary['origin'].nunique()} "
          f"cells={int(summary['n_series'].sum())} "
          f"scored={int(summary['n_scored'].sum())} "
          f"scored_on_sample={int(summary['n_actual_sample'].sum())}")
    sc = summary.dropna(subset=["mae"])
    for h in range(1, HORIZON + 1):
        g = sc[sc["horizon_days"] == h]
        print(f"h={h}: " + (f"MAE {g['mae'].mean():.2f} "
                            f"(n={int(g['n_scored'].sum())})"
                            if not g.empty else "pending"))
    for _, r in roll.iterrows():
        print(f"rolling h=1 {r['commodity']} @ {r['origin']}: {r['rolling_mae']:.2f}")
    print(f"HAND-CHECK: {hand}")
    print(f"WROTE: {summary_path}, {chart_path}, "
          f"reports/day24_forecast_accuracy.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
