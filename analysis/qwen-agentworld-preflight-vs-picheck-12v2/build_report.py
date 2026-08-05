#!/usr/bin/env python3
"""Build the Qwen-AgentWorld PreFlight versus pi-check comparison report."""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import statistics
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

MODEL_LEAF = "qwen-agentworld-35b-a3b"
THINKING_LEVEL = "high"
PLAIN_BASELINE_CONFIG = "baseline-qwen-agentworld-35b@1.0.0"
CONTROL_CONFIG = "pi-check@1.3.0"
PREFLIGHT_CONFIG = "pi-check@1.6.0"
EXPECTED_PAIR_COUNT = 36
MATERIAL_F2P_DELTA = 0.25
MATERIAL_P2P_DELTA = 0.05
LARGE_PATCH_BYTES = 1_048_576
LONG_CHECKPOINT_CALLS = 25
BOOTSTRAP_SEED = 20260805

PACKET_CLASSIFICATIONS: dict[tuple[str, int], dict[str, str]] = {
    ("adaptix-name-mapping-aliases", 0): {
        "primary_driver": "likely variance",
        "secondary_driver": "completion audit",
        "first_divergence": "PreFlight read three owner files, then reissued the blocked component edit unchanged; six later re-audit mutations preceded the final gain.",
        "mechanism": "F2P rose 6/44 to 13/44 and P2P 2569/2738 to 2738/2738, but the checkpoint did not alter the first mutation, so the gain cannot be isolated to PreFlight.",
        "disposition": "useful candidate trajectory, not a supported PreFlight win",
    },
    ("adaptix-name-mapping-aliases", 1): {
        "primary_driver": "cross-scope regression",
        "secondary_driver": "missing invariant/guard",
        "first_divergence": "PreFlight read loader paths but reissued the blocked layout edit unchanged; the final patch spread across seven loader/layout modules and one test file.",
        "mechanism": "Feature tests gained 2 passes, but dumper-provider preservation failures rose by 534, dropping P2P from 2704/2738 to 2170/2738.",
        "disposition": "clear preservation loss; checkpoint failed to constrain scope",
    },
    ("go-critic-doc-link-checker", 0): {
        "primary_driver": "validation gap",
        "secondary_driver": "execution control",
        "first_divergence": "The checkpoint expanded into 53 calls—50 Bash commands, including repeated go/doc probes—before the first successful mutation.",
        "mechanism": "Outcome stayed exactly 2/3 F2P and 15/16 P2P while tokens rose from 8.20M to 19.22M; extra investigation did not change graded behavior.",
        "disposition": "direct checkpoint-overrun evidence",
    },
    ("go-critic-doc-link-checker", 1): {
        "primary_driver": "validation gap",
        "secondary_driver": "execution control",
        "first_divergence": "The checkpoint made 26 calls before mutation, mostly Go API and repository-structure probes.",
        "mechanism": "Outcome again stayed exactly 2/3 F2P and 15/16 P2P while tokens rose from 3.22M to 8.51M and wall time more than doubled.",
        "disposition": "second checkpoint-overrun example with no observed benefit",
    },
    ("langchain-request-coalescing", 0): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "repository understanding",
        "first_divergence": "After the blocked coalesce.py write, PreFlight inspected callback managers and chain lifecycle seams, then rewrote the file with different content.",
        "mechanism": "The prior config's patch timed out in verification; the PreFlight trajectory graded at 39/50 F2P and 232/232 P2P.",
        "disposition": "plausibly PreFlight-assisted termination recovery, not a strict solve",
    },
    ("langchain-request-coalescing", 2): {
        "primary_driver": "validation gap",
        "secondary_driver": "resource evidence unavailable",
        "first_divergence": "The first treatment attempt finished without promotable verifier resource evidence; the harness discarded it and reran the full subject trajectory.",
        "mechanism": "The discarded attempt consumed 9.74M tokens and ended after 59 minutes of run time; only the second attempt appears in canonical result totals.",
        "disposition": "infrastructure retry; final grade is valid but efficiency needs retry-inclusive accounting",
    },
    ("mobly-grouped-test-barriers", 0): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "repository understanding",
        "first_divergence": "PreFlight blocked sync.py, inspected controller configuration and BaseTest execution ownership, then replaced the planned file with different content.",
        "mechanism": "The prior config's synchronization patch timed out in verification; the revised trajectory terminated with 24/79 F2P and 808/808 P2P.",
        "disposition": "plausibly PreFlight-assisted termination recovery; feature coverage remains low",
    },
    ("mobly-grouped-test-barriers", 1): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "repository understanding",
        "first_divergence": "PreFlight blocked a large synchronization.py replacement, read BaseTest end to end, and rewrote the planned implementation before mutation.",
        "mechanism": "The verifier changed from timeout to a complete 41/79 F2P, 808/808 P2P grade.",
        "disposition": "plausibly PreFlight-assisted termination recovery; still no solve",
    },
    ("mobly-grouped-test-barriers", 2): {
        "primary_driver": "likely variance",
        "secondary_driver": "validation gap",
        "first_divergence": "The checkpoint read five execution/configuration files but reissued the blocked synchronization.py write byte-for-byte.",
        "mechanism": "The final verifier completed at 35/79 F2P while the prior config timed out, but the unchanged blocked mutation provides no direct PreFlight mechanism.",
        "disposition": "reliability gain observed; PreFlight attribution unsupported",
    },
    ("participle-grammar-conflict-analysis", 0): {
        "primary_driver": "under-implementation",
        "secondary_driver": "completion audit",
        "first_divergence": "The checkpoint gathered no extra tool evidence before rewriting analyze_types.go, and the final re-audit made no mutation.",
        "mechanism": "The patch preserved all 153 P2P tests but implemented only 12/91 feature cases versus 56/91 in the prior trajectory.",
        "disposition": "material feature loss; no checkpoint-to-repair mechanism",
    },
    ("participle-grammar-conflict-analysis", 2): {
        "primary_driver": "validation gap",
        "secondary_driver": "completion audit",
        "first_divergence": "Validation compiled /tmp/test_with_analyze.go and /tmp/test_parser_methods.go from /app, creating binaries in the repository.",
        "mechanism": "The final git-status check saw the generated files but left both binaries in model.patch, inflating it to 4.15MB for a four-test F2P gain and no solve.",
        "disposition": "clear repository-hygiene failure, not useful implementation scope",
    },
    ("sql-formatter-bigquery-pipe-formatting", 1): {
        "primary_driver": "under-implementation",
        "secondary_driver": "wrong seam/layer",
        "first_divergence": "The checkpoint inspected tokenizer, AST, grammar, and formatter seams, but the final patch omitted lexer and grammar support.",
        "mechanism": "All 26 pipe feature tests failed while 5709/5709 preservation tests passed; the prior config covered 22/26 through the broader parser stack.",
        "disposition": "checkpoint found the seam but did not enforce an end-to-end implementation",
    },
    ("sql-formatter-bigquery-pipe-formatting", 2): {
        "primary_driver": "under-implementation",
        "secondary_driver": "validation gap",
        "first_divergence": "PreFlight read one tokenizer file and then reissued the blocked token edit unchanged.",
        "mechanism": "The final six-file patch preserved 5709/5709 tests but failed every pipe feature test; the prior config passed 14/26.",
        "disposition": "material feature loss with no supported checkpoint correction",
    },
    ("superjson-error-stack-serialization", 0): {
        "primary_driver": "under-implementation",
        "secondary_driver": "missing invariant/guard",
        "first_divergence": "PreFlight read transformer and public-entry seams, then changed the planned error-options write, but the final patch still missed annotation, mode, AggregateError, cause, and redaction invariants.",
        "mechanism": "F2P fell from 43/80 to 17/80 while P2P improved from 114/116 to 116/116.",
        "disposition": "scope-safe but substantially incomplete implementation",
    },
    ("superjson-error-stack-serialization", 1): {
        "primary_driver": "likely variance",
        "secondary_driver": "scope control",
        "first_divergence": "The checkpoint read only tsconfig and reissued the blocked error-options write unchanged; the re-audit made no mutation.",
        "mechanism": "The final patch gained 22 F2P and 16 P2P passes while using fewer turns than the control, but no checkpoint action links PreFlight to the gain.",
        "disposition": "strong candidate outcome without a supported PreFlight mechanism",
    },
}


def parse_report_arguments() -> argparse.Namespace:
    """Parse canonical result, task, state, and output locations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--tasks-root", type=Path, required=True)
    parser.add_argument("--state-path", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("index.html"),
    )
    return parser.parse_args()


def load_config_results(
    results_root: Path,
    config: str,
    expected_keys: set[tuple[str, int]] | None = None,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Load one config's canonical results, optionally restricted to matched keys."""
    config_root = results_root / MODEL_LEAF / THINKING_LEVEL / config
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for result_path in sorted(config_root.glob("*/rep*/result.json")):
        task = result_path.parents[1].name
        rep = int(result_path.parent.name.removeprefix("rep"))
        key = (task, rep)
        if expected_keys is not None and key not in expected_keys:
            continue
        row = json.loads(result_path.read_text())
        row["artifact_root"] = str(result_path.parent)
        row["task"] = task
        row["rep"] = rep
        rows[key] = row
    if len(rows) != EXPECTED_PAIR_COUNT:
        raise ValueError(
            f"PreFlight comparison invalid: expected {EXPECTED_PAIR_COUNT} "
            f"results for {config}; found {len(rows)} under {config_root}"
        )
    return rows


