#!/usr/bin/env python3
"""Build the GPT-5.6 Luna all-thinking pi-check matched comparison report."""

from __future__ import annotations

import collections
import html
import json
import math
import random
import re
import statistics
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from render_all_thinking_report import render_all_thinking_report

REPO = Path(__file__).resolve().parents[2]
CANONICAL_REPO = REPO.parents[1] if REPO.parent.name == ".worktrees" else REPO
REPORT_DIR = Path(__file__).resolve().parent
PACKET_DIR = REPORT_DIR / "packets"
RESULTS_ROOT = CANONICAL_REPO / "results" / "gpt-5.6-luna"
TASKS_ROOT = CANONICAL_REPO.parent / "deep-swe" / "tasks"
SUBSET_PATH = REPO / "subsets" / "12_v2.txt"
SUMMARY_PATH = REPORT_DIR / "summary.json"
OUT_PATH = REPORT_DIR / "index.html"
LEVELS = ("low", "high", "max")
LEFT_CONFIG = "baseline@1.0.0"
RIGHT_CONFIG = "pi-check@1.0.1"
CONFIGS = (LEFT_CONFIG, RIGHT_CONFIG)
CHECK_MARKER = "Re-audit"
MATERIAL_THRESHOLD = 0.25
EXPECTED_PLAN_IDENTITIES = {
    "low": {"sha256:6c6cbdff0e20147ba9dfca670e1459f2b903a10451d7a8524049924a9bbb0f7f"},
    "high": {
        "sha256:6ecbadc5a8520ca629cc6d474d9b908019e470f7841895259ca2c8c024f09eaf",
        "sha256:2317828592fad13528ad71a8686917b4e62138354226fdc74354b27671b7e86b",
    },
    "max": {"sha256:38bc68c7cb8412b8464de7bfb3ecf6e270354c31a8fd132efc4620ae7c7d1cb1"},
}


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def percentage_points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def ratio_change(right: float, left: float) -> float:
    return right / left - 1 if left else math.nan


