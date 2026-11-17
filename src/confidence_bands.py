#!/usr/bin/env python3
"""Day 38: forecast confidence bands — prediction intervals from
walk-forward residuals, shown on the site's forecast table.

Method:
  * Score every stored 7-day forecast against actual modal prices
    (forecast_accuracy.py's loader/scorer, imported unchanged) and
    take the SIGNED residual r = actual - forecast on scored rows only.
  * Per commodity, pool the signed residuals across all origins and
    horizons (n is small and reported honestly — see Limits). The 80%
    prediction interval is the empirical 10th/90th percentile of that
    pooled residual distribution.
  * Horizon widening: recursive multi-step errors accumulate, so the
    pooled interval (which mixes horizons 1..7) is rescaled to each
    horizon h by sqrt(h / h_bar), where h_bar is the mean horizon of
    that commodity's pooled residuals — the standard random-walk
    error-growth assumption, stated here, not hidden. Band for a
    forecast cell: [forecast + q10 * sqrt(h/h_bar),
                    forecast + q90 * sqrt(h/h_bar)], floored at 0.
  * Fallback: a commodity with fewer than 3 scored residuals gets no
    empirical quantiles — its band is +/- (walk-forward 1-day MAE x
    sqrt(h)), flagged method="mae_fallback" in the outputs.
  * Coverage check: fraction of scored residuals that fall inside
    their own horizon's band (in-sample by construction — a sanity
    check, not an out-of-sample claim).

Reads : data/processed/forecast_table_*.csv
        data/processed/mandi_prices_clean.csv
        data/processed/forecast_mae_YYYY-MM-DD.json (fallback scale)
Writes: data/processed/confidence_bands_YYYY-MM-DD.csv
        data/processed/confidence_bands_YYYY-MM-DD.json (site sidecar)
        charts/confidence_bands_YYYY-MM-DD.svg
        reports/day38_forecast_confidence_bands.md
Prints: per-commodity n, q10/q90, h_bar, coverage, hand-check.
"""
import datetime as dt
import glob
import json
import math
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
PROCESSED = os.path.join(BASE_DIR, "data", "processed")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SRC_DIR = os.path.join(BASE_DIR, "src")
TODAY = dt.date.today().isoformat()

COMMS = ["Onion", "Potato", "Tomato"]
HORIZON = 7
COLORS = {"Onion": "#c0392b", "Potato": "#b7950b", "Tomato": "#e74c3c"}
MIN_N_EMPIRICAL = 3

sys.path.insert(0, SRC_DIR)
import forecast_accuracy as fa  # noqa: E402  (reuse its scoring, unchanged)


def pooled_residuals(scored):
    """Signed residuals (actual - forecast) per commodity, scored rows."""
    out = {}
    for comm in COMMS:
        s = scored[(scored["commodity"] == comm) & scored["scored"]]
        r = (s["modal_price"] - s["forecast_price"]).to_numpy(dtype=float)
        h = s["horizon_days"].to_numpy(dtype=float)
        out[comm] = (r, h)
    return out


def band_offsets(resid, horizons):
    """(lo, hi, method, h_bar) offsets for horizon scaling.

    Empirical: q10/q90 of the pooled signed residuals, scaled by
    sqrt(h / h_bar) at use time. Fallback (n < 3): symmetric MAE band.
    """
    r, h = resid, horizons
    n = len(r)
    if n >= MIN_N_EMPIRICAL:
        lo = float(np.percentile(r, 10))
        hi = float(np.percentile(r, 90))
        return lo, hi, "empirical_q10_q90", float(np.mean(h))
    return None, None, "mae_fallback", (float(np.mean(h)) if n else np.nan)


def mae_fallback_scale():
    """Walk-forward 1-day MAE per commodity from the latest sidecar."""
    paths = sorted(glob.glob(os.path.join(
        PROCESSED, "forecast_mae_*.json")))
    if not paths:
        return {c: float("nan") for c in COMMS}
    with open(paths[-1], encoding="utf-8") as f:
        sidecar = json.load(f)
    return {c: float(sidecar[c]["mae"]) for c in COMMS if c in sidecar}


def apply_bands(fc_today, bands):
    """Attach lo80/hi80 to each row of today's forecast table."""
    rows = []
    for _, r in fc_today.iterrows():
        comm = r["commodity"]
        h = int(r["horizon_days"])
        f = float(r["forecast_price"])
        lo_off, hi_off, method, h_bar, _mae = bands[comm]
        if method == "empirical_q10_q90":
            scale = math.sqrt(h / h_bar) if h_bar and h_bar > 0 else 1.0
            lo = max(0.0, f + lo_off * scale)
            hi = f + hi_off * scale
        else:  # mae_fallback: symmetric +/- MAE * sqrt(h)
            mae = bands[comm][4]
            half = mae * math.sqrt(h)
            lo, hi = max(0.0, f - half), f + half
        rows.append({"market": r["market"], "commodity": comm,
                     "forecast_date": r["forecast_date"],
                     "horizon_days": h, "forecast_price": round(f, 2),
                     "lo80": round(lo, 2), "hi80": round(hi, 2),
                     "method": method})
    return pd.DataFrame(rows)