def load_task_metadata(tasks_root: Path, task: str) -> dict[str, str]:
    """Load stable task metadata; difficulty is absent from these task files."""
    document = tomllib.loads((tasks_root / task / "task.toml").read_text())
    metadata = document["metadata"]
    return {
        "title": str(
            metadata.get("display_title") or metadata.get("original_title") or task
        ),
        "language": str(metadata.get("language") or "unknown"),
        "category": str(metadata.get("category") or "unknown"),
        "difficulty": "not recorded in task.toml",
    }


def result_directory(row: dict[str, Any]) -> Path:
    """Return the canonical artifact directory attached while loading results."""
    return Path(str(row["artifact_root"]))


def is_invalid(row: dict[str, Any]) -> bool:
    """Return whether a result lacks a normal binary grade."""
    return row.get("reward_binary") == -1


def result_status(row: dict[str, Any]) -> str:
    """Return a compact outcome class for report tables."""
    if row.get("reward_binary") == 1:
        return "solved"
    if row.get("agent_timed_out"):
        return "agent timeout"
    if row.get("verifier_exit") == "timeout":
        return "verifier timeout"
    if is_invalid(row):
        return "invalid"
    return "graded"


def weighted_grade(rows: list[dict[str, Any]], prefix: str) -> tuple[int, int, float]:
    """Return passed, total, and ratio for F2P or P2P grading fields."""
    passed = sum(int(row.get(f"{prefix}_passed") or 0) for row in rows)
    total = sum(int(row.get(f"{prefix}_total") or 0) for row in rows)
    return passed, total, passed / total if total else 0.0


def paired_bootstrap_interval(values: list[float]) -> tuple[float, float]:
    """Return a deterministic paired cell-bootstrap 95% interval."""
    random_source = random.Random(BOOTSTRAP_SEED)
    means = [
        statistics.mean(random_source.choice(values) for _ in values)
        for _ in range(20_000)
    ]
    means.sort()
    return means[500], means[19_499]


def message_text(message: dict[str, Any]) -> str:
    """Flatten Pi text content while excluding hidden reasoning blocks."""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(item.get("text", ""))
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )


def record_message(record: dict[str, Any]) -> dict[str, Any]:
    """Return one validated Pi message object or an empty mapping."""
    message = record.get("message")
    return message if isinstance(message, dict) else {}


def load_session_attempts(result_root: Path) -> list[list[dict[str, Any]]]:
    """Load each native Pi session as one ordered subject attempt."""
    attempts: list[list[dict[str, Any]]] = []
    for session_path in sorted((result_root / "session").glob("*.jsonl")):
        records: list[dict[str, Any]] = []
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        attempts.append(records)
    return attempts


def tool_argument_summary(arguments: Any) -> str:
    """Render bounded tool arguments without dropping paths or commands."""
    return json.dumps(arguments, sort_keys=True, ensure_ascii=False)[:600]


def is_validation_command(arguments: Any) -> bool:
    """Identify test, build, and type-check commands in Bash arguments."""
    rendered = json.dumps(arguments, sort_keys=True).lower()
    return bool(
        re.search(
            r"pytest|go test|go build|npm (?:test|run)|pnpm|yarn|bun test|cargo test|ruff|mypy|ty check|tsc|make test|gradle.*test",
            rendered,
        )
    )


def assistant_usage(records: list[dict[str, Any]]) -> dict[str, int]:
    """Sum native assistant usage for one subject attempt."""
    input_tokens = 0
    output_tokens = 0
    turns = 0
    for record in records:
        message = record.get("message", {})
        if record.get("type") != "message" or message.get("role") != "assistant":
            continue
        usage = message.get("usage", {})
        if isinstance(usage, dict):
            input_tokens += int(usage.get("input") or 0)
            output_tokens += int(usage.get("output") or 0)
        turns += 1
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "turns": turns,
    }


def build_session_evidence(result_root: Path) -> dict[str, Any]:
    """Build tool, PreFlight, re-audit, retry, and stage evidence."""
    attempts = load_session_attempts(result_root)
    timeline: list[dict[str, Any]] = []
    checkpoint_calls = 0
    checkpoint_reads = 0
    checkpoint_bash = 0
    checkpoints_with_calls = 0
    checkpoints_with_reads = 0
    checkpoints_with_bash = 0
    checkpoint_exact_reissues = 0
    checkpoint_changed_reissues = 0
    checkpoint_other_continuations = 0
    preflight_triggers = 0
    blocked_mutations = 0
    reaudit_triggers = 0
    successful_read_paths: list[str] = []
    usage_by_attempt: list[dict[str, int]] = []

    for attempt_index, records in enumerate(attempts):
        usage_by_attempt.append(assistant_usage(records))
        result_by_call: dict[str, dict[str, Any]] = {}
        for record in records:
            message = record.get("message", {})
            if record.get("type") == "message" and message.get("role") == "toolResult":
                result_by_call[str(message.get("toolCallId"))] = message

        preflight_indexes = [
            index
            for index, record in enumerate(records)
            if record.get("type") == "message"
            and record_message(record).get("role") == "user"
            and "Pi-check preflight:" in message_text(record_message(record))
        ]
        reaudit_indexes = [
            index
            for index, record in enumerate(records)
            if record.get("type") == "message"
            and record_message(record).get("role") == "user"
            and "Re-audit every requirement" in message_text(record_message(record))
        ]
        preflight_triggers += len(preflight_indexes)
        reaudit_triggers += len(reaudit_indexes)

        attempt_calls: list[dict[str, Any]] = []
        for record_index, record in enumerate(records):
            message = record.get("message", {})
            if record.get("type") != "message" or message.get("role") != "assistant":
                continue
            content = message.get("content", [])
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "toolCall":
                    continue
                call_id = str(item.get("id"))
                tool_name = str(item.get("name"))
                arguments = item.get("arguments", {})
                tool_result = result_by_call.get(call_id)
                result_text = message_text(tool_result or {})
                entry = {
                    "attempt": attempt_index + 1,
                    "ordinal": len(timeline) + 1,
                    "record_index": record_index,
                    "timestamp": message.get("timestamp"),
                    "tool": tool_name,
                    "arguments": tool_argument_summary(arguments),
                    "arguments_raw": arguments,
                    "blocked_by_preflight": "Blocked by pi-check preflight"
                    in result_text,
                    "result_state": (
                        "missing"
                        if tool_result is None
                        else "error"
                        if tool_result.get("isError")
                        else "ok"
                    ),
                    "result_excerpt": result_text[:400],
                }
                timeline.append(entry)
                attempt_calls.append(entry)
                blocked_mutations += int(entry["blocked_by_preflight"])
                if (
                    tool_name == "read"
                    and entry["result_state"] == "ok"
                    and isinstance(arguments, dict)
                    and arguments.get("path")
                ):
                    successful_read_paths.append(str(arguments["path"]))

        for preflight_index in preflight_indexes:
            blocked = next(
                (
                    call
                    for call in attempt_calls
                    if call["record_index"] < preflight_index
                    and call["blocked_by_preflight"]
                ),
                None,
            )
            following = [
                call for call in attempt_calls if call["record_index"] > preflight_index
            ]
            first_successful_mutation_index = next(
                (
                    index
                    for index, call in enumerate(following)
                    if call["tool"] in {"edit", "write"}
                    and call["result_state"] == "ok"
                ),
                len(following),
            )
            checkpoint = following[:first_successful_mutation_index]
            checkpoint_calls += len(checkpoint)
            checkpoint_reads += sum(call["tool"] == "read" for call in checkpoint)
            checkpoint_bash += sum(call["tool"] == "bash" for call in checkpoint)
            checkpoints_with_calls += int(bool(checkpoint))
            checkpoints_with_reads += int(
                any(call["tool"] == "read" for call in checkpoint)
            )
            checkpoints_with_bash += int(
                any(call["tool"] == "bash" for call in checkpoint)
            )
            first_mutation = (
                following[first_successful_mutation_index]
                if first_successful_mutation_index < len(following)
                else None
            )
            if blocked is not None and first_mutation is not None:
                if (
                    blocked["tool"] == first_mutation["tool"]
                    and blocked["arguments_raw"] == first_mutation["arguments_raw"]
                ):
                    checkpoint_exact_reissues += 1
                elif blocked["tool"] == first_mutation["tool"]:
                    checkpoint_changed_reissues += 1
                else:
                    checkpoint_other_continuations += 1
            else:
                checkpoint_other_continuations += 1

    tool_counts = Counter(entry["tool"] for entry in timeline)
    tool_error_counts = Counter(
        entry["tool"] for entry in timeline if entry["result_state"] == "error"
    )
    validation_entries = [
        entry
        for entry in timeline
        if entry["tool"] == "bash" and is_validation_command(entry["arguments_raw"])
    ]
    post_check_entries: list[dict[str, Any]] = []
    for attempt_index, records in enumerate(attempts):
        reaudit_index = next(
            (
                index
                for index, record in enumerate(records)
                if record.get("type") == "message"
                and record_message(record).get("role") == "user"
                and "Re-audit every requirement" in message_text(record_message(record))
            ),
            None,
        )
        if reaudit_index is None:
            continue
        post_check_entries.extend(
            entry
            for entry in timeline
            if entry["attempt"] == attempt_index + 1
            and entry["record_index"] > reaudit_index
        )

    unique_reads = set(successful_read_paths)
    discarded_usage = usage_by_attempt[:-1]
    return {
        "session_attempts": len(attempts),
        "usage_by_attempt": usage_by_attempt,
        "discarded_attempt_tokens": sum(
            usage["total_tokens"] for usage in discarded_usage
        ),
        "preflight_triggers": preflight_triggers,
        "blocked_mutations": blocked_mutations,
        "checkpoint_calls": checkpoint_calls,
        "checkpoint_reads": checkpoint_reads,
        "checkpoint_bash": checkpoint_bash,
        "checkpoints_with_calls": checkpoints_with_calls,
        "checkpoints_with_reads": checkpoints_with_reads,
        "checkpoints_with_bash": checkpoints_with_bash,
        "checkpoint_exact_reissues": checkpoint_exact_reissues,
        "checkpoint_changed_reissues": checkpoint_changed_reissues,
        "checkpoint_other_continuations": checkpoint_other_continuations,
        "reaudit_triggers": reaudit_triggers,
        "tool_counts": dict(tool_counts),
        "tool_error_counts": dict(tool_error_counts),
        "tool_result_errors": sum(tool_error_counts.values()),
        "successful_exact_reads": len(successful_read_paths),
        "unique_successful_exact_reads": len(unique_reads),
        "repeated_successful_reads": len(successful_read_paths) - len(unique_reads),
        "first_validation_ordinal": (
            validation_entries[0]["ordinal"] if validation_entries else None
        ),
        "last_validation_ordinal": (
            validation_entries[-1]["ordinal"] if validation_entries else None
        ),
        "post_check_tool_calls": len(post_check_entries),
        "post_check_mutation_calls": sum(
            entry["tool"] in {"edit", "write"} for entry in post_check_entries
        ),
        "unmatched_tool_calls": sum(
            entry["result_state"] == "missing" for entry in timeline
        ),
        "timeline": [
            {key: value for key, value in entry.items() if key != "arguments_raw"}
            for entry in timeline
        ],
    }


