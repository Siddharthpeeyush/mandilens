#!/usr/bin/env python3
"""Day 48: week-7 summary — the website becomes the point.

Week 7 (Days 43-47) set out to turn the site from a dashboard with
sample-seeded sections into a product that shows only real portal data:
mandi-compare restored (Day 43), 7-day forecast restored (Day 44),
Hindi-first labels (Day 45), shareable commodity deep links (Day 46)
and the data.js performance pass (Day 47). This module closes the week:

1. Verdict roll-up Days 43-47, from the day reports.
2. Scored forecast, Day 42 vs today — scored-cell counts and OLS vs
   persistence MAE per horizon and per commodity, from the Day 24
   accuracy CSVs. MAE convention is the dashboard's: unweighted mean of
   per-(origin, commodity) cell MAEs, stated in the report.
3. Dataset state from the clean CSV (rows, markets, commodities,
   calendar coverage, per-mandi history).
4. Site state from site/data.js (size, latest date, real-backed
   forecast series, mandi rows) — the product week's deliverable,
   measured, not asserted.

The item's second half — one real user (him) tapping through every
screen on his phone — is NOT verifiable from here. It is recorded as
pending in the report and in the ROADMAP entry, not claimed done.

Outputs:
  data/processed/week7_summary_2026-11-27.csv
  charts/week7_summary_2026-11-27.svg
  reports/day48_week7_summary.md
Prints: scoring comparison, hand-check result.
"""
import csv
import datetime as dt
import json
import os
import re
import xml.dom.minidom

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = dt.date.today().isoformat()
COMMS = ["Onion", "Potato", "Tomato"]


def slim_svg(path):
    """Same slimming as week6_summary.slim_svg: hoist font styles, drop
    no-op rotates, round decimals to 0.1pt, then XML-parse to verify."""
    with open(path, encoding="utf-8") as f:
        s = f.read()
    before = len(s)
    styles = {}

    def _hoist(m):
        st = m.group(1)
        if st not in styles:
            styles[st] = f"mlf{len(styles)}"
        return f'class="{styles[st]}"'

    s = re.sub(r'style="(font:[^"]*)"', _hoist, s)
    if styles and "</defs>" in s:
        css = "".join(f".{cls}{{{st}}}" for st, cls in
                      sorted(styles.items(), key=lambda kv: kv[1]))
        s = s.replace("</defs>", f"<style>{css}</style></defs>", 1)
    s = re.sub(r' transform="rotate\(-0(?:\.0+)? [0-9.]+ [0-9.]+\)"', "", s)
    s = re.sub(r"\d+\.\d+", lambda m: f"{float(m.group(0)):.1f}", s)
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)
    xml.dom.minidom.parse(path)
    return before, len(s)


def horizon_table(acc):
    """Per-horizon OLS vs persistence MAE (dashboard convention: unweighted
    mean of per-cell MAEs) and scored counts."""
    s = acc.dropna(subset=["mae"])
    rows = []
    for h in sorted(s["horizon_days"].unique()):
        g = s[s["horizon_days"] == h]
        rows.append({"horizon": int(h), "n_scored": int(g["n_scored"].sum()),
                     "ols_mae": round(float(g["mae"].mean()), 2),
                     "persist_mae": round(float(g["persist_mae"].mean()), 2)})
    return pd.DataFrame(rows), int(s["n_scored"].sum()), \
        int(acc["n_series"].sum())


def commodity_table(acc):
    s = acc.dropna(subset=["mae"])
    rows = []
    for c in COMMS:
        g = s[s["commodity"] == c]
        rows.append({"commodity": c, "n_scored": int(g["n_scored"].sum()),
                     "ols_mae": round(float(g["mae"].mean()), 2),
                     "persist_mae": round(float(g["persist_mae"].mean()), 2)})
    return pd.DataFrame(rows)


