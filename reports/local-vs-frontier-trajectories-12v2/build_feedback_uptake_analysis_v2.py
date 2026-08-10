#!/usr/bin/env python3
"""Write the authorized feedback-uptake v2 analysis dataset."""

from __future__ import annotations

import json
from pathlib import Path

from feedback_uptake_analysis_v2 import build_feedback_v2_analysis

REPORT_ROOT = Path(__file__).resolve().parent
FEEDBACK_ROOT = REPORT_ROOT / "feedback-uptake"
OUTPUT_PATH = FEEDBACK_ROOT / "analysis-v2.json"


def main() -> None:
    """Build and write feedback analysis from immutable candidates and ledger."""
    analysis = build_feedback_v2_analysis(
        candidate_units_path=FEEDBACK_ROOT / "candidates/units.jsonl",
        candidate_manifest_path=FEEDBACK_ROOT / "candidates/manifest.json",
        population_ledger_path=FEEDBACK_ROOT
        / "calibration-v2-repair/population/candidate-ledger.jsonl",
        population_manifest_path=FEEDBACK_ROOT
        / "calibration-v2-repair/population/manifest.json",
    )
    OUTPUT_PATH.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
