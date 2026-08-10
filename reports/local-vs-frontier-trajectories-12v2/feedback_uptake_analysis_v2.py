"""Build descriptive feedback-uptake analysis from authorized Luna annotations."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MODEL_ORDER = ("frontier", "agentworld", "thinkingcap")
UPTAKE_FIELDS = (
    "next_response_label",
    "window_outcome",
    "relevant_change_observed",
    "post_change_validation_scope",
    "plan_revision",
)


def sorted_feedback_counter(values: list[str]) -> dict[str, int]:
    """Return a stable lexical count mapping for one annotation field."""
    return dict(sorted(Counter(values).items()))


def feedback_fraction(numerator: int, denominator: int) -> float | None:
    """Return a descriptive rate or None when its denominator is empty."""
    return numerator / denominator if denominator else None


def feedback_trajectory_summary(
    *, trajectory_id: str, rows: list[tuple[dict[str, Any], dict[str, Any]]]
) -> dict[str, Any]:
    """Summarize candidate feedback behavior for one complete model trajectory."""
    first_unit = rows[0][0]
    negative = [
        annotation
        for _, annotation in rows
        if annotation["candidate_disposition"] == "negative_feedback"
    ]
    changed = [
        annotation
        for annotation in negative
        if annotation["relevant_change_observed"] == "yes"
    ]
    validated_changes = [
        annotation
        for annotation in changed
        if annotation["post_change_validation_scope"]
        not in ("none", "not_applicable", "indeterminate")
    ]
    return {
        "trajectory_id": trajectory_id,
        "model_key": first_unit["model_key"],
        "task": first_unit["task"],
        "rep": first_unit["rep"],
        "reward_binary": first_unit["result_outcome"]["reward_binary"],
        "candidate_units": len(rows),
        "negative_feedback": len(negative),
        "recovery_rate": feedback_fraction(
            sum(annotation["window_outcome"] == "recovered" for annotation in negative),
            len(negative),
        ),
        "progress_or_recovery_rate": feedback_fraction(
            sum(
                annotation["window_outcome"] in ("progressed", "recovered")
                for annotation in negative
            ),
            len(negative),
        ),
        "relevant_changes": len(changed),
        "post_change_validation_rate": feedback_fraction(
            len(validated_changes), len(changed)
        ),
    }


def feedback_model_summary(
    *,
    model_key: str,
    rows: list[tuple[dict[str, Any], dict[str, Any]]],
    trajectory_summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize unseen candidate events and equal-weighted trajectories for one model."""
    annotations = [annotation for _, annotation in rows]
    negative = [
        annotation
        for annotation in annotations
        if annotation["candidate_disposition"] == "negative_feedback"
    ]
    changed = [
        annotation
        for annotation in negative
        if annotation["relevant_change_observed"] == "yes"
    ]
    validated_changes = [
        annotation
        for annotation in changed
        if annotation["post_change_validation_scope"]
        not in ("none", "not_applicable", "indeterminate")
    ]
    same_or_broader = [
        annotation
        for annotation in changed
        if annotation["post_change_validation_scope"] in ("same_scope", "broader_scope")
    ]
    schema_invalid = [
        annotation
        for annotation in negative
        if annotation["observation_class"] == "schema_invalid_tool_arguments"
    ]
    model_trajectories = [
        summary for summary in trajectory_summaries if summary["model_key"] == model_key
    ]

    def trajectory_median(field: str) -> float | None:
        values = [
            summary[field]
            for summary in model_trajectories
            if summary[field] is not None
        ]
        return statistics.median(values) if values else None

    return {
        "candidate_units": len(rows),
        "negative_feedback": len(negative),
        "negative_feedback_rate": feedback_fraction(len(negative), len(rows)),
        "candidate_disposition_counts": sorted_feedback_counter(
            [annotation["candidate_disposition"] for annotation in annotations]
        ),
        "observation_class_counts": sorted_feedback_counter(
            [annotation["observation_class"] for annotation in annotations]
        ),
        **{
            f"{field}_counts": sorted_feedback_counter(
                [annotation[field] for annotation in negative]
            )
            for field in UPTAKE_FIELDS
        },
        "recovery_rate": feedback_fraction(
            sum(annotation["window_outcome"] == "recovered" for annotation in negative),
            len(negative),
        ),
        "progress_or_recovery_rate": feedback_fraction(
            sum(
                annotation["window_outcome"] in ("progressed", "recovered")
                for annotation in negative
            ),
            len(negative),
        ),
        "not_recovered_rate": feedback_fraction(
            sum(
                annotation["window_outcome"] == "not_recovered"
                for annotation in negative
            ),
            len(negative),
        ),
        "relevant_change_rate": feedback_fraction(len(changed), len(negative)),
        "post_change_validation_rate": feedback_fraction(
            len(validated_changes), len(changed)
        ),
        "same_or_broader_validation_rate": feedback_fraction(
            len(same_or_broader), len(changed)
        ),
        "no_post_change_validation_rate": feedback_fraction(
            sum(
                annotation["post_change_validation_scope"] == "none"
                for annotation in changed
            ),
            len(changed),
        ),
        "schema_invalid_tool_arguments": len(schema_invalid),
        "schema_invalid_outcome_counts": sorted_feedback_counter(
            [annotation["window_outcome"] for annotation in schema_invalid]
        ),
        "trajectory_count": len(model_trajectories),
        "trajectory_median_candidate_units": trajectory_median("candidate_units"),
        "trajectory_median_recovery_rate": trajectory_median("recovery_rate"),
        "trajectory_median_progress_or_recovery_rate": trajectory_median(
            "progress_or_recovery_rate"
        ),
        "trajectory_median_post_change_validation_rate": trajectory_median(
            "post_change_validation_rate"
        ),
    }