def patch_summary(result_root: Path) -> dict[str, Any]:
    """Extract changed files, line counts, and a bounded patch excerpt."""
    patch_path = result_root / "artifacts/model.patch"
    patch = patch_path.read_text(errors="replace") if patch_path.exists() else ""
    changed_files = re.findall(r"^diff --git a/(.*?) b/", patch, re.MULTILINE)
    additions = sum(
        line.startswith("+") and not line.startswith("+++")
        for line in patch.splitlines()
    )
    deletions = sum(
        line.startswith("-") and not line.startswith("---")
        for line in patch.splitlines()
    )
    return {
        "path": str(patch_path),
        "bytes": len(patch.encode()),
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
        "excerpt": patch[:12_000],
    }


def verifier_evidence(result_root: Path) -> dict[str, Any]:
    """Extract failed tests and bounded verifier logs without regrading."""
    failed_tests: list[dict[str, str]] = []
    ctrf_path = result_root / "verifier/ctrf.json"
    if ctrf_path.exists():
        document = json.loads(ctrf_path.read_text())
        results = document.get("results")
        if not isinstance(results, dict):
            raise ValueError(f"CTRF results missing or invalid: {ctrf_path}")
        tests = results.get("tests")
        if not isinstance(tests, list):
            raise ValueError(f"CTRF tests missing or invalid: {ctrf_path}")
        for test in tests:
            if not isinstance(test, dict):
                raise TypeError(f"CTRF test record invalid: {ctrf_path}")
            if test.get("status") == "failed":
                failed_tests.append(
                    {
                        "name": str(test.get("name", "")),
                        "message": str(test.get("message", ""))[:2_000],
                    }
                )
    excerpts: dict[str, str] = {}
    for relative_path in [
        "verifier/run.log",
        "logs/verifier.stdout.txt",
        "verifier/base.log",
        "verifier/new.log",
    ]:
        path = result_root / relative_path
        if path.exists():
            excerpts[relative_path] = path.read_text(errors="replace")[-8_000:]
    resource_events_path = result_root / "logs/verifier-resource-events.ndjson"
    resource_events = []
    if resource_events_path.exists():
        resource_events = [
            json.loads(line)
            for line in resource_events_path.read_text().splitlines()
            if line.strip()
        ]
    return {
        "failed_test_count": len(failed_tests),
        "failed_tests": failed_tests,
        "log_excerpts": excerpts,
        "verifier_resource_events": resource_events,
    }


def timeout_trace_evidence(result_root: Path) -> dict[str, Any]:
    """Summarize the Qwen-AgentWorld Bash timeout extension trace."""
    trace_path = result_root / "qwen-agentworld-bash-timeout.ndjson"
    if not trace_path.exists():
        return {"present": False, "records": 0, "defaulted": 0, "preserved": 0}
    records = [
        json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()
    ]
    return {
        "present": True,
        "records": len(records),
        "defaulted": sum(record.get("action") == "defaulted" for record in records),
        "preserved": sum(record.get("action") == "preserved" for record in records),
    }


def result_packet_side(row: dict[str, Any]) -> dict[str, Any]:
    """Collect one side of a packet from immutable trajectory artifacts."""
    artifact_root = result_directory(row)
    session = build_session_evidence(artifact_root)
    patch = patch_summary(artifact_root)
    return {
        "result_path": str(artifact_root / "result.json"),
        "status": result_status(row),
        "metrics": {
            key: row.get(key)
            for key in [
                "reward_binary",
                "reward_partial",
                "f2p",
                "f2p_passed",
                "f2p_total",
                "p2p",
                "p2p_passed",
                "p2p_total",
                "agent_exit",
                "agent_timed_out",
                "verifier_exit",
                "agent_wall_s",
                "turns",
                "tool_calls",
                "total_tokens",
                "output_tokens",
                "patch_bytes",
                "resource_policy",
            ]
        },
        "patch": patch,
        "session": session,
        "verifier": verifier_evidence(artifact_root),
        "bash_timeout_trace": timeout_trace_evidence(artifact_root),
        "stage_ledger": {
            "initialization": f"{session['session_attempts']} subject attempt(s)",
            "preflight_checkpoint": (
                f"triggers={session['preflight_triggers']}; "
                f"blocked={session['blocked_mutations']}; "
                f"evidence calls={session['checkpoint_calls']}"
            ),
            "contract_and_seam": (
                f"{session['unique_successful_exact_reads']} unique successful reads"
            ),
            "implementation": (
                f"{len(patch['changed_files'])} files; "
                f"{patch['additions']} additions; {patch['deletions']} deletions"
            ),
            "validation": (
                f"first tool #{session['first_validation_ordinal']}; "
                f"last tool #{session['last_validation_ordinal']}"
            ),
            "completion_audit": (
                f"re-audit triggers={session['reaudit_triggers']}; "
                f"post-check tools={session['post_check_tool_calls']}; "
                f"mutations={session['post_check_mutation_calls']}"
            ),
            "termination": (
                f"agent_exit={row.get('agent_exit')}; "
                f"verifier_exit={row.get('verifier_exit')}"
            ),
        },
    }


def packet_selection_reasons(
    control: dict[str, Any],
    treatment: dict[str, Any],
) -> list[str]:
    """Apply reliability, grading, patch, retry, and checkpoint packet triggers."""
    reasons: list[str] = []
    if is_invalid(control) or is_invalid(treatment):
        reasons.append("invalid outcome on either side")
    if not is_invalid(control) and not is_invalid(treatment):
        if abs(float(treatment["f2p"]) - float(control["f2p"])) >= MATERIAL_F2P_DELTA:
            reasons.append("absolute F2P delta >= 0.25")
        if abs(float(treatment["p2p"]) - float(control["p2p"])) >= MATERIAL_P2P_DELTA:
            reasons.append("absolute P2P delta >= 0.05")
    treatment_session = build_session_evidence(result_directory(treatment))
    if int(treatment.get("patch_bytes") or 0) >= LARGE_PATCH_BYTES:
        reasons.append("treatment patch >= 1 MiB")
    if treatment_session["session_attempts"] > 1:
        reasons.append("treatment subject retry")
    if treatment_session["checkpoint_calls"] >= LONG_CHECKPOINT_CALLS:
        reasons.append("PreFlight checkpoint >= 25 tool calls")
    return reasons


