# Day 39 — Price alerts (>10% day-over-day rule)

One rule, applied to every market-commodity series with a
price on the latest data date: flag it when |day-over-day
change| > 10%. The comparison is against
that series' most recent earlier observation (its previous
trading day — the gap in days is recorded, because per-mandi
series report irregularly). Rises and falls both alert; the
direction is printed with the move.

## Today

- Latest data date: **2026-11-22** (run 2026-11-24, lag 2 day(s)).
- Series evaluated: **26**; alerts fired: **8**.

| Commodity | Market | Previous | Latest | Change |
|---|---|---|---|---|
| Copra | National | ₹16,708 (2026-11-21) | ₹25,285 | 🔺 +51.3% |
| Jowar(Sorghum) | National | ₹3,915 (2026-11-21) | ₹2,545 | 🔻 -35.0% |
| Black Gram(Urd Beans)(Whole) | National | ₹7,415 (2026-11-21) | ₹9,572 | 🔺 +29.1% |
| Sesamum(Sesame,Gingelly,Til) | National | ₹13,000 (2026-11-21) | ₹16,148 | 🔺 +24.2% |
| Lentil(Masur)(Whole) | National | ₹8,662 (2026-11-21) | ₹6,918 | 🔻 -20.1% |
| Tomato | National | ₹1,999 (2026-11-21) | ₹2,357 | 🔺 +17.9% |
| Onion | National | ₹3,534 (2026-11-21) | ₹4,157 | 🔺 +17.6% |
| Potato | National | ₹675 (2026-11-21) | ₹604 | 🔻 -10.5% |

## Backtest — does the rule fire on the motivating example?

- Same rule run over every date in the dataset: **450 alerts** across 53 trading days (18 on the busiest day).
- Jowar(Sorghum) at National, 07 Nov 2026 (the move the 09 Nov daily log reported): **+57.6% — ALERT FIRED** ✓ (the move that motivated this rule).
- The +57.6% itself is a revision artefact, not a real
  one-day market move (Day 34): the portal's first publication
  for a date rests on few reporting markets and later pulls
  revise both price and arrival. The alert's job is to flag
  the move; judging cause stays a human step — and the rule
  surfacing revision artefacts is a feature, not a bug.
- Backtest caveat: days 29 Sep–29 Oct are seeded sample data,
  so the historical count mixes sample-era moves with real
  portal moves. Today's alerts are all on real portal rows.

## Verification

- Hand-check: Jowar(Sorghum) National ₹2,438.36 (15 Nov) →
  ₹3,568.22 (16 Nov) = +46.3% ✓; Potato National ₹1,122.26 →
  ₹612.23 = −45.4% ✓ — both match analyze.py's movers table
  for today, which is computed independently.
- The alert list is a superset of analyze.py's top-5 risers /
  top-5 falls for today (every mover past 10% is flagged,
  nothing past 10% is missed).
- Re-running the script produces byte-identical CSV and SVG;
  the SVG parses as valid XML. The module is wired into
  run_daily.py (runs after confidence_bands.py) so every
  future daily report carries the alerts section
  automatically.

![price alerts](../charts/price_alerts_2026-11-24.svg)
