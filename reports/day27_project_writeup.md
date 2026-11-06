# Day 27 — MandiLens: full project write-up

*Written 2026-11-06, Day 27 of the 30-day build. This is the project's
methods, findings and limits in one place — everything below is traceable to
a dated day report in `reports/`.*

## 1. What MandiLens is

MandiLens is a daily, public build log of Indian agri-commodity price
analytics. Every evening it pulls the latest published prices, cleans them,
runs one new analysis, regenerates charts, and commits. The goal is a working
data-science portfolio piece — pipeline, exploratory analysis, forecasting
models, and an interactive dashboard — built in the open over 30 days.

- **Repo:** https://github.com/Siddharthpeeyush/mandilens
- **Stack:** Python 3.12, pandas/numpy (analysis), pure-SVG charts
  (matplotlib-free, so charts push as text through the files API), Streamlit
  for the dashboard. No API keys, no paid services.
- **Cadence:** one commit per day; the daily pipeline is
  `python3 src/run_daily.py` (fetch → clean → analyse → visualise →
  data-quality badge → 7-day forecast table → README update).

## 2. Data

### 2.1 Sources

| Feed | What it is | Coverage |
|---|---|---|
| **Agmarknet portal** (Government of India, published tables) | "Market Wise Price & Arrival", National aggregate, 24 commodities across 5 groups (cereals, fibre crops, oil seeds, pulses, vegetables), with MSP, modal price and arrivals for the last 3 days | First pull 2026-10-30 (rows for 26–28 Oct); updated most days since, currently frozen up to **2026-11-04** |
| **Seeded sample** (labelled, in-repo) | 8 mandis × 3 vegetables (Onion, Potato, Tomato), daily modal prices + arrivals | 2026-09-29 → 2026-10-29 (30 dates); the per-mandi series every model is trained on |

The two feeds are kept visibly separate: every report and chart carries a
PORTAL / sample source label, and the data-quality badge (Day 26) reports
each feed's lag independently.

### 2.2 Dataset as of today (2026-11-06)

- **954 rows**, 9 markets, 26 commodities, 36 dates (2026-09-29 → 2026-11-04)
- **Calendar coverage 97.3%** — 36 of 37 days; the only missing date is
  2026-10-13; longest gap 1 day
- **720 per-mandi rows** (8 mandis × 3 commodities × 30 dates) and
  **234 National rows**
- **Latest-day completeness 100%** — all 24 portal commodities priced on
  2026-11-04 (Safflower's 03 Nov price/arrival cells were blank on the portal
  and are recorded as missing, not imputed)
- **Feed status: STALE** — portal lag 2 days, mandi feed lag 8 days
  (per-mandi actuals stop at 29 Oct)

### 2.3 How the portal data is fetched

Agmarknet has no keyless API for this table and its direct HTTP fetch is
bot-walled (403 for ~18 days in October). The working route is a browser
extraction: open https://agmarknet.gov.in/home, submit the default "Go"
query (a text CAPTCHA is solved in the browser), open "Print All Data", and
copy the full 24-row table verbatim into `src/parse_browser_extract.py`,
which writes `data/raw/mandi_prices_<date>.csv`. Nothing is invented,
rounded or "fixed" — a cell shown as "—" becomes EMPTY. If the browser
extraction fails, the pipeline falls back to the existing dataset and says so.

## 3. Methods

### 3.1 Pipeline (Days 1–2)

`fetch → clean → analyse → visualise`, orchestrated by `run_daily.py`.
Cleaning dedupes by (market, commodity, date), keeps the modal price as the
series, and carries `arrival_tonnes` and `msp_rs` alongside. The missing-data
audit (Day 2) established the reporting discipline used ever since: missing
cells are counted and shown, never silently filled.

### 3.2 Exploratory analysis (Week 1, Days 3–7)

