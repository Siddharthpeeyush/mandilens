#!/usr/bin/env python3
"""Day 13: animated price-trend chart.

Reads : data/processed/mandi_prices_clean.csv
Writes: charts/price_trend_animated_YYYY-MM-DD.svg

The chart is a pure-SMIL animated SVG (no JavaScript, no binaries), so it
renders animated in any modern browser and pushes through the GitHub
push_files API like every other text chart. Three lines (Onion / Potato /
Tomato, 14-day median modal price) draw themselves over an 8-second loop, with
a travelling dot on each line, a sweeping playhead cursor, and a date readout
that tracks the playhead.
"""
import math
import os
import sys
from xml.sax.saxutils import escape

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, "data", "processed",
                         "mandi_prices_clean.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")

FOCUS = ["Onion", "Potato", "Tomato"]
COLORS = {"Onion": "#c0392b", "Potato": "#b7950b", "Tomato": "#e74c3c"}

WIDTH, HEIGHT = 960, 540
MARGIN = {"left": 74, "right": 36, "top": 64, "bottom": 76}
PLOT_W = WIDTH - MARGIN["left"] - MARGIN["right"]
PLOT_H = HEIGHT - MARGIN["top"] - MARGIN["bottom"]
DUR = 8.0  # seconds per loop


def path_d(points):
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def path_length(points):
    return sum(math.hypot(x2 - x1, y2 - y1)
               for (x1, y1), (x2, y2) in zip(points, points[1:]))


SOURCE_LABEL = {
    "portal": "Source: Agmarknet portal tables (govt. published)",
    "api": "Source: data.gov.in Agmarknet feed",
    "sample": "Source: seeded MandiLens feed",
}