def write_trajectory_packets(
    output_dir: Path,
    metadata_by_task: dict[str, dict[str, str]],
    baseline: dict[tuple[str, int], dict[str, Any]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
) -> dict[tuple[str, int], str]:
    """Write one reviewable JSON packet for every predeclared trigger."""
    packet_dir = output_dir / "packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_links: dict[tuple[str, int], str] = {}
    for key in sorted(treatment):
        reasons = packet_selection_reasons(control[key], treatment[key])
        if not reasons:
            continue
        classification = PACKET_CLASSIFICATIONS.get(key)
        if classification is None:
            raise ValueError(f"Missing packet classification for {key}: {reasons}")
        task, rep = key
        packet = {
            "schema_version": 2,
            "selection_reasons": reasons,
            "selection_rule": (
                "invalid either side; |F2P delta| >= 0.25; |P2P delta| >= 0.05; "
                "treatment patch >= 1 MiB; treatment retry; or checkpoint >= 25 calls"
            ),
            "task": task,
            "rep": rep,
            **metadata_by_task[task],
            "comparison_roles": {
                "plain_baseline": "secondary same-model config control",
                "pi_check": "primary same-model config control with re-audit and Bash timeout",
                "preflight": "same-model config control adding PreFlight",
                "frontier_reference": "none",
            },
            "classification": classification,
            "paired_deltas": {
                metric: (
                    float(treatment[key][metric]) - float(control[key][metric])
                    if isinstance(control[key].get(metric), int | float)
                    and isinstance(treatment[key].get(metric), int | float)
                    else None
                )
                for metric in [
                    "reward_partial",
                    "f2p",
                    "p2p",
                    "agent_wall_s",
                    "turns",
                    "tool_calls",
                    "total_tokens",
                    "output_tokens",
                ]
            },
            "plain_baseline_metrics": result_packet_side(baseline[key])["metrics"],
            "pi_check": result_packet_side(control[key]),
            "preflight": result_packet_side(treatment[key]),
        }
        filename = f"{task}--rep{rep}.json"
        (packet_dir / filename).write_text(json.dumps(packet, indent=2, sort_keys=True))
        packet_links[key] = f"packets/{filename}"
    if set(packet_links) != set(PACKET_CLASSIFICATIONS):
        raise ValueError(
            "PreFlight packet selection changed: "
            f"expected {sorted(PACKET_CLASSIFICATIONS)}; found {sorted(packet_links)}"
        )
    return packet_links


def classify_tool_errors(rows: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    """Classify recorded tool-result errors, separating intentional blocks."""
    calls: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    causes: Counter[str] = Counter()
    for row in rows.values():
        for records in load_session_attempts(result_directory(row)):
            for record in records:
                message = record.get("message", {})
                if (
                    record.get("type") != "message"
                    or message.get("role") != "toolResult"
                ):
                    continue
                tool = str(message.get("toolName"))
                calls[tool] += 1
                if not message.get("isError"):
                    continue
                errors[tool] += 1
                text = message_text(message).lower()
                if "blocked by pi-check preflight" in text:
                    causes["intentional PreFlight block"] += 1
                elif tool == "bash":
                    causes["shell nonzero / diagnostic"] += 1
                elif tool == "edit" and text.startswith("validation failed for tool"):
                    causes["malformed edit arguments"] += 1
                elif tool == "edit" and (
                    "could not find" in text or "old text must match" in text
                ):
                    causes["edit target mismatch"] += 1
                elif tool == "edit":
                    causes["edit no-op / other"] += 1
                elif tool == "read" and (
                    "enoent" in text or "no such file" in text or "not found" in text
                ):
                    causes["read missing file"] += 1
                elif tool == "read" and ("offset" in text or "range" in text):
                    causes["read range error"] += 1
                else:
                    causes[f"{tool} other"] += 1
    intentional = int(causes.get("intentional PreFlight block", 0))
    return {
        "calls": dict(calls),
        "errors": dict(errors),
        "causes": dict(causes),
        "total_calls": sum(calls.values()),
        "total_errors": sum(errors.values()),
        "operational_calls": sum(calls.values()) - intentional,
        "operational_errors": sum(errors.values()) - intentional,
    }


def request_shape_matches(request: dict[str, Any]) -> bool:
    """Check the approved AgentWorld provider request shape."""
    return (
        request.get("model") == "qwen-agentworld-35b-a3b"
        and request.get("max_tokens") == 65_536
        and request.get("temperature") == 0.6
        and request.get("top_p") == 0.95
        and request.get("top_k") == 20
        and request.get("min_p") == 0
        and request.get("repetition_penalty") == 1
        and request.get("chat_template_kwargs")
        == {"enable_thinking": True, "preserve_thinking": True}
        and "reasoning_effort" not in request
    )


def verify_treatment_delivery(
    treatment: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Verify PreFlight, re-audit, timeout, provider, RPC, and resource delivery."""
    delivered_cells = 0
    request_shape_cells = 0
    rpc_cells = 0
    preflight_cells = 0
    reaudit_cells = 0
    timeout_cells = 0
    resource_policy_cells = 0
    aggregate = Counter()
    checkpoint_call_counts: list[int] = []
    max_single_completion_output = 0
    length_stops = 0

    for row in treatment.values():
        artifact_root = result_directory(row)
        requests = [
            json.loads(path.read_text())
            for path in sorted(
                (artifact_root / "initial_context").glob("provider_request_*.json")
            )
        ]
        shape = len(requests) >= 2 and all(
            request_shape_matches(request) for request in requests[:2]
        )
        session = build_session_evidence(artifact_root)
        rpc_events = []
        rpc_path = artifact_root / "logs/pi-rpc-runner.jsonl"
        if rpc_path.exists():
            rpc_events = [
                json.loads(line).get("event")
                for line in rpc_path.read_text().splitlines()
                if line.strip()
            ]
        rpc = "prompt_sent" in rpc_events and "quiescent" in rpc_events
        trace = timeout_trace_evidence(artifact_root)
        preflight = (
            session["preflight_triggers"] >= 1 and session["blocked_mutations"] >= 1
        )
        reaudit = session["reaudit_triggers"] >= 1
        policy = row.get("resource_policy") == {
            "additional_swap_gib": 0.0,
            "host_reserve_gib": 12.0,
            "subject_memory_gib": 12.0,
            "verifier_memory_gib": 12.0,
        }
        request_shape_cells += int(shape)
        rpc_cells += int(rpc)
        preflight_cells += int(preflight)
        reaudit_cells += int(reaudit)
        timeout_cells += int(trace["present"])
        resource_policy_cells += int(policy)
        delivered_cells += int(
            shape and rpc and preflight and reaudit and trace["present"] and policy
        )
        checkpoint_call_counts.append(int(session["checkpoint_calls"]))
        for key in [
            "preflight_triggers",
            "blocked_mutations",
            "checkpoint_calls",
            "checkpoint_reads",
            "checkpoint_bash",
            "checkpoints_with_calls",
            "checkpoints_with_reads",
            "checkpoints_with_bash",
            "checkpoint_exact_reissues",
            "checkpoint_changed_reissues",
            "checkpoint_other_continuations",
            "post_check_tool_calls",
            "post_check_mutation_calls",
            "discarded_attempt_tokens",
        ]:
            aggregate[key] += int(session[key])
        aggregate["retried_cells"] += int(session["session_attempts"] > 1)
        aggregate["cells_with_post_check_mutation"] += int(
            session["post_check_mutation_calls"] > 0
        )
        for records in load_session_attempts(artifact_root):
            for record in records:
                message = record.get("message", {})
                if (
                    record.get("type") != "message"
                    or message.get("role") != "assistant"
                ):
                    continue
                usage = message.get("usage", {})
                if isinstance(usage, dict):
                    max_single_completion_output = max(
                        max_single_completion_output,
                        int(usage.get("output") or 0),
                    )
                length_stops += int(
                    (message.get("stopReason") or message.get("rawStopReason"))
                    == "length"
                )

    return {
        "classification": (
            "delivered" if delivered_cells == EXPECTED_PAIR_COUNT else "missing"
        ),
        "delivered_cells": delivered_cells,
        "request_shape_cells": request_shape_cells,
        "rpc_cells": rpc_cells,
        "preflight_cells": preflight_cells,
        "reaudit_cells": reaudit_cells,
        "timeout_trace_cells": timeout_cells,
        "resource_policy_cells": resource_policy_cells,
        "checkpoint_median_calls": statistics.median(checkpoint_call_counts),
        "checkpoint_max_calls": max(checkpoint_call_counts),
        "max_single_completion_output": max_single_completion_output,
        "length_stops": length_stops,
        **dict(aggregate),
    }


def verify_comparison_provenance(
    baseline: dict[tuple[str, int], dict[str, Any]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Verify fixed identities and disclose the expected harness-policy mismatch."""
    fixed_fields = [
        "model",
        "thinking_level",
        "subject",
        "subject_version",
        "task_revision",
        "verifier_identity",
        "immutable_image_identities",
    ]
    mismatches: dict[str, list[str]] = {}
    for field in fixed_fields:
        mismatched_keys = [
            f"{key[0]}/rep{key[1]}"
            for key in treatment
            if len(
                {
                    json.dumps(rows[key].get(field), sort_keys=True)
                    for rows in [baseline, control, treatment]
                }
            )
            != 1
        ]
        if mismatched_keys:
            mismatches[field] = mismatched_keys
    if mismatches:
        raise ValueError(f"Fixed comparison provenance differs: {mismatches}")
    harness_revisions = {
        config: sorted({str(row.get("harness_revision")) for row in rows.values()})
        for config, rows in [
            (PLAIN_BASELINE_CONFIG, baseline),
            (CONTROL_CONFIG, control),
            (PREFLIGHT_CONFIG, treatment),
        ]
    }
    resource_policies = {
        config: sorted(
            {
                json.dumps(row.get("resource_policy"), sort_keys=True)
                for row in rows.values()
            }
        )
        for config, rows in [
            (PLAIN_BASELINE_CONFIG, baseline),
            (CONTROL_CONFIG, control),
            (PREFLIGHT_CONFIG, treatment),
        ]
    }
    return {
        "fixed_fields": fixed_fields,
        "harness_revisions": harness_revisions,
        "resource_policies": resource_policies,
        "comparison_is_provenance_identical": False,
        "reason": (
            "pi-check@1.6.0 ran under the schema-2 resource-policy harness; older "
            "controls share subject, model, task, verifier, and image identities but "
            "have the earlier harness revision and no recorded resource policy"
        ),
    }


def verify_completed_run(state_path: Path) -> dict[str, Any]:
    """Require the structured run to be complete and expose retry events."""
    status = json.loads((state_path / "status.json").read_text())
    counts = status["counts"]
    if status.get("state") != "completed" or status.get("stage") != "done":
        raise ValueError(f"PreFlight run is not complete: {status.get('state')}")
    if counts.get("batch_done") != EXPECTED_PAIR_COUNT:
        raise ValueError(f"PreFlight batch count invalid: {counts}")
    events = [
        json.loads(line)
        for line in (state_path / "events.ndjson").read_text().splitlines()
        if line.strip()
    ]
    exception_events = [
        event
        for event in events
        if event.get("event") == "cell_finished"
        and event.get("exit_code") == "exception"
    ]
    return {
        "state": status["state"],
        "stage": status["stage"],
        "counts": counts,
        "started_at": status.get("started_at"),
        "updated_at": status.get("updated_at"),
        "exception_events": exception_events,
        "resource_halt_present": (state_path / "resource-halt.json").exists(),
    }


def format_percent(value: float, signed: bool = False) -> str:
    """Format a ratio as a one-decimal percentage."""
    return f"{value:+.1%}" if signed else f"{value:.1%}"


def format_metric(value: Any, digits: int = 3) -> str:
    """Format nullable metrics for dense evidence tables."""
    if not isinstance(value, int | float):
        return "—"
    return f"{float(value):.{digits}f}"


def status_tag(status: str) -> str:
    """Render one compact outcome tag."""
    css_class = (
        "bad"
        if "timeout" in status or status == "invalid"
        else "good"
        if status == "solved"
        else "neutral"
    )
    return f"<span class='tag {css_class}'>{html.escape(status)}</span>"


def render_complete_pair_rows(
    baseline: dict[tuple[str, int], dict[str, Any]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
    packet_links: dict[tuple[str, int], str],
) -> str:
    """Render all 36 matched outcomes before packet filtering."""
    rows: list[str] = []
    for key in sorted(treatment):
        task, rep = key
        left = control[key]
        right = treatment[key]
        f2p_delta = (
            float(right["f2p"]) - float(left["f2p"])
            if not is_invalid(left) and not is_invalid(right)
            else None
        )
        packet = (
            f"<a href='{html.escape(packet_links[key])}'>packet</a>"
            if key in packet_links
            else "—"
        )
        rows.append(
            "<tr>"
            f"<td class='task'>{html.escape(task)}</td>"
            f"<td class='num'>{rep}</td>"
            f"<td>{status_tag(result_status(baseline[key]))}</td>"
            f"<td class='num'>{format_metric(baseline[key].get('f2p'))}</td>"
            f"<td>{status_tag(result_status(left))}</td>"
            f"<td class='num'>{format_metric(left.get('f2p'))}</td>"
            f"<td class='num'>{format_metric(left.get('p2p'))}</td>"
            f"<td>{status_tag(result_status(right))}</td>"
            f"<td class='num'>{format_metric(right.get('f2p'))}</td>"
            f"<td class='num'>{format_metric(right.get('p2p'))}</td>"
            f"<td class='num delta {'up' if f2p_delta is not None and f2p_delta > 0 else 'down' if f2p_delta is not None and f2p_delta < 0 else ''}'>{format_percent(f2p_delta, signed=True) if f2p_delta is not None else '—'}</td>"
            f"<td>{packet}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_task_rows(
    baseline: dict[tuple[str, int], dict[str, Any]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
) -> str:
    """Render task-level mean F2P and validity across three config controls."""
    rows: list[str] = []
    tasks = sorted({key[0] for key in treatment})
    for task in tasks:
        keys = [(task, rep) for rep in range(3)]
        rendered = []
        for config_rows in [baseline, control, treatment]:
            valid_rows = [
                config_rows[key] for key in keys if not is_invalid(config_rows[key])
            ]
            mean_f2p = (
                statistics.mean(float(row["f2p"]) for row in valid_rows)
                if valid_rows
                else None
            )
            rendered.append((len(valid_rows), mean_f2p))
        rows.append(
            "<tr>"
            f"<td class='task'>{html.escape(task)}</td>"
            f"<td class='num'>{rendered[0][0]}/3</td>"
            f"<td class='num'>{format_percent(rendered[0][1]) if rendered[0][1] is not None else '—'}</td>"
            f"<td class='num'>{rendered[1][0]}/3</td>"
            f"<td class='num'>{format_percent(rendered[1][1]) if rendered[1][1] is not None else '—'}</td>"
            f"<td class='num'>{rendered[2][0]}/3</td>"
            f"<td class='num'>{format_percent(rendered[2][1]) if rendered[2][1] is not None else '—'}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_language_rows(
    metadata_by_task: dict[str, dict[str, str]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
) -> str:
    """Render mutually valid weighted F2P and P2P by language."""
    rows: list[str] = []
    for language in sorted(
        {metadata["language"] for metadata in metadata_by_task.values()}
    ):
        keys = [
            key
            for key in treatment
            if metadata_by_task[key[0]]["language"] == language
            and not is_invalid(control[key])
            and not is_invalid(treatment[key])
        ]
        left_f2p = weighted_grade([control[key] for key in keys], "f2p")
        right_f2p = weighted_grade([treatment[key] for key in keys], "f2p")
        left_p2p = weighted_grade([control[key] for key in keys], "p2p")
        right_p2p = weighted_grade([treatment[key] for key in keys], "p2p")
        rows.append(
            "<tr>"
            f"<td>{html.escape(language)}</td>"
            f"<td class='num'>{len(keys)}</td>"
            f"<td class='num'>{format_percent(left_f2p[2])} → {format_percent(right_f2p[2])}</td>"
            f"<td class='num delta {'up' if right_f2p[2] > left_f2p[2] else 'down' if right_f2p[2] < left_f2p[2] else ''}'>{format_percent(right_f2p[2] - left_f2p[2], signed=True)}</td>"
            f"<td class='num'>{format_percent(left_p2p[2])} → {format_percent(right_p2p[2])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_tool_error_rows(
    control_errors: dict[str, Any],
    treatment_errors: dict[str, Any],
) -> str:
    """Render tool-result error causes with concrete denominators."""
    tool_for_cause = {
        "intentional PreFlight block": None,
        "shell nonzero / diagnostic": "bash",
        "malformed edit arguments": "edit",
        "edit target mismatch": "edit",
        "edit no-op / other": "edit",
        "read missing file": "read",
        "read range error": "read",
    }
    causes = sorted(set(control_errors["causes"]) | set(treatment_errors["causes"]))
    rows: list[str] = []
    for cause in causes:
        tool = tool_for_cause.get(cause, cause.split()[0])
        left_count = int(control_errors["causes"].get(cause, 0))
        right_count = int(treatment_errors["causes"].get(cause, 0))
        if tool is None:
            left_value = str(left_count)
            right_value = str(right_count)
        else:
            left_denominator = int(control_errors["calls"].get(tool, 0))
            right_denominator = int(treatment_errors["calls"].get(tool, 0))
            left_value = (
                f"{left_count}/{left_denominator} ({left_count / left_denominator:.1%})"
            )
            right_value = f"{right_count}/{right_denominator} ({right_count / right_denominator:.1%})"
        rows.append(
            "<tr>"
            f"<td>{html.escape(cause)}</td>"
            f"<td class='num'>{left_value}</td>"
            f"<td class='num'>{right_value}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_packet_cards(packet_links: dict[tuple[str, int], str]) -> str:
    """Render classified packet cards with direct JSON evidence links."""
    cards: list[str] = []
    for key in sorted(packet_links):
        classification = PACKET_CLASSIFICATIONS[key]
        task, rep = key
        cards.append(
            "<article class='packet-card'>"
            f"<div><span class='tag neutral'>{html.escape(classification['primary_driver'])}</span> "
            f"<span class='muted'>{html.escape(task)} · rep{rep}</span></div>"
            f"<h3>{html.escape(classification['first_divergence'])}</h3>"
            f"<p>{html.escape(classification['mechanism'])}</p>"
            f"<p class='muted'><strong>Disposition:</strong> {html.escape(classification['disposition'])}</p>"
            f"<a href='{html.escape(packet_links[key])}'>Open trajectory packet →</a>"
            "</article>"
        )
    return "\n".join(cards)


def render_comparison_report(
    baseline: dict[tuple[str, int], dict[str, Any]],
    control: dict[tuple[str, int], dict[str, Any]],
    treatment: dict[tuple[str, int], dict[str, Any]],
    metadata_by_task: dict[str, dict[str, str]],
    packet_links: dict[tuple[str, int], str],
    delivery: dict[str, Any],
    control_errors: dict[str, Any],
    treatment_errors: dict[str, Any],
    provenance: dict[str, Any],
    run_evidence: dict[str, Any],
) -> str:
    """Render the self-contained evidence-first comparison report."""
    keys = sorted(treatment)
    mutually_valid = [
        key
        for key in keys
        if not is_invalid(control[key]) and not is_invalid(treatment[key])
    ]
    control_rows = [control[key] for key in keys]
    treatment_rows = [treatment[key] for key in keys]
    control_mutual = [control[key] for key in mutually_valid]
    treatment_mutual = [treatment[key] for key in mutually_valid]
    baseline_mutual_keys = [
        key
        for key in keys
        if not is_invalid(baseline[key]) and not is_invalid(treatment[key])
    ]
    baseline_mutual = [baseline[key] for key in baseline_mutual_keys]
    treatment_baseline_mutual = [treatment[key] for key in baseline_mutual_keys]

    control_f2p_all = weighted_grade(
        [row for row in control_rows if not is_invalid(row)], "f2p"
    )
    treatment_f2p_all = weighted_grade(treatment_rows, "f2p")
    control_f2p_mutual = weighted_grade(control_mutual, "f2p")
    treatment_f2p_mutual = weighted_grade(treatment_mutual, "f2p")
    control_p2p_mutual = weighted_grade(control_mutual, "p2p")
    treatment_p2p_mutual = weighted_grade(treatment_mutual, "p2p")
    baseline_f2p_mutual = weighted_grade(baseline_mutual, "f2p")
    treatment_baseline_f2p = weighted_grade(treatment_baseline_mutual, "f2p")
    baseline_p2p_mutual = weighted_grade(baseline_mutual, "p2p")
    treatment_baseline_p2p = weighted_grade(treatment_baseline_mutual, "p2p")

    f2p_deltas = [
        float(treatment[key]["f2p"]) - float(control[key]["f2p"])
        for key in mutually_valid
    ]
    p2p_deltas = [
        float(treatment[key]["p2p"]) - float(control[key]["p2p"])
        for key in mutually_valid
    ]
    partial_all_deltas = [
        float(treatment[key]["reward_partial"]) - float(control[key]["reward_partial"])
        for key in keys
    ]
    partial_mutual_deltas = [
        float(treatment[key]["reward_partial"]) - float(control[key]["reward_partial"])
        for key in mutually_valid
    ]
    f2p_interval = paired_bootstrap_interval(f2p_deltas)
    p2p_interval = paired_bootstrap_interval(p2p_deltas)
    partial_all_interval = paired_bootstrap_interval(partial_all_deltas)
    partial_mutual_interval = paired_bootstrap_interval(partial_mutual_deltas)

    recovered_invalid = sum(
        is_invalid(control[key]) and not is_invalid(treatment[key]) for key in keys
    )
    new_invalid = sum(
        not is_invalid(control[key]) and is_invalid(treatment[key]) for key in keys
    )
    left_only_solves = sum(
        control[key].get("reward_binary") == 1
        and treatment[key].get("reward_binary") != 1
        for key in keys
    )
    right_only_solves = sum(
        treatment[key].get("reward_binary") == 1
        and control[key].get("reward_binary") != 1
        for key in keys
    )

    control_tokens = sum(int(row.get("total_tokens") or 0) for row in control_rows)
    treatment_recorded_tokens = sum(
        int(row.get("total_tokens") or 0) for row in treatment_rows
    )
    treatment_actual_tokens = treatment_recorded_tokens + int(
        delivery["discarded_attempt_tokens"]
    )
    recorded_token_delta = treatment_recorded_tokens / control_tokens - 1
    actual_token_delta = treatment_actual_tokens / control_tokens - 1
    control_wall = sum(float(row.get("agent_wall_s") or 0) for row in control_rows)
    treatment_wall = sum(float(row.get("agent_wall_s") or 0) for row in treatment_rows)
    wall_delta = treatment_wall / control_wall - 1
    control_tools = sum(int(row.get("tool_calls") or 0) for row in control_rows)
    treatment_tools = sum(int(row.get("tool_calls") or 0) for row in treatment_rows)
    tool_delta = treatment_tools / control_tools - 1

    complete_rows = render_complete_pair_rows(
        baseline, control, treatment, packet_links
    )
    task_rows = render_task_rows(baseline, control, treatment)
    language_rows = render_language_rows(metadata_by_task, control, treatment)
    tool_error_rows = render_tool_error_rows(control_errors, treatment_errors)
    packet_cards = render_packet_cards(packet_links)
    selected_packet_task_count = len({key[0] for key in packet_links})

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>Qwen-AgentWorld PreFlight vs pi-check · 12_v2</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#a86f00;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08);--radius:24px;--max:1380px}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),linear-gradient(180deg,#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}} .wrap{{max-width:var(--max);margin:auto;padding:28px 20px 48px}} .hero,section{{background:rgba(255,255,255,.93);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}} .hero{{padding:clamp(24px,4vw,42px)}} .eyebrow{{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#1d3fb8;background:#eef3ff;padding:8px 12px;border-radius:999px;display:inline-block}} h1,h2{{letter-spacing:-.035em;line-height:1.08}} h1{{font-size:clamp(2.1rem,5vw,4.2rem);max-width:18ch;margin:14px 0}} h2{{margin:0;font-size:clamp(1.4rem,2.5vw,2rem)}} h3{{line-height:1.25}} .subtitle,.muted{{color:var(--muted)}} .subtitle{{max-width:88ch;font-size:1.05rem}} .pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}} .pill,.tag{{display:inline-flex;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:7px 10px}} .pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}} .pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}} .pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}} .pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}} .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:25px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}} .stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}} .stat .value{{display:block;font-size:clamp(1.35rem,2.3vw,2rem);font-weight:900;margin-top:9px}} .stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:6px}} section{{padding:clamp(18px,3vw,28px);margin-top:20px}} .section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;max-width:90ch;color:var(--muted)}} .callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin-top:14px}} .callout.bad{{border-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.caution{{border-color:var(--amber);background:linear-gradient(90deg,#fff8e7,#fff)}} .grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .card,.packet-card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--surface)}} .card h3,.packet-card h3{{margin:9px 0}} .packet-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}} .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:18px}} table{{width:100%;border-collapse:collapse;min-width:1050px}} th,td{{padding:10px 11px;border-bottom:1px solid #e7edf5;text-align:left;vertical-align:middle}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:#fbfcff;position:sticky;top:0}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}} td.task{{font-family:ui-monospace,monospace;font-size:.82rem;max-width:310px}} .delta.up{{color:var(--green);font-weight:800}} .delta.down{{color:var(--red);font-weight:800}} a{{color:#244bd5;font-weight:750;text-decoration:none}} a:hover{{text-decoration:underline}} code{{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}} .foot{{color:var(--muted);font-size:.84rem;text-align:center;margin-top:24px}} @media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid-2,.packet-grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">Same local model · 36 matched reps · 12_v2 · high thinking</span>
<h1>PreFlight made every rep grade—but did not make Qwen-AgentWorld finish the features.</h1>
<p class="subtitle">Against the same model with pi-check plus the 360-second Bash timeout, PreFlight recovered four verifier-invalid reps. On the 32 pairs where both configs graded, however, weighted F2P fell from {control_f2p_mutual[2]:.1%} to {treatment_f2p_mutual[2]:.1%}, P2P fell from {control_p2p_mutual[2]:.2%} to {treatment_p2p_mutual[2]:.2%}, and strict solves stayed at zero. The checkpoint often changed the immediate plan, but it did not reliably convert added evidence into complete behavior.</p>
<div class="pillrow"><span class="pill bad">0 → 0 strict solves</span><span class="pill good">4 invalids recovered</span><span class="pill bad">{(treatment_f2p_mutual[2] - control_f2p_mutual[2]) * 100:+.1f} pp matched F2P</span><span class="pill caution">{format_percent(actual_token_delta, signed=True)} actual tokens</span><span class="pill neutral">delivery 36/36</span></div>
<div class="stats">
<div class="stat"><span class="label">Canonical validity</span><span class="value">32 → 36</span><span class="sub">one treatment rep needed a full retry</span></div>
<div class="stat"><span class="label">Mutually valid F2P</span><span class="value">{control_f2p_mutual[2]:.1%} → {treatment_f2p_mutual[2]:.1%}</span><span class="sub">−76 / 1,390 feature passes</span></div>
<div class="stat"><span class="label">Mutually valid P2P</span><span class="value">{control_p2p_mutual[2]:.2%} → {treatment_p2p_mutual[2]:.2%}</span><span class="sub">−352 / 36,704 preservation passes</span></div>
<div class="stat"><span class="label">Actual tokens</span><span class="value">{control_tokens / 1_000_000:.1f}M → {treatment_actual_tokens / 1_000_000:.1f}M</span><span class="sub">includes {delivery["discarded_attempt_tokens"] / 1_000_000:.2f}M retry tokens</span></div>
<div class="stat"><span class="label">Checkpoint evidence</span><span class="value">{delivery["checkpoint_calls"]} calls</span><span class="sub">median {delivery["checkpoint_median_calls"]:.1f}; max {delivery["checkpoint_max_calls"]}</span></div>
</div></header>

<section><div class="section-head"><div><h2>Answer first</h2><p>Roles: Qwen-AgentWorld is the local subject in all three configs. <code>{CONTROL_CONFIG}</code> is the primary same-model control; <code>{PLAIN_BASELINE_CONFIG}</code> is a secondary scaffold reference. No frontier reference is part of this comparison.</p></div></div>
<div class="callout good"><strong>Reliable capability:</strong> the combined PreFlight, re-audit, and Bash-timeout config produced a gradable patch in all 36 canonical reps. LangChain rep0 and all three Mobly reps moved from verifier timeout under the primary control to complete grades, with perfect P2P on those recovered reps.</div>
<div class="callout caution"><strong>Checkpoint behavior was real but inconsistent:</strong> {delivery["preflight_triggers"]} PreFlight triggers blocked {delivery["blocked_mutations"]} mutations across 36 reps. The model gathered {delivery["checkpoint_calls"]} evidence calls before its next successful edit/write: {delivery["checkpoint_reads"]} reads and {delivery["checkpoint_bash"]} Bash calls. It reissued {delivery["checkpoint_exact_reissues"]} blocked mutations unchanged, changed {delivery["checkpoint_changed_reissues"]} while keeping the same tool, and continued another way {delivery["checkpoint_other_continuations"]} times.</div>
<div class="callout bad"><strong>No feature-completion gain:</strong> no config solved a rep. On mutually valid pairs, mean F2P moved {statistics.mean(f2p_deltas):+.3f} (cell bootstrap 95% interval {f2p_interval[0]:+.3f} to {f2p_interval[1]:+.3f}); weighted F2P lost 76 passes. Large SQL, Participle, and SuperJSON losses outweighed smaller gains.</div>
<div class="callout"><strong>Interpretation:</strong> PreFlight looks more promising as a termination and seam-reconsideration scaffold than as a general correctness scaffold for this model. The strongest positive packets changed a blocked concurrency implementation after reading lifecycle owners. The strongest negative packets either ignored the checkpoint, found the right seam but did not implement it end to end, or expanded into unbounded investigation.</div></section>

<section><div class="section-head"><div><h2>Complete 36-rep comparison</h2><p>All canonical outcomes appear before packet filtering. “Base” is the plain AgentWorld baseline; “check” is pi-check+timeout; “PreFlight” adds the new mutation checkpoint. F2P and P2P remain separate.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Base</th><th class="num">Base F2P</th><th>Check</th><th class="num">Check F2P</th><th class="num">Check P2P</th><th>PreFlight</th><th class="num">PF F2P</th><th class="num">PF P2P</th><th class="num">Δ F2P</th><th>Evidence</th></tr></thead><tbody>{complete_rows}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Net, churn, and timeout sensitivity</h2><p>Canonical validity improved, but one infrastructure retry and mutually valid grading prevent a simple “36 clean wins” reading.</p></div></div>
<div class="grid-2"><div class="card"><h3>Observed outcomes</h3><ul><li>Strict flips: {left_only_solves} control-only, {right_only_solves} PreFlight-only; neither config solved any rep.</li><li>Validity: {recovered_invalid} control invalid → PreFlight valid; {new_invalid} PreFlight invalid regressions.</li><li>Mutually valid F2P: {sum(delta > 0 for delta in f2p_deltas)} improved, {sum(delta < 0 for delta in f2p_deltas)} worsened, {sum(delta == 0 for delta in f2p_deltas)} tied.</li><li>All-pair partial Δ {statistics.mean(partial_all_deltas):+.3f}, 95% interval {partial_all_interval[0]:+.3f} to {partial_all_interval[1]:+.3f}; this includes recovered invalids.</li><li>Mutually valid partial Δ {statistics.mean(partial_mutual_deltas):+.3f}, 95% interval {partial_mutual_interval[0]:+.3f} to {partial_mutual_interval[1]:+.3f}.</li></ul></div>
<div class="card"><h3>Grading decomposition</h3><ul><li>All graded F2P: check {control_f2p_all[0]}/{control_f2p_all[1]} ({control_f2p_all[2]:.1%}); PreFlight {treatment_f2p_all[0]}/{treatment_f2p_all[1]} ({treatment_f2p_all[2]:.1%}). Denominators differ because PreFlight recovered four reps.</li><li>Mutually valid F2P: {control_f2p_mutual[0]}/{control_f2p_mutual[1]} → {treatment_f2p_mutual[0]}/{treatment_f2p_mutual[1]}.</li><li>Mutually valid P2P: {control_p2p_mutual[0]}/{control_p2p_mutual[1]} → {treatment_p2p_mutual[0]}/{treatment_p2p_mutual[1]}; mean paired Δ {statistics.mean(p2p_deltas):+.4f}, 95% interval {p2p_interval[0]:+.4f} to {p2p_interval[1]:+.4f}.</li><li>Against plain baseline on 33 mutually valid reps: F2P {baseline_f2p_mutual[2]:.1%} → {treatment_baseline_f2p[2]:.1%}; P2P {baseline_p2p_mutual[2]:.2%} → {treatment_baseline_p2p[2]:.2%}. The combined scaffold is slightly stronger on features but weaker on preservation than plain Pi.</li></ul></div></div></section>

<section><div class="section-head"><div><h2>Task-level capability shape</h2><p>Means use each config's valid reps. This table keeps the complete task denominator visible while showing where reliability changed.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Base valid</th><th class="num">Base mean F2P</th><th class="num">Check valid</th><th class="num">Check mean F2P</th><th class="num">PF valid</th><th class="num">PF mean F2P</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<div class="callout good"><strong>Concurrency reliability:</strong> LangChain went 2/3 → 3/3 valid and Mobly 0/3 → 3/3 valid versus check+timeout. Three of those four packets show the checkpoint reading lifecycle owners and changing the blocked implementation; Mobly rep2 reissued its mutation unchanged, so not every recovery supports the same mechanism.</div>
<div class="callout bad"><strong>Feature losses:</strong> SQL reps 1 and 2 fell to 0/26 F2P; Participle rep0 fell 56/91 → 12/91; SuperJSON rep0 fell 43/80 → 17/80. These were complete grades, not infrastructure failures.</div>
<div class="callout bad"><strong>Preservation loss:</strong> Adaptix rep1 gained two feature passes but lost 534 additional P2P passes after spreading changes across loader and name-layout modules. PreFlight read related files but reissued its first mutation unchanged.</div></section>

<section><div class="section-head"><div><h2>Language splits</h2><p>Each language has four tasks and 12 reps; the table uses only mutually valid pairs. Treat these as capability-shape clues, not population estimates.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">Valid pairs</th><th class="num">F2P check → PF</th><th class="num">Δ F2P</th><th class="num">P2P check → PF</th></tr></thead><tbody>{language_rows}</tbody></table></div></section>

<section><div class="section-head"><div><h2>What PreFlight actually did</h2><p>Delivery was verified from session, request, RPC, timeout, and resource artifacts—not inferred from config files.</p></div></div>
<div class="grid-2"><div class="card"><h3>Delivery: {html.escape(str(delivery["classification"]))}</h3><ul><li>Approved request shape: {delivery["request_shape_cells"]}/36.</li><li>PreFlight block and steering evidence: {delivery["preflight_cells"]}/36.</li><li>Final re-audit: {delivery["reaudit_cells"]}/36.</li><li>Bash-timeout trace: {delivery["timeout_trace_cells"]}/36.</li><li>RPC prompt/quiescent: {delivery["rpc_cells"]}/36.</li><li>Schema-2 resource policy: {delivery["resource_policy_cells"]}/36.</li></ul></div>
<div class="card"><h3>Checkpoint conversion</h3><ul><li>{delivery["checkpoints_with_calls"]}/{delivery["preflight_triggers"]} checkpoints made at least one tool call before the next successful edit/write.</li><li>{delivery["checkpoints_with_reads"]} checkpoints read a file; {delivery["checkpoints_with_bash"]} used Bash.</li><li>Median evidence calls: {delivery["checkpoint_median_calls"]:.1f}; maximum: {delivery["checkpoint_max_calls"]}.</li><li>Final re-audit changed code in {delivery["cells_with_post_check_mutation"]}/36 canonical reps.</li><li>Maximum single completion output: {delivery["max_single_completion_output"]:,} tokens; length stops: {delivery["length_stops"]}.</li></ul></div></div>
<div class="callout caution"><strong>Checkpoint overrun:</strong> Go-Critic reps 0 and 1 used 53 and 26 checkpoint calls and produced the same F2P/P2P as the control. Rep0 repeated a /tmp go/doc probe many times. PreFlight needs an evidence-call bound or a “new information” stop rule for this model.</div>
<div class="callout"><strong>Negative evidence:</strong> all requests preserved the approved model, thinking, and sampling path; RPC had no response errors; no result recorded resource exhaustion; no completion stopped for length; the largest single completion was {delivery["max_single_completion_output"]:,} tokens. Do not change serving parameters, the 65,536-token completion ceiling, or the one-hour agent budget based on this comparison.</div></section>

<section><div class="section-head"><div><h2>Execution accounting and provenance</h2><p>The canonical comparison is useful but not a perfectly single-variable A/B.</p></div></div>
<div class="callout caution"><strong>One hidden retry:</strong> LangChain rep2 first ended with <code>LaunchVerifierResourceError</code> because <code>verifier/memory-events.txt</code> was missing. The harness reran the full subject. Canonical result totals retain only the final 8.81M-token attempt; the discarded session consumed {delivery["discarded_attempt_tokens"]:,} tokens. Recorded overhead is {format_percent(recorded_token_delta, signed=True)}; retry-inclusive overhead is {format_percent(actual_token_delta, signed=True)}.</div>
<div class="callout caution"><strong>Harness confound:</strong> {html.escape(provenance["reason"])}. The task revision, Pi version, model/thinking, verifier identity, and all immutable images match. No resource limit was hit, which makes direct resource-policy causation unlikely, but the earlier results are not provenance-identical.</div>
<div class="grid-2"><div class="card"><h3>Efficiency</h3><ul><li>Canonical tokens: {control_tokens:,} → {treatment_recorded_tokens:,} ({format_percent(recorded_token_delta, signed=True)}).</li><li>Retry-inclusive tokens: {treatment_actual_tokens:,} ({format_percent(actual_token_delta, signed=True)}).</li><li>Recorded agent wall: {control_wall / 3600:.2f}h → {treatment_wall / 3600:.2f}h ({format_percent(wall_delta, signed=True)}); discarded retry wall is not represented in result.json.</li><li>Canonical tool calls: {control_tools:,} → {treatment_tools:,} ({format_percent(tool_delta, signed=True)}).</li></ul></div>
<div class="card"><h3>Run integrity</h3><ul><li>Structured state: {html.escape(run_evidence["state"])}/{html.escape(run_evidence["stage"])}; 36/36 batch reps done.</li><li>Resource halt: {run_evidence["resource_halt_present"]}.</li><li>Canonical subject/verifier nonzero exits: 0/36.</li><li>Infrastructure exception events: {len(run_evidence["exception_events"])}; the one event is preserved in the LangChain rep2 packet.</li></ul></div></div></section>

<section><div class="section-head"><div><h2>Tool-result errors by cause</h2><p>An intentional PreFlight block is mechanism delivery, not a tool failure. Shell nonzero results are usually useful diagnostic feedback.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Cause</th><th class="num">Check count / tool calls</th><th class="num">PreFlight count / tool calls</th></tr></thead><tbody>{tool_error_rows}</tbody></table></div>
<div class="callout"><strong>Operational error rate:</strong> check {control_errors["operational_errors"]}/{control_errors["operational_calls"]} ({control_errors["operational_errors"] / control_errors["operational_calls"]:.1%}); PreFlight {treatment_errors["operational_errors"]}/{treatment_errors["operational_calls"]} ({treatment_errors["operational_errors"] / treatment_errors["operational_calls"]:.1%}), after excluding {treatment_errors["causes"].get("intentional PreFlight block", 0)} intentional blocks. Malformed edit arguments fell from {control_errors["causes"].get("malformed edit arguments", 0)}/{control_errors["calls"].get("edit", 0)} to {treatment_errors["causes"].get("malformed edit arguments", 0)}/{treatment_errors["calls"].get("edit", 0)}. No parser or transport failure signature appeared.</div></section>

<section><div class="section-head"><div><h2>Fifteen trajectory packets</h2><p>Selection rule: invalid outcome; |ΔF2P| ≥ 25 points; |ΔP2P| ≥ 5 points; treatment patch ≥ 1MiB; treatment retry; or PreFlight checkpoint ≥ 25 calls. Each packet contains both results, patches, failed tests, stage ledgers, tool timelines, timeout traces, and retry evidence.</p></div></div><div class="packet-grid">{packet_cards}</div></section>

<section><div class="section-head"><div><h2>Scaffoldability ledger</h2><p>These are same-model support hypotheses, not cross-model judgments about pi-check.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Observed weakness</th><th>Layer</th><th>Smallest support</th><th>Success criterion</th></tr></thead><tbody>
<tr><td>Four prior verifier timeouts became canonical valid grades; three checkpoints changed blocked concurrency implementations after reading lifecycle owners.</td><td>Repository understanding / execution control</td><td>Keep the mutation gate, but require one named lifecycle or termination invariant and one bounded targeted probe before concurrent code changes.</td><td>All six LangChain/Mobly reps grade on first attempt, with no P2P loss and higher F2P.</td></tr>
<tr><td>Checkpoint investigation reached 53 calls and repeated low-yield probes.</td><td>Execution control</td><td>Cap checkpoint evidence calls and stop when successive probes do not change the seam, invariant, or plan.</td><td>No checkpoint exceeds 12 calls; Go-Critic outcomes do not regress; total token overhead stays below 8%.</td></tr>
<tr><td>SQL, Participle, and SuperJSON found relevant files but left end-to-end feature paths incomplete.</td><td>Under-implementation</td><td>Require a short requirement-to-seam ledger whose entries each end in implementation plus a targeted observable check.</td><td>At least one strict solve and no decrease in mutually valid weighted F2P.</td></tr>
<tr><td>Adaptix gained two feature passes while losing 534 preservation passes.</td><td>Cross-scope regression</td><td>Add an impact/scope checkpoint before changing loader-wide behavior, followed by targeted preservation tests for adjacent dump paths.</td><td>No material P2P loss (≤0.5 pp) while retaining any F2P gain.</td></tr>
<tr><td>Validation left 4.1MB of generated Go binaries in the patch.</td><td>Completion audit</td><td>Before final response, inspect changed/untracked files and reject build outputs outside declared source/test paths.</td><td>Zero generated binaries or build artifacts in model.patch.</td></tr>
<tr><td>A missing verifier sidecar caused a full subject rerun and hidden usage.</td><td>Harness evidence</td><td>Preserve verifier diagnostics without rerunning the subject when the completed patch can be reverified safely; account discarded attempts in run totals.</td><td>No subject rerun for verifier-evidence-only failures; run-level usage includes every attempt.</td></tr>
</tbody></table></div></section>

<section><div class="section-head"><div><h2>What to test next</h2></div></div>
<div class="callout good"><strong>Keep the mechanism, narrow its job.</strong> The most credible signal is concurrency termination: the checkpoint interrupted a large mutation, exposed lifecycle owners, and three revised plans produced complete grades. Test a bounded “termination invariant” PreFlight on the six LangChain/Mobly reps.</div>
<div class="callout caution"><strong>Do not add more generic reflection.</strong> The model already received both PreFlight and final re-audit. More effort did not produce a solve, and Go-Critic shows that open-ended evidence gathering can double cost without changing behavior.</div>
<div class="callout"><strong>Minimal A/B:</strong> compare current pi-check+timeout against a PreFlight variant capped at 12 checkpoint calls and requiring one requirement→seam→probe ledger. Use the same 12_v2×3 cells. Stop if it produces any new verifier timeout, loses >0.5 pp P2P, fails to improve mutually valid F2P, or exceeds 8% retry-inclusive token overhead.</div>
<div class="callout"><strong>Do not change:</strong> provider sampling, reasoning preservation, output ceiling, and agent timeout all worked as configured. The missing capability is not more context or time; it is converting selected evidence into complete, scope-safe implementation and bounded validation.</div></section>
<div class="foot">Source: <code>results/{MODEL_LEAF}/{THINKING_LEVEL}/</code><br />Primary: <code>{CONTROL_CONFIG}</code> → <code>{PREFLIGHT_CONFIG}</code>; secondary: <code>{PLAIN_BASELINE_CONFIG}</code>. 36 canonical pairs, 72 canonical trajectories, 73 subject attempts, 15 selected packet pairs across {selected_packet_task_count} tasks. Generated deterministically by <code>analysis/qwen-agentworld-preflight-vs-picheck-12v2/build_report.py</code>.</div>
</div></body></html>"""


def main() -> None:
    """Validate canonical inputs, write packets, and render the report."""
    arguments = parse_report_arguments()
    treatment = load_config_results(arguments.results_root, PREFLIGHT_CONFIG)
    expected_keys = set(treatment)
    control = load_config_results(arguments.results_root, CONTROL_CONFIG, expected_keys)
    baseline = load_config_results(
        arguments.results_root,
        PLAIN_BASELINE_CONFIG,
        expected_keys,
    )
    metadata_by_task = {
        task: load_task_metadata(arguments.tasks_root, task)
        for task in sorted({key[0] for key in treatment})
    }
    output_dir = arguments.output.parent
    packet_links = write_trajectory_packets(
        output_dir,
        metadata_by_task,
        baseline,
        control,
        treatment,
    )
    delivery = verify_treatment_delivery(treatment)
    provenance = verify_comparison_provenance(baseline, control, treatment)
    run_evidence = verify_completed_run(arguments.state_path)
    report = render_comparison_report(
        baseline,
        control,
        treatment,
        metadata_by_task,
        packet_links,
        delivery,
        classify_tool_errors(control),
        classify_tool_errors(treatment),
        provenance,
        run_evidence,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(report)
    print(arguments.output)


if __name__ == "__main__":
    main()
