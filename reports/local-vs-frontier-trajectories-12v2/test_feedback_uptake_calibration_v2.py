import copy
import json
from pathlib import Path

import pytest

from build_feedback_uptake_calibration_v2 import feedback_v2_generated_artifacts
from feedback_uptake_calibration_v2 import (
    FeedbackCalibrationV2ValidationError,
    evaluate_feedback_v2_production_protocol,
    require_feedback_v2_production_model,
    score_feedback_v2_annotations,
    select_feedback_v2_heldout_units,
    select_feedback_v2_production_protocol,
    validate_feedback_v2_annotation_semantics,
    validate_feedback_v2_dataset_split,
    validate_feedback_v2_development_annotations,
    validate_feedback_v2_heldout_annotations,
    validate_feedback_v2_population_authorization,
)
from run_feedback_uptake_calibration_v2 import (
    feedback_v2_calibration_command,
    feedback_v2_model_run_root,
)
from run_feedback_uptake_population_v2 import (
    feedback_v2_population_command,
    partition_feedback_v2_population_units,
    repair_feedback_v2_batch_annotation_order,
    repair_feedback_v2_batch_identity,
)

REPORT_ROOT = Path(__file__).parent
CALIBRATION_V1_ROOT = REPORT_ROOT / "feedback-uptake/calibration"
CALIBRATION_V2_ROOT = REPORT_ROOT / "feedback-uptake/calibration-v2"


def negative_feedback_annotation() -> dict:
    return {
        "candidate_disposition": "negative_feedback",
        "observation_class": "schema_invalid_tool_arguments",
        "action_purpose": "delivery_or_tool_mechanics",
        "next_response_label": "corrective_change",
        "window_outcome": "recovered",
        "relevant_change_observed": "yes",
        "post_change_validation_scope": "none",
        "plan_revision": "local_adjustment",
        "confidence": "high",
        "uncertainty_reasons": [],
    }


def test_feedback_v2_production_model_must_be_luna_or_glm() -> None:
    assert (
        require_feedback_v2_production_model("openai-codex/gpt-5.6-luna")
        == "openai-codex/gpt-5.6-luna"
    )
    assert require_feedback_v2_production_model("zai/glm-5.2") == "zai/glm-5.2"

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="production model must be GPT-5.6 Luna or GLM-5.2",
    ):
        require_feedback_v2_production_model("openai-codex/gpt-5.6-sol")


def test_feedback_v2_validation_scope_requires_an_observed_change() -> None:
    annotation = negative_feedback_annotation()
    validate_feedback_v2_annotation_semantics(annotation)

    no_change = annotation | {
        "relevant_change_observed": "no",
        "post_change_validation_scope": "not_applicable",
    }
    validate_feedback_v2_annotation_semantics(no_change)

    invalid = no_change | {"post_change_validation_scope": "same_scope"}
    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="post-change validation is not applicable without a relevant change",
    ):
        validate_feedback_v2_annotation_semantics(invalid)


def test_feedback_v2_observed_change_requires_validation_label() -> None:
    invalid = negative_feedback_annotation() | {
        "post_change_validation_scope": "not_applicable"
    }

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="observed change requires a post-change validation label",
    ):
        validate_feedback_v2_annotation_semantics(invalid)


def test_feedback_v2_uncertainty_is_required_but_not_exact_wording() -> None:
    uncertain = negative_feedback_annotation() | {
        "window_outcome": "indeterminate",
        "confidence": "medium",
        "uncertainty_reasons": ["context_window_censored"],
    }
    validate_feedback_v2_annotation_semantics(uncertain)
    validate_feedback_v2_annotation_semantics(
        uncertain | {"uncertainty_reasons": ["ambiguous_relevance"]}
    )

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="uncertain annotation requires at least one reason",
    ):
        validate_feedback_v2_annotation_semantics(
            uncertain | {"uncertainty_reasons": []}
        )


def test_feedback_v2_high_confidence_has_no_uncertainty_reasons() -> None:
    invalid = negative_feedback_annotation() | {
        "uncertainty_reasons": ["ambiguous_scope"]
    }

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="high confidence cannot include uncertainty reasons",
    ):
        validate_feedback_v2_annotation_semantics(invalid)


