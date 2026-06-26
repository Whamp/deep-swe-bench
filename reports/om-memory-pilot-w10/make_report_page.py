#!/usr/bin/env python3
"""Build a mobile-friendly HTML report page from OM assets and markdown reports."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = json.loads((HERE / "paired_manifest.json").read_text())["rows"]

IMAGE_ORDER = [
    "difficulty-bucket-card.png",
    "baseline-vs-om-scatter-card.png",
    "partial-delta-waterfall-card.png",
    "quality-vs-token-tradeoff-card.png",
    "success-modes-card.png",
    "regression-modes-card.png",
    "readme-style-benchmark-card.png",
]

REPORT_ORDER = [
    "deep_dive_synthesis.md",
    "initial_summary.md",
    "success_modes.md",
    "regression_failure_modes.md",
    "memory_mechanics.md",
    "difficulty_causal_analysis.md",
    "resource_tradeoffs.md",
    "public_framing_notes.md",
    "pair_0_top_wins.md",
    "pair_1_top_losses.md",
    "pair_2_new_solves.md",
    "pair_3_pathology_rescues.md",
    "pair_4_hard_bucket_wins.md",
    "pair_5_medium_easy_regressions.md",
    "pair_6_cheap_wins.md",
    "pair_7_expensive_wins.md",
]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0


def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def inline_md(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md: str) -> str:
    out = []
    in_ul = False
    in_code = False
    code = []
    para = []

    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + inline_md(" ".join(para)) + "</p>")
            para = []

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_para(); close_ul()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                code = []; in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not line.strip():
            flush_para(); close_ul(); continue
        if line.startswith("#"):
            flush_para(); close_ul()
            level = min(4, len(line) - len(line.lstrip("#")))
            title = line.lstrip("#").strip()
            out.append(f'<h{level} id="{slug(title)}">{inline_md(title)}</h{level}>')
            continue
        if line.startswith("- "):
            flush_para()
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append("<li>" + inline_md(line[2:].strip()) + "</li>")
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_para(); close_ul()
            out.append("<p>" + inline_md(line) + "</p>")
            continue
        para.append(line)
    flush_para(); close_ul()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
    return "\n".join(out)


b = [r["baseline"]["reward_partial"] for r in ROWS]
o = [r["om"]["reward_partial"] for r in ROWS]
d = [r["delta"]["partial"] for r in ROWS]
summary = {
    "n": len(ROWS),
    "baseline_mean": mean(b),
    "om_mean": mean(o),
    "delta_mean": mean(d),
    "baseline_solves": sum(r["baseline"]["reward_binary"] == 1 for r in ROWS),
    "om_solves": sum(r["om"]["reward_binary"] == 1 for r in ROWS),
    "improved": sum(x > 0 for x in d),
    "worse": sum(x < 0 for x in d),
    "tied": sum(x == 0 for x in d),
    "median_tokens_b": median([r["baseline"]["total_tokens"] for r in ROWS]),
    "median_tokens_o": median([r["om"]["total_tokens"] for r in ROWS]),
    "median_cost_b": median([r["baseline"]["cost_usd"] for r in ROWS]),
    "median_cost_o": median([r["om"]["cost_usd"] for r in ROWS]),
}

bucket_rows = []
for bucket in ["hard", "medium", "easy"]:
    rs = [r for r in ROWS if r["difficulty_bucket"] == bucket]
    bucket_rows.append((
        bucket.title(), len(rs), mean([r["baseline"]["reward_partial"] for r in rs]), mean([r["om"]["reward_partial"] for r in rs]),
        sum(r["baseline"]["reward_binary"] == 1 for r in rs), sum(r["om"]["reward_binary"] == 1 for r in rs),
    ))

reports_html = []
for name in REPORT_ORDER:
    p = HERE / name
    if not p.exists():
        continue
    title = name.replace("_", " ").replace(".md", "")
    reports_html.append(f"""
      <details class="report">
        <summary>{html.escape(title)}</summary>
        <article>{md_to_html(p.read_text())}</article>
      </details>
    """)

image_cards = "\n".join(
    f'<figure><a href="{img}"><img src="{img}" alt="{html.escape(img)}" loading="lazy"></a><figcaption>{html.escape(img)}</figcaption></figure>'
    for img in IMAGE_ORDER if (HERE / img).exists()
)

bucket_table = "\n".join(
    f"<tr><td>{name}</td><td>{n}</td><td>{bp:.3f}</td><td>{op:.3f}</td><td>{bs} → {os}</td></tr>"
    for name, n, bp, op, bs, os in bucket_rows
)

html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pi-observational-memory DeepSWE report</title>
<style>
:root {{ --blue:#2d2af4; --paper:#fbfaf6; --ink:#0d0d12; --muted:#555965; --line:#ded9cc; --good:#07875b; --bad:#d3412f; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--blue); color:var(--ink); font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:22px; }}
.hero, section {{ background:var(--paper); border-radius:28px; padding:28px; margin:22px 0; box-shadow:0 18px 50px rgba(0,0,0,.16); }}
h1,h2,h3 {{ font-family: Georgia, 'Times New Roman', serif; letter-spacing:-.025em; }}
h1 {{ font-size:clamp(38px, 8vw, 78px); line-height:.94; margin:0 0 14px; }}
h2 {{ font-size:clamp(30px, 5vw, 48px); margin:0 0 18px; }}
h3 {{ font-size:30px; margin-top:30px; }}
p {{ line-height:1.6; }}
a {{ color:var(--blue); }}
.kicker {{ color:var(--muted); font-weight:800; text-transform:uppercase; letter-spacing:.08em; }}
.metrics {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px; margin:24px 0; }}
.metric {{ background:white; border:1px solid rgba(0,0,0,.08); border-radius:18px; padding:18px; }}
.metric b {{ display:block; font-family:Georgia,serif; font-size:36px; color:var(--blue); }}
.metric span {{ color:var(--muted); font-weight:800; font-size:14px; }}
.callout {{ border-left:8px solid var(--blue); padding:16px 18px; background:white; border-radius:14px; font-size:18px; }}
.grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:18px; }}
figure {{ margin:0; background:white; border-radius:18px; padding:10px; border:1px solid rgba(0,0,0,.08); }}
figure img {{ width:100%; height:auto; display:block; border-radius:12px; }}
figcaption {{ color:var(--muted); padding:8px 4px 2px; font-size:13px; overflow-wrap:anywhere; }}
table {{ width:100%; border-collapse:collapse; background:white; border-radius:16px; overflow:hidden; }}
th,td {{ text-align:left; padding:13px 14px; border-bottom:1px solid var(--line); }}
th {{ color:var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:.07em; }}
.report {{ background:white; border-radius:16px; border:1px solid rgba(0,0,0,.08); margin:12px 0; }}
.report summary {{ cursor:pointer; padding:18px; font-weight:900; font-size:18px; }}
.report article {{ padding:0 22px 24px; }}
.report pre {{ overflow:auto; background:#11131a; color:#f8f8f2; padding:14px; border-radius:12px; }}
.report code {{ background:#eee9dc; padding:.15em .35em; border-radius:5px; }}
.report pre code {{ background:transparent; padding:0; }}
.good {{ color:var(--good); }} .bad {{ color:var(--bad); }}
.footer {{ color:white; opacity:.92; padding:20px 0 36px; text-align:center; }}
@media (max-width:760px) {{
  .wrap {{ padding:12px; }} .hero, section {{ padding:20px; border-radius:20px; margin:14px 0; }}
  .metrics {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} .grid {{ grid-template-columns:1fr; }}
  table {{ font-size:13px; }} th,td {{ padding:10px 8px; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="kicker">DeepSWE · Pi extension evaluation</div>
    <h1>pi-observational-memory improved hard-task performance</h1>
    <p class="callout">Paired 113-task replay versus the reused DeepSeek V4 Flash baseline. OM improved mean partial reward and full solves, with the lift concentrated in hard cross-file tasks. It cost more tokens/time.</p>
    <div class="metrics">
      <div class="metric"><span>mean partial</span><b>{summary['baseline_mean']:.3f} → {summary['om_mean']:.3f}</b><span class="good">Δ {summary['delta_mean']:+.3f}</span></div>
      <div class="metric"><span>full solves</span><b>{summary['baseline_solves']} → {summary['om_solves']}</b><span class="good">+{summary['om_solves']-summary['baseline_solves']}</span></div>
      <div class="metric"><span>task direction</span><b>{summary['improved']} / {summary['worse']} / {summary['tied']}</b><span>wins / losses / ties</span></div>
      <div class="metric"><span>median cost</span><b>${summary['median_cost_b']:.3f} → ${summary['median_cost_o']:.3f}</b><span class="bad">agent-side only</span></div>
    </div>
  </header>

  <section>
    <h2>Cards and charts</h2>
    <div class="grid">{image_cards}</div>
  </section>

  <section>
    <h2>Difficulty summary</h2>
    <table>
      <thead><tr><th>bucket</th><th>n</th><th>baseline partial</th><th>OM partial</th><th>full solves</th></tr></thead>
      <tbody>{bucket_table}</tbody>
    </table>
  </section>

  <section>
    <h2>Analysis reports</h2>
    <p>Open sections below for the full deep-dive, success modes, regressions, mechanics, and task sweeps.</p>
    {''.join(reports_html)}
  </section>

  <section>
    <h2>Source files</h2>
    <ul>
      <li><a href="paired_manifest.json">paired_manifest.json</a></li>
      <li><a href="findings_for_assets.json">findings_for_assets.json</a></li>
      <li><a href="make_om_assets.py">make_om_assets.py</a></li>
      <li><a href="make_report_page.py">make_report_page.py</a></li>
    </ul>
    <p><strong>Caveats:</strong> one rep, reused baseline, and OM worker model-call cost is not included in the main-session token/cost columns.</p>
  </section>

  <div class="footer">Served from deep-swe-bench over Tailscale</div>
</div>
</body>
</html>
"""

(HERE / "index.html").write_text(html_doc)
print(HERE / "index.html")