def build_feedback_v2_analysis(
    *,
    candidate_units_path: Path,
    candidate_manifest_path: Path,
    population_ledger_path: Path,
    population_manifest_path: Path,
) -> dict[str, Any]:
    """Build fail-closed feedback-uptake summaries over unseen production cases."""
    candidate_units = [
        json.loads(line) for line in candidate_units_path.read_bytes().splitlines()
    ]
    candidate_manifest = json.loads(candidate_manifest_path.read_text())
    population_manifest = json.loads(population_manifest_path.read_text())
    ledger_bytes = population_ledger_path.read_bytes()
    ledger = [json.loads(line) for line in ledger_bytes.splitlines()]
    if len(candidate_units) != candidate_manifest["candidate_unit_count"]:
        raise ValueError("Feedback analysis v2: candidate manifest count mismatch")
    if [unit["candidate_unit_id"] for unit in candidate_units] != [
        record["candidate_unit_id"] for record in ledger
    ]:
        raise ValueError("Feedback analysis v2: ledger order differs from candidates")
    if (
        hashlib.sha256(ledger_bytes).hexdigest()
        != population_manifest["candidate_ledger_sha256"]
    ):
        raise ValueError("Feedback analysis v2: ledger identity mismatch")

    eligible_rows = []
    excluded_count = 0
    rows_by_trajectory: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = (
        defaultdict(list)
    )
    for unit, record in zip(candidate_units, ledger, strict=True):
        if not record["analysis_eligible"]:
            excluded_count += 1
            continue
        annotation = record["annotation"]
        if annotation["candidate_unit_id"] != unit["candidate_unit_id"]:
            raise ValueError("Feedback analysis v2: annotation candidate mismatch")
        row = (unit, annotation)
        eligible_rows.append(row)
        rows_by_trajectory[unit["trajectory_id"]].append(row)
    if len(eligible_rows) != population_manifest["analysis_eligible_count"]:
        raise ValueError("Feedback analysis v2: eligible count mismatch")
    if excluded_count != population_manifest["calibration_excluded_count"]:
        raise ValueError("Feedback analysis v2: exclusion count mismatch")

    trajectory_summaries = [
        feedback_trajectory_summary(trajectory_id=trajectory_id, rows=rows)
        for trajectory_id, rows in sorted(rows_by_trajectory.items())
    ]
    trajectories_per_model = dict(
        sorted(
            Counter(summary["model_key"] for summary in trajectory_summaries).items()
        )
    )
    models = {
        model_key: feedback_model_summary(
            model_key=model_key,
            rows=[row for row in eligible_rows if row[0]["model_key"] == model_key],
            trajectory_summaries=trajectory_summaries,
        )
        for model_key in MODEL_ORDER
    }

    event_root = candidate_units_path.parent.parent / "events"
    tool_calls_by_model = Counter()
    for event_path in event_root.glob("*/*.json"):
        packet = json.loads(event_path.read_text())
        tool_calls_by_model[packet["model_key"]] += packet["tool_call_count"]
    candidate_density = {
        model_key: {
            "all_candidate_units": candidate_manifest["model_counts"][model_key],
            "tool_calls": tool_calls_by_model[model_key],
            "candidate_units_per_100_tool_calls": 100
            * candidate_manifest["model_counts"][model_key]
            / tool_calls_by_model[model_key],
        }
        for model_key in MODEL_ORDER
    }
    return {
        "analysis_schema_version": 2,
        "scope_note": "Descriptive rates among detector-flagged candidate events. Candidate windows can overlap and are not independent episodes or task-success estimates.",
        "population": {
            "candidate_units": len(candidate_units),
            "analysis_eligible": len(eligible_rows),
            "calibration_excluded": excluded_count,
            "trajectories": len(trajectory_summaries),
            "trajectories_per_model": trajectories_per_model,
        },
        "models": models,
        "candidate_density": candidate_density,
        "trajectory_summaries": trajectory_summaries,
        "provenance": {
            "candidate_set_sha256": candidate_manifest["candidate_set_sha256"],
            "candidate_ledger_sha256": population_manifest["candidate_ledger_sha256"],
            "production_annotation_sha256": population_manifest[
                "production_annotation_sha256"
            ],
            "authorization_sha256": population_manifest["authorization_sha256"],
            "production_model": population_manifest["production_model"],
            "thinking_level": population_manifest["thinking_level"],
        },
    }
