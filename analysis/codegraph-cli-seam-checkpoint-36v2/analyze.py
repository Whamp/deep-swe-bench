#!/usr/bin/env python3
"""Paired analysis for the CodeGraph seam-checkpoint skill variant.

Headline comparison: seam-checkpoint skill vs the original codegraph-cli-skill
(isolates the skill-text change while holding model/tools/prompt constant).
Also reports vs clean baseline, workflow prompt, and clean GPT-5.5 medium.
"""
from __future__ import annotations

import json
import math
import re
import statistics as stats
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from scipy.stats import wilcoxon
except Exception:  # pragma: no cover
    wilcoxon = None

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SUBSET = ROOT / "subsets" / "36_v2.txt"
DIFF = ROOT / "data" / "deepswe-v1.1-task-difficulty.tsv"
MODEL = "gpt-5.5"
THINKING = "low"
BASE = ROOT / "results" / MODEL / THINKING

PRIMARY = "codegraph-cli-skill-seam-checkpoint"
OLD_CODEGRAPH = "codegraph-cli-skill"  # the non-seam sibling: isolates the skill-text change
BASELINE = "baseline"
CODEGRAPH_SKILL = "codegraph-skill"
WF_ONLY = "baseline-wf-only"
GOAL = "pi-codex-goal"
CLEAN_MEDIUM = "baseline__gpt55_medium"
PREAMBLE_MEDIUM = "baseline-preamble-orchestration__gpt55_medium"
CONFIG_PATHS = {
    CLEAN_MEDIUM: ROOT / "results" / "gpt-5.5" / "medium" / "baseline",
    PREAMBLE_MEDIUM: ROOT / "results" / "gpt-5.5" / "medium" / "baseline-preamble-orchestration",
}
CONFIGS = [BASELINE, OLD_CODEGRAPH, PRIMARY, CODEGRAPH_SKILL, WF_ONLY, GOAL, CLEAN_MEDIUM, PREAMBLE_MEDIUM]
LABELS = {
    BASELINE: "Clean Pi · low",
    OLD_CODEGRAPH: "CodeGraph CLI · low (old skill)",
    PRIMARY: "CodeGraph CLI · low (seam skill)",
    CODEGRAPH_SKILL: "CodeGraph skill · low",
    WF_ONLY: "Workflow prompt · low",
    GOAL: "pi-codex-goal · low",
    CLEAN_MEDIUM: "Clean Pi · medium",
    PREAMBLE_MEDIUM: "Pi preamble/orch · medium",
}


def task_list() -> list[str]:
    return [l.strip() for l in SUBSET.read_text().splitlines() if l.strip() and not l.startswith("#")]


def difficulty() -> dict[str, dict[str, Any]]:
    out = {}
    with DIFF.open() as f:
        header = f.readline().strip().split("\t")
        for line in f:
            if not line.strip():
                continue
            cols = line.rstrip("\n").split("\t")
            rec = dict(zip(header, cols))
            pr = float(rec["pass_rate"])
            bucket = "hard" if pr < 33 else "medium" if pr < 66 else "easy"
            out[rec["slug"]] = {
                "pass_rate": pr,
                "difficulty": bucket,
                "language": rec["language"],
                "title": rec["title"],
                "repository": rec["repository"],
            }
    return out


def config_base(config: str) -> Path:
    return CONFIG_PATHS.get(config, BASE / config)


def load_cell(config: str, task: str, rep: int, diff: dict[str, Any]) -> dict[str, Any] | None:
    p = config_base(config) / task / f"rep{rep}" / "result.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text())
    d = diff[task]
    r.update({"task": task, "rep": rep, "difficulty": d["difficulty"], "language": d["language"], "title": d["title"], "result_path": str(p)})
    return r


