#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics as stats
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scipy import stats as scipy_stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "analysis" / "omp-pi-prompt-no-project-36v2"
MODEL_DIR = ROOT / "results" / "gpt-5.5" / "low"
SUBSET_PATH = ROOT / "subsets" / "36_v2.txt"
DIFF_PATH = ROOT / "data" / "deepswe-v1.1-task-difficulty.tsv"

CLEAN_PI = "baseline"
CLEAN_MEDIUM_PI = "baseline__gpt55_medium"
MEDIUM_PREAMBLE_PI = "baseline-preamble-orchestration__gpt55_medium"
CONFIG_PATHS = {
    CLEAN_MEDIUM_PI: ROOT / "results" / "gpt-5.5" / "medium" / "baseline",
    MEDIUM_PREAMBLE_PI: ROOT / "results" / "gpt-5.5" / "medium" / "baseline-preamble-orchestration",
}
NO_PROJECT = [
    "baseline-omp-pi-prompt-bash-only-no-project",
    "baseline-omp-pi-prompt-grepglob-no-project",
    "baseline-omp-pi-prompt-ast-no-project",
]
PRIOR_PI_PROMPT = [
    "baseline-omp-pi-prompt-bash-only",
    "baseline-omp-pi-prompt-grepglob",
    "baseline-omp-pi-prompt-ast",
]
DEFAULT_OMP = ["baseline-omp-bash-only", "baseline-omp", "baseline-omp-ast"]
# 36_v2 has full coverage for clean Pi low/medium, default OMP, the
# no-PROJECT rerun, and the historical prompt-bearing medium Pi baseline. The
# PROJECT-contaminated Pi-like OMP configs only ran on 12_v2, so keep their
# labels for reference but exclude them from 36_v2 loading.
ALL_CONFIGS = [CLEAN_PI, CLEAN_MEDIUM_PI, MEDIUM_PREAMBLE_PI] + NO_PROJECT + DEFAULT_OMP
LABELS = {
    CLEAN_PI: "Clean Pi baseline · GPT-5.5 low",
    CLEAN_MEDIUM_PI: "Clean Pi baseline · GPT-5.5 medium",
    MEDIUM_PREAMBLE_PI: "Pi + preamble/orchestration · GPT-5.5 medium",
    "baseline-omp-pi-prompt-bash-only-no-project": "OMP Pi-like bash-only, no PROJECT",
    "baseline-omp-pi-prompt-grepglob-no-project": "OMP Pi-like grep/glob, no PROJECT",
    "baseline-omp-pi-prompt-ast-no-project": "OMP Pi-like AST, no PROJECT",
    "baseline-omp-pi-prompt-bash-only": "OMP Pi-like bash-only, PROJECT contaminated",
    "baseline-omp-pi-prompt-grepglob": "OMP Pi-like grep/glob, PROJECT contaminated",
    "baseline-omp-pi-prompt-ast": "OMP Pi-like AST, PROJECT contaminated",
    "baseline-omp-bash-only": "Default OMP bash-only",
    "baseline-omp": "Default OMP grep/glob",
    "baseline-omp-ast": "Default OMP AST",
}

TOOL_EXPECTED = {
    "baseline-omp-pi-prompt-bash-only-no-project": {"read", "bash", "edit", "write"},
    "baseline-omp-pi-prompt-grepglob-no-project": {"read", "bash", "edit", "write", "grep", "glob"},
    "baseline-omp-pi-prompt-ast-no-project": {"read", "bash", "edit", "write", "ast_grep", "ast_edit"},
}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.fmean(xs)) if xs else None


def median(xs):
    xs = [x for x in xs if x is not None]
    return float(stats.median(xs)) if xs else None


def load_subset():
    return [l.strip() for l in SUBSET_PATH.read_text().splitlines() if l.strip() and not l.startswith("#")]


def load_diff():
    out = {}
    for line in DIFF_PATH.read_text().splitlines():
        if not line.strip() or line.startswith("pass_rate"):
            continue
        pass_rate, language, slug, repo, title = line.split("\t")[:5]
        pr = float(pass_rate)
        bucket = "hard" if pr < 33 else "medium" if pr < 66 else "easy"
        out[slug] = {"pass_rate": pr, "language": language, "repository": repo, "title": title, "difficulty": bucket}
    return out


def config_base(config: str) -> Path:
    return CONFIG_PATHS.get(config, MODEL_DIR / config)


