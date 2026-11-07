# Day 28 — README + docs polish, chart gallery refresh — 07 Nov 2026

## What was stale

Three docs had drifted behind the repo they describe:

1. **README.md** — "Currently tracking: 24 commodities" (dataset now 26
   across 9 markets); project structure listed only 5 `src/` files and
   presented the data.gov.in API key as the way to get live data, although the
   daily job has run keyless from the portal since 30 Oct; no mention of the
   chart gallery, the Streamlit dashboard, or the findings so far.
2. **CHART_GALLERY.md** — last regenerated 24 Oct with 37 charts in 15
   families; 84 SVGs existed by today, and the 12 analysis families added in
   Days 15–26 (rolling features, regression, random forest, forecast tracking,
   hyperparameter search, forecast accuracy, data-quality badge, …) had no
   family entry, so they would have landed in an undifferentiated "Other"
   bucket.
3. **data/README.md** — said `data/raw/` "currently holds synthetic sample
   data"; it now holds 30 sample files (12–29 Oct) **and** 9 portal files
   (30 Oct – 07 Nov). Its Columns line also omitted `arrival_tonnes` and
   `msp_rs`.

## What changed

- **README.md**
  - Tracking line now reads 26 commodities / 9 markets (8 mandis + National
    benchmark; the portal itself publishes 24), dataset 978 rows,
    29 Sep – 05 Nov 2026, plus an honest freshness note (portal lag 2 days,
    mandi feed stopped 29 Oct) pointing at the data-quality badge.
  - Project structure rewritten to the real tree: all 14 `src/` modules with
    one-line roles, `tools/build_chart_gallery.py`, `data/README.md`,
    `reports/day*.md`, `CHART_GALLERY.md`, and the SVG-only note for `charts/`.
  - "Run it yourself" now leads with the keyless portal pull
    (`parse_browser_extract.py` + `BROWSER_FETCH_BRIEF.md`), keeps the API key
    as the optional fallback, and adds `streamlit run src/dashboard.py`.
  - New "What the 30 days found (so far)" section: OLS champion (MAE ₹207/qtl),
    volatility ranking, the three honest nulls, links to the Day 21 summary,
    Day 9, Day 27 write-up, and the gallery (84 SVGs, 27 families). Roadmap
    line now says "Currently on Day 28 of 30".
- **tools/build_chart_gallery.py** — 12 new families added
  (rolling_features, naive_baselines, linear_regression, train_test_split,
  random_forest, forecast_tracking, forecast_bias, week3_model_comparison,
  hyperparameter_search, forecast_7day, forecast_accuracy, data_quality_badge);
  `CHART_GALLERY.md` regenerated: **84 charts in 27 families, zero in
  "Other"**.
- **data/README.md** — sample/portal split stated with exact counts and date
  ranges; Layout gains the per-day analysis tables row and the 978-row count;
  Columns line now lists all 12 columns with units and the portal-vs-sample
  price note.

## Verification

- Gallery re-run is byte-identical (md5 `a9ae6e03d15531f782c63308ab3f2e45` before
  and after a second run).
- All 13 relative links in README.md resolve to files that exist; the
  `DAILY-UPDATE` block is intact (Day 27, 07 Nov 2026).
- Every headline number re-checked against the files: 978 rows, 9 markets,
  26 commodities, 2026-09-29 → 2026-11-05, 84 SVGs, 9 portal raw files.

## Known inconsistency (not fixed today)

`run_daily.py` numbers the README block by calendar day (Day 27 for 07 Nov)
while `analyze.py` numbers the daily report by latest data date (Day 25 for
05 Nov) — a 2-day skew that grows whenever the portal lags. Worth a one-line
fix in `run_daily.py`/`analyze.py` on Day 29's reproducibility pass, so a fresh
clone reports one consistent day number.

## Today's data (for the record)

Portal pull, 71 rows (24 commodities × 3 dates, 03–05 Nov; Safflower 03 Nov
price missing on the portal). Dataset now 978 rows. Feed verdict STALE
(portal lag 2 days, mandi lag 9). Biggest mover: Paddy(Common) +35.8% in a day
(₹3,065 → ₹4,161/qtl); Jowar −29.1%.
