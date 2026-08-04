#!/usr/bin/env python3
"""Build disjoint development and held-out datasets for feedback calibration v2."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from feedback_uptake_calibration_v2 import (
    FeedbackCalibrationV2ValidationError,
    select_feedback_v2_heldout_units,
    validate_feedback_v2_dataset_split,
)

REPORT_ROOT = Path(__file__).resolve().parent
FEEDBACK_ROOT = REPORT_ROOT / "feedback-uptake"
CALIBRATION_V1_ROOT = FEEDBACK_ROOT / "calibration"
CALIBRATION_V2_ROOT = FEEDBACK_ROOT / "calibration-v2"
CALIBRATION_V2_REPAIR_ROOT = FEEDBACK_ROOT / "calibration-v2-repair"
CANDIDATE_UNITS_PATH = FEEDBACK_ROOT / "candidates/units.jsonl"
CANDIDATE_MANIFEST_PATH = FEEDBACK_ROOT / "candidates/manifest.json"


def canonical_feedback_v2_json_bytes(value: Any) -> bytes:
    """Serialize one calibration value with stable identity bytes."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def feedback_v2_jsonl_bytes(units: list[dict[str, Any]]) -> bytes:
    """Serialize selected candidate units in stable JSONL form."""
    return b"".join(canonical_feedback_v2_json_bytes(unit) + b"\n" for unit in units)


