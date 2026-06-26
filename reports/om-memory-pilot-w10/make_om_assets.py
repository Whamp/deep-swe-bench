#!/usr/bin/env python3
"""Generate deterministic OM DeepSWE report/social assets from paired_manifest.json."""
from __future__ import annotations

import html
import json
import math
import statistics as st
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "paired_manifest.json"
ASSETS = HERE
W = H = 1254
BLUE = "#2d2af4"
PURPLE = "#6b4cff"
BLACK = "#090909"
TEXT = "#11131a"
MUTED = "#4a4d57"
GRID = "#c9c9c9"
PAPER = "#fbfaf6"
BG = "#2d2af4"
GREEN = "#0b8f5a"
RED = "#d3412f"
ORANGE = "#d08a00"
GRAY = "#888b94"


def load_rows():
    return json.loads(MANIFEST.read_text())["rows"]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0


def median(xs):
    return st.median(xs) if xs else 0


def pct(x):
    return f"{100*x:.1f}%"


def esc(s):
    return html.escape(str(s), quote=True)


def text(x, y, s, size=24, fill=TEXT, anchor="start", weight="600", family="monospace", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="{family}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'


def tspans(x, y, lines, size=24, fill=TEXT, anchor="start", weight="600", family="monospace", line_h=1.25):
    out = [f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="{family}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">']
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else size * line_h
        out.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    out.append('</text>')
    return ''.join(out)


def card_start(title, subtitle):
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    svg.append('<defs>')
    svg.append('<pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r="0.65" fill="#ece8dc" opacity="0.65"/></pattern>')
    svg.append('<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="20" flood-color="#111" flood-opacity="0.18"/></filter>')
    svg.append(f'<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 Z" fill="{BLUE}"/></marker>')
    svg.append('</defs>')
    svg.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    svg.append(f'<rect x="58" y="58" width="1138" height="1138" rx="42" fill="{PAPER}" filter="url(#shadow)"/>')
    svg.append('<rect x="58" y="58" width="1138" height="1138" rx="42" fill="url(#dots)" opacity="0.82"/>')
    svg.append(text(105, 145, title, 52, BLACK, "start", "800", "Georgia,serif"))
    svg.append(text(108, 190, subtitle, 24, MUTED, "start", "700", "monospace"))
    return svg


def card_end(svg, foot="DeepSWE · pi-observational-memory vs baseline · 113 paired tasks · thinking: high"):
    svg.append(f'<line x1="105" y1="1130" x2="1149" y2="1130" stroke="{BLACK}" stroke-width="2" opacity="0.16"/>')
    svg.append(text(108, 1168, foot, 20, MUTED, "start", "700", "monospace"))
    svg.append('</svg>')
    return '\n'.join(svg) + '\n'


def render(name, svg):
    sp = ASSETS / f"{name}.svg"
    pp = ASSETS / f"{name}.png"
    sp.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), str(sp), "-o", str(pp)], check=True)
    return pp


def metric_summary(rows):
    bpart = [r["baseline"]["reward_partial"] for r in rows]
    opart = [r["om"]["reward_partial"] for r in rows]
    return {
        "n": len(rows),
        "baseline_mean": mean(bpart),
        "om_mean": mean(opart),
        "mean_delta": mean([r["delta"]["partial"] for r in rows]),
        "baseline_solves": sum(r["baseline"]["reward_binary"] == 1 for r in rows),
        "om_solves": sum(r["om"]["reward_binary"] == 1 for r in rows),
        "improved": sum(r["delta"]["partial"] > 0 for r in rows),
        "worse": sum(r["delta"]["partial"] < 0 for r in rows),
        "tie": sum(r["delta"]["partial"] == 0 for r in rows),
        "median_tokens_b": median([r["baseline"]["total_tokens"] for r in rows]),
        "median_tokens_o": median([r["om"]["total_tokens"] for r in rows]),
        "median_cost_b": median([r["baseline"]["cost_usd"] for r in rows]),
        "median_cost_o": median([r["om"]["cost_usd"] for r in rows]),
        "median_wall_b": median([r["baseline"]["agent_wall_s"] for r in rows]),
        "median_wall_o": median([r["om"]["agent_wall_s"] for r in rows]),
    }


