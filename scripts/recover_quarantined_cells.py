#!/usr/bin/env python3
"""Restore, regrade, or preserve quarantined benchmark cells without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from harness.container_resources import (
    container_resource_docker_args,
    inspect_docker_container_oom,
    verifier_container_memory_status,
    verifier_memory_events_shell_args,
)
from harness.lib import read_reward
from harness.verifier_evidence import (
    raw_verifier_retention_requested,
    write_compact_verifier_result,
)

RecoveryAction = Literal["restore", "quarantine-for-rerun", "recompute-verifier"]
_VERIFIER_EVIDENCE_FIELDS = {
    "verifier_memory_events",
    "verifier_resource_diagnostic",
    "verifier_resource_evidence_unavailable",
    "verifier_resource_exhausted",
}
_GRADE_FIELDS = {
    "f2p",
    "f2p_passed",
    "f2p_total",
    "p2p",
    "p2p_passed",
    "p2p_total",
    "reward_binary",
    "reward_partial",
    "reward_unverified",
}


@dataclass(frozen=True, slots=True)
class RecoveryOperation:
    """Describe one exact quarantined-cell recovery or preservation action."""

    action: RecoveryAction
    source: Path
    destination: Path
    expected_result_identity: str
    reason: str
    verifier_memory_gib: float | None = None
    source_record_name: str = "result.json"
    allow_verifier_memory_override: bool = False
    source_archive: Path | None = None


@dataclass(frozen=True, slots=True)
class VerifierRecomputationEvidence:
    """Record how one saved patch received a replacement verifier grade."""

    verifier_exit: int
    memory_status: Mapping[str, object]
    source_result_identity: str
    source_record_name: str
    harness_commit: str
    reason: str
    original_verifier_memory_gib: float
    verifier_memory_gib: float


def file_identity(path: Path) -> str:
    """Return the SHA-256 identity of one exact artifact file."""
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def append_recovery_manifest(manifest: Path, record: Mapping[str, object]) -> None:
    """Append one auditable recovery record to the quarantine manifest."""
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(dict(record), sort_keys=True) + "\n")


def recovery_source_record_path(operation: RecoveryOperation) -> Path:
    """Return the exact canonical result or failed-verifier candidate to recover."""
    source_record = Path(operation.source_record_name)
    if (
        source_record.name != operation.source_record_name
        or source_record.is_absolute()
    ):
        raise ValueError(
            "recovery source record must be one filename: "
            f"{operation.source_record_name!r}"
        )
    return operation.source / source_record


def validate_recovery_operation(operation: RecoveryOperation) -> None:
    """Reject source drift and occupied destinations before changing a cell."""
    result_path = recovery_source_record_path(operation)
    if not result_path.is_file():
        raise FileNotFoundError(f"recovery source result is missing: {result_path}")
    observed_identity = file_identity(result_path)
    if observed_identity != operation.expected_result_identity:
        raise ValueError(
            "recovery source result identity mismatch: "
            f"expected={operation.expected_result_identity}; observed={observed_identity}"
        )
    in_place_recomputation = (
        operation.action == "recompute-verifier"
        and operation.destination == operation.source
    )
    if operation.destination.exists() and not in_place_recomputation:
        raise FileExistsError(
            f"recovery destination already exists: {operation.destination}"
        )
    if in_place_recomputation:
        if operation.source_archive is None:
            raise ValueError("in-place verifier recomputation requires sourceArchive")
        if operation.source_archive.exists():
            raise FileExistsError(
                f"recovery source archive already exists: {operation.source_archive}"
            )
        resolved_source = operation.source.resolve()
        resolved_archive = operation.source_archive.resolve()
        if (
            resolved_archive == resolved_source
            or resolved_source in resolved_archive.parents
        ):
            raise ValueError("recovery source archive must be outside the source cell")
    if not operation.reason.strip():
        raise ValueError("recovery reason must not be empty")


def _recovery_record(
    operation: RecoveryOperation,
    *,
    published_result_identity: str,
) -> dict[str, object]:
    record: dict[str, object] = {
        "action": operation.action,
        "category": "recovery",
        "destination_path": str(operation.destination),
        "published_result_identity": published_result_identity,
        "reason": operation.reason,
        "source_path": str(operation.source),
        "source_result_identity": operation.expected_result_identity,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if operation.verifier_memory_gib is not None:
        record["verifier_memory_gib"] = operation.verifier_memory_gib
    if operation.source_record_name != "result.json":
        record["source_record_name"] = operation.source_record_name
    if operation.source_archive is not None:
        record["source_archive_path"] = str(operation.source_archive)
    return record


def apply_file_recovery_operation(
    operation: RecoveryOperation,
    manifest: Path,
) -> None:
    """Atomically copy a restored cell or move a cell preserved for rerun."""
    validate_recovery_operation(operation)
    operation.destination.parent.mkdir(parents=True, exist_ok=True)
    if operation.action == "restore":
        staging = operation.destination.with_name(
            f".{operation.destination.name}.restore-{uuid.uuid4().hex}"
        )
        try:
            shutil.copytree(operation.source, staging)
            os.replace(staging, operation.destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    elif operation.action == "quarantine-for-rerun":
        operation.source.rename(operation.destination)
    else:
        raise ValueError(f"file recovery action unsupported: {operation.action}")
    published_identity = file_identity(operation.destination / "result.json")
    append_recovery_manifest(
        manifest,
        _recovery_record(
            operation,
            published_result_identity=published_identity,
        ),
    )


def build_recomputed_result(
    original: Mapping[str, object],
    reward: Mapping[str, object],
    evidence: VerifierRecomputationEvidence,
) -> dict[str, object]:
    """Replace only verifier grade fields and record verifier-only provenance."""
    result = dict(original)
    for field in _VERIFIER_EVIDENCE_FIELDS | _GRADE_FIELDS:
        result.pop(field, None)
    result.update(
        {
            "reward_binary": reward["reward"],
            "reward_partial": float(cast(int | float, reward["partial"])),
            "reward_unverified": bool(reward.get("unverified", False)),
            "verifier_exit": evidence.verifier_exit,
        }
    )
    for field in _GRADE_FIELDS - {"reward_binary", "reward_partial"}:
        if field in reward:
            result[field] = reward[field]
    result.update(evidence.memory_status)
    resource_policy = result.get("resource_policy")
    if isinstance(resource_policy, Mapping):
        result["resource_policy"] = {
            **resource_policy,
            "verifier_memory_gib": evidence.verifier_memory_gib,
        }
    result["verifier_recomputation"] = {
        "harness_commit": evidence.harness_commit,
        "original_verifier_memory_gib": evidence.original_verifier_memory_gib,
        "reason": evidence.reason,
        "source_record_name": evidence.source_record_name,
        "source_result_identity": evidence.source_result_identity,
        "timestamp": datetime.now(UTC).isoformat(),
        "verifier_memory_gib": evidence.verifier_memory_gib,
    }
    return result


def run_recovery_verifier_container(
    staging: Path,
    verifier_image: str,
    verifier_memory_gib: float,
) -> tuple[int, dict[str, object]]:
    """Run one network-isolated verifier and return exit and memory evidence."""
    verifier_dir = staging / "verifier"
    logs_dir = staging / "logs"
    container_name = f"dswb-verifier-recompute-{uuid.uuid4().hex[:12]}"
    command = [
        "docker",
        "run",
        "--name",
        container_name,
        *container_resource_docker_args(
            memory_gib=verifier_memory_gib,
            additional_swap_gib=0,
            labels={},
        ),
        "--network",
        "none",
        "--platform",
        "linux/amd64",
        "-v",
        f"{staging}:/logs",
        verifier_image,
        *verifier_memory_events_shell_args(),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        (logs_dir / "verifier.stdout.txt").write_text(
            completed.stdout + completed.stderr
        )
        memory_status = verifier_container_memory_status(
            verifier_dir / "memory-events.txt",
            oom_evidence=inspect_docker_container_oom(container_name),
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            check=False,
        )
    return completed.returncode, memory_status


def load_verifier_recovery_source(
    staging: Path,
    operation: RecoveryOperation,
) -> tuple[dict[str, object], str, float]:
    """Load exact verifier image and memory provenance from one saved subject."""
    source_record_path = staging / operation.source_record_name
    original = cast(dict[str, object], json.loads(source_record_path.read_text()))
    images = original.get("immutable_image_identities")
    if not isinstance(images, dict) or not isinstance(images.get("verifier"), str):
        raise TypeError(
            "verifier recomputation requires immutable verifier image identity"
        )
    resource_policy = original.get("resource_policy")
    if not isinstance(resource_policy, dict):
        raise TypeError("verifier recomputation requires recorded resource policy")
    recorded_memory_gib = resource_policy.get("verifier_memory_gib")
    if not isinstance(recorded_memory_gib, int | float):
        raise TypeError(
            "verifier recomputation requires numeric recorded verifier memory"
        )
    if (
        recorded_memory_gib != operation.verifier_memory_gib
        and not operation.allow_verifier_memory_override
    ):
        raise ValueError(
            "verifier recomputation memory override requires explicit approval: "
            f"recorded={recorded_memory_gib}; "
            f"requested={operation.verifier_memory_gib}"
        )
    return original, images["verifier"], float(recorded_memory_gib)


def publish_recomputed_verifier_cell(
    staging: Path,
    operation: RecoveryOperation,
) -> None:
    """Atomically publish a verifier-only result and preserve an in-place source."""
    if operation.source != operation.destination:
        os.replace(staging, operation.destination)
        return
    assert operation.source_archive is not None
    operation.source_archive.parent.mkdir(parents=True, exist_ok=True)
    os.replace(operation.source, operation.source_archive)
    try:
        os.replace(staging, operation.destination)
    except OSError:
        os.replace(operation.source_archive, operation.source)
        raise


def recompute_quarantined_verifier(
    operation: RecoveryOperation,
    manifest: Path,
    *,
    harness_commit: str,
) -> None:
    """Regrade a saved patch in its immutable verifier image and publish it."""
    validate_recovery_operation(operation)
    if operation.action != "recompute-verifier":
        raise ValueError(f"verifier recomputation action invalid: {operation.action}")
    if operation.verifier_memory_gib is None:
        raise ValueError("verifier recomputation requires verifier_memory_gib")
    staging = operation.destination.with_name(
        f".{operation.destination.name}.recompute-{uuid.uuid4().hex}"
    )
    operation.destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(operation.source, staging)
    verifier_dir = staging / "verifier"
    shutil.rmtree(verifier_dir, ignore_errors=True)
    verifier_dir.mkdir()
    (staging / "logs").mkdir(exist_ok=True)
    original, verifier_image, recorded_memory_gib = load_verifier_recovery_source(
        staging, operation
    )
    verifier_exit, memory_status = run_recovery_verifier_container(
        staging,
        verifier_image,
        operation.verifier_memory_gib,
    )
    if verifier_exit != 0:
        raise RuntimeError(
            "verifier recomputation failed: "
            f"cell={operation.source}; exit={verifier_exit}"
        )
    if (
        memory_status.get("verifier_resource_exhausted") is True
        or memory_status.get("verifier_resource_evidence_unavailable") is True
    ):
        raise RuntimeError(
            f"verifier recomputation resource evidence invalid: {memory_status!r}"
        )
    reward = read_reward(verifier_dir)
    recomputed = build_recomputed_result(
        original,
        reward,
        VerifierRecomputationEvidence(
            verifier_exit=verifier_exit,
            memory_status=memory_status,
            source_result_identity=operation.expected_result_identity,
            source_record_name=operation.source_record_name,
            harness_commit=harness_commit,
            reason=operation.reason,
            original_verifier_memory_gib=recorded_memory_gib,
            verifier_memory_gib=operation.verifier_memory_gib,
        ),
    )
    recomputed.pop("result_schema_version", None)
    recomputed.pop("verifier_summary", None)
    write_compact_verifier_result(
        staging,
        recomputed,
        retain_raw_verifier_evidence=raw_verifier_retention_requested(),
    )
    if operation.source_record_name != "result.json":
        (staging / operation.source_record_name).unlink()
    publish_recomputed_verifier_cell(staging, operation)
    append_recovery_manifest(
        manifest,
        _recovery_record(
            operation,
            published_result_identity=file_identity(
                operation.destination / "result.json"
            ),
        ),
    )


def load_recovery_operations(spec_path: Path) -> list[RecoveryOperation]:
    """Load exact recovery operations from a reviewed JSON specification."""
    document: Any = json.loads(spec_path.read_text())
    if not isinstance(document, dict) or document.get("schemaVersion") != 1:
        raise ValueError("recovery specification requires schemaVersion 1")
    raw_operations = document.get("operations")
    if not isinstance(raw_operations, list):
        raise TypeError("recovery specification operations must be a list")
    operations = []
    for raw in raw_operations:
        if not isinstance(raw, dict):
            raise TypeError("recovery operation must be an object")
        operations.append(
            RecoveryOperation(
                action=raw["action"],
                source=Path(raw["source"]),
                destination=Path(raw["destination"]),
                expected_result_identity=raw["expectedResultIdentity"],
                reason=raw["reason"],
                verifier_memory_gib=raw.get("verifierMemoryGiB"),
                source_record_name=raw.get("sourceRecordName", "result.json"),
                allow_verifier_memory_override=raw.get(
                    "allowVerifierMemoryOverride", False
                ),
                source_archive=(
                    Path(raw["sourceArchive"])
                    if raw.get("sourceArchive") is not None
                    else None
                ),
            )
        )
    return operations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    operations = load_recovery_operations(args.spec)
    for operation in operations:
        validate_recovery_operation(operation)
    if not args.apply:
        print(f"validated {len(operations)} recovery operations; no changes made")
        return
    harness_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    for operation in operations:
        if operation.action == "recompute-verifier":
            recompute_quarantined_verifier(
                operation,
                args.manifest,
                harness_commit=harness_commit,
            )
        else:
            apply_file_recovery_operation(operation, args.manifest)
        print(f"{operation.action}: {operation.destination}")


if __name__ == "__main__":
    main()
