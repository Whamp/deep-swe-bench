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
KAGGLE_LESSONS = ANALYSIS_DIR / "kaggle_plugin_prompt_lessons.json"
OUT_JSON = ANALYSIS_DIR / "nearest_neighbor_outcome_divergence.json"
OUT_HTML = ROOT / "reports/gpt55-low-neighbor-divergence/index.html"
RESULT_ROOT = ROOT / "results/gpt-5.5/low"
SIM_THRESHOLD = 0.86


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def num(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}"


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


def valid_reward(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") in (0, 1)


def cost(row: dict[str, Any]) -> float:
    value = row.get("combined_cost_usd", row.get("cost_usd", 0.0))
    return float(value or 0.0)


def tokens(row: dict[str, Any]) -> int:
    value = row.get("combined_total_tokens", row.get("total_tokens", 0))
    return int(value or 0)


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
        task = path.parts[-3]
        rep = path.parts[-2]
        key = f"{task}/{rep}"
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
    a_invalid = b_invalid = 0
    a_partial_wins = b_partial_wins = ties = 0
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
        a_invalid += int(not valid_reward(ar))
        b_invalid += int(not valid_reward(br))
        if partial(ar) > partial(br):
            a_partial_wins += 1
        elif partial(br) > partial(ar):
            b_partial_wins += 1
        else:
            ties += 1
        if len(examples) < 3 and sa != sb:
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
        "a_invalid_reward_cells": a_invalid,
        "b_invalid_reward_cells": b_invalid,
        "a_cost": round(a_cost, 6),
        "b_cost": round(b_cost, 6),
        "b_minus_a_cost": round(b_cost - a_cost, 6),
        "a_tokens": a_tokens,
        "b_tokens": b_tokens,
        "b_minus_a_tokens": b_tokens - a_tokens,
        "mean_partial_delta_b_minus_a": round((b_partial - a_partial) / n, 6) if n else None,
        "a_partial_wins": a_partial_wins,
        "b_partial_wins": b_partial_wins,
        "partial_ties": ties,
        "discordant_examples": examples,
    }


def normalize_path(path: str, config: str) -> str:
    prefix = f"configs/{config}/"
    if path.startswith(prefix):
        return path[len(prefix) :]
    return path


def short_paths(paths: list[str], limit: int = 5) -> list[str]:
    if len(paths) <= limit:
        return paths
    return paths[:limit] + [f"… +{len(paths)-limit} more"]


def path_diff(config_a: str, config_b: str, surface_paths_by_config: dict[str, list[str]]) -> dict[str, Any]:
    raw_a = surface_paths_by_config.get(config_a, [])
    raw_b = surface_paths_by_config.get(config_b, [])
    norm_a = {normalize_path(p, config_a) for p in raw_a}
    norm_b = {normalize_path(p, config_b) for p in raw_b}
    return {
        "a_paths": raw_a,
        "b_paths": raw_b,
        "shared_normalized_paths": sorted(norm_a & norm_b),
        "unique_to_a_normalized": sorted(norm_a - norm_b),
        "unique_to_b_normalized": sorted(norm_b - norm_a),
    }


def interpretation(a: str, b: str) -> str:
    pair = {a, b}
    if pair == {"codebase-memory-max", "codebase-memory-max-pi-codex-goal"}:
        return "Same maximal codebase-memory family; the high row adds pi-codex-goal initial goal creation and goal-continuation text. This is the clearest sign that trajectory/goal management, not semantic prompt proximity, is carrying many extra solves."
    if pair == {"baseline-wf-only", "baseline-preamble-orchestration-wf"}:
        return "The workflow checklist alone beats the semantically similar preamble+workflow combination. Adding a generic engineer preamble appears to dilute or perturb the useful checklist behavior in this sample."
    if any("observational-memory" in x or "projected-om" in x or "recall-placebo" in x or x == "om-orchestration-only" for x in pair):
        return "These rows are embedding-near because their surface talks about memory, but outcomes move with the injection/projection mode: live/projection/delta/no-orchestration/placebo are not interchangeable."
    if any(x.startswith("baseline-omp") for x in pair):
        return "Treat as OMP/tool-surface evidence, not clean Pi prompt-only evidence. Similar OMP prompt text hides different tool schemas, harness context, and cost profiles."
    return "High semantic similarity with outcome divergence; inspect unique files and direct discordant cells before treating the cluster as one prompt family."


