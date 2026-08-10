#!/usr/bin/env python3
"""Annotate unseen feedback candidates with the authorized Luna v2 protocol."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from build_feedback_uptake_calibration_v2 import canonical_feedback_v2_json_bytes
from feedback_uptake_calibration_v2 import (
    FeedbackCalibrationV2ValidationError,
    require_feedback_v2_production_model,
    validate_feedback_v2_heldout_annotations,
    validate_feedback_v2_population_authorization,
)
from run_feedback_uptake_calibration_v2 import (
    PI_REAL_EXECUTABLE,
    feedback_v2_file_sha256,
    parse_feedback_v2_json_output,
)

REPORT_ROOT = Path(__file__).resolve().parent
FEEDBACK_ROOT = REPORT_ROOT / "feedback-uptake"
CALIBRATION_V1_ROOT = FEEDBACK_ROOT / "calibration"
CALIBRATION_V2_ROOT = FEEDBACK_ROOT / "calibration-v2"
CALIBRATION_V2_REPAIR_ROOT = FEEDBACK_ROOT / "calibration-v2-repair"
CANDIDATE_UNITS_PATH = FEEDBACK_ROOT / "candidates/units.jsonl"
CANDIDATE_MANIFEST_PATH = FEEDBACK_ROOT / "candidates/manifest.json"
PRODUCTION_BATCH_COUNT = 50
PRODUCTION_CONCURRENCY = 4


def partition_feedback_v2_population_units(
    units: list[dict[str, Any]], *, batch_count: int
) -> list[list[dict[str, Any]]]:
    """Partition ordered candidate units into balanced, nonempty fixed batches."""
    if batch_count <= 0 or batch_count > len(units):
        raise ValueError(
            "Feedback population v2: batch count must be positive and no larger than unit count"
        )
    base_size, larger_batch_count = divmod(len(units), batch_count)
    batches = []
    offset = 0
    for batch_index in range(batch_count):
        batch_size = base_size + (1 if batch_index < larger_batch_count else 0)
        batches.append(units[offset : offset + batch_size])
        offset += batch_size
    if offset != len(units) or any(not batch for batch in batches):
        raise AssertionError("Feedback population v2: partition lost or emptied units")
    return batches


def feedback_v2_population_command(
    *,
    model: str,
    level: str,
    annotator_id: str,
    batch_relative_root: Path,
    batch_sample_sha256: str,
) -> list[str]:
    """Build one authorized production batch command without calibration answers."""
    require_feedback_v2_production_model(model)
    if (model, level) != ("openai-codex/gpt-5.6-luna", "xhigh"):
        raise ValueError(
            "Feedback population v2: authorized production protocol is Luna xhigh"
        )
    batch_root = batch_relative_root.as_posix()
    final_request = (
        "Classify this production batch now. Return JSON only. "
        f"Set annotator_id to {json.dumps(annotator_id)}. "
        "Set candidate_set_sha256 to "
        "e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d "
        f"and heldout_sample_sha256 to {batch_sample_sha256}."
    )
    return [
        str(PI_REAL_EXECUTABLE),
        "--model",
        model,
        "--thinking",
        level,
        "--mode",
        "text",
        "--print",
        "--no-session",
        "--no-tools",
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-context-files",
        "--system-prompt",
        "You classify bounded feedback evidence under supplied rules and worked examples. Return JSON only.",
        "@calibration-instructions.md",
        f"@{batch_root}/annotation-schema.json",
        "@development/manifest.json",
        "@development/units.jsonl",
        "@development/annotations.json",
        f"@{batch_root}/manifest.json",
        f"@{batch_root}/units.jsonl",
        final_request,
    ]


def feedback_v2_calibration_exclusions() -> dict[str, list[str]]:
    """Return all candidate IDs exposed during any calibration round."""
    return {
        "v1_calibration": json.loads(
            (CALIBRATION_V1_ROOT / "sample-selection.json").read_text()
        )["candidate_unit_ids"],
        "initial_v2_heldout": json.loads(
            (CALIBRATION_V2_ROOT / "heldout/selection.json").read_text()
        )["candidate_unit_ids"],
        "repair_v2_heldout": json.loads(
            (CALIBRATION_V2_REPAIR_ROOT / "heldout/selection.json").read_text()
        )["candidate_unit_ids"],
    }


def materialize_feedback_v2_population_batches(
    *, production_units: list[dict[str, Any]], calibration_root: Path
) -> list[dict[str, Any]]:
    """Write deterministic batch inputs and return their manifests in order."""
    schema = json.loads((calibration_root / "annotation-schema.json").read_text())
    candidate_manifest = json.loads(CANDIDATE_MANIFEST_PATH.read_text())
    batches = partition_feedback_v2_population_units(
        production_units, batch_count=PRODUCTION_BATCH_COUNT
    )
    manifests = []
    for batch_number, batch_units in enumerate(batches, 1):
        batch_id = f"batch-{batch_number:03d}"
        batch_root = calibration_root / "population/batches" / batch_id
        batch_root.mkdir(parents=True, exist_ok=True)
        unit_bytes = b"".join(
            canonical_feedback_v2_json_bytes(unit) + b"\n" for unit in batch_units
        )
        batch_sha256 = hashlib.sha256(unit_bytes).hexdigest()
        batch_schema = json.loads(json.dumps(schema))
        batch_schema["properties"]["annotations"]["minItems"] = len(batch_units)
        batch_schema["properties"]["annotations"]["maxItems"] = len(batch_units)
        manifest = {
            "population_batch_manifest_schema_version": 2,
            "batch_id": batch_id,
            "candidate_set_sha256": candidate_manifest["candidate_set_sha256"],
            "dataset_sha256": batch_sha256,
            "candidate_unit_count": len(batch_units),
            "candidate_unit_ids": [unit["candidate_unit_id"] for unit in batch_units],
        }
        (batch_root / "units.jsonl").write_bytes(unit_bytes)
        (batch_root / "annotation-schema.json").write_text(
            json.dumps(batch_schema, ensure_ascii=False, indent=2) + "\n"
        )
        (batch_root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        manifests.append(manifest)
    return manifests


def repair_feedback_v2_batch_annotation_order(
    document: dict[str, Any], *, batch_manifest: dict[str, Any]
) -> dict[str, Any]:
    """Restore fixed annotation order only when IDs form an exact unique permutation."""
    annotations = document.get("annotations")
    if not isinstance(annotations, list) or any(
        not isinstance(annotation, dict) for annotation in annotations
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback population v2: batch annotations are not an object list"
        )
    expected_ids = batch_manifest["candidate_unit_ids"]
    actual_ids = [annotation.get("candidate_unit_id") for annotation in annotations]
    if actual_ids == expected_ids:
        return document
    if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_ids):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback population v2: batch annotation IDs are not an exact permutation"
        )
    annotations_by_id = {
        annotation["candidate_unit_id"]: annotation for annotation in annotations
    }
    repaired = dict(document)
    repaired["annotations"] = [
        annotations_by_id[candidate_id] for candidate_id in expected_ids
    ]
    return repaired


def repair_feedback_v2_batch_identity(
    document: dict[str, Any], *, batch_manifest: dict[str, Any]
) -> dict[str, Any]:
    """Repair only a one-character truncated batch hash with exact candidate IDs."""
    expected_hash = batch_manifest["dataset_sha256"]
    actual_hash = document.get("heldout_sample_sha256")
    if actual_hash == expected_hash:
        return document
    actual_ids = [
        annotation.get("candidate_unit_id")
        for annotation in document.get("annotations", [])
        if isinstance(annotation, dict)
    ]
    if (
        actual_ids == batch_manifest["candidate_unit_ids"]
        and isinstance(actual_hash, str)
        and len(actual_hash) == 63
        and expected_hash.startswith(actual_hash)
    ):
        repaired = dict(document)
        repaired["heldout_sample_sha256"] = expected_hash
        return repaired
    raise FeedbackCalibrationV2ValidationError(
        "Feedback population v2: batch identity mismatch is not safely repairable"
    )


def run_feedback_v2_population_batch(
    *,
    batch_manifest: dict[str, Any],
    calibration_root: Path,
    model: str,
    level: str,
    force: bool,
) -> dict[str, Any]:
    """Run and validate one resumable production annotation batch."""
    batch_id = batch_manifest["batch_id"]
    batch_root = calibration_root / "population/batches" / batch_id
    output_path = batch_root / "annotations.json"
    if output_path.exists() and not force:
        document = json.loads(output_path.read_text())
    else:
        annotator_id = f"{model}:{level}:feedback-v2-production:{batch_id}"
        completed = subprocess.run(
            feedback_v2_population_command(
                model=model,
                level=level,
                annotator_id=annotator_id,
                batch_relative_root=Path("population/batches") / batch_id,
                batch_sample_sha256=batch_manifest["dataset_sha256"],
            ),
            cwd=calibration_root,
            text=True,
            capture_output=True,
            check=False,
        )
        (batch_root / "annotations.raw.txt").write_text(completed.stdout)
        if completed.stderr:
            (batch_root / "annotations.stderr.txt").write_text(completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(
                f"Feedback population v2: {batch_id} exited {completed.returncode}"
            )
        document = parse_feedback_v2_json_output(completed.stdout)

    original_annotation_order = [
        annotation.get("candidate_unit_id")
        for annotation in document.get("annotations", [])
        if isinstance(annotation, dict)
    ]
    document = repair_feedback_v2_batch_annotation_order(
        document, batch_manifest=batch_manifest
    )
    repaired_annotation_order = [
        annotation["candidate_unit_id"] for annotation in document["annotations"]
    ]
    if repaired_annotation_order != original_annotation_order:
        (batch_root / "annotation-order-repair.json").write_text(
            json.dumps(
                {
                    "repair_rule": "restore_manifest_order_after_exact_unique_candidate_id_permutation",
                    "from": original_annotation_order,
                    "to": repaired_annotation_order,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )

    original_sample_sha256 = document.get("heldout_sample_sha256")
    document = repair_feedback_v2_batch_identity(
        document, batch_manifest=batch_manifest
    )
    if document.get("heldout_sample_sha256") != original_sample_sha256:
        (batch_root / "identity-repair.json").write_text(
            json.dumps(
                {
                    "repair_rule": "append_one_missing_sha256_character_after_exact_candidate_id_match",
                    "field": "heldout_sample_sha256",
                    "from": original_sample_sha256,
                    "to": document["heldout_sample_sha256"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
    schema = json.loads((batch_root / "annotation-schema.json").read_text())
    validate_feedback_v2_heldout_annotations(
        document, schema=schema, heldout_manifest=batch_manifest
    )
    output_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    return document


def write_feedback_v2_population_outputs(
    *,
    candidate_units: list[dict[str, Any]],
    production_documents: list[dict[str, Any]],
    exclusions: dict[str, list[str]],
    authorization: dict[str, Any],
    calibration_root: Path,
) -> dict[str, Any]:
    """Write the eligible annotation corpus and a complete 1,237-case audit ledger."""
    annotations = [
        annotation
        for document in production_documents
        for annotation in document["annotations"]
    ]
    annotation_by_id = {
        annotation["candidate_unit_id"]: annotation for annotation in annotations
    }
    if len(annotation_by_id) != len(annotations):
        raise ValueError("Feedback population v2: duplicate production annotation IDs")
    exclusion_sets_by_id: dict[str, list[str]] = defaultdict(list)
    for exclusion_set, candidate_ids in exclusions.items():
        for candidate_id in candidate_ids:
            exclusion_sets_by_id[candidate_id].append(exclusion_set)
    if set(annotation_by_id) & set(exclusion_sets_by_id):
        raise ValueError(
            "Feedback population v2: calibration case was production annotated"
        )

    ordered_production_annotations = [
        annotation_by_id[unit["candidate_unit_id"]]
        for unit in candidate_units
        if unit["candidate_unit_id"] in annotation_by_id
    ]
    production_document = {
        "production_annotation_schema_version": 2,
        "candidate_set_sha256": json.loads(CANDIDATE_MANIFEST_PATH.read_text())[
            "candidate_set_sha256"
        ],
        "authorization_sha256": feedback_v2_file_sha256(
            calibration_root / "authorization.json"
        ),
        "production_model": authorization["production_model"],
        "thinking_level": authorization["selected_level"],
        "candidate_unit_count": len(ordered_production_annotations),
        "annotations": ordered_production_annotations,
    }
    production_bytes = (
        json.dumps(production_document, ensure_ascii=False, indent=2) + "\n"
    ).encode()
    population_root = calibration_root / "population"
    (population_root / "production-annotations.json").write_bytes(production_bytes)

    ledger_lines = []
    for unit in candidate_units:
        candidate_id = unit["candidate_unit_id"]
        if candidate_id in annotation_by_id:
            record = {
                "candidate_unit_id": candidate_id,
                "analysis_eligible": True,
                "annotation_status": "production_annotated",
                "annotation_source": f"{authorization['production_model']}:{authorization['selected_level']}",
                "annotation": annotation_by_id[candidate_id],
            }
        else:
            record = {
                "candidate_unit_id": candidate_id,
                "analysis_eligible": False,
                "annotation_status": "calibration_excluded",
                "calibration_sets": exclusion_sets_by_id[candidate_id],
            }
        ledger_lines.append(canonical_feedback_v2_json_bytes(record) + b"\n")
    ledger_bytes = b"".join(ledger_lines)
    (population_root / "candidate-ledger.jsonl").write_bytes(ledger_bytes)

    manifest = {
        "population_manifest_schema_version": 2,
        "candidate_unit_count": len(candidate_units),
        "analysis_eligible_count": len(annotation_by_id),
        "calibration_excluded_count": len(exclusion_sets_by_id),
        "production_annotation_sha256": hashlib.sha256(production_bytes).hexdigest(),
        "candidate_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
        "production_model": authorization["production_model"],
        "thinking_level": authorization["selected_level"],
        "authorization_sha256": feedback_v2_file_sha256(
            calibration_root / "authorization.json"
        ),
        "calibration_exclusion_counts": {
            name: len(candidate_ids) for name, candidate_ids in exclusions.items()
        },
    }
    (population_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    return manifest


def run_feedback_v2_population(
    *,
    calibration_root: Path = CALIBRATION_V2_REPAIR_ROOT,
    concurrency: int = PRODUCTION_CONCURRENCY,
    force: bool = False,
) -> dict[str, Any]:
    """Validate authorization, annotate unseen candidates, and write the audit ledger."""
    authorization_path = calibration_root / "authorization.json"
    authorization = json.loads(authorization_path.read_text())
    heldout_manifest = json.loads(
        (calibration_root / "heldout/manifest.json").read_text()
    )
    validate_feedback_v2_population_authorization(
        authorization,
        heldout_sample_sha256=heldout_manifest["dataset_sha256"],
        annotation_schema_sha256=feedback_v2_file_sha256(
            calibration_root / "annotation-schema.json"
        ),
        calibration_instructions_sha256=feedback_v2_file_sha256(
            calibration_root / "calibration-instructions.md"
        ),
    )
    model = str(authorization["production_model"])
    level = str(authorization["selected_level"])
    if (model, level) != ("openai-codex/gpt-5.6-luna", "xhigh"):
        raise ValueError(
            "Feedback population v2: authorization did not select Luna xhigh"
        )

    candidate_units = [
        json.loads(line) for line in CANDIDATE_UNITS_PATH.read_bytes().splitlines()
    ]
    exclusions = feedback_v2_calibration_exclusions()
    excluded_ids = {candidate_id for ids in exclusions.values() for candidate_id in ids}
    if len(excluded_ids) != 72:
        raise ValueError(
            f"Feedback population v2: expected 72 unique calibration exclusions, got {len(excluded_ids)}"
        )
    production_units = [
        unit
        for unit in candidate_units
        if unit["candidate_unit_id"] not in excluded_ids
    ]
    if len(production_units) != 1165:
        raise ValueError(
            f"Feedback population v2: expected 1165 unseen units, got {len(production_units)}"
        )
    batch_manifests = materialize_feedback_v2_population_batches(
        production_units=production_units, calibration_root=calibration_root
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        production_documents = list(
            executor.map(
                lambda manifest: run_feedback_v2_population_batch(
                    batch_manifest=manifest,
                    calibration_root=calibration_root,
                    model=model,
                    level=level,
                    force=force,
                ),
                batch_manifests,
            )
        )
    return write_feedback_v2_population_outputs(
        candidate_units=candidate_units,
        production_documents=production_documents,
        exclusions=exclusions,
        authorization=authorization,
        calibration_root=calibration_root,
    )


def main() -> None:
    """Run or resume authorized full-population feedback annotation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--concurrency", type=int, default=PRODUCTION_CONCURRENCY)
    parser.add_argument(
        "--calibration-root", type=Path, default=CALIBRATION_V2_REPAIR_ROOT
    )
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_feedback_v2_population(
                calibration_root=arguments.calibration_root.resolve(),
                concurrency=arguments.concurrency,
                force=arguments.force,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
