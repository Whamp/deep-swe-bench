#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

CHILD_RE = re.compile(r"^.+_d[1-9]\d*_c[1-9]\d*\.jsonl$")
FIRST_LINE_CENSORED_RE = re.compile(r"^\[Line (\d+) is ([^,]+), exceeds 50KB limit\.")
LONG_LINE_LIMIT = 2_000


def utf16_len(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def newest_root_session(session_dir: Path) -> Path | None:
    roots = [p for p in session_dir.glob("*.jsonl") if not CHILD_RE.match(p.name)]
    if not roots:
        return None
    return max(roots, key=lambda p: (p.stat().st_mtime_ns, p.name))


def text_content(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        part.get("text", "")
        for part in content
        if isinstance(part, dict) and part.get("type") == "text"
    )


def notice_length(source_line: int, original_length: int) -> int:
    notice = (
        f"[Line {source_line} shortened: showing 2,000 of {original_length:,} characters. "
        f"Use offset={source_line}, limit=1 to read the complete line.]"
    )
    return utf16_len(notice)


def scan_rep(result_path: Path) -> tuple[dict, list[dict], list[dict]]:
    result = json.loads(result_path.read_text())
    rep_dir = result_path.parent
    session_path = newest_root_session(rep_dir / "session")
    rep_row = {
        "model_leaf": result_path.parts[-6],
        "thinking": result_path.parts[-5],
        "config": result.get("config", result_path.parts[-4]),
        "task": result.get("task", result_path.parts[-3]),
        "rep": result.get("rep", result_path.parts[-2]),
        "result_path": str(result_path),
        "session_path": str(session_path) if session_path else "",
        "read_results": 0,
        "read_result_characters": 0,
        "long_read_results": 0,
        "ordinary_long_read_results": 0,
        "exempt_long_read_results": 0,
        "long_lines": 0,
        "ordinary_long_lines": 0,
        "exempt_long_lines": 0,
        "omitted_characters": 0,
        "notice_characters": 0,
        "net_characters_saved": 0,
        "censored_first_line_results": 0,
        "max_line_characters": 0,
    }
    if session_path is None:
        return rep_row, [], []

    calls: dict[str, dict] = {}
    activation_rows: list[dict] = []
    read_rows: list[dict] = []
    with session_path.open() as handle:
        for record_line, raw in enumerate(handle, 1):
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            message = record.get("message") or {}
            content = message.get("content")
            if message.get("role") == "assistant" and isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "toolCall":
                        calls[part.get("id", "")] = {
                            "name": part.get("name"),
                            "arguments": part.get("arguments") or {},
                            "record_line": record_line,
                        }
                continue
            if message.get("role") != "toolResult" or message.get("toolName") != "read":
                continue

            call_id = message.get("toolCallId", "")
            call = calls.get(call_id, {})
            args = call.get("arguments") or {}
            text = text_content(message)
            lines = text.split("\n")
            line_lengths = [utf16_len(line) for line in lines]
            long_indices = [
                index
                for index, length in enumerate(line_lengths)
                if length > LONG_LINE_LIMIT
            ]
            exempt = args.get("limit") == 1
            omitted = (
                sum(line_lengths[index] - LONG_LINE_LIMIT for index in long_indices)
                if not exempt
                else 0
            )
            raw_offset = args.get("offset")
            start_line = int(raw_offset) if isinstance(raw_offset, (int, float)) else 1
            notices = (
                [
                    notice_length(start_line + index, line_lengths[index])
                    for index in long_indices
                ]
                if not exempt
                else []
            )
            notice_chars = (
                (2 + sum(notices) + max(0, len(notices) - 1)) if notices else 0
            )
            censored = any(FIRST_LINE_CENSORED_RE.match(line) for line in lines)

            rep_row["read_results"] += 1
            rep_row["read_result_characters"] += utf16_len(text)
            rep_row["max_line_characters"] = max(
                rep_row["max_line_characters"], max(line_lengths, default=0)
            )
            rep_row["censored_first_line_results"] += int(censored)
            if long_indices:
                rep_row["long_read_results"] += 1
                rep_row["long_lines"] += len(long_indices)
                if exempt:
                    rep_row["exempt_long_read_results"] += 1
                    rep_row["exempt_long_lines"] += len(long_indices)
                else:
                    rep_row["ordinary_long_read_results"] += 1
                    rep_row["ordinary_long_lines"] += len(long_indices)
                    rep_row["omitted_characters"] += omitted
                    rep_row["notice_characters"] += notice_chars
                    rep_row["net_characters_saved"] += omitted - notice_chars

            read_rows.append(
                {
                    **{
                        k: rep_row[k]
                        for k in (
                            "model_leaf",
                            "thinking",
                            "config",
                            "task",
                            "rep",
                            "session_path",
                        )
                    },
                    "record_line": record_line,
                    "call_record_line": call.get("record_line", ""),
                    "path": args.get("path", args.get("file_path", "")),
                    "offset": args.get("offset", ""),
                    "limit": args.get("limit", ""),
                    "result_characters": utf16_len(text),
                    "line_count": len(lines),
                    "long_line_count": len(long_indices),
                    "ordinary_affected": int(bool(long_indices) and not exempt),
                    "exempt_limit_1": int(bool(long_indices) and exempt),
                    "omitted_characters": omitted,
                    "notice_characters": notice_chars,
                    "net_characters_saved": omitted - notice_chars,
                    "censored_first_line": int(censored),
                    "max_line_characters": max(line_lengths, default=0),
                }
            )
            for index in long_indices:
                source_line = start_line + index
                activation_rows.append(
                    {
                        **{
                            k: rep_row[k]
                            for k in (
                                "model_leaf",
                                "thinking",
                                "config",
                                "task",
                                "rep",
                                "session_path",
                            )
                        },
                        "record_line": record_line,
                        "call_record_line": call.get("record_line", ""),
                        "path": args.get("path", args.get("file_path", "")),
                        "offset": args.get("offset", ""),
                        "limit": args.get("limit", ""),
                        "source_line": source_line,
                        "result_line_index": index,
                        "line_characters": line_lengths[index],
                        "ordinary_affected": int(not exempt),
                        "omitted_characters": line_lengths[index] - LONG_LINE_LIMIT
                        if not exempt
                        else 0,
                        "notice_characters": notice_length(
                            source_line, line_lengths[index]
                        )
                        if not exempt
                        else 0,
                    }
                )
    return rep_row, activation_rows, read_rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def aggregate(rows: list[dict], group_keys: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in group_keys)].append(row)
    output = []
    for key, items in groups.items():
        out = dict(zip(group_keys, key))
        out.update(
            {
                "reps": len(items),
                "activated_reps": sum(
                    item["ordinary_long_read_results"] > 0 for item in items
                ),
                "activation_rate": sum(
                    item["ordinary_long_read_results"] > 0 for item in items
                )
                / len(items),
                "read_results": sum(item["read_results"] for item in items),
                "ordinary_long_read_results": sum(
                    item["ordinary_long_read_results"] for item in items
                ),
                "ordinary_long_lines": sum(
                    item["ordinary_long_lines"] for item in items
                ),
                "omitted_characters": sum(item["omitted_characters"] for item in items),
                "notice_characters": sum(item["notice_characters"] for item in items),
                "net_characters_saved": sum(
                    item["net_characters_saved"] for item in items
                ),
                "censored_first_line_results": sum(
                    item["censored_first_line_results"] for item in items
                ),
                "max_line_characters": max(
                    item["max_line_characters"] for item in items
                ),
            }
        )
        output.append(out)
    return sorted(output, key=lambda row: tuple(str(row[k]) for k in group_keys))