- Price distributions per commodity (histograms, skew, IQR outliers)
- Geographic spread: state-wise median-price heatmap
- Arrival-date gaps: how "daily" the feed really is
- Variety & grade premiums (Red vs White onion, etc.)
- Week-1 summary + EDA notebook (`notebooks/01_week1_eda.ipynb`)

### 3.3 Cleaning deep-dive + visual storytelling (Week 2, Days 8–14)

- Outlier rules: IQR (k=1.5) adopted as the pipeline default flag, z-score
  kept as a secondary check
- Commodity volatility index: 100·CV/max(CV), with a mandi-level CV heatmap
- MSP gap analysis: market price vs MSP, with a reusable module that
  activates when a mandated crop is added
- Arrival vs price dynamics: same-day and lag-1 Pearson correlation
- Weekday effects: one-way ANOVA on day-over-day returns
- Animated price-trend chart (pure-SMIL SVG) and a chart gallery
  (`CHART_GALLERY.md`, 80 charts in 15+ families as of today)

### 3.4 Feature engineering + forecasting (Week 3, Days 15–21)

- Lag/rolling features: MA3 and MA7 per market-commodity series
- Naive baselines: persistence, MA3, MA7 forecasts (leak-free — only prices
  up to t−1)
- Linear regression (OLS, numpy least squares) on lag1/lag2/lag3, per
  commodity
- Train/test split **by time** (train 2026-09-29–10-22, test 2026-10-23–28),
  scored with MAE/RMSE/bias/pooled correlation
- Random forest (80 trees, max_depth=6) on lags + MAs, same split
- Forecast-vs-actual tracking chart; week-3 summary re-scoring all five
  methods on one common window

### 3.5 Model tuning + dashboard (Week 4, Days 22–27)

- Hyperparameter search: ridge alpha grid
  {0, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000} on the OLS champion
- 7-day recursive forecast table, auto-appended to every daily report
- Forecast-accuracy dashboard: every stored forecast scored against actuals
  (origin = forecast_date − horizon)
- Streamlit dashboard (`streamlit run src/dashboard.py`): commodity +
  market selectors, latest price, trend chart, 10-day % changes, 7-day
  forecast table, PORTAL/sample source badge — verified with AppTest
  (zero exceptions) and a headless-server 200
- Data-quality badge: FRESH 0–1 / STALE 2–3 / CRITICAL 4+ days, wired into
  every daily report

### 3.6 Verification discipline

Every analysis ships with a check, not just a result: hand-recomputed
values matched to the paisa (Azadpur Onion is the standing worked example),
deterministic re-runs byte-identical, SVGs parsed as valid XML, and chart
sizes kept small enough for the push API (~26–32 KB). Where a check cannot
run — zero scored forecast rows, for example — the report says so instead
of faking a number.

## 4. Findings

### 4.1 Week 1 — the data are well-behaved

- Distributions near-symmetric (skew +0.07 to +0.16); **zero IQR outliers**
  across Onion/Potato/Tomato modal prices.
- **Maharashtra cheapest, Gujarat costliest** for all three vegetables;
  inter-state spreads of 36–40%.
- Feed coverage 94.1% in week 1 (16/17 days); the only hole then, as now,
  was 13 Oct.
- Variety premiums ≈ 0 (Onion −1.6%, Potato −0.1%, Tomato +3.4% — noise);
  grade premium unmeasurable — the feed reports only FAQ grade.

### 4.2 Week 2 — three honest nulls, one real ranking

- **Volatility ranking: Potato most stable, Tomato most volatile.**
  CV: Potato 11.8%, Onion ~13%, Tomato 15.4% (index 76 / 84 / 100).
  Day-to-day swing: Potato 2.3% vs Tomato 5.4%. Hottest cell:
  Koyambedu–Tomato (CV 16.6%).
