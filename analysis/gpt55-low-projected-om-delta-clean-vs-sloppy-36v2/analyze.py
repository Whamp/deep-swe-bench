#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics as stats
from pathlib import Path
from typing import Any

from scipy import stats as scipy_stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "gpt55-low-projected-om-delta-clean-vs-sloppy-36v2"
MODEL_DIR = ROOT / "results" / "gpt-5.5" / "low"
SUBSET = ROOT / "subsets" / "36_v2.txt"
DIFF = ROOT / "data" / "deepswe-v1.1-task-difficulty.tsv"
OLD = "projected-om-delta-gpt54mini-low"
NEW = "projected-om-delta-no-orchestration-gpt54mini-low"
OLD_LABEL = "sloppy sentence delta"
NEW_LABEL = "clean no-orchestration delta"
SLOPPY = "Observational memory is enabled for this run. Work normally as a competent engineer; do not change your behavior just because memory is present."


def median(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.median(xs)) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.fmean(xs)) if xs else None


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


def projection_audit(config: str, task: str, rep: int) -> dict[str, Any]:
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
    custom_delta = compactions = folded = 0
    for sp in (cell / "session").glob("*.jsonl"):
        for line in sp.read_text(errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("type") == "custom_message" and row.get("customType") == "om.delta_projection":
                custom_delta += 1
            if row.get("type") == "compaction":
                compactions += 1
            if isinstance(row.get("details"), dict) and row["details"].get("type") == "om.folded":
                folded += 1
    txt = p.read_text(errors="ignore") if p.exists() else ""
    return {
        "projection_file": str(p.relative_to(ROOT)) if p.exists() else None,
        "projection_rows": len(rows),
        "injected_rows": len(injected),
        "first_injection_ordinal": next((i + 1 for i, r in enumerate(rows) if r.get("injected")), None),
        "injected_chars": sum(int((r.get("contentChars") if r.get("contentChars") is not None else r.get("summaryChars")) or 0) for r in injected),
        "injected_observations": sum(int(r.get("observations") or 0) for r in injected),
        "injected_reflections": sum(int(r.get("reflections") or 0) for r in injected),
        "injected_drops": sum(int(r.get("droppedObservations") or 0) for r in injected),
        "custom_delta_messages": custom_delta,
        "compactions": compactions,
        "om_folded_details": folded,
        "payload_shape_mentions": int("payloadShape" in txt) if p.exists() else 0,
    }


def prompt_audit(config: str, task: str, rep: int) -> dict[str, Any]:
    cell = MODEL_DIR / config / task / f"rep{rep}"
    result = json.loads((cell / "result.json").read_text())
    ic = cell / "initial_context"
    system_prompt = (ic / "system_prompt.txt").read_text(errors="ignore") if (ic / "system_prompt.txt").exists() else ""
    provider = None
    tools = []
    instructions_len = None
    provider_path = ic / "provider_request_0001.json"
    if provider_path.exists():
        provider = json.loads(provider_path.read_text())
        if isinstance(provider, dict):
            instructions_len = len(provider.get("instructions") or "")
            for t in provider.get("tools") or []:
                tools.append(((t.get("function") or {}).get("name") or t.get("name") or t.get("type")))
    return {
        "system_preamble_chars": result.get("system_preamble_chars"),
        "orchestration_chars": result.get("orchestration_chars"),
        "append_system_prompt_chars": result.get("append_system_prompt_chars"),
        "system_prompt_chars": len(system_prompt) if system_prompt else None,
        "provider_instructions_chars": instructions_len,
        "has_sloppy_sentence": SLOPPY in system_prompt,
        "provider_has_sloppy_sentence": bool(provider and SLOPPY in json.dumps(provider)),
        "tools": tools,
    }


def summarize(config: str, rows: dict[tuple[str, int], dict[str, Any]], audits: dict[tuple[str, int], dict[str, Any]], prompts: dict[tuple[str, int], dict[str, Any]]):
    vals = list(rows.values())
    av = list(audits.values())
    pv = list(prompts.values())
    return {
        "config": config,
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
        "median_total_tokens": median([r.get("total_tokens") for r in vals]),
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
        "projection_files": sum(1 for a in av if a["projection_file"]),
        "projection_cells_with_injection": sum(1 for a in av if a["injected_rows"] > 0),
        "projection_rows": sum(a["projection_rows"] for a in av),
        "projection_injected_rows": sum(a["injected_rows"] for a in av),
        "projection_delta_messages": sum(a["custom_delta_messages"] for a in av),
        "projection_injected_chars_total": sum(a["injected_chars"] for a in av),
        "projection_injected_chars_median_cell": median([a["injected_chars"] for a in av]),
        "projection_observations": sum(a["injected_observations"] for a in av),
        "projection_reflections": sum(a["injected_reflections"] for a in av),
        "projection_drops": sum(a["injected_drops"] for a in av),
        "projection_first_injection_median": median([a["first_injection_ordinal"] for a in av if a["first_injection_ordinal"]]),
        "compaction_entries": sum(a["compactions"] for a in av),
        "om_folded_details": sum(a["om_folded_details"] for a in av),
        "payload_shape_mentions": sum(a["payload_shape_mentions"] for a in av),
        "prompt_system_chars_median": median([p["system_prompt_chars"] for p in pv]),
        "prompt_provider_instructions_chars_median": median([p["provider_instructions_chars"] for p in pv]),
        "prompt_has_sloppy_cells": sum(1 for p in pv if p["has_sloppy_sentence"]),
        "provider_has_sloppy_cells": sum(1 for p in pv if p["provider_has_sloppy_sentence"]),
        "append_system_prompt_chars_median": median([p["append_system_prompt_chars"] for p in pv]),
        "orchestration_chars_median": median([p["orchestration_chars"] for p in pv]),
    }


def wilcoxon(xs: list[float]) -> float | None:
    nz = [x for x in xs if abs(x) > 1e-12]
    if len(nz) < 2:
        return None
    try:
        return float(scipy_stats.wilcoxon(nz, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        return None


def paired(old_rows, new_rows, diff):
    keys = sorted(old_rows)
    deltas = [new_rows[k]["reward_partial"] - old_rows[k]["reward_partial"] for k in keys]
    old_s = [1 if old_rows[k]["reward_binary"] == 1 else 0 for k in keys]
    new_s = [1 if new_rows[k]["reward_binary"] == 1 else 0 for k in keys]
    old_only = sum(1 for o, n in zip(old_s, new_s) if o and not n)
    new_only = sum(1 for o, n in zip(old_s, new_s) if n and not o)
    discordant = old_only + new_only
    mcnemar = float(scipy_stats.binomtest(min(old_only, new_only), discordant, 0.5).pvalue) if discordant else None
    res = {
        "n": len(keys),
        "old_solves": sum(old_s),
        "new_solves": sum(new_s),
        "solve_delta": sum(new_s) - sum(old_s),
        "both_solved": sum(1 for o, n in zip(old_s, new_s) if o and n),
        "old_only": old_only,
        "new_only": new_only,
        "neither": sum(1 for o, n in zip(old_s, new_s) if not o and not n),
        "mcnemar_p": mcnemar,
        "mean_delta_partial": mean(deltas),
        "median_delta_partial": median(deltas),
        "wilcoxon_partial_p": wilcoxon(deltas),
        "improved_cells": sum(1 for d in deltas if d > 1e-9),
        "worsened_cells": sum(1 for d in deltas if d < -1e-9),
        "tied_cells": sum(1 for d in deltas if abs(d) <= 1e-9),
    }
    for metric in ["combined_total_tokens", "combined_cost_usd", "cost_usd", "total_tokens", "agent_wall_s", "turns", "tool_calls", "patch_bytes", "om_worker_total_tokens", "om_worker_cost_usd", "om_worker_calls"]:
        ds = [(new_rows[k].get(metric) or 0) - (old_rows[k].get(metric) or 0) for k in keys]
        res[f"median_delta_{metric}"] = median(ds)
        res[f"mean_delta_{metric}"] = mean(ds)
        res[f"sum_delta_{metric}"] = sum(ds)
    rep_rows = []
    for rep in range(3):
        rk = [k for k in keys if k[1] == rep]
        rep_rows.append({
            "rep": rep,
            "solve_delta": sum(1 if new_rows[k]["reward_binary"] == 1 else 0 for k in rk) - sum(1 if old_rows[k]["reward_binary"] == 1 else 0 for k in rk),
            "partial_delta": mean([new_rows[k]["reward_partial"] - old_rows[k]["reward_partial"] for k in rk]),
            "cost_delta": mean([(new_rows[k].get("combined_cost_usd") or 0) - (old_rows[k].get("combined_cost_usd") or 0) for k in rk]),
            "token_delta": mean([(new_rows[k].get("combined_total_tokens") or 0) - (old_rows[k].get("combined_total_tokens") or 0) for k in rk]),
        })
    res["rep_level"] = rep_rows
    for field in ["solve_delta", "partial_delta", "cost_delta", "token_delta"]:
        vals = [r[field] for r in rep_rows]
        res[f"rep_values_{field}"] = vals
        res[f"rep_mean_{field}"] = mean(vals)
        res[f"rep_wilcoxon_{field}_p"] = wilcoxon(vals)
    strata = {}
    for bucket in ["hard", "medium", "easy"]:
        ks = [k for k in keys if diff[k[0]]["difficulty"] == bucket]
        strata[bucket] = {
            "n": len(ks),
            "old_solves": sum(1 for k in ks if old_rows[k]["reward_binary"] == 1),
            "new_solves": sum(1 for k in ks if new_rows[k]["reward_binary"] == 1),
            "mean_delta_partial": mean([new_rows[k]["reward_partial"] - old_rows[k]["reward_partial"] for k in ks]),
            "median_delta_cost": median([(new_rows[k].get("combined_cost_usd") or 0) - (old_rows[k].get("combined_cost_usd") or 0) for k in ks]),
            "median_delta_tokens": median([(new_rows[k].get("combined_total_tokens") or 0) - (old_rows[k].get("combined_total_tokens") or 0) for k in ks]),
        }
        strata[bucket]["solve_delta"] = strata[bucket]["new_solves"] - strata[bucket]["old_solves"]
    res["difficulty"] = strata
    movers = []
    for k, d in zip(keys, deltas):
        task, rep = k
        movers.append({
            "task": task,
            "rep": rep,
            "title": diff[task]["title"],
            "difficulty": diff[task]["difficulty"],
            "old_partial": old_rows[k]["reward_partial"],
            "new_partial": new_rows[k]["reward_partial"],
            "delta_partial": d,
            "old_solved": old_rows[k]["reward_binary"] == 1,
            "new_solved": new_rows[k]["reward_binary"] == 1,
            "delta_cost": (new_rows[k].get("combined_cost_usd") or 0) - (old_rows[k].get("combined_cost_usd") or 0),
            "delta_tokens": (new_rows[k].get("combined_total_tokens") or 0) - (old_rows[k].get("combined_total_tokens") or 0),
        })
    res["top_wins"] = sorted(movers, key=lambda x: x["delta_partial"], reverse=True)[:20]
    res["top_losses"] = sorted(movers, key=lambda x: x["delta_partial"])[:20]
    res["solve_gains"] = [m for m in movers if not m["old_solved"] and m["new_solved"]]
    res["solve_losses"] = [m for m in movers if m["old_solved"] and not m["new_solved"]]
    return res


def task_level(old_rows, new_rows, diff):
    out = []
    for task in sorted({t for t, _ in old_rows}):
        ks = [(task, rep) for rep in range(3)]
        old_vals = [old_rows[k] for k in ks]
        new_vals = [new_rows[k] for k in ks]
        out.append({
            "task": task,
            "title": diff[task]["title"],
            "difficulty": diff[task]["difficulty"],
            "old_solves": sum(r["reward_binary"] == 1 for r in old_vals),
            "new_solves": sum(r["reward_binary"] == 1 for r in new_vals),
            "old_mean_partial": mean([r["reward_partial"] for r in old_vals]),
            "new_mean_partial": mean([r["reward_partial"] for r in new_vals]),
            "mean_delta_partial": mean([new_vals[i]["reward_partial"] - old_vals[i]["reward_partial"] for i in range(3)]),
            "median_delta_cost": median([(new_vals[i].get("combined_cost_usd") or 0) - (old_vals[i].get("combined_cost_usd") or 0) for i in range(3)]),
            "median_delta_tokens": median([(new_vals[i].get("combined_total_tokens") or 0) - (old_vals[i].get("combined_total_tokens") or 0) for i in range(3)]),
        })
    for r in out:
        r["solve_delta"] = r["new_solves"] - r["old_solves"]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subset = load_subset()
    diff = load_difficulty()
    old_rows = load_results(OLD, subset)
    new_rows = load_results(NEW, subset)
    old_a = {k: projection_audit(OLD, *k) for k in old_rows}
    new_a = {k: projection_audit(NEW, *k) for k in new_rows}
    old_p = {k: prompt_audit(OLD, *k) for k in old_rows}
    new_p = {k: prompt_audit(NEW, *k) for k in new_rows}
    data = {
        "run_id_old": "gpt55-low-projected-om-delta-36v2-r3-w24",
        "run_id_new": "gpt55-low-projected-om-delta-no-orch-36v2-r3-w24",
        "old_config": OLD,
        "new_config": NEW,
        "old_label": OLD_LABEL,
        "new_label": NEW_LABEL,
        "sloppy_sentence": SLOPPY,
        "subset": "36_v2",
        "reps": 3,
        "model": "openai-codex/gpt-5.5",
        "thinking": "low",
        "worker_model": "openai-codex/gpt-5.4-mini",
        "worker_thinking": "low",
        "summaries": {
            OLD: summarize(OLD, old_rows, old_a, old_p),
            NEW: summarize(NEW, new_rows, new_a, new_p),
        },
        "pair": paired(old_rows, new_rows, diff),
        "task_level": task_level(old_rows, new_rows, diff),
        "config_diff": {
            "treatment_diff": "The only config treatment file removed was orchestration.md. README/smoke metadata differ but the pi-flags, OM settings, worker model, and delta projection extension match.",
            "removed_file": f"configs/{OLD}/orchestration.md",
            "removed_text": SLOPPY,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(data, indent=2))
    print(json.dumps({
        "old": data["summaries"][OLD],
        "new": data["summaries"][NEW],
        "pair": {k: data["pair"][k] for k in ["old_solves", "new_solves", "solve_delta", "mean_delta_partial", "median_delta_combined_cost_usd", "median_delta_combined_total_tokens", "mcnemar_p", "wilcoxon_partial_p", "new_only", "old_only"]},
    }, indent=2))


if __name__ == "__main__":
    main()
