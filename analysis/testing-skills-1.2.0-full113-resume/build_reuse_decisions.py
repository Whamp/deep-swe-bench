#!/usr/bin/env python3
"""Pin completed testing-skills full-113 cells for the timeout-fix resume."""

from __future__ import annotations

import json
from pathlib import Path

from harness.result_provenance import (
    read_result_record,
    recorded_result_provenance,
    result_file_identity,
)

REPO = Path(__file__).resolve().parents[2]
RESULTS = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
SUBSET = REPO / "subsets/113_v0.txt"
OUTPUT = Path(__file__).with_name("reuse-decisions.json")
CONFIGS = ("testing-skills@1.1.0", "testing-skills@1.2.0")
EXPECTED_COMPLETED_CELLS = 670
RATIONALE = (
    "Preserve this completed full-113 cell across the verifier-timeout infrastructure "
    "fix. The fix only recovers live cgroup counters after a verifier timeout; this "
    "cell already produced its canonical outcome and recorded resource evidence. Exact "
    "result bytes and recorded provenance are pinned here."
)


def build_reuse_decisions() -> list[dict[str, object]]:
    """Return exact reuse decisions for every completed canonical matrix cell."""
    tasks = [line for line in SUBSET.read_text().splitlines() if line]
    decisions: list[dict[str, object]] = []
    for task in tasks:
        for rep in range(3):
            for config in CONFIGS:
                result_path = RESULTS / config / task / f"rep{rep}" / "result.json"
                if not result_path.is_file():
                    continue
                record = read_result_record(result_path)
                if record.get("config") != config:
                    raise ValueError(
                        "Resume reuse result config mismatch: "
                        f"path={result_path}; recorded={record.get('config')!r}"
                    )
                if record.get("task") != task or record.get("rep") != rep:
                    raise ValueError(
                        "Resume reuse result address mismatch: "
                        f"path={result_path}; task={record.get('task')!r}; "
                        f"rep={record.get('rep')!r}"
                    )
                decisions.append(
                    {
                        "priorConfigIdentity": config,
                        "rationale": RATIONALE,
                        "recordedProvenance": recorded_result_provenance(record),
                        "resultIdentity": result_file_identity(result_path),
                        "resultPath": str(result_path.resolve()),
                    }
                )
    if len(decisions) != EXPECTED_COMPLETED_CELLS:
        raise ValueError(
            "Resume reuse decision count mismatch: "
            f"expected={EXPECTED_COMPLETED_CELLS}; observed={len(decisions)}"
        )
    return decisions


def main() -> None:
    """Write the deterministic exact-result reuse ledger."""
    OUTPUT.write_text(json.dumps(build_reuse_decisions(), indent=2) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
