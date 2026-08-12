from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from scripts.recover_quarantined_cells import (
    RecoveryOperation,
    VerifierRecomputationEvidence,
    apply_file_recovery_operation,
    build_recomputed_result,
    file_identity,
)


def write_cell(path: Path, *, reward: int = 1) -> None:
    path.mkdir(parents=True)
    (path / "artifacts").mkdir()
    (path / "artifacts" / "model.patch").write_text("patch")
    (path / "result.json").write_text(
        json.dumps(
            {
                "reward_binary": reward,
                "reward_partial": float(reward),
                "verifier_exit": 127,
                "verifier_resource_exhausted": True,
                "verifier_resource_diagnostic": "old failure",
                "verifier_resource_evidence_unavailable": True,
            },
            sort_keys=True,
        )
    )


def test_restore_copies_exact_quarantine_cell_and_records_recovery(
    tmp_path: Path,
) -> None:
    source = tmp_path / "quarantine" / "rep0"
    destination = tmp_path / "results" / "rep0"
    manifest = tmp_path / "manifest.jsonl"
    write_cell(source)
    identity = file_identity(source / "result.json")
    operation = RecoveryOperation(
        action="restore",
        source=source,
        destination=destination,
        expected_result_identity=identity,
        reason="valid subject resource evidence",
    )

    apply_file_recovery_operation(operation, manifest)

    assert source.is_dir()
    assert (destination / "result.json").read_bytes() == (
        source / "result.json"
    ).read_bytes()
    record = json.loads(manifest.read_text())
    assert record["action"] == "restore"
    assert record["source_result_identity"] == identity
    assert record["published_result_identity"] == identity


def test_quarantine_for_rerun_moves_cell_without_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "results" / "rep0"
    destination = tmp_path / "quarantine" / "rep0"
    manifest = tmp_path / "manifest.jsonl"
    write_cell(source)
    identity = file_identity(source / "result.json")
    operation = RecoveryOperation(
        action="quarantine-for-rerun",
        source=source,
        destination=destination,
        expected_result_identity=identity,
        reason="paired resource-policy replacement",
    )

    apply_file_recovery_operation(operation, manifest)

    assert not source.exists()
    assert (destination / "result.json").is_file()
    record = json.loads(manifest.read_text())
    assert record["action"] == "quarantine-for-rerun"
    assert record["published_result_identity"] == identity


def test_recovery_rejects_changed_source_or_occupied_destination(
    tmp_path: Path,
) -> None:
    source = tmp_path / "quarantine" / "rep0"
    destination = tmp_path / "results" / "rep0"
    manifest = tmp_path / "manifest.jsonl"
    write_cell(source)
    operation = RecoveryOperation(
        action="restore",
        source=source,
        destination=destination,
        expected_result_identity="sha256:wrong",
        reason="test",
    )
    with pytest.raises(ValueError, match="source result identity mismatch"):
        apply_file_recovery_operation(operation, manifest)

    operation = RecoveryOperation(
        action="restore",
        source=source,
        destination=destination,
        expected_result_identity=file_identity(source / "result.json"),
        reason="test",
    )
    destination.mkdir(parents=True)
    with pytest.raises(FileExistsError, match="destination already exists"):
        apply_file_recovery_operation(operation, manifest)


def test_build_recomputed_result_replaces_only_grade_and_verifier_evidence() -> None:
    original = {
        "task": "igel-persist-feature-schema",
        "total_tokens": 123,
        "reward_binary": -1,
        "reward_partial": 0.0,
        "verifier_exit": 127,
        "verifier_resource_exhausted": True,
        "verifier_resource_diagnostic": "old failure",
        "verifier_resource_evidence_unavailable": True,
    }
    reward = {
        "reward": 1,
        "partial": 1.0,
        "f2p": 1.0,
        "p2p": 1.0,
        "f2p_passed": 24,
        "f2p_total": 24,
        "p2p_passed": 2,
        "p2p_total": 2,
    }
    memory_status = {
        "verifier_memory_events": {"oom_kill": 0},
    }

    recomputed = build_recomputed_result(
        original,
        reward,
        VerifierRecomputationEvidence(
            verifier_exit=0,
            memory_status=memory_status,
            source_result_identity="sha256:source",
            harness_commit="abc123",
            reason="preserve verifier PATH",
            verifier_memory_gib=4,
        ),
    )

    assert recomputed["total_tokens"] == 123
    assert recomputed["reward_binary"] == 1
    assert recomputed["f2p_passed"] == 24
    assert recomputed["verifier_exit"] == 0
    assert recomputed["verifier_memory_events"] == {"oom_kill": 0}
    assert "verifier_resource_exhausted" not in recomputed
    assert "verifier_resource_diagnostic" not in recomputed
    assert "verifier_resource_evidence_unavailable" not in recomputed
    recomputation = cast(dict[str, object], recomputed["verifier_recomputation"])
    assert recomputation["source_result_identity"] == "sha256:source"
    assert recomputation["verifier_memory_gib"] == 4
