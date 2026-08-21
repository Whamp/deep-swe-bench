#!/usr/bin/env python3
"""Build a llama-benchy workload profile from canonical DeepSWE trajectories.

The extractor reads the newest root Pi session for every canonical result cell under
``results/<model>/<thinking>/<config>/<task>/repN``. It excludes underscore-prefixed
administrative trees, including quarantined and archived copies.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from itertools import pairwise
from pathlib import Path
from typing import Any

RECURSIVE_CHILD_SESSION_RE = re.compile(r"^.+_d[1-9]\d*_c[1-9]\d*\.jsonl$")
PERCENTILES = (10, 25, 50, 75, 90, 95, 99)


def percentile(values: list[int], percentage: int) -> float:
    """Return a linearly interpolated percentile for integer token counts."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentage / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def summarize_values(values: Iterable[int]) -> dict[str, float | int]:
    """Summarize one token or turn-count distribution."""
    materialized = list(values)
    if not materialized:
        return {"count": 0, "mean": 0.0, **{f"p{p}": 0.0 for p in PERCENTILES}}
    p99 = percentile(materialized, 99)
    below_p99 = [value for value in materialized if value <= p99]
    return {
        "count": len(materialized),
        "mean": sum(materialized) / len(materialized),
        "mean_below_p99": sum(below_p99) / len(below_p99),
        **{f"p{p}": percentile(materialized, p) for p in PERCENTILES},
        "max": max(materialized),
    }


def canonical_result_paths(results_dir: Path) -> list[Path]:
    """List normal result cells while excluding all underscore-prefixed trees."""
    paths: list[Path] = []
    for model_dir in results_dir.iterdir():
        if not model_dir.is_dir() or model_dir.name.startswith("_"):
            continue
        paths.extend(model_dir.glob("*/*/*/rep*/result.json"))
    return sorted(paths)


def newest_root_session(cell_dir: Path) -> Path | None:
    """Select the newest non-recursive root session for a result cell."""
    session_dir = cell_dir / "session"
    roots = [
        path
        for path in session_dir.glob("*.jsonl")
        if not RECURSIVE_CHILD_SESSION_RE.match(path.name)
    ]
    return max(
        roots, key=lambda path: (path.stat().st_mtime_ns, path.name), default=None
    )


def load_result_metadata(result_path: Path) -> dict[str, Any]:
    """Load the small set of result fields used to segment workload distributions."""
    with result_path.open(encoding="utf-8") as handle:
        result = json.load(handle)
    model = str(result.get("model") or "unknown")
    return {
        "result_path": str(result_path),
        "model": model,
        "model_leaf": model.rsplit("/", 1)[-1],
        "thinking": str(result.get("thinking_level") or "unknown"),
        "config": str(result.get("config") or "unknown"),
        "task": str(result.get("task") or "unknown"),
        "rep": result.get("rep"),
        "successful": result.get("agent_exit") == 0
        and not result.get("agent_timed_out"),
    }


def parse_assistant_requests(session_path: Path) -> list[dict[str, int]]:
    """Read final per-assistant-message usage from one native Pi root session."""
    requests: list[dict[str, int]] = []
    with session_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "message":
                continue
            message = record.get("message")
            if not isinstance(message, dict) or message.get("role") != "assistant":
                continue
            usage = (
                message.get("usage") if isinstance(message.get("usage"), dict) else {}
            )
            requests.append(
                {
                    "input": max(0, int(usage.get("input") or 0)),
                    "output": max(0, int(usage.get("output") or 0)),
                    "cache_read": max(0, int(usage.get("cacheRead") or 0)),
                    "cache_write": max(0, int(usage.get("cacheWrite") or 0)),
                }
            )
    return requests


def annotate_cache_friendly_shape(requests: list[dict[str, int]]) -> None:
    """Add llama-benchy depth/pp fields, estimating cache shape only when unreported.

    For sessions with cache usage, backend-reported cache read is depth and uncached
    input plus cache write is pp. For sessions with no cache usage metadata, the first
    request is a cold prefill. A later monotonically growing prompt reuses the previous
    prompt plus generated KV; any remaining suffix is pp. A context shrink is treated as
    a cold prefill because the exact surviving prefix cannot be recovered from usage.
    """
    reports_cache = any(item["cache_read"] or item["cache_write"] for item in requests)
    previous_context = 0
    previous_output = 0
    for index, item in enumerate(requests):
        context = item["input"] + item["cache_read"] + item["cache_write"]
        item["context"] = context
        item["reported_depth"] = item["cache_read"]
        item["reported_pp"] = item["input"] + item["cache_write"]
        if reports_cache:
            item["cache_friendly_depth"] = item["reported_depth"]
            item["cache_friendly_pp"] = item["reported_pp"]
            item["cache_shape_estimated"] = 0
        elif index == 0 or context < previous_context:
            item["cache_friendly_depth"] = 0
            item["cache_friendly_pp"] = context
            item["cache_shape_estimated"] = 1
        else:
            reusable_prefix = min(previous_context + previous_output, context)
            item["cache_friendly_depth"] = reusable_prefix
            item["cache_friendly_pp"] = context - reusable_prefix
            item["cache_shape_estimated"] = 1
        previous_context = context
        previous_output = item["output"]


