"""Per-task breakdown + sample observations (run via -m so relative imports work)."""
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR
from .metrics.impact_capture import score_case


def load(p):
    return {json.loads(l)["case_id"]: json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()}


def main():
    cases = {json.loads(l)["case_id"]: json.loads(l) for l in (CASESDIR / "impact_subset.jsonl").read_text().splitlines() if l.strip()}
    p1 = load(str(RUNSDIR / "p1-live.jsonl")); p2 = load(str(RUNSDIR / "p2-live.jsonl")); p4 = load(str(RUNSDIR / "p4-deterministic.jsonl"))
    clean = sorted(cid for cid, r in p1.items() if len(r.get("observations", [])) > 0)

    def cc(run, cid):
        r = run.get(cid, {})
        recs = r.get("observations") or r.get("records") or []
        return score_case(cases[cid], recs)["caller_capture"] or 0.0

    bytask = defaultdict(list)
    for cid in clean:
        bytask[cases[cid]["session_path"].split("/")[4]].append(cid)

    print(f"{'task':32} {'P4':>6} {'P1':>6} {'P2':>6}  P4wins?")
    p4wins = 0
    for t, cids in sorted(bytask.items()):
        a = round(st.mean([cc(p4, c) for c in cids]), 2)
        b = round(st.mean([cc(p1, c) for c in cids]), 2)
        c = round(st.mean([cc(p2, c) for c in cids]), 2)
        w = "YES" if a >= max(b, c) else "no"
        p4wins += 1 if w == "YES" else 0
        print(f"{t[:32]:32} {a:>6} {b:>6} {c:>6}  {w}")
    print(f"\nP4 wins/ties on {p4wins}/{len(bytask)} tasks")

    print("\n--- sample P1 observations from a tool-calling arktype case ---")
    for cid in clean:
        if p1[cid].get("n_tool_calls", 0) > 0 and "arktype" in cases[cid]["session_path"]:
            tc = p1[cid].get("tool_calls", [])
            print(f"task=arktype tool_calls={p1[cid]['n_tool_calls']} symbols queried:", [x.get("symbol") for x in tc])
            for o in p1[cid]["observations"][:4]:
                print("  -", o.get("content", "")[:140])
            break


if __name__ == "__main__":
    main()