def canonicalize_result_artifact_paths(
    rep: dict,
    activations: list[dict],
    reads: list[dict],
    results_root: Path,
) -> None:
    """Make result and session paths stable across absolute checkout locations."""
    resolved_root = results_root.resolve()
    canonical_root = Path(results_root.name)
    for row in [rep, *activations, *reads]:
        for field in ("result_path", "session_path"):
            raw_path = row.get(field)
            if not raw_path:
                continue
            try:
                relative_path = Path(raw_path).resolve().relative_to(resolved_root)
            except ValueError:
                continue
            row[field] = str(canonical_root / relative_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    result_paths = []
    for path in args.results.glob("*/*/*/*/rep*/result.json"):
        try:
            result = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if result.get("config", path.parts[-4]) in set(args.configs):
            result_paths.append(path)

    rep_rows: list[dict] = []
    activation_rows: list[dict] = []
    read_rows: list[dict] = []
    for index, path in enumerate(sorted(result_paths), 1):
        rep, activations, reads = scan_rep(path)
        canonicalize_result_artifact_paths(
            rep, activations, reads, results_root=args.results
        )
        rep_rows.append(rep)
        activation_rows.extend(activations)
        read_rows.extend(reads)
        if index % 100 == 0:
            print(f"scanned {index}/{len(result_paths)}", flush=True)

    summary = {
        "configs": args.configs,
        "reps": len(rep_rows),
        "sessions": sum(bool(row["session_path"]) for row in rep_rows),
        "tasks": len({row["task"] for row in rep_rows}),
        "activated_tasks": len(
            {row["task"] for row in rep_rows if row["ordinary_long_read_results"] > 0}
        ),
        "activated_reps": sum(
            row["ordinary_long_read_results"] > 0 for row in rep_rows
        ),
        "read_results": sum(row["read_results"] for row in rep_rows),
        "read_result_characters": sum(
            row["read_result_characters"] for row in rep_rows
        ),
        "long_read_results": sum(row["long_read_results"] for row in rep_rows),
        "ordinary_long_read_results": sum(
            row["ordinary_long_read_results"] for row in rep_rows
        ),
        "exempt_long_read_results": sum(
            row["exempt_long_read_results"] for row in rep_rows
        ),
        "ordinary_long_lines": sum(row["ordinary_long_lines"] for row in rep_rows),
        "exempt_long_lines": sum(row["exempt_long_lines"] for row in rep_rows),
        "omitted_characters": sum(row["omitted_characters"] for row in rep_rows),
        "notice_characters": sum(row["notice_characters"] for row in rep_rows),
        "net_characters_saved": sum(row["net_characters_saved"] for row in rep_rows),
        "censored_first_line_results": sum(
            row["censored_first_line_results"] for row in rep_rows
        ),
        "max_line_characters": max(
            (row["max_line_characters"] for row in rep_rows), default=0
        ),
    }
    summary["rep_activation_rate"] = (
        summary["activated_reps"] / summary["reps"] if summary["reps"] else 0
    )
    summary["read_result_activation_rate"] = (
        summary["ordinary_long_read_results"] / summary["read_results"]
        if summary["read_results"]
        else 0
    )
    summary["gross_omission_rate"] = (
        summary["omitted_characters"] / summary["read_result_characters"]
        if summary["read_result_characters"]
        else 0
    )
    summary["net_reduction_rate"] = (
        summary["net_characters_saved"] / summary["read_result_characters"]
        if summary["read_result_characters"]
        else 0
    )

    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_csv(args.out / "reps.csv", rep_rows)
    write_csv(args.out / "reads.csv", read_rows)
    write_csv(args.out / "activations.csv", activation_rows)
    write_csv(args.out / "by-task.csv", aggregate(rep_rows, ("task",)))
    write_csv(
        args.out / "by-model-thinking-config.csv",
        aggregate(rep_rows, ("model_leaf", "thinking", "config")),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