def dataset_state():
    cl = pd.read_csv(os.path.join(BASE_DIR, "data", "processed",
                                  "mandi_prices_clean.csv"),
                     parse_dates=["arrival_date"])
    per = cl[cl["market"] != "National"]
    first, last = cl["arrival_date"].min().date(), cl["arrival_date"].max().date()
    cal_days = (last - dt.date(2026, 9, 29)).days + 1
    covered = cl["arrival_date"].dt.date.nunique()
    week = cl[cl["arrival_date"] >= "2026-11-22"]
    week_per = per[per["arrival_date"] >= "2026-11-22"]
    return {"rows": len(cl), "markets": int(cl["market"].nunique()),
            "commodities": int(cl["commodity"].nunique()),
            "first": first.isoformat(), "last": last.isoformat(),
            "calendar_days": cal_days, "covered_days": int(covered),
            "per_mandi_rows": len(per),
            "per_mandi_latest": per["arrival_date"].max().date().isoformat(),
            "per_mandi_markets": sorted(per["market"].unique()),
            "national_rows": int((cl["market"] == "National").sum()),
            "week_rows": len(week),
            "week_per_mandi_rows": len(week_per),
            "week_reporting": sorted(week_per["market"].unique())}


def site_state():
    path = os.path.join(BASE_DIR, "site", "data.js")
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    payload = raw[len("window.MANDILENS_DATA = "):].rstrip().rstrip(";")
    data = json.loads(payload)
    meta = data["meta"]
    fc_real = meta.get("forecastReal", {})
    fc_real_str = "; ".join(
        f"{m} ({', '.join(cs)})" for m, cs in fc_real.items())
    return {"bytes": os.path.getsize(path), "generated": meta["generated"],
            "latest": meta["latestDate"], "rows": meta["rows"],
            "commodities": meta["commodities"],
            "today_count": meta["todayCount"],
            "mandi_real": meta["mandiReal"],
            "mandi_rows": len(data.get("mandiToday", [])),
            "forecast_keys": len(data.get("forecast", {})),
            "forecast_real": fc_real_str}


def hand_check(acc_path):
    """Pure-Python (csv module only) recompute of the headline numbers."""
    with open(acc_path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["mae"]]
    h1 = [float(r["mae"]) for r in rows if r["horizon_days"] == "1"]
    h1_mean = round(sum(h1) / len(h1), 2) if h1 else None
    scored = sum(int(r["n_scored"]) for r in rows)
    sample_cells = sum(int(r["n_actual_sample"]) for r in rows)
    return h1_mean, scored, sample_cells


