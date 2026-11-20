# Day 41 — Seasonality check: weekly cycles in the National series (2026-11-20)

## Verdict: NO recurring weekly cycle — the naive flags are one anomalous weekend

The naive tests LOOK like a weekly pattern: **5 of 23** series cross ±2 SE on lag-7 return autocorrelation (about 1.2 expected by chance at 5%), and **7 of 23** have a weekday-ANOVA p < 0.05 (smallest p 0.001, Sesamum). But the flags are mixed-sign (3 negative, 2 positive) — a genuine 7-day cycle in levels would give same-signed lag-7 return autocorrelations — and the pooled lag-7 ACF is **-0.009** (SE 0.064), indistinguishable from zero. The median 6–8-day periodogram power share is 0.14, BELOW the ~0.18 an even spread over the 11 bins would give: no spectral evidence of a 7-day cycle either. The weekday-ANOVA flags are addressed in the sensitivity section below — they do not survive scrutiny either.

## The driver: Sunday 08 Nov 2026 in the portal's own published table

On Sunday 08 Nov, **14 of 30 series fell more than 5% in one day** (Potato −56% to Rs 394.20, Sesamum −44%, Jowar −37%, Bengal Gram −33%), and on Monday 09 Nov they bounced back almost exactly (Potato +81%, Sesamum +51%). Pooled mean log-return: Sunday −5.2%, Monday +3.7% — both dominated by that single weekend. The 08 Nov Potato figure appears identically in the 10, 11 and 12 Nov extracts, so it is the portal's published number, not an extraction error. Notably it is NOT a thin-Sunday composition effect: Potato arrivals on 08 Nov were 19,148 t, roughly DOUBLE the ~9,000 t of the surrounding days, while Onion arrivals collapsed to 735 t (from ~4,800–9,800 t) with its price UP — the two vegetables moved opposite ways on the same day. Whatever happened on 08 Nov, it was a one-day event, not a weekly rhythm: no other Sunday in the window shows anything like it.

## Sensitivity test — the verdict rests on this

