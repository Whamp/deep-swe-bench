"""P2 prep — enrich observer replay cases with a codegraph blast-radius digest.

For each case: ensure graph, extract touched source files, compute a TIGHT
digest (capped files/symbols/callers so it stays observer-cheap), append it to
the chunk text. Output is a NEW cases file; original om-gepa cases untouched.

The enriched cases are then replayed through the STOCK observer runner (no agent
or tool changes) with a real model, so P2 isolates: does injected blast context
get distilled into observations?
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR, case_task_id, ensure_graph, extract_chunk_files, file_symbols

DIGEST_HEADER = "[codegraph blast-radius digest for files touched since last observation]"
DIGEST_FOOTER = "[/codegraph digest — weight observations of high-caller symbols toward reflection]"


def compute_inject_digest(graph_dir, files, max_files=4, max_syms=6, max_callers=5) -> str:
    if not files:
        return ""
    lines = [DIGEST_HEADER]
    for fp in files[:max_files]:
        syms = file_symbols(graph_dir, fp, limit=max_syms)
        if not syms:
            continue
        lines.append(f"{fp}:")
        for s in syms:
            callers = (s.get("callers") or [])[:max_callers]
            n = len(s.get("callers") or [])
            tag = f"{n} caller(s)" + (f": {', '.join(callers)}" if callers else "")
            lines.append(f"  - {s['name']} ({s.get('kind','?')}): {tag}")
    if len(lines) == 1:
        return ""
    lines.append(DIGEST_FOOTER)
    return "\n".join(lines)


def enrich_case(case: dict) -> dict:
    out = dict(case)
    tid = case_task_id(case)
    if not tid:
        out["_p2_status"] = "no_task"
        return out
    gdir, status, _ = ensure_graph(tid)
    if gdir is None:
        out["_p2_status"] = status
        return out
    files = extract_chunk_files(case.get("chunk", ""), gdir)
    digest = compute_inject_digest(gdir, files)
    if digest:
        out["chunk"] = (case.get("chunk", "") + "\n\n" + digest)
        out["_p2_status"] = "ok"
        out["_p2_files"] = files
        out["_p2_digest_len"] = len(digest)
    else:
        out["_p2_status"] = "empty_digest"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default=str(CASESDIR / "impact_subset.jsonl"))
    ap.add_argument("--out", default=str(CASESDIR / "p2_enriched.jsonl"))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    rows = [json.loads(l) for l in Path(a.cases).read_text().splitlines() if l.strip()]
    if a.limit:
        rows = rows[:a.limit]
    opath = Path(a.out)
    opath.parent.mkdir(parents=True, exist_ok=True)
    statuses: dict[str, int] = {}
    with opath.open("w") as f:
        for i, c in enumerate(rows, 1):
            e = enrich_case(c)
            statuses[e.get("_p2_status", "?")] = statuses.get(e.get("_p2_status", "?"), 0) + 1
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
            print(f"[P2-enrich {i}/{len(rows)}] {case_task_id(c)}: {e.get('_p2_status')} "
                  f"files={len(e.get('_p2_files',[]))} digest_len={e.get('_p2_digest_len',0)}", flush=True)
    print("\nP2 enrich done. status counts:", statuses)
    print(f"-> {opath}")


if __name__ == "__main__":
    main()
