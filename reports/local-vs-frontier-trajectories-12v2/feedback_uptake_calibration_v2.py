"""Validate feedback-uptake calibration v2 artifacts and authorization."""

from __future__ import annotations

import hashlib
from typing import Any

FEEDBACK_V2_PRODUCTION_MODELS = frozenset(
    {
        "openai-codex/gpt-5.6-luna",
        "zai/glm-5.2",
    }
)
FEEDBACK_V2_PRODUCTION_PROTOCOLS = (
    ("openai-codex/gpt-5.6-luna", "xhigh"),
    ("zai/glm-5.2", "max"),
)
FEEDBACK_V2_FIELD_MINIMUM_RATES = {
    "candidate_disposition": 23 / 24,
    "observation_class": 22 / 24,
    "action_purpose": 21 / 24,
    "next_response_label": 20 / 24,
    "window_outcome": 20 / 24,
    "relevant_change_observed": 20 / 24,
    "post_change_validation_scope": 20 / 24,
    "plan_revision": 18 / 24,
}
FEEDBACK_V2_EXACT_UNIT_MINIMUM_RATE = 14 / 24


class FeedbackCalibrationV2ValidationError(ValueError):
    """Report an invalid feedback calibration v2 artifact or decision."""


def score_feedback_v2_annotations(
    gold: dict[str, Any], prediction: dict[str, Any]
) -> dict[str, Any]:
    """Score semantic labels without requiring identical uncertainty wording."""
    gold_annotations = {
        annotation["candidate_unit_id"]: annotation
        for annotation in gold["annotations"]
    }
    prediction_annotations = {
        annotation["candidate_unit_id"]: annotation
        for annotation in prediction["annotations"]
    }
    if list(gold_annotations) != list(prediction_annotations):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 score: candidate IDs or order differ"
        )
    denominator = len(gold_annotations)
    field_scores = {}
    for field in FEEDBACK_V2_FIELD_MINIMUM_RATES:
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
            for field in FEEDBACK_V2_FIELD_MINIMUM_RATES
        )
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
    }


def feedback_v2_score_passes(score: dict[str, Any]) -> bool:
    """Return whether one held-out score meets every declared v2 threshold."""
    return (
        all(
            score["field_scores"][field]["rate"] >= minimum_rate
            for field, minimum_rate in FEEDBACK_V2_FIELD_MINIMUM_RATES.items()
        )
        and score["exact_unit_score"]["rate"] >= FEEDBACK_V2_EXACT_UNIT_MINIMUM_RATE
    )


