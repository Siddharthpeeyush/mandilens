#!/usr/bin/env python3
"""MandiLens daily job: fetch -> clean -> analyze -> visualize -> README.

Tolerates a missing/failed live fetch: the pipeline then runs on the
existing dataset (sample data until a data.gov.in API key is configured)
and labels the report accordingly.
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


def run(script):
    proc = subprocess.run([sys.executable, os.path.join(SRC_DIR, script)],
                          capture_output=True, text=True)
    print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


def update_readme(date_s, live):
    with open(README, encoding="utf-8") as f:
        content = f.read()
    trend_chart = f"charts/price_trends_{date_s}.svg"
    movers_chart = f"charts/top_movers_{date_s}.svg"
    source = ("live Agmarknet feed (data.gov.in)" if live
              else "seeded sample data — set MANDILENS_DATA_GOV_KEY for the live feed")
    report = f"reports/daily/{date_s}.md"
    block = (
        f"{START}\n"
        f"*Last run: {pd_today(date_s)}*  \n"
        f"*Data source: {source}*\n\n"
        f"![Price trends]({trend_chart})\n\n"
        f"![Top movers]({movers_chart})\n\n"
        f"📄 [Full daily report]({report})\n"
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
    fetch_rc = run("fetch_prices.py")
    live = (fetch_rc == 0)
    if run("clean.py") != 0:
        return 1
    if run("analyze.py") != 0:
        return 1
    if run("visualize.py") != 0:
        return 1
    date_s = dt.date.today().isoformat()
    update_readme(date_s, live)
    mode = "LIVE" if live else "SAMPLE"
    print(f"DAILY DONE [{mode}]: README updated for {date_s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
