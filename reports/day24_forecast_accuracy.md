# Day 24 — Forecast accuracy dashboard (rolling MAE)

Date: 2026-11-03. Every stored 7-day forecast is scored against
actual modal prices. Origin = forecast_date − horizon_days,
exactly the base date the recursive model ran from.

## Coverage

- Forecast origins: 1 (2026-10-29)
- Forecast cells: 168; scored: 0; pending: 168
- Of scored rows, 0 scored against actuals dated on sample-mode days (seeded data — see Limits)

## MAE by horizon (Rs/quintal, scored rows only)

| Horizon | Onion | Potato | Tomato |
|---:|---:|---:|---:|
| h=1 | pending | pending | pending |
| h=2 | pending | pending | pending |
| h=3 | pending | pending | pending |
| h=4 | pending | pending | pending |
| h=5 | pending | pending | pending |
| h=6 | pending | pending | pending |
| h=7 | pending | pending | pending |

## OLS vs persistence (same scored rows)

- Onion: no scored rows yet
- Potato: no scored rows yet
- Tomato: no scored rows yet

## Rolling 1-day-ahead MAE


## Hand check

- SKIP: no scored rows at all

## Limits

- The 7-day table started on Day 23; the dashboard accumulates one origin per day, and duplicate runs re-baselined on the same date (portal days add no per-mandi actuals) are deduped to the latest run so pooled MAE never double-counts.
- Recent origins' longer horizons are pending future actuals.
- Scored rows whose actual date fell on a sample-mode day used seeded (synthetic) actuals — the n_actual_sample column counts them; today's real portal pull (if it lands) will steadily replace sample actuals with real ones.

## Pending (not yet scoreable)

- 2026-10-29 Onion h=1: targets 2026-10-30 (8 series)
- 2026-10-29 Potato h=1: targets 2026-10-30 (8 series)
- 2026-10-29 Tomato h=1: targets 2026-10-30 (8 series)
- 2026-10-29 Onion h=2: targets 2026-10-31 (8 series)
- 2026-10-29 Potato h=2: targets 2026-10-31 (8 series)
- 2026-10-29 Tomato h=2: targets 2026-10-31 (8 series)
- 2026-10-29 Onion h=3: targets 2026-11-01 (8 series)
- 2026-10-29 Potato h=3: targets 2026-11-01 (8 series)
- 2026-10-29 Tomato h=3: targets 2026-11-01 (8 series)
- 2026-10-29 Onion h=4: targets 2026-11-02 (8 series)
- 2026-10-29 Potato h=4: targets 2026-11-02 (8 series)
- 2026-10-29 Tomato h=4: targets 2026-11-02 (8 series)
- 2026-10-29 Onion h=5: targets 2026-11-03 (8 series)
- 2026-10-29 Potato h=5: targets 2026-11-03 (8 series)
- 2026-10-29 Tomato h=5: targets 2026-11-03 (8 series)
- 2026-10-29 Onion h=6: targets 2026-11-04 (8 series)
- 2026-10-29 Potato h=6: targets 2026-11-04 (8 series)
- 2026-10-29 Tomato h=6: targets 2026-11-04 (8 series)
- 2026-10-29 Onion h=7: targets 2026-11-05 (8 series)
- 2026-10-29 Potato h=7: targets 2026-11-05 (8 series)
- 2026-10-29 Tomato h=7: targets 2026-11-05 (8 series)