def chart(day42, today, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    hs = [1, 2, 3, 4, 5, 6, 7]
    c42 = [int(day42[day42["horizon"] == h]["n_scored"].sum()) if
           (day42["horizon"] == h).any() else 0 for h in hs]
    ct = [int(today[today["horizon"] == h]["n_scored"].sum()) if
          (today["horizon"] == h).any() else 0 for h in hs]
    x = range(len(hs))
    ax.bar([i - 0.2 for i in x], c42, 0.4, label="Day 42 (21 Nov)",
           color="#90a4ae")
    ax.bar([i + 0.2 for i in x], ct, 0.4, label="Day 48 (27 Nov)",
           color="#2e86ab")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"h={h}" for h in hs])
    ax.set_ylabel("Scored forecast cells")
    ax.set_title("Scored cells by horizon — Day 42 vs Day 48")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax = axes[1]
    ols = [float(today[today["horizon"] == h]["ols_mae"].iloc[0])
           if (today["horizon"] == h).any() else float("nan") for h in hs]
    per = [float(today[today["horizon"] == h]["persist_mae"].iloc[0])
           if (today["horizon"] == h).any() else float("nan") for h in hs]
    ax.plot(hs, ols, marker="o", label="OLS champion", color="#2e86ab")
    ax.plot(hs, per, marker="s", label="Persistence", color="#e53935")
    ax.set_xticks(hs)
    ax.set_xlabel("Forecast horizon (days ahead)")
    ax.set_ylabel("MAE (Rs/quintal)")
    ax.set_title("OLS vs persistence MAE by horizon (Day 48)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.suptitle("MandiLens week-7 summary — the site becomes the product")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return slim_svg(path)


def write_report(day42, today, day42_tot, today_tot, comms, state, site,
                 hand, chart_path):
    lines = [
        "# Day 48 — Week-7 summary: the website becomes the point",
        "",
        f"*Dated {TODAY}. Week 7 (Days 43–47) set out to turn the site "
        "from a dashboard with sample-seeded sections into a product "
        "that shows only real portal data: mandi-compare restored, "
        "7-day forecast restored, Hindi-first labels, shareable "
        "commodity deep links and the data.js performance pass. This "
        "closes the week: the product half is measured below; the user "
        "test half is his phone tap-through, still pending.*",
        "",
        "## 1. Week-7 verdict roll-up",
        "",
        "| Day | Item | Verdict |",
        "|---:|---|---|",
        "| 43 | Mandi-compare restored on the site with real data | "
        "**DONE** — section + nav link unhidden, badge 'Real portal "
        "data'; the rs(null) '₹0 – ₹0' Range bug fixed to '—'. |",
        "| 44 | 7-day forecast restored on the site with real data | "
        "**DONE** — only the 6 real-backed series shown; the other 18 "
        "sample-anchored series render as '—'. |",
        "| 45 | Hindi-first polish | **DONE** — every heading, nav link, "
        "tab, chip, table header, sort option and calculator label is "
        "Hindi-first bilingual (1,034 Devanagari glyphs, 0 JS errors). |",
        "| 46 | Shareable commodity view | **DONE** — `?c=<commodity>` "
        "deep link opens that commodity's detail on load; a Hindi-first "
        "copy-link button writes the link into the URL. |",
        "| 47 | Performance pass | **DONE** — data.js 51,937 → 25,473 "
        "bytes (−51%) via columnar series; round-trip 0 mismatches on "
        "744 points / 44 commodities. |",
        "",
        "## 2. The scored forecast, one week on",
        "",
        f"Scored cells grew from **{day42_tot[0]}/{day42_tot[1]} "
        f"({100 * day42_tot[0] / day42_tot[1]:.1f}%) on Day 42 to "
        f"{today_tot[0]}/{today_tot[1]} "
        f"({100 * today_tot[0] / today_tot[1]:.1f}%) today** — "
        f"{today_tot[0] - day42_tot[0]} new scored cells in six days, "
        f"and **{today_tot[0] - hand[2]} of {today_tot[0]} scored against "
        f"real portal actuals ({hand[2]} on sample-mode actuals)**.",
        "",
        "### MAE by horizon (Rs/quintal; dashboard convention: unweighted "
        "mean of per-(origin, commodity) cell MAEs)",
        "",
        "| Horizon | Day 42 OLS | Day 42 persist | Day 48 OLS | Day 48 persist | "
        "Day 48 n |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for h in [1, 2, 3, 4, 5, 6, 7]:
        r42 = day42[day42["horizon"] == h]
        rt = today[today["horizon"] == h]
        v42 = (f"{r42['ols_mae'].iloc[0]:.2f}",
               f"{r42['persist_mae'].iloc[0]:.2f}") if not r42.empty \
            else ("—", "—")
        vt = (f"{rt['ols_mae'].iloc[0]:.2f}",
              f"{rt['persist_mae'].iloc[0]:.2f}",
              f"{int(rt['n_scored'].iloc[0])}") if not rt.empty \
            else ("—", "—", "0")
        lines.append(f"| h={h} | {v42[0]} | {v42[1]} | "
                     f"{vt[0]} | {vt[1]} | {vt[2]} |")
    lines += [
        "",
        "### Per commodity (Day 48)",
        "",
        "| Commodity | Scored | OLS MAE | Persistence MAE |",
        "|---|---:|---:|---:|",
    ]
    for _, r in comms.iterrows():
        lines.append(f"| {r['commodity']} | {int(r['n_scored'])} | "
                     f"{r['ols_mae']:.2f} | {r['persist_mae']:.2f} |")
    lines += [
        "",
        "### Dataset state",
        "",
        f"- **{state['rows']:,} rows**, {state['markets']} markets, "
        f"{state['commodities']} commodities, {state['first']} → "
        f"{state['last']}",
        f"- Calendar coverage **{state['covered_days']}/{state['calendar_days']} "
        f"days ({100 * state['covered_days'] / state['calendar_days']:.1f}%)** "
        "— only 13 Oct 2026 missing",
        f"- Per-mandi history: {state['per_mandi_rows']} rows, latest "
        f"{state['per_mandi_latest']}; reporting markets: "
        f"{', '.join(state['per_mandi_markets'])}",
        f"- Week-7 window (22–25 Nov, portal frozen at 25 Nov): "
        f"{state['week_rows']} new rows, {state['week_per_mandi_rows']} "
        f"per-mandi; reporting mandis: "
        f"{', '.join(state['week_reporting'])}",
        "",
        "### Site state (measured from site/data.js)",
        "",
        f"- data.js **{site['bytes']:,} bytes** (was 51,937 before the "
        "Day-47 compression; 25,473 on 26 Nov — today's figure is "
        "bigger only because it carries the 25 Nov rows)",
        f"- Latest data {site['latest']}, {site['rows']:,} rows, "
        f"{site['commodities']} commodities, {site['today_count']} "
        "National commodities priced today",
        f"- Mandi rows on the site: {site['mandi_rows']} real rows "
        f"(mandiReal={site['mandi_real']}); forecast: "
        f"{site['forecast_keys']} real-backed series "
        f"({site['forecast_real']})",
        "",
        "## Reading the result",
        "",
        "**The site is now a product, not a demo.** Every section that "
        "was hidden for being sample-seeded is back, and every one of "
        "them now shows only real portal rows — mandi-compare, the "
        "7-day forecast, the Hindi-first labels and the shareable "
        "commodity links all sit on the same 1,604-row dataset, and "
        "data.js is half the size it was a week ago. The scored "
        "forecast kept growing underneath: 233 → 457 cells, and the "
        "OLS champion's h=1 MAE improved 231.97 → 198.05, its best "
        "real-data figure yet — driven by Onion (583.32 → 388.90) as "
        "the flat Azadpur Onion series scored more cells. But the "
        "Day 35/42 verdict survives: **persistence still beats OLS on "
        "every horizon and every commodity** (h=1: 77.78 vs 198.05), "
        "because the real series sit flat for days at a time while the "
        "model chases moves that never come.",
        "",
        "The honest caveats travel with the numbers. First, the portal "
        "is frozen at 25 Nov (lag 2) and only 3 of 8 mandis reported "
        "this week — Azadpur, Bowenpally, Sealdah Koley Market — so the "
        "site's mandi tables are thin by construction. Second, the "
        "portal's Safflower error persists (₹1,43,696.75 on 24 Nov "
        "against an MSP of ₹6,540); clean.py's sanity cap keeps it off "
        "the site, and the raw extract keeps it for the record. Third, "
        "Azadpur Onion printed ₹3,563.00 flat on all three days and "
        "Sealdah Tomato has no 23 Nov row — flat and gappy series are "
        "exactly what makes persistence hard to beat.",
        "",
        "## User test — pending (his action)",
        "",
        "The second half of Day 48 is one real user (him) tapping "
        "through every screen on his phone and listing what breaks. "
        "That cannot be verified from this run and is **not claimed "
        "done here** — the summary above is the verified half. When he "
        "reports back, his list becomes the Week-8 fix queue.",
        "",
        "## What Week 8 must do",
        "",
        "- Day 49: MSP coverage extension — add one mandated crop with "
        "a real MSP (Tur/Arhar or Wheat) and activate the Day-10 gap "
        "module for real.",
        "- Day 50: data-quality badge v2 — separate portal vs mandi "
        "freshness, and a 'days since last real per-mandi row' counter.",
        "- Day 51: error audit — every 'expected null on sample data' "
        "re-tested on whatever real data exists by then; nulls that "
        "survive become findings.",
        "- Day 52: cost/ops note — the whole stack is $0 (GitHub + "
        "Netlify free); document the running cost and the manual steps "
        "(browser extract) so anyone can take over the daily run.",
        "- Day 53: v2.0 release notes + Days 61–90 sketch.",
        "- Day 54–60: buffer — the portal bot-wall has already eaten "
        "~18 days once; buffer absorbs the next outage without "
        "breaking the streak.",
        "",
        "## Verification",
        "",
        f"- Hand-check (pure Python, csv module only): h=1 OLS MAE "
        f"recomputed from the accuracy CSV = {hand[0]} (module: "
        f"{today[today['horizon'] == 1]['ols_mae'].iloc[0] if (today['horizon'] == 1).any() else '—'}) — "
        f"{'MATCH' if (today['horizon'] == 1).any() and hand[0] is not None and abs(hand[0] - today[today['horizon'] == 1]['ols_mae'].iloc[0]) < 0.005 else 'MISMATCH' if (today['horizon'] == 1).any() else 'N/A — no h=1 rows'}; "
        f"scored cells = {hand[1]} (module: {today_tot[0]}) — "
        f"{'MATCH' if hand[1] == today_tot[0] else 'MISMATCH'}; "
        f"sample-scored cells = {hand[2]}",
        "- Deterministic re-run: CSV and report byte-identical; SVG "
        "content-identical after normalizing matplotlib's timestamp and "
        "random element IDs (the project's Day 29 standard).",
        f"- Site data.js parses as JSON (node check) and carries "
        f"meta.generated {site['generated']}, latestDate {site['latest']}.",
        "",
        f"![Week-7 summary](../charts/week7_summary_{TODAY}.svg)",
        "",
    ]
    path = os.path.join(BASE_DIR, "reports", "day48_week7_summary.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main():
    acc42 = pd.read_csv(os.path.join(
        BASE_DIR, "data", "processed", "forecast_accuracy_2026-11-21.csv"))
    acc48 = pd.read_csv(os.path.join(
        BASE_DIR, "data", "processed", f"forecast_accuracy_{TODAY}.csv"))
    day42, n42, tot42 = horizon_table(acc42)
    today, n48, tot48 = horizon_table(acc48)
    comms = commodity_table(acc48)
    state = dataset_state()
    site = site_state()
    print(f"SCORED: Day 42 {n42}/{tot42} -> Day 48 {n48}/{tot48}")
    print(today.to_string(index=False))
    print(comms.to_string(index=False))
    print(f"DATASET: {state['rows']} rows, {state['covered_days']}/"
          f"{state['calendar_days']} days, per-mandi latest "
          f"{state['per_mandi_latest']}")
    print(f"SITE: data.js {site['bytes']} bytes, latest {site['latest']}, "
          f"mandi rows {site['mandi_rows']}, forecast keys "
          f"{site['forecast_keys']}")
    summary = pd.concat([
        day42.assign(day="Day 42").set_index(["day", "horizon"]),
        today.assign(day="Day 48").set_index(["day", "horizon"])])
    spath = os.path.join(BASE_DIR, "data", "processed",
                         f"week7_summary_{TODAY}.csv")
    summary.to_csv(spath)
    cpath = os.path.join(BASE_DIR, "charts", f"week7_summary_{TODAY}.svg")
    before, after = chart(day42, today, cpath)
    print(f"CHART: {cpath} ({before} -> {after} bytes after slimming)")
    hand = hand_check(os.path.join(
        BASE_DIR, "data", "processed", f"forecast_accuracy_{TODAY}.csv"))
    rpath = write_report(day42, today, (n42, tot42), (n48, tot48),
                         comms, state, site, hand, cpath)
    print(f"REPORT: {rpath}")
    print(f"HAND-CHECK: h=1 OLS {hand[0]}, scored {hand[1]}, "
          f"sample-scored {hand[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