def summarize_requests(requests: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize request-weighted context, depth, prompt processing, and generation."""
    return {
        key: summarize_values(int(item[key]) for item in requests)
        for key in (
            "context",
            "reported_depth",
            "reported_pp",
            "cache_friendly_depth",
            "cache_friendly_pp",
            "output",
        )
    }


def summarize_context_bands(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe a compact workload mix across operationally useful context bands."""
    boundaries = (
        (0, 16_384),
        (16_384, 32_768),
        (32_768, 65_536),
        (65_536, 131_072),
        (131_072, None),
    )
    rows: list[dict[str, Any]] = []
    for lower, upper in boundaries:
        members = [
            item
            for item in requests
            if item["context"] >= lower and (upper is None or item["context"] < upper)
        ]
        rows.append(
            {
                "label": f"{lower}-{upper if upper is not None else 'plus'}",
                "requests": len(members),
                "share": len(members) / len(requests) if requests else 0.0,
                **summarize_requests(members),
            }
        )
    return rows


def request_outlier_examples(
    requests: list[dict[str, Any]], key: str
) -> list[dict[str, Any]]:
    """Keep the five largest requests for audit without copying trajectory content."""
    fields = (
        "result_path",
        "model_leaf",
        "thinking",
        "config",
        "task",
        "rep",
        "turn_index",
        "context",
        "cache_friendly_depth",
        "cache_friendly_pp",
        "output",
    )
    return [
        {field: item[field] for field in fields}
        for item in sorted(requests, key=lambda item: item[key], reverse=True)[:5]
    ]


def summarize_turn_checkpoints(
    request_sequences: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Summarize exact turn numbers while exposing late-turn survivor counts."""
    rows: list[dict[str, Any]] = []
    for turn_number in (1, 2, 5, 10, 20, 40, 60, 100, 150):
        members = [
            sequence[turn_number - 1]
            for sequence in request_sequences
            if len(sequence) >= turn_number
        ]
        rows.append(
            {
                "turn": turn_number,
                "trajectories": len(members),
                "trajectory_share": len(members) / len(request_sequences)
                if request_sequences
                else 0.0,
                **summarize_requests(members),
            }
        )
    final_turns = [sequence[-1] for sequence in request_sequences if sequence]
    rows.append(
        {
            "turn": "final",
            "trajectories": len(final_turns),
            "trajectory_share": 1.0 if final_turns else 0.0,
            **summarize_requests(final_turns),
        }
    )
    return rows


def summarize_normalized_stages(
    request_sequences: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Give every trajectory equal weight within five normalized conversation stages."""
    fields = ("context", "cache_friendly_depth", "cache_friendly_pp", "output")
    stage_rows: list[dict[str, Any]] = []
    for stage_index in range(5):
        trajectory_stage_medians: list[dict[str, int]] = []
        for sequence in request_sequences:
            if not sequence:
                continue
            members = [
                item
                for index, item in enumerate(sequence)
                if min(4, index * 5 // len(sequence)) == stage_index
            ]
            if not members:
                continue
            trajectory_stage_medians.append(
                {
                    field: round(percentile([item[field] for item in members], 50))
                    for field in fields
                }
            )
        stage_rows.append(
            {
                "stage": stage_index + 1,
                "trajectory_fraction": f"{stage_index * 20}-{(stage_index + 1) * 20}%",
                "trajectories": len(trajectory_stage_medians),
                **{
                    field: summarize_values(
                        row[field] for row in trajectory_stage_medians
                    )
                    for field in fields
                },
            }
        )
    return stage_rows


def build_profile(results_dir: Path) -> dict[str, Any]:
    """Build corpus, trajectory, request, and model-segment workload summaries."""
    all_requests: list[dict[str, Any]] = []
    request_sequences: list[list[dict[str, Any]]] = []
    trajectories: list[dict[str, Any]] = []
    missing_sessions: list[str] = []
    zero_usage_requests = 0

    for result_path in canonical_result_paths(results_dir):
        session_path = newest_root_session(result_path.parent)
        if session_path is None:
            missing_sessions.append(str(result_path))
            continue
        metadata = load_result_metadata(result_path)
        requests = parse_assistant_requests(session_path)
        annotate_cache_friendly_shape(requests)
        usable_requests = [
            item for item in requests if item["context"] or item["output"]
        ]
        zero_usage_requests += len(requests) - len(usable_requests)
        for turn_index, item in enumerate(usable_requests, start=1):
            item.update(metadata)
            item["turn_index"] = turn_index
            item["session_reports_cache"] = int(
                any(
                    request["cache_read"] or request["cache_write"]
                    for request in requests
                )
            )
        all_requests.extend(usable_requests)
        request_sequences.append(usable_requests)
        trajectories.append(
            {
                **metadata,
                "turns": len(usable_requests),
                "max_context": max(
                    (item["context"] for item in usable_requests), default=0
                ),
                "total_output": sum(item["output"] for item in usable_requests),
                "reports_cache": bool(
                    any(
                        request["cache_read"] or request["cache_write"]
                        for request in requests
                    )
                ),
            }
        )

    model_requests: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in all_requests:
        model_requests[str(item["model_leaf"])].append(item)

    cache_reported = [item for item in all_requests if item["session_reports_cache"]]
    cache_estimated = [
        item for item in all_requests if not item["session_reports_cache"]
    ]
    successful = [item for item in all_requests if item["successful"]]
    first_turns = [item for item in all_requests if item["turn_index"] == 1]
    follow_up_turns = [item for item in all_requests if item["turn_index"] > 1]

    return {
        "method": {
            "result_glob": "results/<model>/<thinking>/<config>/<task>/rep*/result.json",
            "excluded": "all underscore-prefixed top-level result trees, including _contaminated and _archives",
            "session_selection": "newest non-recursive root session per canonical result cell",
            "request_weighting": "each nonzero assistant completion counts once",
            "reported_mapping": {
                "depth": "cacheRead",
                "pp": "input + cacheWrite",
                "context": "input + cacheRead + cacheWrite",
                "tg": "output",
            },
            "estimated_mapping": "Only for sessions with no cache metadata: cold first/shrunk prompts; otherwise reuse min(previous context + previous output, current context).",
        },
        "corpus": {
            "canonical_result_cells": len(canonical_result_paths(results_dir)),
            "trajectories_with_sessions": len(trajectories),
            "missing_root_sessions": len(missing_sessions),
            "assistant_requests": len(all_requests),
            "zero_usage_assistant_records_excluded": zero_usage_requests,
            "unique_tasks": len({item["task"] for item in trajectories}),
            "model_counts_by_trajectory": dict(
                Counter(item["model_leaf"] for item in trajectories).most_common()
            ),
            "cache_reported_trajectories": sum(
                item["reports_cache"] for item in trajectories
            ),
            "cache_estimated_trajectories": sum(
                not item["reports_cache"] for item in trajectories
            ),
            "missing_session_paths": missing_sessions,
        },
        "trajectory_weighted": {
            "turns": summarize_values(item["turns"] for item in trajectories),
            "max_context": summarize_values(
                item["max_context"] for item in trajectories
            ),
            "total_output": summarize_values(
                item["total_output"] for item in trajectories
            ),
        },
        "request_weighted": {
            "all": summarize_requests(all_requests),
            "successful_trajectories": summarize_requests(successful),
            "first_turn": summarize_requests(first_turns),
            "follow_up_turns": summarize_requests(follow_up_turns),
            "cache_reported_sessions": summarize_requests(cache_reported),
            "cache_estimated_sessions": summarize_requests(cache_estimated),
        },
        "context_bands": summarize_context_bands(all_requests),
        "trajectory_progression": {
            "absolute_turn_checkpoints": summarize_turn_checkpoints(request_sequences),
            "normalized_stages": summarize_normalized_stages(request_sequences),
            "context_shrink_transitions": sum(
                current["context"] < previous["context"]
                for sequence in request_sequences
                for previous, current in pairwise(sequence)
            ),
            "total_follow_up_transitions": sum(
                max(0, len(sequence) - 1) for sequence in request_sequences
            ),
        },
        "audit": {
            "largest_context_requests": request_outlier_examples(
                all_requests, "context"
            ),
            "largest_output_requests": request_outlier_examples(all_requests, "output"),
        },
        "by_model": {
            model: {"requests": len(items), **summarize_requests(items)}
            for model, items in sorted(
                model_requests.items(), key=lambda pair: (-len(pair[1]), pair[0])
            )
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/agentic-inference-profile/profile.json"),
    )
    args = parser.parse_args()
    profile = build_profile(args.results)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(profile["corpus"], indent=2))


if __name__ == "__main__":
    main()
