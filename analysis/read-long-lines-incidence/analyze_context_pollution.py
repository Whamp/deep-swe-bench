#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

USAGE_FIELDS = {
    "input": "post_activation_input_tokens",
    "output": "post_activation_output_tokens",
    "cacheRead": "post_activation_cache_read_tokens",
    "cacheWrite": "post_activation_cache_write_tokens",
    "totalTokens": "post_activation_total_tokens",
}


def summarize_post_activation_usage(
    records: list[dict], first_activation_record_line: int
) -> dict[str, int]:
    """Sum native executor usage after the first context-polluting read result."""
    summary = {
        "post_activation_assistant_messages": 0,
        **{output_field: 0 for output_field in USAGE_FIELDS.values()},
    }
    for record in records[first_activation_record_line:]:
        message = record.get("message") or {}
        if message.get("role") != "assistant":
            continue
        summary["post_activation_assistant_messages"] += 1
        usage = message.get("usage") or {}
        for usage_field, output_field in USAGE_FIELDS.items():
            value = usage.get(usage_field, 0)
            if isinstance(value, (int, float)):
                summary[output_field] += int(value)
    return summary


def read_jsonl_preserving_lines(path: Path) -> list[dict]:
    records = []
    for raw in path.read_text().splitlines():
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            records.append({})
    return records


def read_classifications(path: Path) -> dict[str, dict[str, str]]:
    return {row["task"]: row for row in csv.DictReader(path.open())}


def read_notice_characters(activation_rows: list[dict[str, str]]) -> int:
    if not activation_rows:
        return 0
    return (
        2
        + sum(int(row["notice_characters"]) for row in activation_rows)
        + len(activation_rows)
        - 1
    )


def analyze_context_pollution_reps(
    results_root: Path,
    activation_path: Path,
    classification_path: Path,
) -> list[dict]:
    classifications = read_classifications(classification_path)
    reads: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in csv.DictReader(activation_path.open()):
        if row["task"] in classifications:
            reads[(row["session_path"], int(row["record_line"]))].append(row)

    rep_reads: dict[str, list[list[dict[str, str]]]] = defaultdict(list)
    for (session_path, _), rows in reads.items():
        rep_reads[session_path].append(rows)

    output = []
    for session_relative_path, grouped_reads in sorted(rep_reads.items()):
        first_row = grouped_reads[0][0]
        classification = classifications[first_row["task"]]
        session_path = results_root.parent / session_relative_path
        result = json.loads((session_path.parent.parent / "result.json").read_text())
        first_activation_record_line = min(
            int(rows[0]["record_line"]) for rows in grouped_reads
        )
        omitted_characters = sum(
            int(row["omitted_characters"]) for rows in grouped_reads for row in rows
        )
        notice_characters = sum(read_notice_characters(rows) for rows in grouped_reads)
        output.append(
            {
                "task": first_row["task"],
                "category": classification["category"],
                "classification_evidence": classification["evidence"],
                "model_leaf": first_row["model_leaf"],
                "thinking": first_row["thinking"],
                "config": first_row["config"],
                "rep": first_row["rep"],
                "session_path": session_relative_path,
                "first_activation_record_line": first_activation_record_line,
                "affected_read_results": len(grouped_reads),
                "long_lines": sum(len(rows) for rows in grouped_reads),
                "omitted_characters": omitted_characters,
                "notice_characters": notice_characters,
                "net_characters_removed": omitted_characters - notice_characters,
                **summarize_post_activation_usage(
                    read_jsonl_preserving_lines(session_path),
                    first_activation_record_line,
                ),
                "reward_binary": result.get("reward_binary"),
                "reward_partial": result.get("reward_partial"),
                "turns": result.get("turns"),
                "total_tokens": result.get("total_tokens"),
                "agent_timed_out": result.get("agent_timed_out"),
                "agent_exit": result.get("agent_exit"),
            }
        )
    return output


def summarize_context_pollution(rows: list[dict]) -> dict:
    count_fields = (
        "affected_read_results",
        "long_lines",
        "omitted_characters",
        "notice_characters",
        "net_characters_removed",
        "post_activation_assistant_messages",
        *USAGE_FIELDS.values(),
    )

    def summarize(group: list[dict]) -> dict:
        return {
            "reps": len(group),
            "solved_reps": sum(row["reward_binary"] == 1 for row in group),
            **{field: sum(row[field] for row in group) for field in count_fields},
        }

    by_category = {}
    for category in sorted({row["category"] for row in rows}):
        by_category[category] = summarize(
            [row for row in rows if row["category"] == category]
        )
    return {
        **summarize(rows),
        "tasks": len({row["task"] for row in rows}),
        "by_category": by_category,
        "interpretation": (
            "This is observational exposure evidence, not a token-savings estimate or "
            "a causal reward comparison. Post-activation usage includes all subsequent "
            "trajectory behavior and prompt-cache effects."
        ),
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--activations", type=Path, required=True)
    parser.add_argument("--classifications", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = analyze_context_pollution_reps(
        args.results, args.activations, args.classifications
    )
    write_csv(args.out / "reps.csv", rows)
    summary = summarize_context_pollution(rows)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
