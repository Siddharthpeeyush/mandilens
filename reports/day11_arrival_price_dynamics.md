# Day 11 — Arrival vs price dynamics: do bigger arrivals mean lower prices?

## Data availability (read this first)

The clean dataset holds **528 rows**; **528** carry an
arrival quantity (`arrival_tonnes`, the arrivals column of the
government's published "Market Wise Price & Arrival" table).

**Honest-data note:** the sample generator draws arrivals from a
random stream *independent of the price drift*
(`tools/make_sample.py` — no baked-in arrival-price relationship),
so on sample rows the expected correlation is ≈ 0. That null is the
honest result for synthetic data; the same module runs unchanged on
real portal extracts, where a genuine demand-curve slope should
appear if one exists.

## Same-day: arrivals vs modal price (per commodity, pooled mandis)

| Commodity | n | Pearson r | Spearman ρ |
|---|---|---|---|
| Onion | 176 | -0.013 | -0.045 |
| Potato | 176 | 0.057 | 0.018 |
| Tomato | 176 | -0.018 | -0.074 |

Expected sign if bigger arrivals push prices down: **negative**.
Reading guide: |r| < 0.2 ≈ no relationship; 0.2–0.5 weak; > 0.5 strong.

## Lagged: yesterday's arrivals vs today's price

| Market | Commodity | n | r (lag-1) | ρ (lag-1) |
|---|---|---|---|---|
| Azadpur | Onion | 20 | -0.060 | -0.122 |
| Azadpur | Potato | 20 | -0.049 | 0.268 |
| Azadpur | Tomato | 20 | 0.222 | 0.143 |
| Bowenpally | Onion | 20 | -0.149 | -0.255 |
| Bowenpally | Potato | 20 | 0.093 | 0.160 |
| Bowenpally | Tomato | 20 | -0.166 | -0.171 |
| Koyambedu | Onion | 20 | 0.009 | 0.024 |
| Koyambedu | Potato | 20 | 0.253 | 0.255 |
| Koyambedu | Tomato | 20 | -0.347 | -0.333 |
| Muhana | Onion | 20 | -0.146 | -0.334 |
| Muhana | Potato | 20 | -0.499 | -0.256 |
| Muhana | Tomato | 20 | -0.078 | -0.177 |
| Naroda | Onion | 20 | -0.018 | -0.056 |
| Naroda | Potato | 20 | 0.406 | 0.110 |
| Naroda | Tomato | 20 | -0.244 | -0.283 |
| Sealdah Koley Market | Onion | 20 | 0.151 | 0.178 |
| Sealdah Koley Market | Potato | 20 | 0.058 | 0.021 |
| Sealdah Koley Market | Tomato | 20 | -0.054 | -0.195 |
| Vashi | Onion | 20 | -0.025 | -0.086 |
| Vashi | Potato | 20 | -0.211 | -0.145 |
| Vashi | Tomato | 20 | 0.081 | 0.117 |
| Yeshwanthpur | Onion | 20 | -0.384 | -0.457 |
| Yeshwanthpur | Potato | 20 | 0.171 | 0.326 |
| Yeshwanthpur | Tomato | 20 | -0.170 | -0.200 |

## Reading the result

On the current (sample) data the same-day correlations are
essentially zero for all three commodities — exactly what the
independent-draw generator produces. The module is verified working
(OLS trend lines drawn, lag merge joins correctly), so when the
first real portal extract lands with its own arrivals, re-running
this script will surface the true slope: expect negative r on real
data if the classic supply effect holds, and the lag-1 panel tells
whether the effect lands same-day or next-day.

![Arrivals vs price](../charts/arrival_price_dynamics_2026-10-21.svg)
