from pathlib import Path

from feedback_uptake_analysis_v2 import build_feedback_v2_analysis

REPORT_ROOT = Path(__file__).parent
FEEDBACK_ROOT = REPORT_ROOT / "feedback-uptake"


def test_feedback_v2_analysis_uses_all_trajectories_and_only_unseen_candidates() -> (
    None
):
    analysis = build_feedback_v2_analysis(
        candidate_units_path=FEEDBACK_ROOT / "candidates/units.jsonl",
        candidate_manifest_path=FEEDBACK_ROOT / "candidates/manifest.json",
        population_ledger_path=FEEDBACK_ROOT
        / "calibration-v2-repair/population/candidate-ledger.jsonl",
        population_manifest_path=FEEDBACK_ROOT
        / "calibration-v2-repair/population/manifest.json",
    )

    assert analysis["population"] == {
        "candidate_units": 1237,
        "analysis_eligible": 1165,
        "calibration_excluded": 72,
        "trajectories": 108,
        "trajectories_per_model": {
            "agentworld": 36,
            "frontier": 36,
            "thinkingcap": 36,
        },
    }
    assert {
        model: summary["candidate_units"]
        for model, summary in analysis["models"].items()
    } == {"frontier": 210, "agentworld": 446, "thinkingcap": 509}
    assert {
        model: summary["negative_feedback"]
        for model, summary in analysis["models"].items()
    } == {"frontier": 204, "agentworld": 443, "thinkingcap": 503}
    assert {
        model: summary["window_outcome_counts"]
        for model, summary in analysis["models"].items()
    } == {
        "frontier": {"not_recovered": 14, "progressed": 100, "recovered": 90},
        "agentworld": {"not_recovered": 14, "progressed": 259, "recovered": 170},
        "thinkingcap": {"not_recovered": 16, "progressed": 322, "recovered": 165},
    }
