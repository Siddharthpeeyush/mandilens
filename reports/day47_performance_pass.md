# Day 47 — Performance pass: data.js 52KB → 25KB

## Problem

`site/data.js` had grown to 51,937 bytes and was still growing ~1KB/day
(each new trading day adds one point to every National series). At that
rate it crosses the ~60KB push-files comfort zone within weeks, and it is
already a needless weight on a phone load. 80% of the file (41,781 bytes)
was the `series` key: 744 points × one object each, repeating the 10-char
date string and the MSP on every point.

## Change: compress, don't split

The roadmap offered "split by commodity or compress". I compressed:

- `series` is now columnar in `data.js`:
  `{"dates": [...], "data": {commodity: {"i": [date-index...],
  "p": [price...], "a": [arrivals...]}}}` — one shared dates array,
  parallel arrays per commodity.
- Per-point MSP dropped from the series entirely: it is constant per
  commodity (verified: 0 of 44 commodities vary) and the site never reads
  it there — MSP still reaches the site per commodity via `today`.
- `site/app.js` gains one small adapter at load that expands the columnar
  form back to the `[{d, p, a}]` point objects the rest of the file uses
  (guarded, so an old object-per-point `data.js` still works).

Split-by-commodity was considered and rejected: it needs `fetch()`, which
breaks the `file://` preview the daily QA uses, and it would add one
request per commodity on a 2G phone — the opposite of the goal.

## Result

| | Before | After |
|---|---|---|
| `site/data.js` | 51,937 bytes | 25,473 bytes (−51%) |
| `series` key | 41,781 bytes | ~14,000 bytes |
| With today's new day (24 Nov) | — | 26,487 bytes |

Growth is now ~150 bytes/day instead of ~1KB/day.

## Verification

- **Round-trip exact:** expanding the new columnar `data.js` with the same
  logic `app.js` uses reproduces the old per-point format on all 744
  points / 44 commodities — 0 mismatches. The only other difference in
  the file is `meta.generated` (today's date).
- **Headless-CDP render** (desktop 1280 + mobile 390, `file://`):
  24 price rows; Onion detail opens with its 29-point chart drawn
  (₹3,235/quintal, range ₹3,235–₹4,564, −17.3% since 26 Oct 2026);
  mandi + forecast tables render; **0 JS errors**. Screenshots:
  `/tmp/mandilens_day47_{desktop,mobile}.png`.
- Rebuilt after the pipeline with today's data: `data.js` 26,487 bytes,
  23 commodities on 2026-11-24, 6 real mandi rows, 6 forecast series.

## Files

`site/build_site.py` (columnar emit + docstring), `site/app.js`
(expand adapter), `site/data.js` (regenerated), `ROADMAP.md` (Day 47 [x]).

## Today's data note (not Day 47 work, recorded here)

The portal published Safflower at ₹1,43,696.75/qtl for 24 Nov — a 2,100%
jump from ₹6,508.72 on 23 Nov against an MSP of ₹6,540, on 1.02 tonnes
arrival. `clean.py`'s existing sanity cap (modal price < ₹1,00,000)
dropped the row, so today's site shows 23 National commodities and the
daily log counts 29 rows for today. The value is almost certainly a portal
data error, not a market move; the raw extract keeps it for the record.
