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
11 Nov 2026), exactly like the earlier scoring days.

## Empirical error scale

Walk-forward: refit on history up to 7 days ago, then
one-step-ahead on the last 7 days, per commodity:

| Commodity | Walk-forward 1-day MAE (₹/qtl) | n |
|---|---|---|
| Onion | 419.12 | 21 |
| Potato | 167.38 | 25 |
| Tomato | 333.29 | 24 |

The table below shows **point forecasts**. A fair mental
band is ±(1-day MAE × horizon): error compounds because each
forecast day reuses the previous day's forecast as a lag.
The forecast also inherits whatever drift the last 3 days
carried — a 7-day OLS forecast cannot predict a shock.

## 7-day forecast table

### Onion — latest actual 11 Nov 2026

| Market | 12 Nov | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 3,976 | 3,867 | 3,765 | 3,655 | 3,559 | 3,470 | 3,387 |
| Bowenpally | 2,267 | 2,282 | 2,314 | 2,307 | 2,310 | 2,315 | 2,318 |
| Koyambedu | 2,401 | 2,396 | 2,415 | 2,404 | 2,399 | 2,398 | 2,394 |
| Muhana | 2,119 | 2,132 | 2,156 | 2,169 | 2,183 | 2,196 | 2,208 |
| Naroda | 2,502 | 2,460 | 2,490 | 2,472 | 2,461 | 2,455 | 2,448 |
| Sealdah Koley Market | 2,294 | 2,330 | 2,323 | 2,324 | 2,329 | 2,330 | 2,332 |
| Vashi | 2,142 | 2,154 | 2,163 | 2,180 | 2,194 | 2,205 | 2,217 |
| Yeshwanthpur | 2,107 | 2,140 | 2,149 | 2,165 | 2,180 | 2,193 | 2,205 |

### Potato — latest actual 11 Nov 2026

| Market | 12 Nov | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 1,264 | 1,303 | 1,322 | 1,358 | 1,383 | 1,399 | 1,415 |
| Bowenpally | 1,375 | 1,418 | 1,433 | 1,434 | 1,446 | 1,454 | 1,458 |
| Koyambedu | 1,598 | 1,564 | 1,614 | 1,566 | 1,542 | 1,543 | 1,530 |
| Muhana | 1,428 | 1,414 | 1,428 | 1,446 | 1,449 | 1,455 | 1,462 |
| Naroda | 1,552 | 1,500 | 1,534 | 1,521 | 1,505 | 1,507 | 1,503 |
| Sealdah Koley Market | 1,444 | 1,546 | 1,504 | 1,484 | 1,501 | 1,496 | 1,490 |
| Vashi | 1,460 | 1,488 | 1,432 | 1,459 | 1,473 | 1,466 | 1,470 |
| Yeshwanthpur | 1,432 | 1,484 | 1,465 | 1,464 | 1,476 | 1,475 | 1,475 |

### Tomato — latest actual 11 Nov 2026

| Market | 12 Nov | 13 Nov | 14 Nov | 15 Nov | 16 Nov | 17 Nov | 18 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 2,245 | 2,260 | 2,272 | 2,283 | 2,290 | 2,295 | 2,299 |
| Bowenpally | 1,877 | 1,995 | 2,062 | 2,135 | 2,183 | 2,215 | 2,241 |
| Koyambedu | 2,448 | 2,360 | 2,412 | 2,368 | 2,346 | 2,342 | 2,332 |
| Muhana | 2,154 | 2,209 | 2,197 | 2,240 | 2,261 | 2,271 | 2,282 |
| Naroda | 2,598 | 2,476 | 2,480 | 2,423 | 2,388 | 2,371 | 2,354 |
| Sealdah Koley Market | 2,589 | 2,521 | 2,477 | 2,426 | 2,395 | 2,373 | 2,356 |
| Vashi | 2,419 | 2,392 | 2,360 | 2,350 | 2,340 | 2,331 | 2,326 |
| Yeshwanthpur | 2,220 | 2,272 | 2,277 | 2,283 | 2,292 | 2,297 | 2,300 |

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

![7-day forecast](../charts/forecast_7day_2026-11-13.svg)
