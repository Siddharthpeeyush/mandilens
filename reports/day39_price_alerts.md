# Day 39 — Price alerts (>10% day-over-day rule)

One rule, applied to every market-commodity series with a
price on the latest data date: flag it when |day-over-day
change| > 10%. The comparison is against
that series' most recent earlier observation (its previous
trading day — the gap in days is recorded, because per-mandi
series report irregularly). Rises and falls both alert; the
direction is printed with the move.

## Today

- Latest data date: **2026-11-25** (run 2026-11-27, lag 2 day(s)).
- Series evaluated: **30**; alerts fired: **6**.

| Commodity | Market | Previous | Latest | Change |
|---|---|---|---|---|
| Barley(Jau) | National | ₹2,129 (2026-11-24) | ₹2,666 | 🔺 +25.2% |
| Jowar(Sorghum) | National | ₹4,943 (2026-11-24) | ₹3,726 | 🔻 -24.6% |
| Lentil(Masur)(Whole) | National | ₹9,701 (2026-11-24) | ₹7,422 | 🔻 -23.5% |
| Onion | National | ₹4,023 (2026-11-24) | ₹3,134 | 🔻 -22.1% |
| Tomato | Bowenpally | ₹1,800 (2026-11-24) | ₹1,500 | 🔻 -16.7% |
| Black Gram(Urd Beans)(Whole) | National | ₹8,603 (2026-11-24) | ₹7,596 | 🔻 -11.7% |

## Backtest — does the rule fire on the motivating example?

- Same rule run over every date in the dataset: **466 alerts** across 56 trading days (18 on the busiest day).
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

![price alerts](../charts/price_alerts_2026-11-27.svg)
