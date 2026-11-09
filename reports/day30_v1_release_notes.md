# Day 30 — MandiLens v1.0 release notes + next-30-days plan

**Release date:** 09 Nov 2026 · **Dataset:** 1,026 rows, 29 Sep – 07 Nov 2026 · **Source:** Government of India's published Agmarknet portal tables (keyless, no API key) + seeded per-mandi sample feed

## What v1.0 is

MandiLens started on 12 Oct 2026 as a 30-day public build log: one fresh pull of
Indian mandi prices every day, one new analysis, one commit. Thirty roadmap
items later it is a working analytics pipeline, a forecasting model with a
measured error, an interactive dashboard, and a live website — all reproducible
from a fresh clone with one command (`python3 src/run_daily.py`, verified
Day 29).

## What shipped (verified counts, 09 Nov 2026)

- **Pipeline:** 30 Python modules in `src/` — fetch (keyless portal extract via
  browser + parser), clean, analyze, visualize, forecast, quality badge,
  Streamlit dashboard. One-command daily run; sample fallback so a blocked
  portal day never crashes the run.
- **Dataset:** 1,026 rows — 306 National benchmark rows from real portal
  tables (24 commodities × 5 groups) + 720 per-mandi rows (8 mandis × Onion /
  Potato / Tomato). 9 markets, 26 commodities, 29 Sep – 07 Nov 2026.
- **Daily output:** 28 daily logs (12 Oct – 09 Nov; only 13 Oct missing —
  97.5% calendar coverage, longest gap 1 day), 27 day reports, 41 raw extracts.
- **Charts:** 92 SVGs in 27 families (price trends, top movers, volatility,
  heatmaps, animated trend, forecast tracking, data-quality badge), gallery in
  `CHART_GALLERY.md`. SVG-only in the repo — zero PNGs tracked.
- **Forecasting:** champion = linear regression on lag1/lag2/lag3, leak-free,
  time-split validated. Out-of-sample MAE on the 24–29 Oct test window:
  **Rs 207.22/qtl overall** (Onion 202.89, Potato 139.91, Tomato 257.95) —
  beats MA3 (217.15), MA7 and persistence, and beats the 80-tree random forest
  (221.60). Ridge search (Day 22) found regularization is a verified null —
  plain OLS ships. Walk-forward 1-day MAE today: Onion ₹208, Potato ₹144,
  Tomato ₹266. A 7-day forecast table auto-appends to every daily report.
- **Dashboard:** Streamlit explorer (`streamlit run src/dashboard.py`) —
  commodity + market selectors, latest price, trend chart, 10-day % changes,
  7-day forecast table, PORTAL/sample source badge.
- **Website:** live at https://mandilens-in.netlify.app — National prices for
  24 commodities, search (English + Hindi), category filter, sort, tap-any-row
  trend chart + MSP, biggest movers, quintal/kg/tonne calculator. Data
  refreshed from the pipeline on every run (`site/build_site.py` →
  `site/data.js`).
- **Docs:** README rewritten to the real tree (Day 28), chart gallery, Week 1 /
  2 / 3 summaries, full project write-up (Day 27), reproducibility check
  (Day 29).

## Findings that held up

- **Volatility ranking is stable across all 30 days:** Potato most stable,
  Tomato most volatile (CV 11.8% vs 15.4%, Day 9; confirmed in every
  re-score since).
- **Maharashtra cheapest, Gujarat costliest** for all three vegetables
  (36–40% inter-state spreads, Day 4).
- **Three honest nulls, all labelled as expected on sample data:** variety /
  grade premiums ≈ 0 (Day 6), arrival ↔ price correlation ≈ 0 (Day 11),
  weekday effects none (ANOVA p = 0.81–0.92, Day 12). The modules re-run
  unchanged on real portal extracts.
- **MSP gap:** 0/3 tracked vegetables have a notified MSP (vegetables aren't
  in the 22 mandated crops) — the gap module activates when a mandated crop
  is added (Day 10).
- **Jowar is today's story:** National Jowar jumped +57.6% in a day
  (₹3,472 → ₹5,472/qtl, 07 Nov); Black Gram +16.7%, Barley +16.1%. Tomato
  fell −10.6% (₹1,957 → ₹1,750), Potato −7.3% (₹964 → ₹893). Onion ₹3,874/qtl
  on 07 Nov, up from ₹3,768 the day before.

## Honest limits (carried into v1.0, not hidden)

1. **Most findings still rest on seeded sample data.** The per-mandi feed
   (8 mandis × 3 vegetables) stopped at 29 Oct 2026 — 11 days stale today.
   Only the National benchmark rows come from the real portal, and those
   resumed only on 30 Oct after an ~18-day bot-wall.