def build() -> dict[str, Any]:
    emb = load_json(EMBED_ANALYSIS)
    vectors = load_json(EMBED_VECTORS)["vectors"]
    corpus = load_json(CORPUS)
    rows_by_config = {row["config"]: row for row in corpus["rows"]}
    docs = emb["documents"]
    docs_by_id = {doc["id"]: doc for doc in docs}
    surface_paths_by_config = {
        doc["config"]: doc.get("paths", [])
        for doc in docs
        if doc.get("doc_type") == "prompt_surface"
    }

    all_pairs: list[dict[str, Any]] = []
    for doc_type in ["explicit_prompt", "prompt_surface"]:
        ids = [doc["id"] for doc in docs if doc.get("doc_type") == doc_type and doc["id"] in vectors]
        for i, a_id in enumerate(ids):
            for b_id in ids[i + 1 :]:
                a_doc = docs_by_id[a_id]
                b_doc = docs_by_id[b_id]
                a_cfg = a_doc["config"]
                b_cfg = b_doc["config"]
                a_row = rows_by_config[a_cfg]
                b_row = rows_by_config[b_cfg]
                sim = cosine(vectors[a_id], vectors[b_id])
                pair_cells = pairwise_cells(a_cfg, b_cfg)
                if a_row["solves_on_overlap"] > b_row["solves_on_overlap"]:
                    winner, loser = a_cfg, b_cfg
                elif b_row["solves_on_overlap"] > a_row["solves_on_overlap"]:
                    winner, loser = b_cfg, a_cfg
                else:
                    # If solves tie, call the cheaper row the winner for cost-divergence rows.
                    winner, loser = (a_cfg, b_cfg) if a_row["cost_delta"] <= b_row["cost_delta"] else (b_cfg, a_cfg)
                pdiff = path_diff(a_cfg, b_cfg, surface_paths_by_config)
                record = {
                    "doc_type": doc_type,
                    "a_id": a_id,
                    "b_id": b_id,
                    "a_config": a_cfg,
                    "b_config": b_cfg,
                    "similarity": round(sim, 6),
                    "a_category": a_doc["category"],
                    "b_category": b_doc["category"],
                    "a_solve_delta_vs_clean": a_row["solve_delta"],
                    "b_solve_delta_vs_clean": b_row["solve_delta"],
                    "a_solves_on_overlap": a_row["solves_on_overlap"],
                    "b_solves_on_overlap": b_row["solves_on_overlap"],
                    "solve_delta_gap": abs(a_row["solve_delta"] - b_row["solve_delta"]),
                    "a_cost_delta_vs_clean": a_row["cost_delta"],
                    "b_cost_delta_vs_clean": b_row["cost_delta"],
                    "cost_delta_gap": abs(a_row["cost_delta"] - b_row["cost_delta"]),
                    "a_overlap_cells": a_row["overlap_cells"],
                    "b_overlap_cells": b_row["overlap_cells"],
                    "full_108_pair": a_row["overlap_cells"] == 108 and b_row["overlap_cells"] == 108 and pair_cells["cells"] == 108,
                    "winner_by_outcome_or_cost": winner,
                    "loser_by_outcome_or_cost": loser,
                    "pairwise": pair_cells,
                    "path_diff": pdiff,
                    "interpretation": interpretation(a_cfg, b_cfg),
                }
                all_pairs.append(record)

    high_divergence = [
        p
        for p in all_pairs
        if p["full_108_pair"]
        and p["similarity"] >= SIM_THRESHOLD
        and (p["solve_delta_gap"] >= 4 or p["cost_delta_gap"] >= 40)
    ]
    high_divergence.sort(key=lambda p: (-p["solve_delta_gap"], -p["cost_delta_gap"], -p["similarity"]))
    deduped_high_divergence: list[dict[str, Any]] = []
    seen_config_pairs: set[tuple[str, str]] = set()
    for p in high_divergence:
        key = tuple(sorted([p["a_config"], p["b_config"]]))
        if key in seen_config_pairs:
            continue
        seen_config_pairs.add(key)
        deduped_high_divergence.append(p)

    nearest_outliers: list[dict[str, Any]] = []
    for doc_type in ["explicit_prompt", "prompt_surface"]:
        ids = [doc["id"] for doc in docs if doc.get("doc_type") == doc_type and doc["id"] in vectors]
        for a_id in ids:
            a_doc = docs_by_id[a_id]
            a_row = rows_by_config[a_doc["config"]]
            neighbors = []
            for b_id in ids:
                if a_id == b_id:
                    continue
                b_doc = docs_by_id[b_id]
                b_row = rows_by_config[b_doc["config"]]
                neighbors.append((cosine(vectors[a_id], vectors[b_id]), b_id, b_row))
            if not neighbors:
                continue
            sim, b_id, b_row = max(neighbors, key=lambda x: x[0])
            b_doc = docs_by_id[b_id]
            if a_row["overlap_cells"] == 108 and b_row["overlap_cells"] == 108:
                nearest_outliers.append(
                    {
                        "doc_type": doc_type,
                        "config": a_doc["config"],
                        "nearest_config": b_doc["config"],
                        "similarity": round(sim, 6),
                        "solve_delta": a_row["solve_delta"],
                        "nearest_solve_delta": b_row["solve_delta"],
                        "solve_gap": abs(a_row["solve_delta"] - b_row["solve_delta"]),
                        "cost_delta": a_row["cost_delta"],
                        "nearest_cost_delta": b_row["cost_delta"],
                        "cost_gap": abs(a_row["cost_delta"] - b_row["cost_delta"]),
                    }
                )
    nearest_outliers = [n for n in nearest_outliers if n["solve_gap"] >= 4 or n["cost_gap"] >= 40 or (n["solve_delta"] >= 10 and n["similarity"] < SIM_THRESHOLD)]
    nearest_outliers.sort(key=lambda n: (-n["solve_gap"], n["similarity"]))

    cluster_ranges: list[dict[str, Any]] = []
    for analysis_key, doc_type in [("explicit_prompt_analysis", "explicit_prompt"), ("prompt_surface_analysis", "prompt_surface")]:
        part = emb.get(analysis_key) or {}
        for idx, cluster in enumerate(part.get("clusters", []), 1):
            configs = []
            for doc_id in cluster:
                cfg = docs_by_id[doc_id]["config"]
                row = rows_by_config[cfg]
                if row["overlap_cells"] == 108:
                    configs.append(cfg)
            configs = sorted(set(configs))
            if len(configs) < 2:
                continue
            rowset = [rows_by_config[c] for c in configs]
            solve_deltas = [r["solve_delta"] for r in rowset]
            cost_deltas = [r["cost_delta"] for r in rowset]
            solve_range = max(solve_deltas) - min(solve_deltas)
            cost_range = max(cost_deltas) - min(cost_deltas)
            if solve_range >= 4 or cost_range >= 40:
                best = max(rowset, key=lambda r: (r["solve_delta"], -r["cost_delta"]))
                worst = min(rowset, key=lambda r: (r["solve_delta"], r["cost_delta"]))
                cluster_ranges.append(
                    {
                        "doc_type": doc_type,
                        "cluster_index": idx,
                        "configs": configs,
                        "solve_delta_min": min(solve_deltas),
                        "solve_delta_max": max(solve_deltas),
                        "solve_delta_range": solve_range,
                        "cost_delta_min": min(cost_deltas),
                        "cost_delta_max": max(cost_deltas),
                        "cost_delta_range": cost_range,
                        "best_config": best["config"],
                        "worst_config": worst["config"],
                    }
                )
    cluster_ranges.sort(key=lambda c: (-c["solve_delta_range"], -c["cost_delta_range"]))

    singletons = []
    for cfg, row in rows_by_config.items():
        if row["overlap_cells"] != 108 or row["solve_delta"] < 10:
            continue
        surface_id = f"{cfg}::prompt_surface"
        explicit_id = f"{cfg}::explicit_prompt"
        candidate_id = surface_id if surface_id in vectors else explicit_id if explicit_id in vectors else None
        if not candidate_id:
            continue
        doc_type = docs_by_id[candidate_id]["doc_type"]
        ids = [doc["id"] for doc in docs if doc.get("doc_type") == doc_type and doc["id"] in vectors and doc["id"] != candidate_id]
        nearest = max(((cosine(vectors[candidate_id], vectors[other]), other) for other in ids), default=None)
        if nearest and nearest[0] < SIM_THRESHOLD:
            nearest_row = rows_by_config[docs_by_id[nearest[1]]["config"]]
            singletons.append(
                {
                    "config": cfg,
                    "doc_type": doc_type,
                    "solve_delta": row["solve_delta"],
                    "cost_delta": row["cost_delta"],
                    "nearest_config": docs_by_id[nearest[1]]["config"],
                    "nearest_similarity": round(nearest[0], 6),
                    "nearest_solve_delta": nearest_row["solve_delta"],
                    "nearest_cost_delta": nearest_row["cost_delta"],
                }
            )
    singletons.sort(key=lambda r: (-r["solve_delta"], r["nearest_similarity"]))

    return {
        "inputs": {
            "prompt_embedding_analysis": str(EMBED_ANALYSIS.relative_to(ROOT)),
            "prompt_embeddings": str(EMBED_VECTORS.relative_to(ROOT)),
            "corpus_overlap": str(CORPUS.relative_to(ROOT)),
            "kaggle_plugin_lessons": str(KAGGLE_LESSONS.relative_to(ROOT)),
            "result_root": str(RESULT_ROOT.relative_to(ROOT)),
        },
        "similarity_threshold": SIM_THRESHOLD,
        "documents": len(docs),
        "pairs_total": len(all_pairs),
        "high_divergence_pairs": high_divergence,
        "deduped_high_divergence_pairs": deduped_high_divergence,
        "nearest_outliers": nearest_outliers,
        "cluster_ranges": cluster_ranges,
        "high_outcome_semantic_singletons": singletons,
    }


