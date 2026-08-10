#!/usr/bin/env python3
"""Recover omitted feedback annotations with explicit one-case Luna calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from build_feedback_uptake_calibration_v2 import canonical_feedback_v2_json_bytes
from feedback_uptake_calibration_v2 import validate_feedback_v2_heldout_annotations
from run_feedback_uptake_calibration_v2 import parse_feedback_v2_json_output
from run_feedback_uptake_population_v2 import (
    CALIBRATION_V2_REPAIR_ROOT,
    feedback_v2_population_command,
)


def recover_feedback_v2_missing_batch_annotations(
    *, calibration_root: Path, batch_id: str, rejected_path: Path
) -> dict[str, Any]:
    """Classify only omitted IDs, then compose and validate the original batch."""
    batch_root = calibration_root / "population/batches" / batch_id
    batch_manifest = json.loads((batch_root / "manifest.json").read_text())
    batch_schema = json.loads((batch_root / "annotation-schema.json").read_text())
    batch_units = {
        unit["candidate_unit_id"]: unit
        for unit in (
            json.loads(line)
            for line in (batch_root / "units.jsonl").read_bytes().splitlines()
        )
    }
    rejected = json.loads(rejected_path.read_text())
    rejected_annotations = rejected.get("annotations", [])
    rejected_ids = [
        annotation["candidate_unit_id"] for annotation in rejected_annotations
    ]
    expected_ids = batch_manifest["candidate_unit_ids"]
    if len(rejected_ids) != len(set(rejected_ids)) or not set(rejected_ids) < set(
        expected_ids
    ):
        raise ValueError(
            "Feedback population v2 recovery: rejected output is not a strict unique subset"
        )
    missing_ids = [
        candidate_id
        for candidate_id in expected_ids
        if candidate_id not in rejected_ids
    ]
    if not missing_ids:
        raise ValueError(
            "Feedback population v2 recovery: rejected output has no omissions"
        )

    recovered_annotations = []
    recovery_receipts = []
    for recovery_number, candidate_id in enumerate(missing_ids, 1):
        recovery_id = f"recovery-{recovery_number:03d}"
        recovery_root = batch_root / recovery_id
        recovery_root.mkdir(parents=True, exist_ok=True)
        unit_bytes = canonical_feedback_v2_json_bytes(batch_units[candidate_id]) + b"\n"
        sample_sha256 = hashlib.sha256(unit_bytes).hexdigest()
        recovery_manifest = {
            "population_batch_manifest_schema_version": 2,
            "batch_id": f"{batch_id}/{recovery_id}",
            "candidate_set_sha256": batch_manifest["candidate_set_sha256"],
            "dataset_sha256": sample_sha256,
            "candidate_unit_count": 1,
            "candidate_unit_ids": [candidate_id],
        }
        recovery_schema = json.loads(json.dumps(batch_schema))
        recovery_schema["properties"]["annotations"]["minItems"] = 1
        recovery_schema["properties"]["annotations"]["maxItems"] = 1
        (recovery_root / "units.jsonl").write_bytes(unit_bytes)
        (recovery_root / "manifest.json").write_text(
            json.dumps(recovery_manifest, ensure_ascii=False, indent=2) + "\n"
        )
        (recovery_root / "annotation-schema.json").write_text(
            json.dumps(recovery_schema, ensure_ascii=False, indent=2) + "\n"
        )
        annotator_id = (
            "openai-codex/gpt-5.6-luna:xhigh:feedback-v2-production:"
            f"{batch_id}:{recovery_id}"
        )
        relative_root = recovery_root.relative_to(calibration_root)
        completed = subprocess.run(
            feedback_v2_population_command(
                model="openai-codex/gpt-5.6-luna",
                level="xhigh",
                annotator_id=annotator_id,
                batch_relative_root=relative_root,
                batch_sample_sha256=sample_sha256,
            ),
            cwd=calibration_root,
            text=True,
            capture_output=True,
            check=False,
        )
        (recovery_root / "annotations.raw.txt").write_text(completed.stdout)
        if completed.stderr:
            (recovery_root / "annotations.stderr.txt").write_text(completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(
                f"Feedback population v2 recovery: {batch_id}/{recovery_id} exited {completed.returncode}"
            )
        recovery_document = parse_feedback_v2_json_output(completed.stdout)
        validate_feedback_v2_heldout_annotations(
            recovery_document,
            schema=recovery_schema,
            heldout_manifest=recovery_manifest,
        )
        (recovery_root / "annotations.json").write_text(
            json.dumps(recovery_document, ensure_ascii=False, indent=2) + "\n"
        )
        recovered_annotations.extend(recovery_document["annotations"])
        recovery_receipts.append(
            {
                "recovery_id": recovery_id,
                "candidate_unit_id": candidate_id,
                "sample_sha256": sample_sha256,
                "annotator_id": recovery_document["annotator_id"],
            }
        )

    annotations_by_id = {
        annotation["candidate_unit_id"]: annotation
        for annotation in [*rejected_annotations, *recovered_annotations]
    }
    composed = dict(rejected)
    composed["annotator_id"] = (
        f"{rejected['annotator_id']}+explicit-missing-unit-recovery"
    )
    composed["annotations"] = [
        annotations_by_id[candidate_id] for candidate_id in expected_ids
    ]
    validate_feedback_v2_heldout_annotations(
        composed, schema=batch_schema, heldout_manifest=batch_manifest
    )
    (batch_root / "annotations.json").write_text(
        json.dumps(composed, ensure_ascii=False, indent=2) + "\n"
    )
    receipt = {
        "recovery_schema_version": 2,
        "batch_id": batch_id,
        "rejected_output": rejected_path.name,
        "preserved_annotation_count": len(rejected_annotations),
        "recovered_annotation_count": len(recovered_annotations),
        "recovery_calls": recovery_receipts,
        "semantic_labels_modified": False,
    }
    (batch_root / "recovery-composition.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    )
    return receipt


def main() -> None:
    """Recover one explicitly named rejected production batch."""
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_id")
    parser.add_argument("rejected_path", type=Path)
    parser.add_argument(
        "--calibration-root", type=Path, default=CALIBRATION_V2_REPAIR_ROOT
    )
    arguments = parser.parse_args()
    print(
        json.dumps(
            recover_feedback_v2_missing_batch_annotations(
                calibration_root=arguments.calibration_root.resolve(),
                batch_id=arguments.batch_id,
                rejected_path=arguments.rejected_path.resolve(),
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
