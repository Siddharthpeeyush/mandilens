# MandiLens daily browser-extraction brief

(Pasted verbatim as a browser-task assignment each day. Read-only: no downloads,
no logins, no personal data. The target is the Government of India's public
Agmarknet portal — published commodity price tables.)

## Goal

Extract the published "Market Wise Price & Arrival" table from
https://agmarknet.gov.in/home — the government's own daily commodity price
publication (24 commodities: cereals, fibre crops, oil seeds, pulses,
vegetables including Onion, Potato, Tomato).

## Steps

1. Open https://agmarknet.gov.in/home and wait for the dashboard to load
   ("Market Wise Price & Arrival" tab is the default).
2. Click "Go" with the DEFAULT filters (do not change State/District/Market).
3. Click "Print All Data". A print-friendly view appears containing the FULL
   unpaginated table (header mentions "Total Records").
4. Report EXACTLY in the format below — copy every value EXACTLY as displayed.
   If a cell shows "-" or is blank, write EMPTY. NEVER invent, round, or "fix"
   a value. If a value is not readable, write UNREADABLE.

```
MARKET: National
DATES: <date from Price header 1> | <date from Price header 2> | <date from Price header 3>
HEADER: Commodity Group | Commodity | MSP (Rs./Quintal) | Price_D1 | Price_D2 | Price_D3 | Arrival_D1 | Arrival_D2 | Arrival_D3
ROW: Cereals | Wheat | 2425.00 | 2800.00 | 2790.00 | 2810.00 | 1500.00 | 1600.00 | 1550.00
ROW: ... (one ROW line per table row — report ALL rows)
```

5. End your report with a line containing only: DONE

## Notes

- The DATES line must be copied from the Price column headers (format is like
  "11 Oct, 2026" — copy it verbatim, commas included).
- Report every row of the table, including cereals, pulses, oilseeds, fibre
  crops and vegetables.
- If the table fails to load, say so plainly and stop — do not guess values.

---

## Part B — Per-mandi pull (Day 31 onwards)

Same portal, same "Market Wise Price & Arrival" tab, but one market at a
time. For EACH mandi below, set the State, District and Market filters to
the values given, click "Go", then "Print All Data", and report ONLY the
Onion, Potato and Tomato rows (other commodities are not needed for this
part). Use one block per mandi, separated by a blank line, in this format:

```
MARKET: Azadpur
STATE: NCT of Delhi, DISTRICT: Delhi
DATES: <date from Price header 1> | <date from Price header 2> | <date from Price header 3>
HEADER: Commodity Group | Commodity | MSP (Rs./Quintal) | Price_D1 | Price_D2 | Price_D3 | Arrival_D1 | Arrival_D2 | Arrival_D3
ROW: Vegetables | Onion | EMPTY | 4,151.25 | 3,873.77 | 3,768.48 | 734.61 | 4,802.58 | 7,067.04
ROW: Vegetables | Potato | EMPTY | 394.20 | 893.24 | 963.57 | 19,147.87 | 9,094.53 | 9,412.52
ROW: Vegetables | Tomato | EMPTY | 1,731.85 | 1,750.32 | 1,956.99 | 1,607.61 | 3,516.61 | 4,203.43
```

Mandis (in this order — names verified on the live portal 10 Nov 2026;
use these exact dropdown values):

1. MARKET: APMC Azadpur — STATE: NCT of Delhi, DISTRICT: Delhi
2. MARKET: APMC Mumbai — STATE: Maharashtra, DISTRICT: Mumbai
   ("Vashi" is NOT listed; APMC Mumbai is the Vashi APMC market — use it
   and report it as APMC Mumbai, never relabel it Vashi)
3. MARKET: Koyambedu — STATE: Tamil Nadu, DISTRICT: Chennai
   (NOT FOUND on 10 Nov 2026 — Chennai's dropdown returned "No options
   found"; retry, and if still absent report NOT_FOUND)
4. MARKET: Sealdah Koley Market APMC — STATE: West Bengal, DISTRICT: Kolkata
5. MARKET: Bengaluru APMC — STATE: Karnataka, DISTRICT: Bengaluru
   ("Yeshwanthpur" is NOT listed; Bengaluru APMC is the closest listed
   market — use it and report it as Bengaluru APMC, never relabel it
   Yeshwanthpur)
6. MARKET: Bowenpally APMC — STATE: Telangana, DISTRICT: Hyderabad
7. MARKET: Ahmedabad(Fruit Market, Naroda) APMC — STATE: Gujarat,
   DISTRICT: Ahmedabad (returned "No Data Available" on 10 Nov 2026)
8. MARKET: Muhana — STATE: Rajasthan, DISTRICT: Jaipur
   (NOT FOUND on 10 Nov 2026 — searched Jaipur and Jaipur Rural, "No
   options found"; retry, and if still absent report NOT_FOUND)

The parser strips a leading/trailing "APMC" from the MARKET name, so
"APMC Azadpur" lands as Azadpur, "Bowenpally APMC" as Bowenpally and
"Sealdah Koley Market APMC" as Sealdah Koley Market — the existing series
names. Report the exact portal name in the MARKET line; the parser does
the normalising.

Rules:
- Pick the market whose name matches the one given; if the exact name is
  not in the dropdown, try the closest match and note the exact name shown.
  If no match exists at all, write a block `MARKET: <name>` followed by a
  single line `NOT_FOUND` and move on — never guess values.
- The portal may show the market name with a suffix (e.g. "(F&V)"); copy
  the exact name shown into the MARKET line.
- A mandi may have no Onion/Potato/Tomato rows on a given day — report the
  rows that exist; if none of the three exist, write the MARKET + STATE /
  DISTRICT + DATES lines and then `NO_ROWS`.
- End the whole report with a line containing only: DONE
