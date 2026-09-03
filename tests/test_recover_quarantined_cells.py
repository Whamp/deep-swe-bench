from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from scripts.recover_quarantined_cells import (
    RecoveryOperation,
    VerifierRecomputationEvidence,
    apply_file_recovery_operation,
    build_recomputed_result,
    file_identity,
    load_recovery_operations,
    recompute_quarantined_verifier,
    validate_recovery_operation,
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


def write_verifier_recovery_candidate(path: Path) -> Path:
    """Write one failed-verifier cell with complete subject provenance."""
    path.mkdir(parents=True)
    (path / "artifacts").mkdir()
    (path / "artifacts" / "model.patch").write_text("fixture patch\n")
    (path / "logs").mkdir()
    candidate_path = path / "verifier-recovery-candidate.json"
    candidate_path.write_text(
        json.dumps(
            {
                "agent_exit": 0,
                "config": "baseline@1.0.0",
                "immutable_image_identities": {
                    "agent": "sha256:agent",
                    "environment": "sha256:environment",
                    "verifier": "sha256:verifier",
                },
                "launch_plan_identity": "sha256:subject-plan",
                "model": "provider/model",
                "patch_bytes": 14,
                "resource_policy": {
                    "additional_swap_gib": 0.0,
                    "host_reserve_gib": 12.0,
                    "subject_memory_gib": 4.0,
                    "verifier_memory_gib": 4.0,
                },
                "reward_binary": 0,
                "reward_partial": 0.0,
                "task": "task-a",
                "total_tokens": 123,
                "verifier_exit": "memory_limit",
                "verifier_memory_events": {"oom_kill": 1},
                "verifier_resource_exhausted": True,
            },
            sort_keys=True,
        )
    )
    return candidate_path


def test_load_verifier_recovery_candidate_operation(tmp_path: Path) -> None:
    """Recovery specs expose candidate, archive, and memory-review fields."""
    spec = tmp_path / "recovery.json"
    spec.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "operations": [
                    {
                        "action": "recompute-verifier",
                        "source": "/results/task-a/rep0",
                        "destination": "/results/task-a/rep0",
                        "expectedResultIdentity": "sha256:candidate",
                        "reason": "verifier memory exhaustion",
                        "verifierMemoryGiB": 8,
                        "sourceRecordName": "verifier-recovery-candidate.json",
                        "allowVerifierMemoryOverride": True,
                        "sourceArchive": "/results/_failed/task-a/rep0",
                    }
                ],
            }
        )
    )

    operation = load_recovery_operations(spec)[0]

    assert operation.source_record_name == "verifier-recovery-candidate.json"
    assert operation.allow_verifier_memory_override is True
    assert operation.source_archive == Path("/results/_failed/task-a/rep0")
    assert operation.verifier_memory_gib == 8


def test_in_place_recovery_rejects_archive_inside_source(tmp_path: Path) -> None:
    """An in-place archive cannot disappear when the source directory moves."""
    source = tmp_path / "results" / "task-a" / "rep0"
    candidate_path = write_verifier_recovery_candidate(source)
    operation = RecoveryOperation(
        action="recompute-verifier",
        source=source,
        destination=source,
        expected_result_identity=file_identity(candidate_path),
        reason="test invalid archive placement",
        verifier_memory_gib=8.0,
        source_record_name="verifier-recovery-candidate.json",
        allow_verifier_memory_override=True,
        source_archive=source / "failed-attempt",
    )

    with pytest.raises(
        ValueError,
        match="recovery source archive must be outside the source cell",
    ):
        validate_recovery_operation(operation)


