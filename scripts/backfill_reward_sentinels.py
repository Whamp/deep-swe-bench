"""Backfill retired -1 reward sentinels to honest zeros.

Historical cells whose verifier never produced reward.json recorded
``reward_binary: -1``. Naive score averaging over raw result records treats
that sentinel as worse than failure, artificially lowering config scores.
The harness now records ``reward_binary: 0`` plus ``reward_unverified: true``
for unverified cells; this one-time migration rewrites the historical cells
(and their ``results.jsonl`` mirror lines) to the same shape, touching
nothing else.

Scope: live results under ``results/<leaf>/<thinking>/...`` only. The
``results/_contaminated/``, ``results/_archives/``, and ``results/_runs/``
trees are diagnostic or state evidence and are left byte-identical.

Usage:

    python scripts/backfill_reward_sentinels.py            # dry-run summary
    python scripts/backfill_reward_sentinels.py --apply    # rewrite + manifest
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

# Underscore-prefixed results subtrees that are not live efficacy data.
_EXCLUDED_RESULTS_SUBTREES = frozenset({"_contaminated", "_archives", "_runs"})


@dataclass(frozen=True, slots=True)
class BackfillEdit:
    """One planned rewrite: a result.json or one results.jsonl line."""

    path: Path
    kind: str  # "result" | "results_jsonl"
    line_number: int | None = None


def _is_live_result_path(path: Path, results_root: Path) -> bool:
    try:
        relative = path.relative_to(results_root)
    except ValueError:
        return False
    return not any(part in _EXCLUDED_RESULTS_SUBTREES for part in relative.parts[:-1])


def _rewrite_grade(record: dict) -> dict:
    """Zero the sentinel and insert reward_unverified beside reward_binary."""
    rebuilt: dict = {}
    for key, value in record.items():
        rebuilt[key] = 0 if key == "reward_binary" else value
        if key == "reward_binary":
            rebuilt["reward_unverified"] = True
    return rebuilt


def plan_backfill(results_root: Path) -> list[BackfillEdit]:
    """Find every live -1 sentinel cell and its results.jsonl mirror lines."""
    edits: list[BackfillEdit] = []
    for result_path in sorted(results_root.rglob("rep*/result.json")):
        if not _is_live_result_path(result_path, results_root):
            continue
        try:
            record = json.loads(result_path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            print(f"[skip] unreadable result: {result_path}: {error}", file=sys.stderr)
            continue
        if isinstance(record, dict) and record.get("reward_binary") == -1:
            edits.append(BackfillEdit(path=result_path, kind="result"))
    for jsonl_path in sorted(results_root.rglob("results.jsonl")):
        if not _is_live_result_path(jsonl_path, results_root):
            continue
        try:
            lines = jsonl_path.read_text().splitlines()
        except OSError as error:
            print(f"[skip] unreadable jsonl: {jsonl_path}: {error}", file=sys.stderr)
            continue
        for number, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("reward_binary") == -1:
                edits.append(
                    BackfillEdit(
                        path=jsonl_path,
                        kind="results_jsonl",
                        line_number=number,
                    )
                )
    return edits


def _apply_result_edit(edit: BackfillEdit) -> None:
    record = json.loads(edit.path.read_text())
    if record.get("reward_binary") != -1:
        return  # drifted since planning; leave for a later idempotent pass
    edit.path.write_text(json.dumps(_rewrite_grade(record), indent=2))


def _apply_jsonl_edits(path: Path, line_numbers: set[int]) -> int:
    lines = path.read_text().splitlines()
    changed = 0
    for number in sorted(line_numbers):
        if number > len(lines):
            continue
        record = json.loads(lines[number - 1])
        if record.get("reward_binary") != -1:
            continue
        lines[number - 1] = json.dumps(_rewrite_grade(record))
        changed += 1
    if changed:
        path.write_text("\n".join(lines) + "\n")
    return changed


def apply_backfill(
    edits: list[BackfillEdit],
    *,
    manifest_path: Path,
) -> dict[str, int]:
    """Rewrite planned edits atomically per file and record a manifest."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    result_files = 0
    jsonl_lines = 0
    jsonl_targets: dict[Path, set[int]] = {}
    timestamp = datetime.now(UTC).isoformat()
    with open(manifest_path, "a") as manifest:
        for edit in edits:
            if edit.kind == "result":
                _apply_result_edit(edit)
                result_files += 1
                manifest.write(
                    json.dumps(
                        {
                            "kind": "result",
                            "path": str(edit.path),
                            "previous_reward_binary": -1,
                            "ts": timestamp,
                        }
                    )
                    + "\n"
                )
            else:
                assert edit.line_number is not None  # results_jsonl edits carry one
                jsonl_targets.setdefault(edit.path, set()).add(edit.line_number)
        for path, numbers in sorted(jsonl_targets.items()):
            changed = _apply_jsonl_edits(path, numbers)
            jsonl_lines += changed
            manifest.writelines(
                json.dumps(
                    {
                        "kind": "results_jsonl",
                        "path": str(path),
                        "line": number,
                        "previous_reward_binary": -1,
                        "ts": timestamp,
                    }
                )
                + "\n"
                for number in sorted(numbers)
            )
    return {"result_files": result_files, "jsonl_lines": jsonl_lines}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "results",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="rewrite files (default: dry-run, writes nothing)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "analysis"
        / "reward-sentinel-backfill"
        / "manifest.jsonl",
    )
    args = parser.parse_args()
    edits = plan_backfill(args.results_root)
    result_count = sum(1 for e in edits if e.kind == "result")
    jsonl_count = sum(1 for e in edits if e.kind == "results_jsonl")
    print(
        f"planned edits: {result_count} result.json files, "
        f"{jsonl_count} results.jsonl lines"
    )
    if not args.apply:
        print("dry-run: no files written (pass --apply to rewrite)")
        return
    summary = apply_backfill(edits, manifest_path=args.manifest)
    print(
        f"applied: {summary['result_files']} result.json files, "
        f"{summary['jsonl_lines']} results.jsonl lines"
    )
    print(f"manifest: {args.manifest}")


if __name__ == "__main__":
    main()
