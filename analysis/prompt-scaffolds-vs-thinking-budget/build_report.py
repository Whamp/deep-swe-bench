#!/usr/bin/env python3
"""Build the GPT-5.5 prompt-scaffold vs thinking-budget report.

This script is intentionally self-contained and reads only durable benchmark
artifacts already present in the repository. It does not rerun benchmark cells.
"""
from __future__ import annotations

import html
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "analysis" / "prompt-scaffolds-vs-thinking-budget"
REPORT_DIR = ROOT / "reports" / "prompt-scaffolds-vs-thinking-budget"
DATA_PATH = OUT_DIR / "prompt_scaffold_metrics.json"
REPORT_PATH = REPORT_DIR / "index.html"

LOW_PROMPT_SUMMARY = ROOT / "analysis" / "gpt55-low-prompt-ablation-36v2" / "summary.json"
LOW_CLEAN_SUMMARY = ROOT / "analysis" / "gpt55-low-clean-baseline-36v2" / "summary.json"
OMP_SUMMARY = ROOT / "analysis" / "omp-pi-prompt-no-project-36v2" / "summary.json"
MEDIUM_MANIFEST = ROOT / "results" / "_runs" / "gpt55-medium-clean-baseline-36v2-r3-w24" / "manifest.json"
STALE_REPORT = ROOT / "analysis" / "gpt55-medium-36v2-comparison" / "report.md"

LOW_PROMPT_CONFIGS = [
    {
        "config": "baseline-neutral-orchestration-only",
        "label": "Neutral orchestration",
        "cluster": "Neutral/no-op orchestration",
        "prompt_kind": "orchestration.md",
        "source_paths": ["configs/baseline-neutral-orchestration-only/orchestration.md"],
        "classification": "prompt-only; tiny allegedly neutral instruction",
    },
    {
        "config": "baseline-preamble-only",
        "label": "Engineer preamble",
        "cluster": "Engineer-competence preamble",
        "prompt_kind": "system_preamble.md",
        "source_paths": ["configs/baseline-preamble-only/system_preamble.md"],
        "classification": "prompt-only; competent-engineer role/process framing",
    },
    {
        "config": "baseline-preamble-orchestration",
        "label": "Engineer preamble + neutral orchestration",
        "cluster": "Engineer preamble + neutral/no-op orchestration",
        "prompt_kind": "system_preamble.md + orchestration.md",
        "source_paths": [
            "configs/baseline-preamble-orchestration/system_preamble.md",
            "configs/baseline-preamble-orchestration/orchestration.md",
        ],
        "classification": "prompt-only; historical baseline label must keep scaffold label",
    },
    {
        "config": "baseline-wf-only",
        "label": "Workflow checklist",
        "cluster": "Workflow/checklist scaffold",
        "prompt_kind": "orchestration.md",
        "source_paths": ["configs/baseline-wf-only/orchestration.md"],
        "classification": "prompt-only; explicit step-by-step reproduce/edit/test/commit loop",
    },
    {
        "config": "baseline-preamble-orchestration-wf",
        "label": "Engineer preamble + workflow checklist",
        "cluster": "Instruction bundle / clutter test",
        "prompt_kind": "system_preamble.md + orchestration.md",
        "source_paths": [
            "configs/baseline-preamble-orchestration-wf/system_preamble.md",
            "configs/baseline-preamble-orchestration-wf/orchestration.md",
        ],
        "classification": "prompt-only; combined scaffold underperforms the best component alone on binary solves",
    },
]

OMP_PROMPT_CONFIGS = [
    {
        "config": "baseline-omp-pi-prompt-bash-only-no-project",
        "label": "OMP/Pi-like bash-only prompt",
        "cluster": "Mini SWE-agent / OMP-style harness prompt",
        "prompt_kind": "omp-system-prompt.md + verbose tool schema",
        "source_paths": ["configs/baseline-omp-pi-prompt-bash-only-no-project/omp-system-prompt.md"],
        "classification": "top-of-context/tool-surface scaffold; same provider tool names as clean Pi but much larger tool-schema payload",
    },
    {
        "config": "baseline-omp-pi-prompt-grepglob-no-project",
        "label": "OMP/Pi-like grep+glob prompt",
        "cluster": "Tool-use affordance prompt",
        "prompt_kind": "omp-system-prompt.md + grep/glob tools",
        "source_paths": ["configs/baseline-omp-pi-prompt-grepglob-no-project/omp-system-prompt.md"],
        "classification": "top-of-context/tool-surface scaffold; not pure prompt-only because tools differ from clean Pi",
    },
    {
        "config": "baseline-omp-pi-prompt-ast-no-project",
        "label": "OMP/Pi-like AST prompt",
        "cluster": "Tool-use affordance prompt",
        "prompt_kind": "omp-system-prompt.md + AST tools",
        "source_paths": ["configs/baseline-omp-pi-prompt-ast-no-project/omp-system-prompt.md"],
        "classification": "top-of-context/tool-surface scaffold; not pure prompt-only because tools differ from clean Pi",
    },
]


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def read_text(path: str) -> str:
    p = ROOT / path
    return p.read_text() if p.exists() else ""


