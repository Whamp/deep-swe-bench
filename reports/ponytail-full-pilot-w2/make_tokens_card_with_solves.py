#!/usr/bin/env python3
"""Create an additional Twitter card whose x-axis is mean tokens/task."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE / "cost-card.png"
SVG = HERE / "tokens-card-with-solves-overlay.svg"
OVERLAY = HERE / "tokens-card-with-solves-overlay.png"
OUT = HERE / "tokens-card-with-solves.png"

W = H = 1254
BLUE = "#2d2af4"
BLACK = "#090909"
GRID = "#c9c9c9"
TEXT = "#11131a"
MUTED = "#1b1f2b"
PAPER = "#fbfaf6"

cover = (86, 344, 1084, 744)
x0, x1 = 222, 1130
y0, y1 = 365, 1000

# Mean-by-difficulty data from baseline partial-reward terciles.
# x = mean total tokens per task, y = mean partial reward percentage.
points = {
    "EASY": {
        "baseline": (4.6936006, 99.1, "99.1% · 4.69M"),
        "pony": (4.0192206, 84.1, "84.1% · 4.02M"),
    },
    "MEDIUM": {
        "baseline": (3.7660596, 93.4, "93.4% · 3.77M"),
        "pony": (3.4641112, 85.9, "85.9% · 3.46M"),
    },
    "HARD": {
        "baseline": (3.7811604, 40.1, "40.1% · 3.78M"),
        "pony": (3.3369764, 43.1, "43.1% · 3.34M"),
    },
}

def X(tokens_m: float) -> float:
    return x0 + (tokens_m - 3.0) / (5.0 - 3.0) * (x1 - x0)

def Y(pct: float) -> float:
    return y1 - (pct - 30) / (100 - 30) * (y1 - y0)

def text(x, y, s, size=25, fill=TEXT, anchor="middle", weight="600", family="monospace", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="{family}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append('<defs>')
svg.append('<pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.55" fill="#ece8dc" opacity="0.55"/></pattern>')
svg.append(f'<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 Z" fill="{BLUE}"/></marker>')
svg.append('</defs>')

cx, cy, cw, ch = cover
svg.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="{PAPER}"/>')
svg.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="url(#dots)" opacity="0.8"/>')

for pct in [100, 90, 80, 70, 60, 50, 40, 30]:
    y = Y(pct)
    svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.5" stroke-dasharray="2 4" opacity="0.9"/>')
    svg.append(text(203, y + 8, f"{pct}%", 26, MUTED, "end", "500", "monospace"))
for tok in [3.0, 3.5, 4.0, 4.5, 5.0]:
    x = X(tok)
    svg.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{GRID}" stroke-width="1.5" stroke-dasharray="2 4" opacity="0.9"/>')
    svg.append(text(x, 1034, f"{tok:.1f}M", 26, MUTED, "middle", "500", "monospace"))
svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')

svg.append(text(112, 685, "PARTIAL REWARD · → BETTER", 24, MUTED, "middle", "700", "monospace", 'transform="rotate(-90 112 685)"'))
svg.append(text(676, 1067, "TOKENS · PER TASK → MORE TOKENS", 25, MUTED, "middle", "700", "monospace"))

svg.append(text(X(points["EASY"]["baseline"][0]) + 28, Y(points["EASY"]["baseline"][1]) + 48, "EASY", 38, BLACK, "start", "800", "Georgia,serif"))
svg.append(text(X(points["MEDIUM"]["pony"][0]), Y(points["MEDIUM"]["pony"][1]) + 96, "MEDIUM", 38, BLACK, "middle", "800", "Georgia,serif"))
svg.append(text(625, 975, "HARD", 38, BLACK, "middle", "800", "Georgia,serif"))

for tier, d in points.items():
    bx, by = X(d["baseline"][0]), Y(d["baseline"][1])
    px, py = X(d["pony"][0]), Y(d["pony"][1])
    dx, dy = px - bx, py - by
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    sx, sy = bx + ux * 20, by + uy * 20
    ex, ey = px - ux * 24, py - uy * 24
    svg.append(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{BLUE}" stroke-width="3.5" marker-end="url(#arrow)"/>')

for tier, d in points.items():
    bx, by = X(d["baseline"][0]), Y(d["baseline"][1])
    px, py = X(d["pony"][0]), Y(d["pony"][1])
    svg.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="11" fill="{BLACK}" stroke="{PAPER}" stroke-width="3"/>')
    svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="{BLUE}" stroke="{PAPER}" stroke-width="3"/>')

    if tier == "EASY":
        svg.append(text(bx - 18, by + 5, d["baseline"][2], 23, BLACK, "end", "700", "monospace"))
        svg.append(text(px + 22, py + 18, d["pony"][2], 23, BLUE, "start", "700", "monospace"))
    elif tier == "MEDIUM":
        svg.append(text(bx + 18, by + 6, d["baseline"][2], 23, BLACK, "start", "700", "monospace"))
        svg.append(text(px - 22, py + 8, d["pony"][2], 23, BLUE, "end", "700", "monospace"))
    else:
        svg.append(text(bx + 20, by - 18, d["baseline"][2], 23, BLACK, "start", "700", "monospace"))
        svg.append(text(px + 22, py - 18, d["pony"][2], 23, BLUE, "start", "700", "monospace"))


# Minimal inset: primary DeepSWE binary reward / full solves.
inset_x, inset_y, inset_w, inset_h = 835, 615, 245, 210
svg.append(f'<rect x="{inset_x}" y="{inset_y}" width="{inset_w}" height="{inset_h}" rx="16" fill="{PAPER}" opacity="0.82"/>')
svg.append(text(inset_x + inset_w / 2, inset_y + 18, "FULL SOLVES ↑", 22, MUTED, "middle", "800", "monospace"))
# Scale 0..4 solves to compact bars. Baseline=2, Ponytail=4.
bar_base_y = inset_y + 164
bar_w = 50
max_h = 100
baseline_h = max_h * 2 / 4
pony_h = max_h
base_x = inset_x + 58
pony_x = inset_x + 144
svg.append(f'<rect x="{base_x}" y="{bar_base_y - baseline_h:.1f}" width="{bar_w}" height="{baseline_h:.1f}" rx="5" fill="#090909" opacity="0.88"/>')
svg.append(f'<rect x="{pony_x}" y="{bar_base_y - pony_h:.1f}" width="{bar_w}" height="{pony_h:.1f}" rx="5" fill="{BLUE}"/>')
svg.append(text(base_x + bar_w / 2, bar_base_y - baseline_h - 12, "2", 30, BLACK, "middle", "800", "monospace"))
svg.append(text(pony_x + bar_w / 2, bar_base_y - pony_h - 12, "4", 30, BLUE, "middle", "800", "monospace"))
svg.append(text(base_x + bar_w / 2, bar_base_y + 28, "baseline", 17, MUTED, "middle", "700", "monospace"))
svg.append(text(pony_x + bar_w / 2, bar_base_y + 28, "ponytail", 17, BLUE, "middle", "700", "monospace"))

svg.append('</svg>')
SVG.write_text("\n".join(svg) + "\n")
subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), str(SVG), "-o", str(OVERLAY)], check=True)
subprocess.run(["magick", str(BASE), str(OVERLAY), "-composite", str(OUT)], check=True)
print(OUT)
