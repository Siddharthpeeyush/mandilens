# MandiLens — 30-day build roadmap

My 30-day data-science build log: every day I pull fresh mandi prices, extend the
analysis, and commit. Each week adds a new layer.

## Week 1 — Pipeline + Exploratory Data Analysis (Days 1–7)
- [x] Day 1: repo scaffold, fetch/clean/analyze/visualize pipeline, first daily report
- [x] Day 2: missing-data audit — which mandis/commodities report irregularly?
- [x] Day 3: price distributions per commodity (histograms, skew, outliers) — 2026-10-13: histograms near-symmetric (skew +0.07–+0.16), zero IQR outliers across Onion/Potato/Tomato
- [x] Day 4: geographic spread — state-wise median price heatmap — 2026-10-14: Maharashtra cheapest for all 3 vegetables, Gujarat costliest; 36–40% inter-state spreads (src/geographic_spread.py, charts/state_heatmap_*.svg)
- [x] Day 5: arrival-date gaps — how "daily" is the feed really? — 2026-10-15: 94.1% calendar coverage (16/17 days, only 2026-10-13 missing), longest gap 1 day, feed freshness 0 days (src/arrival_gaps.py, charts/arrival_gaps_2026-10-15.svg, reports/day5_arrival_date_gaps.md)
- [x] Day 6: variety & grade price premiums (Red vs White onion, etc.) — 2026-10-16: market-adjusted premiums ≈ 0 (Onion −1.6%, Potato −0.1%, Tomato +3.4% — noise, as expected on seeded sample where variety is price-independent); grade premium unmeasurable — feed reports only FAQ (src/variety_premiums.py, charts/variety_premiums_2026-10-16.svg, reports/day6_variety_grade_premiums.md)
- [x] Day 7: week-1 summary report + EDA notebook — 2026-10-17: 432 rows over 18/19 calendar days, spreads Onion 39.1%/Potato 35.4%/Tomato 33.1%, Maharashtra cheapest / Gujarat costliest for all 3, variety premiums ≈ 0; consolidated notebook with embedded SVG charts (tools/build_week1_notebook.py, notebooks/01_week1_eda.ipynb, reports/day7_week1_summary.md)

