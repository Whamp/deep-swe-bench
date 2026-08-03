#!/usr/bin/env python3
"""Build the matched Qwen-AgentWorld pi-check versus baseline report."""

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
BASELINE_CONFIG = "baseline-qwen-agentworld-35b@1.0.0"
PI_CHECK_CONFIG = "pi-check@1.3.0"
EXPECTED_PAIR_COUNT = 36
MATERIAL_F2P_DELTA = 0.25
BOOTSTRAP_SEED = 20260803

PACKET_CLASSIFICATIONS: dict[tuple[str, int], dict[str, str]] = {
    ("dateutil-rfc5545-timezone-interop", 2): {
        "primary_driver": "under-implementation",
        "secondary_driver": "completion audit",
        "first_divergence": "The re-audit returned to rrule.py and changed repr, VCALENDAR force-set handling, and iCalendar emission before the final verifier.",
        "mechanism": "Post-check mutations plausibly closed timezone and round-trip cases; F2P rose from 33/67 to 51/67 while P2P became perfect.",
        "disposition": "plausibly check-assisted, not isolated from trajectory variance",
    },
    ("goreleaser-retry-publish-auditing", 0): {
        "primary_driver": "validation gap",
        "secondary_driver": "under-implementation",
        "first_divergence": "The candidate entered the re-audit with a weaker retry/auditing patch, then ran 14 Bash checks without changing the patch.",
        "mechanism": "The check observed the work but did not convert failures into repair; F2P fell from 10/29 to 2/29.",
        "disposition": "candidate loss; no post-check mutation supports a direct harm claim",
    },
    ("goreleaser-retry-publish-auditing", 1): {
        "primary_driver": "validation gap",
        "secondary_driver": "under-implementation",
        "first_divergence": "The candidate reached the re-audit with incomplete retry/status handling, then ran 21 Bash checks without a mutation.",
        "mechanism": "Repeated validation did not repair the missing retry and attempt-auditing invariants; F2P fell from 10/29 to 2/29.",
        "disposition": "candidate loss; check failed to rescue an initially weaker patch",
    },
    ("langchain-request-coalescing", 0): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "resource exhaustion",
        "first_divergence": "The candidate changed coalescing and export behavior, then its verifier never completed; the baseline patch graded at 43/50 F2P.",
        "mechanism": "A concurrency or lifecycle invariant in the final candidate patch likely left verifier tests blocked. No independent harness failure signature isolates infrastructure.",
        "disposition": "observed candidate verifier timeout; patch-linked cause remains likely, not proven",
    },
    ("langchain-request-coalescing", 1): {
        "primary_driver": "resource exhaustion",
        "secondary_driver": "execution control",
        "first_divergence": "The baseline ended on an unbounded Bash call and hit 3,600 seconds; the timeout-enabled candidate completed and graded.",
        "mechanism": "The 360-second Bash default removed the terminal hang and recovered a 36/50 F2P, 232/232 P2P result.",
        "disposition": "clear timeout-control recovery; pi-check contribution is not isolated",
    },
    ("langchain-request-coalescing", 2): {
        "primary_driver": "resource exhaustion",
        "secondary_driver": "execution control",
        "first_divergence": "The baseline ended on an unbounded Bash call and hit 3,600 seconds; the timeout-enabled candidate completed and graded.",
        "mechanism": "The 360-second Bash default removed the terminal hang and recovered a 31/50 F2P, 232/232 P2P result.",
        "disposition": "clear timeout-control recovery; pi-check contribution is not isolated",
    },
    ("mobly-grouped-test-barriers", 0): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "validation gap",
        "first_divergence": "During re-audit the candidate rewrote waiter locking and cleanup in grouped_execution.py; the final verifier then hung.",
        "mechanism": "Barrier registration/cleanup changes plausibly introduced a deadlock or leaked rendezvous. The baseline graded at 37/79 F2P.",
        "disposition": "candidate verifier-timeout loss; final patch is the leading cause",
    },
    ("mobly-grouped-test-barriers", 1): {
        "primary_driver": "resource exhaustion",
        "secondary_driver": "unknown",
        "first_divergence": "Both patches reached verifier timeout through different synchronization implementations.",
        "mechanism": "The treatment neither resolved nor clearly worsened the persistent verifier hang for this rep.",
        "disposition": "both invalid; mechanism unresolved",
    },
    ("mobly-grouped-test-barriers", 2): {
        "primary_driver": "missing invariant/guard",
        "secondary_driver": "resource exhaustion",
        "first_divergence": "The baseline completed grading with 0/79 F2P; the candidate synchronization patch blocked verifier completion.",
        "mechanism": "The candidate changed barrier semantics but did not establish safe lifecycle and cleanup invariants.",
        "disposition": "candidate verifier-timeout loss; no check-stage mutation in this rep",
    },
    ("obsidian-linter-link-format-conversion", 1): {
        "primary_driver": "under-implementation",
        "secondary_driver": "completion audit",
        "first_divergence": "The re-audit made seven edit attempts around Markdown parsing and default heading display handling.",
        "mechanism": "The final candidate covered nested destinations, images, and heading-display cases; F2P rose from 31/60 to 51/60 with P2P unchanged at 1131/1131.",
        "disposition": "plausibly check-assisted feature gain",
    },
    ("participle-grammar-conflict-analysis", 0): {
        "primary_driver": "under-implementation",
        "secondary_driver": "completion audit",
        "first_divergence": "The re-audit rewrote seven analysis modules, expanding report types, conflict detection, and build integration.",
        "mechanism": "The broader second-pass implementation raised F2P from 14/91 to 56/91 while preserving 153/153 P2P tests.",
        "disposition": "plausibly check-assisted feature gain with high added work",
    },
    ("sql-formatter-bigquery-pipe-formatting", 0): {
        "primary_driver": "likely variance",
        "secondary_driver": "implementation plan",
        "first_divergence": "The candidate had already produced its final parser/formatter patch before the re-audit; the check ran five Bash calls and made no mutation.",
        "mechanism": "F2P rose from 0/26 to 11/26 and P2P recovered to 5709/5709, but the gain preceded the check stage.",
        "disposition": "candidate gain not attributable to pi-check",
    },
    ("sql-formatter-bigquery-pipe-formatting", 1): {
        "primary_driver": "likely variance",
        "secondary_driver": "implementation plan",
        "first_divergence": "The candidate had already produced its final parser/formatter patch before the re-audit; the check ran eight Bash calls and made no mutation.",
        "mechanism": "F2P rose from 12/26 to 22/26 with perfect P2P, but no post-check patch change links the gain to pi-check.",
        "disposition": "candidate gain not attributable to pi-check",
    },
}


