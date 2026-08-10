from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("build_read_long_lines_report.py")
SPEC = importlib.util.spec_from_file_location(
    "build_read_long_lines_report", MODULE_PATH
)
assert SPEC and SPEC.loader
REPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REPORT)


def test_parse_read_long_lines_telemetry_counts_actual_preview_savings() -> None:
    records = [
        {
            "type": "custom",
            "customType": "read-long-lines.telemetry",
            "data": {"schemaVersion": 1, "event": "registered"},
        },
        {
            "type": "custom",
            "customType": "read-long-lines.telemetry",
            "data": {
                "schemaVersion": 1,
                "event": "previewed",
                "toolCallId": "read-1",
                "path": "src/main.rs",
                "shortenedLines": [
                    {
                        "lineNumber": 57,
                        "totalCharacters": 2950,
                        "omittedCharacters": 950,
                    },
                    {
                        "lineNumber": 58,
                        "totalCharacters": 2822,
                        "omittedCharacters": 822,
                    },
                ],
                "omittedCharacters": 1772,
            },
        },
    ]

    telemetry = REPORT.parse_read_long_lines_telemetry(records)

    expected_notice_characters = (
        2
        + len(
            "[Line 57 shortened: showing 2,000 of 2,950 characters. "
            "Use offset=57, limit=1 to read the complete line.]"
        )
        + 1
        + len(
            "[Line 58 shortened: showing 2,000 of 2,822 characters. "
            "Use offset=58, limit=1 to read the complete line.]"
        )
    )
    assert telemetry["registered_events"] == 1
    assert telemetry["preview_events"] == 1
    assert telemetry["shortened_lines"] == 2
    assert telemetry["omitted_characters"] == 1772
    assert telemetry["notice_characters"] == expected_notice_characters
    assert telemetry["net_characters_saved"] == 1772 - expected_notice_characters


def test_select_trajectory_packets_uses_predeclared_triggers() -> None:
    pairs = [
        {
            "pair_id": "flip",
            "baseline": {"reward_binary": 0, "reward_partial": 0.99},
            "extension": {"reward_binary": 1, "reward_partial": 1.0},
            "telemetry": {"preview_events": 0},
        },
        {
            "pair_id": "partial",
            "baseline": {"reward_binary": 0, "reward_partial": 0.8},
            "extension": {"reward_binary": 0, "reward_partial": 0.6},
            "telemetry": {"preview_events": 0},
        },
        {
            "pair_id": "activated",
            "baseline": {"reward_binary": 1, "reward_partial": 1.0},
            "extension": {"reward_binary": 1, "reward_partial": 1.0},
            "telemetry": {"preview_events": 1},
        },
        {
            "pair_id": "stable",
            "baseline": {"reward_binary": 1, "reward_partial": 1.0},
            "extension": {"reward_binary": 1, "reward_partial": 1.0},
            "telemetry": {"preview_events": 0},
        },
    ]

    selected = REPORT.select_trajectory_packets(pairs, partial_delta_threshold=0.1)

    assert [pair["pair_id"] for pair in selected] == [
        "flip",
        "partial",
        "activated",
    ]


def test_summarize_paired_results_separates_net_outcomes_from_churn() -> None:
    pairs = [
        {
            "baseline": {
                "reward_binary": 1,
                "reward_partial": 1.0,
                "total_tokens": 100,
                "input_tokens": 20,
                "cache_read_tokens": 70,
                "output_tokens": 10,
                "agent_wall_s": 10,
                "turns": 2,
                "tool_calls": 3,
                "cost_usd": 1.0,
            },
            "extension": {
                "reward_binary": 1,
                "reward_partial": 1.0,
                "total_tokens": 80,
                "input_tokens": 20,
                "cache_read_tokens": 50,
                "output_tokens": 10,
                "agent_wall_s": 9,
                "turns": 2,
                "tool_calls": 3,
                "cost_usd": 0.8,
            },
            "telemetry": {
                "preview_events": 1,
                "omitted_characters": 100,
                "net_characters_saved": 80,
            },
        },
        {
            "baseline": {
                "reward_binary": 0,
                "reward_partial": 0.5,
                "total_tokens": 100,
                "input_tokens": 20,
                "cache_read_tokens": 70,
                "output_tokens": 10,
                "agent_wall_s": 10,
                "turns": 2,
                "tool_calls": 3,
                "cost_usd": 1.0,
            },
            "extension": {
                "reward_binary": 1,
                "reward_partial": 1.0,
                "total_tokens": 120,
                "input_tokens": 20,
                "cache_read_tokens": 90,
                "output_tokens": 10,
                "agent_wall_s": 11,
                "turns": 3,
                "tool_calls": 4,
                "cost_usd": 1.2,
            },
            "telemetry": {
                "preview_events": 0,
                "omitted_characters": 0,
                "net_characters_saved": 0,
            },
        },
    ]

    summary = REPORT.summarize_paired_results(pairs)

    assert summary["pairs"] == 2
    assert summary["both_solved"] == 1
    assert summary["baseline_only_solved"] == 0
    assert summary["extension_only_solved"] == 1
    assert summary["neither_solved"] == 0
    assert summary["baseline_solves"] == 1
    assert summary["extension_solves"] == 2
    assert summary["total_tokens"]["baseline"] == 200
    assert summary["total_tokens"]["extension"] == 200
    assert summary["activated_pairs"] == 1
    assert summary["net_characters_saved"] == 80
