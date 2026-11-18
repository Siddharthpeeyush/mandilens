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
16 Nov 2026), exactly like the earlier scoring days.

## Empirical error scale

Walk-forward: refit on history up to 7 days ago, then
one-step-ahead on the last 7 days, per commodity:

| Commodity | Walk-forward 1-day MAE (₹/qtl) | n |
|---|---|---|
| Onion | 419.12 | 21 |
| Potato | 110.90 | 9 |
| Tomato | 283.86 | 16 |

The table below shows **point forecasts**. A fair mental
band is ±(1-day MAE × horizon): error compounds because each
forecast day reuses the previous day's forecast as a lag.
The forecast also inherits whatever drift the last 3 days
carried — a 7-day OLS forecast cannot predict a shock.

## 7-day forecast table

### Onion — latest actual 16 Nov 2026

| Market | 17 Nov | 18 Nov | 19 Nov | 20 Nov | 21 Nov | 22 Nov | 23 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 3,976 | 3,867 | 3,765 | 3,655 | 3,559 | 3,470 | 3,387 |
| Bowenpally | 2,267 | 2,282 | 2,314 | 2,307 | 2,310 | 2,315 | 2,318 |
| Koyambedu | 2,401 | 2,396 | 2,415 | 2,404 | 2,399 | 2,398 | 2,394 |
| Muhana | 2,119 | 2,132 | 2,156 | 2,169 | 2,183 | 2,196 | 2,208 |
| Naroda | 2,502 | 2,460 | 2,490 | 2,472 | 2,461 | 2,455 | 2,448 |
| Sealdah Koley Market | 2,294 | 2,330 | 2,323 | 2,324 | 2,329 | 2,330 | 2,332 |
| Vashi | 2,142 | 2,154 | 2,163 | 2,180 | 2,194 | 2,205 | 2,217 |
| Yeshwanthpur | 2,107 | 2,140 | 2,149 | 2,165 | 2,180 | 2,193 | 2,205 |

### Potato — latest actual 16 Nov 2026

| Market | 17 Nov | 18 Nov | 19 Nov | 20 Nov | 21 Nov | 22 Nov | 23 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 1,268 | 1,307 | 1,326 | 1,363 | 1,388 | 1,403 | 1,420 |
| Bowenpally | 1,449 | 1,551 | 1,486 | 1,480 | 1,502 | 1,492 | 1,488 |
| Koyambedu | 1,593 | 1,562 | 1,615 | 1,564 | 1,541 | 1,544 | 1,531 |
| Muhana | 1,430 | 1,415 | 1,431 | 1,449 | 1,452 | 1,458 | 1,465 |
| Naroda | 1,550 | 1,500 | 1,535 | 1,522 | 1,505 | 1,508 | 1,505 |
| Sealdah Koley Market | 1,445 | 1,549 | 1,505 | 1,486 | 1,504 | 1,498 | 1,492 |
| Vashi | 1,465 | 1,491 | 1,433 | 1,463 | 1,477 | 1,468 | 1,474 |
| Yeshwanthpur | 1,434 | 1,487 | 1,467 | 1,466 | 1,479 | 1,478 | 1,478 |

### Tomato — latest actual 16 Nov 2026

| Market | 17 Nov | 18 Nov | 19 Nov | 20 Nov | 21 Nov | 22 Nov | 23 Nov |
|---|---|---|---|---|---|---|---|
| Azadpur | 2,231 | 2,243 | 2,254 | 2,265 | 2,272 | 2,278 | 2,283 |
| Bowenpally | 1,662 | 1,805 | 1,896 | 1,976 | 2,043 | 2,093 | 2,135 |
| Koyambedu | 2,460 | 2,371 | 2,438 | 2,389 | 2,364 | 2,360 | 2,347 |
| Muhana | 2,130 | 2,178 | 2,157 | 2,203 | 2,225 | 2,236 | 2,250 |
| Naroda | 2,642 | 2,521 | 2,536 | 2,476 | 2,435 | 2,415 | 2,391 |
| Sealdah Koley Market | 2,637 | 2,577 | 2,534 | 2,482 | 2,447 | 2,420 | 2,396 |
| Vashi | 2,440 | 2,413 | 2,378 | 2,369 | 2,356 | 2,344 | 2,336 |
| Yeshwanthpur | 2,199 | 2,257 | 2,260 | 2,263 | 2,274 | 2,280 | 2,284 |

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

![7-day forecast](../charts/forecast_7day_2026-11-18.svg)
