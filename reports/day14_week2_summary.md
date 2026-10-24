# MandiLens — Day 14 · Week-2 summary (24 Oct 2026)

*Cleaning deep-dive + visual storytelling week. All numbers recomputed on the
full dataset: 600 rows, 25/26 calendar days (2026-09-29 → 2026-10-24), 8
mandis, 3 commodities (Onion, Potato, Tomato).*

## What Week 2 built

| Day | Item | Finding |
|---|---|---|
| 8 | Outlier detection rules (IQR vs z-score on modal prices) | Both rules flag 0 points on 152 modal prices/commodity; IQR (k=1.5) adopted as pipeline default flag, z-score kept as secondary check |
| 9 | Commodity volatility index | Potato most stable (index 76, CV 11.8%), Onion #2 (84), Tomato most volatile (100, CV 15.4%); day-to-day swing 2.3% (Potato) vs 5.4% (Tomato); hottest cell Koyambedu-Tomato (CV 16.6%) |
| 10 | MSP gap analysis | Verified finding — 0/3 tracked commodities have a notified MSP (vegetables aren't in the 22 mandated crops, Kharif+Rabi 2026-27 per PIB); gap module built, activates when a mandated crop is added |
| 11 | Arrival vs price dynamics | Same-day Pearson r ≈ 0 for all 3 commodities (Onion −0.013, Potato +0.057, Tomato −0.018, n=176 each); median lag-1 r −0.052 — expected null on synthetic arrivals, which are drawn independently of price drift |
| 12 | Weekday effects | 504 day-over-day returns across 24 market-commodity series; one-way ANOVA per commodity finds no weekday effect (Onion p=0.920, Potato p=0.835, Tomato p=0.810) — expected null, generator has no weekday component |
| 13 | Animated price-trend chart | Pure-SMIL animated SVG (3 self-drawing lines, travelling dots, sweeping playhead, date readout, 8s loop); text-only so it pushes via the files API |
| 14 | Week-2 summary + chart gallery refresh | This report + `CHART_GALLERY.md` (37 charts, 15 families, regenerable via `tools/build_chart_gallery.py`) |

## Key Week-2 numbers (full window)

- **Coverage:** 600 rows; 25 of 26 calendar days; single missing day 2026-10-13; longest gap 1 day.
- **Median modal price (₹/q, full window):** Onion 1,970 · Potato 1,370 · Tomato 2,050.
- **Volatility ranking (unchanged since Day 9):** Potato < Onion < Tomato — the ranking, not the levels, is the Week-2 result that survives the sample-to-real switch.
- **Nulls, honestly labelled:** arrival↔price correlation, weekday effects, and variety premiums all read ≈ 0 — every one of them is the *expected* null on seeded sample data (the generators carry no such component), and every module re-runs unchanged on real portal extracts.
- **MSP:** undefined for all 3 tracked commodities — reporting a gap would mean inventing a benchmark that does not exist.

## Data-quality caveat

The Agmarknet portal returned a hard 403 again today (24 Oct) — the browser
task tried the dashboard URL, site root, www variant, http redirect and
trailing-slash variant, plus a fresh browser environment; every variant
showed only "403 Forbidden". Week 2 therefore ran on deterministically
seeded sample rows, as did Week 1. The statistics above describe the
**pipeline's** shape, not live market prices. The daily keyless-pull
attempt continues unchanged; the day the portal answers, every number above
re-computes from real tables with no code change.

## The chart gallery

`CHART_GALLERY.md` collects every SVG the pipeline has produced — 37 charts
in 15 families (daily trends, daily movers, and the named per-day analyses),
newest first within each family. It is generated, not hand-maintained:
`python3 tools/build_chart_gallery.py` re-scans `charts/` and rebuilds it,
so tomorrow's charts join the gallery automatically.

## Week 3 preview

Lag/rolling features (Day 15) → naive baselines: persistence & moving-average
forecasts (16) → linear regression on lag features, per commodity (17) →
train/test split by time + MAE/RMSE evaluation (18) → random forest
regressor, feature importances (19) → forecast vs actual tracking chart
(20) → week-3 summary — which model wins so far? (21).
