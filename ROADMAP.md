# MandiLens — 30-day build roadmap

A living data-science project: every day at 7 PM IST the pipeline fetches fresh
mandi prices, extends the analysis, and commits. Each week adds a new layer.

## Week 1 — Pipeline + Exploratory Data Analysis (Days 1–7)
- [x] Day 1: repo scaffold, fetch/clean/analyze/visualize pipeline, first daily report
- [ ] Day 2: missing-data audit — which mandis/commodities report irregularly?
- [ ] Day 3: price distributions per commodity (histograms, skew, outliers)
- [ ] Day 4: geographic spread — state-wise median price heatmap
- [ ] Day 5: arrival-date gaps — how "daily" is the feed really?
- [ ] Day 6: variety & grade price premiums (Red vs White onion, etc.)
- [ ] Day 7: week-1 summary report + EDA notebook

## Week 2 — Cleaning deep-dive + Visual storytelling (Days 8–14)
- [ ] Day 8: outlier detection rules (IQR vs z-score on modal prices)
- [ ] Day 9: mandi volatility index — rank mandis by price stability
- [ ] Day 10: cheapest-basket analysis — where would a bulk buyer shop?
- [ ] Day 11: inter-mandi price spread per commodity (arbitrage gaps)
- [ ] Day 12: weekday effects — do prices move on specific days?
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
- [ ] Day 25: Streamlit dashboard — interactive mandi explorer
- [ ] Day 26: data-quality badge (feed freshness monitor)
- [ ] Day 27: full project write-up (methods, findings, limits)
- [ ] Day 28: README + docs polish, chart gallery
- [ ] Day 29: reproducibility check — fresh clone, one-command run
- [ ] Day 30: v1.0 release notes + next-30-days plan

> The daily 7 PM job always runs the pipeline first (fresh data → report → charts),
> then works the next unchecked roadmap item.