2. **The forecast accuracy dashboard has scored zero forecasts.** Every
   stored 7-day forecast is still PENDING — scoring needs per-mandi actuals,
   which haven't arrived since 29 Oct. The dashboard shows the pending cells
   instead of hiding them.
3. **Portal feed lags 2 days** (latest 07 Nov today) and the portal only
   publishes a 3-day window, so a missed day is gone for good.
4. **Day-number skew:** roadmap labels run one ahead of run-date day numbers
   (today is roadmap Day 30 but run-date Day 29; first run 12 Oct). Noted on
   Day 29, harmless, kept visible rather than silently renumbered.
5. **scikit-learn / Streamlit are not in this environment** — the random
   forest (Day 19) and dashboard (Day 25) need them; the daily path doesn't.

## v1.0 release checklist — all verified today

- [x] Fresh portal pull: 72 rows, 24 commodities, 05–07 Nov 2026 (PORTAL mode)
- [x] Pipeline green: 1,026 rows, daily log + quality badge + forecast table
- [x] Website data refreshed: `site/data.js` (34,328 bytes, 24 commodities on 07 Nov)
- [x] README headline numbers corrected to today's verified state
      (was stale: 978 rows / latest 05 Nov)
- [x] Fresh-clone reproducibility verified (Day 29, commit f21de83)
- [x] SVG-only rule holds; no secrets, no API keys anywhere in the repo

## Next 30 days (Days 31–60) — the plan

**Week 5 — Fix the data gap (the one thing v1.0 can't claim).**
- Day 31: per-mandi portal pull — the portal's market-wise tables exist per
  state/district/market; extend the browser brief to capture the 8 tracked
  mandis directly instead of the National aggregate, so forecasts finally get
  real actuals to score against.
- Day 32: backfill check — how many of the 11 missing per-mandi days are
  recoverable from the portal's 3-day window vs permanently lost; mark the
  loss honestly in the dataset README.
- Day 33: first scored forecast — re-run the accuracy dashboard once real
  per-mandi actuals land; report the first real MAE, however bad.
- Day 34: arrival data quality — the portal's arrival figures are in tonnes
  with Indian-format commas; audit the parser against a second source day.
- Day 35: week-5 summary — data-gap status, first scored forecast.

**Week 6 — Make the forecasts earn their keep.**
- Day 36: expand the champion — add arrival + weekday features to the OLS
  and re-score on the same time split; keep only if out-of-sample MAE improves.
- Day 37: per-mandi forecast table on the website (today the site shows
  National only; the 7-day table lives only in the daily log).
- Day 38: forecast confidence bands — prediction intervals from walk-forward
  residuals, shown on the site chart.
- Day 39: alert rule — flag any commodity moving >10% day-over-day in the
  daily log (Jowar's +57.6% today would have tripped it).
- Day 40: model comparison refresh — re-score all 5 methods on the longer
  window now that real portal rows exist.
- Day 41: seasonality check — 40+ days of data; test for weekly cycles in
  the National series.
- Day 42: week-6 summary.

**Week 7 — Product: the website becomes the point.**
- Day 43: mandi-compare restored on the site with real data (hidden since
  07 Nov because it was seeded sample — unhide only when real per-mandi
  rows exist).
- Day 44: 7-day forecast restored on the site with real data (same rule).
- Day 45: Hindi-first polish — full Hindi labels alongside English on the
  site's main views.
- Day 46: shareable commodity view — deep link per commodity
  (`?c=Onion`) for the daily log.
- Day 47: performance pass — data.js is 34KB and growing; split by
  commodity or compress before it slows the phone load.
- Day 48: week-7 summary + user test — one real user (him) taps through
  every screen on his phone and lists what breaks.

**Week 8 — Close-out: v2.0.**
- Day 49: MSP coverage extension — add one mandated crop with a real MSP
  (Tur/Arhar or Wheat) and activate the Day-10 gap module for real.
- Day 50: data-quality badge v2 — separate portal vs mandi freshness, and a
  "days since last real per-mandi row" counter.
- Day 51: error audit — every "expected null on sample data" re-tested on
  whatever real data exists by then; nulls that survive become findings.
- Day 52: cost/ops note — the whole stack is $0 (GitHub + Netlify free);
  document the running cost and the manual steps (browser extract) so
  anyone can take over the daily run.
- Day 53: v2.0 release notes + Days 61–90 sketch.
- Day 54–60: buffer — the portal bot-wall has already eaten ~18 days once;
  buffer absorbs the next outage without breaking the streak.

## Method note

Every number in the "What shipped" section was re-checked against the files
today (09 Nov 2026) — row counts from `data/processed/mandi_prices_clean.csv`,
chart counts from `charts/`, module count from `src/`, model MAEs from the
Day 18/19/21 reports. Nothing here is carried forward from memory.
