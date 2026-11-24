# Day 45 — Hindi-first polish (2026-11-24)

Hindi-first labels on the site's main views: every heading, nav link, tab,
category chip, table header, sort option and calculator label now shows Hindi
(Devanagari, first) alongside English. Commodity names already carried Hindi;
this pass covers everything around them.

## What changed

- `site/index.html` — nav (5 links), hero h1 (`आज के मंडी भाव`) + lede
  sentence, all 6 section headings, movers card titles, prices sub, sort
  options (5), price-table header row, mandi/forecast/calculator/about
  headings and subs, calculator labels + unit options, footer line, noscript.
- `site/app.js` — `HINDI_CAT` (5 categories) + `HINDI_VEG` maps; category
  chips (`सब्जियाँ · Vegetables` …), mandi + forecast tabs (`प्याज · Onion`
  …), mandi/forecast table headers, detail stat labels, freshness badge
  (`ताज़ा भाव: 22 Nov 2026 · 23 वस्तुएँ · फ़ीड 2 दिन पुरानी · Latest prices`),
  movers sub, calculator result now names the commodity in Hindi
  (`Onion (प्याज)`), `MSP नहीं · no MSP`, empty-search and load-fail strings.
- `site/styles.css` — `.hi` rules: headings 0.62em muted, nav 12px at 0.8
  opacity, movers titles 0.85em muted.
- `site/README.md` — "What's on the site" gains the Hindi-first bullet.

## Deliberately NOT translated

Explanatory prose stays English: the About list, the mandi/forecast
"how to read it" notes, the detail note and the MSP line. The item asked
for labels, not a full translation — a language toggle is a later item if
he wants it.

## Verification (headless-CDP render, file://, desktop 1280 + mobile 390)

- `node --check` clean for `app.js` and `data.js`; HTML parser: no errors,
  no unclosed tags.
- DOM checks on the live render: 6/6 h2s bilingual, 5/5 nav links bilingual,
  6/6 category chips bilingual, 3/3 mandi tabs + 3/3 forecast tabs bilingual,
  23 price rows, 3 hero cards, 1,034 Devanagari glyphs on the page,
  0 JS errors.
- Screenshots: `/tmp/mandilens_day45_desktop.png` (1280×4660),
  `/tmp/mandilens_day45_mobile.png` (390 wide) — visually checked: headings,
  badge, chips, tables and calculator all render Hindi-first with no
  overflow; mobile nav wraps to 3 lines, hero cards stack.

## Data note (not a Day-45 regression)

- Mandi Onion tab shows 0 rows and the forecast Onion tab is all "—":
  Azadpur's 22 Nov Onion price was EMPTY on the portal, so no mandi
  reported Onion on 22 Nov; `mandiToday` is Bowenpally Potato/Tomato +
  Sealdah Tomato only. The forecast rule (Day 44) drops Azadpur Onion
  because its latest real price is 21 Nov, not 22 Nov. The Day-43 note
  names the reporting vs non-reporting mandis, so the sparse day reads
  as sparse, not broken.

## Today's data (portal, 22 Nov 2026 — feed still 2 days behind)

- National 24 rows (71 parsed incl. 3 dates); per-mandi 15 rows, 3/8 mandis
  reporting (Azadpur, Sealdah, Bowenpally). Koyambedu + Muhana NOT_FOUND;
  Mumbai, Bengaluru, Naroda NO_ROWS.
- 8 alerts on 22 Nov: Copra +51.3% headline, Jowar −35.0%, Black Gram
  +29.1%, Sesamum +24.2%, Lentil −20.1%, Tomato +17.9%, Onion +17.6%,
  Potato −10.5%. Walk-forward 1-day MAE: Onion ₹406 / Potato ₹146 /
  Tomato ₹267.
