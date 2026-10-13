#!/usr/bin/env python3
"""Parse the browser task's text extract into our raw CSV schema.

Usage: python3 src/parse_browser_extract.py /tmp/extract_2026-10-13.txt [YYYY-MM-DD]

Input : text blocks exactly as specified in src/BROWSER_FETCH_BRIEF.md
Output: data/raw/mandi_prices_YYYY-MM-DD.csv with columns
        state, district, market, commodity, variety, grade,
        arrival_date (DD/MM/YYYY), min_price, max_price, modal_price,
        arrival_tonnes

The portal publishes one benchmark Price per day (mapped to modal_price;
min/max are left empty) and arrivals in metric tonnes. Rows whose market is
NOT_FOUND are skipped. Exits 1 when zero usable rows were parsed.
"""
import datetime as dt
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

COLUMNS = ["state", "district", "market", "commodity", "variety", "grade",
           "arrival_date", "min_price", "max_price", "modal_price",
           "arrival_tonnes", "msp_rs"]


def num(text):
    text = text.strip().replace(",", "")
    if text in ("", "-", "EMPTY", "UNREADABLE", "NA", "N/A"):
        return ""
    try:
        return f"{float(text):.2f}".rstrip("0").rstrip(".")
    except ValueError:
        return ""


def parse_date(text):
    # "11 Oct, 2026" or "11 Oct 2026" -> "11/10/2026"
    return dt.datetime.strptime(text.replace(",", "").strip(),
                                "%d %b %Y").strftime("%d/%m/%Y")


def parse_block(block):
    """Return (meta, rows) for one MARKET block, or None."""
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    if not lines or not lines[0].upper().startswith("MARKET:"):
        return None
    market = lines[0].split(":", 1)[1].strip()
    if market.upper().startswith("NOT_FOUND"):
        return None
    meta = {"market": market, "state": "", "district": "", "dates": []}
    if market.lower() == "national":
        meta["state"], meta["district"] = "All India", "All Districts"
    rows = []
    for ln in lines[1:]:
        up = ln.upper()
        if up.startswith("STATE:"):
            m = re.match(r"STATE:\s*(.*?),\s*DISTRICT:\s*(.*)", ln, re.I)
            if m:
                meta["state"], meta["district"] = m.group(1).strip(), m.group(2).strip()
        elif up.startswith("DATES:"):
            try:
                meta["dates"] = [parse_date(p) for p in ln.split(":", 1)[1].split("|")]
            except ValueError:
                return None
        elif up.startswith("ROW:"):
            parts = [p.strip() for p in ln.split(":", 1)[1].split("|")]
            if len(parts) >= 9:
                rows.append(parts[:9])
    if not meta["dates"] or not rows:
        return None
    return meta, rows


def main():
    if len(sys.argv) < 2:
        print("usage: parse_browser_extract.py <extract.txt> [YYYY-MM-DD]",
              file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        text = f.read()
    tag = sys.argv[2] if len(sys.argv) > 2 else dt.date.today().isoformat()

    out_rows = []
    markets_seen = set()
    for block in re.split(r"\n\s*\n", text):
        parsed = parse_block(block)
        if not parsed:
            continue
        meta, rows = parsed
        markets_seen.add(meta["market"])
        for parts in rows:
            group, commodity = parts[0], parts[1]
            msp = num(parts[2]) if len(parts) > 2 else ""
            prices, arrivals = parts[3:6], parts[6:9]
            for i, d in enumerate(meta["dates"]):
                modal = num(prices[i]) if i < len(prices) else ""
                if not modal:
                    continue
                arr = num(arrivals[i]) if i < len(arrivals) else ""
                out_rows.append({
                    "state": meta["state"], "district": meta["district"],
                    "market": meta["market"], "commodity": commodity,
                    "variety": "Aggregate", "grade": "FAQ",
                    "arrival_date": d, "min_price": "", "max_price": "",
                    "modal_price": modal, "arrival_tonnes": arr,
                    "msp_rs": msp,
                })

    if not out_rows:
        print("PARSE: zero usable rows", file=sys.stderr)
        return 1
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, f"mandi_prices_{tag}.csv")
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out_rows)
    print(f"PARSE: {len(out_rows)} rows, {len(markets_seen)} markets -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