def test_recompute_failed_verifier_candidate_with_memory_override(
    tmp_path: Path,
) -> None:
    """Verifier-only recovery archives the failed attempt and publishes a grade."""
    cell = tmp_path / "results" / "task-a" / "rep0"
    archive = tmp_path / "failed-verifiers" / "task-a" / "rep0"
    manifest = tmp_path / "verifier-recoveries.ndjson"
    candidate_path = write_verifier_recovery_candidate(cell)
    operation = RecoveryOperation(
        action="recompute-verifier",
        source=cell,
        destination=cell,
        expected_result_identity=file_identity(candidate_path),
        reason="rerun verifier after 4 GiB memory exhaustion",
        verifier_memory_gib=8.0,
        source_record_name="verifier-recovery-candidate.json",
        allow_verifier_memory_override=True,
        source_archive=archive,
    )
    reward = {
        "reward": 1,
        "partial": 1.0,
        "f2p": 1.0,
        "p2p": 1.0,
        "f2p_passed": 2,
        "f2p_total": 2,
        "p2p_passed": 3,
        "p2p_total": 3,
    }

    with (
        patch(
            "scripts.recover_quarantined_cells.run_recovery_verifier_container",
            return_value=(
                0,
                {
                    "verifier_memory_events": {"oom_kill": 0},
                    "verifier_resource_exhausted": False,
                },
            ),
        ) as verifier,
        patch(
            "scripts.recover_quarantined_cells.read_reward",
            return_value=reward,
        ),
    ):
        recompute_quarantined_verifier(
            operation,
            manifest,
            harness_commit="recovery-commit",
        )

    verifier.assert_called_once()
    assert archive.joinpath("verifier-recovery-candidate.json").is_file()
    assert not cell.joinpath("verifier-recovery-candidate.json").exists()
    result = json.loads(cell.joinpath("result.json").read_text())
    assert result["result_schema_version"] == 2
    assert result["verifier_summary"]["source_report"] is None
    assert not cell.joinpath("verifier").exists()
    assert result["total_tokens"] == 123
    assert result["reward_binary"] == 1
    assert result["resource_policy"]["subject_memory_gib"] == 4.0
    assert result["resource_policy"]["verifier_memory_gib"] == 8.0
    recomputation = cast(dict[str, object], result["verifier_recomputation"])
    assert recomputation["original_verifier_memory_gib"] == 4.0
    assert recomputation["verifier_memory_gib"] == 8.0
    assert recomputation["source_record_name"] == "verifier-recovery-candidate.json"
    recovery_record = json.loads(manifest.read_text())
    assert recovery_record["source_archive_path"] == str(archive)
    assert recovery_record["verifier_memory_gib"] == 8.0


def test_recompute_rejects_unreviewed_verifier_memory_override(
    tmp_path: Path,
) -> None:
    """A higher verifier limit requires an explicit reviewed override."""
    source = tmp_path / "source" / "rep0"
    destination = tmp_path / "destination" / "rep0"
    candidate_path = write_verifier_recovery_candidate(source)
    operation = RecoveryOperation(
        action="recompute-verifier",
        source=source,
        destination=destination,
        expected_result_identity=file_identity(candidate_path),
        reason="test unreviewed memory change",
        verifier_memory_gib=8.0,
        source_record_name="verifier-recovery-candidate.json",
    )

    with pytest.raises(
        ValueError,
        match="verifier recomputation memory override requires explicit approval",
    ):
        recompute_quarantined_verifier(
            operation,
            tmp_path / "manifest.ndjson",
            harness_commit="recovery-commit",
        )

    assert not destination.exists()


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
            source_record_name="result.json",
            harness_commit="abc123",
            reason="preserve verifier PATH",
            original_verifier_memory_gib=4,
            verifier_memory_gib=4,
        ),
    )

    assert recomputed["total_tokens"] == 123
    assert recomputed["reward_binary"] == 1
    assert recomputed["reward_unverified"] is False
    assert recomputed["f2p_passed"] == 24
    assert recomputed["verifier_exit"] == 0
    assert recomputed["verifier_memory_events"] == {"oom_kill": 0}
    assert "verifier_resource_exhausted" not in recomputed
    assert "verifier_resource_diagnostic" not in recomputed
    assert "verifier_resource_evidence_unavailable" not in recomputed
    recomputation = cast(dict[str, object], recomputed["verifier_recomputation"])
    assert recomputation["source_result_identity"] == "sha256:source"
    assert recomputation["verifier_memory_gib"] == 4
