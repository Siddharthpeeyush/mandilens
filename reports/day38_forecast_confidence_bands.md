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

All 275 scored residuals rest on
real Agmarknet portal actuals (0 scored against seeded
sample-mode actuals — zero). Origins: 08–13 Nov 2026.

| Commodity | Scored residuals (n) | Mean horizon h_bar | q10 (₹/qtl) | q90 (₹/qtl) | Method |
|---|---|---|---|---|---|
| Onion | 34 | 3.59 | 225.71 | 818.70 | empirical_q10_q90 |
| Potato | 89 | 3.56 | -314.25 | 126.27 | empirical_q10_q90 |
| Tomato | 152 | 3.56 | -724.09 | 714.17 | empirical_q10_q90 |

## In-sample coverage (sanity check, not an out-of-sample claim)

Share of scored residuals falling inside their own horizon's
band. By construction the pooled band covers ~80% at the mean
horizon; per-horizon numbers will drift as more scored rows
arrive.

- Onion: 85.3% inside (n=34)
- Potato: 77.5% inside (n=89)
- Tomato: 89.5% inside (n=152)

## Today's bands (cross-mandi median, ₹/qtl)

| Commodity | 21 Nov | 22 Nov | 23 Nov | 24 Nov | 25 Nov | 26 Nov | 27 Nov |
|---|---|---|---|---|---|---|---|
| Onion | 2,277 (2,396–2,709) | 2,312 (2,480–2,923) | 2,330 (2,536–3,078) | 2,330 (2,568–3,194) | 2,339 (2,605–3,305) | 2,347 (2,639–3,406) | 2,354 (2,669–3,497) |
| Potato | 1,433 (1,267–1,500) | 1,478 (1,243–1,573) | 1,441 (1,152–1,557) | 1,451 (1,118–1,585) | 1,463 (1,091–1,613) | 1,459 (1,051–1,623) | 1,461 (1,020–1,638) |
| Tomato | 2,323 (1,940–2,702) | 2,318 (1,775–2,853) | 2,326 (1,661–2,982) | 2,324 (1,556–3,081) | 2,325 (1,466–3,171) | 2,321 (1,381–3,249) | 2,320 (1,304–3,321) |

## Hand check

- Azadpur Onion base 2026-11-08 h=1: forecast 3309.70 -> band [3428.85, 3741.90] (empirical q10 225.71 / q90 818.70, h_bar 3.59, scale sqrt(1/3.59)=0.528); actual 4019.00 -> OUTSIDE

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
- Onion's band sits entirely ABOVE its point forecast (q10 is
  +₹226/qtl): on the 34 scored Onion rows
  the model under-predicts every time — the band is reporting a
  real bias, not a symmetric error. A bias correction is a
  follow-up, not today's change.

![Forecast with 80% bands](../charts/confidence_bands_2026-11-22.svg)
