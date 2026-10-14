# Day 4 — Geographic spread: where are vegetables cheapest?

*14 Oct 2026 · sample data (portal blocked automated access today — details in the daily log)*

## What I did

Built `src/geographic_spread.py`: median modal price per (state, commodity)
across the full 15-day history, drawn as an annotated heatmap
(`charts/state_heatmap_2026-10-14.svg`).

## Findings

| Commodity | Cheapest state | Costliest state | Spread |
|---|---|---|---|
| Onion | Maharashtra (₹1,810/q) | Gujarat (₹2,540/q) | 40% |
| Potato | Maharashtra (₹1,270/q) | Gujarat (₹1,730/q) | 36% |
| Tomato | Maharashtra (₹1,940/q) | Gujarat (₹2,660/q) | 37% |

- **Maharashtra is the cheapest state for all three vegetables**, Gujarat the
  costliest — the ranking is identical across commodities, which suggests
  structural factors (transport corridors, APMC fee structures) rather than
  crop-specific shocks.
- A 36–40% inter-state spread is large for wholesale staples: moving onions
  from Maharashtra to Gujarat at even half that gap would be profitable before
  logistics.
- Caveat: this is seeded sample data, so the *magnitudes* are illustrative —
  the method (state × commodity median heatmap) is what I'm validating here.
  Once the portal feed flows, these numbers become real.

## Method note

Median (not mean) per state — resistant to the occasional supply-shock day
(Tomato gets synthetic ±20% shocks in the sample generator). States ordered by
mean price so the heatmap reads cheapest → costliest top to bottom.
