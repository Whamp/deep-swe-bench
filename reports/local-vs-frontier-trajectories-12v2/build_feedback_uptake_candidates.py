#!/usr/bin/env python3
"""Freeze the bounded feedback candidate population as content-addressed JSONL."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from build_analysis import REPORT_ROOT
from build_feedback_uptake_events import (
    FEEDBACK_UPTAKE_EVENT_ROOT,
    load_feedback_uptake_event_files,
)
from feedback_uptake_candidates import (
    CANDIDATE_UNIT_SCHEMA_VERSION,
    MAX_CANDIDATE_WINDOW_BYTES,
    MAX_CONTEXT_ASSISTANT_RESPONSES,
    build_feedback_candidate_units,
    validate_feedback_candidate_units,
)
from feedback_uptake_event_validation import validate_feedback_uptake_packets

FEEDBACK_CANDIDATE_ROOT = REPORT_ROOT / "feedback-uptake/candidates"
CANDIDATE_MANIFEST_SCHEMA_VERSION = 1


def serialize_feedback_candidate_units(units: list[dict[str, Any]]) -> bytes:
    """Serialize fixed candidate units as canonical newline-delimited JSON bytes."""
    return b"".join(
        (json.dumps(unit, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        for unit in units
    )


def feedback_candidate_manifest(
    units: list[dict[str, Any]], *, jsonl_bytes: bytes, packet_count: int
) -> dict[str, Any]:
    """Describe the exact immutable candidate bytes and their complete unit IDs."""
    model_counts = collections.Counter(unit["model_key"] for unit in units)
    source_kind_counts = collections.Counter(
        unit["source_event_kind"] for unit in units
    )
    return {
        "manifest_schema_version": CANDIDATE_MANIFEST_SCHEMA_VERSION,
        "candidate_unit_schema_version": CANDIDATE_UNIT_SCHEMA_VERSION,
        "source_packet_schema_version": 3,
        "source_packet_count": packet_count,
        "candidate_unit_count": len(units),
        "candidate_set_sha256": hashlib.sha256(jsonl_bytes).hexdigest(),
        "candidate_set_bytes": len(jsonl_bytes),
        "maximum_candidate_window_bytes": MAX_CANDIDATE_WINDOW_BYTES,
        "following_assistant_response_limit": MAX_CONTEXT_ASSISTANT_RESPONSES,
        "model_counts": dict(sorted(model_counts.items())),
        "source_event_kind_counts": dict(sorted(source_kind_counts.items())),
        "candidate_unit_ids": [unit["candidate_unit_id"] for unit in units],
    }


def write_feedback_candidate_dataset(
    units: list[dict[str, Any]],
    *,
    packets: list[dict[str, Any]],
    dataset_root: Path = FEEDBACK_CANDIDATE_ROOT,
) -> dict[str, Any]:
    """Validate and atomically replace one fixed candidate JSONL dataset."""
    validate_feedback_candidate_units(units, packets=packets)
    jsonl_bytes = serialize_feedback_candidate_units(units)
    manifest = feedback_candidate_manifest(
        units, jsonl_bytes=jsonl_bytes, packet_count=len(packets)
    )
    dataset_root.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = dataset_root.parent / (
        f".{dataset_root.name}.tmp-{uuid.uuid4().hex}"
    )
    backup_root = dataset_root.parent / (
        f".{dataset_root.name}.backup-{uuid.uuid4().hex}"
    )
    temporary_root.mkdir(parents=True)
    try:
        (temporary_root / "units.jsonl").write_bytes(jsonl_bytes)
        (temporary_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        loaded_manifest, loaded_units = load_feedback_candidate_dataset(
            temporary_root, packets=packets
        )
        if loaded_manifest != manifest or loaded_units != units:
            raise ValueError(
                "Feedback uptake candidates: atomic write verification mismatch"
            )
        if dataset_root.exists():
            dataset_root.rename(backup_root)
        try:
            temporary_root.rename(dataset_root)
        except Exception:
            if backup_root.exists():
                backup_root.rename(dataset_root)
            raise
        if backup_root.exists():
            shutil.rmtree(backup_root)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return manifest


def load_feedback_candidate_dataset(
    dataset_root: Path, *, packets: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and fail closed on any manifest, hash, schema, or source mismatch."""
    manifest_path = dataset_root / "manifest.json"
    units_path = dataset_root / "units.jsonl"
    manifest = json.loads(manifest_path.read_text())
    if not isinstance(manifest, dict):
        raise TypeError("Feedback uptake candidates: manifest is not an object")
    jsonl_bytes = units_path.read_bytes()
    actual_sha256 = hashlib.sha256(jsonl_bytes).hexdigest()
    if manifest.get("candidate_set_sha256") != actual_sha256:
        raise ValueError("Feedback uptake candidates: candidate set SHA-256 mismatch")
    if manifest.get("candidate_set_bytes") != len(jsonl_bytes):
        raise ValueError(
            "Feedback uptake candidates: candidate set byte count mismatch"
        )
    units = []
    for line_number, raw_line in enumerate(jsonl_bytes.splitlines(), start=1):
        try:
            unit = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Feedback uptake candidates: invalid unit JSON at line {line_number}"
            ) from error
        if not isinstance(unit, dict):
            raise TypeError(
                f"Feedback uptake candidates: unit at line {line_number} is not an object"
            )
        units.append(unit)
    validate_feedback_candidate_units(units, packets=packets)
    expected_manifest = feedback_candidate_manifest(
        units, jsonl_bytes=jsonl_bytes, packet_count=len(packets)
    )
    if manifest != expected_manifest:
        raise ValueError(
            "Feedback uptake candidates: manifest differs from candidate population"
        )
    return manifest, units


def build_feedback_candidate_dataset(
    *,
    event_root: Path = FEEDBACK_UPTAKE_EVENT_ROOT,
    dataset_root: Path = FEEDBACK_CANDIDATE_ROOT,
) -> dict[str, Any]:
    """Build the canonical fixed candidate set from all 108 validated packets."""
    packets = load_feedback_uptake_event_files(event_root)
    expected_tasks = sorted({packet["task"] for packet in packets})
    validate_feedback_uptake_packets(packets, expected_tasks=expected_tasks)
    units = build_feedback_candidate_units(packets)
    return write_feedback_candidate_dataset(
        units, packets=packets, dataset_root=dataset_root
    )


def parse_feedback_candidate_arguments() -> argparse.Namespace:
    """Parse packet and fixed-candidate output roots."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-root", type=Path, default=FEEDBACK_UPTAKE_EVENT_ROOT)
    parser.add_argument("--dataset-root", type=Path, default=FEEDBACK_CANDIDATE_ROOT)
    return parser.parse_args()


def main() -> None:
    """Build and print the fixed candidate set identity."""
    arguments = parse_feedback_candidate_arguments()
    manifest = build_feedback_candidate_dataset(
        event_root=arguments.event_root,
        dataset_root=arguments.dataset_root,
    )
    print(
        "Wrote "
        f"{manifest['candidate_unit_count']} bounded feedback candidates "
        f"sha256:{manifest['candidate_set_sha256']}"
    )


if __name__ == "__main__":
    main()
