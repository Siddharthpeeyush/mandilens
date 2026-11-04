# Day 25 — Streamlit dashboard: interactive commodity explorer (2026-11-04)

## What I built
`src/dashboard.py` — a Streamlit app ("MandiLens — commodity price explorer"), keyless and
offline: it reads the flat CSVs the daily pipeline already produces
(`data/processed/mandi_prices_clean.csv` + latest `data/processed/forecast_table_*.csv`).

Sidebar picks commodity (Onion/Potato/Tomato pinned first, then 23 portal commodities)
and market. The page shows: latest modal-price metric for the pair, a price-trend chart,
the last 10 day-over-day % changes, and the OLS champion's 7-day forecast table.
A caption line states row/market/commodity counts, the latest date, and the data mode
(PORTAL vs sample) — the same honesty rule as the daily reports.

Run it: `streamlit run src/dashboard.py` (added `streamlit>=1.66` to requirements.txt).

## Verification (all pass)
- Headless data check: 907 rows, 9 markets, 26 commodities load; Azadpur Onion latest
  2026-10-29 Rs 2,310/qtl; forecast table has 7 rows with h=1 Rs 2219.74 matching the
  pipeline's own hand-check.
- `streamlit.testing.v1.AppTest`: full app run renders with zero exceptions — title,
  metric "Onion in Azadpur — latest modal price: Rs 2,310/qtl", 2 dataframes, 26
  commodity options.
- Interaction path: selectbox reselect to Potato/Vashi re-renders correctly
  ("Potato in Vashi — latest modal price: Rs 1,280/qtl"), no exceptions.
- Live headless server on :8502 returned HTTP 200 with no script errors in the log.
- Fixed along the way: deprecated `use_container_width` → `width="stretch"`, and a
  `round(2)` on the mixed date column.

## Limits
- The app is local (`streamlit run`); no public deployment yet — that's a Day 26+ call.
- Streamlit shells are JS apps: the curl check only proves the server runs; the AppTest
  run proves the Python script renders.
