#!/usr/bin/env python3
"""MandiLens website data builder.

Reads the daily pipeline's processed CSVs and emits site/data.js
(`window.MANDILENS_DATA = {...}`) so the static site always shows the
latest verified numbers. Re-run after src/run_daily.py:

    python3 site/build_site.py

Honesty rules baked in:
- "today" = the latest date in the National (real Agmarknet portal) feed.
- Per-mandi Onion/Potato/Tomato history was SEEDED SAMPLE data (tools/
  make_sample.py) ending 29 Oct 2026 — flagged `sample: true` everywhere
  and badged on the site. Never presented as real mandi prices. From
  10 Nov 2026 (Day 31) real portal per-mandi rows land in
  data/raw/mandi_prices_YYYY-MM-DD-mandi.csv; build_site.py marks the
  latest-date mandi rows `mandiReal: true` only when their source_file
  ends "-mandi.csv", and the note says which it is.
- Forecasts were fit on data to 29 Oct 2026 for 30 Oct-05 Nov 2026 —
  dates are carried verbatim, never relabelled as "next 7 days".
"""
import csv
import glob
import json
import os
from collections import defaultdict
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE, "data", "processed", "mandi_prices_clean.csv")

# Short display name, Hindi name, category (Agmarknet's 5 groups + cash crops).
COMMODITY_META = {
    "Onion": ("Onion", "प्याज", "Vegetables"),
    "Potato": ("Potato", "आलू", "Vegetables"),
    "Tomato": ("Tomato", "टमाटर", "Vegetables"),
    "Bajra(Pearl Millet/Cumbu)": ("Bajra", "बाजरा", "Cereals"),
    "Barley(Jau)": ("Barley", "जौ", "Cereals"),
    "Jowar(Sorghum)": ("Jowar", "ज्वार", "Cereals"),
    "Maize": ("Maize", "मक्का", "Cereals"),
    "Paddy(Common)": ("Paddy (Common)", "धान (सामान्य)", "Cereals"),
    "Paddy(Fine/Superfine/Grade A)": ("Paddy (Fine)", "धान (बारीक)", "Cereals"),
    "Ragi(Finger Millet)": ("Ragi", "रागी", "Cereals"),
    "Wheat": ("Wheat", "गेहूं", "Cereals"),
    "Bengal Gram(Gram)(Whole)": ("Bengal Gram", "चना", "Pulses"),
    "Black Gram(Urd Beans)(Whole)": ("Black Gram", "उड़द", "Pulses"),
    "Green Gram(Moong)(Whole)": ("Green Gram", "मूंग", "Pulses"),
    "Lentil(Masur)(Whole)": ("Lentil", "मसूर", "Pulses"),
    "Red Gram/Arhar/Tur(Whole)": ("Red Gram", "अरहर", "Pulses"),
    "Copra": ("Copra", "खोपरा", "Oilseeds"),
    "Groundnut": ("Groundnut", "मूंगफली", "Oilseeds"),
    "Mustard": ("Mustard", "सरसों", "Oilseeds"),
    "Niger Seed(Ramtil)": ("Niger Seed", "रामतिल", "Oilseeds"),
    "Safflower": ("Safflower", "कुसुम", "Oilseeds"),
    "Sesamum(Sesame,Gingelly,Til)": ("Sesamum", "तिल", "Oilseeds"),
    "Soyabean": ("Soyabean", "सोयाबीन", "Oilseeds"),
    "Sunflower/Sunflower Seed": ("Sunflower", "सूरजमुखी", "Oilseeds"),
    "Cotton": ("Cotton", "कपास", "Fibre & cash crops"),
    "Sugarcane": ("Sugarcane", "गन्ना", "Fibre & cash crops"),
}

MANDI_META = {
    "Azadpur": ("Azadpur", "Delhi"),
    "Vashi": ("Vashi", "Mumbai"),
    "Koyambedu": ("Koyambedu", "Chennai"),
    "Sealdah Koley Market": ("Sealdah", "Kolkata"),
    "Yeshwanthpur": ("Yeshwanthpur", "Bengaluru"),
    "Bowenpally": ("Bowenpally", "Hyderabad"),
    "Naroda": ("Naroda", "Ahmedabad"),
    "Muhana": ("Muhana", "Jaipur"),
}


