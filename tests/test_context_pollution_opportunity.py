from __future__ import annotations

import importlib.util
from pathlib import Path

ANALYZER_PATH = (
    Path(__file__).parents[1]
    / "analysis"
    / "read-long-lines-incidence"
    / "analyze_context_pollution.py"
)
SPEC = importlib.util.spec_from_file_location(
    "analyze_context_pollution", ANALYZER_PATH
)
assert SPEC and SPEC.loader
analyze_context_pollution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(analyze_context_pollution)


def test_summarize_post_activation_usage_counts_only_later_assistant_messages() -> None:
    records = [
        {"message": {"role": "assistant", "usage": {"input": 10, "totalTokens": 12}}},
        {"message": {"role": "toolResult"}},
        {
            "message": {
                "role": "assistant",
                "usage": {"input": 20, "cacheRead": 30, "totalTokens": 55},
            }
        },
        {"message": {"role": "assistant", "usage": {"output": 7, "totalTokens": 7}}},
    ]

    summary = analyze_context_pollution.summarize_post_activation_usage(
        records, first_activation_record_line=2
    )

    assert summary == {
        "post_activation_assistant_messages": 2,
        "post_activation_input_tokens": 20,
        "post_activation_output_tokens": 7,
        "post_activation_cache_read_tokens": 30,
        "post_activation_cache_write_tokens": 0,
        "post_activation_total_tokens": 62,
    }
