#!/usr/bin/env python3
"""Compounding cache burden + turn-sequence analysis: why OMP burns 3x tokens.

A tool result, once produced, stays in history and is re-cached on EVERY later
assistant turn. So total token cost ~= integral of cumulative-context over turns.
We compute, per cell: sum over assistant turns of cumulative_result_chars, which
is the result-derived portion of cache-read tokens. Plus per-turn wrapper cost.
"""
from __future__ import annotations
import json, statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "results" / "gpt-5.5" / "low"
SUBSET = (REPO / "subsets" / "36_v2.txt").read_text().split()

def cells(cfg):
    out=[]
    for rj in (RESULTS/cfg).rglob("result.json"):
        d=json.load(open(rj))
        if d["task"] in SUBSET and d["rep"] in (0,1,2):
            out.append(rj.parent)
    return out

def cell_sequence(cell_dir):
    """Return ordered list of events: ('assistant', None) or ('result', chars, tool)."""
    events=[]
    for sf in sorted((cell_dir/"session").glob("*.jsonl")):
        for line in open(sf, errors="ignore"):
            try: d=json.loads(line)
            except: continue
            if d.get("type")!="message": continue
            m=d.get("message",{}); role=m.get("role")
            ts=d.get("timestamp","")
            if role=="assistant":
                events.append((ts,"assistant",0,""))
            elif role=="toolResult":
                chars=sum(len(p.get("text","")) for p in (m.get("content") or []) if isinstance(p,dict))
                events.append((ts,"result",chars,m.get("toolName","?")))
    events.sort(key=lambda e:e[0])
    return events

def compounding(cfg):
    per_cell_recache=[]   # sum of cumulative_result_chars at each assistant turn
    per_cell_turns=[]; per_cell_result_total=[]
    for cd in cells(cfg):
        ev=cell_sequence(cd)
        cum=0; recache=0; turns=0; rtotal=0
        for ts,kind,chars,tn in ev:
            if kind=="result":
                cum+=chars; rtotal+=chars
            elif kind=="assistant":
                turns+=1
                recache+=cum   # this assistant turn re-caches all prior results
        per_cell_recache.append(recache)
        per_cell_turns.append(turns)
        per_cell_result_total.append(rtotal)
    return per_cell_recache, per_cell_turns, per_cell_result_total

def med(xs): return statistics.median(xs) if xs else 0

for cfg,label in [("baseline","Pi baseline"),("baseline-omp","OMP grep+glob")]:
    rc,tns,rtot=compounding(cfg)
    print(f"\n=== {label} ===")
    print(f"  median turns/cell:             {med(tns):>8.0f}")
    print(f"  median result chars/cell:      {med(rtot):>12,.0f}")
    print(f"  median re-cache char-turns:    {med(rc):>14,.0f}   (cumulative results × later turns)")

# head to head
rc_p,tn_p,_=compounding("baseline")
rc_o,tn_o,_=compounding("baseline-omp")
print(f"\n=== compounding ratio ===")
print(f"  re-cache burden: OMP/Pi = {med(rc_o)/med(rc_p):.2f}x  ({med(rc_o):,.0f} vs {med(rc_p):,.0f})")
print(f"  turns:           OMP/Pi = {med(tn_o)/med(tn_p):.2f}x")
print(f"  -> result content alone, re-cached over OMP's longer runs, explains a large share of the 3x token gap")

# wrapper contribution (known constants from prior forensic)
print(f"\n=== wrapper contribution (per-turn system-prompt+tool-defs, re-cached each turn) ===")
WP=1891; WO=7968  # Pi turn-1 input ~1891; OMP nonMessageTokens 7968 (10685 on one task)
print(f"  Pi  wrapper: {WP:,} tok × {med(tn_p):.0f} turns = {WP*med(tn_p):,.0f} tok/cell (median)")
print(f"  OMP wrapper: {WO:,} tok × {med(tn_o):.0f} turns = {WO*med(tn_o):,.0f} tok/cell (median)")
print(f"  wrapper ratio OMP/Pi = {WO*med(tn_o)/(WP*med(tn_p)):.2f}x")
