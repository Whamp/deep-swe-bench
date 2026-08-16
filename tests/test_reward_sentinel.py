"""Unverified-reward sentinel semantics.

A cell whose verifier never produced reward.json (empty patch, verifier
timeout, degeneration watchdog) must record reward_binary 0 — never -1 —
plus reward_unverified: true, so naive score averaging cannot be dragged
below an honest zero. Verifier-emitted grades flow through unchanged with
reward_unverified: false.
"""

from pathlib import Path

from harness.lib import read_reward, reward_grade_fields


def test_read_reward_missing_reward_json_scores_zero_unverified(tmp_path: Path) -> None:
    grade = read_reward(tmp_path)

    assert grade["reward"] == 0
    assert grade["partial"] == 0.0
    assert grade["unverified"] is True
    assert grade.get("_missing") is True


def test_read_reward_crash_sentinel_scores_zero_unverified(tmp_path: Path) -> None:
    (tmp_path / "reward.txt").write_text("test.sh: crash sentinel\n")

    grade = read_reward(tmp_path)

    assert grade["reward"] == 0
    assert grade["partial"] == 0.0
    assert grade["unverified"] is True
    assert grade["_sentinel"] == "test.sh: crash sentinel"


def test_read_reward_verifier_reward_json_flows_through_unchanged(
    tmp_path: Path,
) -> None:
    (tmp_path / "reward.json").write_text(
        '{"reward": 1, "partial": 0.92, "f2p": 0.9, "p2p": 1.0}'
    )

    grade = read_reward(tmp_path)

    assert grade == {"reward": 1, "partial": 0.92, "f2p": 0.9, "p2p": 1.0}
    assert "unverified" not in grade


def test_reward_grade_fields_marks_unverified_reward() -> None:
    fields = reward_grade_fields({"reward": 0, "partial": 0.0, "unverified": True})

    assert fields == {
        "reward_binary": 0,
        "reward_partial": 0.0,
        "reward_unverified": True,
    }


def test_reward_grade_fields_verifier_grade_is_verified() -> None:
    fields = reward_grade_fields({"reward": 1, "partial": 0.92})

    assert fields == {
        "reward_binary": 1,
        "reward_partial": 0.92,
        "reward_unverified": False,
    }


def test_reward_grade_fields_defaults_are_zero_not_negative() -> None:
    fields = reward_grade_fields({})

    assert fields == {
        "reward_binary": 0,
        "reward_partial": 0.0,
        "reward_unverified": True,
    }