def difficulty_card(rows):
    buckets = ["hard", "medium", "easy"]
    data = []
    for b in buckets:
        rs = [r for r in rows if r["difficulty_bucket"] == b]
        data.append({
            "bucket": b.upper(), "n": len(rs),
            "b": mean([r["baseline"]["reward_partial"] for r in rs]) * 100,
            "o": mean([r["om"]["reward_partial"] for r in rs]) * 100,
            "bs": sum(r["baseline"]["reward_binary"] == 1 for r in rs),
            "os": sum(r["om"]["reward_binary"] == 1 for r in rs),
            "iw": (sum(r["delta"]["partial"] > 0 for r in rs), sum(r["delta"]["partial"] < 0 for r in rs), sum(r["delta"]["partial"] == 0 for r in rs)),
        })
    svg = card_start("Memory helped hard tasks", "Mean partial reward by baseline difficulty tercile")
    x0, x1, y0, y1 = 210, 1105, 300, 910
    def Y(v): return y1 - (v / 100) * (y1 - y0)
    for p in range(0, 101, 20):
        y = Y(p)
        svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.3" stroke-dasharray="2 5"/>')
        svg.append(text(x0 - 18, y + 8, f"{p}%", 24, MUTED, "end", "600"))
    svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
    svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
    svg.append(text(125, 610, "PARTIAL REWARD ↑", 23, MUTED, "middle", "800", "monospace", 'transform="rotate(-90 125 610)"'))
    group_w = (x1 - x0) / 3
    bar_w = 82
    for i, d in enumerate(data):
        cx = x0 + group_w * (i + 0.5)
        for j, key in enumerate(["b", "o"]):
            val = d[key]; color = BLACK if key == "b" else BLUE
            x = cx + (-bar_w - 8 if key == "b" else 8)
            y = Y(val)
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{y1-y:.1f}" rx="9" fill="{color}" opacity="0.92"/>')
            svg.append(text(x + bar_w/2, y - 14, f"{val:.1f}%", 25, color, "middle", "800"))
        svg.append(text(cx, y1 + 50, d["bucket"], 36, BLACK, "middle", "800", "Georgia,serif"))
        svg.append(text(cx, y1 + 84, f"n={d['n']} · solves {d['bs']}→{d['os']}", 21, MUTED, "middle", "700"))
        svg.append(text(cx, y1 + 112, f"win/loss/tie {d['iw'][0]}/{d['iw'][1]}/{d['iw'][2]}", 19, MUTED, "middle", "600"))
    svg.append(f'<circle cx="870" cy="255" r="9" fill="{BLACK}"/><text x="890" y="263" font-size="22" font-family="monospace" font-weight="700" fill="{TEXT}">baseline</text>')
    svg.append(f'<circle cx="1010" cy="255" r="9" fill="{BLUE}"/><text x="1030" y="263" font-size="22" font-family="monospace" font-weight="700" fill="{TEXT}">OM</text>')
    return render("difficulty-bucket-card", card_end(svg))


def scatter_card(rows):
    svg = card_start("Baseline vs memory", "Each dot is one DeepSWE task · above line = OM improved")
    x0, x1, y0, y1 = 210, 1090, 300, 985
    def X(v): return x0 + v * (x1 - x0)
    def Y(v): return y1 - v * (y1 - y0)
    for p in [0, .25, .5, .75, 1.0]:
        x, y = X(p), Y(p)
        svg.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="2 5"/>')
        svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="2 5"/>')
        svg.append(text(x, y1 + 36, f"{int(p*100)}%", 22, MUTED, "middle", "600"))
        svg.append(text(x0 - 14, y + 8, f"{int(p*100)}%", 22, MUTED, "end", "600"))
    svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y0}" stroke="{BLACK}" stroke-width="3" opacity="0.35"/>')
    svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
    svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
    colors = {"hard": BLUE, "medium": PURPLE, "easy": BLACK}
    for r in rows:
        x, y = X(r["baseline"]["reward_partial"]), Y(r["om"]["reward_partial"])
        color = colors[r["difficulty_bucket"]]
        opacity = .78 if abs(r["delta"]["partial"]) > .05 else .34
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" opacity="{opacity}"/>')
    labels = [
        ("mashumaro", "mashumaro-flattened-dataclass-fields", 26, -30, "start"),
        ("fastapi HEAD", "fastapi-implicit-head-options", 26, 14, "start"),
        ("adaptix", "adaptix-name-mapping-aliases", -18, 24, "end"),
        ("cattrs", "cattrs-partial-structuring-recovery", -18, -16, "end"),
        ("kgateway", "kgateway-consistent-hash-policy", 26, 56, "start"),
    ]
    bytask = {r["task"]: r for r in rows}
    for lab, task, dx, dy, anchor in labels:
        r = bytask[task]
        svg.append(text(X(r["baseline"]["reward_partial"])+dx, Y(r["om"]["reward_partial"])+dy, lab, 21, TEXT, anchor, "800"))
    svg.append(text((x0+x1)/2, y1 + 80, "BASELINE PARTIAL REWARD →", 24, MUTED, "middle", "800"))
    svg.append(text(118, 650, "OM PARTIAL REWARD ↑", 24, MUTED, "middle", "800", "monospace", 'transform="rotate(-90 118 650)"'))
    svg.append(text(850, 1070, "hard", 22, BLUE, "start", "800")); svg.append(text(930, 1070, "medium", 22, PURPLE, "start", "800")); svg.append(text(1050, 1070, "easy", 22, BLACK, "start", "800"))
    return render("baseline-vs-om-scatter-card", card_end(svg))


