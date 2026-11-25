# Day 46 — Shareable commodity view (2026-11-25)

Every commodity on the site now has a deep link: `?c=Onion` opens the
Onion detail panel directly, so the daily log (and anyone else) can link
straight to one commodity's trend, stats and MSP line instead of the
generic homepage.

## What changed

- `site/app.js` — `openDetail()` now writes `?c=<Commodity>` into the
  address bar via `history.replaceState`, so any opened detail (price-row
  tap or hero card) makes the link in the bar shareable. On load, `?c=`
  is matched case-insensitively against the commodity, short name or
  Hindi name (`?c=tomato`, `?c=प्याज` both work); an unknown value is
  ignored and the default view loads. A "🔗 इस भाव का लिंक कॉपी करें ·
  Copy link to this commodity" button in the detail panel copies the
  deep link (clipboard API with execCommand fallback, "कॉपी हो गया ✓"
  confirmation for 2s).
- `site/index.html` — copy-link button added to the detail card.
- `site/styles.css` — `.copy-link` pill-button style (green on hover).
- `site/README.md` — "What's on the site" gains the deep-link bullet.

Example links (live site): `https://mandilens-in.netlify.app/?c=Onion`,
`?c=Potato`, `?c=Wheat`.

## Verification (headless-CDP render, file://, desktop 1280 + mobile 390)

- `node --check` clean for `app.js`; 6/6 DOM checks passed, 0 JS
  exceptions across all navigations: `?c=Onion` opens the Onion detail
  (panel visible, row selected, `location.search === "?c=Onion"`);
  `?c=tomato` (lowercase) opens Tomato; `?c=NoSuch` stays on the
  default view (detail hidden); clicking a Wheat row sets the URL to
  `?c=Wheat` and opens its detail; clicking the Potato hero card sets
  `?c=Potato`; mobile `?c=Onion` opens the detail with no errors.
- Re-verified after the daily `build_site.py` regenerated `data.js`
  (fresh 23 Nov data) — same 6/6 pass.
- Screenshots: `/tmp/mandilens_day46_deeplink.png` (desktop, detail +
  copy button visible), `/tmp/mandilens_day46_mobile.png`.

## Data note (not a Day-46 regression)

- Portal pull today: 71 National + 14 per-mandi rows (23/22/21 Nov);
  3/8 mandis reporting (Azadpur 3, Sealdah 1, Bowenpally 2). APMC
  Mumbai + Bengaluru APMC: NO_ROWS; Koyambedu + Muhana: NOT_FOUND;
  Naroda: NO_DATA_AVAILABLE. Portal frozen at 23 Nov — feed STALE lag 2.
- 6 alerts, Jowar +64.7% headline (₹2,545 → ₹4,193 National) — the
  third wild Jowar swing in the series (see Day 39: revision artefact,
  flag and let humans judge); Tomato National −28.5%, Onion −22.2%.
- Site `data.js` now carries 5 real mandi rows for 23 Nov (Azadpur
  Onion/Potato/Tomato, Bowenpally Potato/Tomato); Sealdah reported no
  23 Nov row (its Tomato was EMPTY), so the mandi-compare Onion tab
  shows Azadpur only and the forecast shows 5 real-backed series.
- Azadpur Onion 22 Nov was EMPTY on the portal again, so the Azadpur
  Onion forecast still starts from 21 Nov.