def median(xs):
    xs = [x for x in xs if x is not None]
    return stats.median(xs) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    solves = sum(1 for r in rows if r.get("reward_binary") == 1)
    tool_counts = Counter()
    for r in rows:
        tc = r.get("tool_counts") or {}
        tool_counts.update(tc)
    return {
        "n": n,
        "solves": solves,
        "solve_rate": solves / n if n else 0,
        "mean_partial": mean([r.get("reward_partial") for r in rows]),
        "median_partial": median([r.get("reward_partial") for r in rows]),
        "median_tokens": median([r.get("combined_total_tokens", r.get("total_tokens")) for r in rows]),
        "total_tokens": sum(r.get("combined_total_tokens", r.get("total_tokens", 0)) or 0 for r in rows),
        "median_cost": median([r.get("combined_cost_usd", r.get("cost_usd")) for r in rows]),
        "total_cost": sum(r.get("combined_cost_usd", r.get("cost_usd", 0)) or 0 for r in rows),
        "median_wall_s": median([r.get("agent_wall_s") for r in rows]),
        "median_turns": median([r.get("turns") for r in rows]),
        "median_tool_calls": median([r.get("tool_calls") for r in rows]),
        "median_patch_bytes": median([r.get("patch_bytes") for r in rows]),
        "timeouts": sum(1 for r in rows if r.get("agent_timed_out")),
        "empty_patches": sum(1 for r in rows if (r.get("patch_bytes") or 0) == 0),
        "reward_minus_one": sum(1 for r in rows if r.get("reward_binary") == -1 or r.get("reward_partial") == -1),
        "stderr_nonempty": sum(1 for r in rows if Path(r["result_path"]).with_name("logs").joinpath("pi.stderr.txt").exists() and Path(r["result_path"]).with_name("logs").joinpath("pi.stderr.txt").stat().st_size > 0),
        "tool_counts": dict(tool_counts),
        "by_difficulty": by_group(rows, "difficulty"),
        "by_language": by_group(rows, "language"),
    }


def by_group(rows, key):
    out = {}
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    for k, rs in groups.items():
        out[k] = {
            "n": len(rs),
            "solves": sum(1 for r in rs if r.get("reward_binary") == 1),
            "mean_partial": mean([r.get("reward_partial") for r in rs]),
            "median_cost": median([r.get("combined_cost_usd", r.get("cost_usd")) for r in rs]),
            "median_tokens": median([r.get("combined_total_tokens", r.get("total_tokens")) for r in rs]),
        }
    return out


def binom_two_sided(k, n, p=0.5):
    if n <= 0:
        return None
    prob = sum(math.comb(n, i) * (p**i) * ((1-p)**(n-i)) for i in range(k + 1))
    return min(1.0, 2 * min(prob, 1 - prob + math.comb(n, k) * (p**k) * ((1-p)**(n-k))))