def tradeoff_card(rows):
    svg = card_start("Quality vs search cost", "Δpartial reward vs Δtokens · right side used more main-session tokens")
    x0, x1, y0, y1 = 205, 1100, 300, 960
    xs = [r["delta"]["tokens"] / 1_000_000 for r in rows]
    ys = [r["delta"]["partial"] for r in rows]
    xmin, xmax = -22, 38
    ymin, ymax = -1.05, 1.05
    def X(v): return x0 + (v - xmin) / (xmax - xmin) * (x1 - x0)
    def Y(v): return y1 - (v - ymin) / (ymax - ymin) * (y1 - y0)
    for xt in [-20, -10, 0, 10, 20, 30]:
        x = X(xt); svg.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="2 5"/>'); svg.append(text(x, y1+35, f"{xt}M", 21, MUTED, "middle", "600"))
    for yt in [-1, -.5, 0, .5, 1]:
        y = Y(yt); svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="2 5"/>'); svg.append(text(x0-14, y+8, f"{yt:+.1f}", 21, MUTED, "end", "600"))
    svg.append(f'<line x1="{X(0):.1f}" y1="{y0}" x2="{X(0):.1f}" y2="{y1}" stroke="{BLACK}" stroke-width="3" opacity="0.45"/>')
    svg.append(f'<line x1="{x0}" y1="{Y(0):.1f}" x2="{x1}" y2="{Y(0):.1f}" stroke="{BLACK}" stroke-width="3" opacity="0.45"/>')
    for r in rows:
        x, y = X(r["delta"]["tokens"] / 1_000_000), Y(r["delta"]["partial"])
        color = GREEN if r["delta"]["partial"] > .05 else RED if r["delta"]["partial"] < -.05 else GRAY
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" opacity="0.72"/>')
    bytask = {r["task"]: r for r in rows}
    for lab, task, dx, dy in [("fastapi", "fastapi-implicit-head-options", 14, -12), ("koota pair", "koota-pair-relation-tracking", -10, -18), ("adaptix", "adaptix-name-mapping-aliases", 10, 22), ("ts-pattern", "ts-pattern-match-each", 12, -16), ("pebble", "pebble-durability-wait-apis", -12, -16)]:
        r = bytask[task]
        anchor = "end" if dx < 0 else "start"
        svg.append(text(X(r["delta"]["tokens"]/1_000_000)+dx, Y(r["delta"]["partial"])+dy, lab, 21, TEXT, anchor, "800"))
    svg.append(text((x0+x1)/2, y1+78, "Δ TOKENS (M) → MORE MAIN-SESSION TOKENS", 23, MUTED, "middle", "800"))
    svg.append(text(115, 650, "Δ PARTIAL REWARD ↑", 23, MUTED, "middle", "800", "monospace", 'transform="rotate(-90 115 650)"'))
    return render("quality-vs-token-tradeoff-card", card_end(svg))


def success_modes_card(rows):
    data = [
        ("New full solves", "8", "baseline not solved → OM solved"),
        ("Baseline pathology rescues", "4/5", "empty/pathological baselines became real patches"),
        ("Hard-task partial jumps", "26", "hard rows improved by > 0.05 partial"),
        ("Cheap / efficient wins", "13", "wins or ties with fewer tokens + tool calls"),
        ("Integration-completeness wins", "7", "cross-layer fixture/golden/API repairs"),
    ]
    svg = card_start("Where memory helped", "Success modes from the OM DeepSWE run")
    y = 285
    for i, (name, count, desc) in enumerate(data):
        h = 135; x = 130
        svg.append(f'<rect x="{x}" y="{y}" width="995" height="{h}" rx="24" fill="#ffffff" opacity="0.72" stroke="{BLACK}" stroke-opacity="0.10"/>')
        svg.append(text(x+55, y+83, count, 56, BLUE, "start", "900", "Georgia,serif"))
        svg.append(text(x+220, y+58, name, 32, BLACK, "start", "800", "Georgia,serif"))
        svg.append(text(x+220, y+95, desc, 22, MUTED, "start", "700"))
        y += h + 24
    svg.append(text(140, 1065, "Main pattern: memory helped the model finish the adjacent seams.", 26, BLACK, "start", "800", "Georgia,serif"))
    return render("success-modes-card", card_end(svg))


