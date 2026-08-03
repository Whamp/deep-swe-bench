"""Validate and score fixed-unit feedback-uptake calibration annotations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCORED_SEMANTIC_FIELDS = (
    "candidate_disposition",
    "observation_class",
    "action_purpose",
    "next_response_label",
    "window_outcome",
    "revalidation_scope",
    "plan_revision",
)
CALIBRATION_LEVEL_ORDER = ("low", "medium", "high", "xhigh", "max")
CALIBRATION_FIELD_MINIMUM_RATES = {
    "candidate_disposition": 23 / 24,
    "observation_class": 22 / 24,
    "action_purpose": 21 / 24,
    "next_response_label": 20 / 24,
    "window_outcome": 20 / 24,
    "revalidation_scope": 20 / 24,
    "plan_revision": 18 / 24,
}
CALIBRATION_EXACT_UNIT_MINIMUM_RATE = 14 / 24
CALIBRATION_UNCERTAINTY_MINIMUM_RATE = 18 / 24

NOT_APPLICABLE_SEMANTIC_FIELDS = (
    "next_response_label",
    "window_outcome",
    "revalidation_scope",
    "plan_revision",
)
REQUIRED_NEGATIVE_FEEDBACK_FIELDS = (
    "next_response_label",
    "window_outcome",
    "plan_revision",
)


class FeedbackCalibrationValidationError(ValueError):
    """Report a formal annotation schema, identity, or cross-field violation."""


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize one value for stable calibration identity hashes."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def load_feedback_calibration_sample(
    *, selection_path: Path, sample_root: Path, candidate_units_path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and verify the exact stratified sample against the frozen candidates."""
    selection = json.loads(selection_path.read_text())
    manifest = json.loads((sample_root / "manifest.json").read_text())
    sample_bytes = (sample_root / "units.jsonl").read_bytes()
    if (
        manifest.get("selection_sha256")
        != hashlib.sha256(canonical_json_bytes(selection)).hexdigest()
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: selection SHA-256 mismatch"
        )
    if (
        manifest.get("calibration_sample_sha256")
        != hashlib.sha256(sample_bytes).hexdigest()
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: sample SHA-256 mismatch"
        )
    sample_units = [json.loads(line) for line in sample_bytes.splitlines()]
    master_units = {
        unit["candidate_unit_id"]: unit
        for unit in (
            json.loads(line) for line in candidate_units_path.read_bytes().splitlines()
        )
    }
    selected_ids = selection.get("candidate_unit_ids")
    if not isinstance(selected_ids, list) or len(selected_ids) != len(
        set(selected_ids)
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: selection IDs must be a unique list"
        )
    try:
        expected_units = [master_units[candidate_id] for candidate_id in selected_ids]
    except KeyError as error:
        raise FeedbackCalibrationValidationError(
            f"Feedback calibration: unknown selected candidate {error.args[0]}"
        ) from error
    if sample_units != expected_units:
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: sample units differ from frozen candidates"
        )
    if manifest.get("candidate_unit_ids") != selected_ids:
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: sample manifest ID order mismatch"
        )
    if manifest.get("candidate_unit_count") != len(sample_units):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: sample manifest count mismatch"
        )
    return manifest, sample_units


def annotation_schema_enums(schema: dict[str, Any]) -> dict[str, set[str]]:
    """Extract annotation enum vocabularies from the formal JSON Schema."""
    properties = schema["$defs"]["annotation"]["properties"]
    return {
        field: set(definition["enum"])
        for field, definition in properties.items()
        if "enum" in definition
    }


def validate_feedback_calibration_annotations(
    document: dict[str, Any],
    *,
    schema: dict[str, Any],
    sample_manifest: dict[str, Any],
) -> None:
    """Fail closed unless one annotation document covers the exact fixed sample."""
    expected_document_fields = set(schema["properties"])
    if set(document) != expected_document_fields:
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: annotation document fields differ from schema"
        )
    if document.get("annotation_schema_version") != 1:
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: annotation schema version mismatch"
        )
    if document.get("candidate_set_sha256") != sample_manifest.get(
        "candidate_set_sha256"
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: candidate set identity mismatch"
        )
    if document.get("calibration_sample_sha256") != sample_manifest.get(
        "calibration_sample_sha256"
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: sample identity mismatch"
        )
    if (
        not isinstance(document.get("annotator_id"), str)
        or not document["annotator_id"]
    ):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: annotator ID is required"
        )
    annotations = document.get("annotations")
    if not isinstance(annotations, list):
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: annotations must be a list"
        )
    expected_ids = sample_manifest["candidate_unit_ids"]
    actual_ids = [
        annotation.get("candidate_unit_id") if isinstance(annotation, dict) else None
        for annotation in annotations
    ]
    if actual_ids != expected_ids:
        raise FeedbackCalibrationValidationError(
            "Feedback calibration: annotations must cover exact sample ID order"
        )

    annotation_schema = schema["$defs"]["annotation"]
    expected_annotation_fields = set(annotation_schema["properties"])
    enums = annotation_schema_enums(schema)
    uncertainty_enum = set(
        annotation_schema["properties"]["uncertainty_reasons"]["items"]["enum"]
    )
    for annotation in annotations:
        candidate_id = annotation["candidate_unit_id"]
        if set(annotation) != expected_annotation_fields:
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: annotation fields differ from schema for {candidate_id}"
            )
        for field, allowed_values in enums.items():
            if annotation.get(field) not in allowed_values:
                raise FeedbackCalibrationValidationError(
                    f"Feedback calibration: invalid {field} for {candidate_id}"
                )
        uncertainty_reasons = annotation.get("uncertainty_reasons")
        if (
            not isinstance(uncertainty_reasons, list)
            or len(uncertainty_reasons) != len(set(uncertainty_reasons))
            or any(reason not in uncertainty_enum for reason in uncertainty_reasons)
        ):
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: invalid uncertainty reasons for {candidate_id}"
            )
        evidence_summary = annotation.get("evidence_summary")
        if not isinstance(evidence_summary, str) or len(evidence_summary) < 10:
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: evidence summary is too short for {candidate_id}"
            )
        disposition = annotation["candidate_disposition"]
        if disposition != "negative_feedback" and any(
            annotation[field] != "not_applicable"
            for field in NOT_APPLICABLE_SEMANTIC_FIELDS
        ):
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: excluded candidate has uptake labels for {candidate_id}"
            )
        if disposition == "negative_feedback" and any(
            annotation[field] == "not_applicable"
            for field in REQUIRED_NEGATIVE_FEEDBACK_FIELDS
        ):
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: negative feedback lacks uptake labels for {candidate_id}"
            )
        if (
            any(
                annotation[field] == "indeterminate" for field in SCORED_SEMANTIC_FIELDS
            )
            and not uncertainty_reasons
        ):
            raise FeedbackCalibrationValidationError(
                f"Feedback calibration: indeterminate label lacks uncertainty for {candidate_id}"
            )