def test_feedback_v2_nonnegative_candidates_have_no_uptake_labels() -> None:
    excluded = negative_feedback_annotation() | {
        "candidate_disposition": "not_subject_visible",
        "next_response_label": "not_applicable",
        "window_outcome": "not_applicable",
        "relevant_change_observed": "not_applicable",
        "post_change_validation_scope": "not_applicable",
        "plan_revision": "not_applicable",
    }
    validate_feedback_v2_annotation_semantics(excluded)

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="nonnegative candidate has feedback-uptake labels",
    ):
        validate_feedback_v2_annotation_semantics(
            excluded | {"window_outcome": "recovered"}
        )


def test_feedback_v2_indeterminate_change_has_indeterminate_validation_scope() -> None:
    uncertain = negative_feedback_annotation() | {
        "relevant_change_observed": "indeterminate",
        "post_change_validation_scope": "indeterminate",
        "confidence": "medium",
        "uncertainty_reasons": ["context_window_censored"],
    }
    validate_feedback_v2_annotation_semantics(uncertain)

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="indeterminate change requires indeterminate validation scope",
    ):
        validate_feedback_v2_annotation_semantics(
            uncertain | {"post_change_validation_scope": "none"}
        )


def test_feedback_v2_development_and_heldout_cases_are_disjoint() -> None:
    validate_feedback_v2_dataset_split(
        development_ids=["dev-a", "dev-b"],
        heldout_ids=["test-a", "test-b"],
        retired_v1_ids=["old-a", "old-b"],
    )

    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="development and held-out cases overlap",
    ):
        validate_feedback_v2_dataset_split(
            development_ids=["shared"],
            heldout_ids=["shared"],
            retired_v1_ids=[],
        )


def test_feedback_v2_heldout_cases_do_not_reuse_v1_calibration() -> None:
    with pytest.raises(
        FeedbackCalibrationV2ValidationError,
        match="held-out cases reuse v1 calibration",
    ):
        validate_feedback_v2_dataset_split(
            development_ids=[],
            heldout_ids=["old-a"],
            retired_v1_ids=["old-a"],
        )


def test_feedback_v2_heldout_selection_uses_fixed_hash_order() -> None:
    def unit(candidate_id: str, *, signal: str = "reported_tool_error") -> dict:
        return {
            "candidate_unit_id": candidate_id,
            "model_key": "agentworld",
            "task": "task-a",
            "focal_event": {"candidate_signal_types": [signal]},
        }

    selected = select_feedback_v2_heldout_units(
        candidate_units=[unit("a"), unit("b"), unit("excluded")],
        strata=[
            {
                "model_key": "agentworld",
                "task": "task-a",
                "candidate_signal_type": "reported_tool_error",
            }
        ],
        excluded_ids={"excluded"},
    )

    assert [candidate["candidate_unit_id"] for candidate in selected] == ["b"]


def test_feedback_v2_generated_datasets_match_source_artifacts() -> None:
    for path, expected_bytes in feedback_v2_generated_artifacts().items():
        assert path.read_bytes() == expected_bytes

    development = json.loads(
        (CALIBRATION_V2_ROOT / "development/manifest.json").read_text()
    )
    heldout = json.loads((CALIBRATION_V2_ROOT / "heldout/manifest.json").read_text())
    retired_v1 = json.loads((CALIBRATION_V1_ROOT / "sample-selection.json").read_text())
    assert development["candidate_unit_count"] == 12
    assert heldout["candidate_unit_count"] == 24
    assert heldout["model_counts"] == {
        "agentworld": 8,
        "frontier": 8,
        "thinkingcap": 8,
    }
    assert len(heldout["tasks"]) == 12
    validate_feedback_v2_dataset_split(
        development_ids=development["candidate_unit_ids"],
        heldout_ids=heldout["candidate_unit_ids"],
        retired_v1_ids=retired_v1["candidate_unit_ids"],
    )


