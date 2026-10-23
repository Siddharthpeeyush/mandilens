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
- [ ] Day 13: animated price-trend chart
- [ ] Day 14: week-2 summary + chart gallery refresh

## Week 3 — Feature engineering + Forecasting baselines (Days 15–21)
- [ ] Day 15: lag/rolling features (3-day, 7-day moving averages)
- [ ] Day 16: naive baselines — persistence & moving-average forecasts
- [ ] Day 17: linear regression on lag features, per commodity
- [ ] Day 18: train/test split by time + MAE/RMSE evaluation
- [ ] Day 19: random forest regressor, feature importances
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
