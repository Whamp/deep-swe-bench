"""impact_capture_rate: does a prototype's memory output carry real blast-radius signal?

For each prototype output (observations OR deterministic impact records) we ask:
  - caller_capture  : fraction of the task's gold CALLERS named in the output
  - edge_capture    : fraction of gold (caller,goldSym) EDGES whose caller appears
                      (edge fully captured if both endpoints named)
  - n_records       : how many records/observations emitted
  - has_file_refs   : did the output reference any touched file at all

Ground truth = analysis/attention-edges/subgraphs/<task>.json (the real
caller->changed-symbol edges from codegraph on the repo at base commit).

This is the same caller-matching attention_edges applies to executor sessions,
but here applied to the prototype's *memory stream* — exactly the question:
does the durable observation/reflection layer carry the relationship signal?
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..impact_common import case_task_id, gold_callers, gold_edges, gold_symbols


def _sym_matcher(sym: str) -> re.Pattern:
    # word-boundary, like attention_edges turn matcher; symbols are identifiers
    return re.compile(r"(?:^|[^\w$])" + re.escape(sym) + r"(?:[^\w$]|$)")


def _norm_text(records: list[dict[str, Any]]) -> str:
    parts = []
    for r in records:
        parts.append(str(r.get("content", "")))
        parts.append(str(r.get("sourceEntryIds", "")))
    return " " + " ".join(parts)


def score_case(case: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    tid = case_task_id(case)
    g_callers = gold_callers(tid)
    g_syms = gold_symbols(tid)
    g_edges = gold_edges(tid)
    blob = _norm_text(records)
    cap_c = {c for c in g_callers if _sym_matcher(c).search(blob)} if g_callers else set()
    cap_s = {s for s in g_syms if _sym_matcher(s).search(blob)} if g_syms else set()
    edge_hits = 0
    for caller, sym in g_edges:
        if _sym_matcher(caller).search(blob) and _sym_matcher(sym).search(blob):
            edge_hits += 1
    return {
        "task": tid,
        "case_id": case.get("case_id"),
        "n_records": len(records),
        "n_gold_callers": len(g_callers),
        "n_gold_edges": len(g_edges),
        "caller_capture": round(len(cap_c) / len(g_callers), 3) if g_callers else None,
        "symbol_capture": round(len(cap_s) / len(g_syms), 3) if g_syms else None,
        "edge_capture": round(edge_hits / len(g_edges), 3) if g_edges else None,
        "captured_callers": sorted(cap_c),
        "gold_callers": sorted(g_callers),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    import statistics as st
    def m(k):
        v = [r[k] for r in rows if r.get(k) is not None]
        return round(st.mean(v), 3) if v else None
    return {
        "n_cases": len(rows),
        "mean_caller_capture": m("caller_capture"),
        "mean_edge_capture": m("edge_capture"),
        "mean_symbol_capture": m("symbol_capture"),
        "mean_n_records": m("n_records"),
        "tasks": sorted({r["task"] for r in rows}),
    }


def selftest() -> None:
    case = {"session_path": "results/m/t/c/abs-module-cache-flags/rep0/session/x.jsonl",
            "case_id": "x"}
    # synthetic records that name a real gold caller/symbol for this task
    gc = gold_callers("abs-module-cache-flags")
    ge = gold_edges("abs-module-cache-flags")
    assert gc and ge, (gc, ge)
    # pick a REAL (caller, sym) edge so edge_capture must be > 0
    sample_caller, sample_sym = next(iter(ge))
    records = [{"content": f"edited {sample_sym}; caller {sample_caller} affected"}]
    s = score_case(case, records)
    assert s["caller_capture"] is not None and s["caller_capture"] > 0, s
    assert s["edge_capture"] is not None and s["edge_capture"] > 0, s
    # empty records -> zero capture
    z = score_case(case, [])
    assert z["caller_capture"] == 0.0, z
    print("SELFTEST PASS", s["caller_capture"], s["edge_capture"])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
