# Day 37 — Per-mandi forecast table on the website

## What changed

The 7-day price outlook is now live on the site — the same per-mandi table
that used to live only in the daily log. The section had been hidden since
07 Nov 2026 because the forecast was built on the seeded sample series; the
table itself (8 mandis × 3 commodities, window = latest per-mandi date
+1..+7) was already in `site/data.js` — only the section was hidden and the
copy was stale.

- `site/index.html`: forecast section unhidden, "Forecast" nav link
  restored, About-the-data forecast bullet restored (text filled by JS).
  Mandi compare stays hidden — Day 43 owns that restore, same real-data rule.
- `site/app.js`: the forecast sub-heading, note and About bullet are now
  derived from `data.js` every load — window dates, latest-actual date and
  per-commodity MAE. The old copy was hardcoded to "30 Oct – 5 Nov 2026,
  from data to 29 Oct 2026" and would have gone stale again the day after
  any restore; that class of bug is gone.
- `src/forecast_table.py`: writes a `data/processed/forecast_mae_YYYY-MM-DD.json`
  sidecar with the walk-forward 1-day MAE per commodity (and n) on every run.
- `site/build_site.py`: `meta.mae` now reads the latest MAE sidecar. The
  Day-23 values (Onion ₹208 / Potato ₹144 / Tomato ₹266) were hardcoded and
  are no longer true — see below. Fallback to those values only if no
  sidecar exists.

## Today's data (portal, 12–14 Nov 2026)

Browser extract: National 25 rows (Total Records 25, verified against Print
All Data) + per-mandi 9 rows. Only 2 of 8 mandis reported: Sealdah Koley
Market Tomato ₹2,800 flat all 3 days; Bowenpally Potato ₹1,400/₹1,400/₹1,500
and Tomato ₹1,000/₹1,400/₹1,500. Azadpur and Naroda returned "No Data
Available" after captcha-accepted Go attempts (3 and 2 attempts); APMC
Mumbai and Bengaluru APMC loaded but have no vegetable rows; Koyambedu and
Muhana are still NOT_FOUND in the market dropdowns. Dataset now 1,251 rows;
feed STALE, lag 2 days (latest 14 Nov); coverage 97.9% (46/47 days, only
13 Oct missing).

Biggest moves 13 → 14 Nov: Copra +41.2% (₹19,822 → ₹27,988), Lentil +23.3%,
Sesamum +10.3%; Bowenpally Tomato −28.6% (₹1,400 → ₹1,000), Jowar −11.2%.

## Verification (headless Chrome via CDP, file:// site)

- Forecast section `hidden: false`; nav shows the Forecast link.
- Table renders 8 mandi rows × 7 date columns (15–21 Nov 2026) for Onion,
  with 0 empty cells; switching to the Potato tab re-renders (Azadpur
  ₹1,265 → ₹1,417 across the week).
- Sub-heading reads "Model outlook for 15 Nov 2026 – 21 Nov 2026, generated
  16 Nov 2026 from per-mandi prices to 14 Nov 2026"; note and About bullet
  show the current MAE (below). Screenshot of the rendered section:
  `/tmp/mandilens_day37_forecast.png` (kept in /tmp, not pushed).
- Hand-check still MATCH: Azadpur Onion h=1 ₹3,975.61, h=2 ₹3,867.08.
  Deterministic re-run of forecast_table.py reproduces the CSV.

## Honest caveats (shown on the site, not hidden)

- The forecast is fit on per-mandi history that mixes seeded sample
  (29 Sep – 29 Oct 2026) with real portal rows from 10 Nov — the note on
  the site says so. The sample share shrinks as real rows accumulate.
- Typical 1-day error is now WORSE than the stale Day-23 numbers the site
  used to show: Onion ₹419 (n=21) vs ₹208, Potato ₹126 (n=10) vs ₹144,
  Tomato ₹291 (n=16) vs ₹266. The walk-forward window now includes real
  portal actuals, which are more volatile than the seeded sample — the site
  shows the current numbers, not the flattering old ones.
- Azadpur did not report today, so its forecast values are unchanged from
  yesterday's run, relabelled one day forward (15–21 Nov instead of
  14–20 Nov). That is correct behaviour for a sparse series — the model
  forecasts from each series' own last 3 actuals — but it means the Azadpur
  column carries no new information today.

## Files

- `site/index.html`, `site/app.js`, `site/build_site.py`, `site/data.js`
- `src/forecast_table.py`, `data/processed/forecast_mae_2026-11-16.json`
- `data/raw/mandi_prices_2026-11-16.csv` (73 rows),
  `data/raw/mandi_prices_2026-11-16-mandi.csv` (9 rows)
- `data/processed/forecast_table_2026-11-16.csv`,
  `data/processed/data_quality_2026-11-16.csv`,
  `reports/daily/2026-11-16.md`, `reports/day37_per_mandi_forecast_on_site.md`
- `charts/forecast_7day_2026-11-16.svg`,
  `charts/data_quality_badge_2026-11-16.svg`,
  `charts/price_trends_2026-11-16.svg`, `charts/top_movers_2026-11-16.svg`
