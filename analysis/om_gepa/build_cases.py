from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any

from . import ARTIFACT_ROOT, REPO_ROOT
from .common import (
    fold_memory,
    index_by_entry_id,
    observation_line,
    read_jsonl,
    reflection_line,
    serialize_source_entries,
    stable_split,
    write_jsonl,
)


def latest_observation_coverage_idx(entries: list[dict[str, Any]], before_idx: int, indexes: dict[str, int]) -> int:
    idx = -1
    for i, entry in enumerate(entries[:before_idx]):
        if entry.get("type") != "custom" or entry.get("customType") != "om.observations.recorded":
            continue
        data = entry.get("data") if isinstance(entry.get("data"), dict) else {}
        covers = data.get("coversUpToId")
        if isinstance(covers, str) and covers in indexes:
            idx = max(idx, indexes[covers])
    return idx


def observer_cases_from_session(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    entries = read_jsonl(path)
    indexes = index_by_entry_id(entries)
    cases: list[dict[str, Any]] = []
    for i, entry in enumerate(entries):
        if entry.get("type") != "custom" or entry.get("customType") != "om.observations.recorded":
            continue
        data = entry.get("data") if isinstance(entry.get("data"), dict) else {}
        gold = data.get("observations") if isinstance(data.get("observations"), list) else []
        covers = data.get("coversUpToId")
        if not gold or not isinstance(covers, str) or covers not in indexes:
            continue
        start_idx = latest_observation_coverage_idx(entries, i, indexes)
        end_idx = indexes[covers]
        chunk_entries = entries[start_idx + 1 : end_idx + 1]
        chunk, source_ids = serialize_source_entries(chunk_entries)
        if not chunk or not source_ids:
            continue
        prior_observations, prior_reflections = fold_memory(entries, i - 1)
        case_id = f"observer:{path.parent.parent.name}:{path.parent.name}:{entry.get('id', i)}"
        cases.append(
            {
                "case_id": case_id,
                "role": "observer",
                "session_path": str(path.relative_to(REPO_ROOT)),
                "split": stable_split(case_id),
                "priorReflections": [reflection_line(r) for r in prior_reflections],
                "priorObservations": [observation_line(o) for o in prior_observations],
                "chunk": chunk,
                "allowedSourceEntryIds": source_ids,
                "goldObservations": gold,
                "coversUpToId": covers,
            }
        )
        if limit and len(cases) >= limit:
            break
    return cases


def reflector_cases_from_session(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    entries = read_jsonl(path)
    cases: list[dict[str, Any]] = []
    for i, entry in enumerate(entries):
        if entry.get("type") != "custom" or entry.get("customType") != "om.reflections.recorded":
            continue
        data = entry.get("data") if isinstance(entry.get("data"), dict) else {}
        gold = data.get("reflections") if isinstance(data.get("reflections"), list) else []
        covers = data.get("coversUpToId")
        if not gold or not isinstance(covers, str):
            continue
        observations, reflections = fold_memory(entries, i - 1)
        if not observations:
            continue
        case_id = f"reflector:{path.parent.parent.name}:{path.parent.name}:{entry.get('id', i)}"
        cases.append(
            {
                "case_id": case_id,
                "role": "reflector",
                "session_path": str(path.relative_to(REPO_ROOT)),
                "split": stable_split(case_id),
                "observations": observations,
                "reflections": reflections,
                "goldReflections": gold,
                "coversUpToId": covers,
            }
        )
        if limit and len(cases) >= limit:
            break
    return cases


def build_cases(role: str, roots: list[str], out_dir: Path, limit: int | None = None) -> dict[str, int]:
    session_paths: list[Path] = []
    for root in roots:
        root_path = REPO_ROOT / root if not Path(root).is_absolute() else Path(root)
        if root_path.is_file():
            session_paths.append(root_path)
        else:
            session_paths.extend(Path(p) for p in glob.glob(str(root_path / "**" / "session" / "*.jsonl"), recursive=True))
    session_paths = sorted(set(session_paths))
    all_cases: list[dict[str, Any]] = []
    remaining = limit
    for path in session_paths:
        per_session = observer_cases_from_session(path, remaining) if role == "observer" else reflector_cases_from_session(path, remaining)
        all_cases.extend(per_session)
        if remaining is not None:
            remaining = max(0, remaining - len(per_session))
            if remaining == 0:
                break
    counts: dict[str, int] = {"all": write_jsonl(out_dir / f"{role}_all.jsonl", all_cases)}
    for split in ["train", "val", "test"]:
        counts[split] = write_jsonl(out_dir / f"{role}_{split}.jsonl", [c for c in all_cases if c.get("split") == split])
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build observer/reflector replay cases from results/**/session/*.jsonl. Dropper is intentionally excluded.")
    parser.add_argument("--role", choices=["observer", "reflector"], required=True)
    parser.add_argument("--from", dest="roots", action="append", default=[], help="Results/session root or a single session JSONL. May be repeated.")
    parser.add_argument("--out", type=Path, default=ARTIFACT_ROOT / "cases")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    roots = args.roots or ["results"]
    counts = build_cases(args.role, roots, args.out, args.limit)
    print({"role": args.role, "out": str(args.out), "counts": counts})


if __name__ == "__main__":
    main()