def prompt_chars(paths: list[str]) -> int:
    return sum(len(read_text(p)) for p in paths)


def snippet(paths: list[str], max_chars: int = 220) -> str:
    chunks = []
    for p in paths:
        text = " ".join(read_text(p).strip().split())
        if text:
            chunks.append(f"{p}: {text[:max_chars]}{'…' if len(text) > max_chars else ''}")
    return " | ".join(chunks)


def fmt_money(x: float | None, digits: int = 2) -> str:
    if x is None or math.isnan(x):
        return "—"
    return f"${x:,.{digits}f}"


def fmt_num(x: float | None, digits: int = 1) -> str:
    if x is None or math.isnan(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{digits}f}"


def pct(x: float | None, digits: int = 1) -> str:
    if x is None or math.isnan(x):
        return "—"
    return f"{x * 100:.{digits}f}%"


def e(s) -> str:
    return html.escape(str(s), quote=True)


def median_clean_medium_from_manifest() -> dict:
    manifest = load_json(MEDIUM_MANIFEST)
    rows = []
    for cell in manifest["batch_cells"]:
        rows.append(load_json(ROOT / cell["result_path"]))
    return {
        "n": len(rows),
        "distinct_tasks": len({r["task"] for r in rows}),
        "solves": sum(int(r["reward_binary"]) for r in rows),
        "solve_rate": sum(int(r["reward_binary"]) for r in rows) / len(rows),
        "mean_partial": sum(float(r["reward_partial"]) for r in rows) / len(rows),
        "median_tokens": statistics.median(float(r["combined_total_tokens"]) for r in rows),
        "total_tokens": sum(float(r["combined_total_tokens"]) for r in rows),
        "median_cost": statistics.median(float(r["combined_cost_usd"]) for r in rows),
        "total_cost": sum(float(r["combined_cost_usd"]) for r in rows),
        "median_wall_s": statistics.median(float(r["agent_wall_s"]) for r in rows),
        "median_turns": statistics.median(float(r["turns"]) for r in rows),
        "median_tool_calls": statistics.median(float(r["tool_calls"]) for r in rows),
    }


def row_from_low_prompt(meta: dict, low_summary: dict, clean_low: dict, reference_delta: dict) -> dict:
    cfg = meta["config"]
    s = low_summary["summary"][cfg]
    pair = low_summary["paired"][cfg]
    solve_delta = s["solves"] - clean_low["solves"]
    total_cost_delta = s["total_cost"] - clean_low["total_cost"]
    cost_per_net = total_cost_delta / solve_delta if solve_delta > 0 else None
    return {
        **meta,
        "thinking": "low",
        "n": s["n"],
        "solves": s["solves"],
        "solve_rate": s["solve_rate"],
        "mean_partial": s["mean_partial"],
        "median_tokens": s["median_tokens"],
        "median_cost": s["median_cost"],
        "total_cost": s["total_cost"],
        "solve_delta_vs_clean_low": solve_delta,
        "total_cost_delta_vs_clean_low": total_cost_delta,
        "median_token_delta_vs_clean_low": pair["deltas"]["tokens"]["median"],
        "median_cost_delta_vs_clean_low": pair["deltas"]["cost"]["median"],
        "cost_per_net_solve_vs_clean_low": cost_per_net,
        "gap_closed_vs_low_to_medium": solve_delta / reference_delta["solves"],
        "both_solved": pair["both"],
        "clean_only": pair["clean_only"],
        "other_only": pair["other_only"],
        "neither": pair["neither"],
        "improved_cells": sum(1 for m in pair.get("movers", []) if m.get("delta_partial", 0) > 0),
        "worsened_cells": sum(1 for m in pair.get("movers", []) if m.get("delta_partial", 0) < 0),
        "difficulty": pair.get("bucket", {}),
        "prompt_chars": prompt_chars(meta["source_paths"]),
        "prompt_excerpt": snippet(meta["source_paths"]),
        "evidence_paths": [
            str(LOW_PROMPT_SUMMARY.relative_to(ROOT)),
            *meta["source_paths"],
        ],
        "purity": "pure_prompt_only",
    }


