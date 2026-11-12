# Day 24 — Forecast accuracy dashboard (rolling MAE)

Date: 2026-11-12. Every stored 7-day forecast is scored against
actual modal prices. Origin = forecast_date − horizon_days,
exactly the base date the recursive model ran from.

## Coverage

- Forecast origins: 4 (2026-10-29, 2026-11-08, 2026-11-09, 2026-11-10)
- Forecast cells: 672; scored: 16; pending: 656
- Of scored rows, 0 scored against actuals dated on sample-mode days (seeded data — see Limits)

## MAE by horizon (Rs/quintal, scored rows only)

| Horizon | Onion | Potato | Tomato |
|---:|---:|---:|---:|
| h=1 | 628.09 | 140.94 | 122.46 |
| h=2 | 1015.57 | 111.79 | 222.83 |
| h=3 | pending | pending | pending |
| h=4 | pending | pending | pending |
| h=5 | pending | pending | pending |
| h=6 | pending | pending | pending |
| h=7 | pending | pending | pending |

## OLS vs persistence (same scored rows)

- Onion: OLS MAE 757.25 vs persistence 187.00 (n=3)
- Potato: OLS MAE 131.23 vs persistence 0.00 (n=5)
- Tomato: OLS MAE 155.92 vs persistence 33.33 (n=8)

## Rolling 1-day-ahead MAE

- Onion @ 2026-11-08: 709.30 (from 1 origin(s), 1 scored rows)
- Onion @ 2026-11-09: 628.09 (from 2 origin(s), 2 scored rows)
- Potato @ 2026-11-08: 224.27 (from 1 origin(s), 1 scored rows)
- Potato @ 2026-11-09: 140.94 (from 2 origin(s), 3 scored rows)
- Tomato @ 2026-11-08: 90.24 (from 1 origin(s), 2 scored rows)
- Tomato @ 2026-11-09: 122.46 (from 2 origin(s), 5 scored rows)

## Hand check

- Azadpur Onion base 2026-11-08 h=1: forecast 3309.70 vs actual 4019.00 -> abs err 709.30; script 709.30 -> MATCH; origin derivation OK

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
- 2026-11-08 Onion h=3: targets 2026-11-11 (8 series)
- 2026-11-08 Potato h=3: targets 2026-11-11 (8 series)
- 2026-11-08 Tomato h=3: targets 2026-11-11 (8 series)
- 2026-11-08 Onion h=4: targets 2026-11-12 (8 series)
- 2026-11-08 Potato h=4: targets 2026-11-12 (8 series)
- 2026-11-08 Tomato h=4: targets 2026-11-12 (8 series)
- 2026-11-08 Onion h=5: targets 2026-11-13 (8 series)
- 2026-11-08 Potato h=5: targets 2026-11-13 (8 series)
- 2026-11-08 Tomato h=5: targets 2026-11-13 (8 series)
- 2026-11-08 Onion h=6: targets 2026-11-14 (8 series)
- 2026-11-08 Potato h=6: targets 2026-11-14 (8 series)
- 2026-11-08 Tomato h=6: targets 2026-11-14 (8 series)
- 2026-11-08 Onion h=7: targets 2026-11-15 (8 series)
- 2026-11-08 Potato h=7: targets 2026-11-15 (8 series)
- 2026-11-08 Tomato h=7: targets 2026-11-15 (8 series)
- 2026-11-09 Onion h=2: targets 2026-11-11 (8 series)
- 2026-11-09 Potato h=2: targets 2026-11-11 (8 series)
- 2026-11-09 Tomato h=2: targets 2026-11-11 (8 series)
- 2026-11-09 Onion h=3: targets 2026-11-12 (8 series)
- 2026-11-09 Potato h=3: targets 2026-11-12 (8 series)
- 2026-11-09 Tomato h=3: targets 2026-11-12 (8 series)
- 2026-11-09 Onion h=4: targets 2026-11-13 (8 series)
- 2026-11-09 Potato h=4: targets 2026-11-13 (8 series)
- 2026-11-09 Tomato h=4: targets 2026-11-13 (8 series)
- 2026-11-09 Onion h=5: targets 2026-11-14 (8 series)
- 2026-11-09 Potato h=5: targets 2026-11-14 (8 series)
- 2026-11-09 Tomato h=5: targets 2026-11-14 (8 series)
- 2026-11-09 Onion h=6: targets 2026-11-15 (8 series)
- 2026-11-09 Potato h=6: targets 2026-11-15 (8 series)
- 2026-11-09 Tomato h=6: targets 2026-11-15 (8 series)
- 2026-11-09 Onion h=7: targets 2026-11-16 (8 series)
- 2026-11-09 Potato h=7: targets 2026-11-16 (8 series)
- 2026-11-09 Tomato h=7: targets 2026-11-16 (8 series)
- 2026-11-10 Onion h=1: targets 2026-11-11 (8 series)
- 2026-11-10 Potato h=1: targets 2026-11-11 (8 series)
- 2026-11-10 Tomato h=1: targets 2026-11-11 (8 series)
- 2026-11-10 Onion h=2: targets 2026-11-12 (8 series)
- 2026-11-10 Potato h=2: targets 2026-11-12 (8 series)
- 2026-11-10 Tomato h=2: targets 2026-11-12 (8 series)
- 2026-11-10 Onion h=3: targets 2026-11-13 (8 series)
- 2026-11-10 Potato h=3: targets 2026-11-13 (8 series)
- 2026-11-10 Tomato h=3: targets 2026-11-13 (8 series)
- 2026-11-10 Onion h=4: targets 2026-11-14 (8 series)
- 2026-11-10 Potato h=4: targets 2026-11-14 (8 series)
- 2026-11-10 Tomato h=4: targets 2026-11-14 (8 series)
- 2026-11-10 Onion h=5: targets 2026-11-15 (8 series)
- 2026-11-10 Potato h=5: targets 2026-11-15 (8 series)
- 2026-11-10 Tomato h=5: targets 2026-11-15 (8 series)
- 2026-11-10 Onion h=6: targets 2026-11-16 (8 series)
- 2026-11-10 Potato h=6: targets 2026-11-16 (8 series)
- 2026-11-10 Tomato h=6: targets 2026-11-16 (8 series)
- 2026-11-10 Onion h=7: targets 2026-11-17 (8 series)
- 2026-11-10 Potato h=7: targets 2026-11-17 (8 series)
- 2026-11-10 Tomato h=7: targets 2026-11-17 (8 series)
