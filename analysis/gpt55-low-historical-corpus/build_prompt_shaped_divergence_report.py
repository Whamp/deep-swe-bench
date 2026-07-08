#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-historical-corpus"
EMBED_ANALYSIS = ANALYSIS_DIR / "prompt_embedding_analysis.json"
EMBED_VECTORS = ANALYSIS_DIR / "prompt_embeddings.json"
CORPUS = ANALYSIS_DIR / "corpus_overlap_vs_clean_low.json"
OUT_JSON = ANALYSIS_DIR / "prompt_shaped_neighbor_divergence.json"
OUT_HTML = ROOT / "reports/gpt55-low-prompt-shaped-divergence/index.html"
RESULT_ROOT = ROOT / "results/gpt-5.5/low"

PROMPT_ONLY = "prompt_or_orchestration_only"
PROMPT_TOOL = "omp_pi_like_prompt_or_tool_surface"
INCLUDED_CATEGORIES = {PROMPT_ONLY, PROMPT_TOOL}


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def solved(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") == 1


def cost(row: dict[str, Any]) -> float:
    return float(row.get("combined_cost_usd", row.get("cost_usd", 0.0)) or 0.0)


def tokens(row: dict[str, Any]) -> int:
    return int(row.get("combined_total_tokens", row.get("total_tokens", 0)) or 0)


def partial(row: dict[str, Any]) -> float:
    return float(row.get("reward_partial") or 0.0)


@lru_cache(maxsize=None)
def result_cells(config: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    base = RESULT_ROOT / config
    if not base.exists():
        return out
    for path in base.glob("*/rep*/result.json"):
        try:
            row = load_json(path)
        except Exception:
            continue
        key = f"{path.parts[-3]}/{path.parts[-2]}"
        row["_path"] = str(path.relative_to(ROOT))
        out[key] = row
    return out


def pairwise_cells(a: str, b: str) -> dict[str, Any]:
    ac = result_cells(a)
    bc = result_cells(b)
    keys = sorted(set(ac) & set(bc))
    both = a_only = b_only = neither = 0
    a_cost = b_cost = 0.0
    a_tokens = b_tokens = 0
    a_partial = b_partial = 0.0
    examples: list[dict[str, str]] = []
    for key in keys:
        ar = ac[key]
        br = bc[key]
        sa = solved(ar)
        sb = solved(br)
        both += int(sa and sb)
        a_only += int(sa and not sb)
        b_only += int(sb and not sa)
        neither += int((not sa) and (not sb))
        a_cost += cost(ar)
        b_cost += cost(br)
        a_tokens += tokens(ar)
        b_tokens += tokens(br)
        a_partial += partial(ar)
        b_partial += partial(br)
        if len(examples) < 4 and sa != sb:
            examples.append({"cell": key, a: ar["_path"], b: br["_path"]})
    n = len(keys)
    return {
        "cells": n,
        "a_solves": both + a_only,
        "b_solves": both + b_only,
        "a_only": a_only,
        "b_only": b_only,
        "both": both,
        "neither": neither,
        "a_cost": round(a_cost, 6),
        "b_cost": round(b_cost, 6),
        "b_minus_a_cost": round(b_cost - a_cost, 6),
        "b_minus_a_tokens": b_tokens - a_tokens,
        "mean_partial_delta_b_minus_a": round((b_partial - a_partial) / n, 6) if n else None,
        "discordant_examples": examples,
    }


def doc_for_config(config: str, docs: dict[str, dict[str, Any]], vectors: dict[str, list[float]]) -> str | None:
    explicit = f"{config}::explicit_prompt"
    surface = f"{config}::prompt_surface"
    if explicit in docs and explicit in vectors:
        return explicit
    if surface in docs and surface in vectors:
        return surface
    return None


def build() -> dict[str, Any]:
    emb = load_json(EMBED_ANALYSIS)
    vectors = load_json(EMBED_VECTORS)["vectors"]
    corpus = load_json(CORPUS)
    rows_by_config = {row["config"]: row for row in corpus["rows"]}
    docs = {doc["id"]: doc for doc in emb["documents"]}

    included_rows = [
        row for row in corpus["rows"]
        if row["overlap_cells"] == 108 and row["category"] in INCLUDED_CATEGORIES
    ]
    included_rows.sort(key=lambda r: (r["category"] != PROMPT_ONLY, -r["solve_delta"], r["cost_delta"]))
    included_configs = [row["config"] for row in included_rows]
    doc_ids = {cfg: doc_for_config(cfg, docs, vectors) for cfg in included_configs}
    doc_ids = {cfg: doc_id for cfg, doc_id in doc_ids.items() if doc_id}

    pairs = []
    for i, a in enumerate(doc_ids):
        for b in list(doc_ids)[i + 1:]:
            a_doc = docs[doc_ids[a]]
            b_doc = docs[doc_ids[b]]
            a_row = rows_by_config[a]
            b_row = rows_by_config[b]
            sim = cosine(vectors[doc_ids[a]], vectors[doc_ids[b]])
            pw = pairwise_cells(a, b)
            pairs.append({
                "a_config": a,
                "b_config": b,
                "a_category": a_row["category"],
                "b_category": b_row["category"],
                "a_doc_id": doc_ids[a],
                "b_doc_id": doc_ids[b],
                "a_paths": a_doc.get("paths", []),
                "b_paths": b_doc.get("paths", []),
                "similarity": round(sim, 6),
                "a_solve_delta_vs_clean": a_row["solve_delta"],
                "b_solve_delta_vs_clean": b_row["solve_delta"],
                "solve_delta_gap": abs(a_row["solve_delta"] - b_row["solve_delta"]),
                "a_cost_delta_vs_clean": a_row["cost_delta"],
                "b_cost_delta_vs_clean": b_row["cost_delta"],
                "cost_delta_gap": abs(a_row["cost_delta"] - b_row["cost_delta"]),
                "pairwise": pw,
            })
    pairs.sort(key=lambda p: (-p["similarity"], -p["solve_delta_gap"], -p["cost_delta_gap"]))

    pure_pairs = [p for p in pairs if p["a_category"] == PROMPT_ONLY and p["b_category"] == PROMPT_ONLY]
    tool_pairs = [p for p in pairs if p["a_category"] == PROMPT_TOOL and p["b_category"] == PROMPT_TOOL]
    cross_pairs = [p for p in pairs if {p["a_category"], p["b_category"]} == {PROMPT_ONLY, PROMPT_TOOL}]

    excluded = [row for row in corpus["rows"] if row["overlap_cells"] == 108 and row["category"] not in INCLUDED_CATEGORIES]
    excluded.sort(key=lambda r: (-r["solve_delta"], r["config"]))

    return {
        "inputs": {
            "prompt_embedding_analysis": str(EMBED_ANALYSIS.relative_to(ROOT)),
            "prompt_embeddings": str(EMBED_VECTORS.relative_to(ROOT)),
            "corpus_overlap": str(CORPUS.relative_to(ROOT)),
            "result_root": str(RESULT_ROOT.relative_to(ROOT)),
        },
        "included_categories": sorted(INCLUDED_CATEGORIES),
        "included_configs": included_rows,
        "pairs": pairs,
        "pure_prompt_pairs": pure_pairs,
        "prompt_tool_surface_pairs": tool_pairs,
        "cross_prompt_tool_pairs": cross_pairs,
        "excluded_behavioral_or_nonprompt_configs": excluded,
    }


def tag_for(row: dict[str, Any]) -> str:
    if row["category"] == PROMPT_ONLY and row["solve_delta"] > 0:
        return "good"
    if row["category"] == PROMPT_TOOL:
        return "caution"
    return "neutral"


def config_row(row: dict[str, Any]) -> str:
    caveat = "clean Pi prompt-only" if row["category"] == PROMPT_ONLY else "OMP prompt + tool-surface"
    return f'''<tr><td><span class="tag {tag_for(row)}">{e(row['config'])}</span><div class="muted">{e(caveat)}</div></td><td>{row['solves_on_overlap']}/108</td><td><b>{row['solve_delta']:+d}</b><div class="muted">{row['other_only']} gains / {row['clean_only']} losses vs clean</div></td><td>{money(row['cost_delta'])}</td><td>{money(row['cost_per_net_solve']) if row['cost_per_net_solve'] is not None else '—'}</td><td>{'<br>'.join(f'<code>{e(p)}</code>' for p in row['prompt_files'])}</td></tr>'''


def pair_label(p: dict[str, Any]) -> tuple[str, str, int, int, float]:
    pw = p["pairwise"]
    a, b = p["a_config"], p["b_config"]
    # Prefer solve winner; if tied, prefer cheaper total direct cost.
    if pw["a_solves"] > pw["b_solves"]:
        return a, b, pw["a_solves"], pw["b_solves"], pw["a_cost"] - pw["b_cost"]
    if pw["b_solves"] > pw["a_solves"]:
        return b, a, pw["b_solves"], pw["a_solves"], pw["b_cost"] - pw["a_cost"]
    if pw["a_cost"] <= pw["b_cost"]:
        return a, b, pw["a_solves"], pw["b_solves"], pw["a_cost"] - pw["b_cost"]
    return b, a, pw["b_solves"], pw["a_solves"], pw["b_cost"] - pw["a_cost"]


def pair_row(p: dict[str, Any]) -> str:
    winner, loser, w_solves, l_solves, cost_vs_neighbor = pair_label(p)
    pw = p["pairwise"]
    if winner == p["a_config"]:
        unique = pw["a_only"]
        lost = pw["b_only"]
    else:
        unique = pw["b_only"]
        lost = pw["a_only"]
    cls = "good" if w_solves > l_solves else "caution"
    return f'''<tr><td><b>{e(winner)}</b><div class="muted">vs {e(loser)}</div></td><td>{p['similarity']:.3f}</td><td><span class="tag {cls}">{w_solves-l_solves:+d} solves</span><div class="muted">{w_solves}/{pw['cells']} vs {l_solves}/{pw['cells']}</div></td><td>{unique} unique wins / {lost} unique losses</td><td>{money(cost_vs_neighbor)}</td><td>{money(p['cost_delta_gap'])}</td><td>{e('; '.join(p['a_paths'][:2]))}<br><span class="muted">↔</span><br>{e('; '.join(p['b_paths'][:2]))}</td></tr>'''


def excluded_row(row: dict[str, Any]) -> str:
    return f'''<tr><td><code>{e(row['config'])}</code></td><td>{e(row['category'])}</td><td>{row['solve_delta']:+d}</td><td>{money(row['cost_delta'])}</td><td>{e('behavioral wrapper / extension / memory projection; not prioritized for prompt-shape decomposition')}</td></tr>'''


def bar_chart(rows: list[dict[str, Any]]) -> str:
    width, height = 820, 270
    left, right, top, bottom = 180, 30, 18, 32
    plot_w = width - left - right
    usable = rows[:9]
    max_delta = max([abs(r["solve_delta"]) for r in usable] + [1])
    row_h = (height - top - bottom) / max(len(usable), 1)
    zero = left + plot_w * 0.28
    scale = (plot_w * 0.68) / max_delta
    pieces = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Prompt-shaped solve deltas versus clean low"><rect width="{width}" height="{height}" rx="18" fill="#091220"/><line x1="{zero:.1f}" x2="{zero:.1f}" y1="{top}" y2="{height-bottom}" stroke="#9fb0c9"/>']
    for i, r in enumerate(usable):
        y = top + i * row_h + row_h * 0.22
        x0 = zero if r["solve_delta"] >= 0 else zero + r["solve_delta"] * scale
        w = abs(r["solve_delta"] * scale)
        color = "#34d399" if r["category"] == PROMPT_ONLY else "#fbbf24"
        pieces.append(f'<text x="12" y="{y+12:.1f}" fill="#dbeafe" font-size="11">{e(r["config"][:34])}</text>')
        pieces.append(f'<rect x="{x0:.1f}" y="{y:.1f}" width="{w:.1f}" height="14" rx="7" fill="{color}" opacity="0.86"/>')
        pieces.append(f'<text x="{x0+w+6:.1f}" y="{y+12:.1f}" fill="#dbeafe" font-size="11">{r["solve_delta"]:+d}</text>')
    pieces.append(f'<text x="{zero-30:.1f}" y="{height-8}" fill="#9fb0c9" font-size="11">clean low</text></svg>')
    return ''.join(pieces)


def render(data: dict[str, Any]) -> str:
    rows = data["included_configs"]
    pure_rows = [r for r in rows if r["category"] == PROMPT_ONLY]
    tool_rows = [r for r in rows if r["category"] == PROMPT_TOOL]
    best_pure = max(pure_rows, key=lambda r: (r["solve_delta"], -r["cost_delta"]))
    pure_pairs = data["pure_prompt_pairs"]
    tool_pairs = data["prompt_tool_surface_pairs"]
    excluded = data["excluded_behavioral_or_nonprompt_configs"]
    html_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low prompt-shaped divergence</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#173c54,#07111f 43%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}main{{max-width:1320px;margin:0 auto;padding:36px 22px 64px}}.hero,.card,.callout{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:22px}}.hero{{padding:32px;background:linear-gradient(135deg,rgba(52,211,153,.16),rgba(15,29,49,.94) 45%,rgba(251,191,36,.10))}}h1{{font-size:clamp(34px,5vw,64px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}}h2{{margin:34px 0 12px}}p,li{{color:#dbe7fb;max-width:1040px}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:30px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.pills{{display:flex;gap:10px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px;padding:1px 5px;font-size:12px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.chart{{padding:12px;background:rgba(9,18,32,.55);border:1px solid var(--line);border-radius:20px;overflow:hidden}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Prompt-shaped subset · GPT-5.5 low · excludes behavioral wrappers</div><h1>Now the priority is static prompt shape, not every high-performing wrapper.</h1><p>This view answers the narrowed question: among configs that are essentially variations on top-of-context/system-prompt text, which prompt shapes help, which combinations interfere, and which apparent prompt results are confounded by tool-surface changes?</p><div class="pills"><span class="pill good">{len(pure_rows)} clean-Pi prompt-only configs</span><span class="pill caution">{len(tool_rows)} OMP prompt/tool-surface configs</span><span class="pill bad">behavioral wrappers excluded from primary ranking</span><span class="pill neutral">full 108-cell overlap only</span></div><div class="src">Inputs: <code>{e(data['inputs']['prompt_embedding_analysis'])}</code>, <code>{e(data['inputs']['prompt_embeddings'])}</code>, <code>{e(data['inputs']['corpus_overlap'])}</code>, and direct <code>result.json</code> cells.</div></section>
<div class="stats"><div class="stat"><b>{best_pure['solve_delta']:+d}</b><span>best clean-Pi prompt-only delta: {e(best_pure['config'])}</span></div><div class="stat"><b>{pure_pairs[0]['similarity']:.3f}</b><span>closest clean prompt pair: {e(pure_pairs[0]['a_config'])} ↔ {e(pure_pairs[0]['b_config'])}</span></div><div class="stat"><b>{pure_pairs[0]['solve_delta_gap']}</b><span>solve gap in closest prompt pair</span></div><div class="stat"><b>{len(excluded)}</b><span>full-overlap behavioral/non-prompt configs demoted</span></div></div>
<section class="callout good"><h2>Reprioritized verdict</h2><p>Yes: <code>codebase-memory-max-pi-codex-goal</code> is a strong result, but it is not the right lead example for prompt-shape analysis. In the clean-Pi prompt-only subset, the important divergence is <b>workflow checklist alone</b> versus <b>engineer preamble + workflow checklist</b>: the semantically close pair has cosine <b>{pure_pairs[0]['similarity']:.3f}</b>, but checklist-only wins <b>35 vs 31</b> direct solves. The prompt-shaped hypothesis becomes: concrete task workflow helps; generic competence preamble can interfere when layered on top.</p></section>
<div class="grid"><section class="card"><h2>Prompt-shaped solve deltas</h2><div class="chart">{bar_chart(rows)}</div></section><section class="callout caution"><h2>Scope guardrail</h2><ul><li>Primary claims use only <b>clean-Pi prompt-only</b> rows: system preamble and/or orchestration markdown, no behavior-changing extension.</li><li>OMP rows are shown separately because they are system-prompt shaped, but their tool schemas/harness differ.</li><li>pi-codex-goal, codebase-memory, projected memory, recursive, workflow agents, advisor, codegraph, and ponytail are excluded from prompt-shape conclusions.</li></ul></section></div>
<h2>Included prompt-shaped configs</h2><table><thead><tr><th>Config</th><th>Solves</th><th>Δ vs clean low</th><th>Cost Δ</th><th>$/net solve</th><th>Prompt files</th></tr></thead><tbody>{''.join(config_row(r) for r in rows)}</tbody></table>
<h2>Clean-Pi prompt-only neighbor pairs</h2><p>This is the priority table for pulling apart prompt wording and composition.</p><table><thead><tr><th>Winner / cheaper tie</th><th>Cosine</th><th>Direct solve gap</th><th>Discordant cells</th><th>Cost vs neighbor</th><th>Cost-gap vs clean</th><th>Prompt files</th></tr></thead><tbody>{''.join(pair_row(p) for p in pure_pairs[:12])}</tbody></table>
<h2>OMP prompt/tool-surface neighbor pairs</h2><p>These are prompt-shaped but not clean-Pi prompt-only. Keep them useful as a tool-schema confound check, not as pure prompt evidence.</p><table><thead><tr><th>Winner / cheaper tie</th><th>Cosine</th><th>Direct solve gap</th><th>Discordant cells</th><th>Cost vs neighbor</th><th>Cost-gap vs clean</th><th>Prompt files</th></tr></thead><tbody>{''.join(pair_row(p) for p in tool_pairs[:8])}</tbody></table>
<h2>Behavioral/non-prompt configs explicitly demoted</h2><p>These may be interesting separately, but not for the current prompt-shape decomposition.</p><table><thead><tr><th>Config</th><th>Category</th><th>Δ solves</th><th>Cost Δ</th><th>Why demoted</th></tr></thead><tbody>{''.join(excluded_row(r) for r in excluded)}</tbody></table>
<section class="callout neutral"><h2>Next prompt-shaped questions</h2><ol><li>Why does <code>baseline-wf-only</code> beat <code>baseline-preamble-orchestration-wf</code>? Inspect direct discordant cells and traces for over-scaffolding, extra turns, or different verification behavior.</li><li>Why is <code>baseline-preamble-orchestration</code> nearly as good as <code>baseline-preamble-only</code> while costing less? The neutral orchestration may shorten or stabilize trajectories.</li><li>Does the concrete checklist’s “create a reproduction script” line drive the gain, or is the six-step structure itself enough? That requires a smaller ablation.</li><li>For OMP no-PROJECT prompts, separate prompt text from tool schema bytes before attributing any lift to wording.</li></ol></section>
<section class="callout"><h2>Evidence</h2><p>Generated JSON: <code>{e(OUT_JSON.relative_to(ROOT))}</code>. Solve counts use <code>reward_binary == 1</code>. All primary rows have 108 overlapping cells against clean GPT-5.5:low baseline.</p></section>
</main></body></html>'''
    return html_doc


def main() -> None:
    data = build()
    OUT_JSON.write_text(json.dumps(data, indent=2))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(render(data))
    print("wrote", OUT_JSON.relative_to(ROOT), OUT_JSON.stat().st_size)
    print("wrote", OUT_HTML.relative_to(ROOT), OUT_HTML.stat().st_size)


if __name__ == "__main__":
    main()