def main():
    if not os.path.exists(PROCESSED):
        print("ANIMATE: no processed data", file=sys.stderr)
        return 1
    df = pd.read_csv(PROCESSED, parse_dates=["arrival_date"])
    trend = (df[df["commodity"].isin(FOCUS)]
             .groupby(["arrival_date", "commodity"])["modal_price"]
             .median().unstack())
    trend = trend.tail(14)
    dates = list(trend.index)
    n = len(dates)
    if n < 2:
        print("ANIMATE: need >= 2 dates", file=sys.stderr)
        return 1
    date_s = (sys.argv[1] if len(sys.argv) > 1
              else pd.Timestamp(dates[-1]).strftime("%Y-%m-%d"))
    source = sys.argv[2] if len(sys.argv) > 2 else "sample"

    lo = float(trend.min().min())
    hi = float(trend.max().max())
    pad = (hi - lo) * 0.12 or 1.0
    lo, hi = lo - pad, hi + pad

    def X(i):
        return MARGIN["left"] + i * PLOT_W / (n - 1)

    def Y(v):
        return MARGIN["top"] + PLOT_H * (1 - (v - lo) / (hi - lo))

    series = {}
    for comm in FOCUS:
        if comm in trend.columns:
            vals = trend[comm].tolist()
            series[comm] = [(X(i), Y(v)) for i, v in enumerate(vals)]

    parts = []
    a = parts.append
    a('<?xml version="1.0" encoding="utf-8"?>')
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
      f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
      f'font-family="DejaVu Sans, Arial, sans-serif">')
    a('<rect x="0" y="0" width="960" height="540" fill="#ffffff"/>')
    a('<text x="480" y="30" text-anchor="middle" font-size="18" '
      'font-weight="bold" fill="#2c3e50">MandiLens — animated price trends</text>')
    a('<text x="480" y="52" text-anchor="middle" font-size="12" fill="#7f8c8d">'
      'Median modal price across tracked mandis (Rs/quintal) · 14-day window</text>')

    # Gridlines + y ticks
    for k in range(6):
        v = lo + (hi - lo) * k / 5
        y = Y(v)
        a(f'<line x1="{MARGIN["left"]}" y1="{y:.1f}" '
          f'x2="{WIDTH - MARGIN["right"]}" y2="{y:.1f}" stroke="#ecf0f1"/>')
        a(f'<text x="{MARGIN["left"] - 10}" y="{y + 4:.1f}" text-anchor="end" '
          f'font-size="11" fill="#7f8c8d">{v:,.0f}</text>')

    # x ticks (every 2nd date)
    for i, d in enumerate(dates):
        if i % 2 == 0:
            x = X(i)
            lab = pd.Timestamp(d).strftime("%d %b")
            a(f'<text x="{x:.1f}" y="{HEIGHT - MARGIN["bottom"] + 22}" '
              f'text-anchor="middle" font-size="11" fill="#7f8c8d">{lab}</text>')
            a(f'<line x1="{x:.1f}" y1="{HEIGHT - MARGIN["bottom"]}" '
              f'x2="{x:.1f}" y2="{HEIGHT - MARGIN["bottom"] + 6}" stroke="#7f8c8d"/>')

    a(f'<line x1="{MARGIN["left"]}" y1="{HEIGHT - MARGIN["bottom"]}" '
      f'x2="{WIDTH - MARGIN["right"]}" y2="{HEIGHT - MARGIN["bottom"]}" stroke="#2c3e50"/>')

    # Animated lines + travelling dots
    for j, comm in enumerate(FOCUS):
        if comm not in series:
            continue
        pts = series[comm]
        d = escape(path_d(pts))
        L = path_length(pts)
        begin = f"{j * 0.5:.1f}s"
        dur = f"{DUR - j * 0.5:.1f}s"
        a(f'<path d="{d}" fill="none" stroke="{COLORS[comm]}" stroke-width="2.5" '
          f'stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}">'
          f'<animate attributeName="stroke-dashoffset" from="{L:.1f}" to="0" '
          f'dur="{dur}" begin="{begin}" fill="freeze" repeatCount="indefinite"/>'
          f'</path>')
        a(f'<circle r="6" fill="{COLORS[comm]}" opacity="0.95">'
          f'<animateMotion dur="{dur}" begin="{begin}" fill="freeze" '
          f'repeatCount="indefinite" path="{d}"/>'
          f'</circle>')

    # Sweeping playhead cursor
    x0 = X(0)
    x1 = X(n - 1)
    a(f'<line x1="{x0:.1f}" y1="{MARGIN["top"]}" x2="{x0:.1f}" '
      f'y2="{HEIGHT - MARGIN["bottom"]}" stroke="#2c3e50" stroke-width="1" '
      f'stroke-dasharray="4,3" opacity="0.55">'
      f'<animate attributeName="x1" from="{x0:.1f}" to="{x1:.1f}" dur="{DUR}s" '
      f'fill="freeze" repeatCount="indefinite"/>'
      f'<animate attributeName="x2" from="{x0:.1f}" to="{x1:.1f}" dur="{DUR}s" '
      f'fill="freeze" repeatCount="indefinite"/>'
      f'</line>')

    # Date readout that tracks the playhead (one <set> per segment)
    seg = DUR / (n - 1)
    sets = []
    for i, d in enumerate(dates):
        lab = escape(pd.Timestamp(d).strftime("%d %b %Y"))
        begin = i * seg
        sets.append(f'<set attributeName="textContent" to="{lab}" '
                    f'begin="{begin:.2f}s" dur="{seg:.2f}s" '
                    f'repeatCount="indefinite"/>')
    first_lab = escape(pd.Timestamp(dates[0]).strftime("%d %b %Y"))
    a(f'<text x="{WIDTH - MARGIN["right"]}" y="{MARGIN["top"] - 12}" '
      f'text-anchor="end" font-size="14" font-weight="bold" fill="#2c3e50">'
      f'{first_lab}{"".join(sets)}</text>')

    # Legend
    lx = MARGIN["left"] + 8
    ly = MARGIN["top"] + 8
    for j, comm in enumerate(FOCUS):
        if comm not in series:
            continue
        yy = ly + j * 22
        a(f'<rect x="{lx}" y="{yy - 10}" width="26" height="10" '
          f'fill="{COLORS[comm]}"/>')
        a(f'<text x="{lx + 32}" y="{yy}" font-size="12" fill="#2c3e50">{comm}</text>')

    a('<text x="480" y="528" text-anchor="middle" font-size="11" fill="#95a5a6">'
      f'{escape(SOURCE_LABEL.get(source, SOURCE_LABEL["sample"]))} · loops every 8s</text>')
    a('</svg>')

    os.makedirs(CHARTS_DIR, exist_ok=True)
    out = os.path.join(CHARTS_DIR, f"price_trend_animated_{date_s}.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"ANIMATE: {out} ({os.path.getsize(out)} bytes, "
          f"{len(series)} series, {n} dates, {DUR:.0f}s loop)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
