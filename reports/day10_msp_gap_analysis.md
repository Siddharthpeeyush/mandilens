# Day 10 — MSP gap analysis: market price vs MSP per commodity

Question: for each tracked commodity, is the market price above or
below the government-notified Minimum Support Price — and where is the
MSP floor actually biting?

## The verified answer first

**0 of 3 tracked commodities have a notified MSP.** Onion,
Potato and Tomato are vegetables; MSP is notified only for the 22
mandated crops (14 Kharif + 6 Rabi + 2 commercial, Marketing Season
2026-27, per the PIB press releases of 13 May 2026 and Oct 2025).
Vegetables are covered instead by price-stabilisation schemes, not by
an MSP floor — so **the market-price-vs-MSP gap is undefined for every
commodity MandiLens currently tracks**. Reporting a 'gap' for them
would mean inventing a benchmark that does not exist.

## Coverage audit (alias-checked against the mandated list)

| Commodity | Notified MSP? | Mandated crop | MSP (Rs/qtl) | Season | Median modal (Rs/qtl) |
|---|---|---|---|---|---|
| Onion | NO | — | — | — | 2,180 |
| Potato | NO | — | — | — | 1,510 |
| Tomato | NO | — | — | — | 2,275 |

## Gap computation (skipped — no covered commodities)

The gap machinery is built and ready: for any commodity with a
notified MSP, it computes per mandi-day `gap = modal − MSP`,
`gap_pct = gap / MSP`, the median gap, and the share of mandi-days
trading below MSP ('under support'). It runs the moment a
mandated crop enters the tracked set. See
`src/msp_gap_analysis.py::gap_summary`.

## How to make Day 10 live

Add **one mandated crop to the MandiLens tracked set** — e.g.
Tur/Arhar (MSP Rs 8,450/qtl) or Wheat (Rs 2,585/qtl), both routinely
published in the Agmarknet tables. Then: today's portal 403 block
aside, portal rows carry an `msp_rs` column that feeds this module
directly. Recommended: Tur/Arhar, because pulses trade near their
floor often enough to make the 'share of days under support'
statistic meaningful.

## Sources

- Notified MSPs: PIB press release PRID 2260617 (Kharif 2026-27,
  13 May 2026) and PIB PRID 2177219 (Rabi 2026-27). Copied exactly;
  see `src/msp_data.py`.
- Market prices: MandiLens cleaned dataset to
  2026-10-20 (3 commodities).
- Data mode note: today's Agmarknet portal fetch was blocked (site-wide
  403 bot-wall), so the pipeline ran on the seeded sample fallback —
  the coverage audit is unaffected since MSPs are a published table,
  not portal-derived.

![MSP gap analysis](../charts/msp_gap_2026-10-20.svg)