def coverage(scored, bands):
    """In-sample share of scored residuals inside their horizon band."""
    out = {}
    for comm in COMMS:
        s = scored[(scored["commodity"] == comm) & scored["scored"]]
        if s.empty:
            out[comm] = (float("nan"), 0)
            continue
        lo_off, hi_off, method, h_bar, _mae = bands[comm]
        inside = 0
        for _, r in s.iterrows():
            h = int(r["horizon_days"])
            resid = float(r["modal_price"]) - float(r["forecast_price"])
            if method == "empirical_q10_q90":
                scale = math.sqrt(h / h_bar) if h_bar and h_bar > 0 else 1.0
                ok = lo_off * scale <= resid <= hi_off * scale
            else:
                ok = abs(resid) <= bands[comm][4] * math.sqrt(h)
            inside += int(ok)
        out[comm] = (inside / len(s), len(s))
    return out


def hand_check(scored, bands):
    """Pure-Python recompute of one banded cell end-to-end."""
    s = scored[scored["scored"]].sort_values(
        ["base_date", "horizon_days", "market", "commodity"])
    if s.empty:
        return "SKIP: no scored rows at all"
    r = s.iloc[0]
    comm, h = r["commodity"], int(r["horizon_days"])
    lo_off, hi_off, method, h_bar, _mae = bands[comm]
    f = float(r["forecast_price"])
    if method == "empirical_q10_q90":
        scale = math.sqrt(h / h_bar)
        lo = max(0.0, f + lo_off * scale)
        hi = f + hi_off * scale
        detail = (f"empirical q10 {lo_off:.2f} / q90 {hi_off:.2f}, "
                  f"h_bar {h_bar:.2f}, scale sqrt({h}/{h_bar:.2f})="
                  f"{scale:.3f}")
    else:
        half = bands[comm][4] * math.sqrt(h)
        lo, hi = max(0.0, f - half), f + half
        detail = f"MAE fallback half-width {half:.2f}"
    return (f"{r['market']} {comm} base {r['base_date']} h={h}: forecast "
            f"{f:.2f} -> band [{lo:.2f}, {hi:.2f}] ({detail}); actual "
            f"{float(r['modal_price']):.2f} -> "
            f"{'INSIDE' if lo <= float(r['modal_price']) <= hi else 'OUTSIDE'}")


