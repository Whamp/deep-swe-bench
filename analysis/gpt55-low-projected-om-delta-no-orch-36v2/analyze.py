#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import statistics as stats
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats as scipy_stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "gpt55-low-projected-om-delta-no-orch-36v2"
MODEL_DIR = ROOT / "results" / "gpt-5.5" / "low"
SUBSET = ROOT / "subsets" / "36_v2.txt"
DIFF = ROOT / "data" / "deepswe-v1.1-task-difficulty.tsv"
TARGET = "projected-om-delta-no-orchestration-gpt54mini-low"
CONFIGS = [
    "baseline",
    "om-orchestration-only",
    "recall-placebo-gpt54mini-low",
    "observational-memory-gpt54mini-low",
    "projected-om-gpt54mini-low",
    "projected-om-delta-gpt54mini-low",
    TARGET,
]
LABELS = {
    "baseline": "clean baseline",
    "om-orchestration-only": "OM sentence only",
    "recall-placebo-gpt54mini-low": "recall placebo",
    "observational-memory-gpt54mini-low": "stock OM workers",
    "projected-om-gpt54mini-low": "projected OM v1",
    "projected-om-delta-gpt54mini-low": "projected OM delta + neutral sentence",
    TARGET: "projected OM delta / no orchestration",
}
LOWER_BETTER = {"combined_total_tokens", "combined_cost_usd", "agent_wall_s", "turns", "tool_calls", "patch_bytes"}


def median(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.median(xs)) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.fmean(xs)) if xs else None


def pct(x):
    return 100.0 * x


def load_subset():
    return [l.strip() for l in SUBSET.read_text().splitlines() if l.strip() and not l.startswith("#")]


def load_difficulty():
    out = {}
    for line in DIFF.read_text().splitlines():
        if not line.strip() or line.startswith("pass_rate"):
            continue
        pass_rate, language, slug, repo, title = line.split("\t")[:5]
        pr = float(pass_rate)
        bucket = "hard" if pr < 33 else "medium" if pr < 66 else "easy"
        out[slug] = {"pass_rate": pr, "language": language, "difficulty": bucket, "title": title, "repository": repo}
    return out


def load_results(config: str, subset: list[str]) -> dict[tuple[str, int], dict[str, Any]]:
    rows = {}
    for task in subset:
        for rep in range(3):
            p = MODEL_DIR / config / task / f"rep{rep}" / "result.json"
            if not p.exists():
                raise FileNotFoundError(p)
            r = json.loads(p.read_text())
            r["result_path"] = str(p.relative_to(ROOT))
            rows[(task, rep)] = r
    return rows


