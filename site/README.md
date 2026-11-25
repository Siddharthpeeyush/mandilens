# MandiLens website

Static site — no build step, no server, no dependencies. Open `index.html`
or deploy the whole folder.

## Deploy

- **Netlify (drag-and-drop):** drag this `site/` folder onto
  https://app.netlify.com/drop — done. Or connect the `mandilens` repo and
  set the publish directory to `site/`.
- **GitHub Pages:** copy this folder's contents to the repo's `docs/` (or a
  `gh-pages` branch) and enable Pages.
- **Local preview:** open `index.html` in any browser (works from `file://`
  too — data is inlined via `data.js`, no fetch needed).

## Daily refresh

After the 7 PM pipeline run (`python3 src/run_daily.py`), regenerate the
site's data and it picks up the new prices automatically:

```bash
python3 site/build_site.py
```

`build_site.py` reads `data/processed/mandi_prices_clean.csv` + the latest
`forecast_table_*.csv` and rewrites `site/data.js`. Commit/push `data.js`
with the daily run — the HTML/JS never needs to change for a data update.

## What's on the site

- **Shareable commodity links (Day 46)** — every commodity has a deep
  link: `?c=Onion` opens that commodity's detail directly, and opening
  any detail writes its link into the address bar; a copy-link button in
  the detail panel copies it.
- **Hindi-first labels (Day 45)** — every heading, nav link, tab, category
  chip, table header, sort option and calculator label shows Hindi alongside
  English (Devanagari first); commodity names already carried Hindi.
  Explanatory paragraphs stay English.
- **Today's prices** — National benchmark for 24 commodities (real Agmarknet
  portal data), with ₹/kg, day-on-day change and vs-MSP.
- **Trend detail** — tap any row for an 11-day trend chart, range and MSP.
- **Mandi compare** — Onion/Potato/Tomato across 8 mandis, cheapest vs
  costliest. **Real portal data** — latest per-mandi prices for the mandis
  that reported; mandis that did not report show no row.
- **7-day outlook** — OLS forecasts, dates labelled as generated.
- **Calculator** — quintal/kg/tonne cost at today's modal price.
- **Search + category filter + sort** across all 26 commodities (Hindi names
  included).

> **Restored (Day 37, 16 Nov 2026; Day 43, 22 Nov 2026; Day 44, 23 Nov 2026):** the 7-day outlook
> and Mandi compare sections are back — the outlook on the per-mandi
> forecast table, the compare on real per-mandi portal rows (10 Nov 2026
> onwards). From Day 44 the outlook shows ONLY series whose latest price
> is a real portal row (6 of 24 today); the rest render as "—". The
> forecast model is still fit on per-mandi history that mixes
> seeded sample (29 Sep–29 Oct 2026) with real rows; the sample share
> shrinks as real rows accumulate.