def num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def main():
    rows = list(csv.DictReader(open(CLEAN)))
    nat = [r for r in rows if r["market"] == "National"]
    nat_dates = sorted({r["arrival_date"] for r in nat})
    latest, prev = nat_dates[-1], nat_dates[-2]
    all_dates = sorted({r["arrival_date"] for r in rows})

    # --- Today's National prices (real portal data) ---
    today, prev_map = [], {}
    for r in nat:
        if r["arrival_date"] == prev:
            prev_map[r["commodity"]] = num(r["modal_price"])
    for r in sorted([x for x in nat if x["arrival_date"] == latest],
                    key=lambda x: COMMODITY_META.get(x["commodity"], (x["commodity"], "", ""))[0]):
        price, msp = num(r["modal_price"]), num(r["msp_rs"])
        pp = prev_map.get(r["commodity"])
        chg = round((price - pp) / pp * 100, 1) if price and pp else None
        short, hindi, cat = COMMODITY_META.get(
            r["commodity"], (r["commodity"], "", "Other"))
        today.append({
            "commodity": r["commodity"], "short": short, "hindi": hindi,
            "category": cat, "price": price, "perKg": round(price / 100, 2) if price else None,
            "changePct": chg, "arrivals": num(r["arrival_tonnes"]),
            "msp": msp,
            "vsMspPct": round((price - msp) / msp * 100, 1) if price and msp else None,
        })

    # --- National trend series (real portal data, 26 Oct 2026 -> latest) ---
    series = {}
    for r in nat:
        p = num(r["modal_price"])
        if p is None:
            continue
        series.setdefault(r["commodity"], []).append(
            {"d": r["arrival_date"], "p": p,
             "a": num(r["arrival_tonnes"]), "msp": num(r["msp_rs"])})
    for v in series.values():
        v.sort(key=lambda x: x["d"])

    # --- Movers (latest vs previous trading day, National) ---
    with_chg = [t for t in today if t["changePct"] is not None]
    risers = sorted(with_chg, key=lambda t: -t["changePct"])[:5]
    fallers = sorted(with_chg, key=lambda t: t["changePct"])[:5]

    # --- Per-mandi rows at the latest date ---
    # Before Day 31 these were SEEDED SAMPLE (tools/make_sample.py, ends
    # 29 Oct 2026). From 10 Nov 2026 the per-mandi pull lands real portal
    # rows in data/raw/mandi_prices_YYYY-MM-DD-mandi.csv, so a latest-date
    # row whose source_file ends "-mandi.csv" is REAL — never label it
    # sample, and never label sample rows real. The note says which.
    mandi = [r for r in rows if r["market"] != "National"]
    mandi_latest = max(r["arrival_date"] for r in mandi)
    mandi_today = []
    for r in mandi:
        p = num(r["modal_price"])
        if p is None:
            continue
        if r["arrival_date"] == mandi_latest:
            mandi_today.append({
                "market": r["market"], "commodity": r["commodity"],
                "price": p, "perKg": round(p / 100, 2),
                "min": num(r["min_price"]), "max": num(r["max_price"]),
            })
    mandi_real = any(
        r.get("source_file", "").endswith("-mandi.csv")
        for r in mandi if r["arrival_date"] == mandi_latest)
    mandi_note = (
        "Per-mandi Onion/Potato/Tomato prices are real Agmarknet portal "
        "prices for the mandis that reported on this date; mandis that did "
        "not report show no row."
        if mandi_real else
        "Per-mandi Onion/Potato/Tomato prices are seeded sample data "
        "(tools/make_sample.py), not real mandi prices.")

    # --- Forecast (OLS champion, fit to 29 Oct; window 30 Oct-05 Nov) ---
    fc_paths = sorted(glob.glob(os.path.join(
        BASE, "data", "processed", "forecast_table_*.csv")))
    forecast, fc_meta = {}, {}
    if fc_paths:
        fc_rows = list(csv.DictReader(open(fc_paths[-1])))
        fc_meta = {"file": os.path.basename(fc_paths[-1]),
                   "dates": sorted({r["forecast_date"] for r in fc_rows}),
                   "model": fc_rows[0]["model"] if fc_rows else ""}
        for r in fc_rows:
            key = f"{r['market']}||{r['commodity']}"
            forecast.setdefault(key, []).append(
                {"d": r["forecast_date"], "p": round(num(r["forecast_price"]), 2),
                 "h": int(r["horizon_days"])})
        for v in forecast.values():
            v.sort(key=lambda x: x["h"])

    data = {
        "meta": {
            "generated": date.today().isoformat(),
            "latestDate": latest, "prevDate": prev,
            "datasetRange": [all_dates[0], all_dates[-1]],
            "rows": len(rows),
            "commodities": len({r["commodity"] for r in rows}),
            "todayCount": len(today),
            "nationalSeriesStart": nat_dates[0],
            "mandiSampleLatest": mandi_latest,
            "mandiReal": mandi_real,
            "mandiSampleNote": mandi_note,
            "forecast": fc_meta,
            "mae": {"Onion": 208, "Potato": 144, "Tomato": 266},
            "source": "Agmarknet portal (agmarknet.gov.in), Government of India",
        },
        "today": today,
        "series": series,
        "risers": risers,
        "fallers": fallers,
        "mandiToday": mandi_today,
        "forecast": forecast,
        "mandis": [{"market": m, "short": s, "city": c}
                   for m, (s, c) in MANDI_META.items()],
        "categories": ["Vegetables", "Cereals", "Pulses", "Oilseeds",
                       "Fibre & cash crops"],
    }
    out = os.path.join(BASE, "site", "data.js")
    with open(out, "w") as fh:
        fh.write("window.MANDILENS_DATA = ")
        # Compact separators: data.js must stay well under the ~60KB
        # push_files argument limit so the daily cron can push it in one go.
        # (mandiSeries is computed but NOT emitted — the site renders the
        # mandi table from mandiToday only.)
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";\n")
    print(f"wrote {out}: {len(today)} commodities on {latest}, "
          f"{len(series)} series, {len(mandi_today)} mandi rows "
          f"({'real' if mandi_real else 'sample'}, {mandi_latest}), "
          f"forecast {len(forecast)} keys")


if __name__ == "__main__":
    main()