def paired(a: str, b: str, rows: dict[str, dict[tuple[str, int], dict[str, Any]]]) -> dict[str, Any]:
    pairs = []
    for key, ar in rows[a].items():
        br = rows[b].get(key)
        if br:
            pairs.append((ar, br))
    a_solves = sum(1 for ar, _ in pairs if ar.get("reward_binary") == 1)
    b_solves = sum(1 for _, br in pairs if br.get("reward_binary") == 1)
    a_only = sum(1 for ar, br in pairs if ar.get("reward_binary") == 1 and br.get("reward_binary") != 1)
    b_only = sum(1 for ar, br in pairs if ar.get("reward_binary") != 1 and br.get("reward_binary") == 1)
    deltas = [(br.get("reward_partial") or 0) - (ar.get("reward_partial") or 0) for ar, br in pairs]
    nonzero = [d for d in deltas if abs(d) > 1e-12]
    try:
        wp = float(wilcoxon(deltas, zero_method="wilcox").pvalue) if wilcoxon and nonzero else None
    except Exception:
        wp = None
    cells = []
    for ar, br in pairs:
        cells.append({
            "task": ar["task"], "rep": ar["rep"], "title": ar["title"], "difficulty": ar["difficulty"], "language": ar["language"],
            "a_solved": ar.get("reward_binary") == 1, "b_solved": br.get("reward_binary") == 1,
            "a_partial": ar.get("reward_partial"), "b_partial": br.get("reward_partial"),
            "delta_partial": (br.get("reward_partial") or 0) - (ar.get("reward_partial") or 0),
            "delta_cost": (br.get("combined_cost_usd", br.get("cost_usd")) or 0) - (ar.get("combined_cost_usd", ar.get("cost_usd")) or 0),
            "delta_tokens": (br.get("combined_total_tokens", br.get("total_tokens")) or 0) - (ar.get("combined_total_tokens", ar.get("total_tokens")) or 0),
            "delta_wall_s": (br.get("agent_wall_s") or 0) - (ar.get("agent_wall_s") or 0),
            "delta_tool_calls": (br.get("tool_calls") or 0) - (ar.get("tool_calls") or 0),
            "a_cost": ar.get("combined_cost_usd", ar.get("cost_usd")), "b_cost": br.get("combined_cost_usd", br.get("cost_usd")),
        })
    difficulty_rows = {}
    for bucket in ["hard", "medium", "easy"]:
        cs = [c for c in cells if c["difficulty"] == bucket]
        difficulty_rows[bucket] = {
            "n": len(cs),
            "a_solves": sum(c["a_solved"] for c in cs),
            "b_solves": sum(c["b_solved"] for c in cs),
            "solve_delta": sum(c["b_solved"] for c in cs) - sum(c["a_solved"] for c in cs),
            "mean_delta_partial": mean([c["delta_partial"] for c in cs]),
            "median_delta_cost": median([c["delta_cost"] for c in cs]),
            "median_delta_tokens": median([c["delta_tokens"] for c in cs]),
        }
    return {
        "n": len(pairs),
        "a": a, "b": b, "a_label": LABELS[a], "b_label": LABELS[b],
        "a_solves": a_solves, "b_solves": b_solves, "solve_delta": b_solves - a_solves,
        "both_solved": sum(1 for ar, br in pairs if ar.get("reward_binary") == 1 and br.get("reward_binary") == 1),
        "neither_solved": sum(1 for ar, br in pairs if ar.get("reward_binary") != 1 and br.get("reward_binary") != 1),
        "a_only": a_only, "b_only": b_only,
        "mcnemar_p": binom_two_sided(min(a_only, b_only), a_only + b_only) if (a_only + b_only) else None,
        "mean_delta_partial": mean(deltas), "median_delta_partial": median(deltas), "wilcoxon_partial_p": wp,
        "median_delta_cost": median([c["delta_cost"] for c in cells]),
        "median_delta_tokens": median([c["delta_tokens"] for c in cells]),
        "median_delta_wall_s": median([c["delta_wall_s"] for c in cells]),
        "median_delta_tool_calls": median([c["delta_tool_calls"] for c in cells]),
        "improved_cells": sum(1 for d in deltas if d > 1e-12),
        "worsened_cells": sum(1 for d in deltas if d < -1e-12),
        "tied_cells": sum(1 for d in deltas if abs(d) <= 1e-12),
        "difficulty": difficulty_rows,
        "top_wins": sorted(cells, key=lambda c: c["delta_partial"], reverse=True)[:12],
        "top_losses": sorted(cells, key=lambda c: c["delta_partial"])[:12],
        "solve_gains": sorted([c for c in cells if c["b_solved"] and not c["a_solved"]], key=lambda c: c["delta_partial"], reverse=True),
        "solve_losses": sorted([c for c in cells if c["a_solved"] and not c["b_solved"]], key=lambda c: c["delta_partial"]),
    }


def pareto(summaries: dict[str, dict[str, Any]], configs: list[str]):
    rows = []
    for c in configs:
        s = summaries[c]
        dominated = []
        for d in configs:
            if d == c:
                continue
            t = summaries[d]
            if t["solves"] >= s["solves"] and t["median_cost"] <= s["median_cost"] and (t["solves"] > s["solves"] or t["median_cost"] < s["median_cost"]):
                dominated.append(d)
        rows.append({"config": c, "label": LABELS[c], "solves": s["solves"], "median_cost": s["median_cost"], "mean_partial": s["mean_partial"], "dominated_by": dominated})
    return sorted(rows, key=lambda r: (r["median_cost"], -r["solves"]))