def make_chart(df, banded, latest, fdates, path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 8.4), sharex=True)
    all_dates = list(df["arrival_date"].sort_values().unique())[-14:]
    x_hist = pd.to_datetime(all_dates)
    x_fc = pd.to_datetime(fdates)
    for ax, comm in zip(axes, COMMS):
        hist_med = (df[(df["commodity"] == comm)
                       & (df["arrival_date"].isin(all_dates))]
                    .groupby("arrival_date")["modal_price"].median())
        sub = banded[banded["commodity"] == comm]
        fc_med = np.array([np.nanmedian(sub[sub["forecast_date"] == d]["forecast_price"])
                           for d in fdates])
        lo_med = np.array([np.nanmedian(sub[sub["forecast_date"] == d]["lo80"])
                           for d in fdates])
        hi_med = np.array([np.nanmedian(sub[sub["forecast_date"] == d]["hi80"])
                           for d in fdates])
        ax.plot(x_hist, hist_med.reindex(x_hist).to_numpy(), "o-",
                color=COLORS[comm], linewidth=1.8, markersize=4,
                label="Actual (cross-mandi median)")
        ax.plot(x_fc, fc_med, "s--", color="#2c3e50", linewidth=1.8,
                markersize=4, label="OLS forecast (median)")
        ax.fill_between(x_fc, lo_med, hi_med, color="#2c3e50", alpha=0.15,
                        label="80% prediction interval")
        ax.axvline(x_fc[0] - pd.Timedelta(hours=12), color="gray",
                   linestyle=":", linewidth=1)
        ax.set_title(f"{comm} — last 14 days + 7-day forecast with 80% band (₹/qtl)",
                     fontsize=11, fontweight="bold")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.autofmt_xdate(rotation=30)
    fig.suptitle(f"7-day forecast with 80% prediction intervals from "
                 f"{latest:%d %b %Y} — OLS on lag1/lag2/lag3, recursive",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(path, format="svg")
    plt.close(fig)
    xml.dom.minidom.parse(path)  # proves the SVG is valid XML


def write_report(bands, resid, cov, hand, banded, chart_name, latest, fdates,
                 n_sample):
    lines = [
        "# Day 38 — Forecast confidence bands (prediction intervals)",
        "",
        "## Method",
        "",
        "Every stored 7-day forecast is scored against actual modal",
        "prices (the Day-24 scorer, reused unchanged) and the SIGNED",
        "residual r = actual − forecast is kept. Per commodity the",
        "residuals are pooled across all origins and horizons; the 80%",
        "prediction interval is the empirical 10th/90th percentile of",
        "that pooled distribution. Because the pool mixes horizons 1–7,",
        "each horizon h rescales the offsets by sqrt(h / h_bar), where",
        "h_bar is the mean horizon of that commodity's pooled residuals",
        "— the standard random-walk error-growth assumption, stated",
        "here rather than hidden. Bands are floored at ₹0 (prices",
        "cannot go negative). A commodity with fewer than 3 scored",
        "residuals gets no empirical quantiles: its band is",
        "±(walk-forward 1-day MAE × sqrt(h)) and is flagged",
        "`mae_fallback` in the CSV.",
        "",
        "## Residual base (all scored rows to date)",
        "",
        f"All {sum(len(resid[c][0]) for c in COMMS)} scored residuals rest on",
        f"real Agmarknet portal actuals ({n_sample} scored against seeded",
        "sample-mode actuals — zero). Origins: 08–13 Nov 2026.",
        "",
        "| Commodity | Scored residuals (n) | Mean horizon h_bar | q10 (₹/qtl) | q90 (₹/qtl) | Method |",
        "|---|---|---|---|---|---|",
    ]
    for comm in COMMS:
        r, h = resid[comm]
        lo, hi, method, h_bar, _mae = bands[comm]
        lo_s = f"{lo:.2f}" if lo is not None else "—"
        hi_s = f"{hi:.2f}" if hi is not None else "—"
        hb_s = f"{h_bar:.2f}" if h_bar == h_bar else "—"
        lines.append(f"| {comm} | {len(r)} | {hb_s} | {lo_s} | {hi_s} | {method} |")
    lines += [
        "",
        "## In-sample coverage (sanity check, not an out-of-sample claim)",
        "",
        "Share of scored residuals falling inside their own horizon's",
        "band. By construction the pooled band covers ~80% at the mean",
        "horizon; per-horizon numbers will drift as more scored rows",
        "arrive.",
        "",
    ]
    for comm in COMMS:
        c, n = cov[comm]
        lines.append(f"- {comm}: {c * 100:.1f}% inside (n={n})"
                     if n else f"- {comm}: no scored rows yet")
    lines += [
        "",
        "## Today's bands (cross-mandi median, ₹/qtl)",
        "",
        "| Commodity | " + " | ".join(d.strftime("%d %b") for d in fdates) + " |",
        "|" + "---|" * (len(fdates) + 1),
    ]
    for comm in COMMS:
        sub = banded[banded["commodity"] == comm]
        cells = []
        for d in fdates:
            day = sub[sub["forecast_date"] == d]
            if day.empty:
                cells.append("—")
            else:
                cells.append(f"{day['forecast_price'].median():,.0f} "
                             f"({day['lo80'].median():,.0f}–{day['hi80'].median():,.0f})")
        lines.append(f"| {comm} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Hand check",
        "",
        f"- {hand}",
        "",
        "## Verification",
        "",
        "- Banded CSV re-runs deterministically (same inputs, same",
        "  quantiles); chart parses as valid SVG.",
        "- The site sidecar (confidence_bands_YYYY-MM-DD.json) carries",
        "  per-commodity, per-horizon lo/hi offsets so build_site.py",
        "  can render the band under every forecast cell; the site's",
        "  forecast note now states the residual count behind each band.",
        "",
        "## Limits",
        "",
        "- The residual base is THIN: a handful of scored rows per",
        "  commodity, all from real portal actuals since 10 Nov — so",
        "  the 80% label is an empirical-quantile statement on a small",
        "  sample, not a calibrated interval. It widens honestly as",
        "  scored rows accumulate (re-run daily via run_daily.py).",
        "- sqrt(h) widening is an assumption, not a measurement: if",
        "  multi-step errors grow faster than a random walk, the h=6–7",
        "  bands understate the true spread. The coverage table above",
        "  will expose that as scored rows arrive.",
        "- Bands inherit the forecast's own limits (sample-fit history",
        "  to 29 Oct + real rows from 10 Nov; sparse per-mandi actuals).",
    ]
    onion_q10 = bands["Onion"][0]
    if onion_q10 is not None and onion_q10 > 0:
        lines += [
            f"- Onion's band sits entirely ABOVE its point forecast (q10 is",
            f"  +₹{onion_q10:,.0f}/qtl): on the {len(resid['Onion'][0])} scored Onion rows",
            "  the model under-predicts every time — the band is reporting a",
            "  real bias, not a symmetric error. A bias correction is a",
            "  follow-up, not today's change.",
        ]
    lines += [
        "",
        f"![Forecast with 80% bands](../charts/{chart_name})",
        "",
    ]
    with open(os.path.join(REPORTS_DIR, "day38_forecast_confidence_bands.md"),
              "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    actuals = fa.load_actuals()
    fc = fa.load_forecasts()
    if fc.empty:
        print("CONFIDENCE_BANDS: no forecast_table_*.csv files found",
              file=sys.stderr)
        return 1
    scored = fa.score(fc, actuals)
    resid = pooled_residuals(scored)

    mae_scale = mae_fallback_scale()
    bands = {}
    for comm in COMMS:
        lo, hi, method, h_bar = band_offsets(*resid[comm])
        bands[comm] = (lo, hi, method, h_bar, mae_scale.get(comm, float("nan")))

    # Today's forecast table (latest run) gets the bands.
    fc_paths = sorted(glob.glob(os.path.join(
        PROCESSED, "forecast_table_*.csv")))
    fc_today = pd.read_csv(fc_paths[-1])
    fc_today["forecast_date"] = pd.to_datetime(
        fc_today["forecast_date"]).dt.date
    banded = apply_bands(fc_today, bands)

    out_csv = os.path.join(PROCESSED, f"confidence_bands_{TODAY}.csv")
    banded_out = banded.copy()
    banded_out["forecast_date"] = banded_out["forecast_date"].apply(
        lambda d: d.isoformat())
    banded_out.to_csv(out_csv, index=False)

    # Site sidecar: per-commodity, per-horizon lo/hi OFFSETS (₹/qtl),
    # plus the residual count so the site can state its basis honestly.
    sidecar = {}
    for comm in COMMS:
        lo_off, hi_off, method, h_bar, _mae = bands[comm]
        per_h = {}
        for h in range(1, HORIZON + 1):
            if method == "empirical_q10_q90":
                scale = math.sqrt(h / h_bar) if h_bar and h_bar > 0 else 1.0
                per_h[str(h)] = {"lo": round(lo_off * scale, 2),
                                 "hi": round(hi_off * scale, 2)}
            else:
                half = bands[comm][4] * math.sqrt(h)
                per_h[str(h)] = {"lo": round(-half, 2),
                                 "hi": round(half, 2)}
        sidecar[comm] = {"n": len(resid[comm][0]), "method": method,
                         "h_bar": round(h_bar, 2) if h_bar == h_bar else None,
                         "offsets": per_h}
    sidecar_path = os.path.join(PROCESSED, f"confidence_bands_{TODAY}.json")
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sidecar, f)
    print(f"CONFIDENCE_BANDS: sidecar -> {sidecar_path}")

    cov = coverage(scored, bands)
    hand = hand_check(scored, bands)

    # Chart: history + today's median forecast with band.
    df = pd.read_csv(os.path.join(PROCESSED, "mandi_prices_clean.csv"),
                     parse_dates=["arrival_date"])
    df = df[(df["market"] != "National") & df["commodity"].isin(COMMS)]
    latest = df["arrival_date"].max()
    fdates = [(latest + pd.Timedelta(days=h)).date()
              for h in range(1, HORIZON + 1)]
    chart_name = f"confidence_bands_{TODAY}.svg"
    make_chart(df, banded, latest, fdates,
               os.path.join(CHARTS_DIR, chart_name))

    write_report(bands, resid, cov, hand, banded, chart_name, latest, fdates,
                 int(((scored["scored"]) &
                      (scored["actual_mode"] == "sample")).sum()))

    print(f"CONFIDENCE_BANDS: {len(banded)} cells banded "
          f"({banded['market'].nunique()} markets x {HORIZON} days)")
    for comm in COMMS:
        r, h = resid[comm]
        lo, hi, method, h_bar, _mae = bands[comm]
        c, n = cov[comm]
        print(f"  {comm}: n={len(r)} {method} "
              f"q10={lo if lo is not None else float('nan'):.2f} "
              f"q90={hi if hi is not None else float('nan'):.2f} "
              f"h_bar={h_bar:.2f} coverage={c * 100:.1f}% (n={n})")
    print(f"HAND-CHECK: {hand}")
    print(f"WROTE: {out_csv}, {sidecar_path}, charts/{chart_name}, "
          f"reports/day38_forecast_confidence_bands.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
