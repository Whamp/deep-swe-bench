#!/usr/bin/env python3
"""Run two fixed-schema Luna calibrations per reasoning level and gate fan-out."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from feedback_uptake_calibration import (
    CALIBRATION_EXACT_UNIT_MINIMUM_RATE,
    CALIBRATION_FIELD_MINIMUM_RATES,
    CALIBRATION_LEVEL_ORDER,
    CALIBRATION_UNCERTAINTY_MINIMUM_RATE,
    evaluate_feedback_calibration_level,
    select_feedback_calibration_level,
    validate_feedback_calibration_annotations,
)

REPORT_ROOT = Path(__file__).resolve().parent
CALIBRATION_ROOT = REPORT_ROOT / "feedback-uptake/calibration"
CALIBRATION_RUN_ROOT = CALIBRATION_ROOT / "runs"
LUNA_MODEL = "openai-codex/gpt-5.6-luna"


def parse_luna_json_output(raw_output: str) -> dict[str, Any]:
    """Parse one JSON object from plain or fenced model output and reject trailing prose."""
    stripped = raw_output.strip()
    if stripped.startswith("```json") and stripped.endswith("```"):
        stripped = stripped[len("```json") : -len("```")].strip()
    elif stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[len("```") : -len("```")].strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError(
            "Feedback calibration runner: Luna output contains no JSON object"
        )
    document, end = json.JSONDecoder().raw_decode(stripped[start:])
    trailing = stripped[start + end :].strip()
    if trailing:
        raise ValueError(
            "Feedback calibration runner: Luna output contains trailing non-JSON text"
        )
    if not isinstance(document, dict):
        raise TypeError("Feedback calibration runner: Luna output is not an object")
    return document


def luna_calibration_command(*, level: str, annotator_id: str) -> list[str]:
    """Build one isolated noninteractive Luna calibration command."""
    final_request = (
        "Classify the attached fixed sample now. Return JSON only. "
        f"Set annotator_id to {json.dumps(annotator_id)}. "
        "Set candidate_set_sha256 to "
        "e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d "
        "and calibration_sample_sha256 to "
        "42ebc337026bbfdba1b132539a2815ca9eee4fb5b7f2760cb1d5f279ee28cd95."
    )
    return [
        "pi",
        "--model",
        LUNA_MODEL,
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
        "You classify fixed evidence units under a supplied JSON schema. Follow the attached instructions exactly and return JSON only.",
        "@calibration-instructions.md",
        "@annotation-schema.json",
        "@sample/manifest.json",
        "@sample/units.jsonl",
        final_request,
    ]


def run_luna_calibration_once(
    *,
    level: str,
    run_number: int,
    schema: dict[str, Any],
    sample_manifest: dict[str, Any],
    force: bool,
) -> dict[str, Any]:
    """Run and validate one independent Luna fixed-sample annotation."""
    run_root = CALIBRATION_RUN_ROOT / level
    run_root.mkdir(parents=True, exist_ok=True)
    output_path = run_root / f"run-{run_number}.json"
    raw_output_path = run_root / f"run-{run_number}.raw.txt"
    if output_path.exists() and not force:
        document = json.loads(output_path.read_text())
        validate_feedback_calibration_annotations(
            document, schema=schema, sample_manifest=sample_manifest
        )
        return document

    annotator_id = f"{LUNA_MODEL}:{level}:run-{run_number}"
    completed = subprocess.run(
        luna_calibration_command(level=level, annotator_id=annotator_id),
        cwd=CALIBRATION_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    raw_output_path.write_text(completed.stdout)
    if completed.returncode != 0:
        (run_root / f"run-{run_number}.stderr.txt").write_text(completed.stderr)
        raise RuntimeError(
            f"Feedback calibration runner: Luna {level} run {run_number} exited {completed.returncode}"
        )
    document = parse_luna_json_output(completed.stdout)
    validate_feedback_calibration_annotations(
        document, schema=schema, sample_manifest=sample_manifest
    )
    output_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    return document


def write_feedback_calibration_evaluation(
    *,
    evaluations: list[dict[str, Any]],
    selection: dict[str, Any],
) -> None:
    """Write complete per-level scores and the fail-closed selection decision."""
    evaluation_document = {
        "evaluation_schema_version": 1,
        "model": LUNA_MODEL,
        "candidate_set_sha256": "e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d",
        "calibration_sample_sha256": "42ebc337026bbfdba1b132539a2815ca9eee4fb5b7f2760cb1d5f279ee28cd95",
        "calibration_instructions_sha256": hashlib.sha256(
            (CALIBRATION_ROOT / "calibration-instructions.md").read_bytes()
        ).hexdigest(),
        "annotation_schema_sha256": hashlib.sha256(
            (CALIBRATION_ROOT / "annotation-schema.json").read_bytes()
        ).hexdigest(),
        "runs_per_level": 2,
        "quality_thresholds": {
            "field_minimum_rates": CALIBRATION_FIELD_MINIMUM_RATES,
            "exact_unit_minimum_rate": CALIBRATION_EXACT_UNIT_MINIMUM_RATE,
            "uncertainty_minimum_rate": CALIBRATION_UNCERTAINTY_MINIMUM_RATE,
        },
        "level_evaluations": evaluations,
    }
    CALIBRATION_RUN_ROOT.mkdir(parents=True, exist_ok=True)
    (CALIBRATION_RUN_ROOT / "evaluation.json").write_text(
        json.dumps(evaluation_document, ensure_ascii=False, indent=2) + "\n"
    )
    (CALIBRATION_RUN_ROOT / "selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n"
    )


def run_feedback_calibration(*, force: bool = False) -> dict[str, Any]:
    """Run every Luna level twice, score gold accuracy/repeatability, and select."""
    schema = json.loads((CALIBRATION_ROOT / "annotation-schema.json").read_text())
    sample_manifest = json.loads(
        (CALIBRATION_ROOT / "sample/manifest.json").read_text()
    )
    gold = json.loads((CALIBRATION_ROOT / "gold-adjudication.json").read_text())
    validate_feedback_calibration_annotations(
        gold, schema=schema, sample_manifest=sample_manifest
    )
    evaluations = []
    for level in CALIBRATION_LEVEL_ORDER:
        runs = [
            run_luna_calibration_once(
                level=level,
                run_number=run_number,
                schema=schema,
                sample_manifest=sample_manifest,
                force=force,
            )
            for run_number in (1, 2)
        ]
        evaluations.append(
            evaluate_feedback_calibration_level(level=level, gold=gold, runs=runs)
        )
    selection = select_feedback_calibration_level(evaluations)
    write_feedback_calibration_evaluation(evaluations=evaluations, selection=selection)
    return selection


def parse_feedback_calibration_arguments() -> argparse.Namespace:
    """Parse whether existing validated Luna outputs may be overwritten."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run fixed calibration and print the fail-closed selection result."""
    arguments = parse_feedback_calibration_arguments()
    selection = run_feedback_calibration(force=arguments.force)
    print(json.dumps(selection, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
