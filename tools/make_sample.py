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
           "arrival_date", "min_price", "max_price", "modal_price"]


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    end = dt.date.today()
    start = end - dt.timedelta(days=days - 1)
    rng = random.Random(42)
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
