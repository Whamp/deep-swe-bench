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


def test_summarize_usage_through_first_mutation_includes_decision_message() -> None:
    records = [
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "usage": {
                    "input": 10,
                    "output": 5,
                    "cacheRead": 20,
                    "cacheWrite": 0,
                    "reasoning": 2,
                    "totalTokens": 35,
                    "cost": {"total": 0.1},
                },
                "content": [
                    {
                        "type": "toolCall",
                        "name": "read",
                        "id": "read-1",
                        "arguments": {"path": "src/main.rs"},
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "usage": {
                    "input": 30,
                    "output": 10,
                    "cacheRead": 40,
                    "cacheWrite": 0,
                    "reasoning": 3,
                    "totalTokens": 80,
                    "cost": {"total": 0.2},
                },
                "content": [
                    {
                        "type": "toolCall",
                        "name": "edit",
                        "id": "edit-1",
                        "arguments": {"path": "src/main.rs", "edits": []},
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "usage": {"totalTokens": 999},
                "content": [],
            },
        },
    ]

    phase = REPORT.summarize_usage_through_first_mutation(records)

    assert phase["boundary_found"] is True
    assert phase["first_mutation_tool"] == "edit"
    assert phase["first_mutation_turn"] == 2
    assert phase["assistant_messages"] == 2
    assert phase["usage"] == {
        "input_tokens": 40,
        "output_tokens": 15,
        "cache_read_tokens": 60,
        "cache_write_tokens": 0,
        "reasoning_tokens": 5,
        "total_tokens": 115,
        "cost_usd": 0.30000000000000004,
    }


def test_compare_activated_read_results_requires_exact_baseline_arguments() -> None:
    extension_records = [
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolCall",
                        "name": "read",
                        "id": "extension-read",
                        "arguments": {
                            "path": "/app/src/main.rs",
                            "offset": 1,
                            "limit": 280,
                        },
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "read",
                "toolCallId": "extension-read",
                "content": [{"type": "text", "text": "preview"}],
            },
        },
    ]
    baseline_records = [
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolCall",
                        "name": "read",
                        "id": "baseline-read",
                        "arguments": {
                            "path": "src/main.rs",
                            "offset": 1,
                            "limit": 360,
                        },
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "read",
                "toolCallId": "baseline-read",
                "content": [{"type": "text", "text": "unshortened"}],
            },
        },
    ]
    telemetry = {
        "events": [
            {
                "toolCallId": "extension-read",
                "path": "/app/src/main.rs",
                "shortenedLines": [
                    {
                        "lineNumber": 57,
                        "totalCharacters": 2950,
                        "omittedCharacters": 950,
                    }
                ],
                "omittedCharacters": 950,
            }
        ]
    }

    comparisons = REPORT.compare_activated_read_results(
        baseline_records, extension_records, telemetry
    )

    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison["normalized_path"] == "src/main.rs"
    assert comparison["extension_result_characters"] == len("preview")
    assert comparison["counterfactual_result_characters"] > len("preview")
    assert comparison["baseline_match"] == "same_path_different_arguments"
    assert comparison["baseline_result_characters"] is None


def test_summarize_pre_mutation_pairs_keeps_phase_usage_separate() -> None:
    pairs = [
        {
            "baseline_pre_mutation": {
                "boundary_found": True,
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 10,
                    "cache_read_tokens": 70,
                    "cache_write_tokens": 0,
                    "reasoning_tokens": 5,
                    "total_tokens": 100,
                    "cost_usd": 1.0,
                },
            },
            "extension_pre_mutation": {
                "boundary_found": True,
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 10,
                    "cache_read_tokens": 50,
                    "cache_write_tokens": 0,
                    "reasoning_tokens": 5,
                    "total_tokens": 80,
                    "cost_usd": 0.8,
                },
            },
        },
        {
            "baseline_pre_mutation": {
                "boundary_found": True,
                "usage": {
                    "input_tokens": 50,
                    "output_tokens": 20,
                    "cache_read_tokens": 130,
                    "cache_write_tokens": 0,
                    "reasoning_tokens": 10,
                    "total_tokens": 200,
                    "cost_usd": 2.0,
                },
            },
            "extension_pre_mutation": {
                "boundary_found": True,
                "usage": {
                    "input_tokens": 60,
                    "output_tokens": 20,
                    "cache_read_tokens": 160,
                    "cache_write_tokens": 0,
                    "reasoning_tokens": 10,
                    "total_tokens": 240,
                    "cost_usd": 2.4,
                },
            },
        },
    ]

    summary = REPORT.summarize_pre_mutation_pairs(pairs)

    assert summary["complete_boundaries"] == 2
    assert summary["metrics"]["total_tokens"] == {
        "baseline": 300.0,
        "extension": 320.0,
        "delta": 20.0,
        "delta_fraction": 320 / 300 - 1,
        "paired_delta_median": 10.0,
        "pairs_lower_with_extension": 1,
        "pairs_higher_with_extension": 1,
        "paired_deltas": [-20.0, 40.0],
    }
    assert summary["context_input_tokens"]["baseline"] == 270.0
    assert summary["context_input_tokens"]["extension"] == 290.0


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