def row_from_omp_prompt(meta: dict, omp: dict, clean_low: dict, reference_delta: dict) -> dict:
    cfg = meta["config"]
    s = omp["summaries"][cfg]
    pair_key = f"baseline__vs__{cfg}"
    pair = omp["pairs"][pair_key]
    solve_delta = pair["solve_delta"]
    total_cost_delta = pair["sum_delta_combined_cost_usd"]
    return {
        **meta,
        "thinking": "low",
        "n": s["n"],
        "solves": s["solves"],
        "solve_rate": s["solve_rate"],
        "mean_partial": s["mean_partial"],
        "median_tokens": s["median_tokens"],
        "median_cost": s["median_cost"],
        "total_cost": s["total_cost"],
        "solve_delta_vs_clean_low": solve_delta,
        "total_cost_delta_vs_clean_low": total_cost_delta,
        "median_token_delta_vs_clean_low": pair["median_delta_combined_total_tokens"],
        "median_cost_delta_vs_clean_low": pair["median_delta_combined_cost_usd"],
        "cost_per_net_solve_vs_clean_low": total_cost_delta / solve_delta if solve_delta > 0 else None,
        "gap_closed_vs_low_to_medium": solve_delta / reference_delta["solves"],
        "both_solved": pair["both_solved"],
        "clean_only": pair["a_only"],
        "other_only": pair["b_only"],
        "neither": pair["neither"],
        "improved_cells": pair["improved_cells"],
        "worsened_cells": pair["worsened_cells"],
        "difficulty": pair.get("difficulty", {}),
        "provider_tool_variants": s.get("provider_tool_variants"),
        "provider_tool_schema_bytes_median": s.get("provider_tool_schema_bytes_median"),
        "provider_instructions_chars_median": s.get("provider_instructions_chars_median"),
        "prompt_chars": prompt_chars(meta["source_paths"]),
        "prompt_excerpt": snippet(meta["source_paths"]),
        "evidence_paths": [
            str(OMP_SUMMARY.relative_to(ROOT)),
            *meta["source_paths"],
        ],
        "purity": "top_context_plus_tool_surface",
    }


def build_data() -> dict:
    low_clean = load_json(LOW_CLEAN_SUMMARY)["configs"]["baseline"]
    low_prompt = load_json(LOW_PROMPT_SUMMARY)
    omp = load_json(OMP_SUMMARY)
    medium_clean = median_clean_medium_from_manifest()

    reference_pair = omp["pairs"]["baseline__vs__baseline__gpt55_medium"]
    reference_delta = {
        "solves": medium_clean["solves"] - low_clean["solves"],
        "total_cost": medium_clean["total_cost"] - low_clean["total_cost"],
        "median_tokens": medium_clean["median_tokens"] - low_clean["median_tokens"],
        "cost_per_net_solve": (medium_clean["total_cost"] - low_clean["total_cost"]) / (medium_clean["solves"] - low_clean["solves"]),
        "paired": reference_pair,
    }

    prompt_rows = [row_from_low_prompt(meta, low_prompt, low_clean, reference_delta) for meta in LOW_PROMPT_CONFIGS]
    prompt_rows += [row_from_omp_prompt(meta, omp, low_clean, reference_delta) for meta in OMP_PROMPT_CONFIGS]

    medium_pair = omp["pairs"]["baseline__gpt55_medium__vs__baseline-preamble-orchestration__gpt55_medium"]
    medium_scaffold = omp["summaries"]["baseline-preamble-orchestration__gpt55_medium"]
    medium_prompt_behavior = {
        "config": "baseline-preamble-orchestration__gpt55_medium",
        "label": "Engineer preamble + neutral orchestration at medium",
        "thinking": "medium",
        "n": medium_pair["n"],
        "solves": medium_scaffold["solves"],
        "clean_medium_solves": medium_clean["solves"],
        "solve_delta_vs_clean_medium": medium_pair["solve_delta"],
        "total_cost_delta_vs_clean_medium": medium_pair["sum_delta_combined_cost_usd"],
        "cost_per_net_solve_vs_clean_medium": medium_pair["sum_delta_combined_cost_usd"] / medium_pair["solve_delta"] if medium_pair["solve_delta"] > 0 else None,
        "both_solved": medium_pair["both_solved"],
        "clean_only": medium_pair["a_only"],
        "other_only": medium_pair["b_only"],
        "neither": medium_pair["neither"],
        "mean_delta_partial": medium_pair["mean_delta_partial"],
        "median_delta_tokens": medium_pair["median_delta_combined_total_tokens"],
        "median_delta_cost": medium_pair["median_delta_combined_cost_usd"],
        "evidence_paths": [str(OMP_SUMMARY.relative_to(ROOT)), str(MEDIUM_MANIFEST.relative_to(ROOT))],
        "caveat": "Only this medium prompt scaffold has a clean 108-cell comparable pair in the chosen artifacts; medium workflow-bundle cells do not cover the same 36_v2 cell set and are excluded from apples-to-apples claims.",
    }

    data = {
        "title": "Prompt scaffolds vs thinking budget: what instructions actually help GPT-5.5 in Pi?",
        "generated_from": [
            str(LOW_CLEAN_SUMMARY.relative_to(ROOT)),
            str(LOW_PROMPT_SUMMARY.relative_to(ROOT)),
            str(OMP_SUMMARY.relative_to(ROOT)),
            str(MEDIUM_MANIFEST.relative_to(ROOT)),
        ],
        "stale_report_superseded": str(STALE_REPORT.relative_to(ROOT)),
        "baselines": {
            "clean_low": {**low_clean, "source": str(LOW_CLEAN_SUMMARY.relative_to(ROOT))},
            "clean_medium": {**medium_clean, "source": str(MEDIUM_MANIFEST.relative_to(ROOT))},
            "low_to_medium_reference": reference_delta,
        },
        "prompt_rows": prompt_rows,
        "medium_prompt_behavior": medium_prompt_behavior,
        "excluded_or_context_only": [
            {
                "item": "analysis/gpt55-medium-36v2-comparison/report.md",
                "reason": "Useful historical context, but stale for this report because it reports historical low baseline numbers rather than clean low 28/108 and clean medium 50/108.",
            },
            {
                "item": "results/_contaminated/",
                "reason": "Excluded from normal efficacy claims by project rule.",
            },
            {
                "item": "results/gpt-5.5/medium/baseline-preamble-orchestration-wf",
                "reason": "Has only 33 overlapping cells with the clean-medium 36_v2 manifest, so it is not used for medium apples-to-apples scaffold claims.",
            },
            {
                "item": "baseline-omp / baseline-omp-bash-only / baseline-omp-ast",
                "reason": "Different OMP harness context; useful for harness comparisons, not prompt-on-clean-Pi claims.",
            },
        ],
    }
    return data


