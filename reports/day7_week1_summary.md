# MandiLens — Day 7 · Week-1 summary (17 Oct 2026)

*Pipeline + EDA week. All numbers recomputed on the full dataset: 432 rows,
18/19 calendar days (2026-09-29 → 2026-10-17), 8 mandis, 3 commodities
(Onion, Potato, Tomato).*

## What Week 1 built

| Day | Item | Finding |
|---|---|---|
| 1 | Repo scaffold, fetch/clean/analyze/visualize pipeline, first daily report | Pipeline runs end-to-end; README carries the daily block |
| 2 | Missing-data audit | Every covered day ships all 8 mandis × 3 commodities; 94.7% calendar coverage |
| 3 | Price distributions | Near-symmetric (skew −0.03…+0.16), zero IQR outliers |
| 4 | Geographic spread | Maharashtra cheapest, Gujarat costliest for all 3; 36–40% inter-state spreads |
| 5 | Arrival-date gaps | One 1-day gap (2026-10-13); feed freshness 0 days |
| 6 | Variety & grade premiums | Market-adjusted premiums ≈ 0 (±2.5%); grade premium unmeasurable (FAQ only) |
| 7 | Week-1 summary report + EDA notebook | This report + `notebooks/01_week1_eda.ipynb` |

## Key EDA numbers (full window)

- **Coverage:** 432 rows; 18 of 19 calendar days; single missing day 2026-10-13; longest gap 1 day.
- **Distributions (modal price ₹/q):** Onion skew +0.026, Potato −0.030, Tomato +0.162; IQR outliers: 0 / 0 / 0.
- **Geography (state median modal price ₹/q):**

  | State | Onion | Potato | Tomato |
  |---|---|---|---|
  | Maharashtra | 1,815 | 1,270 | 1,980 |
  | Gujarat | 2,525 | 1,720 | 2,635 |

  Inter-state spread (max−min)/min: Onion 39.1%, Potato 35.4%, Tomato 33.1%.
- **Variety premiums vs market median:** Onion Red −0.5% / White +1.1%; Potato Chipsona +1.3% / Jyoti +0.2%; Tomato Desi +2.5% / Hybrid −1.6% — noise, as expected on variety-independent data.
- **Grade:** feed reports only FAQ — grade premium unmeasurable.

## Data-quality caveat

The Agmarknet portal has returned a hard 403 all week (no login barrier, no CAPTCHA — just blocked), so Week 1 ran on deterministically seeded sample rows. The statistics above describe the **pipeline's** shape, not live market prices. The daily keyless-pull attempt continues unchanged; the day the portal answers, every number above re-computes from real tables with no code change.

## The EDA notebook

`notebooks/01_week1_eda.ipynb` consolidates all six EDA strands with embedded
charts — the single entry point for anyone reviewing Week 1. Regenerate with
`python3 tools/build_week1_notebook.py`.

## Week 2 preview

Outlier-detection rules (Day 8) → commodity volatility index (9) → MSP gap
analysis (10) → arrival-vs-price dynamics (11) → weekday effects (12) →
animated trend chart (13) → week-2 summary + chart gallery refresh (14).