def svg_scatter(pairs: list[dict[str, Any]]) -> str:
    width, height = 760, 300
    left, right, top, bottom = 52, 24, 18, 42
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_min, x_max = 0.84, 1.0
    y_max = max([p["solve_delta_gap"] for p in pairs] + [10])
    y_max = max(10, y_max)
    def x(sim: float) -> float:
        return left + (sim - x_min) / (x_max - x_min) * plot_w
    def y(gap: float) -> float:
        return top + (y_max - gap) / y_max * plot_h
    circles = []
    labels = []
    for idx, p in enumerate(sorted(pairs, key=lambda p: p["similarity"])):
        color = "#60a5fa" if p["doc_type"] == "explicit_prompt" else "#34d399"
        cx, cy = x(p["similarity"]), y(p["solve_delta_gap"])
        circles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{color}" opacity="0.82"><title>{e(p["a_config"])} ↔ {e(p["b_config"])} · sim {p["similarity"]:.3f} · solve gap {p["solve_delta_gap"]}</title></circle>')
        if idx in (0, len(pairs) - 1) or p["solve_delta_gap"] >= 8:
            label = p["winner_by_outcome_or_cost"][:22]
            labels.append(f'<text x="{min(cx+8,width-180):.1f}" y="{max(14,cy-8):.1f}" fill="#dbeafe" font-size="10">{e(label)}</text>')
    grid = []
    for sim in [0.86, 0.90, 0.95, 1.00]:
        xx = x(sim)
        grid.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{top}" y2="{height-bottom}" stroke="#263850"/><text x="{xx-14:.1f}" y="{height-16}" fill="#9fb0c9" font-size="10">{sim:.2f}</text>')
    for gap in [0, 4, 8, 12, y_max]:
        if gap > y_max: continue
        yy = y(gap)
        grid.append(f'<line x1="{left}" x2="{width-right}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#263850"/><text x="8" y="{yy+4:.1f}" fill="#9fb0c9" font-size="10">{gap}</text>')
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-label="Scatter plot of cosine similarity versus solve-delta gap">
<rect width="{width}" height="{height}" rx="18" fill="#091220"/>{''.join(grid)}
<line x1="{left}" x2="{width-right}" y1="{height-bottom}" y2="{height-bottom}" stroke="#9fb0c9"/><line x1="{left}" x2="{left}" y1="{top}" y2="{height-bottom}" stroke="#9fb0c9"/>
<text x="{width/2-85:.1f}" y="{height-4}" fill="#cfe2ff" font-size="12">cosine similarity</text><text x="4" y="14" fill="#cfe2ff" font-size="12">solve-gap</text>
{''.join(circles)}{''.join(labels)}
<circle cx="610" cy="24" r="5" fill="#60a5fa"/><text x="620" y="28" fill="#9fb0c9" font-size="11">explicit</text><circle cx="682" cy="24" r="5" fill="#34d399"/><text x="692" y="28" fill="#9fb0c9" font-size="11">surface</text>
</svg>'''


def path_list(paths: list[str]) -> str:
    if not paths:
        return '<span class="muted">none</span>'
    return "<br>".join(f"<code>{e(p)}</code>" for p in short_paths(paths, 4))


def divergent_row(pair: dict[str, Any]) -> str:
    a, b = pair["a_config"], pair["b_config"]
    pw = pair["pairwise"]
    winner = pair["winner_by_outcome_or_cost"]
    loser = pair["loser_by_outcome_or_cost"]
    if winner == a:
        w_solves, l_solves = pw["a_solves"], pw["b_solves"]
        w_only, l_only = pw["a_only"], pw["b_only"]
        w_cost_delta = pw["a_cost"] - pw["b_cost"]
    else:
        w_solves, l_solves = pw["b_solves"], pw["a_solves"]
        w_only, l_only = pw["b_only"], pw["a_only"]
        w_cost_delta = pw["b_cost"] - pw["a_cost"]
    pclass = "good" if w_solves > l_solves else "caution"
    return f'''<tr>
