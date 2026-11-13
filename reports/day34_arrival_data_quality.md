# Day 34 — Arrival data quality audit

Date: 2026-11-13. The portal's arrival figures are in tonnes with
Indian-format commas (e.g. "1,00,389.39"). This audit checks the parser
against a second source day: every (market, commodity, arrival_date)
that appears in two or more pull-day files is compared across its
sources, and the parser's number handling is unit-tested directly.

## Method

New module `src/arrival_audit.py` (deterministic, byte-identical re-runs):

1. **Unit-test `parse_browser_extract.num()`** on Indian-format strings:
   `1,00,389.39` → `100389.39`, `19,147.87` → `19147.87`,
   `4,151.25` → `4151.25`, `1,00,00,000.00` → `10000000`,
   plus `-` / `EMPTY` / blank → empty. 10/10 pass.
2. **Overlap cross-check**: all raw files `data/raw/mandi_prices_*.csv`
   grouped by (market, commodity, arrival_date); first vs latest
   published value compared for price and arrival.
3. **Parser-bug signature**: exactly one column jumping >10x while the
   other is exact, or the last two pulls still disagreeing >10x. Both
   columns moving together with later pulls converging = portal
   revision, not a parse slip.
4. **Dedup impact**: how many clean-dataset rows differ from the latest
   published value because `clean.py` keeps first-seen.

## Results (data through today's 13 Nov pull)

- Overlapping keys: **369** (18 per-mandi, 351 National)
- Exact on both price and arrival: **219/369**
- **Per-mandi: 18/18 exact** — every per-mandi key reproduced bit-for-bit
  across pulls. Today's pull re-observed 10 per-mandi keys (Azadpur
  Onion/Potato/Tomato 09–10 Nov, Bowenpally Potato/Tomato 10 Nov,
  Sealdah Tomato 09–10 Nov): 0 changed.
- National: 140 of 351 keys revised by the portal. Price revisions are
  small (median |Δ| 0.21%, max 7.04% — Mustard 09/11); arrival revisions
  run larger (median 3.02%, max 49.7% — Jowar 09/11, 69.4 → 34.9 t).
  In 135 of the 140 changed keys price AND arrival moved together;
  0 price-only changes; 5 arrival-only changes, all ≤4.05%.
- **Gross distortions: 0.** No one-column >10x jump, no unsettled key.
- Anomaly scan over all 1,742 raw rows: 0 leftover commas, 0
  non-numeric values, 0 arrival == price, arrivals in plausible ranges
  (per-mandi max 1,841 t Azadpur Onion; National max 458,856 t).

## The Jowar case, resolved

The one extreme in the data — National Jowar(Sorghum) 08/11: arrival
0.3 t → 5.3 t and price ₹3,793.33 → ₹5,941.13 between the 10 Nov and
11 Nov pulls — is thin early reporting, not a parser error: the 11 Nov
and 12 Nov pulls agree exactly, and both columns moved together. The
portal's first morning publication for a date rests on very few
reporting markets; later pulls add markets and revise both figures.
(The same jump is why Day 39's alert rule would have tripped on
Jowar's +57.6% on 09 Nov — the +57% was a revision artefact in the
08/11 base, not a real one-day move.)

## Finding: first-seen dedup keeps superseded values

`clean.py`'s `drop_duplicates` keeps the FIRST pull's value for each
(market, commodity, date). Because the portal revises National figures,
**146 of 354 clean rows on overlapping keys (41%) hold values that
differ from the latest published figure** — e.g. clean Jowar 09/11
arrival is 69.4 t, latest published 34.9 t. Per-mandi rows are
unaffected (18/18 exact across pulls). Recorded in `data/README.md`
("Known gap" section). Recommended follow-up, not done today: decide
deliberately — keep first-seen ("as first published") or switch to
keep-latest ("as finally published") — and record the choice; switching
would rewrite 146 historical values, so it is a data decision, not a
bug fix.

## Verdict

**PASS — the parser is faithful.** Indian-format commas are stripped
correctly, per-mandi arrivals reproduce exactly across independent
pulls, and every National revision moves price and arrival together
the way a late-reporting aggregate should. The arrival column is
trustworthy; the caveat is the dataset's first-seen rule, now
documented rather than silent.

## Verification

- `python3 src/arrival_audit.py` → `VERDICT: PASS — num() 10/10, gross
  distortions 0, per-mandi exact 18/18`; stdout + output CSV
  (`data/processed/arrival_audit_2026-11-13.csv`, 369 rows) byte-identical
  on re-run (md5 `5a512cea10f48ce1a6c47660eb802241`, verified twice).
- Today's pull is itself the second source day: it re-observed 54 keys
  (44 National, 10 per-mandi) first published 11–12 Nov; per-mandi
  10/10 exact, National 19/44 revised within the ranges above.

## Today's data (for the record)

- Portal frozen at 11 Nov 2026 (no 12–13 Nov data published yet).
- National 67 rows (24 commodities, 09–11 Nov); per-mandi 16 rows:
  Azadpur 9, Sealdah Tomato 3, Bowenpally 4 (09 Nov EMPTY at
  Bowenpally). Mumbai / Bengaluru / Naroda NO_ROWS; Koyambedu +
  Muhana NOT_FOUND (unchanged).
- Clean dataset: 1,169 rows, 9 markets, 35 commodities. Feed STALE,
  lag 2 days (portal frozen, not a fetch failure).
- Biggest movers: Copra +25.1%, Ragi +14.6%; Jowar −28.2% (see the
  revision note above — treat with care), Lentil −20.2%.