def scatter_svg(rows: list[dict], reference: dict) -> str:
    width, height = 760, 420
    margin = {"l": 70, "r": 26, "t": 24, "b": 58}
    xs = [max(0, r["total_cost_delta_vs_clean_low"]) for r in rows] + [reference["total_cost"]]
    ys = [max(0, r["solve_delta_vs_clean_low"]) for r in rows] + [reference["solves"]]
    xmax = max(xs) * 1.12
    ymax = max(ys) * 1.18

    def sx(x):
        return margin["l"] + (x / xmax) * (width - margin["l"] - margin["r"])

    def sy(y):
        return height - margin["b"] - (y / ymax) * (height - margin["t"] - margin["b"])

    ref_x = sx(reference["total_cost"])
    ref_y = sy(reference["solves"])
    origin_x = sx(0)
    origin_y = sy(0)
    palette = {
        "pure_prompt_only": "#34d399",
        "top_context_plus_tool_surface": "#fbbf24",
    }
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Extra solves versus extra cost scatter plot">',
        '<defs><filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.35"/></filter></defs>',
        f'<rect width="{width}" height="{height}" rx="18" fill="#09182a"/>',
        f'<line x1="{origin_x:.1f}" y1="{origin_y:.1f}" x2="{width-margin["r"]}" y2="{origin_y:.1f}" stroke="#35506e"/>',
        f'<line x1="{origin_x:.1f}" y1="{height-margin["b"]}" x2="{origin_x:.1f}" y2="{margin["t"]}" stroke="#35506e"/>',
        f'<line x1="{origin_x:.1f}" y1="{origin_y:.1f}" x2="{ref_x:.1f}" y2="{ref_y:.1f}" stroke="#60a5fa" stroke-width="2.5" stroke-dasharray="7 6"/>',
        f'<circle cx="{ref_x:.1f}" cy="{ref_y:.1f}" r="8" fill="#60a5fa" filter="url(#shadow)"/>',
        f'<text x="{ref_x-84:.1f}" y="{ref_y-14:.1f}" fill="#bfdbfe" font-size="12" font-weight="800">low → medium</text>',
    ]
    for tick in range(0, int(math.ceil(xmax / 20.0)) * 20 + 1, 20):
        x = sx(tick)
        parts += [
            f'<line x1="{x:.1f}" y1="{origin_y:.1f}" x2="{x:.1f}" y2="{origin_y+5:.1f}" stroke="#35506e"/>',
            f'<text x="{x:.1f}" y="{origin_y+24:.1f}" text-anchor="middle" fill="#9fb0c9" font-size="11">${tick}</text>',
        ]
    for tick in range(0, int(math.ceil(ymax / 5.0)) * 5 + 1, 5):
        y = sy(tick)
        parts += [
            f'<line x1="{origin_x-5:.1f}" y1="{y:.1f}" x2="{origin_x:.1f}" y2="{y:.1f}" stroke="#35506e"/>',
            f'<text x="{origin_x-10:.1f}" y="{y+4:.1f}" text-anchor="end" fill="#9fb0c9" font-size="11">+{tick}</text>',
        ]
    label_offsets = {
        "Neutral orchestration": (9, -8),
        "Engineer preamble": (9, -8),
        "Engineer preamble + neutral orchestration": (9, 14),
        "Workflow checklist": (9, -8),
        "Engineer preamble + workflow checklist": (9, 14),
        "OMP/Pi-like bash-only prompt": (9, -8),
        "OMP/Pi-like grep+glob prompt": (9, 14),
        "OMP/Pi-like AST prompt": (9, 32),
    }
    for r in rows:
        x = sx(max(0, r["total_cost_delta_vs_clean_low"]))
        y = sy(max(0, r["solve_delta_vs_clean_low"]))
        color = palette.get(r["purity"], "#e5e7eb")
        radius = 7 if r["purity"] == "pure_prompt_only" else 8
        dx, dy = label_offsets.get(r["label"], (9, -8))
        parts += [
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" stroke="#07111f" stroke-width="2" filter="url(#shadow)"/>',
            f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" fill="#e7eefb" font-size="11">{e(r["label"])}</text>',
        ]
    parts += [
        f'<text x="{width/2:.1f}" y="{height-14}" text-anchor="middle" fill="#cfe2ff" font-size="12" font-weight="800">extra total cost vs clean low, 108 cells</text>',
        f'<text transform="translate(18 {height/2}) rotate(-90)" text-anchor="middle" fill="#cfe2ff" font-size="12" font-weight="800">extra solves vs clean low</text>',
        '</svg>',
    ]
    return "\n".join(parts)