## Week 2 — Cleaning deep-dive + Visual storytelling (Days 8–14)
- [x] Day 8: outlier detection rules (IQR vs z-score on modal prices) — 2026-10-18: both rules flag 0 points on 152 modal prices/commodity (consistent with Day 3's near-symmetric distributions); rules verified working, IQR (k=1.5) adopted as pipeline default flag, z-score kept as secondary check (src/outlier_rules.py, charts/outlier_rules_2026-10-18.svg, reports/day8_outlier_detection_rules.md)
- [x] Day 9: commodity volatility index — rank commodities by price stability — 2026-10-19: index = 100·CV/max(CV): Potato #1 most stable (76, CV 11.8%), Onion #2 (84), Tomato #3 most volatile (100, CV 15.4%); robust IQR/median agrees with CV ranking; day-to-day swing 2.3% (Potato) vs 5.4% (Tomato); mandi-level CV heatmap shows Koyambedu-Tomato (16.6%) as hottest cell (src/volatility_index.py, charts/volatility_index_2026-10-19.svg, reports/day9_commodity_volatility_index.md)
- [x] Day 10: MSP gap analysis — market price vs MSP per commodity (who's above/below support price?) — 2026-10-20: verified finding — 0/3 tracked commodities have a notified MSP (vegetables aren't in the 22 mandated crops, Kharif+Rabi 2026-27 per PIB); coverage audit + reusable gap module built, activates when a mandated crop (e.g. Tur/Arhar, Wheat) is added (src/msp_data.py, src/msp_gap_analysis.py, charts/msp_gap_2026-10-20.svg, reports/day10_msp_gap_analysis.md)
- [x] Day 11: arrival vs price dynamics — do bigger arrivals mean lower prices? — 2026-10-21: schema now carries `arrival_tonnes` (sample + parser; portal bot-wall blocked today's fetch, sample fallback); verified finding — same-day Pearson r ≈ 0 for all 3 commodities (Onion −0.013, Potato +0.057, Tomato −0.018, n=176 each), median lag-1 r −0.052 — expected null on synthetic arrivals, which are drawn independently of price drift; module re-runs unchanged on real portal extracts (src/arrival_price_dynamics.py, charts/arrival_price_dynamics_2026-10-21.svg, reports/day11_arrival_price_dynamics.md)
- [x] Day 12: weekday effects — do prices move on specific days? — 2026-10-22: 504 day-over-day returns across 24 market-commodity series; one-way ANOVA per commodity finds no weekday effect (Onion p=0.920, Potato p=0.835, Tomato p=0.810) — expected null on sample data (generator has no weekday component); module re-runs unchanged on real portal extracts (src/weekday_effects.py, charts/weekday_effects_2026-10-22.svg, reports/day12_weekday_effects.md)
- [x] Day 13: animated price-trend chart — 2026-10-23: pure-SMIL animated SVG (src/animate_trend.py → charts/price_trend_animated_2026-10-23.svg): 3 self-drawing lines with travelling dots, sweeping playhead, date readout, 8s loop; text-only so it pushes via the files API; XML-verified (5 animate + 3 animateMotion + 14 set), ranges cross-checked vs static chart; source label switches with data mode (sample today — Agmarknet 403)
- [x] Day 14: week-2 summary + chart gallery refresh — 2026-10-24: 600 rows over 25/26 calendar days (only 2026-10-13 missing); volatility ranking Potato < Onion < Tomato holds; arrival↔price, weekday and variety nulls honestly labelled as expected on sample data (portal 403 again today); gallery = 37 charts in 15 families (CHART_GALLERY.md, tools/build_chart_gallery.py), summary in reports/day14_week2_summary.md

## Week 3 — Feature engineering + Forecasting baselines (Days 15–21)
- [x] Day 15: lag/rolling features (3-day, 7-day moving averages) — 2026-10-25: 24 series, 576 rows with MA3 / 480 with MA7 (full windows only); hand-check Azadpur Onion MA7 Rs 2220.00 matches rolling output exactly; latest snapshot 12/24 series above MA7, median |dev vs MA7| 12.4%; feature table feeds Day 16 forecasts unchanged (src/rolling_features.py, data/processed/rolling_features.csv, charts/rolling_features_2026-10-25.svg, reports/day15_lag_rolling_features.md)
- [x] Day 16: naive baselines — persistence & moving-average forecasts — 2026-10-26: leak-free forecasts (persistence, MA3, MA7 — all use only prices up to t−1); MA3 forecast wins on all 3 commodities and overall (MAE Rs 187.07/qtl vs persistence 206.81, MA7 197.20); Tomato hardest to predict (MA3 MAE 279.13), matching Day 9 volatility ranking; hand-check Azadpur Onion all 3 forecasts match manual recomputation (src/naive_baselines.py, data/processed/naive_baselines.csv, charts/naive_baselines_2026-10-26.svg, reports/day16_naive_baselines.md)
- [x] Day 17: linear regression on lag features, per commodity — 2026-10-27: pooled OLS per commodity on lag1/lag2/lag3 (numpy least squares, leak-free, in-sample fit on 200 lag-3 rows/commodity); regression beats MA3 on all 3 commodities in-sample (Onion MAE 165.88 vs MA3 175.47, Potato 102.66 vs 107.70, Tomato 265.35 vs 280.53) — Day 18's time-split will test whether the edge survives out-of-sample; hand-check Azadpur Onion fitted value matches manual recomputation (src/linear_regression.py, charts/linear_regression_2026-10-27.svg, reports/day17_linear_regression.md)
- [x] Day 18: train/test split by time + MAE/RMSE evaluation — 2026-10-28: time split (train 2026-09-29–10-22, 552 rows; test final 6/29 dates, 2026-10-23–28, 144 rows scored); regression fitted on train only still beats MA3 on all 3 commodities out-of-sample (Onion 202.89 vs 227.57, Potato 139.91 vs 153.89, Tomato 257.95 vs 270.00) and wins overall (MAE 200.25 vs MA3 217.15, persistence 240.49); test MAE worse than in-sample for Onion (+34.16) and Potato (+33.50), flat for Tomato (−2.01); hand-check Azadpur Onion matches (src/train_test_split.py, charts/train_test_split_2026-10-28.svg, reports/day18_train_test_split.md)
- [x] Day 19: random forest regressor, feature importances — 2026-10-29: 80-tree forest per commodity on lag1/lag2/lag3 + MA3/MA7 (leak-free, max_depth=6, random_state=19), fitted on train only, scored on Day 18's exact test rows; linear regression STILL wins overall (207.22 vs RF 221.60) — RF wins only Potato (151.79 vs 152.82), loses Onion (217.14 vs 207.18) and Tomato (295.88 vs 261.66); importances spread across lags+MAs rather than loading lag1; determinism + importance sums + manual tree-walk all verified (src/random_forest.py, data/processed/random_forest.csv, charts/random_forest_2026-10-29.svg, reports/day19_random_forest.md)
- [ ] Day 20: forecast vs actual tracking chart
- [ ] Day 21: week-3 summary — which model wins so far?

## Week 4 — Model tuning + Dashboard + Polish (Days 22–30)
- [ ] Day 22: hyperparameter search on the best model
- [ ] Day 23: 7-day price forecast table in the daily report
- [ ] Day 24: forecast accuracy dashboard (rolling MAE)
- [ ] Day 25: Streamlit dashboard — interactive commodity explorer
- [ ] Day 26: data-quality badge (feed freshness monitor)
- [ ] Day 27: full project write-up (methods, findings, limits)
- [ ] Day 28: README + docs polish, chart gallery
- [ ] Day 29: reproducibility check — fresh clone, one-command run
- [ ] Day 30: v1.0 release notes + next-30-days plan

> Every day: fresh data → new analysis → charts → commit, then the next unchecked
> roadmap item.