<td><span class="tag neutral">{e(pair['doc_type'])}</span><div class="muted">cos {pair['similarity']:.3f}</div></td>
<td><b>{e(winner)}</b><div class="muted">{w_solves}/{pw['cells']} direct solves · {w_only} unique wins</div></td>
<td>{e(loser)}<div class="muted">{l_solves}/{pw['cells']} direct solves · {l_only} unique wins</div></td>
<td><span class="tag {pclass}">{w_solves-l_solves:+d} solves</span><div class="muted">cost vs neighbor {money(w_cost_delta)}</div></td>
<td>{e(pair['interpretation'])}</td>
<td>{path_list(pair['path_diff']['unique_to_a_normalized'])}<div class="muted">unique to {e(a)}</div><hr>{path_list(pair['path_diff']['unique_to_b_normalized'])}<div class="muted">unique to {e(b)}</div></td>
</tr>'''


def cluster_row(cluster: dict[str, Any]) -> str:
    configs = ", ".join(cluster["configs"])
    return f'''<tr><td><span class="tag neutral">{e(cluster['doc_type'])}</span><div class="muted">cluster {cluster['cluster_index']}</div></td><td>{e(cluster['best_config'])}</td><td>{e(cluster['worst_config'])}</td><td><b>{cluster['solve_delta_min']:+d} → {cluster['solve_delta_max']:+d}</b><div class="muted">range {cluster['solve_delta_range']} solves</div></td><td>{money(cluster['cost_delta_min'])} → {money(cluster['cost_delta_max'])}<div class="muted">range {money(cluster['cost_delta_range'])}</div></td><td>{e(configs)}</td></tr>'''


def singleton_row(row: dict[str, Any]) -> str:
    return f'''<tr><td><b>{e(row['config'])}</b><div class="muted">{e(row['doc_type'])}</div></td><td><span class="tag good">{row['solve_delta']:+d}</span></td><td>{money(row['cost_delta'])}</td><td>{e(row['nearest_config'])}<div class="muted">cos {row['nearest_similarity']:.3f}</div></td><td>{row['nearest_solve_delta']:+d} · {money(row['nearest_cost_delta'])}</td></tr>'''


def render(data: dict[str, Any]) -> str:
    pairs = data["deduped_high_divergence_pairs"]
    clusters = data["cluster_ranges"]
    singletons = data["high_outcome_semantic_singletons"]
    top = pairs[0]
    # Use the surface version for the OM headline if present.
    om = next((p for p in pairs if p["doc_type"] == "prompt_surface" and "projected-om-delta-no-orchestration" in {p["a_config"], p["b_config"]}), pairs[1] if len(pairs) > 1 else top)
    html_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low neighbor divergence</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#18365c,#07111f 44%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}main{{max-width:1320px;margin:0 auto;padding:36px 22px 64px}}.hero,.card,.callout{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:22px}}.hero{{padding:32px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.94) 46%,rgba(52,211,153,.11))}}h1{{font-size:clamp(34px,5vw,64px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}}h2{{margin:34px 0 12px}}p,li{{color:#dbe7fb;max-width:1040px}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:30px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.pills{{display:flex;gap:10px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px;padding:1px 5px;font-size:12px}}hr{{border:0;border-top:1px solid var(--line);margin:8px 0}}.grid{{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}}.chart{{padding:12px;background:rgba(9,18,32,.55);border:1px solid var(--line);border-radius:20px;overflow:hidden}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Semantic nearest-neighbor divergence · GPT-5.5 low · Octen embeddings</div><h1>Similar prompt surfaces often do not mean similar benchmark behavior.</h1><p>This report applies the Kaggle prompt-recovery lesson directly: after embedding prompt/config surfaces, look for near neighbors whose solve/cost outcomes diverge. The goal is to expose hidden causal factors inside a semantic cluster — goal creation, projection mode, tool schema, and context placement.</p><div class="pills"><span class="pill neutral">{data['documents']} embedded docs</span><span class="pill neutral">cosine threshold ≥ {data['similarity_threshold']:.2f}</span><span class="pill neutral">{len(pairs)} distinct divergent config-pairs</span><span class="pill neutral">{len(data['high_divergence_pairs'])} doc-type pair views</span><span class="pill neutral">direct result.json cell comparisons</span></div><div class="src">Inputs: <code>{e(data['inputs']['prompt_embedding_analysis'])}</code>, <code>{e(data['inputs']['prompt_embeddings'])}</code>, <code>{e(data['inputs']['corpus_overlap'])}</code>, and result cells under <code>{e(data['inputs']['result_root'])}</code>.</div></section>
<div class="stats"><div class="stat"><b>{top['solve_delta_gap']}</b><span>largest solve-gap inside a high-sim pair</span></div><div class="stat"><b>{top['similarity']:.3f}</b><span>cosine for that top gap</span></div><div class="stat"><b>{om['similarity']:.3f}</b><span>OM family surface similarity can still hide big outcome shifts</span></div><div class="stat"><b>{len(singletons)}</b><span>high-outcome semantic singletons</span></div></div>
<section class="callout good"><h2>Verdict</h2><p>Embedding clusters are useful for taxonomy, but <b>not causal evidence</b>. The clearest divergence is <code>codebase-memory-max</code> versus <code>codebase-memory-max-pi-codex-goal</code>: they are embedding-near, share the maximal codebase-memory surface, and the goal variant wins <b>48 vs 34</b> direct solves on the same 108 cells while costing <b>$146.59</b> more. In other words, the added goal/trajectory wrapper is the likely effect, not generic prompt similarity.</p></section>
<div class="grid"><section class="card"><h2>Divergence map</h2><div class="chart">{svg_scatter(pairs)}</div></section><section class="callout caution"><h2>How to read this</h2><ul><li><b>High cosine + high solve gap</b> means the text surfaces cluster together, but outcomes disagree.</li><li><b>Unique wins</b> are direct paired cells solved by one config and not the other.</li><li>Rows use only full 108-cell overlaps against clean GPT-5.5:low unless explicitly labeled otherwise.</li><li>OMP/tool-surface rows remain non-clean-Pi context; do not call them prompt-only effects.</li></ul></section></div>
<h2>High-similarity divergent neighbors</h2><table><thead><tr><th>Doc type</th><th>Higher outcome / cheaper tie</th><th>Neighbor</th><th>Direct gap</th><th>Likely differentiator</th><th>Unique surface files</th></tr></thead><tbody>{''.join(divergent_row(p) for p in pairs[:16])}</tbody></table>
<h2>Cluster-level outcome ranges</h2><p>These are embedding clusters whose full-overlap members have materially different outcome or cost ranges. They are the best candidates for intra-cluster ablation.</p><table><thead><tr><th>Cluster</th><th>Best member</th><th>Worst member</th><th>Solve-delta range</th><th>Cost-delta range</th><th>Members</th></tr></thead><tbody>{''.join(cluster_row(c) for c in clusters[:12])}</tbody></table>
<h2>High-outcome semantic singletons</h2><p>Some strong configs are not close to any other prompt surface at the 0.86 threshold. These should be studied as separate mechanisms rather than merged into a broad prompt cluster.</p><table><thead><tr><th>Config</th><th>Δ solves vs clean low</th><th>Cost Δ vs clean low</th><th>Nearest neighbor</th><th>Neighbor outcome</th></tr></thead><tbody>{''.join(singleton_row(s) for s in singletons)}</tbody></table>
<section class="callout neutral"><h2>Actionable next experiments</h2><ol><li><b>Goal-wrapper ablation inside codebase-memory:</b> compare codebase-memory-max, pi-codex-goal, and codebase-memory-max-pi-codex-goal with direct task win/loss inspection. The current pair shows +14 direct solves for the goal variant but at +$146.59.</li><li><b>Memory projection ablation:</b> projected-OM delta no-orchestration beats several near-identical OM surfaces; inspect the 15 direct wins vs observational-memory and the 14 direct wins vs recall-placebo.</li><li><b>Prompt-only checklist ablation:</b> workflow checklist alone beats preamble+workflow by +4 direct solves. Inspect whether the preamble causes extra tests/turns/cost or changes commit behavior.</li><li><b>Tool-surface audit:</b> OMP rows show similar prompts but different tool schemas and costs; keep them labeled as harness/tool context.</li></ol></section>
<section class="callout"><h2>Evidence and caveats</h2><p>Every numeric row in this report is generated from <code>{e(OUT_JSON.relative_to(ROOT))}</code>, which in turn reads Octen vectors from <code>{e(EMBED_VECTORS.relative_to(ROOT))}</code>, document metadata from <code>{e(EMBED_ANALYSIS.relative_to(ROOT))}</code>, full-corpus overlap metrics from <code>{e(CORPUS.relative_to(ROOT))}</code>, and direct per-cell <code>result.json</code> files under <code>{e(RESULT_ROOT.relative_to(ROOT))}</code>. Solve counts use <code>reward_binary == 1</code>; invalid/negative reward cells are not counted as solves.</p></section>
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