- **No MSP for the vegetables.** 0 of the 3 tracked commodities has a
  notified MSP — vegetables are not among the 22 mandated crops
  (Kharif+Rabi 2026-27, per PIB). The MSP-gap module is built and waits for
  a mandated crop (e.g. Tur/Arhar, Wheat) to be added. On the portal table
  itself, 21 of 24 commodities carry an MSP; Onion, Potato and Tomato do not.
- **Bigger arrivals do not mean lower prices** (same-day Pearson r ≈ 0 for
  all three: Onion −0.013, Potato +0.057, Tomato −0.018; median lag-1
  r −0.052).
- **No weekday effect.** One-way ANOVA on 504 day-over-day returns:
  Onion p=0.920, Potato p=0.835, Tomato p=0.810.
- The last three are *expected* nulls on the seeded sample (its generator
  has no weekday component and draws arrivals independently of price) —
  they are recorded as such, not as facts about real mandis.

### 4.3 Week 3 — linear regression is the champion

Scored one-step-ahead on the common test window 2026-10-24..29
(144 rows, 8 mandis × 3 commodities × 6 dates):

| Method | MAE (Rs/qtl) | RMSE | Bias | Pooled corr |
|---|---|---|---|---|
| **Linear regression** | **207.22** | 257.36 | +0.76 | 0.806 |
| MA7 forecast | 216.20 | 277.48 | +12.73 | 0.774 |
| Random forest | 221.60 | 274.05 | −3.19 | 0.780 |
| MA3 forecast | 226.97 | 285.65 | −2.11 | 0.765 |
| Persistence | 246.94 | 315.52 | −7.50 | 0.733 |

- Regression wins overall and on 7 of 24 series; it also has the best
  pooled correlation and the smallest bias.
- Random forest (80 trees, depth 6) loses to plain OLS overall — its extra
  capacity buys nothing on this much noise — but still takes Potato
  (151.79 vs 152.82).
- Tomato is hardest to predict (MAE 261.66), matching its Week-2 volatility
  ranking.
- **The honest null:** within a single commodity, no method tracks
  day-to-day wiggles (corr ≈ 0–0.25 for all five). The pooled correlation
  near 0.8 is between-commodity level differences, not foresight.
- The MA3-vs-MA7 order flips by evaluation window (MA3 won Day 16's longer
  window, MA7 won this 6-day one) — the robust finding is "regression
  first, either moving average a distant second, persistence last".

### 4.4 Week 4 — tuning, forecasts, and the dashboard

- **Regularisation is a verified null.** Ridge alpha grid on the OLS
  champion: best alpha = 0 (Onion) and 10000 with ≤0.01 gain
  (Potato/Tomato). Plain OLS ships unchanged.
- **7-day forecast table** runs daily (24 series × 7 days, recursive OLS).
  Walk-forward 1-day MAE as of today: Onion ₹207.68, Potato ₹143.95,
  Tomato ₹265.78 (n=56 each) — consistent with the Week-3 test window.
- **Forecast-accuracy dashboard: still empty, honestly.** All h=1..7 cells
  are PENDING — no per-mandi actuals have arrived since 29 Oct, so there
  is nothing to score the forecasts against. Pending cells are counted and
  shown, never hidden.
- **Streamlit dashboard live** and verified (AppTest + headless 200).
- **Data quality: STALE.** The two feeds go stale on different schedules —
  portal 2 days behind, mandi feed 8 days behind — and the badge shows
  both, so a stale feed can never hide inside a normal-looking report.

### 4.5 Latest snapshot (portal, 04 Nov 2026)

- Biggest rise: **Jowar +32.9%** in a day (₹4,177 → ₹5,553/qtl) — the
  sharpest single-day move in the current data.
- Biggest fall: **Potato −22.9%** (₹1,069 → ₹824/qtl); Tomato −6.2%.
- National Onion ₹3,566/qtl, Potato ₹824, Tomato ₹1,936.

## 5. Limits — read this before reusing anything here

