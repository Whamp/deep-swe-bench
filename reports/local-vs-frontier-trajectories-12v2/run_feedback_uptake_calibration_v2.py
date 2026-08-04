#!/usr/bin/env python3
"""Calibrate Luna-xhigh and GLM-max for feedback annotation v2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from feedback_uptake_calibration_v2 import (
    FEEDBACK_V2_EXACT_UNIT_MINIMUM_RATE,
    FEEDBACK_V2_FIELD_MINIMUM_RATES,
    FEEDBACK_V2_PRODUCTION_PROTOCOLS,
    evaluate_feedback_v2_production_protocol,
    require_feedback_v2_production_model,
    select_feedback_v2_production_protocol,
    validate_feedback_v2_heldout_annotations,
)

REPORT_ROOT = Path(__file__).resolve().parent
CALIBRATION_V2_ROOT = REPORT_ROOT / "feedback-uptake/calibration-v2"
PI_REAL_EXECUTABLE = Path(
    os.environ.get(
        "PI_REAL_EXECUTABLE",
        "/home/will/.local/share/mise/installs/node/24.16.0/bin/pi",
    )
)


def feedback_v2_model_run_root(
    model: str, *, calibration_root: Path = CALIBRATION_V2_ROOT
) -> Path:
    """Return the isolated output directory for one eligible production model."""
    require_feedback_v2_production_model(model)
    model_slug = re.sub(r"[^a-z0-9._-]+", "-", model.lower()).strip("-")
    return calibration_root / "models" / model_slug


def parse_feedback_v2_json_output(raw_output: str) -> dict[str, Any]:
    """Parse one plain or fenced JSON object from model output."""
    stripped = raw_output.strip()
    if stripped.startswith("```json") and stripped.endswith("```"):
        stripped = stripped[len("```json") : -len("```")].strip()
    elif stripped.startswith("```") and stripped.endswith("```"):
        stripped = stripped[len("```") : -len("```")].strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError(
            "Feedback calibration v2 runner: output contains no JSON object"
        )
    document, end = json.JSONDecoder().raw_decode(stripped[start:])
    if stripped[start + end :].strip():
        raise ValueError(
            "Feedback calibration v2 runner: output contains trailing non-JSON text"
        )
    if not isinstance(document, dict):
        raise TypeError("Feedback calibration v2 runner: output is not an object")
    return document


def feedback_v2_calibration_command(
    *,
    model: str,
    level: str,
    annotator_id: str,
    calibration_root: Path = CALIBRATION_V2_ROOT,
) -> list[str]:
    """Build one blind calibration command with teaching examples but no gold labels."""
    require_feedback_v2_production_model(model)
    if (model, level) not in FEEDBACK_V2_PRODUCTION_PROTOCOLS:
        raise ValueError(
            "Feedback calibration v2 runner: unsupported production model and thinking pair"
        )
    heldout_manifest = json.loads(
        (calibration_root / "heldout/manifest.json").read_text()
    )
    final_request = (
        "Classify the held-out units now. Return JSON only. "
        f"Set annotator_id to {json.dumps(annotator_id)}. "
        f"Set candidate_set_sha256 to {heldout_manifest['candidate_set_sha256']} "
        f"and heldout_sample_sha256 to {heldout_manifest['dataset_sha256']}."
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
        "@annotation-schema.json",
        "@development/manifest.json",
        "@development/units.jsonl",
        "@development/annotations.json",
        "@heldout/manifest.json",
        "@heldout/units.jsonl",
        final_request,
    ]


def run_feedback_v2_calibration_once(
    *,
    model: str,
    level: str,
    run_number: int,
    schema: dict[str, Any],
    heldout_manifest: dict[str, Any],
    force: bool,
    calibration_root: Path = CALIBRATION_V2_ROOT,
) -> dict[str, Any]:
    """Run and validate one independent blind held-out classification."""
    run_root = (
        feedback_v2_model_run_root(model, calibration_root=calibration_root) / level
    )
    run_root.mkdir(parents=True, exist_ok=True)
    output_path = run_root / f"run-{run_number}.json"
    raw_output_path = run_root / f"run-{run_number}.raw.txt"
    if output_path.exists() and not force:
        document = json.loads(output_path.read_text())
        validate_feedback_v2_heldout_annotations(
            document, schema=schema, heldout_manifest=heldout_manifest
        )
        return document

    annotator_id = f"{model}:{level}:feedback-v2:run-{run_number}"
    completed = subprocess.run(
        feedback_v2_calibration_command(
            model=model,
            level=level,
            annotator_id=annotator_id,
            calibration_root=calibration_root,
        ),
        cwd=calibration_root,
        text=True,
        capture_output=True,
        check=False,
    )
    raw_output_path.write_text(completed.stdout)
    if completed.stderr:
        (run_root / f"run-{run_number}.stderr.txt").write_text(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Feedback calibration v2 runner: {model} {level} run {run_number} exited {completed.returncode}"
        )
    document = parse_feedback_v2_json_output(completed.stdout)
    validate_feedback_v2_heldout_annotations(
        document, schema=schema, heldout_manifest=heldout_manifest
    )
    output_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    return document


def feedback_v2_file_sha256(path: Path) -> str:
    """Return the lowercase SHA-256 identity of one calibration input."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_feedback_v2_calibration(
    *, force: bool = False, calibration_root: Path = CALIBRATION_V2_ROOT
) -> dict[str, Any]:
    """Run both eligible protocols twice and write one fail-closed selection receipt."""
    schema_path = calibration_root / "annotation-schema.json"
    instructions_path = calibration_root / "calibration-instructions.md"
    gold_path = calibration_root / "heldout/gold-adjudication.json"
    schema = json.loads(schema_path.read_text())
    heldout_manifest = json.loads(
        (calibration_root / "heldout/manifest.json").read_text()
    )
    gold = json.loads(gold_path.read_text())
    validate_feedback_v2_heldout_annotations(
        gold, schema=schema, heldout_manifest=heldout_manifest
    )

    evaluations = []
    for model, level in FEEDBACK_V2_PRODUCTION_PROTOCOLS:
        runs = [
            run_feedback_v2_calibration_once(
                model=model,
                level=level,
                run_number=run_number,
                schema=schema,
                heldout_manifest=heldout_manifest,
                force=force,
                calibration_root=calibration_root,
            )
            for run_number in (1, 2)
        ]
        evaluation = evaluate_feedback_v2_production_protocol(
            model=model, level=level, gold=gold, runs=runs
        )
        evaluations.append(evaluation)
        model_root = feedback_v2_model_run_root(
            model, calibration_root=calibration_root
        )
        evaluation_document = {
            "evaluation_schema_version": 2,
            "model": model,
            "level": level,
            "candidate_set_sha256": heldout_manifest["candidate_set_sha256"],
            "heldout_sample_sha256": heldout_manifest["dataset_sha256"],
            "development_sample_sha256": json.loads(
                (calibration_root / "development/manifest.json").read_text()
            )["dataset_sha256"],
            "annotation_schema_sha256": feedback_v2_file_sha256(schema_path),
            "calibration_instructions_sha256": feedback_v2_file_sha256(
                instructions_path
            ),
            "gold_adjudication_sha256": feedback_v2_file_sha256(gold_path),
            "runs_per_level": 2,
            "quality_thresholds": {
                "field_minimum_rates": FEEDBACK_V2_FIELD_MINIMUM_RATES,
                "exact_unit_minimum_rate": FEEDBACK_V2_EXACT_UNIT_MINIMUM_RATE,
                "uncertainty_reasons_scored": False,
            },
            "evaluation": evaluation,
        }
        model_root.mkdir(parents=True, exist_ok=True)
        (model_root / "evaluation.json").write_text(
            json.dumps(evaluation_document, ensure_ascii=False, indent=2) + "\n"
        )

    selection = select_feedback_v2_production_protocol(
        evaluations,
        heldout_sample_sha256=heldout_manifest["dataset_sha256"],
        annotation_schema_sha256=feedback_v2_file_sha256(schema_path),
        calibration_instructions_sha256=feedback_v2_file_sha256(instructions_path),
    )
    selection_document = {
        **selection,
        "protocol_passes": {
            f"{evaluation['model']}:{evaluation['level']}": evaluation["passes"]
            for evaluation in evaluations
        },
        "gold_adjudication_sha256": feedback_v2_file_sha256(gold_path),
    }
    (calibration_root / "selection.json").write_text(
        json.dumps(selection_document, ensure_ascii=False, indent=2) + "\n"
    )
    (calibration_root / "authorization.json").write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + "\n"
    )
    return selection


def main() -> None:
    """Run the two declared production calibrations and print authorization."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--calibration-root",
        type=Path,
        default=CALIBRATION_V2_ROOT,
    )
    arguments = parser.parse_args()
    print(
        json.dumps(
            run_feedback_v2_calibration(
                force=arguments.force,
                calibration_root=arguments.calibration_root.resolve(),
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
