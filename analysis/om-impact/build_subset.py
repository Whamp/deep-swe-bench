"""Build a focused case subset for the om-impact prototypes.

Selection rule: keep observer replay cases whose task has a non-empty gold
edge subgraph (so impact_capture_rate is scoreable) AND whose repo+graph can
be prepared. Caps per task to avoid one verbose task dominating. Output goes to
analysis/om-impact/cases/ — does NOT touch the om-gepa cases or any results.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .impact_common import CASESDIR, case_task_id, gold_edges


def select(in_path: Path, out_path: Path, per_task: int, max_cases: int,
           require_task: str | None) -> int:
    rows = [json.loads(l) for l in in_path.read_text().splitlines() if l.strip()]
    by_task: dict[str, list[dict]] = defaultdict(list)
    for c in rows:
        tid = case_task_id(c)
        if not tid:
            continue
        if require_task and tid != require_task:
            continue
        if not gold_edges(tid):
            continue  # no gold edges -> not scoreable
        by_task[tid].append(c)
    chosen: list[dict] = []
    for tid, cases in sorted(by_task.items()):
        chosen.extend(cases[:per_task])
    chosen = chosen[:max_cases]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        for c in chosen:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    tasks = sorted({case_task_id(c) for c in chosen})
    print(f"selected {len(chosen)} cases across {len(tasks)} tasks -> {out_path}")
    print(f"tasks: {', '.join(tasks)}")
    return len(chosen)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="src", default="analysis/om-gepa/cases/observer_all.jsonl")
    ap.add_argument("--out", default=str(CASESDIR / "impact_subset.jsonl"))
    ap.add_argument("--per-task", type=int, default=2)
    ap.add_argument("--max", type=int, default=24)
    ap.add_argument("--task", default=None, help="restrict to one task id")
    a = ap.parse_args()
    src = Path(a.src)
    if not src.is_absolute():
        src = Path(__file__).resolve().parents[2] / a.src
    out = Path(a.out)
    if not out.is_absolute():
        out = CASESDIR / a.out
    select(src, out, a.per_task, a.max, a.task)


if __name__ == "__main__":
    main()