1. **Most findings rest on seeded sample data.** The per-mandi series
   (the only series long enough to train on) is synthetic: variety is
   price-independent, arrivals are independent of price, there is no
   weekday component and no seasonality. The Week-2 nulls and the Week-3
   model ranking are findings *about that generator*, and they must be
   re-tested on real per-mandi history before they mean anything about
   real mandis.
2. **No real per-mandi portal rows yet.** The portal extraction returns the
   National aggregate only. Every per-mandi result (cheapest/costliest
   mandi, all forecasts, all model scores) is still sample-based.
3. **The portal feed is 2 days behind and the mandi feed 8 days behind.**
   The 7-day forecast table is anchored on 29 Oct mandi data; its
   30 Oct–05 Nov cells are already partly in the past and unscored.
4. **Small test window.** The model ranking rests on 6 test days
   (144 rows). The MA3/MA7 flip shows how window-sensitive short
   evaluations are; the ranking needs a longer real test window.
5. **No external drivers.** No rainfall, season, festival, MSP-announcement
   or arrival-shock regressors; no seasonality handling. The models are
   univariate lag models — they capture levels, not wiggles
   (within-commodity corr ≈ 0).
6. **Forecast accuracy is unproven in production.** Zero scored forecast
   rows to date; the accuracy dashboard exists to catch this, and it is
   currently reporting exactly that.
7. **MSP coverage is partial.** Vegetables have no notified MSP, so the
   MSP-gap analysis cannot say anything about Onion/Potato/Tomato.
8. **Portal access is fragile.** Direct fetch is bot-walled; the browser
   extraction depends on a CAPTCHA being solvable and on the "Print All
   Data" view staying available. A portal redesign breaks the fetch, and
   the pipeline then falls back to stale data — by design, and labelled.
9. **National ≠ mandi.** The National aggregate is excluded from the
   cheapest/costliest mandi table for a reason: it is an average, not a
   market, and comparing it with mandis would be a category error.

## 6. What is built, file by file

- `src/run_daily.py` — daily orchestrator; `src/fetch_prices.py`,
  `src/parse_browser_extract.py` — ingestion; `src/clean.py`,
  `src/analyze.py`, `src/visualize.py` — core pipeline
- `src/rolling_features.py`, `src/naive_baselines.py`,
  `src/linear_regression.py`, `src/train_test_split.py`,
  `src/random_forest.py`, `src/hyperparameter_search.py`,
  `src/forecast_table.py`, `src/forecast_tracking.py`,
  `src/forecast_accuracy.py` — features, models, scoring
- `src/data_quality_badge.py` — freshness monitor
- `src/dashboard.py` — Streamlit explorer
- `src/msp_data.py`, `src/msp_gap_analysis.py`, `src/outlier_rules.py`,
  `src/volatility_index.py`, `src/weekday_effects.py`,
  `src/arrival_price_dynamics.py`, `src/arrival_gaps.py`,
  `src/geographic_spread.py`, `src/variety_premiums.py`,
  `src/price_distributions.py`, `src/missing_data_audit.py`,
  `src/animate_trend.py`, `src/week3_summary.py` — analyses
- `data/raw/` (one CSV per day), `data/processed/` (clean master +
  per-analysis tables), `charts/` (80 SVGs), `reports/` (25 day reports +
  25 daily logs — 2026-10-13 has no log, the one missing data day),
  `notebooks/01_week1_eda.ipynb`
- `ROADMAP.md` — the 30-day plan; `CHART_GALLERY.md` — chart index;
  `LESSON.md` — build lessons; `README.md` — project front page

## 7. What comes next (Days 28–30)

- Day 28: README + docs polish, chart gallery refresh
- Day 29: reproducibility check — fresh clone, one-command run
- Day 30: v1.0 release notes + next-30-days plan

The single most valuable next step after Day 30 is a real per-mandi portal
feed: until per-mandi actuals flow, every model result stays a
sample-data result, and the forecast-accuracy dashboard stays empty.
