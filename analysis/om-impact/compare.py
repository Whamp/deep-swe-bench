"""Score P1/P2/P4 on a matched case subset and emit a side-by-side comparison.

Fairness: P1 lost cases 22-24 to an OpenAI-codex rate limit (obs=0 empty output).
So we score ALL THREE prototypes on the identical set of clean P1 case_ids.
Also reports P1 tool-call rate (the core assumption test).
"""
from __future__ import annotations

import json
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR
from .metrics.impact_capture import score_case, aggregate


def load_rows(path: str) -> dict[str, dict]:
    return {json.loads(l)["case_id"]: json.loads(l)
            for l in Path(path).read_text().splitlines() if l.strip()}


def main() -> None:
    cases = {json.loads(l)["case_id"]: json.loads(l)
             for l in (CASESDIR / "impact_subset.jsonl").read_text().splitlines() if l.strip()}
    p1 = load_rows(str(RUNSDIR / "p1-live.jsonl"))
    p2 = load_rows(str(RUNSDIR / "p2-live.jsonl"))
    p4 = load_rows(str(RUNSDIR / "p4-deterministic.jsonl"))

    # matched subset = clean P1 cases (obs>0 OR clearly not empty; drop obs=0)
    clean_ids = sorted(cid for cid, r in p1.items() if len(r.get("observations", [])) > 0)
    dropped = sorted(set(p1) - set(clean_ids))
    print(f"matched subset: {len(clean_ids)} clean P1 cases (dropped {len(dropped)} rate-limit empties: {[p1[d]['task'] for d in dropped]})")

    def records_of(run, cid):
        r = run.get(cid, {})
        return r.get("observations") or r.get("records") or []

    summary = {}
    for label, run in (("p4-deterministic", p4), ("p2-injected", p2), ("p1-tool", p1)):
        scored = [score_case(cases[cid], records_of(run, cid)) for cid in clean_ids if cid in cases]
        summary[label] = aggregate(scored)

    # P1 tool-call rate on clean cases (the assumption test)
    p1_clean = [p1[cid] for cid in clean_ids]
    tc_calls = sum(r.get("n_tool_calls", 0) for r in p1_clean)
    cases_with_call = sum(1 for r in p1_clean if r.get("n_tool_calls", 0) > 0)
    summary["p1-tool"]["tool_calls_total"] = tc_calls
    summary["p1-tool"]["cases_with_tool_call"] = cases_with_call
    summary["p1-tool"]["tool_call_case_rate"] = round(cases_with_call / len(p1_clean), 3)

    print("\n=== matched-subset comparison (n=%d) ===" % len(clean_ids))
    for label, s in summary.items():
        print(f"\n[{label}]")
        for k in ("n_cases", "mean_caller_capture", "mean_edge_capture",
                  "mean_symbol_capture", "mean_n_records"):
            if k in s:
                print(f"  {k}: {s[k]}")
        if label == "p1-tool":
            print(f"  tool_calls_total: {s.get('tool_calls_total')}")
            print(f"  cases_with_tool_call: {s.get('cases_with_tool_call')} / {len(p1_clean)}")
            print(f"  tool_call_case_rate: {s.get('tool_call_case_rate')}")

    out = RUNSDIR / "comparison.json"
    out.write_text(json.dumps({
        "matched_subset_size": len(clean_ids),
        "dropped_rate_limit_empties": [p1[d]["task"] for d in dropped],
        "per_prototype": summary,
    }, indent=2))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