def parse_report_arguments() -> argparse.Namespace:
    """Parse canonical result, task, and output locations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--tasks-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("index.html"),
    )
    return parser.parse_args()


def load_config_results(
    results_root: Path,
    config: str,
) -> dict[tuple[str, int], dict[str, Any]]:
    """Load exactly 36 task-rep result records for one config."""
    config_root = results_root / MODEL_LEAF / THINKING_LEVEL / config
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for result_path in sorted(config_root.glob("*/rep*/result.json")):
        row = json.loads(result_path.read_text())
        task = result_path.parents[1].name
        rep = int(result_path.parent.name.removeprefix("rep"))
        row["artifact_root"] = str(result_path.parent)
        row["task"] = task
        row["rep"] = rep
        rows[(task, rep)] = row
    if len(rows) != EXPECTED_PAIR_COUNT:
        raise ValueError(
            f"Qwen-AgentWorld comparison invalid: expected {EXPECTED_PAIR_COUNT} "
            f"results for {config}; found {len(rows)} under {config_root}"
        )
    return rows


def load_task_metadata(tasks_root: Path, task: str) -> dict[str, str]:
    """Load stable display metadata; difficulty is absent from these task files."""
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


def numeric_mean(rows: list[dict[str, Any]], key: str) -> float:
    """Return the mean of available numeric values for one result field."""
    values = [float(row[key]) for row in rows if isinstance(row.get(key), int | float)]
    return statistics.mean(values) if values else 0.0


def weighted_grade(rows: list[dict[str, Any]], prefix: str) -> tuple[int, int, float]:
    """Return passed, total, and ratio for F2P or P2P grading fields."""
    passed = sum(int(row.get(f"{prefix}_passed") or 0) for row in rows)
    total = sum(int(row.get(f"{prefix}_total") or 0) for row in rows)
    return passed, total, passed / total if total else 0.0


def paired_bootstrap_interval(values: list[float]) -> tuple[float, float]:
    """Return a deterministic cell-level paired bootstrap 95% interval."""
    random_source = random.Random(BOOTSTRAP_SEED)
    means = [
        statistics.mean(random_source.choice(values) for _ in values)
        for _ in range(20_000)
    ]
    means.sort()
    return means[int(0.025 * len(means))], means[int(0.975 * len(means)) - 1]


def is_invalid(row: dict[str, Any]) -> bool:
    """Return whether a result lacks a normal binary grade."""
    return row.get("reward_binary") == -1


def has_timeout(row: dict[str, Any]) -> bool:
    """Return whether agent or verifier timeout affected a result."""
    return bool(row.get("agent_timed_out")) or row.get("verifier_exit") == "timeout"


def result_status(row: dict[str, Any]) -> str:
    """Render the outcome class used in the complete pair table."""
    if row.get("reward_binary") == 1:
        return "solved"
    if row.get("agent_timed_out"):
        return "agent timeout"
    if row.get("verifier_exit") == "timeout":
        return "verifier timeout"
    if row.get("reward_binary") == -1:
        return "invalid"
    return "graded"


def result_directory(row: dict[str, Any]) -> Path:
    """Return the canonical artifact directory attached while loading results."""
    return Path(str(row["artifact_root"]))


def patch_summary(result_root: Path) -> dict[str, Any]:
    """Extract changed files, line counts, and a bounded patch excerpt."""
    patch_path = result_root / "artifacts/model.patch"
    patch = patch_path.read_text(errors="replace") if patch_path.exists() else ""
    changed_files = re.findall(r"^diff --git a/(.*?) b/", patch, re.MULTILINE)
    additions = sum(
        1
        for line in patch.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    deletions = sum(
        1
        for line in patch.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    return {
        "path": str(patch_path),
        "bytes": len(patch.encode()),
        "changed_files": changed_files,
        "additions": additions,
        "deletions": deletions,
        "excerpt": patch[:12_000],
    }


def message_text(message: dict[str, Any]) -> str:
    """Flatten Pi message text content for marker and error analysis."""
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


def tool_argument_summary(arguments: Any) -> str:
    """Render bounded tool arguments without dropping searchable paths or commands."""
    rendered = json.dumps(arguments, sort_keys=True, ensure_ascii=False)
    return rendered[:1_200]


def load_session_records(result_root: Path) -> list[dict[str, Any]]:
    """Load native Pi session records in their recorded order."""
    records: list[dict[str, Any]] = []
    for session_path in sorted((result_root / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def is_validation_command(arguments: Any) -> bool:
    """Identify test/build/type-check commands from Bash tool arguments."""
    rendered = json.dumps(arguments, sort_keys=True).lower()
    return bool(
        re.search(
            r"pytest|go test|npm (?:test|run)|pnpm|yarn|bun test|cargo test|ruff|mypy|ty check|tsc|make test|gradle.*test",
            rendered,
        )
    )


def build_session_evidence(result_root: Path) -> dict[str, Any]:
    """Build a bounded tool timeline and stage ledger from a native Pi session."""
    records = load_session_records(result_root)
    result_by_call: dict[str, dict[str, Any]] = {}
    reaudit_record_index: int | None = None
    user_messages = 0
    for index, record in enumerate(records):
        message = record.get("message", {})
        if record.get("type") != "message":
            continue
        if message.get("role") == "user":
            user_messages += 1
            if "Re-audit every requirement" in message_text(message):
                reaudit_record_index = index
        if message.get("role") == "toolResult":
            result_by_call[str(message.get("toolCallId"))] = message

    timeline: list[dict[str, Any]] = []
    successful_read_paths: list[str] = []
    for record_index, record in enumerate(records):
        message = record.get("message", {})
        if record.get("type") != "message" or message.get("role") != "assistant":
            continue
        for item in message.get("content", []):
            if not isinstance(item, dict) or item.get("type") != "toolCall":
                continue
            call_id = str(item.get("id"))
            tool_name = str(item.get("name"))
            arguments = item.get("arguments", {})
            tool_result = result_by_call.get(call_id)
            result_text = message_text(tool_result or {})
            after_reaudit = (
                reaudit_record_index is not None and record_index > reaudit_record_index
            )
            entry = {
                "ordinal": len(timeline) + 1,
                "record_index": record_index,
                "timestamp": message.get("timestamp"),
                "tool": tool_name,
                "arguments": tool_argument_summary(arguments),
                "after_reaudit": after_reaudit,
                "result_state": (
                    "missing"
                    if tool_result is None
                    else "error"
                    if tool_result.get("isError")
                    else "ok"
                ),
                "result_excerpt": result_text[:800],
            }
            timeline.append(entry)
            if (
                tool_name == "read"
                and tool_result is not None
                and not tool_result.get("isError")
                and isinstance(arguments, dict)
                and arguments.get("path")
            ):
                successful_read_paths.append(str(arguments["path"]))

    tool_counts = Counter(entry["tool"] for entry in timeline)
    error_counts = Counter(
        entry["tool"] for entry in timeline if entry["result_state"] == "error"
    )
    post_check = [entry for entry in timeline if entry["after_reaudit"]]
    mutation_entries = [
        entry for entry in timeline if entry["tool"] in {"edit", "write"}
    ]
    validation_entries = [
        entry
        for entry in timeline
        if entry["tool"] == "bash" and is_validation_command(entry["arguments"])
    ]
    unique_reads = set(successful_read_paths)
    return {
        "record_count": len(records),
        "user_messages": user_messages,
        "reaudit_delivered": reaudit_record_index is not None,
        "tool_counts": dict(tool_counts),
        "tool_error_counts": dict(error_counts),
        "tool_result_errors": sum(error_counts.values()),
        "successful_exact_reads": len(successful_read_paths),
        "unique_successful_exact_reads": len(unique_reads),
        "repeated_successful_reads": len(successful_read_paths) - len(unique_reads),
        "first_mutation_ordinal": (
            mutation_entries[0]["ordinal"] if mutation_entries else None
        ),
        "first_validation_ordinal": (
            validation_entries[0]["ordinal"] if validation_entries else None
        ),
        "last_validation_ordinal": (
            validation_entries[-1]["ordinal"] if validation_entries else None
        ),
        "post_check_tool_calls": len(post_check),
        "post_check_bash_calls": sum(entry["tool"] == "bash" for entry in post_check),
        "post_check_mutation_calls": sum(
            entry["tool"] in {"edit", "write"} for entry in post_check
        ),
        "unmatched_tool_calls": sum(
            entry["result_state"] == "missing" for entry in timeline
        ),
        "timeline": timeline,
    }


def verifier_evidence(result_root: Path) -> dict[str, Any]:
    """Extract failed tests and bounded verifier logs without re-running grading."""
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
    return {
        "failed_test_count": len(failed_tests),
        "failed_tests": failed_tests,
        "log_excerpts": excerpts,
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
    """Collect one side of a trajectory packet from immutable artifacts."""
    artifact_root = result_directory(row)
    metrics = {
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
        ]
    }
    session = build_session_evidence(artifact_root)
    return {
        "result_path": str(artifact_root / "result.json"),
        "status": result_status(row),
        "metrics": metrics,
        "patch": patch_summary(artifact_root),
        "session": session,
        "verifier": verifier_evidence(artifact_root),
        "bash_timeout_trace": timeout_trace_evidence(artifact_root),
        "stage_ledger": {
            "initialization": f"{session['user_messages']} user message(s); {session['tool_counts']}",
            "contract_and_seam": (
                f"{session['unique_successful_exact_reads']} unique successful exact reads; "
                f"first mutation tool #{session['first_mutation_ordinal']}"
            ),
            "implementation": (
                f"changed {len(patch_summary(artifact_root)['changed_files'])} files; "
                f"{patch_summary(artifact_root)['additions']} additions and "
                f"{patch_summary(artifact_root)['deletions']} deletions"
            ),
            "validation": (
                f"first validation tool #{session['first_validation_ordinal']}; "
                f"last validation tool #{session['last_validation_ordinal']}"
            ),
            "completion_audit": (
                f"re-audit={session['reaudit_delivered']}; "
                f"post-check tools={session['post_check_tool_calls']}; "
                f"post-check mutations={session['post_check_mutation_calls']}"
            ),
            "termination": (
                f"agent_exit={row.get('agent_exit')}; "
                f"verifier_exit={row.get('verifier_exit')}"
            ),
        },
    }


def packet_selected(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Apply the predeclared timeout or 25-point F2P packet trigger."""
    if has_timeout(left) or has_timeout(right):
        return True
    if is_invalid(left) or is_invalid(right):
        return False
    return abs(float(right["f2p"]) - float(left["f2p"])) >= MATERIAL_F2P_DELTA


