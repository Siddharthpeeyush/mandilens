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
