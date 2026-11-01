#!/usr/bin/env python3
"""Draws the GitHub contribution calendar as a dark SVG in the profile's blue.

Usage: GITHUB_TOKEN=... python3 contrib_graph.py <user> <out.svg>
"""
import json
import os
import sys
import urllib.request
from datetime import date

USER = sys.argv[1] if len(sys.argv) > 1 else "Verisonder"
OUT = sys.argv[2] if len(sys.argv) > 2 else "contrib.svg"

# Empty cell, then four levels up to the profile blue (#379ED6).
LEVELS = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0d3550",
    "SECOND_QUARTILE": "#155b86",
    "THIRD_QUARTILE": "#2380bd",
    "FOURTH_QUARTILE": "#46b4f0",
}
TEXT = "#8b949e"
CELL, GAP = 11, 3
STEP = CELL + GAP
LEFT, TOP = 34, 40

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}
"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "bearer " + token, "Content-Type": "application/json", "User-Agent": "contrib-graph"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def draw(cal):
    weeks = cal["weeks"]
    width = LEFT + len(weeks) * STEP + 4
    height = TOP + 7 * STEP + 34
    font = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"'
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" {font}>',
        f'<text x="{LEFT}" y="14" fill="#e6edf3" font-size="13">{cal["totalContributions"]:,} contributions in the last year</text>',
    ]
    # Month names above the first column of each month.
    last_month = None
    for i, w in enumerate(weeks):
        d = date.fromisoformat(w["contributionDays"][0]["date"])
        if d.month != last_month:
            if last_month is not None or d.day <= 7:
                if i < len(weeks) - 2:
                    out.append(f'<text x="{LEFT + i * STEP}" y="{TOP - 8}" fill="{TEXT}" font-size="10">{d.strftime("%b")}</text>')
            last_month = d.month
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="0" y="{TOP + row * STEP + 9}" fill="{TEXT}" font-size="10">{label}</text>')
    for i, w in enumerate(weeks):
        for d in w["contributionDays"]:
            n = d["contributionCount"]
            tip = f'{n} contribution{"" if n == 1 else "s"} on {d["date"]}'
            out.append(
                f'<rect x="{LEFT + i * STEP}" y="{TOP + d["weekday"] * STEP}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{LEVELS.get(d["contributionLevel"], LEVELS["NONE"])}"><title>{esc(tip)}</title></rect>'
            )
    # Legend: Less ■■■■■ More
    lx = width - 4 - 5 * STEP - 34
    ly = TOP + 7 * STEP + 14
    out.append(f'<text x="{lx - 28}" y="{ly + 9}" fill="{TEXT}" font-size="10">Less</text>')
    for k, color in enumerate(LEVELS.values()):
        out.append(f'<rect x="{lx + k * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    out.append(f'<text x="{lx + 5 * STEP + 4}" y="{ly + 9}" fill="{TEXT}" font-size="10">More</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    svg = draw(fetch())
    with open(OUT, "w") as f:
        f.write(svg)
    print("wrote", OUT)
