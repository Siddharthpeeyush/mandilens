# MandiLens daily browser-extraction brief

(Pasted verbatim as a browser-task assignment each day. Read-only: no downloads,
no logins, no personal data. The target is the Government of India's public
Agmarknet portal — published mandi price tables.)

## Goal

Extract today's mandi price tables from https://agmarknet.gov.in/home
("Market Wise Price & Arrival" tab) for each mandi listed below, and report them
as plain text blocks.

## Steps

1. Open https://agmarknet.gov.in/home and wait for the dashboard to load.
   Use the "Market Wise Price & Arrival" tab (the default).
2. For EACH mandi in the list below:
   a. Click "Reset".
   b. Open the "State/UT" dropdown: click to UNCHECK "All States/UT", then check
      the state. (Click the text row, not just the checkbox.)
   c. Open the "District" dropdown: uncheck "All Districts", then check the
      district. The Market dropdown enables only after this.
   d. Open the "Market" dropdown, type the market keyword in its search box and
      select the matching market. If nothing matches, write a NOT_FOUND block
      (see format) and continue with the next mandi.
   e. Click "Go" and wait for the table to load.
   f. Report the block in the exact format below.
3. After all mandis, end your report with a line containing only: DONE

## Report format (follow EXACTLY)

Copy every value EXACTLY as displayed. If a cell shows "-" or is blank, write
EMPTY. NEVER invent, round, or "fix" a value. If a value is not readable, write
UNREADABLE.

```
MARKET: <exact market name as shown, e.g. APMC Azadpur>
STATE: <state>, DISTRICT: <district>
DATES: <date from Price header 1> | <date from Price header 2> | <date from Price header 3>
HEADER: Commodity Group | Commodity | MSP (Rs./Quintal) | Price_D1 | Price_D2 | Price_D3 | Arrival_D1 | Arrival_D2 | Arrival_D3
ROW: Vegetables | Onion | - | 3545.46 | 3451.56 | 3129.83 | 3014.78 | 9149.75 | 18629.89
ROW: ...

```

For a missing market:

```
MARKET: NOT_FOUND (searched "<keyword>" in <district>, <state>)
```

Separate each market's block with one blank line.

## Mandi list (in this order)

1. State "NCT of Delhi" / District "Delhi" / search "Azadpur" (expect "APMC Azadpur")
2. State "Maharashtra" / District "Thane" / search "Vashi" (may not exist: also try
   District "Raigad" once; if still nothing, NOT_FOUND)
3. State "Tamil Nadu" / District "Chennai" / search "Koyambedu"
4. State "West Bengal" / District "Kolkata" / search "Sealdah"
5. State "Karnataka" / District "Bengaluru Urban" (if absent try "Bangalore") /
   search "Yeshwanthpur"
6. State "Gujarat" / District "Ahmedabad" / search "Naroda"
7. State "Rajasthan" / District "Jaipur" / search "Muhana"
8. State "Telangana" / District "Hyderabad" / search "Bowenpally"

If a District option doesn't exist under the state, try the closest variant and
record the exact names you used in the STATE/DISTRICT line.