def load_results(config: str, subset: list[str]) -> dict[tuple[str, int], dict[str, Any]]:
    rows = {}
    base = config_base(config)
    for task in subset:
        for rep in range(3):
            p = base / task / f"rep{rep}" / "result.json"
            if not p.exists():
                raise FileNotFoundError(p)
            r = json.loads(p.read_text())
            r["result_path"] = str(p.relative_to(ROOT))
            rows[(task, rep)] = r
    return rows


def iter_jsonl(path: Path):
    try:
        raw = path.read_text(errors="ignore")
    except Exception:
        return
    for line in raw.splitlines():
        if not line.strip().startswith("{"):
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def root_sessions(cell: Path) -> list[Path]:
    # Exclude child suffix sessions. OMP does not create recursive child sessions here,
    # but keep parity with parse_usage's root-segment idea.
    return sorted((cell / "session").glob("*.jsonl"), key=lambda p: (p.stat().st_mtime_ns, p.name))


def latest_root(cell: Path) -> Path | None:
    ss = root_sessions(cell)
    return ss[-1] if ss else None


def session_usage(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {"turns": 0, "tool_calls": 0, "cost_usd": 0.0, "total_tokens": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}
    acc = {"turns": 0, "tool_calls": 0, "cost_usd": 0.0, "total_tokens": 0, "input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}
    for r in iter_jsonl(path):
        if r.get("type") != "message":
            continue
        msg = r.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        acc["turns"] += 1
        for blk in msg.get("content") or []:
            if isinstance(blk, dict) and blk.get("type") == "toolCall":
                acc["tool_calls"] += 1
        u = msg.get("usage") or {}
        acc["input_tokens"] += int(u.get("input") or 0)
        acc["output_tokens"] += int(u.get("output") or 0)
        acc["cache_read_tokens"] += int(u.get("cacheRead") or 0)
        acc["cache_write_tokens"] += int(u.get("cacheWrite") or 0)
        acc["cost_usd"] += float((u.get("cost") or {}).get("total") or 0.0)
    acc["total_tokens"] = acc["input_tokens"] + acc["output_tokens"] + acc["cache_read_tokens"] + acc["cache_write_tokens"]
    acc["cost_usd"] = round(acc["cost_usd"], 6)
    return acc


def cell_audit(config: str, task: str, rep: int) -> dict[str, Any]:
    cell = config_base(config) / task / f"rep{rep}"
    sessions = root_sessions(cell)
    latest = latest_root(cell)
    latest_text = latest.read_text(errors="ignore") if latest else ""
    stale = sessions[:-1]
    stale_usage_limit = []
    for sp in stale:
        txt = sp.read_text(errors="ignore")
        if "usage_limit" in txt or "usage limit" in txt.lower():
            stale_usage_limit.append(str(sp.relative_to(ROOT)))
    latest_has_usage_limit = "usage_limit" in latest_text or "usage limit" in latest_text.lower()
    latest_usage = session_usage(latest)
    result = json.loads((cell / "result.json").read_text())
    usage_matches_latest = all(
        abs((result.get(k) or 0) - (latest_usage.get(k) or 0)) < (1e-6 if k == "cost_usd" else 0.5)
        for k in ["turns", "tool_calls", "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "total_tokens", "cost_usd"]
    )
    ic = cell / "initial_context"
    provider_path = ic / "provider_request_0001.json"
    provider = json.loads(provider_path.read_text()) if provider_path.exists() else {}
    provider_dump = json.dumps(provider)
    instructions = provider.get("instructions") or ""
    if not instructions and provider.get("messages"):
        instructions = "".join(
            m.get("content", "") if isinstance(m.get("content"), str) else json.dumps(m.get("content"))
            for m in provider.get("messages", [])
            if isinstance(m, dict) and m.get("role") == "system"
        )
    input_roles = []
    for item in provider.get("input") or provider.get("messages") or []:
        if isinstance(item, dict):
            input_roles.append(item.get("role"))
    tools = []
    for t in provider.get("tools") or []:
        name = ((t.get("function") or {}).get("name") or t.get("name") or t.get("type"))
        tools.append(name)
    strip_file = cell / "omp_project_message_strip" / "strip.ndjson"
    strip_rows = [r for r in iter_jsonl(strip_file)] if strip_file.exists() else []
    stripped_total = sum(int(r.get("stripped") or 0) for r in strip_rows)
    stripped_tools = sorted({name for r in strip_rows for name in (r.get("strippedToolNames") or [])})
    stderr_nonempty = (cell / "logs" / "omp.stderr.txt").exists() and (cell / "logs" / "omp.stderr.txt").stat().st_size > 0
    return {
        "config": config,
        "task": task,
        "rep": rep,
        "session_count": len(sessions),
        "stale_session_count": max(0, len(sessions)-1),
        "stale_usage_limit_sessions": stale_usage_limit,
        "latest_session": str(latest.relative_to(ROOT)) if latest else None,
        "latest_has_usage_limit": latest_has_usage_limit,
        "usage_matches_latest_session": usage_matches_latest,
        "provider_has_project": "PROJECT\n===================================" in provider_dump or "Each response MUST advance the task" in provider_dump or "<workstation>" in provider_dump,
        "provider_has_generate_image": "generate_image" in tools,
        "provider_tools": tools,
        "provider_instructions_chars": len(instructions),
        "provider_payload_bytes": provider_path.stat().st_size if provider_path.exists() else 0,
        "provider_tool_schema_bytes": len(json.dumps(provider.get("tools") or [])),
        "provider_input_roles": input_roles,
        "provider_input_len": len(input_roles),
        "strip_rows": len(strip_rows),
        "stripped_total": stripped_total,
        "stripped_tools": stripped_tools,
        "stderr_nonempty": stderr_nonempty,
        "has_transient_error_json": (cell / "transient_error.json").exists(),
        "result_transient_model_error": result.get("transient_model_error"),
    }


def tool_mix(config: str, rows: dict[tuple[str,int],dict[str,Any]]) -> dict[str, Any]:
    counts = Counter()
    failures = 0
    non_message_t1 = []
    provider_payload_bytes = []
    session_bytes = []
    for task, rep in rows:
        cell = config_base(config) / task / f"rep{rep}"
        sp = latest_root(cell)
        if not sp:
            continue
        session_bytes.append(sp.stat().st_size)
        for r in iter_jsonl(sp):
            if r.get("customType") == "tool_execution_start":
                name = ((r.get("data") or {}).get("toolName") or r.get("toolName"))
                if name:
                    counts[name] += 1
            if r.get("customType") == "tool_execution_end" or r.get("type") == "tool_execution_end":
                d = r.get("data") or r
                if d.get("isError") or d.get("error"):
                    failures += 1
            if r.get("type") == "message":
                msg = r.get("message") or {}
                if msg.get("role") == "assistant":
                    # Pi tool calls live on assistant messages; count if no OMP custom events.
                    for blk in msg.get("content") or []:
                        if isinstance(blk, dict) and blk.get("type") == "toolCall":
                            name = blk.get("name") or (blk.get("toolCall") or {}).get("name")
                            if name and not config.startswith("baseline-omp"):
                                counts[name] += 1
                    pp = msg.get("providerPayload") or {}
                    cs = msg.get("contextSnapshot") or {}
                    if cs.get("nonMessageTokens") is not None and len(non_message_t1) == 0:
                        non_message_t1.append(cs.get("nonMessageTokens"))
                    if pp:
                        provider_payload_bytes.append(len(json.dumps(pp)))
    return {
        "tool_counts": dict(sorted(counts.items())),
        "tool_failures": failures,
        "first_non_message_tokens_median": median(non_message_t1),
        "latest_session_bytes_median": median(session_bytes),
        "assistant_provider_payload_bytes_median": median(provider_payload_bytes),
    }


def summarize(config: str, rows: dict[tuple[str,int],dict[str,Any]], audits: dict[tuple[str,int],dict[str,Any]], diff: dict[str,dict[str,Any]]) -> dict[str,Any]:
    vals = list(rows.values())
    av = list(audits.values())
    out = {
        "config": config,
        "label": LABELS[config],
        "n": len(vals),
        "solves": sum(1 for r in vals if r.get("reward_binary") == 1),
        "solve_rate": sum(1 for r in vals if r.get("reward_binary") == 1)/len(vals),
        "mean_partial": mean([r.get("reward_partial") for r in vals]),
        "median_partial": median([r.get("reward_partial") for r in vals]),
        "partial_lt_09": sum(1 for r in vals if (r.get("reward_partial") or 0) < 0.9),
        "partial_ge_099": sum(1 for r in vals if (r.get("reward_partial") or 0) >= 0.99),
        "reward_minus_one": sum(1 for r in vals if r.get("reward_binary") == -1),
        "timeouts": sum(1 for r in vals if r.get("agent_timed_out")),
        "empty_patches": sum(1 for r in vals if (r.get("patch_bytes") or 0) == 0),
        "median_tokens": median([r.get("combined_total_tokens", r.get("total_tokens")) for r in vals]),
        "median_cost": median([r.get("combined_cost_usd", r.get("cost_usd")) for r in vals]),
        "total_tokens": sum(r.get("combined_total_tokens", r.get("total_tokens")) or 0 for r in vals),
        "total_cost": sum(r.get("combined_cost_usd", r.get("cost_usd")) or 0 for r in vals),
        "median_wall_s": median([r.get("agent_wall_s") for r in vals]),
        "median_turns": median([r.get("turns") for r in vals]),
        "median_tool_calls": median([r.get("tool_calls") for r in vals]),
        "median_patch_bytes": median([r.get("patch_bytes") for r in vals]),
        "f2p_total": sum(r.get("f2p_total") or 0 for r in vals),
        "f2p_passed": sum(r.get("f2p_passed") or 0 for r in vals),
        "p2p_total": sum(r.get("p2p_total") or 0 for r in vals),
        "p2p_passed": sum(r.get("p2p_passed") or 0 for r in vals),
        "stale_session_cells": sum(1 for a in av if a["stale_session_count"]),
        "stale_usage_limit_cells": sum(1 for a in av if a["stale_usage_limit_sessions"]),
        "latest_usage_limit_cells": sum(1 for a in av if a["latest_has_usage_limit"]),
        "usage_mismatch_cells": sum(1 for a in av if not a["usage_matches_latest_session"]),
        "provider_project_cells": sum(1 for a in av if a["provider_has_project"]),
        "provider_generate_image_cells": sum(1 for a in av if a["provider_has_generate_image"]),
        "transient_json_cells": sum(1 for a in av if a["has_transient_error_json"]),
        "stderr_nonempty_cells": sum(1 for a in av if a["stderr_nonempty"]),
        "stripped_project_total": sum(a["stripped_total"] for a in av),
        "stripped_generate_image_cells": sum(1 for a in av if "generate_image" in a["stripped_tools"]),
        "provider_instructions_chars_median": median([a["provider_instructions_chars"] for a in av]),
        "provider_instructions_chars_min": min([a["provider_instructions_chars"] for a in av]) if av else None,
        "provider_instructions_chars_max": max([a["provider_instructions_chars"] for a in av]) if av else None,
        "provider_payload_bytes_median": median([a["provider_payload_bytes"] for a in av]),
        "provider_tool_schema_bytes_median": median([a["provider_tool_schema_bytes"] for a in av]),
        "provider_input_role_variants": sorted({tuple(a["provider_input_roles"]) for a in av}),
        "provider_tool_variants": sorted({tuple(a["provider_tools"]) for a in av}),
    }
    strata = {}
    for bucket in ["hard", "medium", "easy"]:
        ks = [k for k in rows if diff[k[0]]["difficulty"] == bucket]
        strata[bucket] = {
            "n": len(ks),
            "solves": sum(rows[k].get("reward_binary") == 1 for k in ks),
            "mean_partial": mean([rows[k].get("reward_partial") for k in ks]),
            "median_cost": median([rows[k].get("combined_cost_usd", rows[k].get("cost_usd")) for k in ks]),
            "median_tokens": median([rows[k].get("combined_total_tokens", rows[k].get("total_tokens")) for k in ks]),
        }
    out["difficulty"] = strata
    out.update(tool_mix(config, rows))
    return out


def wilcoxon(vals: list[float]) -> float | None:
    nz = [v for v in vals if abs(v) > 1e-12]
    if len(nz) < 2:
        return None
    try:
        return float(scipy_stats.wilcoxon(nz, zero_method="wilcox").pvalue)
    except Exception:
        return None


def paired(a_name: str, b_name: str, rows: dict[str,dict[tuple[str,int],dict[str,Any]]], diff: dict[str,dict[str,Any]]) -> dict[str,Any]:
    a = rows[a_name]; b = rows[b_name]
    keys = sorted(set(a) & set(b))
    da = []
    old_only = new_only = both = neither = 0
    movers = []
    for k in keys:
        ar, br = a[k], b[k]
        asol, bsol = ar.get("reward_binary") == 1, br.get("reward_binary") == 1
        if asol and bsol: both += 1
        elif asol: old_only += 1
        elif bsol: new_only += 1
        else: neither += 1
        d = (br.get("reward_partial") or 0) - (ar.get("reward_partial") or 0)
        da.append(d)
        task, rep = k
        movers.append({
            "task": task, "rep": rep, "title": diff[task]["title"], "difficulty": diff[task]["difficulty"],
            "a_partial": ar.get("reward_partial"), "b_partial": br.get("reward_partial"), "delta_partial": d,
            "a_solved": asol, "b_solved": bsol,
            "delta_cost": (br.get("combined_cost_usd", br.get("cost_usd")) or 0) - (ar.get("combined_cost_usd", ar.get("cost_usd")) or 0),
            "delta_tokens": (br.get("combined_total_tokens", br.get("total_tokens")) or 0) - (ar.get("combined_total_tokens", ar.get("total_tokens")) or 0),
            "delta_turns": (br.get("turns") or 0) - (ar.get("turns") or 0),
            "delta_tools": (br.get("tool_calls") or 0) - (ar.get("tool_calls") or 0),
        })
    disc = old_only + new_only
    mcnemar = float(scipy_stats.binomtest(min(old_only,new_only), disc, 0.5).pvalue) if disc else None
    out = {
        "a": a_name, "b": b_name, "a_label": LABELS[a_name], "b_label": LABELS[b_name], "n": len(keys),
        "a_solves": sum(a[k].get("reward_binary") == 1 for k in keys),
        "b_solves": sum(b[k].get("reward_binary") == 1 for k in keys),
        "solve_delta": sum(b[k].get("reward_binary") == 1 for k in keys) - sum(a[k].get("reward_binary") == 1 for k in keys),
        "both_solved": both, "a_only": old_only, "b_only": new_only, "neither": neither,
        "mcnemar_p": mcnemar,
        "mean_delta_partial": mean(da),
        "median_delta_partial": median(da),
        "wilcoxon_partial_p": wilcoxon(da),
        "improved_cells": sum(d > 1e-9 for d in da),
        "worsened_cells": sum(d < -1e-9 for d in da),
        "tied_cells": sum(abs(d) <= 1e-9 for d in da),
    }
    for metric in ["combined_total_tokens", "combined_cost_usd", "agent_wall_s", "turns", "tool_calls", "patch_bytes"]:
        ds = [(b[k].get(metric, b[k].get(metric.replace("combined_", ""))) or 0) - (a[k].get(metric, a[k].get(metric.replace("combined_", ""))) or 0) for k in keys]
        out[f"median_delta_{metric}"] = median(ds)
        out[f"mean_delta_{metric}"] = mean(ds)
        out[f"sum_delta_{metric}"] = sum(ds)
    strata = {}
    for bucket in ["hard", "medium", "easy"]:
        ks = [k for k in keys if diff[k[0]]["difficulty"] == bucket]
        strata[bucket] = {
            "n": len(ks),
            "a_solves": sum(a[k].get("reward_binary") == 1 for k in ks),
            "b_solves": sum(b[k].get("reward_binary") == 1 for k in ks),
            "solve_delta": sum(b[k].get("reward_binary") == 1 for k in ks) - sum(a[k].get("reward_binary") == 1 for k in ks),
            "mean_delta_partial": mean([(b[k].get("reward_partial") or 0) - (a[k].get("reward_partial") or 0) for k in ks]),
            "median_delta_cost": median([(b[k].get("combined_cost_usd", b[k].get("cost_usd")) or 0) - (a[k].get("combined_cost_usd", a[k].get("cost_usd")) or 0) for k in ks]),
            "median_delta_tokens": median([(b[k].get("combined_total_tokens", b[k].get("total_tokens")) or 0) - (a[k].get("combined_total_tokens", a[k].get("total_tokens")) or 0) for k in ks]),
        }
    out["difficulty"] = strata
    out["top_wins"] = sorted(movers, key=lambda x: x["delta_partial"], reverse=True)[:15]
    out["top_losses"] = sorted(movers, key=lambda x: x["delta_partial"])[:15]
    out["solve_gains"] = [m for m in movers if (not m["a_solved"] and m["b_solved"])]
    out["solve_losses"] = [m for m in movers if (m["a_solved"] and not m["b_solved"])]
    return out


def pareto(summaries: dict[str,dict[str,Any]], configs: list[str]) -> list[dict[str,Any]]:
    rows = []
    for c in configs:
        s = summaries[c]
        dominated = []
        for d in configs:
            if d == c:
                continue
            t = summaries[d]
            if (t["solves"] >= s["solves"] and t["median_cost"] <= s["median_cost"] and (t["solves"] > s["solves"] or t["median_cost"] < s["median_cost"])):
                dominated.append(d)
        rows.append({"config": c, "label": LABELS[c], "solves": s["solves"], "median_cost": s["median_cost"], "mean_partial": s["mean_partial"], "dominated_by": dominated})
    return sorted(rows, key=lambda r: (r["median_cost"], -r["solves"]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    subset = load_subset()
    diff = load_diff()
    rows = {c: load_results(c, subset) for c in ALL_CONFIGS}
    audits = {c: {k: cell_audit(c, *k) for k in rows[c]} for c in ALL_CONFIGS}
    summaries = {c: summarize(c, rows[c], audits[c], diff) for c in ALL_CONFIGS}
    pairs = {}
    for c in NO_PROJECT:
        pairs[f"{CLEAN_PI}__vs__{c}"] = paired(CLEAN_PI, c, rows, diff)
        pairs[f"{c}__vs__{CLEAN_MEDIUM_PI}"] = paired(c, CLEAN_MEDIUM_PI, rows, diff)
    pairs[f"{CLEAN_PI}__vs__{CLEAN_MEDIUM_PI}"] = paired(CLEAN_PI, CLEAN_MEDIUM_PI, rows, diff)
    pairs[f"{CLEAN_MEDIUM_PI}__vs__{MEDIUM_PREAMBLE_PI}"] = paired(CLEAN_MEDIUM_PI, MEDIUM_PREAMBLE_PI, rows, diff)
    pairs[f"{NO_PROJECT[0]}__vs__{NO_PROJECT[1]}"] = paired(NO_PROJECT[0], NO_PROJECT[1], rows, diff)
    pairs[f"{NO_PROJECT[0]}__vs__{NO_PROJECT[2]}"] = paired(NO_PROJECT[0], NO_PROJECT[2], rows, diff)
    for default, clean in zip(DEFAULT_OMP, NO_PROJECT):
        pairs[f"{default}__vs__{clean}"] = paired(default, clean, rows, diff)

    pause_audit = {
        "quota_hit_cells": [a for c in NO_PROJECT for a in audits[c].values() if a["stale_usage_limit_sessions"]],
        "latest_usage_limit_cells": [a for c in NO_PROJECT for a in audits[c].values() if a["latest_has_usage_limit"]],
        "usage_mismatch_cells": [a for c in NO_PROJECT for a in audits[c].values() if not a["usage_matches_latest_session"]],
        "transient_json_cells": [a for c in NO_PROJECT for a in audits[c].values() if a["has_transient_error_json"]],
        "provider_project_cells": [a for c in NO_PROJECT for a in audits[c].values() if a["provider_has_project"]],
        "provider_generate_image_cells": [a for c in NO_PROJECT for a in audits[c].values() if a["provider_has_generate_image"]],
    }

    audits_json = {
        c: {f"{task}/rep{rep}": a for (task, rep), a in cfg_audits.items()}
        for c, cfg_audits in audits.items()
    }
    data = {
        "run_id": "omp-pi-prompt-toolsets-no-project-36v2-r3-w24",
        "subset": "36_v2",
        "reps": 3,
        "model": "openai-codex/gpt-5.5",
        "thinking": "low",
        "configs": ALL_CONFIGS,
        "labels": LABELS,
        "summaries": summaries,
        "pairs": pairs,
        "audits": audits_json,
        "pause_audit": pause_audit,
        "pareto_all": pareto(summaries, [CLEAN_PI, CLEAN_MEDIUM_PI, MEDIUM_PREAMBLE_PI] + NO_PROJECT + DEFAULT_OMP),
        "pareto_no_project_vs_pi": pareto(summaries, [CLEAN_PI, CLEAN_MEDIUM_PI, MEDIUM_PREAMBLE_PI] + NO_PROJECT),
    }
    (OUT / "summary.json").write_text(json.dumps(data, indent=2))
    print(json.dumps({
        "summaries": {c: {k:summaries[c][k] for k in ["solves","mean_partial","median_cost","median_tokens","median_wall_s","median_turns","median_tool_calls","provider_project_cells","provider_generate_image_cells","stale_usage_limit_cells","usage_mismatch_cells"]} for c in [CLEAN_PI]+NO_PROJECT},
        "pause_audit_counts": {k: len(v) for k,v in pause_audit.items()},
        "pairs_vs_pi": {c: {k:pairs[f'{CLEAN_PI}__vs__{c}'][k] for k in ["solve_delta","mean_delta_partial","median_delta_combined_cost_usd","median_delta_combined_total_tokens","mcnemar_p","wilcoxon_partial_p","b_only","a_only"]} for c in NO_PROJECT},
    }, indent=2))

if __name__ == "__main__":
    main()
