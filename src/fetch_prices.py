#!/usr/bin/env python3
"""Fetch daily mandi prices from the data.gov.in (OGD) Agmarknet API.

Dataset : "Current Daily Price of Various Commodities from various Markets (Mandi)"
Endpoint: https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070

Needs env var MANDILENS_DATA_GOV_KEY (free key: https://data.gov.in ->
My Account -> API Key Management).

Writes: data/raw/mandi_prices_YYYY-MM-DD.csv
Exit 0 = fresh data written, 1 = no API key, 2 = fetch failed.
"""
import csv
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

RESOURCE_ID = os.environ.get(
    "MANDILENS_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070"
)
ENDPOINT = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

FOCUS_COMMODITIES = ["Onion", "Potato", "Tomato"]

COLUMNS = [
    "state", "district", "market", "commodity", "variety", "grade",
    "arrival_date", "min_price", "max_price", "modal_price",
]


def fetch(api_key, commodities=FOCUS_COMMODITIES, limit=10000):
    """Pull every record for the focus commodities (paged)."""
    records = []
    for commodity in commodities:
        offset = 0
        while True:
            params = {
                "api-key": api_key,
                "format": "json",
                "limit": limit,
                "offset": offset,
                "filters[Commodity]": commodity,
            }
            url = ENDPOINT + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "MandiLens/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.load(resp)
            batch = payload.get("records", [])
            records.extend(batch)
            total = payload.get("count", 0)
            offset += limit
            if not batch or offset >= total:
                break
    return records


def main():
    api_key = os.environ.get("MANDILENS_DATA_GOV_KEY")
    today = dt.date.today().isoformat()
    os.makedirs(RAW_DIR, exist_ok=True)
    out_path = os.path.join(RAW_DIR, f"mandi_prices_{today}.csv")
    if not api_key:
        print("NO_API_KEY: set MANDILENS_DATA_GOV_KEY to fetch live data.",
              file=sys.stderr)
        return 1
    try:
        records = fetch(api_key)
    except Exception as exc:  # network / API hiccup -> caller falls back
        print(f"FETCH_FAILED: {exc}", file=sys.stderr)
        return 2
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS,
                                extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow({c: rec.get(c, "") for c in COLUMNS})
    print(f"WROTE {len(records)} records -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
