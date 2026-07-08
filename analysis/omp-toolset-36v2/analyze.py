#!/usr/bin/env python3
"""OMP toolset comparison on GPT-5.5 low / 36_v2 (108 cells each).

Compares 4 configs:
  - Pi baseline (plain Pi, no extensions)
  - OMP grep+glob  (baseline-omp: read,bash,edit,write,grep,glob)
  - OMP bash-only  (baseline-omp-bash-only: read,bash,edit,write; grep/glob OFF)
  - OMP AST        (baseline-omp-ast: read,bash,edit,write,ast_grep,ast_edit; grep/glob OFF)

Key questions:
  1. Does removing grep/glob (bash-only) recover token efficiency?
  2. Do AST tools actually get used by GPT-5.5 low?
  3. Solve rates + Pareto placement vs plain Pi.

Outputs summary.json consumed by render_html.py.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "gpt-5.5" / "low"
SUBSET = (REPO / "subsets" / "36_v2.txt").read_text().split()

CONFIGS = [
    ("pi-baseline",       "baseline",              "Pi baseline"),
    ("omp-grepglob",      "baseline-omp",          "OMP grep+glob"),
    ("omp-bash-only",     "baseline-omp-bash-only","OMP bash-only"),
    ("omp-ast",           "baseline-omp-ast",      "OMP AST"),
]

def median(xs): return statistics.median(xs) if xs else 0.0
def mean(xs):   return statistics.fmean(xs) if xs else 0.0

def load_cells(cfg_dir: str) -> dict:
    """Return {(task, rep): result_dict} for 36_v2 x reps 0,1,2."""
    root = RESULTS / cfg_dir
    cells = {}
    for rj in root.rglob("result.json"):
        d = json.load(open(rj))
        if d["task"] in SUBSET and d["rep"] in (0, 1, 2):
            cells[(d["task"], d["rep"])] = d
    return cells

def tool_mix_omp(cells: dict) -> dict:
    """Parse OMP session JSONL custom events for per-tool counts."""
    totals = {}
    per_cell_totals = []
    for (task, rep), d in cells.items():
        sess_dir = Path(d.get("session_dir") or
                        f"results/gpt-5.5/low/{d['config']}/{task}/rep{rep}/session")
        # fall back to locating the session dir relative to result.json
        if not sess_dir.is_absolute():
            sess_dir = (REPO / sess_dir)
        cell_tools = {}
        for rj in [Path(f"results/gpt-5.5/low/{d['config']}/{task}/rep{rep}/result.json")]:
            pass
        # locate session jsonl robustly
        candidates = list((REPO / "results" / "gpt-5.5" / "low" / d["config"] / task / f"rep{rep}" / "session").glob("*.jsonl"))
        for sf in candidates:
            for line in open(sf, errors="ignore"):
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("type") == "custom" and ev.get("customType") == "tool_execution_start":
                    nm = (ev.get("data") or {}).get("toolName", "?")
                    cell_tools[nm] = cell_tools.get(nm, 0) + 1
                    totals[nm] = totals.get(nm, 0) + 1
        per_cell_totals.append(sum(cell_tools.values()))
    return {"totals": totals, "median_per_cell": median(per_cell_totals)}

def headline(cells: dict) -> dict:
    solves = sum(1 for d in cells.values() if d.get("reward_binary") == 1)
    n = len(cells)
    return {
        "n": n,
        "solves": solves,
        "solve_rate": solves / n if n else 0.0,
        "mean_partial": mean([d.get("reward_partial", 0.0) for d in cells.values()]),
        "median_tokens": median([d.get("total_tokens", 0) for d in cells.values()]),
        "median_cost":   median([d.get("cost_usd", 0.0) for d in cells.values()]),
        "median_wall":   median([d.get("agent_wall_s", 0.0) for d in cells.values()]),
        "median_patch":  median([d.get("patch_bytes", 0) for d in cells.values()]),
        "median_turns":  median([d.get("turns", 0) for d in cells.values()]),
        "median_tool_calls": median([d.get("tool_calls", 0) for d in cells.values()]),
        "total_cost":    sum(d.get("cost_usd", 0.0) for d in cells.values()),
        "median_output_tokens": median([d.get("output_tokens", 0) for d in cells.values()]),
        "median_cache_read": median([d.get("cache_read_tokens", 0) for d in cells.values()]),
    }

def paired(a: dict, b: dict) -> dict:
    """Paired deltas a vs b on shared (task, rep)."""
    keys = sorted(set(a) & set(b))
    dpart = [a[k].get("reward_partial", 0.0) - b[k].get("reward_partial", 0.0) for k in keys]
    dtok  = [a[k].get("total_tokens", 0) - b[k].get("total_tokens", 0) for k in keys]
    dcost = [a[k].get("cost_usd", 0.0) - b[k].get("cost_usd", 0.0) for k in keys]
    # solve agreement
    both = sum(1 for k in keys if a[k].get("reward_binary")==1 and b[k].get("reward_binary")==1)
    a_only = sum(1 for k in keys if a[k].get("reward_binary")==1 and b[k].get("reward_binary")!=1)
    b_only = sum(1 for k in keys if a[k].get("reward_binary")!=1 and b[k].get("reward_binary")==1)
    neither = sum(1 for k in keys if a[k].get("reward_binary")!=1 and b[k].get("reward_binary")!=1)
    return {
        "n_pairs": len(keys),
        "mean_delta_partial": mean(dpart),
        "median_delta_tokens": median(dtok),
        "median_delta_cost": median(dcost),
        "solve_both": both, "solve_a_only": a_only, "solve_b_only": b_only, "solve_neither": neither,
    }

def main():
    out = {"configs": {}, "subset": "36_v2", "n_per_config": 108}
    cells_by = {}
    for key, cfg_dir, label in CONFIGS:
        cells = load_cells(cfg_dir)
        cells_by[key] = cells
        h = headline(cells)
        h["label"] = label
        h["config_dir"] = cfg_dir
        if cfg_dir.startswith("baseline-omp"):
            h["tool_mix"] = tool_mix_omp(cells)
        out["configs"][key] = h

    # paired deltas: each OMP vs pi-baseline, and bash-only/AST vs omp-grepglob
    out["paired"] = {
        "omp-grepglob_vs_pi":   paired(cells_by["omp-grepglob"], cells_by["pi-baseline"]),
        "omp-bash-only_vs_pi":  paired(cells_by["omp-bash-only"], cells_by["pi-baseline"]),
        "omp-ast_vs_pi":        paired(cells_by["omp-ast"], cells_by["pi-baseline"]),
        "omp-bash-only_vs_grepglob": paired(cells_by["omp-bash-only"], cells_by["omp-grepglob"]),
        "omp-ast_vs_grepglob":       paired(cells_by["omp-ast"], cells_by["omp-grepglob"]),
        "omp-ast_vs_bash-only":      paired(cells_by["omp-ast"], cells_by["omp-bash-only"]),
    }

    # AST usage check
    ast = out["configs"]["omp-ast"]["tool_mix"]["totals"]
    out["ast_usage"] = {
        "ast_grep_calls": ast.get("ast_grep", 0) + ast.get("ast-grep", 0),
        "ast_edit_calls": ast.get("ast_edit", 0) + ast.get("ast-edit", 0),
        "note": "GPT-5.5 low voluntary usage; tools were registered/available",
    }

    out_path = Path(__file__).parent / "summary.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path}")
    # console summary
    print(f"\n{'config':<20} {'solves':>8} {'partial':>9} {'tok(med)':>12} {'cost(med)':>11} {'wall(med)':>10}")
    for key, _, _ in CONFIGS:
        c = out["configs"][key]
        print(f"{key:<20} {c['solves']}/{c['n']:>3} {c['mean_partial']:>9.4f} {c['median_tokens']:>12,} {c['median_cost']:>10.4f} {c['median_wall']:>9.0f}s")
    print("\nAST usage (voluntary):", out["ast_usage"])
    print("\nTool mix totals:")
    for key, _, _ in CONFIGS[1:]:
        print(f"  {key}: {out['configs'][key]['tool_mix']['totals']}")

if __name__ == "__main__":
    main()
