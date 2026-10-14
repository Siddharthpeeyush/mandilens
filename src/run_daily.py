#!/usr/bin/env python3
"""MandiLens daily job: fetch -> clean -> analyze -> visualize -> README.

Data sources, in order of preference:
  1. portal — keyless browser extract of the government's published Agmarknet
     tables (today's raw CSV already placed before this script runs);
  2. api    — data.gov.in Agmarknet API (needs MANDILENS_DATA_GOV_KEY);
  3. sample — seeded synthetic data for today (clearly labelled).

Tolerates a missing/failed fetch: the pipeline then runs on the existing
dataset and labels the report accordingly.
"""
import datetime as dt
import os
import re
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
README = os.path.join(BASE_DIR, "README.md")

START = "<!-- DAILY-UPDATE:START -->"
END = "<!-- DAILY-UPDATE:END -->"
DAY_ONE = dt.date(2026, 10, 12)  # Day 1 of the build log


def run(script, args=()):
    proc = subprocess.run([sys.executable, os.path.join(SRC_DIR, script),
                           *args], capture_output=True, text=True)
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


def update_readme(date_s, source):
    with open(README, encoding="utf-8") as f:
        content = f.read()
    trend_chart = f"charts/price_trends_{date_s}.svg"
    movers_chart = f"charts/top_movers_{date_s}.svg"
    day_n = (dt.date.today() - DAY_ONE).days + 1
    source_note = {
        "portal": "Prices taken from the government's published Agmarknet portal tables — no API key involved.",
        "api": "Pulling live prices from the data.gov.in Agmarknet feed.",
        "sample": "Currently working with seeded sample data while I wire up the live feed.",
    }[source]
    report = f"reports/daily/{date_s}.md"
    block = (
        f"{START}\n"
        f"*Day {day_n} — {pd_today(date_s)}*  \n"
        f"*{source_note}*\n\n"
        f"![Price trends]({trend_chart})\n\n"
        f"![Top movers]({movers_chart})\n\n"
        f"📄 [Full daily log]({report})\n"
        f"{END}"
    )
    content = re.sub(f"{re.escape(START)}.*?{re.escape(END)}", block,
                     content, flags=re.DOTALL)
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)


def pd_today(date_s):
    return dt.datetime.strptime(date_s, "%Y-%m-%d").strftime("%d %b %Y")


def main():
    os.chdir(BASE_DIR)
    date_s = dt.date.today().isoformat()
    raw_today = os.path.join(BASE_DIR, "data", "raw", f"mandi_prices_{date_s}.csv")
    if os.path.exists(raw_today) and os.path.getsize(raw_today) > 0:
        # Browser-extract (keyless portal pull) already placed today's file.
        print(f"SKIP_FETCH: using existing {raw_today}")
        source = "portal"
    else:
        fetch_rc = run("fetch_prices.py")
        source = "api" if fetch_rc == 0 else "sample"
    if source == "sample" and not (
            os.path.exists(raw_today) and os.path.getsize(raw_today) > 0):
        # No live data today: synthesize today's file deterministically
        # (seeded by the date, so history is never rewritten).
        proc = subprocess.run(
            [sys.executable, os.path.join(BASE_DIR, "tools", "make_sample.py"),
             "--day", date_s], capture_output=True, text=True)
        print(proc.stdout.strip())
    if run("clean.py") != 0:
        return 1
    if run("analyze.py", (date_s,)) != 0:
        return 1
    if run("visualize.py", (date_s,)) != 0:
        return 1
    update_readme(date_s, source)
    mode = {"portal": "PORTAL", "api": "LIVE", "sample": "SAMPLE"}[source]
    print(f"DAILY DONE [{mode}]: README updated for {date_s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