def write_trajectory_packets(
    output_dir: Path,
    metadata_by_task: dict[str, dict[str, str]],
    baseline: dict[tuple[str, int], dict[str, Any]],
    pi_check: dict[tuple[str, int], dict[str, Any]],
) -> dict[tuple[str, int], str]:
    """Write one reviewable JSON packet for every selected paired cell."""
    packet_dir = output_dir / "packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_links: dict[tuple[str, int], str] = {}
    for key in sorted(baseline):
        left = baseline[key]
        right = pi_check[key]
        if not packet_selected(left, right):
            continue
        classification = PACKET_CLASSIFICATIONS.get(key)
        if classification is None:
            raise ValueError(f"Missing packet classification for {key}")
        task, rep = key
        packet = {
            "schema_version": 1,
            "selection_rule": (
                "timeout on either side, or mutually valid absolute F2P delta >= 0.25"
            ),
            "task": task,
            "rep": rep,
            **metadata_by_task[task],
            "comparison_roles": {
                "baseline": "same-model config control",
                "pi_check": "same-model config control with re-audit plus Bash timeout",
            },
            "classification": classification,
            "paired_deltas": {
                metric: (
                    float(right[metric]) - float(left[metric])
                    if isinstance(left.get(metric), int | float)
                    and isinstance(right.get(metric), int | float)
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
            "baseline": result_packet_side(left),
            "pi_check": result_packet_side(right),
        }
        filename = f"{task}--rep{rep}.json"
        (packet_dir / filename).write_text(json.dumps(packet, indent=2, sort_keys=True))
        packet_links[key] = f"packets/{filename}"
    if len(packet_links) != len(PACKET_CLASSIFICATIONS):
        raise ValueError(
            "Qwen-AgentWorld packet selection changed: "
            f"expected {len(PACKET_CLASSIFICATIONS)} packets; found {len(packet_links)}"
        )
    return packet_links


def classify_tool_errors(rows: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    """Classify tool-result errors by tool and concrete cause."""
    calls: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    causes: Counter[str] = Counter()
    for row in rows.values():
        records = load_session_records(result_directory(row))
        for record in records:
            message = record.get("message", {})
            if record.get("type") != "message" or message.get("role") != "toolResult":
                continue
            tool = str(message.get("toolName"))
            calls[tool] += 1
            if not message.get("isError"):
                continue
            errors[tool] += 1
            text = message_text(message).lower()
            if tool == "bash":
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
    return {
        "calls": dict(calls),
        "errors": dict(errors),
        "causes": dict(causes),
        "total_calls": sum(calls.values()),
        "total_errors": sum(errors.values()),
    }


def verify_treatment_delivery(
    pi_check: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Verify request shape, re-audit marker, and timeout trace in all treatment cells."""
    delivered = 0
    request_shape = 0
    reaudit = 0
    timeout_trace = 0
    post_check_tools = 0
    post_check_mutations = 0
    cells_with_post_check_mutation = 0
    for row in pi_check.values():
        artifact_root = result_directory(row)
        request_paths = sorted(
            (artifact_root / "initial_context").glob("provider_request_*.json")
        )
        request = json.loads(request_paths[0].read_text()) if request_paths else {}
        shape_matches = (
            request.get("model") == "qwen-agentworld-35b-a3b"
            and request.get("max_tokens") == 65_536
            and request.get("temperature") == 0.6
            and request.get("top_p") == 0.95
            and request.get("top_k") == 20
            and request.get("min_p") == 0
            and request.get("repetition_penalty") == 1
            and request.get("chat_template_kwargs")
            == {"enable_thinking": True, "preserve_thinking": True}
        )
        session = build_session_evidence(artifact_root)
        trace = timeout_trace_evidence(artifact_root)
        request_shape += int(shape_matches)
        reaudit += int(session["reaudit_delivered"])
        timeout_trace += int(trace["present"])
        post_check_tools += int(session["post_check_tool_calls"])
        post_check_mutations += int(session["post_check_mutation_calls"])
        cells_with_post_check_mutation += int(session["post_check_mutation_calls"] > 0)
        delivered += int(
            shape_matches and session["reaudit_delivered"] and trace["present"]
        )
    return {
        "classification": "delivered"
        if delivered == EXPECTED_PAIR_COUNT
        else "missing",
        "delivered_cells": delivered,
        "request_shape_cells": request_shape,
        "reaudit_cells": reaudit,
        "timeout_trace_cells": timeout_trace,
        "post_check_tool_calls": post_check_tools,
        "post_check_mutations": post_check_mutations,
        "cells_with_post_check_mutation": cells_with_post_check_mutation,
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
    """Render a compact outcome tag."""
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
    pi_check: dict[tuple[str, int], dict[str, Any]],
    packet_links: dict[tuple[str, int], str],
) -> str:
    """Render all 36 matched task-rep outcomes before any packet filtering."""
    rows: list[str] = []
    for key in sorted(baseline):
        task, rep = key
        left = baseline[key]
        right = pi_check[key]
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


def build_task_comparison_rows(
    baseline: dict[tuple[str, int], dict[str, Any]],
    pi_check: dict[tuple[str, int], dict[str, Any]],
) -> str:
    """Render per-task paired-valid F2P and reliability movement."""
    rendered: list[str] = []
    for task in sorted({key[0] for key in baseline}):
        keys = [
            key
            for key in baseline
            if key[0] == task
            and not is_invalid(baseline[key])
            and not is_invalid(pi_check[key])
        ]
        invalid_left = sum(is_invalid(baseline[(task, rep)]) for rep in range(3))
        invalid_right = sum(is_invalid(pi_check[(task, rep)]) for rep in range(3))
        if keys:
            left_f2p = statistics.mean(float(baseline[key]["f2p"]) for key in keys)
            right_f2p = statistics.mean(float(pi_check[key]["f2p"]) for key in keys)
            delta = right_f2p - left_f2p
            values = (
                f"<td class='num'>{format_percent(left_f2p)}</td>"
                f"<td class='num'>{format_percent(right_f2p)}</td>"
                f"<td class='num delta {'up' if delta > 0 else 'down' if delta < 0 else ''}'>{format_percent(delta, signed=True)}</td>"
            )
        else:
            values = (
                "<td class='num'>—</td><td class='num'>—</td><td class='num'>—</td>"
            )
        rendered.append(
            "<tr>"
            f"<td class='task'>{html.escape(task)}</td>"
            f"<td class='num'>{len(keys)}/3</td>"
            f"{values}"
            f"<td class='num'>{invalid_left} → {invalid_right}</td>"
            "</tr>"
        )
    return "\n".join(rendered)


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
            f"<a href='{html.escape(packet_links[key])}'>Open complete trajectory packet →</a>"
            "</article>"
        )
    return "\n".join(cards)


def render_tool_error_rows(
    baseline_errors: dict[str, Any],
    pi_check_errors: dict[str, Any],
) -> str:
    """Render tool error causes with tool-specific denominators."""
    tool_for_cause = {
        "shell nonzero / diagnostic": "bash",
        "malformed edit arguments": "edit",
        "edit target mismatch": "edit",
        "edit no-op / other": "edit",
        "read missing file": "read",
        "read range error": "read",
        "read other": "read",
    }
    causes = sorted(set(baseline_errors["causes"]) | set(pi_check_errors["causes"]))
    rows = []
    for cause in causes:
        tool = tool_for_cause.get(cause, cause.split()[0])
        baseline_count = int(baseline_errors["causes"].get(cause, 0))
        pi_check_count = int(pi_check_errors["causes"].get(cause, 0))
        baseline_denominator = int(baseline_errors["calls"].get(tool, 0))
        pi_check_denominator = int(pi_check_errors["calls"].get(tool, 0))
        rows.append(
            "<tr>"
            f"<td>{html.escape(cause)}</td>"
            f"<td class='num'>{baseline_count}/{baseline_denominator} ({baseline_count / baseline_denominator:.1%})</td>"
            f"<td class='num'>{pi_check_count}/{pi_check_denominator} ({pi_check_count / pi_check_denominator:.1%})</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_comparison_report(
    baseline: dict[tuple[str, int], dict[str, Any]],
    pi_check: dict[tuple[str, int], dict[str, Any]],
    packet_links: dict[tuple[str, int], str],
    delivery: dict[str, Any],
    baseline_errors: dict[str, Any],
    pi_check_errors: dict[str, Any],
) -> str:
    """Render the self-contained evidence-first comparison report."""
    keys = sorted(baseline)
    baseline_rows = [baseline[key] for key in keys]
    pi_check_rows = [pi_check[key] for key in keys]
    mutually_valid = [
        key
        for key in keys
        if not is_invalid(baseline[key]) and not is_invalid(pi_check[key])
    ]
    baseline_mutual = [baseline[key] for key in mutually_valid]
    pi_check_mutual = [pi_check[key] for key in mutually_valid]
    baseline_f2p_all = weighted_grade(baseline_rows, "f2p")
    pi_check_f2p_all = weighted_grade(pi_check_rows, "f2p")
    baseline_f2p_mutual = weighted_grade(baseline_mutual, "f2p")
    pi_check_f2p_mutual = weighted_grade(pi_check_mutual, "f2p")
    baseline_p2p_mutual = weighted_grade(baseline_mutual, "p2p")
    pi_check_p2p_mutual = weighted_grade(pi_check_mutual, "p2p")
    f2p_deltas = [
        float(pi_check[key]["f2p"]) - float(baseline[key]["f2p"])
        for key in mutually_valid
    ]
    partial_all_deltas = [
        float(pi_check[key]["reward_partial"]) - float(baseline[key]["reward_partial"])
        for key in keys
    ]
    partial_mutual_deltas = [
        float(pi_check[key]["reward_partial"]) - float(baseline[key]["reward_partial"])
        for key in mutually_valid
    ]
    f2p_interval = paired_bootstrap_interval(f2p_deltas)
    partial_all_interval = paired_bootstrap_interval(partial_all_deltas)
    partial_mutual_interval = paired_bootstrap_interval(partial_mutual_deltas)

    right_only_solves = sum(
        pi_check[key].get("reward_binary") == 1
        and baseline[key].get("reward_binary") != 1
        for key in keys
    )
    left_only_solves = sum(
        baseline[key].get("reward_binary") == 1
        and pi_check[key].get("reward_binary") != 1
        for key in keys
    )
    recovered_invalid = sum(
        is_invalid(baseline[key]) and not is_invalid(pi_check[key]) for key in keys
    )
    new_invalid = sum(
        not is_invalid(baseline[key]) and is_invalid(pi_check[key]) for key in keys
    )
    both_invalid = sum(
        is_invalid(baseline[key]) and is_invalid(pi_check[key]) for key in keys
    )
    total_token_delta = (
        sum(int(row.get("total_tokens") or 0) for row in pi_check_rows)
        / sum(int(row.get("total_tokens") or 0) for row in baseline_rows)
        - 1
    )
    total_tool_delta = (
        sum(int(row.get("tool_calls") or 0) for row in pi_check_rows)
        / sum(int(row.get("tool_calls") or 0) for row in baseline_rows)
        - 1
    )
    wall_delta = (
        sum(float(row.get("agent_wall_s") or 0) for row in pi_check_rows)
        / sum(float(row.get("agent_wall_s") or 0) for row in baseline_rows)
        - 1
    )
    complete_rows = render_complete_pair_rows(baseline, pi_check, packet_links)
    task_rows = build_task_comparison_rows(baseline, pi_check)
    packet_cards = render_packet_cards(packet_links)
    selected_packet_task_count = len({key[0] for key in packet_links})
    tool_error_rows = render_tool_error_rows(baseline_errors, pi_check_errors)

    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="icon" href="data:," />
<title>Qwen-AgentWorld pi-check vs baseline · 12_v2</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#a86f00;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08);--radius:24px;--max:1320px}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),linear-gradient(180deg,#f9fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,sans-serif;line-height:1.5}} .wrap{{max-width:var(--max);margin:auto;padding:28px 20px 48px}} .hero,section{{background:rgba(255,255,255,.93);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}} .hero{{padding:clamp(24px,4vw,42px)}} .eyebrow{{font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#1d3fb8;background:#eef3ff;padding:8px 12px;border-radius:999px;display:inline-block}} h1,h2{{letter-spacing:-.035em;line-height:1.08}} h1{{font-size:clamp(2.1rem,5vw,4.2rem);max-width:16ch;margin:14px 0}} h2{{margin:0;font-size:clamp(1.4rem,2.5vw,2rem)}} h3{{line-height:1.25}} .subtitle,.muted{{color:var(--muted)}} .subtitle{{max-width:82ch;font-size:1.05rem}} .pillrow{{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}} .pill,.tag{{display:inline-flex;border-radius:999px;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:7px 10px}} .pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}} .pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}} .pill.caution,.tag.caution{{background:var(--amber-soft);color:var(--amber)}} .pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}} .stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:13px;margin-top:25px}} .stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}} .stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}} .stat .value{{display:block;font-size:clamp(1.35rem,2.3vw,2rem);font-weight:900;margin-top:9px}} .stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:6px}} section{{padding:clamp(18px,3vw,28px);margin-top:20px}} .section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:18px}} .section-head p{{margin:6px 0 0;max-width:85ch;color:var(--muted)}} .callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin-top:14px}} .callout.bad{{border-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}} .callout.good{{border-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}} .callout.caution{{border-color:var(--amber);background:linear-gradient(90deg,#fff8e7,#fff)}} .grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .card,.packet-card{{border:1px solid var(--line);border-radius:18px;padding:18px;background:var(--surface)}} .card h3,.packet-card h3{{margin:9px 0}} .packet-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}} .table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:18px}} table{{width:100%;border-collapse:collapse;min-width:980px}} th,td{{padding:10px 11px;border-bottom:1px solid #e7edf5;text-align:left;vertical-align:middle}} th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:#fbfcff;position:sticky;top:0}} td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}} td.task{{font-family:ui-monospace,monospace;font-size:.82rem;max-width:310px}} .delta.up{{color:var(--green);font-weight:800}} .delta.down{{color:var(--red);font-weight:800}} a{{color:#244bd5;font-weight:750;text-decoration:none}} a:hover{{text-decoration:underline}} code{{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}} .foot{{color:var(--muted);font-size:.84rem;text-align:center;margin-top:24px}} @media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid-2,.packet-grid{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">Same local model · 36 matched pairs · 12_v2 · high thinking</span>
<h1>Which scaffolds helped Qwen-AgentWorld—and where they broke down.</h1>
<p class="subtitle">On this local model and subset, pi-check plus the 360-second Bash timeout moved weighted F2P from {baseline_f2p_mutual[2]:.1%} to {pi_check_f2p_mutual[2]:.1%} on the 30 pairs where both sides graded, but produced no strict solve. It recovered two baseline agent hangs, introduced three new verifier timeouts, and used {total_token_delta:.1%} more tokens. These trajectories isolate scaffold opportunities for Qwen-AgentWorld; they do not estimate pi-check's effect on other models.</p>
<div class="pillrow"><span class="pill bad">0 → 0 strict solves</span><span class="pill good">{(pi_check_f2p_mutual[2] - baseline_f2p_mutual[2]) * 100:+.1f} pp matched weighted F2P</span><span class="pill bad">3 new verifier timeouts</span><span class="pill caution">{format_percent(total_token_delta, signed=True)} tokens</span><span class="pill neutral">delivery 36/36</span></div>
<div class="stats">
<div class="stat"><span class="label">Strict result</span><span class="value">0 / 36</span><span class="sub">both configs; no solve flips</span></div>
<div class="stat"><span class="label">Mutually valid F2P</span><span class="value">{baseline_f2p_mutual[2]:.1%} → {pi_check_f2p_mutual[2]:.1%}</span><span class="sub">same 1,290 tests per side</span></div>
<div class="stat"><span class="label">Invalid outcomes</span><span class="value">3 → 4</span><span class="sub">2 recovered, 3 newly lost, 1 shared</span></div>
<div class="stat"><span class="label">Tokens</span><span class="value">{sum(int(row.get("total_tokens") or 0) for row in baseline_rows) / 1_000_000:.1f}M → {sum(int(row.get("total_tokens") or 0) for row in pi_check_rows) / 1_000_000:.1f}M</span><span class="sub">{format_percent(total_token_delta, signed=True)} cumulative</span></div>
<div class="stat"><span class="label">Post-check action</span><span class="value">{delivery["cells_with_post_check_mutation"]}/36</span><span class="sub">cells changed code after re-audit</span></div>
</div></header>

<section><div class="section-head"><div><h2>What this run says about scaffolding</h2><p>Question answered: which support mechanisms appear most useful for this model, and which failure modes remain?</p></div></div>
<div class="callout"><strong>Scope:</strong> this is one local model, one 12-task subset, and three reps. It cannot support a cross-model judgment about pi-check. It can show how Qwen-AgentWorld responded to this combined re-audit and timeout scaffold.</div>
<div class="callout good"><strong>Bounded tool execution produced the clearest gain.</strong> LangChain reps 1 and 2 changed from one-hour agent timeouts to valid results with 72% and 62% F2P. Because this config bundles timeout control with pi-check, a timeout-only config is needed to measure that mechanism cleanly.</div>
<div class="callout caution"><strong>The independent re-audit generated effort more reliably than repair.</strong> The combined config added {format_percent(total_tool_delta, signed=True)} tool calls, {format_percent(total_token_delta, signed=True)} tokens, and {format_percent(wall_delta, signed=True)} agent wall time, but only {delivery["cells_with_post_check_mutation"]}/36 cells changed code after the re-audit. For this model, the likely scaffold gap is converting validation evidence into a bounded repair decision.</div>
<div class="callout"><strong>The feature signal is useful but uncertain.</strong> On mutually valid pairs, mean paired F2P moved {statistics.mean(f2p_deltas):+.3f} (cell bootstrap 95% interval {f2p_interval[0]:+.3f} to {f2p_interval[1]:+.3f}). Weighted F2P gained 100/1,290 tests, while three new verifier timeouts exposed a separate concurrency and completion-control weakness.</div></section>

<section><div class="section-head"><div><h2>Complete 36-pair outcome table</h2><p>All trajectories appear here before packet filtering. F2P and P2P are per-rep pass ratios; invalid outcomes have no grade. Thirteen packet links follow the predeclared timeout-or-25-point rule.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Baseline</th><th class="num">Base F2P</th><th class="num">Base P2P</th><th>Pi-check</th><th class="num">Check F2P</th><th class="num">Check P2P</th><th class="num">Δ F2P</th><th>Evidence</th></tr></thead><tbody>{complete_rows}</tbody></table></div></section>

<section><div class="section-head"><div><h2>Net versus churn</h2><p>Strict score did not move, but reliability and feature tests churned.</p></div></div>
<div class="grid-2"><div class="card"><h3>Observed outcomes</h3><ul><li>Strict flips: {left_only_solves} baseline-only, {right_only_solves} pi-check-only, 0 both solved.</li><li>Invalid discordance: {recovered_invalid} baseline invalid → pi-check valid; {new_invalid} baseline valid → pi-check invalid; {both_invalid} invalid on both.</li><li>Mutually valid F2P: {sum(delta > 0 for delta in f2p_deltas)} improved, {sum(delta < 0 for delta in f2p_deltas)} worsened, {sum(delta == 0 for delta in f2p_deltas)} tied.</li><li>All-pair partial: {sum(delta > 0 for delta in partial_all_deltas)} improved, {sum(delta < 0 for delta in partial_all_deltas)} worsened, {sum(delta == 0 for delta in partial_all_deltas)} tied.</li></ul></div>
<div class="card"><h3>Timeout sensitivity</h3><ul><li>All 36 pairs: partial Δ {statistics.mean(partial_all_deltas):+.3f}, 95% interval {partial_all_interval[0]:+.3f} to {partial_all_interval[1]:+.3f}.</li><li>30 mutually valid pairs: partial Δ {statistics.mean(partial_mutual_deltas):+.3f}, 95% interval {partial_mutual_interval[0]:+.3f} to {partial_mutual_interval[1]:+.3f}.</li><li>All graded tests: F2P {baseline_f2p_all[0]}/{baseline_f2p_all[1]} ({baseline_f2p_all[2]:.1%}) → {pi_check_f2p_all[0]}/{pi_check_f2p_all[1]} ({pi_check_f2p_all[2]:.1%}); denominators differ because of invalid reps.</li><li>Mutually valid P2P: {baseline_p2p_mutual[2]:.1%} → {pi_check_p2p_mutual[2]:.1%}; regression safety stayed essentially flat.</li></ul></div></div></section>

<section><div class="section-head"><div><h2>Task-level capability shape</h2><p>Means use only reps that graded on both sides. LangChain and Mobly have no mutually valid rep because their timeout sets do not overlap cleanly.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Valid pairs</th><th class="num">Baseline F2P</th><th class="num">Pi-check F2P</th><th class="num">Δ F2P</th><th class="num">Invalid base → check</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<div class="callout good"><strong>Observed feature gains:</strong> SQL Formatter, Participle, Obsidian, and Dateutil improved while keeping P2P near-perfect. SQL reps 0 and 1 made no post-check mutation, so their gains show trajectory variance rather than a pi-check mechanism.</div>
<div class="callout bad"><strong>Repeated validation-to-repair failure:</strong> Goreleaser fell from 10/29 to 2/29 F2P in reps 0 and 1. The re-audit ran many checks but made no code change. A useful scaffold for this model must turn failed evidence into a concrete repair or stop without adding more validation loops.</div></section>

<section><div class="section-head"><div><h2>Config delivery and execution substrate</h2><p>Every pi-check cell received the intended config, so missing delivery does not explain the outcome.</p></div></div>
<div class="grid-2"><div class="card"><h3>Delivery: {html.escape(str(delivery["classification"]))}</h3><ul><li>Exact Qwen request shape: {delivery["request_shape_cells"]}/36.</li><li>Independent re-audit marker: {delivery["reaudit_cells"]}/36.</li><li>Bash-timeout trace: {delivery["timeout_trace_cells"]}/36.</li><li>Post-check activity: {delivery["post_check_tool_calls"]} tool calls, including {delivery["post_check_mutations"]} mutations across {delivery["cells_with_post_check_mutation"]} cells.</li></ul></div>
<div class="card"><h3>No serving-path failure</h3><p>All cells used <code>local-vllm/qwen-agentworld-35b-a3b</code>, high thinking, 65,536 max output tokens, <code>enable_thinking=true</code>, <code>preserve_thinking=true</code>, temperature 0.6, top-p 0.95, and top-k 20. No evidence supports changing the provider path, reasoning parser, or output ceiling.</p></div></div></section>

<section><div class="section-head"><div><h2>Tool-result errors by cause</h2><p>These are recorded tool results, not provider parser failures. A failing test command is useful feedback and still records <code>isError=true</code>.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Cause</th><th class="num">Baseline count / tool calls</th><th class="num">Pi-check count / tool calls</th></tr></thead><tbody>{tool_error_rows}</tbody></table></div>
<div class="callout"><strong>Total:</strong> baseline {baseline_errors["total_errors"]}/{baseline_errors["total_calls"]} ({baseline_errors["total_errors"] / baseline_errors["total_calls"]:.1%}); pi-check {pi_check_errors["total_errors"]}/{pi_check_errors["total_calls"]} ({pi_check_errors["total_errors"] / pi_check_errors["total_calls"]:.1%}). Shell nonzero results dominate. Malformed <code>edit</code> arguments also rose from {baseline_errors["causes"].get("malformed edit arguments", 0)}/{baseline_errors["calls"].get("edit", 0)} to {pi_check_errors["causes"].get("malformed edit arguments", 0)}/{pi_check_errors["calls"].get("edit", 0)}, a model schema-adherence cost worth targeting separately.</div></section>

<section><div class="section-head"><div><h2>Thirteen trajectory packets</h2><p>Rule: select every pair with an agent/verifier timeout on either side, plus mutually valid pairs with |ΔF2P| ≥ 0.25. Each JSON packet contains both results, patches, failed tests, stage ledgers, timeout traces, and bounded tool timelines.</p></div></div><div class="packet-grid">{packet_cards}</div></section>

<section><div class="section-head"><div><h2>Scaffoldability ledger</h2><p>The next experiments should separate mechanisms instead of adding more generic effort.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Observed weakness</th><th>Layer</th><th>Smallest support</th><th>Success criterion</th></tr></thead><tbody>
<tr><td>Unbounded Bash ended baseline LangChain reps 1 and 2.</td><td>Execution control</td><td>Timeout-only config with the same 360-second default and no re-audit.</td><td>0 agent timeouts, no increase in verifier timeouts, equal-or-better strict/F2P.</td></tr>
<tr><td>Re-audit ran 786 extra tools but changed code in only 14/36 cells.</td><td>Execution control / validation gap</td><td>A bounded requirement ledger that stops after targeted evidence and converts each failing requirement into one repair decision.</td><td>At least one strict solve or a predeclared F2P gain without >15% token growth.</td></tr>
<tr><td>Mobly and LangChain candidate patches blocked verifier completion.</td><td>Repository understanding / missing invariant</td><td>Concurrency-specific completion gate: targeted deadlock/cleanup tests must terminate before final response.</td><td>No new verifier timeouts on the six timeout packet cells.</td></tr>
<tr><td>Malformed edit calls rose during the longer treatment trajectories.</td><td>Tool protocol</td><td>Repair feedback or schema-focused edit wrapper, tested independently of pi-check.</td><td>Malformed edit rate below baseline without more no-op mutations.</td></tr>
</tbody></table></div>
<div class="callout caution"><strong>Non-targets:</strong> do not raise the output ceiling, extend the one-hour agent budget, or change serving parameters. No length stop or request-shape failure supports those changes. Do not attribute SQL gains to pi-check: both material SQL gains were already in the patch before the re-audit.</div></section>

<section><div class="section-head"><div><h2>Scaffold implications for Qwen-AgentWorld</h2></div></div>
<div class="callout good"><strong>Execution control is the highest-confidence scaffold from this run.</strong> The Bash timeout recovered both terminal LangChain hangs. Test it alone so its effect is not confounded with re-audit behavior.</div>
<div class="callout caution"><strong>The next re-audit scaffold should be more directive and bounded for this model.</strong> It should track unresolved requirements, connect each failed check to one repair decision, run targeted tests, and stop. More generic validation effort alone did not reliably change the patch.</div>
<div class="callout bad"><strong>Concurrency work needs a termination gate.</strong> The three new verifier timeouts point to missing deadlock, cleanup, or lifecycle checks on LangChain and Mobly patches. A scaffold should prove those targeted tests terminate before the agent declares completion.</div>
<div class="callout"><strong>Next mechanism comparison:</strong> baseline versus timeout-only versus timeout-plus a bounded requirement-led check, on the same 12_v2 × 3 cells. This tests which scaffold layer helps Qwen-AgentWorld without making any claim about pi-check's effect on frontier models.</div></section>
<div class="foot">Source: <code>results/{MODEL_LEAF}/{THINKING_LEVEL}/</code> · baseline <code>{BASELINE_CONFIG}</code> · comparison config <code>{PI_CHECK_CONFIG}</code><br />36 matched pairs, 72 full trajectories, 13 selected packet pairs across {selected_packet_task_count} tasks. Generated deterministically by <code>analysis/qwen-agentworld-picheck-vs-baseline-12v2/build_report.py</code>.</div>
</div></body></html>"""


def main() -> None:
    """Validate canonical inputs, write packets, and render the comparison report."""
    arguments = parse_report_arguments()
    baseline = load_config_results(arguments.results_root, BASELINE_CONFIG)
    pi_check = load_config_results(arguments.results_root, PI_CHECK_CONFIG)
    if set(baseline) != set(pi_check):
        raise ValueError("Qwen-AgentWorld comparison invalid: task-rep keys differ")
    metadata_by_task = {
        task: load_task_metadata(arguments.tasks_root, task)
        for task in sorted({key[0] for key in baseline})
    }
    output_dir = arguments.output.parent
    packet_links = write_trajectory_packets(
        output_dir,
        metadata_by_task,
        baseline,
        pi_check,
    )
    report = render_comparison_report(
        baseline,
        pi_check,
        packet_links,
        verify_treatment_delivery(pi_check),
        classify_tool_errors(baseline),
        classify_tool_errors(pi_check),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(report)
    print(arguments.output)


if __name__ == "__main__":
    main()