def score_feedback_calibration_annotations(
    gold: dict[str, Any], prediction: dict[str, Any]
) -> dict[str, Any]:
    """Score bounded semantic fields against hand-adjudicated fixed-unit gold."""
    gold_annotations = {
        annotation["candidate_unit_id"]: annotation
        for annotation in gold["annotations"]
    }
    prediction_annotations = {
        annotation["candidate_unit_id"]: annotation
        for annotation in prediction["annotations"]
    }
    denominator = len(gold_annotations)
    field_scores: dict[str, dict[str, Any]] = {}
    for field in SCORED_SEMANTIC_FIELDS:
        matches = sum(
            gold_annotations[candidate_id][field]
            == prediction_annotations[candidate_id][field]
            for candidate_id in gold_annotations
        )
        field_scores[field] = {
            "matches": matches,
            "denominator": denominator,
            "rate": matches / denominator,
        }
    exact_matches = sum(
        all(
            gold_annotations[candidate_id][field]
            == prediction_annotations[candidate_id][field]
            for field in SCORED_SEMANTIC_FIELDS
        )
        for candidate_id in gold_annotations
    )
    uncertainty_matches = sum(
        gold_annotations[candidate_id]["uncertainty_reasons"]
        == prediction_annotations[candidate_id]["uncertainty_reasons"]
        for candidate_id in gold_annotations
    )
    return {
        "candidate_units": denominator,
        "field_scores": field_scores,
        "exact_unit_score": {
            "matches": exact_matches,
            "denominator": denominator,
            "rate": exact_matches / denominator,
        },
        "uncertainty_reason_score": {
            "matches": uncertainty_matches,
            "denominator": denominator,
            "rate": uncertainty_matches / denominator,
        },
    }


def feedback_calibration_score_passes(score: dict[str, Any]) -> bool:
    """Return whether one valid run meets every predeclared quality threshold."""
    return (
        all(
            score["field_scores"][field]["rate"] >= minimum_rate
            for field, minimum_rate in CALIBRATION_FIELD_MINIMUM_RATES.items()
        )
        and score["exact_unit_score"]["rate"] >= CALIBRATION_EXACT_UNIT_MINIMUM_RATE
        and score["uncertainty_reason_score"]["rate"]
        >= CALIBRATION_UNCERTAINTY_MINIMUM_RATE
    )


def evaluate_feedback_calibration_level(
    *, level: str, gold: dict[str, Any], runs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Require two individually accurate and mutually repeatable fixed-sample runs."""
    if level not in CALIBRATION_LEVEL_ORDER:
        raise ValueError(f"Feedback calibration: unknown Luna level {level!r}")
    if len(runs) != 2:
        raise ValueError(
            f"Feedback calibration: level {level} requires exactly two runs"
        )
    run_scores = [score_feedback_calibration_annotations(gold, run) for run in runs]
    repeatability_score = score_feedback_calibration_annotations(runs[0], runs[1])
    run_passes = [feedback_calibration_score_passes(score) for score in run_scores]
    repeatability_passes = feedback_calibration_score_passes(repeatability_score)
    return {
        "level": level,
        "run_scores": run_scores,
        "run_passes": run_passes,
        "repeatability_score": repeatability_score,
        "repeatability_passes": repeatability_passes,
        "passes": all(run_passes) and repeatability_passes,
    }


def select_feedback_calibration_level(
    level_evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select the lowest passing Luna level or block with no fallback."""
    evaluations_by_level = {
        evaluation["level"]: evaluation for evaluation in level_evaluations
    }
    if set(evaluations_by_level) != set(CALIBRATION_LEVEL_ORDER):
        raise ValueError(
            "Feedback calibration: selection requires every declared Luna level"
        )
    selected_level = next(
        (
            level
            for level in CALIBRATION_LEVEL_ORDER
            if evaluations_by_level[level]["passes"]
        ),
        None,
    )
    return {
        "selection_status": "passed" if selected_level is not None else "blocked",
        "selected_level": selected_level,
        "full_population_authorized": selected_level is not None,
        "fallback_used": False,
        "level_order": list(CALIBRATION_LEVEL_ORDER),
        "level_passes": {
            level: evaluations_by_level[level]["passes"]
            for level in CALIBRATION_LEVEL_ORDER
        },
        "reason": (
            f"Lowest level passing both runs and repeatability: {selected_level}."
            if selected_level is not None
            else "No Luna level passed both gold-accuracy runs and repeatability; full-population annotation is blocked."
        ),
    }