def exact_mcnemar_p(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if not discordant:
        return 1.0
    tail = min(left_only, right_only)
    probability = (
        2 * sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    )
    return min(1.0, probability)


def load_task_metadata(task: str) -> dict[str, str]:
    metadata = {"title": task, "language": "unknown"}
    path = TASKS_ROOT / task / "task.toml"
    if path.exists():
        with path.open("rb") as file:
            raw = tomllib.load(file).get("metadata", {})
        metadata["title"] = str(raw.get("display_title") or task)
        metadata["language"] = str(raw.get("language") or "unknown")
    return metadata


def load_matched_results() -> tuple[
    list[str], dict[tuple[str, str, str, int], dict[str, Any]]
]:
    tasks = [
        line.strip() for line in SUBSET_PATH.read_text().splitlines() if line.strip()
    ]
    records: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for level in LEVELS:
        for config in CONFIGS:
            root = RESULTS_ROOT / level / config
            for task in tasks:
                for rep in range(3):
                    path = root / task / f"rep{rep}" / "result.json"
                    if not path.exists():
                        raise SystemExit(f"Missing matched result: {path}")
                    result = json.loads(path.read_text())
                    key = (level, config, task, rep)
                    if result.get("task") != task or result.get("rep") != rep:
                        raise SystemExit(f"Result identity mismatch: {path}")
                    if result.get("model") != "openai-codex/gpt-5.6-luna":
                        raise SystemExit(f"Model mismatch: {path}")
                    if result.get("thinking_level") != level:
                        raise SystemExit(f"Thinking mismatch: {path}")
                    records[key] = result
    return tasks, records


def cell_path(level: str, config: str, task: str, rep: int) -> Path:
    return RESULTS_ROOT / level / config / task / f"rep{rep}"


def read_session_trace(cell: Path) -> dict[str, Any]:
    session_paths = sorted((cell / "session").glob("*.jsonl"))
    trace: dict[str, Any] = {
        "session": None,
        "check_prompt_count": 0,
        "assistant_turns": 0,
        "post_check_turns": 0,
        "tool_counts": {},
        "post_check_tool_counts": {},
        "bash_commands": [],
        "test_commands": [],
        "last_stop_reason": None,
    }
    if not session_paths:
        return trace
    session_path = session_paths[-1]
    trace["session"] = str(session_path.relative_to(CANONICAL_REPO))
    tool_counts: collections.Counter[str] = collections.Counter()
    post_check_tool_counts: collections.Counter[str] = collections.Counter()
    bash_commands: list[str] = []
    test_commands: list[str] = []
    after_check = False
    for line in session_path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message") or {}
        content = message.get("content")
        text = (
            content
            if isinstance(content, str)
            else " ".join(
                str(part.get("text", ""))
                for part in (content or [])
                if isinstance(part, dict)
            )
        )
        if message.get("role") == "user" and CHECK_MARKER in text:
            trace["check_prompt_count"] += 1
            after_check = True
            continue
        if message.get("role") != "assistant":
            continue
        trace["assistant_turns"] += 1
        trace["last_stop_reason"] = message.get("stopReason")
        if after_check:
            trace["post_check_turns"] += 1
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "toolCall":
                continue
            tool_name = str(part.get("name") or "unknown")
            arguments = part.get("arguments") or {}
            tool_counts[tool_name] += 1
            if after_check:
                post_check_tool_counts[tool_name] += 1
            if tool_name == "bash":
                command = str(arguments.get("command") or "")
                bash_commands.append(command)
                if re.search(
                    r"\b(pytest|go test|npm test|pnpm test|vitest|cargo test|tsc|ruff|lint|test)\b",
                    command,
                ):
                    test_commands.append(command)
    trace["tool_counts"] = dict(tool_counts)
    trace["post_check_tool_counts"] = dict(post_check_tool_counts)
    trace["bash_commands"] = bash_commands[-60:]
    trace["test_commands"] = test_commands[-30:]
    return trace


def read_patch_stats(cell: Path) -> dict[str, Any]:
    path = cell / "artifacts" / "model.patch"
    text = path.read_text(errors="replace") if path.exists() else ""
    files: list[str] = []
    additions = 0
    deletions = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            fields = line.split()
            if len(fields) >= 4:
                files.append(fields[3].removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {
        "path": str(path.relative_to(CANONICAL_REPO)),
        "bytes": len(text.encode()),
        "files": files,
        "files_count": len(files),
        "additions": additions,
        "deletions": deletions,
        "changed_lines": additions + deletions,
        "excerpt": "\n".join(text.splitlines()[:120]),
    }


def read_verifier_evidence(cell: Path) -> dict[str, Any]:
    failed: list[dict[str, str]] = []
    ctrf_path = cell / "verifier" / "ctrf.json"
    if ctrf_path.exists():
        try:
            tests = (
                json.loads(ctrf_path.read_text()).get("results", {}).get("tests", [])
            )
            for test in tests:
                if str(test.get("status", "")).lower() in {"pass", "passed"}:
                    continue
                failed.append(
                    {
                        "name": str(
                            test.get("name") or test.get("testName") or "unknown"
                        ),
                        "message": str(test.get("message") or "")[:500],
                    }
                )
                if len(failed) == 12:
                    break
        except json.JSONDecodeError:
            failed.append({"name": "CTRF parse failure", "message": str(ctrf_path)})
    run_log = cell / "verifier" / "run.log"
    tail = ""
    if run_log.exists():
        tail = "\n".join(run_log.read_text(errors="replace").splitlines()[-50:])
    return {"failed_examples": failed, "run_log_tail": tail}


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "total_tokens",
        "cost_usd",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
        "launch_plan_identity",
    )
    return {field: result.get(field) for field in fields}


def packet_trigger_reasons(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if (left["reward_binary"] == 1) != (right["reward_binary"] == 1):
        reasons.append("binary flip")
    if (left["reward_binary"] < 0) != (right["reward_binary"] < 0):
        reasons.append("negative-reward discordance")
    if bool(left["agent_timed_out"]) != bool(right["agent_timed_out"]):
        reasons.append("agent-timeout discordance")
    if abs(left["reward_partial"] - right["reward_partial"]) >= MATERIAL_THRESHOLD:
        reasons.append(f"partial delta ≥ {MATERIAL_THRESHOLD:.2f}")
    for metric in ("f2p", "p2p"):
        if left.get(metric) is None or right.get(metric) is None:
            continue
        if abs(float(left[metric]) - float(right[metric])) >= MATERIAL_THRESHOLD:
            reasons.append(f"{metric} delta ≥ {MATERIAL_THRESHOLD:.2f}")
    return reasons


def classify_packet(
    level: str,
    task: str,
    rep: int,
    left: dict[str, Any],
    right: dict[str, Any],
    right_trace: dict[str, Any],
    left_verifier: dict[str, Any],
    right_verifier: dict[str, Any],
) -> dict[str, Any]:
    specific: dict[tuple[str, str, int], tuple[str, str, str, str]] = {
        ("low", "claude-code-by-agents-recursive-delegation", 1): (
            "resource exhaustion",
            "The pi-check verifier timed out after a delivered follow-up edit; baseline passed 7/7 feature and 31/31 preservation tests. Saved CTRF evidence also shows six delegation behaviors failing, so patch-linked nontermination is plausible but not proven.",
            "Treat verifier timeout as an explicit completion blocker and bound recursive-delegation validation before finalization.",
            "medium",
        ),
        ("low", "claude-code-by-agents-recursive-delegation", 2): (
            "under-implementation",
            "The pi-check patch passed only 1/7 feature tests while baseline passed 7/7; circular delegation, errors, empty results, unknown agents, and multi-level delegation remained broken after the follow-up edit.",
            "Re-audit recursive delegation as a behavior matrix, not one happy path.",
            "high",
        ),
        ("low", "goreleaser-retry-publish-auditing", 1): (
            "under-implementation",
            "Baseline missed seven retry and Retry-After behaviors (22/29 F2P). The follow-up made eight edits and reached 29/29 F2P plus 29/29 P2P.",
            "Keep the retry audit: enumerate temporary/permanent failure, cancellation, cap, and Retry-After cases before stopping.",
            "high",
        ),
        ("max", "superjson-error-stack-serialization", 2): (
            "cross-scope regression",
            "The pi-check follow-up passed all 80 feature tests but regressed the public-API invariant that errorStack=undefined behaves like omission; baseline passed the full verifier.",
            "After stack-option edits, rerun preservation cases for omitted and explicitly undefined options.",
            "high",
        ),
        ("max", "participle-grammar-conflict-analysis", 0): (
            "under-implementation",
            "Baseline missed the clean-grammar control case (90/91 F2P). The delivered follow-up reached 91/91 F2P and full preservation coverage.",
            "Keep a negative control proving clean grammars remain conflict-free.",
            "high",
        ),
        ("max", "claude-code-by-agents-recursive-delegation", 0): (
            "cross-scope regression",
            "Baseline passed 7/7 delegation behaviors; pi-check passed only 2/7 after the follow-up, missing execution, errors, empty output, circular delegation, and unknown-agent handling.",
            "Require the full recursive-delegation behavior matrix after any follow-up mutation.",
            "high",
        ),
        ("max", "claude-code-by-agents-recursive-delegation", 1): (
            "under-implementation",
            "Baseline passed 2/7 delegation behaviors. The pi-check follow-up reached 7/7 F2P and 31/31 P2P.",
            "Keep a bounded recursive-delegation audit covering every branch before finalization.",
            "high",
        ),
        ("max", "claude-code-by-agents-recursive-delegation", 2): (
            "cross-scope regression",
            "Baseline passed 7/7 delegation behaviors; pi-check passed only 2/7 after the follow-up, reproducing the broad delegation regression from rep0.",
            "Require the full recursive-delegation behavior matrix after any follow-up mutation.",
            "high",
        ),
        ("max", "adaptix-name-mapping-aliases", 2): (
            "under-implementation",
            "Baseline missed four alias-collision behaviors (40/44 F2P). The delivered follow-up reached 44/44 F2P with full preservation coverage.",
            "Audit alias collisions against primary keys and other fields before stopping.",
            "high",
        ),
        ("high", "adaptix-name-mapping-aliases", 1): (
            "under-implementation",
            "Baseline missed three alias-overlay and missing-field cases (41/44 F2P); the delivered follow-up reached 44/44 without losing preservation tests.",
            "Audit alias precedence and missing-field code generation as explicit cases.",
            "high",
        ),
        ("high", "claude-code-by-agents-recursive-delegation", 0): (
            "likely variance",
            "The pi-check trajectory missed five delegation behaviors, but the check stage made no edit or write. The losing patch therefore predates the configured follow-up.",
            "Do not attribute this loss to follow-up mutation; retain the behavior-matrix audit as a hypothesis.",
            "high",
        ),
        ("high", "claude-code-by-agents-recursive-delegation", 1): (
            "under-implementation",
            "Baseline passed 2/7 feature tests. The delivered follow-up edited the implementation and reached 7/7 F2P and 31/31 P2P.",
            "Keep a fresh recursive-delegation behavior matrix in the completion audit.",
            "high",
        ),
        ("high", "dateutil-rfc5545-timezone-interop", 0): (
            "missing invariant/guard",
            "Baseline serialized a tzical object representation instead of TZID=Custom/Zone. The follow-up corrected the last missing feature test.",
            "Assert stable TZID extraction for tzical zones before finalization.",
            "high",
        ),
        ("high", "dateutil-rfc5545-timezone-interop", 1): (
            "cross-scope regression",
            "The pi-check patch both emitted the wrong tzical TZID and rejected non-recurrence VCALENDAR properties such as SUMMARY; baseline passed all tests.",
            "Require VCALENDAR parsing to ignore unrelated properties while preserving TZID serialization.",
            "high",
        ),
        ("high", "dateutil-rfc5545-timezone-interop", 2): (
            "cross-scope regression",
            "The pi-check patch rejected SUMMARY inside VCALENDAR instead of ignoring non-recurrence properties; baseline passed all tests.",
            "Add an explicit unrelated-property preservation test to the audit.",
            "high",
        ),
        ("high", "go-critic-doc-link-checker", 1): (
            "likely variance",
            "Baseline mishandled a link to an unimported package and lost one preservation test. The pi-check stage made no edit or write, so its complete patch existed before the check prompt.",
            "Do not credit the follow-up for this win; audit imported-package resolution in the original implementation.",
            "high",
        ),
        ("high", "langchain-request-coalescing", 0): (
            "cross-scope regression",
            "The pi-check patch made three inner calls where per-item batch coalescing required two. Baseline passed 50/50 F2P; the follow-up edited the code but left this invariant broken.",
            "Count underlying calls for duplicate batch items after every coalescing change.",
            "high",
        ),
        ("high", "mobly-grouped-test-barriers", 1): (
            "missing invariant/guard",
            "Baseline passed every feature test but regressed one no-entry-mode preservation case. The follow-up restored the 808th preservation test.",
            "Include no-entry-mode device access in the barrier completion audit.",
            "high",
        ),
        ("high", "mobly-grouped-test-barriers", 2): (
            "missing invariant/guard",
            "Baseline again missed the same no-entry-mode preservation case; the follow-up restored 808/808 P2P.",
            "Include no-entry-mode device access in the barrier completion audit.",
            "high",
        ),
        ("high", "obsidian-linter-link-format-conversion", 0): (
            "cross-scope regression",
            "The pi-check follow-up rewrote a spaced Markdown target as <My Page>, violating exact preservation; baseline passed 60/60 feature tests.",
            "Audit exact spacing and angle-bracket preservation after link conversion edits.",
            "high",
        ),
        ("high", "obsidian-linter-link-format-conversion", 1): (
            "cross-scope regression",
            "The pi-check patch retained an escaped closing bracket in a converted wiki-link label; baseline passed 60/60 feature tests.",
            "Test escaped delimiters and label unescaping before finalization.",
            "high",
        ),
        ("high", "superjson-error-stack-serialization", 1): (
            "missing invariant/guard",
            "Baseline applied maxStackLines before frame processing and missed two ordering cases. The follow-up reached 80/80 F2P and 116/116 P2P.",
            "Audit strip, redact, and line-limit ordering as one pipeline invariant.",
            "high",
        ),
        ("high", "tengo-callable-instance-isolation", 2): (
            "missing invariant/guard",
            "Baseline lost imported modules when a compiled closure was called from Go (22/23 F2P). The follow-up restored that final case.",
            "Test constants, globals, imports, and closures across Go-side calls.",
            "high",
        ),
    }
    key = (level, task, rep)
    if key in specific:
        bucket, mechanism, implication, confidence = specific[key]
    elif right["reward_binary"] < 0 or right.get("verifier_exit") == "timeout":
        bucket = "resource exhaustion"
        mechanism = "The pi-check side ended with a timeout or negative reward while baseline retained graded evidence."
        implication = "Reserve validation budget and treat missing grading as a hard completion blocker."
        confidence = "high"
    else:
        left_partial = float(left["reward_partial"])
        right_partial = float(right["reward_partial"])
        if right_partial > left_partial:
            bucket = "under-implementation"
            mechanism = (
                f"The pi-check trajectory raised partial reward from {left_partial:.3f} to {right_partial:.3f}; "
                f"the delivered audit used {right_trace['post_check_turns']} post-check turns."
            )
            implication = "Keep a bounded completion audit when feature or preservation coverage remains materially incomplete."
        else:
            bucket = "cross-scope regression"
            mechanism = (
                f"The pi-check trajectory reduced partial reward from {left_partial:.3f} to {right_partial:.3f} after "
                f"{right_trace['post_check_turns']} post-check turns."
            )
            implication = (
                "Require targeted and preservation validation after follow-up mutation."
            )
        confidence = "medium"
    failed_source = (
        right_verifier
        if right["reward_partial"] < left["reward_partial"]
        else left_verifier
    )
    failed_names = [item["name"] for item in failed_source["failed_examples"][:3]]
    return {
        "primary_bucket": bucket,
        "secondary_bucket": None,
        "mechanism": mechanism,
        "evidence": failed_names,
        "guidance_implication": implication,
        "confidence": confidence,
    }


def build_packet(
    level: str,
    task: str,
    rep: int,
    reasons: list[str],
    records: dict[tuple[str, str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    metadata = load_task_metadata(task)
    sides: dict[str, dict[str, Any]] = {}
    for side, config in (("left", LEFT_CONFIG), ("right", RIGHT_CONFIG)):
        result = records[(level, config, task, rep)]
        cell = cell_path(level, config, task, rep)
        sides[side] = {
            "config": config,
            "cell": str(cell.relative_to(CANONICAL_REPO)),
            "result": compact_result(result),
            "session_trace": read_session_trace(cell),
            "patch_stats": read_patch_stats(cell),
            "verifier": read_verifier_evidence(cell),
        }
    classification = classify_packet(
        level,
        task,
        rep,
        sides["left"]["result"],
        sides["right"]["result"],
        sides["right"]["session_trace"],
        sides["left"]["verifier"],
        sides["right"]["verifier"],
    )
    packet = {
        "pair": {
            "level": level,
            "task": task,
            "rep": rep,
            "title": metadata["title"],
            "language": metadata["language"],
            "left_config": LEFT_CONFIG,
            "right_config": RIGHT_CONFIG,
            "trigger_reasons": reasons,
        },
        **sides,
        "stage_ledger": {
            "initialization": "Both sides used pi@0.83.0 and openai-codex/gpt-5.6-luna at the packet thinking level.",
            "contract_representation": "The baseline had no config-authored prompt; pi-check delivered one same-session Re-audit follow-up.",
            "seam_location": {
                "left_files": sides["left"]["patch_stats"]["files"],
                "right_files": sides["right"]["patch_stats"]["files"],
            },
            "implementation": {
                "left_changed_lines": sides["left"]["patch_stats"]["changed_lines"],
                "right_changed_lines": sides["right"]["patch_stats"]["changed_lines"],
            },
            "targeted_validation": {
                "left_commands": sides["left"]["session_trace"]["test_commands"],
                "right_commands": sides["right"]["session_trace"]["test_commands"],
            },
            "completion_audit": {
                "right_post_check_turns": sides["right"]["session_trace"][
                    "post_check_turns"
                ],
                "right_post_check_tools": sides["right"]["session_trace"][
                    "post_check_tool_counts"
                ],
            },
            "termination": {
                "left": sides["left"]["session_trace"]["last_stop_reason"],
                "right": sides["right"]["session_trace"]["last_stop_reason"],
            },
        },
        "classification": classification,
    }
    return packet


def render_packet_markdown(packet: dict[str, Any]) -> str:
    pair = packet["pair"]
    left = packet["left"]
    right = packet["right"]
    classification = packet["classification"]

    def metrics(side: dict[str, Any]) -> str:
        result = side["result"]
        return (
            f"binary={result['reward_binary']}, partial={result['reward_partial']:.3f}, "
            f"F2P={result['f2p_passed']}/{result['f2p_total']}, "
            f"P2P={result['p2p_passed']}/{result['p2p_total']}, "
            f"tokens={result['total_tokens']:,}, cost=${result['cost_usd']:.4f}, "
            f"wall={result['agent_wall_s']:.1f}s"
        )

    def failed(side: dict[str, Any]) -> str:
        rows = side["verifier"]["failed_examples"]
        return (
            "\n".join(f"- {item['name']}: {item['message'][:240]}" for item in rows[:8])
            or "- none captured"
        )

    return f"""# {pair["level"]} · {pair["task"]} · rep{pair["rep"]}

{pair["title"]} · {pair["language"]}

## Packet trigger

{", ".join(pair["trigger_reasons"])}

## Outcome delta

- Baseline: {metrics(left)}
- pi-check: {metrics(right)}

## Patch stats

- Baseline: {left["patch_stats"]["files_count"]} files, +{left["patch_stats"]["additions"]}/-{left["patch_stats"]["deletions"]} lines, {left["patch_stats"]["bytes"]} bytes
- pi-check: {right["patch_stats"]["files_count"]} files, +{right["patch_stats"]["additions"]}/-{right["patch_stats"]["deletions"]} lines, {right["patch_stats"]["bytes"]} bytes

## pi-check delivery and tool summary

- Re-audit prompts: {right["session_trace"]["check_prompt_count"]}
- Post-check turns: {right["session_trace"]["post_check_turns"]}
- Post-check tools: `{json.dumps(right["session_trace"]["post_check_tool_counts"], sort_keys=True)}`

## Baseline verifier evidence

{failed(left)}

## pi-check verifier evidence

{failed(right)}

## Classification

- Primary bucket: **{classification["primary_bucket"]}**
- Mechanism: {classification["mechanism"]}
- Guidance hypothesis: {classification["guidance_implication"]}
- Confidence: {classification["confidence"]}

## Artifact paths

- Baseline cell: `{left["cell"]}`
- pi-check cell: `{right["cell"]}`
- Baseline session: `{left["session_trace"]["session"]}`
- pi-check session: `{right["session_trace"]["session"]}`
"""


def task_cluster_bootstrap_ci(
    level: str,
    tasks: list[str],
    records: dict[tuple[str, str, str, int], dict[str, Any]],
) -> tuple[float, float]:
    rng = random.Random(20260731 + (0 if level == "low" else 1))
    deltas: list[float] = []
    for _ in range(20_000):
        sampled_tasks = [rng.choice(tasks) for _ in tasks]
        delta = sum(
            (records[(level, RIGHT_CONFIG, task, rep)]["reward_binary"] == 1)
            - (records[(level, LEFT_CONFIG, task, rep)]["reward_binary"] == 1)
            for task in sampled_tasks
            for rep in range(3)
        ) / (len(tasks) * 3)
        deltas.append(delta)
    deltas.sort()
    return deltas[500], deltas[19_499]


def summarize_config(rows: list[dict[str, Any]]) -> dict[str, Any]:
    f2p_passed = sum(int(row.get("f2p_passed") or 0) for row in rows)
    f2p_total = sum(int(row.get("f2p_total") or 0) for row in rows)
    p2p_passed = sum(int(row.get("p2p_passed") or 0) for row in rows)
    p2p_total = sum(int(row.get("p2p_total") or 0) for row in rows)
    return {
        "count": len(rows),
        "solves": sum(row["reward_binary"] == 1 for row in rows),
        "negative_rewards": sum(row["reward_binary"] < 0 for row in rows),
        "partial_mean": statistics.mean(row["reward_partial"] for row in rows),
        "partial_median": statistics.median(row["reward_partial"] for row in rows),
        "f2p_passed": f2p_passed,
        "f2p_total": f2p_total,
        "p2p_passed": p2p_passed,
        "p2p_total": p2p_total,
        "tokens_total": sum(row["total_tokens"] for row in rows),
        "tokens_median": statistics.median(row["total_tokens"] for row in rows),
        "cost_total": sum(row["cost_usd"] for row in rows),
        "cost_median": statistics.median(row["cost_usd"] for row in rows),
        "wall_mean": statistics.mean(row["agent_wall_s"] for row in rows),
        "wall_median": statistics.median(row["agent_wall_s"] for row in rows),
        "turns_mean": statistics.mean(row["turns"] for row in rows),
        "tool_calls_mean": statistics.mean(row["tool_calls"] for row in rows),
        "agent_timeouts": sum(bool(row["agent_timed_out"]) for row in rows),
        "verifier_timeouts": sum(row["verifier_exit"] == "timeout" for row in rows),
        "launch_plan_identities": sorted({row["launch_plan_identity"] for row in rows}),
    }


def build_summary(
    tasks: list[str], records: dict[tuple[str, str, str, int], dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary: dict[str, Any] = {
        "comparison": {
            "model": "openai-codex/gpt-5.6-luna",
            "subject_version": "pi@0.83.0",
            "subset": "12_v2",
            "tasks": len(tasks),
            "reps": 3,
            "left_config": LEFT_CONFIG,
            "right_config": RIGHT_CONFIG,
            "packet_rule": "binary flip, timeout/negative-reward discordance, or absolute partial/F2P/P2P delta >= 0.25",
        },
        "levels": {},
        "delivery": {},
    }
    packet_index: list[dict[str, Any]] = []
    for level in LEVELS:
        keys = [(task, rep) for task in tasks for rep in range(3)]
        configs = {
            config: summarize_config(
                [records[(level, config, task, rep)] for task, rep in keys]
            )
            for config in CONFIGS
        }
        observed_identities = set().union(
            *(set(configs[config]["launch_plan_identities"]) for config in CONFIGS)
        )
        if observed_identities != EXPECTED_PLAN_IDENTITIES[level]:
            raise SystemExit(
                f"Launch provenance mismatch for {level}: observed={sorted(observed_identities)}"
            )
        both = left_only = right_only = neither = 0
        flips: list[dict[str, Any]] = []
        timeout_discordant = 0
        timeout_filtered_left = timeout_filtered_right = timeout_filtered_count = 0
        task_rows: list[dict[str, Any]] = []
        language_accumulator: dict[str, list[int]] = collections.defaultdict(
            lambda: [0, 0, 0]
        )
        for task, rep in keys:
            left = records[(level, LEFT_CONFIG, task, rep)]
            right = records[(level, RIGHT_CONFIG, task, rep)]
            left_solve = left["reward_binary"] == 1
            right_solve = right["reward_binary"] == 1
            if left_solve and right_solve:
                both += 1
            elif left_solve:
                left_only += 1
            elif right_solve:
                right_only += 1
            else:
                neither += 1
            if left_solve != right_solve:
                flips.append(
                    {
                        "task": task,
                        "rep": rep,
                        "direction": "pi-check-only"
                        if right_solve
                        else "baseline-only",
                        "left_partial": left["reward_partial"],
                        "right_partial": right["reward_partial"],
                        "left_f2p": [left.get("f2p_passed"), left.get("f2p_total")],
                        "right_f2p": [right.get("f2p_passed"), right.get("f2p_total")],
                    }
                )
            timed_out = (
                bool(left["agent_timed_out"])
                or bool(right["agent_timed_out"])
                or left["verifier_exit"] == "timeout"
                or right["verifier_exit"] == "timeout"
            )
            if timed_out:
                if left_solve != right_solve:
                    timeout_discordant += 1
            else:
                timeout_filtered_count += 1
                timeout_filtered_left += left_solve
                timeout_filtered_right += right_solve
            language = str(left["language"])
            language_accumulator[language][0] += 1
            language_accumulator[language][1] += int(left_solve)
            language_accumulator[language][2] += int(right_solve)
            reasons = packet_trigger_reasons(left, right)
            if reasons:
                packet = build_packet(level, task, rep, reasons, records)
                stem = f"{level}__{task}__rep{rep}"
                json_path = PACKET_DIR / f"{stem}.json"
                md_path = PACKET_DIR / f"{stem}.md"
                json_path.write_text(
                    json.dumps(packet, indent=2, sort_keys=True) + "\n"
                )
                md_path.write_text(render_packet_markdown(packet))
                packet_index.append(
                    {
                        "level": level,
                        "task": task,
                        "rep": rep,
                        "reasons": reasons,
                        "classification": packet["classification"],
                        "json": f"packets/{json_path.name}",
                        "markdown": f"packets/{md_path.name}",
                    }
                )
        for task in tasks:
            metadata = load_task_metadata(task)
            left_solves = sum(
                records[(level, LEFT_CONFIG, task, rep)]["reward_binary"] == 1
                for rep in range(3)
            )
            right_solves = sum(
                records[(level, RIGHT_CONFIG, task, rep)]["reward_binary"] == 1
                for rep in range(3)
            )
            task_rows.append(
                {
                    "task": task,
                    "title": metadata["title"],
                    "language": metadata["language"],
                    "left_solves": left_solves,
                    "right_solves": right_solves,
                    "delta": right_solves - left_solves,
                }
            )
        task_rows.sort(key=lambda row: (-abs(row["delta"]), -row["delta"], row["task"]))
        ci_low, ci_high = task_cluster_bootstrap_ci(level, tasks, records)
        summary["levels"][level] = {
            "configs": configs,
            "agreement": {
                "both": both,
                "baseline_only": left_only,
                "pi_check_only": right_only,
                "neither": neither,
                "discordant": left_only + right_only,
            },
            "solve_delta": configs[RIGHT_CONFIG]["solves"]
            - configs[LEFT_CONFIG]["solves"],
            "solve_rate_delta": (
                configs[RIGHT_CONFIG]["solves"] - configs[LEFT_CONFIG]["solves"]
            )
            / 36,
            "mcnemar_p": exact_mcnemar_p(left_only, right_only),
            "task_cluster_bootstrap_ci": [ci_low, ci_high],
            "timeout_sensitivity": {
                "excluded_pairs": 36 - timeout_filtered_count,
                "discordant_timeout_pairs": timeout_discordant,
                "baseline_solves": timeout_filtered_left,
                "pi_check_solves": timeout_filtered_right,
                "solve_delta": timeout_filtered_right - timeout_filtered_left,
            },
            "flips": flips,
            "task_rows": task_rows,
            "language_rows": [
                {
                    "language": language,
                    "pairs": values[0],
                    "baseline_solves": values[1],
                    "pi_check_solves": values[2],
                }
                for language, values in sorted(language_accumulator.items())
            ],
        }
        delivery: dict[str, Any] = {}
        for config in CONFIGS:
            prompt_counts: collections.Counter[int] = collections.Counter()
            request_count = model_matches = effort_matches = 0
            flags: collections.Counter[str] = collections.Counter()
            for task, rep in keys:
                result = records[(level, config, task, rep)]
                cell = cell_path(level, config, task, rep)
                trace = read_session_trace(cell)
                prompt_counts[int(trace["check_prompt_count"])] += 1
                flags[json.dumps(result.get("arm_pi_flags") or [], sort_keys=True)] += 1
                for request_path in (cell / "initial_context").glob(
                    "provider_request_*.json"
                ):
                    request = json.loads(request_path.read_text())
                    request_count += 1
                    model_matches += request.get("model") == "gpt-5.6-luna"
                    effort_matches += (
                        request.get("reasoning", {}).get("effort") == level
                    )
            delivery[config] = {
                "check_prompt_counts": dict(prompt_counts),
                "provider_requests": request_count,
                "model_matches": model_matches,
                "effort_matches": effort_matches,
                "flags": dict(flags),
                "classification": (
                    "delivered"
                    if (
                        (config == LEFT_CONFIG and prompt_counts == {0: 36})
                        or (config == RIGHT_CONFIG and prompt_counts == {1: 36})
                    )
                    else "ambiguous"
                ),
            }
        summary["delivery"][level] = delivery

    all_level_agreement = {
        key: sum(summary["levels"][level]["agreement"][key] for level in LEVELS)
        for key in ("both", "baseline_only", "pi_check_only", "neither", "discordant")
    }
    all_level_configs = {
        config: summarize_config(
            [
                records[(level, config, task, rep)]
                for level in LEVELS
                for task in tasks
                for rep in range(3)
            ]
        )
        for config in CONFIGS
    }
    all_level_rng = random.Random(20260733)
    all_level_bootstrap: list[float] = []
    for _ in range(20_000):
        sampled_tasks = [all_level_rng.choice(tasks) for _ in tasks]
        delta = sum(
            (records[(level, RIGHT_CONFIG, task, rep)]["reward_binary"] == 1)
            - (records[(level, LEFT_CONFIG, task, rep)]["reward_binary"] == 1)
            for task in sampled_tasks
            for level in LEVELS
            for rep in range(3)
        ) / (len(tasks) * len(LEVELS) * 3)
        all_level_bootstrap.append(delta)
    all_level_bootstrap.sort()
    summary["all_levels"] = {
        "configs": all_level_configs,
        "agreement": all_level_agreement,
        "solve_delta": all_level_configs[RIGHT_CONFIG]["solves"]
        - all_level_configs[LEFT_CONFIG]["solves"],
        "solve_rate_delta": (
            all_level_configs[RIGHT_CONFIG]["solves"]
            - all_level_configs[LEFT_CONFIG]["solves"]
        )
        / (len(tasks) * len(LEVELS) * 3),
        "mcnemar_p": exact_mcnemar_p(
            all_level_agreement["baseline_only"], all_level_agreement["pi_check_only"]
        ),
        "task_cluster_bootstrap_ci": [
            all_level_bootstrap[500],
            all_level_bootstrap[19_499],
        ],
    }

    summary["thinking_transitions"] = {}
    for config in CONFIGS:
        config_transitions: dict[str, Any] = {}
        for from_level, to_level in (("low", "high"), ("high", "max")):
            both = from_only = to_only = neither = 0
            for task in tasks:
                for rep in range(3):
                    from_solve = (
                        records[(from_level, config, task, rep)]["reward_binary"] == 1
                    )
                    to_solve = (
                        records[(to_level, config, task, rep)]["reward_binary"] == 1
                    )
                    if from_solve and to_solve:
                        both += 1
                    elif from_solve:
                        from_only += 1
                    elif to_solve:
                        to_only += 1
                    else:
                        neither += 1
            transition_rng = random.Random(
                20260734
                + (0 if config == LEFT_CONFIG else 10)
                + (0 if from_level == "low" else 1)
            )
            transition_bootstrap: list[float] = []
            for _ in range(20_000):
                sampled_tasks = [transition_rng.choice(tasks) for _ in tasks]
                delta = sum(
                    (records[(to_level, config, task, rep)]["reward_binary"] == 1)
                    - (records[(from_level, config, task, rep)]["reward_binary"] == 1)
                    for task in sampled_tasks
                    for rep in range(3)
                ) / (len(tasks) * 3)
                transition_bootstrap.append(delta)
            transition_bootstrap.sort()
            config_transitions[f"{from_level}_to_{to_level}"] = {
                "from_level": from_level,
                "to_level": to_level,
                "from_solves": summary["levels"][from_level]["configs"][config][
                    "solves"
                ],
                "to_solves": summary["levels"][to_level]["configs"][config]["solves"],
                "solve_delta": to_only - from_only,
                "agreement": {
                    "both": both,
                    "from_only": from_only,
                    "to_only": to_only,
                    "neither": neither,
                    "discordant": from_only + to_only,
                },
                "mcnemar_p": exact_mcnemar_p(from_only, to_only),
                "task_cluster_bootstrap_ci": [
                    transition_bootstrap[500],
                    transition_bootstrap[19_499],
                ],
            }
        summary["thinking_transitions"][config] = config_transitions
    return summary, packet_index


def metric_table_rows(level_summary: dict[str, Any]) -> str:
    left = level_summary["configs"][LEFT_CONFIG]
    right = level_summary["configs"][RIGHT_CONFIG]
    metrics = [
        (
            "Binary solves",
            f"{left['solves']}/36 · {percent(left['solves'] / 36)}",
            f"{right['solves']}/36 · {percent(right['solves'] / 36)}",
            percentage_points(level_summary["solve_rate_delta"]),
            "good"
            if level_summary["solve_delta"] > 0
            else "bad"
            if level_summary["solve_delta"] < 0
            else "neutral",
        ),
        (
            "Mean partial reward",
            percent(left["partial_mean"]),
            percent(right["partial_mean"]),
            percentage_points(right["partial_mean"] - left["partial_mean"]),
            "good" if right["partial_mean"] > left["partial_mean"] else "bad",
        ),
        (
            "F2P passed / total",
            f"{left['f2p_passed']:,}/{left['f2p_total']:,}",
            f"{right['f2p_passed']:,}/{right['f2p_total']:,}",
            "different denominators"
            if left["f2p_total"] != right["f2p_total"]
            else f"{right['f2p_passed'] - left['f2p_passed']:+,}",
            "caution" if left["f2p_total"] != right["f2p_total"] else "neutral",
        ),
        (
            "P2P passed / total",
            f"{left['p2p_passed']:,}/{left['p2p_total']:,}",
            f"{right['p2p_passed']:,}/{right['p2p_total']:,}",
            "different denominators"
            if left["p2p_total"] != right["p2p_total"]
            else f"{right['p2p_passed'] - left['p2p_passed']:+,}",
            "caution" if left["p2p_total"] != right["p2p_total"] else "neutral",
        ),
        (
            "Total tokens",
            f"{left['tokens_total'] / 1e6:.1f}M",
            f"{right['tokens_total'] / 1e6:.1f}M",
            f"{ratio_change(right['tokens_total'], left['tokens_total']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Median tokens / rep",
            f"{left['tokens_median'] / 1e6:.2f}M",
            f"{right['tokens_median'] / 1e6:.2f}M",
            f"{ratio_change(right['tokens_median'], left['tokens_median']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Total recorded cost",
            f"${left['cost_total']:.2f}",
            f"${right['cost_total']:.2f}",
            f"{ratio_change(right['cost_total'], left['cost_total']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Mean wall time",
            f"{left['wall_mean']:.1f}s",
            f"{right['wall_mean']:.1f}s",
            f"{ratio_change(right['wall_mean'], left['wall_mean']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Mean turns",
            f"{left['turns_mean']:.1f}",
            f"{right['turns_mean']:.1f}",
            f"{ratio_change(right['turns_mean'], left['turns_mean']) * 100:+.1f}%",
            "bad",
        ),
        (
            "Verifier timeouts / negative rewards",
            f"{left['verifier_timeouts']} / {left['negative_rewards']}",
            f"{right['verifier_timeouts']} / {right['negative_rewards']}",
            "risk" if right["negative_rewards"] > left["negative_rewards"] else "none",
            "bad"
            if right["negative_rewards"] > left["negative_rewards"]
            else "neutral",
        ),
    ]
    return "".join(
        f'<tr><td>{html.escape(name)}</td><td class="num">{left_value}</td><td class="num">{right_value}</td><td class="num"><span class="tag {verdict}">{delta}</span></td></tr>'
        for name, left_value, right_value, delta, verdict in metrics
    )


def task_table_rows(level_summary: dict[str, Any]) -> str:
    rows = []
    for row in level_summary["task_rows"]:
        verdict = (
            "good" if row["delta"] > 0 else "bad" if row["delta"] < 0 else "neutral"
        )
        rows.append(
            f'<tr><td><strong>{html.escape(row["task"])}</strong><br><span class="muted">{html.escape(row["title"])}</span></td>'
            f'<td>{html.escape(row["language"])}</td><td class="num">{row["left_solves"]}/3</td>'
            f'<td class="num">{row["right_solves"]}/3</td><td class="num"><span class="tag {verdict}">{row["delta"]:+d}</span></td></tr>'
        )
    return "".join(rows)


def flip_table_rows(
    level: str, summary: dict[str, Any], packet_index: list[dict[str, Any]]
) -> str:
    packet_lookup = {
        (row["level"], row["task"], row["rep"]): row for row in packet_index
    }
    rows = []
    for flip in summary["levels"][level]["flips"]:
        packet = packet_lookup[(level, flip["task"], flip["rep"])]
        classification = packet["classification"]
        verdict = "good" if flip["direction"] == "pi-check-only" else "bad"
        rows.append(
            f'<tr><td><strong>{html.escape(flip["task"])}</strong></td><td class="num">{flip["rep"]}</td>'
            f'<td><span class="tag {verdict}">{html.escape(flip["direction"])}</span></td>'
            f'<td class="num">{flip["left_partial"]:.3f}</td><td class="num">{flip["right_partial"]:.3f}</td>'
            f"<td>{html.escape(classification['primary_bucket'])}</td>"
            f"<td>{html.escape(classification['mechanism'])}</td>"
            f'<td><a href="{html.escape(packet["markdown"])}">packet</a></td></tr>'
        )
    return "".join(rows)


def render_report(summary: dict[str, Any], packet_index: list[dict[str, Any]]) -> str:
    low = summary["levels"]["low"]
    high = summary["levels"]["high"]
    low_left = low["configs"][LEFT_CONFIG]
    low_right = low["configs"][RIGHT_CONFIG]
    high_left = high["configs"][LEFT_CONFIG]
    high_right = high["configs"][RIGHT_CONFIG]
    style = """
:root{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#c58a00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px;--max:1240px}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:var(--max);margin:auto;padding:28px 20px 56px}.hero,section{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:clamp(26px,4vw,42px)}.eyebrow{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1,h2,h3{line-height:1.08;letter-spacing:-.035em}h1{font-size:clamp(2.3rem,5vw,4.6rem);max-width:14ch;margin:14px 0}.lede{max-width:78ch;color:var(--muted);font-size:1.08rem}.pills{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.pill,.tag{display:inline-flex;padding:6px 10px;border-radius:999px;font-weight:800;font-size:12px}.pill{padding:8px 12px;text-transform:uppercase;letter-spacing:.04em}.good{background:var(--green-soft);color:var(--green)}.bad{background:var(--red-soft);color:var(--red)}.caution{background:var(--amber-soft);color:#8a6100}.neutral{background:#eef3ff;color:var(--blue-2)}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-top:22px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.65rem;letter-spacing:-.04em}.stat span{display:block;color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:clamp(20px,3vw,30px)}h2{font-size:1.8rem;margin:0 0 6px}.section-lede{color:var(--muted);margin:0 0 18px;max-width:78ch}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.mini{border:1px solid var(--line);border-radius:17px;padding:16px;text-align:center}.mini strong{display:block;font-size:2rem}.mini span{font-size:11px;text-transform:uppercase;color:var(--muted);font-weight:800}.callout{border-left:5px solid var(--blue);background:#f5f7ff;padding:15px 17px;border-radius:13px;margin-top:15px}.callout.goodline{border-color:var(--green);background:var(--green-soft)}.callout.badline{border-color:var(--red);background:var(--red-soft)}.callout.warn{border-color:var(--amber);background:var(--amber-soft)}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.num{text-align:right;font-variant-numeric:tabular-nums}.table-wrap{overflow:auto}.muted{color:var(--muted)}code{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:5px}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}.bars{display:grid;gap:12px}.bar-row{display:grid;grid-template-columns:70px 1fr;gap:12px;align-items:center}.bar-track{height:14px;background:#edf2f7;border-radius:99px;overflow:hidden;margin:4px 0}.bar-fill{height:100%;border-radius:99px}.base{background:#9fb0c9}.check{background:linear-gradient(90deg,#3a73ff,#1d3fb8)}details{border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:12px}summary{cursor:pointer;font-weight:800}footer{text-align:center;color:var(--muted);padding:26px;font-size:13px}@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}.grid4{grid-template-columns:repeat(2,1fr)}}@media(max-width:540px){.stats,.grid4{grid-template-columns:1fr}.hero,section{padding:20px}}
"""

    def agreement_cards(level_summary: dict[str, Any]) -> str:
        agreement = level_summary["agreement"]
        return f"""
<div class="grid4">
  <div class="mini"><strong>{agreement["both"]}</strong><span>both solved</span></div>
  <div class="mini"><strong class="bad">{agreement["baseline_only"]}</strong><span>baseline only</span></div>
  <div class="mini"><strong class="good">{agreement["pi_check_only"]}</strong><span>pi-check only</span></div>
  <div class="mini"><strong>{agreement["neither"]}</strong><span>neither solved</span></div>
</div>"""

    low_ci = low["task_cluster_bootstrap_ci"]
    high_ci = high["task_cluster_bootstrap_ci"]
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>GPT-5.6 Luna · pi-check low/high · 12_v2</title><style>{style}</style></head>
<body><div class="wrap">
<header class="hero">
<span class="eyebrow">DeepSWE · GPT-5.6 Luna · 12_v2 · 3 reps</span>
<h1>High gains two solves. The churn says “not proven.”</h1>
<p class="lede">At low thinking, pi-check moves from 2 to 1 binary solve while doubling tokens, despite a +3.3-point mean partial gain. At high thinking, it moves from 18 to 20 solves, but 14 of 36 matched reps flip direction and the task-cluster uncertainty interval spans a substantial loss to a substantial gain. The stable result is cost: the follow-up makes Luna materially more expensive at both levels.</p>
<div class="pills"><span class="pill bad">Low: −1 solve</span><span class="pill caution">High: +2 solves, inconclusive</span><span class="pill caution">High churn: 14/36</span><span class="pill bad">Tokens: +97% low · +43% high</span><span class="pill neutral">Delivery: 72/72 pi-check reps</span></div>
<div class="stats">
<div class="stat"><strong>{low_left["solves"]} → {low_right["solves"]}</strong><span>Low solves · 36 reps</span></div>
<div class="stat"><strong>{high_left["solves"]} → {high_right["solves"]}</strong><span>High solves · 36 reps</span></div>
<div class="stat"><strong>{percentage_points(low_right["partial_mean"] - low_left["partial_mean"])}</strong><span>Low partial delta</span></div>
<div class="stat"><strong>{percentage_points(high_right["partial_mean"] - high_left["partial_mean"])}</strong><span>High partial delta</span></div>
<div class="stat"><strong>+{len(packet_index)}</strong><span>Evidence packets</span></div>
</div></header>

<section><h2>Decision</h2><div class="grid2">
<div class="callout badline"><strong>Low: no binary benefit.</strong> pi-check loses one net solve, costs {ratio_change(low_right["cost_total"], low_left["cost_total"]) * 100:.0f}% more, and introduces two negative rewards. Excluding timeout-affected pairs changes the solve result to a 1–1 tie, not a win.</div>
<div class="callout warn"><strong>High: promising direction, weak evidence.</strong> The +2 net solves come from 8 gains and 6 losses. Exact McNemar p={high["mcnemar_p"]:.3f}; task-cluster 95% bootstrap CI is {percentage_points(high_ci[0])} to {percentage_points(high_ci[1])}.</div>
</div><div class="callout"><strong>The thinking increase matters far more than pi-check.</strong> Baseline rises from {low_left["solves"]} to {high_left["solves"]} solves; pi-check rises from {low_right["solves"]} to {high_right["solves"]}. This is not a controlled low-vs-high cost comparison, but it shows where the quality signal lives in this subset.</div></section>

<section><h2>Low thinking</h2><p class="section-lede">36 exact pairs. Solve delta {low["solve_delta"]:+d}; exact McNemar p={low["mcnemar_p"]:.3f}; task-cluster 95% CI {percentage_points(low_ci[0])} to {percentage_points(low_ci[1])}.</p>
<div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{metric_table_rows(low)}</tbody></table></div>
<h3>Solve agreement</h3>{agreement_cards(low)}
<div class="callout warn"><strong>Timeout sensitivity:</strong> remove the one verifier-timeout pair and the low comparison becomes 1 solve vs 1, rather than 2 vs 1. The intention-to-treat result remains primary.</div>
<details open><summary>Three solve flips</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Direction</th><th class="num">Base partial</th><th class="num">Check partial</th><th>Driver</th><th>Evidence</th><th></th></tr></thead><tbody>{flip_table_rows("low", summary, packet_index)}</tbody></table></div></details>
<details><summary>Task-by-task solves</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th>Language</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{task_table_rows(low)}</tbody></table></div></details>
</section>

<section><h2>High thinking</h2><p class="section-lede">36 exact pairs after the approved auth recovery repaired 16 zero-token cells. The final tree contains 56 results from the original plan and 16 compatible results from the recovery plan; every rep has positive usage.</p>
<div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{metric_table_rows(high)}</tbody></table></div>
<h3>Solve agreement</h3>{agreement_cards(high)}
<div class="callout warn"><strong>Net hides churn:</strong> 14/36 reps disagree. Most flips are one-to-three-test last-mile differences; two flips had no pi-check edit after the follow-up prompt, so those outcomes cannot be credited to follow-up mutation.</div>
<details open><summary>Fourteen solve flips</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Direction</th><th class="num">Base partial</th><th class="num">Check partial</th><th>Driver</th><th>Evidence</th><th></th></tr></thead><tbody>{flip_table_rows("high", summary, packet_index)}</tbody></table></div></details>
<details><summary>Task-by-task solves</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th>Language</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{task_table_rows(high)}</tbody></table></div></details>
</section>

<section><h2>Delivery and provenance</h2><div class="grid2">
<div class="callout goodline"><strong>Delivered.</strong> Baseline has 0/36 check prompts at each level. pi-check has exactly one <code>Re-audit</code> follow-up in all 36/36 sessions at each level. All captured provider requests match Luna and the requested thinking.</div>
<div class="callout"><strong>Controlled surface.</strong> Both configs use Pi 0.83.0 and Codex OAuth. The config difference is the vendored pi-check extension plus <code>--check</code>; no config-authored system preamble or orchestration prompt was added.</div>
</div><p class="muted">High provenance is intentionally mixed across the original confirmed plan and its compatible auth recovery. Low uses one plan identity. The report reads current canonical result paths and records each plan identity in <a href="summary.json">summary.json</a>.</p></section>

<section><h2>What to keep—and what to prevent</h2><div class="grid2">
<div class="callout goodline"><strong>Keep:</strong> bounded audits that identify a concrete last-mile invariant. The strongest gains complete retry behavior, recursive-delegation branches, alias missing-field handling, stack-processing order, and closure import preservation.</div>
<div class="callout badline"><strong>Prevent:</strong> broad follow-up mutation without a preservation gate. Losses came from incomplete recursive delegation, VCALENDAR scope regression, duplicate coalescing calls, exact link-format regressions, and one verifier timeout.</div>
</div><div class="callout"><strong>Hypothesis, not proof:</strong> make pi-check stop after evidence-only validation when the original patch already passes targeted tests, and require a narrow preservation test after any follow-up edit. This could retain last-mile wins while reducing the observed high-level churn and cost.</div></section>

<section><h2>Conclusion</h2><div class="callout badline"><strong>Low: reject as a quality win.</strong> More partial credit does not offset fewer solves, two negative outcomes, and roughly double token use.</div><div class="callout warn"><strong>High: continue testing, do not claim a win.</strong> +2/36 is directionally positive, but p={high["mcnemar_p"]:.3f}, the task-cluster interval includes zero, and 14 flips reveal unstable behavior. A wider matched subset is needed.</div><div class="callout"><strong>Operational verdict:</strong> pi-check does not earn a Luna recommendation from these 12 tasks. It raises cost at both levels; low loses a solve, while high's observed gain is too uncertain and churn-heavy to treat as reliable.</div></section>

<footer>Generated {generated} from saved DeepSWE artifacts · <a href="summary.json">summary JSON</a> · {len(packet_index)} linked trajectory packets · scope: Luna, 12_v2, reps 0–2, low/high only</footer>
</div></body></html>"""


def main() -> None:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    for path in PACKET_DIR.glob("*"):
        if path.is_file():
            path.unlink()
    tasks, records = load_matched_results()
    summary, packet_index = build_summary(tasks, records)
    summary["packet_index"] = packet_index
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (PACKET_DIR / "packet_index.json").write_text(
        json.dumps(packet_index, indent=2, sort_keys=True) + "\n"
    )
    OUT_PATH.write_text(render_all_thinking_report(summary, packet_index))
    print(f"wrote {OUT_PATH}")
    print(f"wrote {len(packet_index)} packets to {PACKET_DIR}")


if __name__ == "__main__":
    main()