def session_paths(config: str, task: str, rep: int) -> list[Path]:
    d = config_base(config) / task / f"rep{rep}" / "session"
    return sorted(d.glob("*.jsonl")) if d.exists() else []


def tool_calls_from_message(m: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    content = m.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "toolCall":
                out.append({"name": item.get("name"), "arguments": item.get("arguments") or {}})
    return out


def codegraph_usage(rows: dict[tuple[str, int], dict[str, Any]], config: str) -> dict[str, Any]:
    cell_stats = {}
    command_counter = Counter()
    total_calls = 0
    codegraph_cells = 0
    read_skill_cells = 0
    build_cells = 0
    for (task, rep), r in rows.items():
        calls = []
        read_skill = False
        for sp in session_paths(config, task, rep):
            try:
                lines = sp.read_text(errors="ignore").splitlines()
            except Exception:
                continue
            for line in lines:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                m = obj.get("message") if isinstance(obj.get("message"), dict) else {}
                for tc in tool_calls_from_message(m):
                    name = tc.get("name")
                    args = tc.get("arguments") or {}
                    if name == "read" and "/arm/skills/codegraph" in str(args.get("path", "")):
                        read_skill = True
                    if name == "bash":
                        cmd = str(args.get("command", ""))
                        if re.search(r"(^|[;&|\s])(codegraph|cg)(\s|$)", cmd):
                            calls.append(cmd)
                            if "codegraph build" in cmd or re.search(r"(^|[;&|\s])cg build(\s|$)", cmd):
                                command_counter["build"] += 1
                            if "codegraph structure" in cmd or " cg structure" in cmd:
                                command_counter["structure"] += 1
                            for sub in ["locate", "impact", "diff-impact", "callers", "callees", "search", "context", "stats", "check", "where", "brief", "cycles", "dead", "deps", "fn-impact", "implementations", "interfaces", "map", "triage", "complexity", "roles", "exports", "dataflow"]:
                                if f"codegraph {sub}" in cmd or f" cg {sub}" in cmd:
                                    command_counter[sub] += 1
        if calls:
            codegraph_cells += 1
        if any("codegraph build" in c or re.search(r"(^|[;&|\s])cg build(\s|$)", c) for c in calls):
            build_cells += 1
        if read_skill:
            read_skill_cells += 1
        total_calls += len(calls)
        cell_stats[f"{task}/rep{rep}"] = {
            "task": task, "rep": rep, "codegraph_calls": len(calls), "commands": calls[:10], "read_skill": read_skill,
            "solved": r.get("reward_binary") == 1, "partial": r.get("reward_partial"), "difficulty": r["difficulty"], "title": r["title"],
            "tokens": r.get("combined_total_tokens", r.get("total_tokens")), "cost": r.get("combined_cost_usd", r.get("cost_usd")),
        }
    by_calls = defaultdict(list)
    for cs in cell_stats.values():
        by_calls["used" if cs["codegraph_calls"] else "unused"].append(cs)
    usage_groups = {}
    for k, cs in by_calls.items():
        usage_groups[k] = {
            "n": len(cs), "solves": sum(c["solved"] for c in cs), "mean_partial": mean([c["partial"] for c in cs]),
            "median_tokens": median([c["tokens"] for c in cs]), "median_cost": median([c["cost"] for c in cs]),
        }
    return {
        "cells": len(rows), "codegraph_cells": codegraph_cells, "build_cells": build_cells, "read_skill_cells": read_skill_cells,
        "total_codegraph_calls": total_calls, "command_counter": dict(command_counter), "groups": usage_groups,
        "top_call_cells": sorted(cell_stats.values(), key=lambda x: x["codegraph_calls"], reverse=True)[:20],
        "zero_call_cells": [c for c in cell_stats.values() if c["codegraph_calls"] == 0][:20],
        "cell_stats": cell_stats,
    }


def prompt_audit(rows: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    vals = []
    missing = 0
    prompt_has = []
    for (_, _), r in rows.items():
        d = Path(r["result_path"]).parent
        ic = d / "initial_context"
        sys = (ic / "system_prompt.txt")
        if sys.exists():
            txt = sys.read_text(errors="ignore")
            vals.append(len(txt))
            prompt_has.append("You should use `codegraph` cli to assist you." in txt)
        else:
            missing += 1
    return {"initial_context_missing": missing, "system_prompt_chars_median": median(vals), "system_prompt_chars_min": min(vals) if vals else None, "system_prompt_chars_max": max(vals) if vals else None, "codegraph_sentence_cells": sum(prompt_has), "cells_checked": len(prompt_has)}


def main():
    tasks = task_list()
    diff = difficulty()
    rows_by_config = {}
    list_by_config = {}
    for c in CONFIGS:
        rows = {}
        lst = []
        for t in tasks:
            for rep in range(3):
                r = load_cell(c, t, rep, diff)
                if r:
                    rows[(t, rep)] = r
                    lst.append(r)
        rows_by_config[c] = rows
        list_by_config[c] = lst
    summaries = {c: summary(rs) for c, rs in list_by_config.items()}
    pairs = {}
    # Headline: seam skill vs old skill (isolates the skill-text change)
    pair_specs = [
        (OLD_CODEGRAPH, PRIMARY),
        (BASELINE, PRIMARY),
        (CODEGRAPH_SKILL, PRIMARY),
        (WF_ONLY, PRIMARY),
        (PRIMARY, CLEAN_MEDIUM),
        (BASELINE, OLD_CODEGRAPH),
        (BASELINE, WF_ONLY),
        (BASELINE, GOAL),
        (BASELINE, CLEAN_MEDIUM),
    ]
    for a, b in pair_specs:
        pairs[f"{a}__vs__{b}"] = paired(a, b, rows_by_config)
    primary_rows = rows_by_config[PRIMARY]
    old_rows = rows_by_config[OLD_CODEGRAPH]
    run_status = json.loads((ROOT / "results/_runs/gpt55-low-codegraph-cli-seam-checkpoint-36v2-r3-w24/status.json").read_text()) if (ROOT / "results/_runs/gpt55-low-codegraph-cli-seam-checkpoint-36v2-r3-w24/status.json").exists() else None
    treatment = {
        "config_readme": (ROOT / "configs/codegraph-cli-skill-seam-checkpoint/README.md").read_text(errors="ignore")[:4000],
        "orchestration": (ROOT / "configs/codegraph-cli-skill-seam-checkpoint/orchestration.md").read_text(errors="ignore").strip(),
        "env": (ROOT / "configs/codegraph-cli-skill-seam-checkpoint/env").read_text(errors="ignore").strip(),
        "smoke": json.loads((ROOT / "configs/codegraph-cli-skill-seam-checkpoint/gpt-5.5/low/smoke.json").read_text()),
        "prompt_audit": prompt_audit(primary_rows),
        "skill_has_seam_checkpoint": "seam checkpoint" in (ROOT / "configs/codegraph-cli-skill-seam-checkpoint/skills/codegraph/SKILL.md").read_text(errors="ignore").lower(),
        "skill_has_behavioral_seam": "Choose the behavioral seam before editing" in (ROOT / "configs/codegraph-cli-skill-seam-checkpoint/skills/codegraph/SKILL.md").read_text(errors="ignore"),
    }
    out = {
        "run_id": "gpt55-low-codegraph-cli-seam-checkpoint-36v2-r3-w24", "subset": "36_v2", "model": MODEL, "thinking": THINKING,
        "tasks": tasks, "configs": CONFIGS, "labels": LABELS,
        "coverage": {c: {"cells": len(rows_by_config[c]), "tasks": len(set(t for t, _ in rows_by_config[c]))} for c in CONFIGS},
        "run_status": run_status,
        "summaries": summaries,
        "pairs": pairs,
        "codegraph_usage_seam": codegraph_usage(primary_rows, PRIMARY),
        "codegraph_usage_old": codegraph_usage(old_rows, OLD_CODEGRAPH),
        "treatment": treatment,
        "pareto": pareto(summaries, CONFIGS),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(out, indent=2, sort_keys=True))
    print(OUT / "summary.json")


if __name__ == "__main__":
    main()
