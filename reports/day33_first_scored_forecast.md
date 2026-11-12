# Day 33 — First scored forecast (real per-mandi actuals)

Date: 2026-11-12. Re-ran the Day-24 accuracy dashboard now that real
per-mandi actuals have landed (Azadpur / Sealdah / Bowenpally, 08–10 Nov).
This is the first time any stored 7-day forecast is scored against real
portal prices instead of seeded sample rows — reported however bad it is.

## Coverage

- Forecast origins: 4 (29 Oct, 08 Nov, 09 Nov, 10 Nov) — 672 cells total
- Scored: **16 rows** (2.4%); pending: 656
- Of the scored rows, **0 are on sample-mode actuals** — all 16 are real
  portal prices (data/processed/forecast_accuracy_2026-11-12.csv)
- Scored by commodity: Onion 3, Potato 5, Tomato 8
- Scored by origin: 08 Nov → 10 rows, 09 Nov → 6 rows
- 168 cells from origin 29 Oct (targets 30 Oct–05 Nov) will **never** score:
  those per-mandi days are permanently lost (Day 32 backfill check) and no
  actuals exist for them in the clean dataset

## First real MAE (OLS champion, recursive lag-123)

| Horizon | OLS MAE (Rs/qtl) | n | Pooled row-weighted OLS | Persistence (same rows) |
|---:|---:|---:|---:|---:|
| h=1 | **297.17** | 10 | 224.02 | 23.38 (n=8 with a base price) |
| h=2 | **450.06** | 6 | 317.94 | 100.00 (Tomato, origin 08 Nov only) |
| h=3..7 | pending | — | — | — |

Headline MAE is the module's mean-of-group-MAEs (as on Day 24); the pooled
column weights each scored row equally. Both are shown because n is tiny.

## Rolling 1-day-ahead MAE (origins to date)

- Onion: 628.09 (origins 08, 09 Nov)
- Potato: 140.94
- Tomato: 122.46

## The honest verdict: the champion loses its first real test

On these 16 rows, **persistence beats OLS** — h=1 pooled 23.38 vs 224.02.
Two reasons, both visible in the data, neither a modelling mystery:

1. **Flat series.** 5 of the 10 h=1 rows come from prices that did not move
   at all: Sealdah Tomato ₹2,800 on 08, 09 and 10 Nov, Azadpur Potato
   ₹1,160 on 09 and 10 Nov. Persistence is perfect by construction on a
   flat series (error 0); no recursive model can beat 0.
2. **Onion jumped and the model under-predicted it.** Azadpur Onion:
   origin 08 Nov forecast ₹3,309.70 vs actual ₹4,019.00 (err 709.30);
   origin 09 Nov forecast ₹3,659.12 vs actual ₹4,206.00 (err 546.88).
   Real scored Onion h=1 MAE (628.09) is roughly double the walk-forward
   1-day MAE the forecast table quotes (₹331.72) — that walk-forward
   figure was computed on sample history, and the real Onion move is
   bigger than the sample's.

Neither point condemns the model yet: n=10 h=1 rows from 2 origins, half
of them flat, is not a verdict — it is a first reading. The dashboard
(chart: charts/forecast_accuracy_2026-11-12.svg) will keep filling as
portal days land; h=3..7 stay pending until their target dates arrive.

## Verification

- Hand-check: Azadpur Onion base 2026-11-08 h=1, forecast 3309.70 vs
  actual 4019.00 → abs err 709.30; script 709.30 → MATCH; origin
  derivation OK
- Determinism: re-ran src/forecast_accuracy.py a second time; the
  accuracy CSV is byte-identical
- Also fixed today: the daily-log Day number was off by one
  (DAY_ONE 12 Oct in src/analyze.py and src/run_daily.py; roadmap Day 1
  is 11 Oct, Day 3 = 13 Oct). Changed both to 11 Oct and re-ran the
  pipeline — the 12 Nov log now correctly reads "Day 33 · 10 Nov 2026"
  and the README "Day 33 — 12 Nov 2026". Pipeline outputs are otherwise
  unchanged (same walk-forward MAEs, same hand-check).

## Files

- data/processed/forecast_accuracy_2026-11-12.csv
- charts/forecast_accuracy_2026-11-12.svg (~31KB)
- reports/day24_forecast_accuracy.md (dashboard report, refreshed)
- reports/day33_first_scored_forecast.md (this report)
