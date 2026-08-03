import copy
import json
from pathlib import Path

import pytest

from feedback_uptake_calibration import (
    CALIBRATION_LEVEL_ORDER,
    FeedbackCalibrationValidationError,
    evaluate_feedback_calibration_level,
    load_feedback_calibration_sample,
    score_feedback_calibration_annotations,
    select_feedback_calibration_level,
    validate_feedback_calibration_annotations,
)
from run_feedback_uptake_calibration import (
    luna_calibration_command,
    parse_luna_json_output,
)

REPORT_ROOT = Path(__file__).parent
CALIBRATION_ROOT = REPORT_ROOT / "feedback-uptake/calibration"


def load_calibration_artifacts() -> tuple[dict, dict, dict]:
    """Load the formal schema, fixed sample manifest, and hand-adjudicated gold."""
    schema = json.loads((CALIBRATION_ROOT / "annotation-schema.json").read_text())
    manifest = json.loads((CALIBRATION_ROOT / "sample/manifest.json").read_text())
    gold = json.loads((CALIBRATION_ROOT / "gold-adjudication.json").read_text())
    return schema, manifest, gold


def test_fixed_calibration_sample_matches_frozen_candidates() -> None:
    manifest, units = load_feedback_calibration_sample(
        selection_path=CALIBRATION_ROOT / "sample-selection.json",
        sample_root=CALIBRATION_ROOT / "sample",
        candidate_units_path=REPORT_ROOT / "feedback-uptake/candidates/units.jsonl",
    )

    assert len(units) == 24
    assert manifest["model_counts"] == {
        "agentworld": 8,
        "frontier": 8,
        "thinkingcap": 8,
    }
    assert len(manifest["tasks"]) == 12
    assert {unit["candidate_unit_id"] for unit in units} == set(
        manifest["candidate_unit_ids"]
    )


def test_hand_adjudication_satisfies_formal_schema_and_identity() -> None:
    schema, manifest, gold = load_calibration_artifacts()

    validate_feedback_calibration_annotations(
        gold, schema=schema, sample_manifest=manifest
    )
    score = score_feedback_calibration_annotations(gold, gold)

    assert score["exact_unit_score"] == {
        "matches": 24,
        "denominator": 24,
        "rate": 1.0,
    }
    assert all(
        field_score["rate"] == 1.0 for field_score in score["field_scores"].values()
    )


def test_annotation_validator_rejects_missing_fixed_unit() -> None:
    schema, manifest, gold = load_calibration_artifacts()
    invalid = copy.deepcopy(gold)
    invalid["annotations"].pop()

    with pytest.raises(
        FeedbackCalibrationValidationError, match="exact sample ID order"
    ):
        validate_feedback_calibration_annotations(
            invalid, schema=schema, sample_manifest=manifest
        )


def test_annotation_validator_rejects_semantic_label_on_excluded_transport() -> None:
    schema, manifest, gold = load_calibration_artifacts()
    invalid = copy.deepcopy(gold)
    transport = invalid["annotations"][1]
    assert transport["candidate_disposition"] == "not_subject_visible"
    transport["next_response_label"] = "retry_unchanged"

    with pytest.raises(
        FeedbackCalibrationValidationError,
        match="excluded candidate has uptake labels",
    ):
        validate_feedback_calibration_annotations(
            invalid, schema=schema, sample_manifest=manifest
        )


def test_annotation_validator_requires_uncertainty_for_indeterminate_label() -> None:
    schema, manifest, gold = load_calibration_artifacts()
    invalid = copy.deepcopy(gold)
    annotation = invalid["annotations"][12]
    assert annotation["next_response_label"] == "indeterminate"
    annotation["uncertainty_reasons"] = []

    with pytest.raises(
        FeedbackCalibrationValidationError,
        match="indeterminate label lacks uncertainty",
    ):
        validate_feedback_calibration_annotations(
            invalid, schema=schema, sample_manifest=manifest
        )


def test_luna_json_parser_accepts_plain_or_fenced_object() -> None:
    assert parse_luna_json_output('{"ok":true}') == {"ok": True}
    assert parse_luna_json_output('```json\n{"ok":true}\n```') == {"ok": True}

    with pytest.raises(ValueError, match="trailing non-JSON text"):
        parse_luna_json_output('{"ok":true}\nextra')


def test_luna_command_exposes_only_fixed_calibration_inputs() -> None:
    command = luna_calibration_command(level="high", annotator_id="test-run")
    joined = " ".join(command)

    assert "openai-codex/gpt-5.6-luna" in joined
    assert "--no-tools" in command
    assert "@sample/units.jsonl" in command
    assert "@annotation-schema.json" in command
    assert "gold-adjudication" not in joined


def test_calibration_gate_accepts_two_exact_repeatable_runs() -> None:
    _, _, gold = load_calibration_artifacts()

    evaluation = evaluate_feedback_calibration_level(
        level="high", gold=gold, runs=[copy.deepcopy(gold), copy.deepcopy(gold)]
    )

    assert evaluation["run_passes"] == [True, True]
    assert evaluation["repeatability_passes"] is True
    assert evaluation["passes"] is True


def test_calibration_selection_blocks_without_fallback_when_all_levels_fail() -> None:
    _, _, gold = load_calibration_artifacts()
    bad_run = copy.deepcopy(gold)
    for annotation in bad_run["annotations"]:
        if annotation["candidate_disposition"] == "negative_feedback":
            annotation["next_response_label"] = "indeterminate"
            annotation["window_outcome"] = "indeterminate"
            annotation["plan_revision"] = "indeterminate"
            annotation["uncertainty_reasons"] = ["ambiguous_relevance"]
    evaluations = [
        evaluate_feedback_calibration_level(
            level=level,
            gold=gold,
            runs=[copy.deepcopy(bad_run), copy.deepcopy(bad_run)],
        )
        for level in CALIBRATION_LEVEL_ORDER
    ]

    selection = select_feedback_calibration_level(evaluations)

    assert selection["selection_status"] == "blocked"
    assert selection["selected_level"] is None
    assert selection["full_population_authorized"] is False
    assert selection["fallback_used"] is False
    assert selection["level_passes"] == {
        level: False for level in CALIBRATION_LEVEL_ORDER
    }