def regression_modes_card(rows):
    data = [
        ("Memory distraction / over-expansion", "6", "broadened into nearby plumbing without closing the contract"),
        ("Normal model variance", "4", "same surface, hidden edge case still failed"),
        ("API / extension seam missed", "3", "public export or extension contract broke"),
        ("Missed integration", "3", "companion/shared file skipped"),
        ("Stalled / empty patch", "1", "search never turned into a diff"),
        ("Tooling/env", "1", "xauth missing; not model reasoning"),
    ]
    svg = card_start("Where memory hurt", "18 largest regressions · buckets are analyst-classified")
    y = 280
    max_count = 6
    for name, count, desc in data:
        c = int(count); x = 145; bar_w = 530 * c / max_count
        svg.append(text(x, y+14, name, 27, BLACK, "start", "800", "Georgia,serif"))
        svg.append(f'<rect x="{x}" y="{y+38}" width="530" height="34" rx="12" fill="#e7e2d7"/>')
        svg.append(f'<rect x="{x}" y="{y+38}" width="{bar_w:.1f}" height="34" rx="12" fill="{RED if c>=3 else ORANGE}" opacity="0.9"/>')
        svg.append(text(x+560, y+66, count, 34, RED if c>=3 else ORANGE, "start", "900"))
        svg.append(text(x, y+103, desc, 20, MUTED, "start", "650"))
        y += 128
    svg.append(text(145, 1080, "Biggest risk: remembering the wrong layer or missing the public seam.", 25, BLACK, "start", "800", "Georgia,serif"))
    return render("regression-modes-card", card_end(svg))


def waterfall_card(rows):
    ordered = sorted(rows, key=lambda r: r["delta"]["partial"], reverse=True)
    svg = card_start("Task-level lift", "Δpartial reward sorted by task · blue wins, red losses")
    x0, x1, y0, y1 = 150, 1110, 300, 980
    ymin, ymax = -1.05, 1.05
    def X(i): return x0 + i / (len(ordered)-1) * (x1-x0)
    def Y(v): return y1 - (v-ymin)/(ymax-ymin)*(y1-y0)
    for yt in [-1, -.5, 0, .5, 1]:
        y=Y(yt); svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.2" stroke-dasharray="2 5"/>'); svg.append(text(x0-12,y+8,f"{yt:+.1f}",21,MUTED,"end","600"))
    svg.append(f'<line x1="{x0}" y1="{Y(0):.1f}" x2="{x1}" y2="{Y(0):.1f}" stroke="{BLACK}" stroke-width="3" opacity="0.55"/>')
    for i,r in enumerate(ordered):
        x=X(i); y=Y(r["delta"]["partial"]); color=BLUE if r["delta"]["partial"]>0 else RED if r["delta"]["partial"]<0 else GRAY
        svg.append(f'<line x1="{x:.1f}" y1="{Y(0):.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="3" opacity="0.62"/>')
        if abs(r["delta"]["partial"])>.5:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}"/>')
    for lab, idx, dy, anchor in [("mashumaro",0,-14,"start"),("fastapi",1,24,"start"),("adaptix",112,24,"end"),("cattrs",111,-14,"end")]:
        r=ordered[idx]; svg.append(text(X(idx)+(10 if anchor=='start' else -10), Y(r["delta"]["partial"])+dy, lab, 21, TEXT, anchor, "800"))
    svg.append(text(630, 1040, "69 improved · 33 worse · 11 tied", 30, BLACK, "middle", "800", "Georgia,serif"))
    svg.append(text(630, 1078, "sorted from biggest OM gain to biggest OM loss", 21, MUTED, "middle", "700"))
    return render("partial-delta-waterfall-card", card_end(svg))