def rows_table(rows: list[dict]) -> str:
    trs = []
    for r in rows:
        cps = r["cost_per_net_solve_vs_clean_low"]
        eff = "—"
        if cps is not None:
            if cps < 0:
                eff = "near-zero / lower total cost"
            else:
                eff = fmt_money(cps, 2)
        tag = "good" if r["solve_delta_vs_clean_low"] > 0 and (cps is None or cps <= 4.24) else "caution"
        if r["purity"] != "pure_prompt_only":
            tag = "caution"
        trs.append(f"""
<tr>
  <td><span class="tag {tag}">{e(r['label'])}</span><div class="muted">{e(r['cluster'])}</div></td>
  <td>{r['solves']}/108 <span class="muted">({pct(r['solve_rate'])})</span></td>
  <td><b>{r['solve_delta_vs_clean_low']:+d}</b><div class="muted">{r['other_only']} gained / {r['clean_only']} lost cells</div></td>
  <td>{fmt_money(r['total_cost_delta_vs_clean_low'], 2)}<div class="muted">median Δ {fmt_money(r['median_cost_delta_vs_clean_low'], 2)}</div></td>
  <td>{eff}</td>
  <td>{pct(r['gap_closed_vs_low_to_medium'])}</td>
  <td>{fmt_num(r['median_token_delta_vs_clean_low'] / 1000, 0)}k</td>
  <td>{e(r['classification'])}</td>
</tr>""")
    return "\n".join(trs)


def evidence_table(rows: list[dict]) -> str:
    trs = []
    for r in rows:
        sources = "<br>".join(f"<code>{e(p)}</code>" for p in r["evidence_paths"])
        excerpt = e(r["prompt_excerpt"])
        trs.append(f"""
<tr>
  <td>{e(r['label'])}<div class="muted">{r['prompt_chars']} prompt file chars; {e(r['prompt_kind'])}</div></td>
  <td>{excerpt}</td>
  <td>{sources}</td>
</tr>""")
    return "\n".join(trs)


def difficulty_rows(rows: list[dict]) -> str:
    trs = []
    for r in rows:
        parts = []
        for bucket in ["hard", "medium", "easy"]:
            b = r.get("difficulty", {}).get(bucket, {})
            if "solve_delta" in b:
                parts.append(f"{bucket}: {b.get('solve_delta'):+d}")
            elif "other_only" in b and "clean_only" in b:
                parts.append(f"{bucket}: {b.get('other_only') - b.get('clean_only'):+d}")
            elif "solves" in b:
                parts.append(f"{bucket}: {b.get('solves')}")
        trs.append(f"<tr><td>{e(r['label'])}</td><td>{' · '.join(parts) or '—'}</td></tr>")
    return "\n".join(trs)


