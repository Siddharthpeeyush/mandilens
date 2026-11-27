# Day 38 — Forecast confidence bands (prediction intervals)

## Method

Every stored 7-day forecast is scored against actual modal
prices (the Day-24 scorer, reused unchanged) and the SIGNED
residual r = actual − forecast is kept. Per commodity the
residuals are pooled across all origins and horizons; the 80%
prediction interval is the empirical 10th/90th percentile of
that pooled distribution. Because the pool mixes horizons 1–7,
each horizon h rescales the offsets by sqrt(h / h_bar), where
h_bar is the mean horizon of that commodity's pooled residuals
— the standard random-walk error-growth assumption, stated
here rather than hidden. Bands are floored at ₹0 (prices
cannot go negative). A commodity with fewer than 3 scored
residuals gets no empirical quantiles: its band is
±(walk-forward 1-day MAE × sqrt(h)) and is flagged
`mae_fallback` in the CSV.

## Residual base (all scored rows to date)

All 457 scored residuals rest on
real Agmarknet portal actuals (0 scored against seeded
sample-mode actuals — zero). Origins: 08–13 Nov 2026.

| Commodity | Scored residuals (n) | Mean horizon h_bar | q10 (₹/qtl) | q90 (₹/qtl) | Method |
|---|---|---|---|---|---|
| Onion | 62 | 3.77 | -287.06 | 745.74 | empirical_q10_q90 |
| Potato | 152 | 3.74 | -291.53 | 0.36 | empirical_q10_q90 |
| Tomato | 243 | 3.72 | -636.82 | 671.49 | empirical_q10_q90 |

## In-sample coverage (sanity check, not an out-of-sample claim)

Share of scored residuals falling inside their own horizon's
band. By construction the pooled band covers ~80% at the mean
horizon; per-horizon numbers will drift as more scored rows
arrive.

- Onion: 80.6% inside (n=62)
- Potato: 79.6% inside (n=152)
- Tomato: 86.4% inside (n=243)

## Today's bands (cross-mandi median, ₹/qtl)

| Commodity | 26 Nov | 27 Nov | 28 Nov | 29 Nov | 30 Nov | 01 Dec | 02 Dec |
|---|---|---|---|---|---|---|---|
| Onion | 2,281 (2,133–2,665) | 2,309 (2,101–2,852) | 2,324 (2,068–2,989) | 2,323 (2,027–3,090) | 2,329 (1,998–3,187) | 2,334 (1,972–3,274) | 2,338 (1,947–3,353) |
| Potato | 1,430 (1,279–1,430) | 1,474 (1,261–1,474) | 1,434 (1,173–1,434) | 1,443 (1,142–1,444) | 1,455 (1,118–1,456) | 1,450 (1,081–1,450) | 1,451 (1,052–1,451) |
| Tomato | 2,324 (1,994–2,672) | 2,317 (1,850–2,809) | 2,329 (1,757–2,931) | 2,327 (1,667–3,023) | 2,328 (1,591–3,106) | 2,325 (1,517–3,177) | 2,323 (1,450–3,244) |

## Hand check

- Azadpur Onion base 2026-11-08 h=1: forecast 3309.70 -> band [3161.94, 3693.56] (empirical q10 -287.06 / q90 745.74, h_bar 3.77, scale sqrt(1/3.77)=0.515); actual 4019.00 -> OUTSIDE

## Verification

- Banded CSV re-runs deterministically (same inputs, same
  quantiles); chart parses as valid SVG.
- The site sidecar (confidence_bands_YYYY-MM-DD.json) carries
  per-commodity, per-horizon lo/hi offsets so build_site.py
  can render the band under every forecast cell; the site's
  forecast note now states the residual count behind each band.

## Limits

- The residual base is THIN: a handful of scored rows per
  commodity, all from real portal actuals since 10 Nov — so
  the 80% label is an empirical-quantile statement on a small
  sample, not a calibrated interval. It widens honestly as
  scored rows accumulate (re-run daily via run_daily.py).
- sqrt(h) widening is an assumption, not a measurement: if
  multi-step errors grow faster than a random walk, the h=6–7
  bands understate the true spread. The coverage table above
  will expose that as scored rows arrive.
- Bands inherit the forecast's own limits (sample-fit history
  to 29 Oct + real rows from 10 Nov; sparse per-mandi actuals).

![Forecast with 80% bands](../charts/confidence_bands_2026-11-27.svg)