def readme_card(rows):
    m = metric_summary(rows)
    W2, H2 = 1672, 941
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W2}" height="{H2}" viewBox="0 0 {W2} {H2}">']
    svg.append(f'<rect width="{W2}" height="{H2}" fill="#ffffff"/>')
    svg.append(text(70, 95, "pi-observational-memory on DeepSWE", 46, BLACK, "start", "800", "Georgia,serif"))
    svg.append(text(72, 138, "DeepSeek V4 Flash · Pi agent · 113 paired tasks · baseline reused", 23, MUTED, "start", "700"))
    rowspec = [
        ("partial reward ↑", m["baseline_mean"], m["om_mean"], f"{m['baseline_mean']:.3f}", f"{m['om_mean']:.3f}", True),
        ("full solves ↑", m["baseline_solves"], m["om_solves"], f"{m['baseline_solves']}/113", f"{m['om_solves']}/113", True),
        ("median tokens ↓", m["median_tokens_b"], m["median_tokens_o"], f"{m['median_tokens_b']/1e6:.2f}M", f"{m['median_tokens_o']/1e6:.2f}M", False),
        ("median cost ↓", m["median_cost_b"], m["median_cost_o"], f"${m['median_cost_b']:.3f}", f"${m['median_cost_o']:.3f}", False),
        ("median wall ↓", m["median_wall_b"], m["median_wall_o"], f"{m['median_wall_b']:.0f}s", f"{m['median_wall_o']:.0f}s", False),
    ]
    x_label, x_base, x_om, x_bar = 90, 470, 650, 865
    y = 235
    svg.append(text(x_label, 190, "metric", 22, MUTED, "start", "800"))
    svg.append(text(x_base, 190, "baseline", 22, MUTED, "start", "800"))
    svg.append(text(x_om, 190, "OM", 22, MUTED, "start", "800"))
    svg.append(text(x_bar, 190, "relative bar (baseline = 100%; capped)", 22, MUTED, "start", "800"))
    for name,b,o,bs,os,higher_good in rowspec:
        ratio = o / b if b else (5 if o else 1)
        ratio = min(ratio, 5.0)
        svg.append(f'<rect x="60" y="{y-38}" width="1548" height="94" rx="18" fill="#f7f7f7"/>')
        svg.append(text(x_label, y+2, name, 26, BLACK, "start", "800"))
        svg.append(text(x_base, y+2, bs, 25, BLACK, "start", "700"))
        svg.append(text(x_om, y+2, os, 25, BLUE, "start", "800"))
        bx = x_bar; by = y-22; bw = 245; maxw = 520; bh = 26
        ow = min(maxw, bw * ratio)
        svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="8" fill="#d8d8d8"/>')
        svg.append(f'<rect x="{bx}" y="{by+36}" width="{ow:.1f}" height="{bh}" rx="8" fill="{BLUE}"/>')
        if bw * ratio > maxw:
            svg.append(text(bx + maxw + 14, by + 58, "›", 30, BLUE, "start", "900"))
        change = (o/b-1)*100 if b else 400
        color = GREEN if (change>0)==higher_good else RED
        svg.append(text(bx + 620, y+18, f"{change:+.1f}%", 27, color, "end", "900"))
        y += 118
    svg.append(text(70, 850, "Outcome ↑ improved; resource columns ↓ got worse. Agent-side metrics only: OM worker cost is not included.", 22, MUTED, "start", "700"))
    svg.append(text(70, 878, "Bars are capped for layout; exact deltas are printed at right.", 19, MUTED, "start", "650"))
    svg.append(text(70, 912, "Source: reports/om-memory-pilot-w10/paired_manifest.json", 20, MUTED, "start", "650"))
    svg.append('</svg>')
    sp = ASSETS / "readme-style-benchmark-card.svg"; pp = ASSETS / "readme-style-benchmark-card.png"
    sp.write_text('\n'.join(svg)+'\n')
    subprocess.run(["rsvg-convert", "-w", str(W2), "-h", str(H2), str(sp), "-o", str(pp)], check=True)
    return pp


def write_readme(paths):
    md = ["# pi-observational-memory DeepSWE report assets", "", "Deterministic assets generated from `paired_manifest.json`.", "", "## Assets", ""]
    for p in paths:
        md.append(f"- `{p.name}`")
    md += ["", "## Recreate", "", "```bash", "cd reports/om-memory-pilot-w10", "python3 make_om_assets.py", "```", "", "Caveats: one rep, reused baseline, and OM worker model-call cost is not included in the main-session token/cost columns.", ""]
    (HERE / "README.md").write_text('\n'.join(md))


def main():
    rows = load_rows()
    paths = [
        difficulty_card(rows),
        scatter_card(rows),
        waterfall_card(rows),
        tradeoff_card(rows),
        success_modes_card(rows),
        regression_modes_card(rows),
        readme_card(rows),
    ]
    write_readme(paths)
    print('\n'.join(str(p) for p in paths))


if __name__ == "__main__":
    main()
