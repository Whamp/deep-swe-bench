"""Backfill of historical -1 reward sentinels to honest zeros.

Live result cells recorded reward_binary: -1 when the verifier never
produced reward.json. The backfill rewrites those cells (and their
results.jsonl mirror lines) to reward_binary: 0 with reward_unverified:
true, touching nothing else.
"""

import json
from pathlib import Path

from scripts.backfill_reward_sentinels import apply_backfill, plan_backfill


def _write(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record, indent=2))


def _tree(tmp_path: Path) -> Path:
    root = tmp_path / "results"
    _write(
        root / "m1" / "high" / "cfg-a" / "t1" / "rep0" / "result.json",
        {
            "task": "t1",
            "config": "cfg-a",
            "model": "m1",
            "rep": 0,
            "reward_binary": -1,
            "reward_partial": 0.0,
            "verifier_exit": "skipped_empty_patch",
        },
    )
    _write(
        root / "m1" / "high" / "cfg-a" / "t1" / "rep1" / "result.json",
        {
            "task": "t1",
            "config": "cfg-a",
            "model": "m1",
            "rep": 1,
            "reward_binary": 0,
            "reward_partial": 0.5,
            "verifier_exit": 0,
        },
    )
    _write(
        root / "m1" / "high" / "cfg-a" / "t2" / "rep0" / "result.json",
        {
            "task": "t2",
            "config": "cfg-a",
            "model": "m1",
            "rep": 0,
            "reward_binary": 1,
            "reward_partial": 1.0,
            "verifier_exit": 0,
        },
    )
    _write(
        root / "m2" / "low" / "cfg-b" / "t1" / "rep0" / "result.json",
        {
            "task": "t1",
            "config": "cfg-b",
            "model": "m2",
            "rep": 0,
            "reward_binary": -1,
            "reward_partial": 0.0,
            "verifier_exit": "timeout",
        },
    )
    _write(
        root / "_contaminated" / "harness-failure" / "t9" / "rep0" / "result.json",
        {
            "task": "t9",
            "config": "broken",
            "model": "m1",
            "rep": 0,
            "reward_binary": -1,
            "reward_partial": 0.0,
        },
    )
    jsonl = root / "m1" / "high" / "results.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)
    jsonl.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "task": "t1",
                        "config": "cfg-a",
                        "model": "m1",
                        "rep": 0,
                        "reward_binary": -1,
                        "reward_partial": 0.0,
                    }
                ),
                json.dumps(
                    {
                        "task": "t2",
                        "config": "cfg-a",
                        "model": "m1",
                        "rep": 0,
                        "reward_binary": 1,
                        "reward_partial": 1.0,
                    }
                ),
            ]
        )
        + "\n"
    )
    return root


def test_plan_backfill_finds_only_live_sentinel_cells(tmp_path: Path) -> None:
    edits = plan_backfill(_tree(tmp_path))

    result_paths = {e.path for e in edits if e.kind == "result"}
    jsonl_edits = [e for e in edits if e.kind == "results_jsonl"]
    assert len(result_paths) == 2
    assert not any("_contaminated" in str(p) for p in result_paths)
    assert len(jsonl_edits) == 1
    assert jsonl_edits[0].line_number == 1


def test_dry_run_plan_changes_nothing(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    before = {
        p: p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    }

    plan_backfill(root)  # planning alone never writes

    after = {
        p: p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    }
    assert before == after


def test_apply_backfill_rewrites_sentinels_and_preserves_neighbors(
    tmp_path: Path,
) -> None:
    root = _tree(tmp_path)
    untouched = root / "m1" / "high" / "cfg-a" / "t1" / "rep1" / "result.json"
    untouched_bytes = untouched.read_bytes()
    manifest = tmp_path / "manifest.jsonl"

    edits = plan_backfill(root)
    summary = apply_backfill(edits, manifest_path=manifest)

    assert summary["result_files"] == 2
    assert summary["jsonl_lines"] == 1
    fixed = json.loads(
        (root / "m1" / "high" / "cfg-a" / "t1" / "rep0" / "result.json").read_text()
    )
    assert fixed["reward_binary"] == 0
    assert fixed["reward_unverified"] is True
    assert fixed["verifier_exit"] == "skipped_empty_patch"
    assert untouched.read_bytes() == untouched_bytes
    quarantined = json.loads(
        (
            root / "_contaminated" / "harness-failure" / "t9" / "rep0" / "result.json"
        ).read_text()
    )
    assert quarantined["reward_binary"] == -1
    lines = [
        json.loads(line)
        for line in (root / "m1" / "high" / "results.jsonl").read_text().splitlines()
    ]
    assert lines[0]["reward_binary"] == 0
    assert lines[0]["reward_unverified"] is True
    assert lines[1]["reward_binary"] == 1
    assert "reward_unverified" not in lines[1]
    assert manifest.is_file()
    assert len(manifest.read_text().splitlines()) == 3


def test_apply_backfill_is_idempotent(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    apply_backfill(plan_backfill(root), manifest_path=tmp_path / "m.jsonl")

    assert plan_backfill(root) == []


def test_apply_backfill_preserves_field_order(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    target = root / "m2" / "low" / "cfg-b" / "t1" / "rep0" / "result.json"

    apply_backfill(plan_backfill(root), manifest_path=tmp_path / "m.jsonl")

    keys = list(json.loads(target.read_text()))
    assert keys.index("reward_unverified") == keys.index("reward_binary") + 1