def feedback_v2_dataset_manifest(
    *,
    dataset_name: str,
    candidate_set_sha256: str,
    selection: dict[str, Any],
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    """Describe one immutable feedback calibration v2 dataset."""
    unit_bytes = feedback_v2_jsonl_bytes(units)
    signal_types = sorted(
        {
            signal_type
            for unit in units
            for signal_type in unit["focal_event"]["candidate_signal_types"]
        }
    )
    return {
        "dataset_manifest_schema_version": 2,
        "dataset_name": dataset_name,
        "candidate_set_sha256": candidate_set_sha256,
        "selection_sha256": hashlib.sha256(
            canonical_feedback_v2_json_bytes(selection)
        ).hexdigest(),
        "dataset_sha256": hashlib.sha256(unit_bytes).hexdigest(),
        "dataset_bytes": len(unit_bytes),
        "candidate_unit_count": len(units),
        "model_counts": dict(
            sorted(Counter(unit["model_key"] for unit in units).items())
        ),
        "tasks": sorted({unit["task"] for unit in units}),
        "outcomes": sorted({unit["result_outcome"]["reward_binary"] for unit in units}),
        "candidate_signal_types": signal_types,
        "candidate_unit_ids": [unit["candidate_unit_id"] for unit in units],
    }


def feedback_v2_primary_generated_artifacts() -> dict[Path, bytes]:
    """Return the original v2 dataset artifacts keyed by repository path."""
    candidate_manifest = json.loads(CANDIDATE_MANIFEST_PATH.read_text())
    candidate_units = [
        json.loads(line) for line in CANDIDATE_UNITS_PATH.read_bytes().splitlines()
    ]
    candidate_by_id = {unit["candidate_unit_id"]: unit for unit in candidate_units}
    if len(candidate_by_id) != len(candidate_units):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 build: candidate IDs are not unique"
        )

    retired_v1_selection = json.loads(
        (CALIBRATION_V1_ROOT / "sample-selection.json").read_text()
    )
    retired_v1_ids = retired_v1_selection["candidate_unit_ids"]
    development_selection_path = CALIBRATION_V2_ROOT / "development/selection.json"
    development_selection = json.loads(development_selection_path.read_text())
    development_ids = development_selection["candidate_unit_ids"]
    try:
        development_units = [
            candidate_by_id[candidate_id] for candidate_id in development_ids
        ]
    except KeyError as error:
        raise FeedbackCalibrationV2ValidationError(
            f"Feedback calibration v2 build: unknown development candidate {error.args[0]}"
        ) from error

    heldout_strata_path = CALIBRATION_V2_ROOT / "heldout/strata.json"
    heldout_strata_document = json.loads(heldout_strata_path.read_text())
    heldout_units = select_feedback_v2_heldout_units(
        candidate_units=candidate_units,
        strata=heldout_strata_document["strata"],
        excluded_ids=set(retired_v1_ids),
    )
    heldout_ids = [unit["candidate_unit_id"] for unit in heldout_units]
    validate_feedback_v2_dataset_split(
        development_ids=development_ids,
        heldout_ids=heldout_ids,
        retired_v1_ids=retired_v1_ids,
    )

    candidate_set_sha256 = candidate_manifest["candidate_set_sha256"]
    heldout_selection = {
        "selection_schema_version": 2,
        "candidate_set_sha256": candidate_set_sha256,
        "purpose": "Fresh held-out feedback calibration v2 sample; never use for development examples or efficacy rates.",
        "selection_method": "lowest_sha256_candidate_id_per_declared_stratum_after_excluding_all_v1_calibration_ids",
        "strata_sha256": hashlib.sha256(
            canonical_feedback_v2_json_bytes(heldout_strata_document)
        ).hexdigest(),
        "excluded_v1_selection_sha256": hashlib.sha256(
            canonical_feedback_v2_json_bytes(retired_v1_selection)
        ).hexdigest(),
        "candidate_unit_ids": heldout_ids,
    }
    development_manifest = feedback_v2_dataset_manifest(
        dataset_name="development_examples",
        candidate_set_sha256=candidate_set_sha256,
        selection=development_selection,
        units=development_units,
    )
    heldout_manifest = feedback_v2_dataset_manifest(
        dataset_name="heldout_calibration",
        candidate_set_sha256=candidate_set_sha256,
        selection=heldout_selection,
        units=heldout_units,
    )
    return {
        CALIBRATION_V2_ROOT / "development/units.jsonl": feedback_v2_jsonl_bytes(
            development_units
        ),
        CALIBRATION_V2_ROOT / "development/manifest.json": json.dumps(
            development_manifest, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
        CALIBRATION_V2_ROOT / "heldout/selection.json": json.dumps(
            heldout_selection, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
        CALIBRATION_V2_ROOT / "heldout/units.jsonl": feedback_v2_jsonl_bytes(
            heldout_units
        ),
        CALIBRATION_V2_ROOT / "heldout/manifest.json": json.dumps(
            heldout_manifest, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
    }


def feedback_v2_repair_generated_artifacts() -> dict[Path, bytes]:
    """Return fresh repair-round artifacts after excluding every prior test case."""
    candidate_manifest = json.loads(CANDIDATE_MANIFEST_PATH.read_text())
    candidate_units = [
        json.loads(line) for line in CANDIDATE_UNITS_PATH.read_bytes().splitlines()
    ]
    candidate_by_id = {unit["candidate_unit_id"]: unit for unit in candidate_units}
    retired_v1_selection = json.loads(
        (CALIBRATION_V1_ROOT / "sample-selection.json").read_text()
    )
    retired_v2_selection = json.loads(
        (CALIBRATION_V2_ROOT / "heldout/selection.json").read_text()
    )
    retired_ids = [
        *retired_v1_selection["candidate_unit_ids"],
        *retired_v2_selection["candidate_unit_ids"],
    ]
    development_selection = json.loads(
        (CALIBRATION_V2_REPAIR_ROOT / "development/selection.json").read_text()
    )
    development_ids = development_selection["candidate_unit_ids"]
    try:
        development_units = [
            candidate_by_id[candidate_id] for candidate_id in development_ids
        ]
    except KeyError as error:
        raise FeedbackCalibrationV2ValidationError(
            f"Feedback calibration v2 repair build: unknown development candidate {error.args[0]}"
        ) from error

    heldout_strata_document = json.loads(
        (CALIBRATION_V2_REPAIR_ROOT / "heldout/strata.json").read_text()
    )
    heldout_units = select_feedback_v2_heldout_units(
        candidate_units=candidate_units,
        strata=heldout_strata_document["strata"],
        excluded_ids=set(retired_ids),
    )
    heldout_ids = [unit["candidate_unit_id"] for unit in heldout_units]
    validate_feedback_v2_dataset_split(
        development_ids=development_ids,
        heldout_ids=heldout_ids,
        retired_v1_ids=retired_ids,
    )

    candidate_set_sha256 = candidate_manifest["candidate_set_sha256"]
    heldout_selection = {
        "selection_schema_version": 2,
        "candidate_set_sha256": candidate_set_sha256,
        "purpose": "Fresh repair-round held-out sample; never use for development examples or efficacy rates.",
        "selection_method": "lowest_sha256_candidate_id_per_declared_stratum_after_excluding_v1_and_initial_v2_calibration_ids",
        "strata_sha256": hashlib.sha256(
            canonical_feedback_v2_json_bytes(heldout_strata_document)
        ).hexdigest(),
        "excluded_prior_selection_sha256": hashlib.sha256(
            canonical_feedback_v2_json_bytes(
                {
                    "v1": retired_v1_selection["candidate_unit_ids"],
                    "v2": retired_v2_selection["candidate_unit_ids"],
                }
            )
        ).hexdigest(),
        "candidate_unit_ids": heldout_ids,
    }
    development_manifest = feedback_v2_dataset_manifest(
        dataset_name="repair_development_examples",
        candidate_set_sha256=candidate_set_sha256,
        selection=development_selection,
        units=development_units,
    )
    heldout_manifest = feedback_v2_dataset_manifest(
        dataset_name="repair_heldout_calibration",
        candidate_set_sha256=candidate_set_sha256,
        selection=heldout_selection,
        units=heldout_units,
    )
    return {
        CALIBRATION_V2_REPAIR_ROOT / "development/units.jsonl": feedback_v2_jsonl_bytes(
            development_units
        ),
        CALIBRATION_V2_REPAIR_ROOT / "development/manifest.json": json.dumps(
            development_manifest, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
        CALIBRATION_V2_REPAIR_ROOT / "heldout/selection.json": json.dumps(
            heldout_selection, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
        CALIBRATION_V2_REPAIR_ROOT / "heldout/units.jsonl": feedback_v2_jsonl_bytes(
            heldout_units
        ),
        CALIBRATION_V2_REPAIR_ROOT / "heldout/manifest.json": json.dumps(
            heldout_manifest, ensure_ascii=False, indent=2
        ).encode()
        + b"\n",
    }


def feedback_v2_generated_artifacts() -> dict[Path, bytes]:
    """Return generated artifacts for the original and one allowed repair round."""
    artifacts = feedback_v2_primary_generated_artifacts()
    artifacts.update(feedback_v2_repair_generated_artifacts())
    return artifacts


def write_feedback_v2_generated_artifacts(*, check: bool) -> None:
    """Write generated artifacts atomically or verify committed bytes exactly."""
    for path, expected_bytes in feedback_v2_generated_artifacts().items():
        if check:
            if not path.exists() or path.read_bytes() != expected_bytes:
                raise FeedbackCalibrationV2ValidationError(
                    f"Feedback calibration v2 build check: stale artifact {path}"
                )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_name(f".{path.name}.tmp")
        temporary_path.write_bytes(expected_bytes)
        temporary_path.replace(path)


def main() -> None:
    """Build or check feedback calibration v2 development and held-out datasets."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    write_feedback_v2_generated_artifacts(check=arguments.check)


if __name__ == "__main__":
    main()