def evaluate_feedback_v2_production_protocol(
    *,
    model: str,
    level: str,
    gold: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Require two accurate and mutually repeatable runs for one production protocol."""
    require_feedback_v2_production_model(model)
    if (model, level) not in FEEDBACK_V2_PRODUCTION_PROTOCOLS:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: unsupported production model and thinking pair"
        )
    if len(runs) != 2:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: production protocol requires exactly two runs"
        )
    run_scores = [score_feedback_v2_annotations(gold, run) for run in runs]
    repeatability_score = score_feedback_v2_annotations(runs[0], runs[1])
    run_passes = [feedback_v2_score_passes(score) for score in run_scores]
    repeatability_passes = feedback_v2_score_passes(repeatability_score)
    return {
        "model": model,
        "level": level,
        "runs_per_level": 2,
        "run_scores": run_scores,
        "run_passes": run_passes,
        "repeatability_score": repeatability_score,
        "repeatability_passes": repeatability_passes,
        "passes": all(run_passes) and repeatability_passes,
    }


def select_feedback_v2_production_protocol(
    evaluations: list[dict[str, Any]],
    *,
    heldout_sample_sha256: str,
    annotation_schema_sha256: str,
    calibration_instructions_sha256: str,
) -> dict[str, Any]:
    """Select the predeclared Luna protocol, then GLM, or block full annotation."""
    evaluations_by_protocol = {
        (evaluation["model"], evaluation["level"]): evaluation
        for evaluation in evaluations
    }
    if set(evaluations_by_protocol) != set(FEEDBACK_V2_PRODUCTION_PROTOCOLS):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 selection: both declared production protocols are required"
        )
    selected = next(
        (
            protocol
            for protocol in FEEDBACK_V2_PRODUCTION_PROTOCOLS
            if evaluations_by_protocol[protocol]["passes"]
        ),
        None,
    )
    return {
        "authorization_schema_version": 2,
        "production_model": selected[0] if selected else None,
        "selected_level": selected[1] if selected else None,
        "heldout_sample_sha256": heldout_sample_sha256,
        "annotation_schema_sha256": annotation_schema_sha256,
        "calibration_instructions_sha256": calibration_instructions_sha256,
        "runs_per_level": 2,
        "selection_status": "passed" if selected else "blocked",
        "full_population_authorized": selected is not None,
        "fallback_used": False,
    }


def require_feedback_v2_production_model(model: str) -> str:
    """Accept only Luna or GLM-5.2 as the full-population annotation model."""
    if model not in FEEDBACK_V2_PRODUCTION_MODELS:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: production model must be GPT-5.6 Luna or GLM-5.2"
        )
    return model


FEEDBACK_V2_UPTAKE_FIELDS = (
    "next_response_label",
    "window_outcome",
    "relevant_change_observed",
    "post_change_validation_scope",
    "plan_revision",
)
FEEDBACK_V2_SEMANTIC_FIELDS = (
    "candidate_disposition",
    "observation_class",
    "action_purpose",
    *FEEDBACK_V2_UPTAKE_FIELDS,
)


def select_feedback_v2_heldout_units(
    *,
    candidate_units: list[dict[str, Any]],
    strata: list[dict[str, str]],
    excluded_ids: set[str],
) -> list[dict[str, Any]]:
    """Choose the lowest-hash unused candidate in each declared held-out category."""
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for stratum in strata:
        matches = [
            candidate
            for candidate in candidate_units
            if candidate["candidate_unit_id"] not in excluded_ids
            and candidate["candidate_unit_id"] not in selected_ids
            and candidate["model_key"] == stratum["model_key"]
            and candidate["task"] == stratum["task"]
            and stratum["candidate_signal_type"]
            in candidate["focal_event"]["candidate_signal_types"]
        ]
        if not matches:
            raise FeedbackCalibrationV2ValidationError(
                "Feedback calibration v2 selection: declared held-out category has no unused candidate"
            )
        matches.sort(
            key=lambda candidate: hashlib.sha256(
                candidate["candidate_unit_id"].encode()
            ).hexdigest()
        )
        chosen = matches[0]
        selected.append(chosen)
        selected_ids.add(chosen["candidate_unit_id"])
    return selected


def validate_feedback_v2_dataset_split(
    *,
    development_ids: list[str],
    heldout_ids: list[str],
    retired_v1_ids: list[str],
) -> None:
    """Reject duplicate, leaked, or previously tuned held-out candidate IDs."""
    for label, candidate_ids in (
        ("development", development_ids),
        ("held-out", heldout_ids),
        ("v1 calibration", retired_v1_ids),
    ):
        if len(candidate_ids) != len(set(candidate_ids)):
            raise FeedbackCalibrationV2ValidationError(
                f"Feedback calibration v2: {label} candidate IDs are not unique"
            )
    if set(development_ids) & set(heldout_ids):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: development and held-out cases overlap"
        )
    if set(heldout_ids) & set(retired_v1_ids):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: held-out cases reuse v1 calibration"
        )


FEEDBACK_V2_AUTHORIZATION_FIELDS = {
    "authorization_schema_version",
    "production_model",
    "selected_level",
    "heldout_sample_sha256",
    "annotation_schema_sha256",
    "calibration_instructions_sha256",
    "runs_per_level",
    "selection_status",
    "full_population_authorized",
    "fallback_used",
}


def validate_feedback_v2_population_authorization(
    authorization: dict[str, object],
    *,
    heldout_sample_sha256: str,
    annotation_schema_sha256: str,
    calibration_instructions_sha256: str,
) -> None:
    """Require a passing Luna or GLM receipt for the exact v2 calibration inputs."""
    if set(authorization) != FEEDBACK_V2_AUTHORIZATION_FIELDS:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 authorization: fields differ from schema"
        )
    require_feedback_v2_production_model(str(authorization["production_model"]))
    expected_values = {
        "authorization_schema_version": 2,
        "heldout_sample_sha256": heldout_sample_sha256,
        "annotation_schema_sha256": annotation_schema_sha256,
        "calibration_instructions_sha256": calibration_instructions_sha256,
        "runs_per_level": 2,
        "selection_status": "passed",
        "full_population_authorized": True,
        "fallback_used": False,
    }
    for field, expected in expected_values.items():
        if authorization.get(field) != expected:
            raise FeedbackCalibrationV2ValidationError(
                f"Feedback calibration v2 authorization: invalid {field}"
            )
    if (
        not isinstance(authorization.get("selected_level"), str)
        or not authorization["selected_level"]
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 authorization: selected level is required"
        )


def validate_feedback_v2_annotation_shape(
    annotation: dict[str, Any], *, schema: dict[str, Any]
) -> None:
    """Validate one annotation against the v2 field and enum vocabulary."""
    annotation_schema = schema["$defs"]["annotation"]
    properties = annotation_schema["properties"]
    if set(annotation) != set(properties):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: annotation fields differ from schema"
        )
    for field, definition in properties.items():
        if "enum" in definition and annotation.get(field) not in definition["enum"]:
            raise FeedbackCalibrationV2ValidationError(
                f"Feedback calibration v2: invalid {field}"
            )
    uncertainty_reasons = annotation.get("uncertainty_reasons")
    allowed_reasons = set(properties["uncertainty_reasons"]["items"]["enum"])
    if (
        not isinstance(uncertainty_reasons, list)
        or len(uncertainty_reasons) != len(set(uncertainty_reasons))
        or any(reason not in allowed_reasons for reason in uncertainty_reasons)
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: invalid uncertainty reasons"
        )
    evidence_summary = annotation.get("evidence_summary")
    if not isinstance(evidence_summary, str) or len(evidence_summary) < 10:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: evidence summary is too short"
        )
    validate_feedback_v2_annotation_semantics(annotation)


def validate_feedback_v2_development_annotations(
    document: dict[str, Any],
    *,
    schema: dict[str, Any],
    development_manifest: dict[str, Any],
) -> None:
    """Require worked labels for the exact development examples in fixed order."""
    if set(document) != {"annotation_schema_version", "purpose", "annotations"}:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 development: document fields differ from schema"
        )
    if document.get("annotation_schema_version") != 2:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 development: schema version mismatch"
        )
    annotations = document.get("annotations")
    if not isinstance(annotations, list):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 development: annotations must be a list"
        )
    actual_ids = [annotation.get("candidate_unit_id") for annotation in annotations]
    if actual_ids != development_manifest["candidate_unit_ids"]:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 development: annotations do not match example order"
        )
    for annotation in annotations:
        validate_feedback_v2_annotation_shape(annotation, schema=schema)


def validate_feedback_v2_heldout_annotations(
    document: dict[str, Any],
    *,
    schema: dict[str, Any],
    heldout_manifest: dict[str, Any],
) -> None:
    """Require one valid annotation for every held-out case in fixed order."""
    if set(document) != set(schema["properties"]):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: document fields differ from schema"
        )
    if document.get("annotation_schema_version") != 2:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: schema version mismatch"
        )
    if document.get("candidate_set_sha256") != heldout_manifest.get(
        "candidate_set_sha256"
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: candidate set identity mismatch"
        )
    if document.get("heldout_sample_sha256") != heldout_manifest.get("dataset_sha256"):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: sample identity mismatch"
        )
    if (
        not isinstance(document.get("annotator_id"), str)
        or not document["annotator_id"]
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: annotator ID is required"
        )
    annotations = document.get("annotations")
    if not isinstance(annotations, list):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: annotations must be a list"
        )
    actual_ids = [annotation.get("candidate_unit_id") for annotation in annotations]
    if actual_ids != heldout_manifest["candidate_unit_ids"]:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2 held-out: annotations do not match sample order"
        )
    for annotation in annotations:
        validate_feedback_v2_annotation_shape(annotation, schema=schema)


def validate_feedback_v2_annotation_semantics(annotation: dict[str, object]) -> None:
    """Enforce post-change validation and uncertainty rules for one annotation."""
    disposition = annotation.get("candidate_disposition")
    if disposition != "negative_feedback" and any(
        annotation.get(field) != "not_applicable" for field in FEEDBACK_V2_UPTAKE_FIELDS
    ):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: nonnegative candidate has feedback-uptake labels"
        )

    change_observed = annotation.get("relevant_change_observed")
    validation_scope = annotation.get("post_change_validation_scope")
    if change_observed == "no" and validation_scope != "not_applicable":
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: post-change validation is not applicable without a relevant change"
        )
    if change_observed == "yes" and validation_scope == "not_applicable":
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: observed change requires a post-change validation label"
        )
    if change_observed == "indeterminate" and validation_scope != "indeterminate":
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: indeterminate change requires indeterminate validation scope"
        )

    confidence = annotation.get("confidence")
    uncertainty_reasons = annotation.get("uncertainty_reasons")
    if not isinstance(uncertainty_reasons, list):
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: uncertainty reasons must be a list"
        )
    has_indeterminate_label = any(
        annotation.get(field) == "indeterminate"
        for field in FEEDBACK_V2_SEMANTIC_FIELDS
    )
    if (confidence != "high" or has_indeterminate_label) and not uncertainty_reasons:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: uncertain annotation requires at least one reason"
        )
    if confidence == "high" and uncertainty_reasons:
        raise FeedbackCalibrationV2ValidationError(
            "Feedback calibration v2: high confidence cannot include uncertainty reasons"
        )