def projection_audit_for_cell(config: str, task: str, rep: int) -> dict[str, Any]:
    cell = MODEL_DIR / config / task / f"rep{rep}"
    p = cell / "pi-agent" / "observational-memory" / "projection" / "projection.ndjson"
    rows = []
    if p.exists():
        for line in p.read_text(errors="ignore").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    injected = [r for r in rows if r.get("injected")]
    session_delta_msgs = 0
    compactions = 0
    folded = 0
    for sp in (cell / "session").glob("*.jsonl"):
        for line in sp.read_text(errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("type") == "custom_message" and row.get("customType") == "om.delta_projection":
                session_delta_msgs += 1
            if row.get("type") == "compaction":
                compactions += 1
            if isinstance(row.get("details"), dict) and row["details"].get("type") == "om.folded":
                folded += 1
    return {
        "projection_rows": len(rows),
        "projection_injected_rows": len(injected),
        "first_injection_ordinal": next((i + 1 for i, r in enumerate(rows) if r.get("injected")), None),
        "injected_observations": sum(int(r.get("observations") or 0) for r in injected),
        "injected_reflections": sum(int(r.get("reflections") or 0) for r in injected),
        "injected_drops": sum(int(r.get("droppedObservations") or 0) for r in injected),
        "injected_chars": sum(int((r.get("contentChars") if r.get("contentChars") is not None else r.get("summaryChars")) or 0) for r in injected),
        "session_delta_messages": session_delta_msgs,
        "compaction_entries": compactions,
        "om_folded_details": folded,
        "payload_shape_mentions": int("payloadShape" in p.read_text(errors="ignore")) if p.exists() else 0,
        "projection_file": str(p.relative_to(ROOT)) if p.exists() else None,
    }


def projection_audits(config: str, subset: list[str]) -> dict[tuple[str, int], dict[str, Any]]:
    return {(t, r): projection_audit_for_cell(config, t, r) for t in subset for r in range(3)}


def summarize(config: str, rows: dict[tuple[str, int], dict[str, Any]], audits=None) -> dict[str, Any]:
    vals = list(rows.values())
    d = {
        "config": config,
        "label": LABELS.get(config, config),
        "n": len(vals),
        "solves": sum(1 for r in vals if r.get("reward_binary") == 1),
        "solve_rate": sum(1 for r in vals if r.get("reward_binary") == 1) / len(vals),
        "mean_partial": mean([r.get("reward_partial") for r in vals]),
        "median_partial": median([r.get("reward_partial") for r in vals]),
        "partial_lt_09": sum(1 for r in vals if (r.get("reward_partial") or 0) < 0.9),
        "partial_ge_099": sum(1 for r in vals if (r.get("reward_partial") or 0) >= 0.99),
        "agent_timeouts": sum(1 for r in vals if r.get("agent_timed_out")),
        "empty_patches": sum(1 for r in vals if (r.get("patch_bytes") or 0) == 0),
        "reward_minus_one": sum(1 for r in vals if r.get("reward_binary") == -1),
        "median_tokens": median([r.get("total_tokens") for r in vals]),
        "median_combined_tokens": median([r.get("combined_total_tokens") for r in vals]),
        "total_tokens": sum(r.get("total_tokens") or 0 for r in vals),
        "total_combined_tokens": sum(r.get("combined_total_tokens") or 0 for r in vals),
        "median_cost": median([r.get("cost_usd") for r in vals]),
        "median_combined_cost": median([r.get("combined_cost_usd") for r in vals]),
        "total_cost": sum(r.get("cost_usd") or 0 for r in vals),
        "total_combined_cost": sum(r.get("combined_cost_usd") or 0 for r in vals),
        "median_wall_s": median([r.get("agent_wall_s") for r in vals]),
        "median_turns": median([r.get("turns") for r in vals]),
        "median_tool_calls": median([r.get("tool_calls") for r in vals]),
        "median_patch_bytes": median([r.get("patch_bytes") for r in vals]),
        "om_worker_calls": sum(r.get("om_worker_calls") or 0 for r in vals),
        "om_worker_tokens": sum(r.get("om_worker_total_tokens") or 0 for r in vals),
        "om_worker_cost": sum(r.get("om_worker_cost_usd") or 0 for r in vals),
        "om_observer_calls": sum(r.get("om_observer_calls") or 0 for r in vals),
        "om_reflector_calls": sum(r.get("om_reflector_calls") or 0 for r in vals),
        "om_dropper_calls": sum(r.get("om_dropper_calls") or 0 for r in vals),
        "f2p_total": sum(r.get("f2p_total") or 0 for r in vals),
        "f2p_passed": sum(r.get("f2p_passed") or 0 for r in vals),
        "p2p_total": sum(r.get("p2p_total") or 0 for r in vals),
        "p2p_passed": sum(r.get("p2p_passed") or 0 for r in vals),
    }
    d["f2p_rate"] = d["f2p_passed"] / d["f2p_total"] if d["f2p_total"] else None
    d["p2p_rate"] = d["p2p_passed"] / d["p2p_total"] if d["p2p_total"] else None
    if audits:
        av = list(audits.values())
        d.update({
            "projection_files": sum(1 for a in av if a["projection_file"]),
            "projection_cells_with_injection": sum(1 for a in av if a["projection_injected_rows"] > 0),
            "projection_injected_rows": sum(a["projection_injected_rows"] for a in av),
            "projection_delta_messages": sum(a["session_delta_messages"] for a in av),
            "projection_injected_chars_total": sum(a["injected_chars"] for a in av),
            "projection_injected_chars_median_cell": median([a["injected_chars"] for a in av]),
            "projection_observations": sum(a["injected_observations"] for a in av),
            "projection_reflections": sum(a["injected_reflections"] for a in av),
            "projection_drops": sum(a["injected_drops"] for a in av),
            "projection_first_injection_median": median([a["first_injection_ordinal"] for a in av if a["first_injection_ordinal"]]),
            "compaction_entries": sum(a["compaction_entries"] for a in av),
            "om_folded_details": sum(a["om_folded_details"] for a in av),
            "payload_shape_mentions": sum(a["payload_shape_mentions"] for a in av),
        })
    return d


def binom_two_sided(k: int, n: int) -> float | None:
    if n == 0:
        return None
    return float(scipy_stats.binomtest(k, n, 0.5, alternative="two-sided").pvalue)


def wilcoxon(xs: list[float]) -> float | None:
    nz = [x for x in xs if abs(x) > 1e-12]
    if len(nz) < 2:
        return None
    try:
        return float(scipy_stats.wilcoxon(nz, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        return None


def paired(base_name: str, other_name: str, all_rows: dict[str, dict[tuple[str, int], dict[str, Any]]], diff: dict[str, Any]) -> dict[str, Any]:
    base = all_rows[base_name]
    other = all_rows[other_name]
    keys = sorted(base)
    deltas = [other[k]["reward_partial"] - base[k]["reward_partial"] for k in keys]
    solve_base = [1 if base[k]["reward_binary"] == 1 else 0 for k in keys]
    solve_other = [1 if other[k]["reward_binary"] == 1 else 0 for k in keys]
    both = sum(1 for b, o in zip(solve_base, solve_other) if b and o)
    base_only = sum(1 for b, o in zip(solve_base, solve_other) if b and not o)
    other_only = sum(1 for b, o in zip(solve_base, solve_other) if o and not b)
    neither = sum(1 for b, o in zip(solve_base, solve_other) if not b and not o)
    discordant = base_only + other_only
    # exact two-sided mcnemar = binom on smaller side
    mcnemar = float(scipy_stats.binomtest(min(base_only, other_only), discordant, 0.5).pvalue) if discordant else None
    res = {
        "base": base_name,
        "other": other_name,
        "base_label": LABELS.get(base_name, base_name),
        "other_label": LABELS.get(other_name, other_name),
        "n": len(keys),
        "solve_base": sum(solve_base),
        "solve_other": sum(solve_other),
        "solve_delta": sum(solve_other) - sum(solve_base),
        "both_solved": both,
        "base_only": base_only,
        "other_only": other_only,
        "neither": neither,
        "mcnemar_p": mcnemar,
        "mean_delta_partial": mean(deltas),
        "median_delta_partial": median(deltas),
        "wilcoxon_partial_p": wilcoxon(deltas),
        "improved_cells": sum(1 for d in deltas if d > 1e-9),
        "worsened_cells": sum(1 for d in deltas if d < -1e-9),
        "tied_cells": sum(1 for d in deltas if abs(d) <= 1e-9),
    }
    for metric in ["combined_total_tokens", "combined_cost_usd", "agent_wall_s", "turns", "tool_calls", "patch_bytes", "om_worker_total_tokens", "om_worker_cost_usd"]:
        ds = [(other[k].get(metric) or 0) - (base[k].get(metric) or 0) for k in keys]
        res[f"median_delta_{metric}"] = median(ds)
        res[f"mean_delta_{metric}"] = mean(ds)
    # rep-level conservative summaries: n=3 paired by rep aggregate.
    rep_rows = []
    for rep in range(3):
        rk = [k for k in keys if k[1] == rep]
        rep_rows.append({
            "rep": rep,
            "solve_delta": sum(1 if other[k]["reward_binary"] == 1 else 0 for k in rk) - sum(1 if base[k]["reward_binary"] == 1 else 0 for k in rk),
            "partial_delta": mean([other[k]["reward_partial"] - base[k]["reward_partial"] for k in rk]),
            "cost_delta": mean([(other[k].get("combined_cost_usd") or 0) - (base[k].get("combined_cost_usd") or 0) for k in rk]),
            "token_delta": mean([(other[k].get("combined_total_tokens") or 0) - (base[k].get("combined_total_tokens") or 0) for k in rk]),
        })
    res["rep_level"] = rep_rows
    for field in ["solve_delta", "partial_delta", "cost_delta", "token_delta"]:
        vals = [r[field] for r in rep_rows]
        res[f"rep_mean_{field}"] = mean(vals)
        res[f"rep_values_{field}"] = vals
        res[f"rep_wilcoxon_{field}_p"] = wilcoxon(vals)
    # difficulty strata.
    strata = defaultdict(lambda: {"n":0,"base_solves":0,"other_solves":0,"partial_delta_sum":0.0,"token_delta":[],"cost_delta":[]})
    for k in keys:
        bucket = diff[k[0]]["difficulty"]
        s = strata[bucket]
        s["n"] += 1
        s["base_solves"] += 1 if base[k]["reward_binary"] == 1 else 0
        s["other_solves"] += 1 if other[k]["reward_binary"] == 1 else 0
        s["partial_delta_sum"] += other[k]["reward_partial"] - base[k]["reward_partial"]
        s["token_delta"].append((other[k].get("combined_total_tokens") or 0) - (base[k].get("combined_total_tokens") or 0))
        s["cost_delta"].append((other[k].get("combined_cost_usd") or 0) - (base[k].get("combined_cost_usd") or 0))
    res["difficulty"] = {
        b: {
            "n": v["n"],
            "base_solves": v["base_solves"],
            "other_solves": v["other_solves"],
            "solve_delta": v["other_solves"] - v["base_solves"],
            "mean_delta_partial": v["partial_delta_sum"] / v["n"],
            "median_delta_tokens": median(v["token_delta"]),
            "median_delta_cost": median(v["cost_delta"]),
        }
        for b, v in strata.items()
    }
    # top movers.
    movers = []
    for k, d in zip(keys, deltas):
        task, rep = k
        movers.append({
            "task": task,
            "rep": rep,
            "difficulty": diff[task]["difficulty"],
            "title": diff[task]["title"],
            "base_partial": base[k]["reward_partial"],
            "other_partial": other[k]["reward_partial"],
            "delta_partial": d,
            "base_solved": base[k]["reward_binary"] == 1,
            "other_solved": other[k]["reward_binary"] == 1,
            "delta_tokens": (other[k].get("combined_total_tokens") or 0) - (base[k].get("combined_total_tokens") or 0),
            "delta_cost": (other[k].get("combined_cost_usd") or 0) - (base[k].get("combined_cost_usd") or 0),
            "delta_wall_s": (other[k].get("agent_wall_s") or 0) - (base[k].get("agent_wall_s") or 0),
            "other_path": other[k]["result_path"],
        })
    res["top_wins"] = sorted(movers, key=lambda x: x["delta_partial"], reverse=True)[:15]
    res["top_losses"] = sorted(movers, key=lambda x: x["delta_partial"])[:15]
    return res


def difficulty_summary(config: str, rows: dict[tuple[str,int], dict[str, Any]], diff: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for bucket in ["hard", "medium", "easy"]:
        vals = [r for (t,_), r in rows.items() if diff[t]["difficulty"] == bucket]
        out[bucket] = {
            "n": len(vals),
            "solves": sum(1 for r in vals if r["reward_binary"] == 1),
            "mean_partial": mean([r["reward_partial"] for r in vals]),
            "median_combined_cost": median([r["combined_cost_usd"] for r in vals]),
            "median_combined_tokens": median([r["combined_total_tokens"] for r in vals]),
        }
    return out


def task_summary(config: str, rows: dict[tuple[str,int], dict[str, Any]], audits, diff):
    out=[]
    tasks=sorted({t for t,_ in rows})
    for t in tasks:
        vals=[rows[(t,r)] for r in range(3)]
        av=[audits.get((t,r),{}) for r in range(3)] if audits else []
        out.append({
            "task": t,
            "title": diff[t]["title"],
            "difficulty": diff[t]["difficulty"],
            "solves": sum(1 for r in vals if r["reward_binary"] == 1),
            "mean_partial": mean([r["reward_partial"] for r in vals]),
            "partials": [r["reward_partial"] for r in vals],
            "median_cost": median([r["combined_cost_usd"] for r in vals]),
            "median_tokens": median([r["combined_total_tokens"] for r in vals]),
            "worker_calls": sum(r.get("om_worker_calls") or 0 for r in vals),
            "projection_messages": sum(a.get("session_delta_messages",0) for a in av),
            "projection_chars": sum(a.get("injected_chars",0) for a in av),
            "first_injection_median": median([a.get("first_injection_ordinal") for a in av if a.get("first_injection_ordinal")]),
        })
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subset = load_subset()
    diff = load_difficulty()
    rows = {c: load_results(c, subset) for c in CONFIGS}
    audits = {TARGET: projection_audits(TARGET, subset), "projected-om-gpt54mini-low": projection_audits("projected-om-gpt54mini-low", subset), "projected-om-delta-gpt54mini-low": projection_audits("projected-om-delta-gpt54mini-low", subset)}
    summaries = {c: summarize(c, rows[c], audits.get(c)) for c in CONFIGS}
    difficulties = {c: difficulty_summary(c, rows[c], diff) for c in CONFIGS}
    pairs = {
        "delta_vs_baseline": paired("baseline", TARGET, rows, diff),
        "delta_vs_recall_placebo": paired("recall-placebo-gpt54mini-low", TARGET, rows, diff),
        "delta_vs_stock_om": paired("observational-memory-gpt54mini-low", TARGET, rows, diff),
        "delta_vs_projected_v1": paired("projected-om-gpt54mini-low", TARGET, rows, diff),
        "delta_vs_delta_neutral_sentence": paired("projected-om-delta-gpt54mini-low", TARGET, rows, diff),
        "stock_om_vs_recall_placebo": paired("recall-placebo-gpt54mini-low", "observational-memory-gpt54mini-low", rows, diff),
        "projected_v1_vs_stock_om": paired("observational-memory-gpt54mini-low", "projected-om-gpt54mini-low", rows, diff),
    }
    # Projection correlations within target.
    target_rows=rows[TARGET]
    target_audits=audits[TARGET]
    corr_items=[]
    for metric in ["projection_injected_rows", "injected_chars", "injected_observations", "injected_reflections", "first_injection_ordinal"]:
        xs=[]; ys=[]
        for k,a in target_audits.items():
            val = a.get(metric)
            if val is None: continue
            xs.append(val); ys.append(target_rows[k]["reward_partial"])
        if len(xs)>2 and len(set(xs))>1:
            rho,p=scipy_stats.spearmanr(xs,ys)
            corr_items.append({"metric": metric, "spearman_rho": float(rho), "p": float(p)})
    data = {
        "run_id": "gpt55-low-projected-om-delta-no-orch-36v2-r3-w24",
        "target_config": TARGET,
        "subset": "36_v2",
        "reps": 3,
        "model": "openai-codex/gpt-5.5",
        "thinking": "low",
        "worker_model": "openai-codex/gpt-5.4-mini",
        "worker_thinking": "low",
        "configs": CONFIGS,
        "labels": LABELS,
        "summaries": summaries,
        "difficulty_summaries": difficulties,
        "pairs": pairs,
        "projection_correlations": corr_items,
        "target_task_summary": task_summary(TARGET, target_rows, target_audits, diff),
        "notes": {
            "neutral_om_sentence": "projected-om-delta-no-orchestration-gpt54mini-low removes the inherited neutral OM orchestration sentence. It still has extension/tool-owned prompt surfaces from pi-observational-memory and delta projection.",
            "agent_timeout_cell": "No agent timeout was recorded for the no-orchestration target run.",
        },
    }
    (OUT/"summary.json").write_text(json.dumps(data, indent=2))
    print(json.dumps({
        "target": summaries[TARGET],
        "delta_vs_baseline": {k:pairs["delta_vs_baseline"][k] for k in ["solve_base","solve_other","solve_delta","mean_delta_partial","median_delta_combined_cost_usd","median_delta_combined_total_tokens","mcnemar_p","wilcoxon_partial_p"]},
        "delta_vs_stock_om": {k:pairs["delta_vs_stock_om"][k] for k in ["solve_base","solve_other","solve_delta","mean_delta_partial","median_delta_combined_cost_usd","median_delta_combined_total_tokens","mcnemar_p","wilcoxon_partial_p"]},
        "delta_vs_projected_v1": {k:pairs["delta_vs_projected_v1"][k] for k in ["solve_base","solve_other","solve_delta","mean_delta_partial","median_delta_combined_cost_usd","median_delta_combined_total_tokens","mcnemar_p","wilcoxon_partial_p"]},
        "delta_vs_delta_neutral_sentence": {k:pairs["delta_vs_delta_neutral_sentence"][k] for k in ["solve_base","solve_other","solve_delta","mean_delta_partial","median_delta_combined_cost_usd","median_delta_combined_total_tokens","mcnemar_p","wilcoxon_partial_p"]},
    }, indent=2))

if __name__ == "__main__":
    main()
