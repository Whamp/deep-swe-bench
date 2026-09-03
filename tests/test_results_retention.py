import hashlib
import json
from pathlib import Path

from harness.results_retention import (
    collapse_quarantine_category,
    migrate_results_tree,
)
from harness.verifier_evidence import with_compact_verifier_evidence


def write_migration_cell(cell: Path) -> None:
    (cell / "verifier").mkdir(parents=True)
    (cell / "logs").mkdir()
    (cell / "artifacts").mkdir()
    (cell / "artifacts" / "model.patch").write_text("diff --git a/a b/a\n")
    (cell / "result.json").write_text(
        json.dumps(
            {
                "task": "task-a",
                "reward_binary": 1,
                "reward_partial": 1,
                "f2p": 1,
                "f2p_passed": 1,
                "f2p_total": 1,
                "p2p": 1,
                "p2p_passed": 2,
                "p2p_total": 2,
                "verifier_exit": 0,
            },
            indent=2,
        )
    )
    (cell / "verifier" / "reward.json").write_text(
        json.dumps(
            {
                "reward": 1,
                "partial": 1,
                "f2p": 1,
                "f2p_passed": 1,
                "f2p_total": 1,
                "p2p": 1,
                "p2p_passed": 2,
                "p2p_total": 2,
            }
        )
    )
    (cell / "verifier" / "ctrf.json").write_text(
        json.dumps(
            {
                "results": {
                    "tool": {"name": "go test"},
                    "summary": {"tests": 3, "passed": 3, "failed": 0},
                    "tests": [
                        {"name": "base", "status": "passed"},
                        {"name": "patch-a", "status": "passed"},
                        {"name": "patch-b", "status": "passed"},
                    ],
                }
            }
        )
    )
    (cell / "logs" / "verifier.stdout.txt").write_text("all tests passed\n")


def test_results_migration_dry_run_then_apply(tmp_path: Path) -> None:
    cell = tmp_path / "model" / "low" / "config" / "task-a" / "rep0"
    write_migration_cell(cell)
    original_result = (cell / "result.json").read_bytes()

    dry_run = migrate_results_tree(tmp_path, apply=False)

    assert dry_run.examined == 1
    assert dry_run.planned == 1
    assert dry_run.compacted == 0
    assert dry_run.issues == ()
    assert dry_run.raw_bytes > 0
    assert (cell / "result.json").read_bytes() == original_result
    assert (cell / "verifier" / "ctrf.json").is_file()

    applied = migrate_results_tree(tmp_path, apply=True)

    assert applied.examined == 1
    assert applied.planned == 1
    assert applied.compacted == 1
    assert applied.issues == ()
    assert json.loads((cell / "result.json").read_text())["result_schema_version"] == 2
    assert not (cell / "verifier").exists()
    assert not (cell / "logs" / "verifier.stdout.txt").exists()
    assert (cell / "artifacts" / "model.patch").read_text() == "diff --git a/a b/a\n"


def test_quarantine_category_collapses_to_validated_ledger(tmp_path: Path) -> None:
    category = "om-no-executor-projection"
    category_root = tmp_path / "_contaminated" / category
    cell = category_root / "model" / "low" / "config" / "task-a" / "rep0"
    write_migration_cell(cell)
    session_path = cell / "session" / "session.jsonl"
    session_path.parent.mkdir()
    session_path.write_text('{"event":"done"}\n')
    analysis_note = category_root / "ANALYSIS.md"
    analysis_note.write_text("This treatment never projected memory.\n")
    manifest_path = tmp_path / "_contaminated" / "manifest.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "category": category,
                "original_path": "results/model/low/config",
                "quarantine_path": f"results/_contaminated/{category}/model/low/config",
                "reason": "executor did not receive memory",
                "timestamp": "2026-07-02T16:33:15+00:00",
            }
        )
        + "\n"
    )
    assert migrate_results_tree(tmp_path, apply=True).compacted == 1
    patch_bytes = (cell / "artifacts" / "model.patch").read_bytes()
    session_bytes = session_path.read_bytes()
    analysis_bytes = analysis_note.read_bytes()

    dry_run = collapse_quarantine_category(
        tmp_path,
        category=category,
        apply=False,
        archive_uri="endurance:/archive/results.tar.zst",
    )

    assert dry_run.result_count == 1
    assert dry_run.artifact_count == 1
    assert dry_run.applied is False
    assert category_root.is_dir()
    assert not (tmp_path / "_contaminated" / f"{category}.jsonl").exists()

    applied = collapse_quarantine_category(
        tmp_path,
        category=category,
        apply=True,
        archive_uri="endurance:/archive/results.tar.zst",
    )

    ledger_path = tmp_path / "_contaminated" / f"{category}.jsonl"
    records = [json.loads(line) for line in ledger_path.read_text().splitlines()]
    assert applied.result_count == 1
    assert applied.artifact_count == 1
    assert applied.applied is True
    assert not category_root.exists()
    assert len(records) == 2
    result_record = next(
        record for record in records if record["record_type"] == "result_cell"
    )
    artifact_record = next(
        record for record in records if record["record_type"] == "category_artifact"
    )
    assert result_record["cell_path"] == "model/low/config/task-a/rep0"
    assert result_record["result"]["result_schema_version"] == 2
    assert result_record["quarantine"]["reason"] == "executor did not receive memory"
    assert result_record["model_patch"] == {
        "bytes": len(patch_bytes),
        "sha256": hashlib.sha256(patch_bytes).hexdigest(),
    }
    assert result_record["session"] == {
        "bytes": len(session_bytes),
        "file_count": 1,
        "sha256": hashlib.sha256(
            b"session/session.jsonl\0" + session_bytes
        ).hexdigest(),
    }
    assert artifact_record["path"] == "ANALYSIS.md"
    assert artifact_record["bytes"] == len(analysis_bytes)
    assert artifact_record["sha256"] == hashlib.sha256(analysis_bytes).hexdigest()
    assert artifact_record["text_excerpt"] == {
        "original_bytes": len(analysis_bytes),
        "truncated": False,
        "text": "This treatment never projected memory.\n",
    }
    manifest = json.loads(manifest_path.read_text())
    assert manifest["retention"] == "compact-ledger"
    assert manifest["compact_ledger"] == (f"results/_contaminated/{category}.jsonl")
    assert manifest["raw_archive"] == "endurance:/archive/results.tar.zst"
    ledger_bytes = ledger_path.read_bytes()

    repeated = collapse_quarantine_category(
        tmp_path,
        category=category,
        apply=True,
        archive_uri="endurance:/archive/results.tar.zst",
    )

    assert repeated.result_count == 1
    assert repeated.artifact_count == 1
    assert repeated.applied is True
    assert ledger_path.read_bytes() == ledger_bytes


def test_results_migration_finishes_interrupted_raw_prune(tmp_path: Path) -> None:
    cell = tmp_path / "model" / "low" / "config" / "task-a" / "rep0"
    write_migration_cell(cell)
    result_path = cell / "result.json"
    compacted = with_compact_verifier_evidence(
        cell,
        json.loads(result_path.read_text()),
    )
    result_path.write_text(json.dumps(compacted, indent=2) + "\n")
    compact_result_bytes = result_path.read_bytes()

    dry_run = migrate_results_tree(tmp_path, apply=False)

    assert dry_run.already_compact == 1
    assert dry_run.planned == 1
    assert (cell / "verifier").is_dir()

    applied = migrate_results_tree(tmp_path, apply=True)

    assert applied.compacted == 1
    assert result_path.read_bytes() == compact_result_bytes
    assert not (cell / "verifier").exists()
