# Day 43 — Mandi compare restored on the website (real portal data)

## What changed

The Mandi compare section is back on the site — hidden since 07 Nov 2026
because it rested on seeded sample data (29 Sep – 29 Oct 2026). The
real-data rule from the roadmap is now met: real per-mandi portal rows
have landed every day since 10 Nov 2026, and today's table is built
entirely from them.

- `site/index.html`: `#mandis` unhidden, "Mandi compare" nav link restored,
  badge changed from `Sample data` to `Real portal data`. The static sample
  note is replaced by an empty `#mandiNote` div, filled by JS each load.
- `site/app.js`: the note is now derived from `data.js` every load — it
  names the mandis that reported on the latest per-mandi date and the ones
  that did not, so a sparse day reads as sparse, not broken. Also fixed a
  real-data rendering bug found during verification: the portal publishes
  one modal price per mandi-day and no min/max, so `rs(null)` printed
  "₹0 – ₹0" in the Range column — it now shows "—" when min/max are absent.
- `site/README.md`: Mandi compare bullet + the "hidden for now" blockquote
  updated to the restored state (Day 37 forecast + Day 43 compare).

## Verification (headless Chrome, CDP, file:// render)

Section `hidden: false`, nav link present, badge "Real portal data". Note
reads: "real Agmarknet portal prices for the mandis that reported on
20 Nov 2026 — Azadpur, Bowenpally, Sealdah. Vashi, Koyambedu, Yeshwanthpur,
Naroda, Muhana did not report, so they show no row." Tables (cheapest
first): Onion 1 row (Azadpur ₹4,206); Potato 2 rows (Azadpur ₹1,163,
Bowenpally ₹1,200); Tomato 3 rows (Bowenpally ₹1,500 cheapest, Azadpur
₹1,931, Sealdah ₹3,200 costliest). Range column "—" on all rows (no
min/max published). Screenshot: /tmp/mandilens_day43_mandi.png (kept
outside the repo; re-render any time from site/index.html).

## Today's data (portal, 18–20 Nov 2026)

Browser extract: National 24 rows (Total Records 24.00, Print All Data)
+ per-mandi 17 rows. 3 of 8 mandis reported: Azadpur (Onion ₹4,206 flat,
Potato ₹1,163/₹1,163/₹1,074, Tomato ₹1,931/₹2,064/—), Sealdah Koley
Market (Tomato ₹3,200 flat), Bowenpally (Potato ₹1,200 flat, Tomato
₹1,500 flat). APMC Mumbai (8 rows) and Bengaluru APMC (11 rows) loaded
but have no Onion/Potato/Tomato rows; Ahmedabad returned "No Data
Available"; Koyambedu and Muhana still NOT_FOUND in the market dropdowns
(same as 10 Nov 2026). Dataset now 1,424 rows; feed STALE, lag 2 days
(latest 20 Nov — the portal states data frozen up to 20 Nov 2026, so no
21 Nov rows exist yet); coverage 98.1% (52/53 days, only 13 Oct missing);
latest-day completeness 24/24 (100%).

Biggest moves 19 → 20 Nov: Ragi +26.1% (₹3,216 → ₹4,054), Lentil +11.7%,
Jowar +10.6%; Copra −16.5% (₹26,058 → ₹21,750), Potato −14.9%
(₹657 → ₹559). 5 alerts of 30 series. Walk-forward 1-day MAE: Onion
₹570 (n=7), Potato ₹170 (n=10), Tomato ₹312 (n=17).

## Notes

- The forecast model is still fit on per-mandi history mixing seeded
  sample (29 Sep – 29 Oct 2026) with real portal rows from 10 Nov — the
  sample share shrinks as real rows accumulate; that caveat stays on the
  forecast section until the sample history ages out.
- The About section's "full dataset (978 rows)" line is stale (now 1,424)
  — pre-existing, out of Day 43 scope; fix with the next About touch.
- Environment note: the VM restarted mid-run and wiped /tmp (verify
  script + pip's websocket-client had to be recreated/reinstalled). The
  extract file /tmp/mandilens_extract_2026-11-22.txt was parsed before the
  wipe; CSVs were already on disk and are unaffected.