def test_feedback_v2_development_annotations_match_teaching_cases() -> None:
    schema = json.loads((CALIBRATION_V2_ROOT / "annotation-schema.json").read_text())
    manifest = json.loads(
        (CALIBRATION_V2_ROOT / "development/manifest.json").read_text()
    )
    examples = json.loads(
        (CALIBRATION_V2_ROOT / "development/annotations.json").read_text()
    )

    validate_feedback_v2_development_annotations(
        examples, schema=schema, development_manifest=manifest
    )


def test_feedback_v2_final_gold_matches_fresh_heldout_sample() -> None:
    schema = json.loads((CALIBRATION_V2_ROOT / "annotation-schema.json").read_text())
    manifest = json.loads((CALIBRATION_V2_ROOT / "heldout/manifest.json").read_text())
    gold = json.loads(
        (CALIBRATION_V2_ROOT / "heldout/gold-adjudication.json").read_text()
    )

    validate_feedback_v2_heldout_annotations(
        gold, schema=schema, heldout_manifest=manifest
    )


def load_feedback_v2_gold() -> dict:
    return json.loads(
        (CALIBRATION_V2_ROOT / "heldout/gold-adjudication.json").read_text()
    )


def test_feedback_v2_score_does_not_require_exact_uncertainty_wording() -> None:
    gold = load_feedback_v2_gold()
    prediction = copy.deepcopy(gold)
    uncertain = next(
        annotation
        for annotation in prediction["annotations"]
        if annotation["uncertainty_reasons"]
    )
    uncertain["uncertainty_reasons"] = ["ambiguous_scope"]

    score = score_feedback_v2_annotations(gold, prediction)

    assert score["exact_unit_score"]["matches"] == 24
    assert "uncertainty_reason_score" not in score


def test_feedback_v2_protocol_requires_two_accurate_repeatable_runs() -> None:
    gold = load_feedback_v2_gold()
    evaluation = evaluate_feedback_v2_production_protocol(
        model="openai-codex/gpt-5.6-luna",
        level="xhigh",
        gold=gold,
        runs=[copy.deepcopy(gold), copy.deepcopy(gold)],
    )

    assert evaluation["run_passes"] == [True, True]
    assert evaluation["repeatability_passes"] is True
    assert evaluation["passes"] is True


def test_feedback_v2_selection_prefers_luna_then_glm_without_sol_fallback() -> None:
    gold = load_feedback_v2_gold()
    luna = evaluate_feedback_v2_production_protocol(
        model="openai-codex/gpt-5.6-luna",
        level="xhigh",
        gold=gold,
        runs=[copy.deepcopy(gold), copy.deepcopy(gold)],
    )
    glm = evaluate_feedback_v2_production_protocol(
        model="zai/glm-5.2",
        level="max",
        gold=gold,
        runs=[copy.deepcopy(gold), copy.deepcopy(gold)],
    )

    selection = select_feedback_v2_production_protocol(
        [luna, glm],
        heldout_sample_sha256="a" * 64,
        annotation_schema_sha256="b" * 64,
        calibration_instructions_sha256="c" * 64,
    )

    assert selection["production_model"] == "openai-codex/gpt-5.6-luna"
    assert selection["selected_level"] == "xhigh"
    assert selection["full_population_authorized"] is True
    assert "gpt-5.6-sol" not in json.dumps(selection)


def test_feedback_v2_calibration_command_teaches_without_leaking_gold() -> None:
    command = feedback_v2_calibration_command(
        model="openai-codex/gpt-5.6-luna",
        level="xhigh",
        annotator_id="test-run",
    )
    joined = " ".join(command)

    assert "@development/units.jsonl" in command
    assert "@development/annotations.json" in command
    assert "@heldout/units.jsonl" in command
    assert "gold-adjudication" not in joined
    assert "gpt-5.6-sol" not in joined
    assert "--no-tools" in command


def test_feedback_v2_model_outputs_use_separate_roots() -> None:
    assert feedback_v2_model_run_root("openai-codex/gpt-5.6-luna") == (
        CALIBRATION_V2_ROOT / "models/openai-codex-gpt-5.6-luna"
    )
    assert feedback_v2_model_run_root("zai/glm-5.2") == (
        CALIBRATION_V2_ROOT / "models/zai-glm-5.2"
    )