def render_html(data: dict) -> str:
    low = data["baselines"]["clean_low"]
    med = data["baselines"]["clean_medium"]
    ref = data["baselines"]["low_to_medium_reference"]
    rows = data["prompt_rows"]
    pure_rows = [r for r in rows if r["purity"] == "pure_prompt_only"]
    tool_rows = [r for r in rows if r["purity"] != "pure_prompt_only"]
    best_pure = max(pure_rows, key=lambda r: r["solve_delta_vs_clean_low"])
    medium_behavior = data["medium_prompt_behavior"]
    svg = scatter_svg(rows, ref)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{e(data['title'])}</title>
<style>
:root {{
  --bg:#07111f; --surface:#0f1d31; --surface2:#14243b; --ink:#eef5ff; --muted:#9fb0c9;
  --blue:#60a5fa; --green:#34d399; --red:#fb7185; --amber:#fbbf24; --line:#263850;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:radial-gradient(circle at top left,#173d63 0,#07111f 42%,#050913 100%); color:var(--ink); font:15px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
main {{ max-width:1280px; margin:0 auto; padding:36px 22px 64px; }}
.hero {{ border:1px solid rgba(96,165,250,.32); background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.94) 42%,rgba(52,211,153,.10)); border-radius:28px; padding:32px; box-shadow:0 24px 80px rgba(0,0,0,.35); }}
.kicker {{ color:var(--blue); text-transform:uppercase; letter-spacing:.14em; font-size:12px; font-weight:800; }}
h1 {{ font-size:clamp(34px,5vw,64px); line-height:.96; margin:12px 0 16px; letter-spacing:-.055em; max-width:1050px; }}
h2 {{ margin:34px 0 12px; font-size:26px; letter-spacing:-.03em; }}
h3 {{ margin:24px 0 10px; font-size:18px; }}
p {{ color:#dbe7fb; max-width:1000px; }}
.pills {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }}
.pill,.tag {{ display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:5px 10px; font-size:12px; font-weight:800; border:1px solid var(--line); background:#0b1728; color:var(--muted); white-space:nowrap; }}
.pill.good,.tag.good {{ color:#b9f8da; border-color:rgba(52,211,153,.5); background:rgba(52,211,153,.12); }}
.pill.bad,.tag.bad {{ color:#fecdd3; border-color:rgba(251,113,133,.5); background:rgba(251,113,133,.12); }}
.pill.caution,.tag.caution {{ color:#fde68a; border-color:rgba(251,191,36,.55); background:rgba(251,191,36,.12); }}
.pill.neutral,.tag.neutral {{ color:#bfdbfe; border-color:rgba(96,165,250,.45); background:rgba(96,165,250,.12); }}
.stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:22px 0; }}
.stat {{ background:rgba(15,29,49,.86); border:1px solid var(--line); border-radius:20px; padding:18px; min-height:112px; }}
.stat b {{ display:block; font-size:30px; line-height:1; letter-spacing:-.04em; margin-bottom:8px; }}
.stat span {{ color:var(--muted); font-size:13px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.card,.callout {{ background:rgba(15,29,49,.88); border:1px solid var(--line); border-radius:22px; padding:18px; }}
.callout {{ margin:16px 0; }}
.callout.good {{ border-color:rgba(52,211,153,.45); background:rgba(52,211,153,.09); }}
.callout.warn {{ border-color:rgba(251,191,36,.45); background:rgba(251,191,36,.09); }}
.callout.bad {{ border-color:rgba(251,113,133,.45); background:rgba(251,113,133,.09); }}
table {{ width:100%; border-collapse:separate; border-spacing:0; margin:12px 0 22px; overflow:hidden; border:1px solid var(--line); border-radius:18px; background:rgba(9,18,32,.68); }}
th,td {{ text-align:left; vertical-align:top; padding:12px 12px; border-bottom:1px solid var(--line); }}
th {{ color:#cfe2ff; font-size:12px; text-transform:uppercase; letter-spacing:.08em; background:rgba(96,165,250,.10); }}
tr:last-child td {{ border-bottom:0; }}
td {{ color:#e7eefb; }}
code {{ color:#dbeafe; background:rgba(96,165,250,.11); border:1px solid rgba(96,165,250,.18); border-radius:7px; padding:1px 5px; font-size:12px; }}
.src,.muted {{ color:var(--muted); font-size:12px; }}
.chart {{ background:rgba(9,18,32,.72); border:1px solid var(--line); border-radius:22px; padding:12px; overflow-x:auto; }}
ul.evidence-list li {{ margin:8px 0; }}
@media (max-width:900px) {{ .stats,.grid {{ grid-template-columns:1fr; }} table {{ display:block; overflow-x:auto; }} }}
</style>
</head>
<body>
<main>
<section class="hero">
  <div class="kicker">Report synthesis · prompt scaffolds · GPT-5.5 · 36_v2</div>
  <h1>Prompt scaffolds can buy low-thinking solves, but medium thinking is the benchmark.</h1>
  <p>Clean Pi low is <b>{low['solves']}/108</b>. Clean Pi medium is <b>{med['solves']}/108</b>. That low→medium step costs <b>{fmt_money(ref['total_cost'], 2)}</b> for <b>+{ref['solves']}</b> solves, or <b>{fmt_money(ref['cost_per_net_solve'], 2)}</b> per net solve. Any prompt scaffold should be judged against that line, not against a sloppy historical baseline label.</p>
  <div class="pills">
    <span class="pill neutral">model: openai-codex/gpt-5.5</span>
    <span class="pill neutral">subset: 36_v2</span>
    <span class="pill neutral">36 tasks × 3 reps = 108 cells</span>
    <span class="pill good">clean low anchor: {low['solves']}/108</span>
    <span class="pill good">clean medium anchor: {med['solves']}/108</span>
    <span class="pill caution">OMP-style rows include tool-surface caveats</span>
  </div>
  <div class="src">Primary evidence: <code>{e(low['source'])}</code> · <code>{e(med['source'])}</code> · <code>{e(str(LOW_PROMPT_SUMMARY.relative_to(ROOT)))}</code> · <code>{e(str(OMP_SUMMARY.relative_to(ROOT)))}</code></div>
</section>

<div class="stats">
  <div class="stat"><b>{low['solves']}/108</b><span>clean Pi low baseline · total {fmt_money(low['total_cost'], 2)} · median {fmt_num(low['median_tokens']/1000, 0)}k tokens</span></div>
  <div class="stat"><b>{med['solves']}/108</b><span>clean Pi medium baseline · total {fmt_money(med['total_cost'], 2)} · median {fmt_num(med['median_tokens']/1000, 0)}k tokens</span></div>
  <div class="stat"><b>+{ref['solves']}</b><span>net solves from low→medium · {fmt_money(ref['cost_per_net_solve'], 2)} per net solve</span></div>
  <div class="stat"><b>+{best_pure['solve_delta_vs_clean_low']}</b><span>best pure prompt-only low gain: {e(best_pure['label'])} · {fmt_money(best_pure['cost_per_net_solve_vs_clean_low'], 2)} per net solve</span></div>
</div>

<section class="callout good">
  <h2>Verdict</h2>
  <p>The strongest pure prompt-only signal is the explicit workflow checklist: <b>{best_pure['solves']}/108</b>, <b>{best_pure['solve_delta_vs_clean_low']:+d}</b> solves over clean low, and <b>{pct(best_pure['gap_closed_vs_low_to_medium'])}</b> of the low→medium solve gap at <b>{fmt_money(best_pure['cost_per_net_solve_vs_clean_low'], 2)}</b> per net solve. But it still closes only about one-third of the gap to clean medium. The prompt story is therefore not “prompts replace thinking”; it is “process scaffolds can cheaply rescue some low-thinking failures, while thinking level remains the larger lever.”</p>
</section>

<h2>Efficiency frontier: extra solves vs extra cost</h2>
<div class="chart">{svg}</div>
<div class="src">Green = pure prompt-only config files layered on Pi. Amber = OMP/Pi-like top-of-context/tool-surface rows; useful for prompt/tool affordance hypotheses, not pure prompt-only claims.</div>

<h2>Prompt scaffold taxonomy and efficiency</h2>
<table>
<thead><tr><th>Scaffold</th><th>Solves</th><th>Net solves vs clean low</th><th>Total cost delta</th><th>$/net solve</th><th>Low→medium gap closed</th><th>Median token delta</th><th>Classification</th></tr></thead>
<tbody>
{rows_table(rows)}
</tbody>
</table>

<div class="grid">
  <section class="card">
    <h3>Pure prompt-only takeaways</h3>
    <ul class="evidence-list">
      <li><b>Workflow/checklist scaffolding</b> is the best low-thinking pure prompt in this set: {best_pure['other_only']} gained cells versus {best_pure['clean_only']} cells lost.</li>
      <li><b>Engineer-competence framing</b> also helps at low thinking: <code>baseline-preamble-only</code> reaches 34/108, +6 over clean low.</li>
      <li><b>More instructions are not automatically better.</b> The combined preamble+workflow bundle reaches 31/108, below workflow-only at 35/108 and preamble-only at 34/108.</li>
      <li><b>The tiny neutral instruction is not neutral in outcomes</b>: it reaches 30/108, but with small effect size and the exact text (“competent engineer”) means it should not be labeled clean baseline.</li>
    </ul>
  </section>
  <section class="card">
    <h3>Thinking-level constraint</h3>
    <ul class="evidence-list">
      <li>Clean low→medium adds {ref['solves']} solves with 27 gains and 5 losses in paired cells.</li>
      <li>No prompt-only low config reaches clean medium’s {med['solves']}/108.</li>
      <li>The medium comparable prompt scaffold, preamble+neutral orchestration, adds only {medium_behavior['solve_delta_vs_clean_medium']:+d} solves over clean medium, with {medium_behavior['other_only']} gained cells and {medium_behavior['clean_only']} lost cells.</li>
      <li>This suggests prompt scaffolds may be more like <b>low-thinking training wheels</b> than a substitute for thinking budget, though the medium +3 result keeps complementarity plausible.</li>
    </ul>
  </section>
</div>

<h2>Difficulty-level solve deltas</h2>
<table>
<thead><tr><th>Scaffold</th><th>Hard / medium / easy net solve movement</th></tr></thead>
<tbody>
{difficulty_rows(rows)}
</tbody>
</table>

<section class="callout warn">
  <h2>Medium-thinking behavior</h2>
  <p>The only clean 108-cell medium prompt pair in the selected artifacts is <code>baseline-preamble-orchestration__gpt55_medium</code>: <b>{medium_behavior['clean_medium_solves']}/108 → {medium_behavior['solves']}/108</b>, <b>{medium_behavior['solve_delta_vs_clean_medium']:+d}</b> solves, total cost delta <b>{fmt_money(medium_behavior['total_cost_delta_vs_clean_medium'], 2)}</b>, and median token delta <b>{fmt_num(medium_behavior['median_delta_tokens']/1000, 0)}k</b>. That is promising but small; the paired counts are {medium_behavior['other_only']} scaffold-only solves and {medium_behavior['clean_only']} clean-medium-only solves.</p>
  <p class="src">Evidence: <code>{e(str(OMP_SUMMARY.relative_to(ROOT)))}</code> pair <code>baseline__gpt55_medium__vs__baseline-preamble-orchestration__gpt55_medium</code>.</p>
</section>

<h2>Prompt evidence</h2>
<table>
<thead><tr><th>Scaffold</th><th>Prompt excerpt</th><th>Evidence paths</th></tr></thead>
<tbody>
{evidence_table(rows)}
</tbody>
</table>

<section class="callout bad">
  <h2>Caveats and exclusions</h2>
  <ul class="evidence-list">
    <li><b>Do not reuse the old thinking-level report as-is.</b> <code>{e(data['stale_report_superseded'])}</code> is stale for this analysis because it reports historical low numbers rather than clean low 28/108 and clean medium 50/108.</li>
    <li><b>OMP-style prompt rows are not pure prompt-only rows.</b> Their system prompts and/or tool schemas are top-of-context changes; grep/glob and AST rows also change available tools. Treat them as hypotheses about tool-affordance prompting, not clean Pi prompt ablations.</li>
    <li><b>No statistical certainty claim is made.</b> These are 108 paired cells per comparable config. Binary gains/losses are useful directionally, but prompt effects can be noisy.</li>
    <li><b>Contaminated artifacts are excluded.</b> <code>results/_contaminated/</code> is not used for efficacy claims.</li>
    <li><b>Medium workflow-bundle evidence is incomplete for this subset.</b> <code>results/gpt-5.5/medium/baseline-preamble-orchestration-wf</code> does not cover the clean-medium 36_v2 cell set, so it is not used for medium apples-to-apples claims.</li>
  </ul>
</section>

<section class="callout good">
  <h2>Conclusion</h2>
  <p>The most useful next prompt experiments should isolate <b>process checklist</b> from <b>competent-engineer framing</b>, then test whether those same prompts still help at medium. Today’s data says workflow/checklist instructions are the best prompt-only low-thinking scaffold, engineer preambles help, and instruction bundles can dilute rather than compound gains. The low→medium thinking upgrade remains the reference intervention every prompt has to beat or justify.</p>
</section>

<h2>Generated artifacts</h2>
<ul class="evidence-list">
  <li>Data: <code>{e(str(DATA_PATH.relative_to(ROOT)))}</code></li>
  <li>Report: <code>{e(str(REPORT_PATH.relative_to(ROOT)))}</code></li>
  <li>Builder: <code>{e(str(Path(__file__).relative_to(ROOT)))}</code></li>
</ul>

</main>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = build_data()
    DATA_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))
    REPORT_PATH.write_text(render_html(data))
    print(f"wrote {DATA_PATH.relative_to(ROOT)}")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
