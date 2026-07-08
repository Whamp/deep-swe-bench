#!/usr/bin/env python3
"""Per-call tool-result size analysis: OMP vs Pi on 36_v2.

Tests whether OMP's tools return less per call (forcing more calls),
or whether OMP just chooses to call more. Also measures the compounding
cache burden: tool results accumulate in history and get re-cached every
subsequent turn.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "gpt-5.5" / "low"
SUBSET = (REPO / "subsets" / "36_v2.txt").read_text().split()

def cells(cfg):
    root = RESULTS / cfg
    out = []
    for rj in root.rglob("result.json"):
        d = json.load(open(rj))
        if d["task"] in SUBSET and d["rep"] in (0,1,2):
            out.append((d["task"], d["rep"], rj.parent))
    return out

def result_sizes_per_tool(cfg, limit=None):
    """Return {tool: [result_char_sizes]} across cells, plus per-cell totals."""
    by_tool = {}
    per_cell_result_chars = []
    per_cell_calls = []
    cell_list = cells(cfg)
    if limit: cell_list = cell_list[:limit]
    for task, rep, cell_dir in cell_list:
        sess_dir = cell_dir / "session"
        cell_total_chars = 0
        cell_calls = 0
        for sf in sess_dir.glob("*.jsonl"):
            for line in open(sf, errors="ignore"):
                try: d = json.loads(line)
                except: continue
                if d.get("type") != "message": continue
                m = d.get("message", {})
                if m.get("role") != "toolResult": continue
                tn = m.get("toolName", "?")
                size = sum(len(p.get("text","")) for p in (m.get("content") or []) if isinstance(p, dict))
                by_tool.setdefault(tn, []).append(size)
                cell_total_chars += size
                cell_calls += 1
        per_cell_result_chars.append(cell_total_chars)
        per_cell_calls.append(cell_calls)
    return by_tool, per_cell_result_chars, per_cell_calls

def med(xs): return statistics.median(xs) if xs else 0

def report(cfg, label):
    by_tool, per_cell_chars, per_cell_calls = result_sizes_per_tool(cfg)
    total_calls = sum(len(v) for v in by_tool.values())
    total_chars = sum(sum(v) for v in by_tool.values())
    print(f"\n=== {label} ({cfg}) ===  [{len(per_cell_chars)} cells, {total_calls} tool results, {total_chars:,} result chars]")
    print(f"  per-cell: median tool results = {med(per_cell_calls):.0f}, median result chars = {med(per_cell_chars):,.0f}")
    print(f"  {'tool':<12} {'calls':>7} {'tot_chars':>12} {'med_chars/call':>16} {'mean_chars/call':>16}")
    # sort by total chars desc
    for tn in sorted(by_tool, key=lambda t: -sum(by_tool[t])):
        v = by_tool[tn]
        print(f"  {tn:<12} {len(v):>7} {sum(v):>12,} {med(v):>16,.0f} {statistics.fmean(v):>16,.0f}")
    return by_tool, per_cell_chars, per_cell_calls

pi = report("baseline", "Pi baseline")
omp = report("baseline-omp", "OMP grep+glob")

# head-to-head per tool
print("\n=== head-to-head: median chars per call (OMP vs Pi) ===")
print(f"  {'tool':<12} {'Pi med/call':>14} {'OMP med/call':>14} {'OMP/Pi':>8}  {'Pi calls':>9} {'OMP calls':>10} {'call ratio':>10}")
all_tools = sorted(set(pi[0]) | set(omp[0]), key=lambda t: -(sum(omp[0].get(t,[0]))))
for tn in all_tools:
    pv = pi[0].get(tn, []); ov = omp[0].get(tn, [])
    pm, om = med(pv), med(ov)
    ratio = om/pm if pm else float('inf')
    cr = len(ov)/len(pv) if pv else float('inf')
    print(f"  {tn:<12} {pm:>14,.0f} {om:>14,.0f} {ratio:>7.2f}x  {len(pv):>9} {len(ov):>10} {cr:>9.2f}x")

# compounding: total result chars re-cached = sum over calls of (chars * remaining_turns_after)
print("\n=== compounding cache burden (result chars × re-cache count) ===")
print("  Every tool result stays in history and is re-cached on each later turn.")
print(f"  Pi  median result chars/cell:  {med(pi[1]):>12,.0f}")
print(f"  OMP median result chars/cell:  {med(omp[1]):>12,.0f}   ({med(omp[1])/med(pi[1]):.2f}x Pi)")
