# Day 44 — 7-day forecast restored on the website (real portal data)

## What changed

The forecast section was unhidden on Day 37, but it was not yet "with
real data": it showed a 22–28 Nov forecast for all 8 mandis × 3
commodities, while only 6 of those 24 series are backed by a real
portal price — the other 18 are anchored to seeded sample rows from
29 Oct 2026 (the 5 never-reporting mandis, plus Sealdah Onion/Potato
and Bowenpally Onion). The section's own note even claimed "empty
cells mean no forecast for that mandi" — but there were no empty cells
at all. The Day 43 rule (show only real-data-backed content) now
applies to the forecast too:

- `site/build_site.py`: a forecast series reaches `data.js` only when
  its latest actual price is a real portal row (`-mandi.csv`) dated the
  latest per-mandi date (the forecast window's base). Sample-anchored
  series are dropped at the site layer; the pipeline CSV keeps all 24.
  `meta.forecastReal` lists what is shown, so the note can name it.
- `site/app.js`: the forecast note is now derived from `data.js` — it
  names the real-backed series (Azadpur Onion/Potato/Tomato, Bowenpally
  Potato/Tomato, Sealdah Tomato) and says the rest show "—". Also
  dropped the stale "won the Day-21 comparison (MAE ₹207)" claim — Day
  40 flipped that verdict on real data; the note now shows the current
  walk-forward MAE only. The About row count is filled from
  `D.meta.rows` instead of the hardcoded "978 rows" (stale since the
  dataset passed 1,000; Day 43 flagged it as the next About touch).
- `site/index.html`: forecast-section comment updated to the Day 44
  state; About "full dataset" line now a `<span id="aboutRows">`.
- `site/README.md`: restored-state blockquote records Day 44.

## Verification (headless Chrome, CDP, file:// render)

BEFORE (same render, pre-fix): all 8 mandis × 7 dates filled on every
tab — e.g. Onion: Vashi ₹2,142, Koyambedu ₹2,403, Sealdah ₹2,296,
Naroda ₹2,506, Muhana ₹2,117 — sample-anchored values presented next
to Azadpur's real ₹3,665. Zero empty cells.

AFTER: Onion tab — only Azadpur has values (₹3,665 → ₹3,269, h=1..7),
7 mandis "—". Potato tab — Azadpur (₹1,249 → ₹1,389) + Bowenpally
(₹1,276 → ₹1,398), rest "—". Tomato tab — Azadpur (₹2,051 → ₹2,200),
Sealdah (₹2,983 → ₹2,584), Bowenpally (₹1,698 → ₹2,062), rest "—".
Note reads: "Shown only where a mandi's latest price is a real
Agmarknet row — Azadpur (Onion, Potato, Tomato), Bowenpally (Potato,
Tomato), Sealdah (Tomato). Other mandis show —: they have not reported
real prices." About row count renders "1,478". Forecast window
22–28 Nov 2026, generated 23 Nov, from prices to 21 Nov. Screenshots:
`/tmp/mandilens_day44_before.png` / `/tmp/mandilens_day44_after.png`
(kept outside the repo; re-render any time from site/index.html).

## Today's data (portal, 19–21 Nov 2026)

Browser extract: National 24 rows (Total Records 24.00, Print All Data)
+ per-mandi 18 rows. 3 of 8 mandis reported: Azadpur (Onion ₹3,563 /
₹4,206 / ₹4,206, Potato ₹1,163 flat, Tomato ₹1,931 / ₹1,931 /
₹2,064), Sealdah Koley Market (Tomato ₹3,200 flat), Bowenpally
(Potato ₹1,200 flat, Tomato ₹1,500 flat). APMC Mumbai (8 rows) and
Bengaluru APMC (13 rows) loaded but have no Onion/Potato/Tomato rows;
Ahmedabad returned "No Data Available"; Koyambedu and Muhana still
NOT_FOUND in the market dropdowns (same as 10 Nov 2026). Portal states
data frozen up to 21 Nov 2026. Dataset now 1,478 rows; feed STALE, lag
2 days (latest 21 Nov); coverage 98.1% (53/54 days, only 13 Oct
missing); latest-day completeness 24/24 (100%).

Biggest moves 20 → 21 Nov: Potato National +20.7% (₹559 → ₹675),
Tomato National +12.0% (₹1,784 → ₹1,999), Onion National +6.8%
(₹3,310 → ₹3,534); Copra −23.2% (₹21,750 → ₹16,708), Onion Azadpur
−15.3% (₹4,206 → ₹3,563), Sesamum −14.1%, Jowar −12.2%. 6 alerts of
30 series. Walk-forward 1-day MAE: Onion ₹406 (n=7), Potato ₹167
(n=11), Tomato ₹262 (n=18). Confidence bands scored: Onion 41,
Potato 103, Tomato 173 forecasts, all on real portal actuals.

## Notes

- The pipeline (forecast_table.py) still forecasts all 24 series and
  the daily log still lists them — only the public site is filtered.
  A series reappears on the site the day its mandi reports a real row.
- Pre-existing nit, untouched: the note renders "onion 41 scored,
  potato 103 scored, tomato 173 scored forecasts scored" — the
  bandNoteText suffix doubles the word "scored". Cosmetic; fix with
  the next note touch.
- The daily log is Day 44 · 21 Nov 2026 (data date, not run date — the
  portal runs 2 days behind).
