#!/usr/bin/env python3
"""MandiLens Day 32 — backfill check.

Question: of the 11 per-mandi days missing between the sample feed's end
(29 Oct 2026) and the first per-mandi portal pull (10 Nov 2026), how many
are recoverable from the portal's rolling 3-day window, and how many are
permanently lost?

Facts the check rests on (verified against the dataset, not assumed):
  * Sample per-mandi feed ends 29 Oct 2026 (30 days per market).
  * First Part B pull ran 10 Nov 2026; its window was 06-08 Nov.
  * The portal publishes a rolling 3-day window, frozen ~2 days behind
    real time (on 10 Nov it showed 06-08 Nov, not 08-10 Nov).
  * Only 3 of the 8 tracked mandis ever yield vegetable rows from the
    portal (Azadpur, Bowenpally, Sealdah Koley Market). The other 5 are
    structurally empty: Koyambedu + Muhana not listed, Naroda "No Data
    Available", APMC Mumbai + Bengaluru APMC tables carry no vegetables.

Classification per gap day:
  * RECOVERED — real per-mandi rows already in the clean dataset.
  * RECOVERABLE_TODAY — inside today's portal 3-day window (from today's
    mandi extract, when present; else predicted from the 2-day freeze).
  * PERMANENTLY_LOST — older than any past or future window: no pull ran
    while the day was in the window, and the window has slid past it.
  * NEVER_OBTAINABLE — the day is lost for a market that structurally
    cannot yield rows (counted separately so "lost" is never overstated).

Usage: python3 src/backfill_check.py [YYYY-MM-DD]
Writes data/processed/backfill_check_<date>.csv and prints the summary.
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

MARKETS = ["Azadpur", "Vashi", "Koyambedu", "Sealdah Koley Market",
           "Yeshwanthpur", "Bowenpally", "Naroda", "Muhana"]
COMMODITIES = ["Onion", "Potato", "Tomato"]

SAMPLE_END = date(2026, 10, 29)      # last sample per-mandi day
FIRST_PULL = date(2026, 11, 10)      # first Part B pull
GAP_START = SAMPLE_END + timedelta(days=1)          # 30 Oct
GAP_END = FIRST_PULL - timedelta(days=1)            # 09 Nov
# Markets that yielded real vegetable rows on the 10 Nov pull.
REPORTING = {"Azadpur", "Bowenpally", "Sealdah Koley Market"}


def parse(d):
    d = d.strip()
    if "-" in d:
        y, m, dd = map(int, d.split("-"))
        return date(y, m, dd)
    dd, mm, y = map(int, d.split("/"))
    return date(y, mm, dd)


def real_per_mandi_dates():
    """(market, date) pairs with real portal per-mandi rows in the clean set."""
    have = set()
    with open(CLEAN, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["market"] == "National":
                continue
            if r["source_file"].endswith("-mandi.csv"):
                have.add((r["market"], parse(r["arrival_date"])))
    return have


def today_window(run_date):
    """The portal's 3-day window for today's pull.

    From today's mandi extract when it exists (dates actually shown),
    else predicted: the portal freezes ~2 days behind, so on run date D
    the window is D-4, D-3, D-2 (verified: 10 Nov pull showed 06-08 Nov).
    """
    fname = os.path.join(RAW_DIR, f"mandi_prices_{run_date.isoformat()}-mandi.csv")
    if os.path.exists(fname):
        dates = set()
        with open(fname, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                dates.add(parse(r["arrival_date"]))
        return sorted(dates), "extract"
    pred = [run_date - timedelta(days=i) for i in (4, 3, 2)]
    return sorted(pred), "predicted (2-day freeze)"


def main():
    run_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 \
        else date.today()
    have = real_per_mandi_dates()
    window, window_src = today_window(run_date)

    gap_days = [GAP_START + timedelta(days=i)
                for i in range((GAP_END - GAP_START).days + 1)]
    print(f"Backfill check — run {run_date} (Day 32)")
    print(f"Gap window: {GAP_START} .. {GAP_END} = {len(gap_days)} days")
    print(f"Today's portal window: {window[0]} .. {window[-1]} ({window_src})")
    print()

    rows = []
    counts = defaultdict(int)
    for d in gap_days:
        for m in MARKETS:
            if (m, d) in have:
                status = "RECOVERED"
            elif d in window:
                status = "RECOVERABLE_TODAY" if m in REPORTING \
                    else "NEVER_OBTAINABLE"
            elif m not in REPORTING:
                status = "NEVER_OBTAINABLE"
            else:
                status = "PERMANENTLY_LOST"
            counts[status] += 1
            rows.append({"date": d.isoformat(), "market": m, "status": status,
                         "commodities": 3})

    for r in rows:
        print(f"  {r['date']}  {r['market']:<20} {r['status']}")
    print()
    print("Market-day counts (each = 3 commodity rows):")
    for s in ("RECOVERED", "RECOVERABLE_TODAY", "PERMANENTLY_LOST",
              "NEVER_OBTAINABLE"):
        print(f"  {s:<20} {counts[s]:>3} market-days "
              f"({counts[s] * 3} commodity rows)")
    print()
    lost = counts["PERMANENTLY_LOST"]
    print(f"Verdict: {lost} market-days ({lost * 3} commodity rows) across "
          f"{len(REPORTING)} reporting markets are PERMANENTLY LOST — "
          f"{GAP_START} .. {date(2026, 11, 5)} fell out of the portal's "
          f"3-day window before any per-mandi pull ran.")
    print(f"Recovered so far: {counts['RECOVERED']} market-days; "
          f"recoverable today: {counts['RECOVERABLE_TODAY']} market-days "
          f"({GAP_END} for the reporting markets, if today's pull lands).")

    out = os.path.join(BASE_DIR, "data", "processed",
                       f"backfill_check_{run_date.isoformat()}.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "market", "status",
                                          "commodities"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
