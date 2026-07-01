"""Score a prototype's run output with impact_capture_rate.

Usage:
  python3 -m analysis.om-impact.score_run \
      --cases analysis/om-impact/cases/impact_subset.jsonl \
      --run   analysis/om-impact/runs/p4-smoke.jsonl \
      --label p4-deterministic
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR
from .metrics.impact_capture import score_case, aggregate


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default=str(CASESDIR / "impact_subset.jsonl"))
    ap.add_argument("--run", required=True)
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    cases = {json.loads(l)["case_id"]: json.loads(l)
             for l in Path(a.cases).read_text().splitlines() if l.strip()}
    run_rows = [json.loads(l) for l in Path(a.run).read_text().splitlines() if l.strip()]
    scored = []
    for r in run_rows:
        c = cases.get(r.get("case_id"))
        if not c:
            continue
        records = r.get("records") or r.get("observations") or []
        s = score_case(c, records)
        s["label"] = a.label
        scored.append(s)
    agg = aggregate(scored)
    print(f"=== {a.label} (n={agg['n_cases']}) ===")
    print(json.dumps(agg, indent=2))
    print("--- per-case ---")
    for s in scored:
        print(f"  {s['task']}: caller_cap={s['caller_capture']} "
              f"edge_cap={s['edge_capture']} n_records={s['n_records']} "
              f"captured={s['captured_callers']}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"label": a.label, "aggregate": agg,
                                           "per_case": scored}, indent=2))


if __name__ == "__main__":
    main()
