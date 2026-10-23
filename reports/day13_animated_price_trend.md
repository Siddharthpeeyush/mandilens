# Day 13 — animated price-trend chart

- 2026-10-23 · fetch mode: sample fallback (Agmarknet returned 403 to the browser task; portal fetch attempted and blocked, as on Day 11)

## What was built

`src/animate_trend.py` — generates `charts/price_trend_animated_<date>.svg`, a
**pure-SMIL animated SVG** of the 14-day median modal price for Onion, Potato
and Tomato. Pure SMIL was chosen deliberately over GIF/video: it stays plain
text, so it pushes through the GitHub `push_files` API like every other chart
(no binaries in this repo).

The 8-second loop shows:
- each commodity line drawing itself (stroke-dashoffset animation, staggered
  0s / 0.5s / 1.0s for layering),
- a travelling dot riding each line via `animateMotion`,
- a sweeping dashed playhead cursor,
- a date readout that tracks the playhead (one SMIL `<set>` per segment),
- gridlines, y-axis (Rs/quintal), legend, and a source label that switches
  with the data mode (portal / api / sample) — no silent mislabeling.

Usage: `python3 src/animate_trend.py [date] [source]` (defaults: latest date,
"sample").

## Verification (today)

- Script ran clean: 3 series, 14 dates, 7236 bytes — no exceptions.
- SVG parsed with ElementTree: 5 `<animate>` elements (3 line draws + cursor
  x1/x2), 3 `<animateMotion>` dots, 14 `<set>` date steps, 3 dashed line paths,
  root 960×540. All expected elements present, none missing.
- Cross-checked the animated line values against the static
  `charts/price_trends_2026-10-23.svg` data — same 14-day median series,
  Onion 2050–2355 / Potato 1470–1630 / Tomato 2135–2505 Rs/quintal, no
  axis-inversion or missing-day bugs.

## Finding

On sample data the animation is a smooth drift (the generator has no real
shocks); on real portal extracts the same file will show true spikes. The
module needs no changes when the portal unblocks — it reads the processed CSV
like every other chart.

![Animated trend](charts/price_trend_animated_2026-10-23.svg)
