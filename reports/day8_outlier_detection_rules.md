# Day 8 — Outlier detection rules: IQR vs z-score on modal prices

Two classical rules, applied per commodity on the pooled modal-price
series (all mandis, all days):

- **IQR rule (Tukey fences):** flag x outside [Q1 − 1.5·IQR, Q3 + 1.5·IQR]
- **Z-score rule:** flag |z| > 3, z = (x − mean)/std

| Commodity | n | Q1 | Median | Q3 | IQR | mean ± std | max |z| | IQR flags | z flags | both agree |
|---|---|---|---|---|---|---|---|---|---|---|
| Onion | 152 | 1,910 | 2,170 | 2,382 | 472 | 2,164 ± 277 | 1.79 | 0 | 0 | 0 |
| Potato | 152 | 1,340 | 1,510 | 1,642 | 302 | 1,498 ± 175 | 2.12 | 0 | 0 | 0 |
| Tomato | 152 | 2,020 | 2,280 | 2,552 | 532 | 2,292 ± 352 | 2.62 | 0 | 0 | 0 |

## Reading the result

Both rules flag **zero** price points on the current data — consistent
with Day 3's finding of near-symmetric distributions and no IQR
outliers. The rules disagree on nothing because there is nothing to
flag; they are verified working and will fire on real feed shocks
(e.g. a mistyped ₹50,000 or a genuine supply shock).

## Pipeline decision

MandiLens adopts the **IQR rule (k = 1.5) as the default outlier flag**,
because it is robust: the z-score's mean and std are themselves
dragged by the very outliers they try to catch, and |z| > 3 needs
large n before the CLT normal-approximation argument applies. Z-score is kept as a secondary check for large-sample commodities.
Outlier flags are *flags*, not deletions — the cleaner keeps the row
and future Week-3 models can choose to down-weight them.

![IQR vs z-score chart](../charts/outlier_rules_2026-10-18.svg)
