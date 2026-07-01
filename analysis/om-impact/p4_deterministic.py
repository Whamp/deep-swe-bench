"""P4 — Deterministic impact memory (no LLM).

Acts as the floor/control: how much blast-radius signal can a deterministic
codegraph digest capture WITHOUT any model distillation?

For each case:
  1. ensure the task repo graph is ready (checkout base commit + build)
  2. extract files touched in the chunk (executor tool-call paths)
  3. query codegraph for each file's symbols + their direct callers (names)
  4. emit one terse impact "record" per (caller, symbol) edge found in touched
     files, plus per-file summary records.

Output records mimic the observation shape (content + sourceEntryIds) so the
shared impact_capture metric scores them identically to P1/P2 observations.
They are deliberately NOT written into any session/ledger — this is an offline
prototype. No existing results are touched.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR, case_task_id, case_model_arm
from .impact_common import ensure_graph, extract_chunk_files, file_symbols


def run_case(case: dict) -> dict:
    tid = case_task_id(case)
    if not tid:
        return {"case_id": case.get("case_id"), "task": None, "status": "no_task",
                "records": [], "digest": ""}
    gdir, status, _meta = ensure_graph(tid)
    if gdir is None:
        return {"case_id": case.get("case_id"), "task": tid, "status": status,
                "records": [], "digest": "", "files": []}
    files = extract_chunk_files(case.get("chunk", ""), gdir)
    records: list[dict] = []
    digest_lines: list[str] = []
    for fp in files[:6]:
        syms = file_symbols(gdir, fp)
        if not syms:
            continue
        digest_lines.append(f"{fp}:")
        for s in syms:
            callers = s.get("callers") or []
            sym = s.get("name")
            digest_lines.append(f"  {sym} ({s.get('kind','?')}) <- {len(callers)} caller(s)")
            # one record per caller edge — terse, graph-derived, validated
            for c in callers[:8]:
                records.append({
                    "content": f"{c} calls {sym} ({fp}:{s.get('line','?')}) — blast radius if {sym} changes",
                    "sourceEntryIds": case.get("allowedSourceEntryIds", [])[:1],
                    "kind": "impact",
                    "caller": c,
                    "symbol": sym,
                    "file": fp,
                })
    return {
        "case_id": case.get("case_id"),
        "task": tid,
        "status": "ok",
        "files": files,
        "digest": "\n".join(digest_lines),
        "records": records,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default=str(CASESDIR / "impact_subset.jsonl"))
    ap.add_argument("--out", default=str(RUNSDIR / "p4-deterministic.jsonl"))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    cpath = Path(a.cases)
    opath = Path(a.out)
    opath.parent.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(l) for l in cpath.read_text().splitlines() if l.strip()]
    if a.limit:
        rows = rows[:a.limit]
    statuses: dict[str, int] = {}
    with opath.open("w") as f:
        for i, c in enumerate(rows, 1):
            res = run_case(c)
            statuses[res["status"]] = statuses.get(res["status"], 0) + 1
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            print(f"[P4 {i}/{len(rows)}] {res['task']}: {res['status']} "
                  f"files={len(res['files'])} records={len(res['records'])}", flush=True)
    print("\nP4 done. status counts:", statuses)
    print(f"-> {opath}")


if __name__ == "__main__":
    main()
