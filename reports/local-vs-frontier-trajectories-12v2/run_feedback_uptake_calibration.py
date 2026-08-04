#!/usr/bin/env python3
"""Run fixed-schema feedback calibrations and gate full-population annotation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
DEFAULT_CALIBRATION_MODEL = "openai-codex/gpt-5.6-luna"
DEFAULT_CALIBRATION_LEVELS = CALIBRATION_LEVEL_ORDER
CANDIDATE_SET_SHA256 = (
    "e6089bcdf90ec249cab3817c9a4da8cc25217f6bb3cb99f345ac5f774909d73d"
)
CALIBRATION_SAMPLE_SHA256 = (
    "42ebc337026bbfdba1b132539a2815ca9eee4fb5b7f2760cb1d5f279ee28cd95"
)


def calibration_model_run_root(model: str) -> Path:
    """Return an isolated artifact root while retaining the original Luna paths."""
    if model == DEFAULT_CALIBRATION_MODEL:
        return CALIBRATION_ROOT / "runs"
    model_slug = re.sub(r"[^a-z0-9._-]+", "-", model.lower()).strip("-")
    if not model_slug:
        raise ValueError("Feedback calibration runner: model name has no safe path")
    return CALIBRATION_ROOT / "models" / model_slug


def parse_calibration_json_output(raw_output: str) -> dict[str, Any]:
    """Parse one JSON object from plain or fenced model output."""
    stripped = raw_output.strip()
    if stripped.startswith("```json") and stripped.endswith("```"):
        stripped = stripped[len("```json") : -len("```")].strip()
    elif stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[len("```") : -len("```")].strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError(
            "Feedback calibration runner: model output contains no JSON object"
        )
    document, end = json.JSONDecoder().raw_decode(stripped[start:])
    trailing = stripped[start + end :].strip()
    if trailing:
        raise ValueError(
            "Feedback calibration runner: model output contains trailing non-JSON text"
        )
    if not isinstance(document, dict):
        raise TypeError("Feedback calibration runner: model output is not an object")
    return document


def calibration_command(*, model: str, level: str, annotator_id: str) -> list[str]:
    """Build one isolated noninteractive fixed-sample calibration command."""
    final_request = (
        "Classify the attached fixed sample now. Return JSON only. "
        f"Set annotator_id to {json.dumps(annotator_id)}. "
        f"Set candidate_set_sha256 to {CANDIDATE_SET_SHA256} "
        f"and calibration_sample_sha256 to {CALIBRATION_SAMPLE_SHA256}."
    )
    return [
        "pi",
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
        "You classify fixed evidence units under a supplied JSON schema. Follow the attached instructions exactly and return JSON only.",
        "@calibration-instructions.md",
        "@annotation-schema.json",
        "@sample/manifest.json",
        "@sample/units.jsonl",
        final_request,
    ]


def run_model_calibration_once(
    *,
    model: str,
    level: str,
    run_number: int,
    run_root: Path,
    schema: dict[str, Any],
    sample_manifest: dict[str, Any],
    force: bool,
) -> dict[str, Any]:
    """Run and validate one independent fixed-sample annotation."""
    level_root = run_root / level
    level_root.mkdir(parents=True, exist_ok=True)
    output_path = level_root / f"run-{run_number}.json"
    raw_output_path = level_root / f"run-{run_number}.raw.txt"
    if output_path.exists() and not force:
        document = json.loads(output_path.read_text())
        validate_feedback_calibration_annotations(
            document, schema=schema, sample_manifest=sample_manifest
        )
        return document

    annotator_id = f"{model}:{level}:run-{run_number}"
    completed = subprocess.run(
        calibration_command(model=model, level=level, annotator_id=annotator_id),
        cwd=CALIBRATION_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    raw_output_path.write_text(completed.stdout)
    if completed.returncode != 0:
        (level_root / f"run-{run_number}.stderr.txt").write_text(completed.stderr)
        raise RuntimeError(
            f"Feedback calibration runner: {model} {level} run {run_number} exited {completed.returncode}"
        )
    document = parse_calibration_json_output(completed.stdout)
    validate_feedback_calibration_annotations(
        document, schema=schema, sample_manifest=sample_manifest
    )
    output_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    return document


def write_feedback_calibration_evaluation(
    *,
    model: str,
    levels: tuple[str, ...],
    run_root: Path,
    evaluations: list[dict[str, Any]],
    selection: dict[str, Any],
) -> None:
    """Write complete per-level scores and the fail-closed selection decision."""
    evaluation_document = {
        "evaluation_schema_version": 1,
        "model": model,
        "candidate_set_sha256": CANDIDATE_SET_SHA256,
        "calibration_sample_sha256": CALIBRATION_SAMPLE_SHA256,
        "calibration_instructions_sha256": hashlib.sha256(
            (CALIBRATION_ROOT / "calibration-instructions.md").read_bytes()
        ).hexdigest(),
        "annotation_schema_sha256": hashlib.sha256(
            (CALIBRATION_ROOT / "annotation-schema.json").read_bytes()
        ).hexdigest(),
        "supported_levels": list(levels),
        "runs_per_level": 2,
        "quality_thresholds": {
            "field_minimum_rates": CALIBRATION_FIELD_MINIMUM_RATES,
            "exact_unit_minimum_rate": CALIBRATION_EXACT_UNIT_MINIMUM_RATE,
            "uncertainty_minimum_rate": CALIBRATION_UNCERTAINTY_MINIMUM_RATE,
        },
        "level_evaluations": evaluations,
    }
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "evaluation.json").write_text(
        json.dumps(evaluation_document, ensure_ascii=False, indent=2) + "\n"
    )
    (run_root / "selection.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n"
    )


def run_feedback_calibration(
    *,
    model: str = DEFAULT_CALIBRATION_MODEL,
    levels: tuple[str, ...] = DEFAULT_CALIBRATION_LEVELS,
    force: bool = False,
) -> dict[str, Any]:
    """Run each supported level twice and apply the shared fail-closed gate."""
    if not levels or len(levels) != len(set(levels)):
        raise ValueError(
            "Feedback calibration runner: levels must be nonempty and unique"
        )
    unknown_levels = set(levels) - set(CALIBRATION_LEVEL_ORDER)
    if unknown_levels:
        raise ValueError(
            f"Feedback calibration runner: unsupported levels {sorted(unknown_levels)}"
        )

    run_root = calibration_model_run_root(model)
    schema = json.loads((CALIBRATION_ROOT / "annotation-schema.json").read_text())
    sample_manifest = json.loads(
        (CALIBRATION_ROOT / "sample/manifest.json").read_text()
    )
    gold = json.loads((CALIBRATION_ROOT / "gold-adjudication.json").read_text())
    validate_feedback_calibration_annotations(
        gold, schema=schema, sample_manifest=sample_manifest
    )
    evaluations = []
    for level in levels:
        runs = [
            run_model_calibration_once(
                model=model,
                level=level,
                run_number=run_number,
                run_root=run_root,
                schema=schema,
                sample_manifest=sample_manifest,
                force=force,
            )
            for run_number in (1, 2)
        ]
        evaluations.append(
            evaluate_feedback_calibration_level(level=level, gold=gold, runs=runs)
        )
    selection = select_feedback_calibration_level(
        evaluations, level_order=levels, model_name=model
    )
    write_feedback_calibration_evaluation(
        model=model,
        levels=levels,
        run_root=run_root,
        evaluations=evaluations,
        selection=selection,
    )
    return selection


def parse_feedback_calibration_arguments() -> argparse.Namespace:
    """Parse model, supported reasoning levels, and overwrite behavior."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_CALIBRATION_MODEL)
    parser.add_argument(
        "--levels",
        nargs="+",
        choices=CALIBRATION_LEVEL_ORDER,
        default=list(DEFAULT_CALIBRATION_LEVELS),
    )
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run fixed calibration and print the fail-closed selection result."""
    arguments = parse_feedback_calibration_arguments()
    selection = run_feedback_calibration(
        model=arguments.model,
        levels=tuple(arguments.levels),
        force=arguments.force,
    )
    print(json.dumps(selection, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
