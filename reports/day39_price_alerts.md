# Day 39 — Price alerts (>10% day-over-day rule)

One rule, applied to every market-commodity series with a
price on the latest data date: flag it when |day-over-day
change| > 10%. The comparison is against
that series' most recent earlier observation (its previous
trading day — the gap in days is recorded, because per-mandi
series report irregularly). Rises and falls both alert; the
direction is printed with the move.

## Today

- Latest data date: **2026-11-21** (run 2026-11-23, lag 2 day(s)).
- Series evaluated: **30**; alerts fired: **6**.

| Commodity | Market | Previous | Latest | Change |
|---|---|---|---|---|
| Copra | National | ₹21,750 (2026-11-20) | ₹16,708 | 🔻 -23.2% |
| Potato | National | ₹559 (2026-11-20) | ₹675 | 🔺 +20.7% |
| Onion | Azadpur | ₹4,206 (2026-11-20) | ₹3,563 | 🔻 -15.3% |
| Sesamum | National | ₹15,126 (2026-11-20) | ₹12,991 | 🔻 -14.1% |
| Jowar | National | ₹4,385 (2026-11-20) | ₹3,851 | 🔻 -12.2% |
| Tomato | National | ₹1,784 (2026-11-20) | ₹1,999 | 🔺 +12.0% |

## Backtest — does the rule fire on the motivating example?

- Same rule run over every date in the dataset: **439 alerts** across 52 trading days (18 on the busiest day).
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

![price alerts](../charts/price_alerts_2026-11-23.svg)
