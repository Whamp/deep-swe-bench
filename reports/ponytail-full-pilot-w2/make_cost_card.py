#!/usr/bin/env python3
"""Replace the AI-generated chart region with an accurate SVG overlay."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = HERE / "cost-card.png"
SVG = HERE / "cost-card-overlay.svg"
OVERLAY = HERE / "cost-card-overlay.png"
OUT = HERE / "cost-card.png"

W = H = 1254
BLUE = "#2d2af4"
BLACK = "#090909"
GRID = "#c9c9c9"
TEXT = "#11131a"
MUTED = "#1b1f2b"
PAPER = "#fbfaf6"

# Global coordinates on the 1254x1254 card.
cover = (86, 344, 1084, 744)  # x, y, width, height
x0, x1 = 222, 1130
y0, y1 = 365, 1000

# Mean-by-difficulty data from baseline partial-reward terciles.
points = {
    "EASY": {
        "baseline": (0.1486, 99.1, "99.1% · $0.149"),
        "pony": (0.1526, 84.1, "84.1% · $0.153"),
    },
    "MEDIUM": {
        "baseline": (0.1590, 93.4, "93.4% · $0.159"),
        "pony": (0.1465, 85.9, "85.9% · $0.147"),
    },
    "HARD": {
        "baseline": (0.1432, 40.1, "40.1% · $0.143"),
        "pony": (0.1378, 43.1, "43.1% · $0.138"),
    },
}

def X(cost: float) -> float:
    return x0 + (cost - 0.13) / (0.16 - 0.13) * (x1 - x0)

def Y(pct: float) -> float:
    return y1 - (pct - 30) / (100 - 30) * (y1 - y0)

def text(x, y, s, size=25, fill=TEXT, anchor="middle", weight="600", family="monospace", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-family="{family}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>'

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append('<defs>')
svg.append('<pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.55" fill="#ece8dc" opacity="0.55"/></pattern>')
svg.append(f'<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 Z" fill="{BLUE}"/></marker>')
svg.append('</defs>')

# Opaque chart patch over the AI-generated chart only.
cx, cy, cw, ch = cover
svg.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="{PAPER}"/>')
svg.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" fill="url(#dots)" opacity="0.8"/>')

# Grid and axes.
for pct in [100, 90, 80, 70, 60, 50, 40, 30]:
    y = Y(pct)
    svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1.5" stroke-dasharray="2 4" opacity="0.9"/>')
    svg.append(text(203, y + 8, f"{pct}%", 26, MUTED, "end", "500", "monospace"))
for cost in [0.13, 0.14, 0.15, 0.16]:
    x = X(cost)
    svg.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{GRID}" stroke-width="1.5" stroke-dasharray="2 4" opacity="0.9"/>')
    svg.append(text(x, 1034, f"${cost:.2f}", 26, MUTED, "middle", "500", "monospace"))
svg.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')
svg.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{BLACK}" stroke-width="3"/>')

# Axis titles.
svg.append(text(112, 685, "PARTIAL REWARD · → BETTER", 24, MUTED, "middle", "700", "monospace", 'transform="rotate(-90 112 685)"'))
svg.append(text(676, 1067, "COST · $ PER TASK → MORE EXPENSIVE", 25, MUTED, "middle", "700", "monospace"))

# Tier labels, placed near their data rather than centered in empty bands.
svg.append(text(X(points["EASY"]["baseline"][0]) - 115, Y(points["EASY"]["baseline"][1]) + 8, "EASY", 38, BLACK, "end", "800", "Georgia,serif"))
svg.append(text(X(points["MEDIUM"]["pony"][0]), Y(points["MEDIUM"]["pony"][1]) + 96, "MEDIUM", 38, BLACK, "middle", "800", "Georgia,serif"))
svg.append(text(625, 975, "HARD", 38, BLACK, "middle", "800", "Georgia,serif"))

# Arrows, dots, labels. Draw straight arrows first, dots above.
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
        svg.append(text(bx + 20, by + 5, d["baseline"][2], 23, BLACK, "start", "700", "monospace"))
        svg.append(text(px + 22, py + 18, d["pony"][2], 23, BLUE, "start", "700", "monospace"))
    elif tier == "MEDIUM":
        svg.append(text(bx - 18, by + 6, d["baseline"][2], 23, BLACK, "end", "700", "monospace"))
        svg.append(text(px - 22, py + 8, d["pony"][2], 23, BLUE, "end", "700", "monospace"))
    else:
        svg.append(text(bx + 20, by - 18, d["baseline"][2], 23, BLACK, "start", "700", "monospace"))
        svg.append(text(px - 22, py + 8, d["pony"][2], 23, BLUE, "end", "700", "monospace"))

svg.append('</svg>')
SVG.write_text("\n".join(svg) + "\n")
subprocess.run(["rsvg-convert", "-w", str(W), "-h", str(H), str(SVG), "-o", str(OVERLAY)], check=True)
subprocess.run(["magick", str(BASE), str(OVERLAY), "-composite", str(OUT)], check=True)
print(OUT)
