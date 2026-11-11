# Day 32 — Backfill check: 63 per-mandi rows permanently lost

**Date:** 11 Nov 2026 · **Dataset:** 1,104 rows, 29 Sep – 09 Nov 2026 · **Source:** Agmarknet portal tables (keyless browser extract)

## What the portal gave today (window 07–09 Nov 2026, frozen at 09 Nov)

- **National:** 67 rows, 24 commodities. Onion ₹4,563.94/qtl on 09 Nov
  (+9.9% vs 08 Nov ₹4,151.25); Potato ₹884.10 (vs ₹394.20 on 08 Nov,
  **+124.3% in a day** — the sharpest single-day move in the daily log;
  Day 39's alert rule would have tripped); Tomato ₹2,032.98 (+17.4%).
- **Per-mandi:** 12 rows, 3 markets. Azadpur 09 Nov: Onion ₹4,019,
  Potato ₹1,160, Tomato ₹2,186 — flat for the third straight reported
  day. Sealdah Tomato ₹2,800 (09 Nov). Bowenpally: no 09 Nov prices at
  all; Azadpur 08 Nov: still EMPTY on the second consecutive pull.
- Koyambedu + Muhana NOT_FOUND again; APMC Mumbai / Bengaluru APMC
  tables carry no vegetables; Naroda "No Data Available" again.

## The backfill verdict (the Day 32 question)

Of the 11 missing per-mandi days (30 Oct – 09 Nov), how many are
recoverable from the portal's rolling 3-day window vs permanently lost?
Script: `src/backfill_check.py`;
table: `data/processed/backfill_check_2026-11-11.csv`. All 88
market-days (11 days × 8 mandis) accounted for:

| Status | Market-days | Commodity rows | What it means |
|---|---|---|---|
| RECOVERED | 10 | 18 actual (of 30 possible) | 06–09 Nov for Azadpur, Bowenpally, Sealdah — the only 3 mandis whose portal tables ever carry vegetables |
| PERMANENTLY LOST | 21 | **63** | 30 Oct – 05 Nov × 3 reporting markets — slid out of the 3-day window before any per-mandi pull ran |
| RECOVERABLE_TODAY (still in window) | 2 | 6 | Azadpur 08 Nov + Bowenpally 09 Nov |
| NEVER_OBTAINABLE | 55 | 165 | The other 5 mandis yield no vegetable rows from this portal at all |

**The loss, stated plainly:** 63 real per-mandi rows (30 Oct – 05 Nov)
are gone, not delayed — no other source publishes them. Forecasts for
those dates train on the seeded sample feed, and the gap stays visible
in every per-mandi series. The 165 "never obtainable" rows are a
separate, structural fact: the 8-mandi design was never fully
recoverable from this portal, because 5 of the 8 markets cannot yield
vegetable rows here at all.

**The two still in play:** Azadpur 08 Nov showed EMPTY on both the
10 and 11 Nov pulls — the portal published no price that day, so it
will most likely stay empty even though it remains in the 12 Nov
window. Bowenpally 09 Nov gets one more chance in the 12 Nov window
(08–10 Nov). If both stay empty, the final recovered count is 18 rows
and the lost count stands at 63 + 6 = 69 rows for the reporting
markets.

## Pipeline fix made today (not roadmap scope, but the pull exposed it)

`src/parse_browser_extract.py` wrote National + per-mandi rows into one
file. The Day 31 convention needs them split — the site builder and the
backfill check detect real per-mandi rows by the `-mandi.csv`
`source_file` suffix, so a merged file would have silently labelled
today's real mandi rows as sample. The parser now writes National to
`mandi_prices_<date>.csv` and per-mandi rows to
`mandi_prices_<date>-mandi.csv` automatically. Verified: re-running the
parser on today's extract reproduces both files byte-identically.

## Numbers that moved

- Dataset 1,062 → **1,104 rows** (+42 net; 79 new rows, 37 overlapping
  07/08 Nov dates deduped).
- Walk-forward 1-day MAE (real prices keep entering the fit): Onion
  ₹293.43 (n=35, was ₹270.84), Potato ₹166.09 (n=37), Tomato ₹302.97
  (n=34). Hand-check Azadpur Onion h=1 ₹3,659.12 / h=2 ₹3,459.15
  matches manual recompute.
- Data-quality badge still **STALE** — latest 09 Nov, lag 2 days
  (portal + mandi both); coverage 97.6% (41/42 days; only 13 Oct
  missing); latest-day completeness 21/24 (87.5%).

## Honest limits (carried)

- The 63-row loss is final; the only remedy is prevention — the daily
  Part B pull must not miss a day, because any missed day is
  unrecoverable 3 days later.
- Azadpur's flat prices (Onion ₹4,019 on 06, 07 and 09 Nov) look
  suspiciously sticky; the portal may be repeating a stale benchmark.
  Flagged, not fixed — worth watching against the next pull.
- Only 3 of 8 mandis yield rows; the per-mandi series for the other 5
  remain sample-only and end 29 Oct.

## Files

- `src/backfill_check.py` — the check (run date arg, extract-window
  aware, deterministic CSV output)
- `src/parse_browser_extract.py` — auto-split National / per-mandi
- `data/raw/mandi_prices_2026-11-11.csv` — 67 rows, National
- `data/raw/mandi_prices_2026-11-11-mandi.csv` — 12 rows, 3 mandis
- `data/processed/backfill_check_2026-11-11.csv` — 88 market-days
- `data/processed/mandi_prices_clean.csv` — 1,104 rows
- `data/README.md` — gap section added, counts updated
- `reports/daily/2026-11-11.md` — daily log (Day 31 numbering per
  analyze.py's date-based day count)
- `ROADMAP.md` — Day 32 marked [x]
