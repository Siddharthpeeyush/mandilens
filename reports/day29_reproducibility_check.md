# Day 29 — Reproducibility check: fresh clone, one-command run — 08 Nov 2026

## The check

Cloned the repo fresh from GitHub (`git clone --depth 1
https://github.com/Siddharthpeeyush/mandilens`, head `f21de83`, the 07 Nov
state) into a clean directory and ran exactly the one command the README
documents for the daily job:

```bash
python3 src/run_daily.py
```

Environment in the check: Python 3.12.3, pandas 2.1.4, matplotlib 3.6.3,
numpy 1.26.4. No API keys, no network beyond the clone.

## Result: PASS

With today's portal CSV present (24 commodities × 3 dates, 04–06 Nov), the
fresh clone reproduced the workspace run exactly:

- **Byte-identical:** `data/processed/mandi_prices_clean.csv` (1,002 rows),
  `reports/daily/2026-11-08.md`, `data/processed/data_quality_2026-11-08.csv`,
  `data/processed/forecast_table_2026-11-08.csv`,
  `charts/data_quality_badge_2026-11-08.svg`, `README.md`,
  `reports/day23_forecast_table.md`, `reports/day26_data_quality_badge.md`.
  Same walk-forward MAEs (Onion ₹207.68 / Potato ₹143.95 / Tomato ₹265.78),
  same Azadpur Onion hand-check (h=1 ₹2219.74, h=2 ₹2288.07).
- **Content-identical:** the three matplotlib SVGs
  (`price_trends_2026-11-08.svg`, `top_movers_2026-11-08.svg`,
  `forecast_7day_2026-11-08.svg`) differ byte-wise only in the embedded
  `dc:date` creation timestamp and matplotlib's random element IDs — after
  normalizing those two fields, all coordinates and values match exactly.
- **Fallback path verified too:** the clone as-cloned (no 08 Nov raw CSV)
  completed the same command in SAMPLE mode, labelled `DAILY DONE [SAMPLE]`,
  with a correctly dated sample report — a newcomer without today's extract
  still gets a working run, never a crash.

## Two gaps found and fixed

1. **Day-number skew (noted on Day 28).** The daily report header derived
   its Day number from the *latest data date* (`Day 26 · 06 Nov 2026`) while
   the README derives it from the *run date* (`Day 28 — 08 Nov 2026`), so the
   two disagreed whenever the portal feed lagged. Fixed in `src/analyze.py`:
   the Day number now follows the run date passed by `run_daily.py`, while
   the header date stays the latest data date — the lag stays visible.
   Re-verified: workspace and clone both emit `Day 28 · 06 Nov 2026` and
   re-diff byte-identical.
2. **Over-strict dependency floor.** `requirements.txt` demanded
   `matplotlib>=3.7`, but the whole daily path ran fine on matplotlib 3.6.3
   in this environment, and every matplotlib call in `src/` is basic pyplot
   (`subplots`, `savefig`, `xticks`, `close` — stable since 3.0). Relaxed to
   `matplotlib>=3.6` with a comment citing this check.

## Noted, not changed

- The full `pip install -r requirements.txt` was not re-run: pandas /
  matplotlib / numpy were already present for the daily path. scikit-learn
  and streamlit are absent in this environment, but the documented
  one-command daily run (`run_daily.py`) does not need them — only the
  random-forest module (Day 19) and the Streamlit dashboard (Day 25) do, and
  the README's install step covers those.
- SVG-only rule holds in the repo: zero PNGs are tracked (`git ls-files
  charts/ | grep -c png` → 0). The PNGs `visualize.py` writes are local-only
  build artifacts.
