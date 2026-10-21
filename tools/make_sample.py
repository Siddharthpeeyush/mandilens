#!/usr/bin/env python3
"""Generate clearly-labelled SAMPLE mandi data (seeded, reproducible).

Used until a free data.gov.in API key is configured. Every file this
creates is synthetic — see data/README.md. Re-running overwrites the
same dates deterministically.
"""
import csv
import datetime as dt
import os
import random
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

MANDIS = [
    ("NCT of Delhi", "Delhi", "Azadpur"),
    ("Maharashtra", "Mumbai", "Vashi"),
    ("Tamil Nadu", "Chennai", "Koyambedu"),
    ("West Bengal", "Kolkata", "Sealdah Koley Market"),
    ("Karnataka", "Bengaluru", "Yeshwanthpur"),
    ("Telangana", "Hyderabad", "Bowenpally"),
    ("Gujarat", "Ahmedabad", "Naroda"),
    ("Rajasthan", "Jaipur", "Muhana"),
]

COMMODITIES = {
    "Onion":  {"base": 2100, "varieties": ["Red", "White"], "vol": 0.05},
    "Potato": {"base": 1450, "varieties": ["Jyoti", "Chipsona"], "vol": 0.04},
    "Tomato": {"base": 2200, "varieties": ["Desi", "Hybrid"], "vol": 0.09},
}

COLUMNS = ["state", "district", "market", "commodity", "variety", "grade",
           "arrival_date", "min_price", "max_price", "modal_price",
           "arrival_tonnes"]

# Typical daily arrivals (tonnes) per mandi — sample scale only. The
# government's published "Market Wise Price & Arrival" table carries a real
# arrivals column; the sample mirrors that schema so downstream analysis can
# treat both sources identically.
ARRIVAL_BASE = {
    "Azadpur": 1300, "Vashi": 750, "Koyambedu": 950,
    "Sealdah Koley Market": 550, "Yeshwanthpur": 480, "Bowenpally": 430,
    "Naroda": 380, "Muhana": 280,
}
ARRIVAL_COMM_MULT = {"Onion": 1.0, "Potato": 0.85, "Tomato": 0.9}


def sample_arrivals(rng_arr, market, comm):
    """One day's synthetic arrivals (tonnes) for a market-commodity pair.

    Drawn from a stream independent of the price drift, so the sample does
    NOT bake in an arrival-price relationship — correlations computed on
    sample arrivals should come out near zero, which is the honest result
    for synthetic data.
    """
    base = ARRIVAL_BASE[market] * ARRIVAL_COMM_MULT[comm]
    tonnes = base * (1 + rng_arr.gauss(0, 0.15))
    if rng_arr.random() < 0.05:      # occasional thin-supply day
        tonnes *= rng_arr.uniform(0.35, 0.6)
    return max(20, int(round(tonnes)))


def gen_day(day, seed):
    """Generate one day's sample file. Seed derived from the date so each
    date is deterministic and re-runnable without rewriting history."""
    rng = random.Random(seed)
    rng_arr = random.Random(seed ^ 0xA771)  # separate stream: prices untouched
    market_mult = {m[2]: rng.uniform(0.85, 1.25) for m in MANDIS}
    rows = []
    for state, district, market in MANDIS:
        for comm, spec in COMMODITIES.items():
            drift = rng.gauss(0, spec["vol"])
            if comm == "Tomato" and rng.random() < 0.08:  # supply shock
                drift += rng.choice([0.22, -0.18])
            modal = round(spec["base"] * market_mult[market]
                          * (1 + drift) / 10) * 10
            variety = rng.choice(spec["varieties"])
            rows.append({
                "state": state, "district": district, "market": market,
                "commodity": comm, "variety": variety, "grade": "FAQ",
                "arrival_date": day.strftime("%d/%m/%Y"),
                "min_price": round(modal * 0.90 / 10) * 10,
                "max_price": round(modal * 1.15 / 10) * 10,
                "modal_price": modal,
                "arrival_tonnes": sample_arrivals(rng_arr, market, comm),
            })
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, f"mandi_prices_{day.isoformat()}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"SAMPLE: {len(rows)} rows -> {path}")


def main():
    # --day YYYY-MM-DD : generate just that one day (seeded by the date).
    # Otherwise: bulk-generate N days ending today (legacy scaffold mode).
    if "--day" in sys.argv:
        day = dt.date.fromisoformat(sys.argv[sys.argv.index("--day") + 1])
        gen_day(day, int(day.strftime("%Y%m%d")))
        return
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    end = dt.date.today()
    start = end - dt.timedelta(days=days - 1)
    rng = random.Random(42)
    rng_arr = random.Random(42 ^ 0xA771)
    market_mult = {m[2]: rng.uniform(0.85, 1.25) for m in MANDIS}
    os.makedirs(RAW_DIR, exist_ok=True)

    day = start
    while day <= end:
        rows = []
        for state, district, market in MANDIS:
            for comm, spec in COMMODITIES.items():
                drift = rng.gauss(0, spec["vol"])
                if comm == "Tomato" and rng.random() < 0.08:  # supply shock
                    drift += rng.choice([0.22, -0.18])
                modal = round(spec["base"] * market_mult[market]
                              * (1 + drift) / 10) * 10
                variety = rng.choice(spec["varieties"])
                rows.append({
                    "state": state, "district": district, "market": market,
                    "commodity": comm, "variety": variety, "grade": "FAQ",
                    "arrival_date": day.strftime("%d/%m/%Y"),
                    "min_price": round(modal * 0.90 / 10) * 10,
                    "max_price": round(modal * 1.15 / 10) * 10,
                    "modal_price": modal,
                    "arrival_tonnes": sample_arrivals(rng_arr, market, comm),
                })
        path = os.path.join(RAW_DIR, f"mandi_prices_{day.isoformat()}.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        print(f"SAMPLE: {len(rows)} rows -> {path}")
        day += dt.timedelta(days=1)


if __name__ == "__main__":
    main()