def test_feedback_v2_population_batches_cover_each_unit_once() -> None:
    units = [{"candidate_unit_id": f"unit-{index}"} for index in range(1165)]

    batches = partition_feedback_v2_population_units(units, batch_count=50)

    assert len(batches) == 50
    assert {len(batch) for batch in batches} == {23, 24}
    assert [unit for batch in batches for unit in batch] == units


def test_feedback_v2_batch_order_repairs_only_exact_permutations() -> None:
    manifest = {"candidate_unit_ids": ["unit-a", "unit-b"]}
    document = {
        "annotations": [
            {"candidate_unit_id": "unit-b"},
            {"candidate_unit_id": "unit-a"},
        ]
    }

    repaired = repair_feedback_v2_batch_annotation_order(
        document, batch_manifest=manifest
    )

    assert [item["candidate_unit_id"] for item in repaired["annotations"]] == [
        "unit-a",
        "unit-b",
    ]
    with pytest.raises(FeedbackCalibrationV2ValidationError):
        repair_feedback_v2_batch_annotation_order(
            {"annotations": [{"candidate_unit_id": "unit-a"}]},
            batch_manifest=manifest,
        )


def test_feedback_v2_batch_identity_repairs_only_one_character_truncation() -> None:
    expected = "a" * 64
    manifest = {
        "dataset_sha256": expected,
        "candidate_unit_ids": ["unit-a", "unit-b"],
    }
    document = {
        "heldout_sample_sha256": "a" * 63,
        "annotations": [
            {"candidate_unit_id": "unit-a"},
            {"candidate_unit_id": "unit-b"},
        ],
    }

    repaired = repair_feedback_v2_batch_identity(document, batch_manifest=manifest)

    assert repaired["heldout_sample_sha256"] == expected
    with pytest.raises(FeedbackCalibrationV2ValidationError):
        repair_feedback_v2_batch_identity(
            document | {"heldout_sample_sha256": "b" * 63},
            batch_manifest=manifest,
        )


def test_feedback_v2_population_command_contains_no_calibration_answers() -> None:
    command = feedback_v2_population_command(
        model="openai-codex/gpt-5.6-luna",
        level="xhigh",
        annotator_id="population-test",
        batch_relative_root=Path("population/batches/batch-001"),
        batch_sample_sha256="d" * 64,
    )
    joined = " ".join(str(part) for part in command)

    assert "@development/annotations.json" in command
    assert "@population/batches/batch-001/units.jsonl" in command
    assert "gold-adjudication" not in joined
    assert "independent-review" not in joined


def feedback_v2_authorization() -> dict:
    return {
        "authorization_schema_version": 2,
        "production_model": "openai-codex/gpt-5.6-luna",
        "selected_level": "xhigh",
        "heldout_sample_sha256": "a" * 64,
        "annotation_schema_sha256": "b" * 64,
        "calibration_instructions_sha256": "c" * 64,
        "runs_per_level": 2,
        "selection_status": "passed",
        "full_population_authorized": True,
        "fallback_used": False,
    }


def test_feedback_v2_population_requires_passing_luna_or_glm_authorization() -> None:
    validate_feedback_v2_population_authorization(
        feedback_v2_authorization(),
        heldout_sample_sha256="a" * 64,
        annotation_schema_sha256="b" * 64,
        calibration_instructions_sha256="c" * 64,
    )

    for invalid in (
        feedback_v2_authorization() | {"production_model": "openai-codex/gpt-5.6-sol"},
        feedback_v2_authorization() | {"full_population_authorized": False},
        feedback_v2_authorization() | {"runs_per_level": 1},
        feedback_v2_authorization() | {"heldout_sample_sha256": "d" * 64},
    ):
        with pytest.raises(FeedbackCalibrationV2ValidationError):
            validate_feedback_v2_population_authorization(
                invalid,
                heldout_sample_sha256="a" * 64,
                annotation_schema_sha256="b" * 64,
                calibration_instructions_sha256="c" * 64,
            )
