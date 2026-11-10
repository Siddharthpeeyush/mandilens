# Day 31 — Per-mandi portal pull (first real per-mandi rows)

**Date:** 10 Nov 2026 · **Dataset:** 1,062 rows, 29 Sep – 08 Nov 2026 · **Source:** Agmarknet portal tables (keyless browser extract) + seeded per-mandi sample feed (ends 29 Oct)

## What changed today

Day 31 of the Days 31–60 plan (reports/day30_v1_release_notes.md): the daily
pull now captures the 8 tracked mandis directly from the portal's
market-wise tables, instead of only the National aggregate. The browser
brief gained a Part B (`src/BROWSER_FETCH_BRIEF.md`) listing each mandi's
State/District/Market; the parser gained `normalize_market()` (strips a
leading/trailing "APMC" so portal names join the existing series); the
per-mandi extract is parsed to a separate file
(`data/raw/mandi_prices_2026-11-10-mandi.csv`) so it never overwrites the
National extract.

## What the portal actually gave (window 06–08 Nov 2026, frozen at 08 Nov)

| Mandi (portal name) | Rows landed | Notes |
|---|---|---|
| APMC Azadpur | 6 (Onion/Potato/Tomato, 06–07 Nov) | 08 Nov prices EMPTY for all three — no row that day |
| Sealdah Koley Market APMC | 3 (Tomato only, 06–08 Nov) | Only 1 record in the whole table; no Onion/Potato |
| Bowenpally APMC | 5 (Potato 06–07 Nov, Tomato 06–08 Nov) | No Onion row in the window |
| APMC Mumbai (= Vashi APMC) | 0 | Table had 8 records, all cereals/oilseeds/pulses — no vegetables |
| Bengaluru APMC (≈ Yeshwanthpur) | 0 | Table had 11 records, all cereals/oilseeds/pulses — no vegetables |
| Ahmedabad (Fruit Market, Naroda) APMC | 0 | Portal: "No Data Available" for these filters |
| Koyambedu | 0 | NOT_FOUND — Chennai dropdown returned "No options found" (×3) |
| Muhana | 0 | NOT_FOUND — searched Jaipur and Jaipur Rural, "No options found" |

**Total: 14 real per-mandi rows across 3 markets.** Verified in
`data/processed/mandi_prices_clean.csv` (source_file =
mandi_prices_2026-11-10-mandi.csv): Azadpur Onion ₹4,019/qtl on both 06 and
07 Nov, Potato ₹1,174 → ₹1,160, Tomato ₹2,186 flat; Bowenpally Tomato
₹1,402.61 → ₹1,400 → ₹1,400; Sealdah Tomato ₹3,200 → ₹3,200 → ₹2,800.

## The headline number: mandi feed lag 12 days → 2 days

The data-quality badge now reports **mandi feed lag 2 days** (latest real
per-mandi row 08 Nov), down from 12 days this morning. Portal feed lag is
also 2 days (National frozen at 08 Nov). Coverage 97.6% (40/41 days; only
13 Oct missing). Verdict still STALE (lag 2 = STALE tier) — the portal
itself is 2 days behind today, not the pipeline.

## Two bugs the real data exposed — both fixed today

1. **Forecast chart crash** (`src/forecast_table.py`, `make_chart`):
   `hist_med.loc[x_hist]` raised `KeyError: Timestamp('2026-11-08')` —
   real portal rows are sparse (no Onion row anywhere on 08 Nov, while
   Sealdah Tomato reported), so the cross-mandi median had no 08 Nov
   point. Fixed with `hist_med.reindex(x_hist)`: missing dates stay NaN
   and the line honestly breaks instead of crashing the daily run.
   Verified: second `run_daily.py` run green end-to-end, chart
   `charts/forecast_7day_2026-11-10.svg` regenerated and valid XML.
2. **Site mislabel** (`site/build_site.py`): the per-mandi block was
   unconditionally labelled sample. The latest-date mandi rows are now
   real portal data, so the builder marks `mandiReal: true` (and swaps
   the note) only when the rows' `source_file` ends `-mandi.csv`.
   Verified: `site/data.js` now reports "2 mandi rows (real, 2026-11-08)".

## Forecast re-score on real prices

Walk-forward 1-day MAE moved once real Azadpur prices entered the fit:
Onion ₹270.84/qtl (was ₹207.68 on sample-only history), Potato ₹168.77,
Tomato ₹301.09. Hand-check Azadpur Onion h=1 ₹3,309.70 / h=2 ₹3,190.43
matches manual recompute. The jump is expected — the sample generator's
smooth drift understated real day-to-day moves — and it is exactly why
Day 33 (first scored forecast) matters.

## Honest limits (carried)

- Only 3 of 8 mandis yielded rows; 5 of 8 are empty for structural portal
  reasons (not listed, no data, or no vegetable rows), not extraction
  errors. Koyambedu and Muhana need a re-check on later days — the
  portal's market lists change.
- APMC Mumbai and Bengaluru APMC are recorded under their portal names,
  NOT relabelled Vashi/Yeshwanthpur — they are the closest listed markets,
  not the same market.
- The portal only publishes a 3-day window, so the 30 Oct – 05 Nov
  per-mandi gap is permanently lost (Day 32's backfill check will confirm
  the count).
- Azadpur reported no 08 Nov prices at all — the "latest" per-mandi date
  is 08 Nov only because Bowenpally/Sealdah Tomato reported that day.

## Files

- `src/BROWSER_FETCH_BRIEF.md` — Part B added, market names corrected to
  the exact portal dropdown values (10 Nov 2026)
- `src/parse_browser_extract.py` — `normalize_market()` (APMC affix strip)
- `src/forecast_table.py` — `reindex` fix in `make_chart`
- `site/build_site.py` — `mandiReal` flag + conditional note
- `data/raw/mandi_prices_2026-11-10-mandi.csv` — 14 rows, 3 markets
- `data/raw/mandi_prices_2026-11-10.csv` — 70 rows, National, 24 commodities
- `ROADMAP.md` — Days 31–60 plan added (Weeks 5–8); Day 31 marked [x]