Removing just the 08 Nov and 09 Nov returns and recomputing: lag-7 flags fall from **5 to 0 of 23**, and the pooled lag-7 ACF stays at **-0.009** (SE 0.042). The entire 'weekly pattern' in the autocorrelation was two returns out of 23. The weekday ANOVA does NOT clean up the same way — p < 0.05 goes from **7 to 9 of 23** — but that is a small-n artefact, not a cycle: after the cut, the Sunday and Monday groups hold only 2 returns each, so one pair of large moves decides the test, and the 'significant' series disagree on direction (Onion's two Sundays are +24.9% and +13.5%; Green Gram's are −12.4% and −16.7%; Sesamum's −23.8% and −14.1%). The honest weekday check is the POOLED mean return by weekday (all series together, 8–9 Nov excluded): Monday +0.3%, Tuesday +0.1%, Wednesday −1.6%, Thursday −1.1%, Friday +0.0%, Saturday +2.1%, Sunday −2.3% — every one within ~2 SE of zero (SEs 1.1–2.3 points). No weekday stands out.

## The roadmap premise was wrong — and that matters

The roadmap said '40+ days of data'. The National series in `mandi_prices_clean.csv` spans **2026-10-26 → 2026-11-18: 24 daily observations** per commodity, every calendar day present, no gaps. The 40+ day figure is the whole dataset (per-mandi sample from 29 Sep); National rows only start 26 Oct (first browser extract 30 Oct, backfilled to 26 Oct). Two consequences: (a) a lag-7 autocorrelation on 23 returns has SE ≈ 0.21, so only a LARGE weekly effect (|r7| ≳ 0.42) could have been caught — a small genuine cycle cannot be ruled out; (b) the National series is 100% portal data, so no sample-vs-portal join sits inside the window (the sample generator never wrote National rows).

## Caveats

- **Commodity-name variants**: the cleaned file carries both sample-era short names (e.g. `Barley`, `Sesamum`, `Sugarcane`) and portal names (e.g. `Barley(Jau)`); the short names have 1–3 observations and fall below the 20-observation floor, so only the 23 portal-named series are tested. A name-normalisation pass would lengthen some series — noted, not done here.
- **Weekday ANOVA is uninformative at this n** (~3 returns per weekday; 2 per group for Sunday/Monday after the sensitivity cut). Per-series p-values swing on single moves — Jowar alone posts +69.5% (10 Nov), +45.5% (07 Nov) and −34.4% (05 Nov); Potato swings +51.4% (15 Nov) then −60.6% (16 Nov); Copra −49.3% (18 Nov). The pooled weekday means (above) are the honest check, and they show nothing.
- **08 Nov itself deserves a follow-up**: a one-day −56% Potato move with doubled arrivals is either a real local glut or a portal reporting quirk; the arrival/price divergence vs Onion the same day keeps both readings open. Flagged for the data-quality watch, not resolved here.

## Per-commodity results

| Commodity | n | lag-7 ACF | z | Excl 8–9 Nov r7 | z | Peak period | 6–8d power | ANOVA p | ANOVA p excl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Bajra(Pearl Millet/Cumbu) | 24 | +0.329 | +1.58 | +0.198 | +0.91 | 2.2d | 0.13 | 0.047 | 0.179 |
| Barley(Jau) | 22 | -0.401 | -1.84 | -0.401 | -1.84 | 2.0d | 0.35 | 0.936 | 0.936 |
| Bengal Gram(Gram)(Whole) | 24 | +0.356 | +1.71 | +0.022 | +0.10 | 2.4d | 0.05 | 0.020 | 0.023 |
| Black Gram(Urd Beans)(Whole) | 24 | +0.157 | +0.75 | -0.300 | -1.37 | 24.0d | 0.39 | 0.015 | 0.011 |
| Copra | 24 | -0.271 | -1.30 | -0.387 | -1.77 | 2.0d | 0.16 | 0.791 | 0.510 |
| Cotton | 24 | +0.017 | +0.08 | +0.118 | +0.54 | 12.0d | 0.14 | 0.315 | 0.206 |
| Green Gram(Moong)(Whole) | 24 | -0.578 | -2.77 | -0.096 | -0.44 | 12.0d | 0.14 | 0.979 | 0.000 |
| Groundnut | 24 | -0.432 | -2.07 | +0.230 | +1.06 | 24.0d | 0.06 | 0.846 | 0.020 |
| Jowar(Sorghum) | 24 | +0.192 | +0.92 | +0.101 | +0.46 | 3.4d | 0.36 | 0.064 | 0.090 |
| Lentil(Masur)(Whole) | 23 | -0.010 | -0.05 | -0.205 | -0.94 | 23.0d | 0.07 | 0.026 | 0.048 |
| Maize | 24 | +0.162 | +0.77 | -0.023 | -0.10 | 24.0d | 0.20 | 0.181 | 0.185 |
| Mustard | 24 | -0.051 | -0.25 | -0.087 | -0.40 | 3.0d | 0.05 | 0.541 | 0.753 |
| Onion | 24 | +0.020 | +0.10 | -0.122 | -0.56 | 24.0d | 0.15 | 0.025 | 0.000 |
| Paddy(Common) | 24 | +0.059 | +0.28 | +0.106 | +0.49 | 8.0d | 0.40 | 0.120 | 0.098 |
| Paddy(Fine/Superfine/Grade A) | 21 | -0.072 | -0.32 | +0.196 | +0.83 | 10.5d | 0.22 | 0.467 | 0.305 |
| Potato | 24 | -0.526 | -2.52 | +0.151 | +0.69 | 2.0d | 0.05 | 0.999 | 0.028 |
| Ragi(Finger Millet) | 24 | +0.003 | +0.01 | +0.162 | +0.74 | 2.4d | 0.16 | 0.237 | 0.322 |
| Red Gram/Arhar/Tur(Whole) | 24 | +0.091 | +0.44 | +0.127 | +0.58 | 4.0d | 0.07 | 0.291 | 0.529 |
| Sesamum(Sesame,Gingelly,Til) | 24 | +0.488 | +2.34 | -0.171 | -0.78 | 2.4d | 0.08 | 0.001 | 0.006 |
| Soyabean | 24 | -0.266 | -1.27 | -0.232 | -1.06 | 24.0d | 0.11 | 0.636 | 0.175 |
| Sunflower/Sunflower Seed | 20 | +0.310 | +1.35 | +0.229 | +0.94 | 2.5d | 0.05 | 0.133 | 0.200 |
| Tomato | 24 | -0.243 | -1.17 | -0.024 | -0.11 | 8.0d | 0.24 | 0.783 | 0.542 |
| Wheat | 24 | +0.458 | +2.20 | +0.193 | +0.88 | 2.4d | 0.07 | 0.003 | 0.033 |

## Checks

- **Hand-check (Onion lag-7 ACF)**: manual recompute from the raw returns +0.0205 vs script +0.0205 → **MATCH**.
- **Determinism**: re-run the script and diff `data/processed/seasonality_check_2026-11-20.csv` — identical (run twice during this day).
- **Chart**: `charts/seasonality_check_2026-11-20.svg` — lag-7 ACF per commodity against ±2 SE bands.

## Files

- `src/seasonality_check.py`
- `data/processed/seasonality_check_2026-11-20.csv`
- `charts/seasonality_check_2026-11-20.svg`
- `reports/day41_seasonality_check.md` (this file)

## Follow-up

- Re-run this test in early December on ~4 weeks of real portal rows — the first window where a small real weekly cycle could actually be detected.
- Consider a commodity-name normalisation pass (sample-era short names → portal names) to lengthen the pre-portal series.
- Keep 08 Nov 2026 on the data-quality watch: one-day −56% Potato with doubled arrivals, unexplained.
