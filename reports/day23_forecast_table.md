# Day 23 — 7-day price forecast table in the daily report

## Method (read this first)

The champion model from Weeks 2–3 — plain OLS on lag1/lag2/lag3
per commodity, pooled across the 8 mandis (Day 22: ridge
regularisation is a verified null, alpha=0; Day 18/19: OLS
beats MA3 and the random forest out-of-sample) — is refitted
on **all history known as of today** and run recursively:
day h=1 uses real lags from the latest prices, days h=2..7
feed the previous forecasts back in as lags. No future
information enters at any step. The portal's National rows
are an all-India aggregate with a 3-day series, so they never
clear the 3-lag requirement and are excluded — the forecasts
run on the 8 mandi series (latest actual date
12 Nov 2026), exactly like the earlier scoring days.

## Empirical error scale

Walk-forward: refit on history up to 7 days ago, then
one-step-ahead on the last 7 days, per commodity:

| Commodity | Walk-forward 1-day MAE (₹/qtl) | n |
|---|---|---|
| Onion | 419.12 | 21 |
| Potato | 165.44 | 18 |
| Tomato | 341.96 | 18 |

The table below shows **point forecasts**. A fair mental
band is ±(1-day MAE × horizon): error compounds because each
forecast day reuses the previous day's forecast as a lag.
The forecast also inherits whatever drift the last 3 days
carried — a 7-day OLS forecast cannot predict a shock.

## 7-day forecast table

### Onion — latest actual 12 Nov 2026

| Market | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov | 19 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 3,976 | 3,867 | 3,765 | 3,655 | 3,559 | 3,470 | 3,387 |
| Bowenpally | 2,267 | 2,282 | 2,314 | 2,307 | 2,310 | 2,315 | 2,318 |
| Koyambedu | 2,401 | 2,396 | 2,415 | 2,404 | 2,399 | 2,398 | 2,394 |
| Muhana | 2,119 | 2,132 | 2,156 | 2,169 | 2,183 | 2,196 | 2,208 |
| Naroda | 2,502 | 2,460 | 2,490 | 2,472 | 2,461 | 2,455 | 2,448 |
| Sealdah Koley Market | 2,294 | 2,330 | 2,323 | 2,324 | 2,329 | 2,330 | 2,332 |
| Vashi | 2,142 | 2,154 | 2,163 | 2,180 | 2,194 | 2,205 | 2,217 |
| Yeshwanthpur | 2,107 | 2,140 | 2,149 | 2,165 | 2,180 | 2,193 | 2,205 |

### Potato — latest actual 12 Nov 2026

| Market | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov | 19 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 1,266 | 1,306 | 1,326 | 1,362 | 1,386 | 1,402 | 1,419 |
| Bowenpally | 1,466 | 1,458 | 1,478 | 1,477 | 1,475 | 1,480 | 1,481 |
| Koyambedu | 1,599 | 1,565 | 1,613 | 1,566 | 1,542 | 1,543 | 1,531 |
| Muhana | 1,429 | 1,415 | 1,430 | 1,448 | 1,451 | 1,457 | 1,464 |
| Naroda | 1,552 | 1,502 | 1,534 | 1,522 | 1,506 | 1,508 | 1,504 |
| Sealdah Koley Market | 1,446 | 1,545 | 1,505 | 1,486 | 1,502 | 1,497 | 1,491 |
| Vashi | 1,460 | 1,488 | 1,434 | 1,460 | 1,474 | 1,467 | 1,472 |
| Yeshwanthpur | 1,434 | 1,485 | 1,467 | 1,466 | 1,477 | 1,477 | 1,477 |

### Tomato — latest actual 12 Nov 2026

| Market | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov | 19 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 2,242 | 2,257 | 2,269 | 2,280 | 2,287 | 2,292 | 2,297 |
| Bowenpally | 1,857 | 1,964 | 2,023 | 2,108 | 2,159 | 2,194 | 2,224 |
| Koyambedu | 2,450 | 2,361 | 2,418 | 2,372 | 2,350 | 2,346 | 2,335 |
| Muhana | 2,150 | 2,204 | 2,189 | 2,234 | 2,255 | 2,265 | 2,277 |
| Naroda | 2,608 | 2,484 | 2,492 | 2,434 | 2,397 | 2,380 | 2,361 |
| Sealdah Koley Market | 2,599 | 2,533 | 2,489 | 2,437 | 2,405 | 2,382 | 2,363 |
| Vashi | 2,424 | 2,397 | 2,364 | 2,354 | 2,343 | 2,334 | 2,328 |
| Yeshwanthpur | 2,214 | 2,269 | 2,274 | 2,279 | 2,289 | 2,294 | 2,297 |

## Verification

Hand-check on Azadpur Onion: recomputing h=1 and h=2 from the
coefficients by hand gives Rs 3975.61 and Rs 3867.08/qtl —
both **match** the module output exactly, so the recursion is
verified. Re-running the script produces a byte-identical CSV
(deterministic), and the chart parses as valid SVG.

## Reading the result

Prices are strongly autocorrelated day to day, so h=1
forecasts mostly say 'tomorrow looks like yesterday, pulled
slightly toward the last few days'. By h=7 the forecast has
converged toward the series' recent drift — treat day 5–7
values as directional, not precise. This table now ships in
every daily report via run_daily.py (forecast_table.py runs
right after analyze.py), so tomorrow's report will carry a
fresh 7-day table automatically. Day 24's rolling-MAE
dashboard will start tracking these forecasts against
realised prices as they arrive.

![7-day forecast](../charts/forecast_7day_2026-11-14.svg)
