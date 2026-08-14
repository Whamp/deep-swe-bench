"""Read native Pi sessions and extract pre-verifier trajectory process signals."""

from __future__ import annotations

import hashlib
import json
import math
import posixpath
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROCESS_FEATURE_NAMES = (
    "repeated_normalized_tool_actions",
    "repeated_normalized_tool_action_rate",
    "repeated_read_targets",
    "repeated_read_target_rate",
    "repeated_search_actions",
    "repeated_search_action_rate",
    "observable_test_runs",
    "repeated_tests_without_observed_edit",
    "repeated_unchanged_test_failures",
    "test_failure_to_pass_transitions",
    "test_pass_to_failure_transitions",
    "direct_mutation_calls",
    "failed_direct_mutation_calls",
    "direct_mutation_target_revisits",
    "exact_inverse_edit_pairs",
    "strategy_reset_turns",
    "strategy_reset_turn_rate",
    "opaque_top_level_tool_calls",
    "semantic_event_coverage",
)

_DIRECT_SEMANTIC_TOOLS = {
    "bash",
    "edit",
    "find",
    "grep",
    "ls",
    "read",
    "search",
    "write",
    "apply_patch",
}
_MUTATION_TOOLS = {"edit", "write", "apply_patch"}
_READ_TOOLS = {"read"}
_SEARCH_TOOLS = {"find", "grep", "search"}
_SEARCH_COMMAND_RE = re.compile(r"(?:^|[;&|()]\s*)(?:rg|grep|git\s+grep|find|fd)\b")
_TEST_COMMAND_RE = re.compile(
    r"(?:^|[;&|()]\s*)(?:"
    r"python(?:\d+(?:\.\d+)?)?\s+-m\s+(?:pytest|unittest)|"
    r"pytest|tox|nox|go\s+test|cargo\s+test|ctest|"
    r"npm\s+(?:run\s+)?test|pnpm\s+(?:run\s+)?test|yarn\s+test|"
    r"bun\s+test|deno\s+test|vitest|jest|mocha|"
    r"bundle\s+exec\s+rspec|rspec|mvn(?:w)?\s+test|"
    r"gradle(?:w)?\s+test|dotnet\s+test|make\s+(?:check|test)"
    r")\b",
    re.IGNORECASE,
)
_STRATEGY_RESET_RE = re.compile(
    r"\b(?:start(?:ing)? over|rethink(?:ing)?(?: this| the)?(?: approach| strategy)?|"
    r"different approach|new approach|change(?:ing)? (?:the )?(?:approach|strategy)|"
    r"backtrack(?:ing)?|abandon(?:ing)? (?:this|that|the) (?:approach|strategy)|"
    r"reset(?:ting)? (?:the )?(?:approach|strategy))\b",
    re.IGNORECASE,
)
_TRUNCATION_STOP_REASONS = {"length", "max_tokens", "max_output_tokens", "output_limit"}
_ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


@dataclass
class ToolEvent:
    """One top-level tool call joined to its native-session tool result."""

    index: int
    turn_index: int
    call_id: str
    name: str
    arguments: Any
    result_text: str | None = None
    is_error: bool | None = None


@dataclass
class NativeSessionParse:
    """Minimal native-session facts needed for process extraction and schema audit."""

    path: Path
    session: dict[str, Any] = field(default_factory=dict)
    assistant_turns: int = 0
    tool_calls: int = 0
    malformed_records: int = 0
    unresolved_tool_calls: int = 0
    orphan_tool_results: int = 0
    terminal_stop_reason: str | None = None
    record_types: Counter[str] = field(default_factory=Counter)
    roles: Counter[str] = field(default_factory=Counter)
    block_types: Counter[str] = field(default_factory=Counter)
    tool_names: Counter[str] = field(default_factory=Counter)
    stop_reasons: Counter[str] = field(default_factory=Counter)
    assistant_text_by_turn: list[str] = field(default_factory=list)
    events: list[ToolEvent] = field(default_factory=list)


def parse_native_session(path: Path) -> NativeSessionParse:
    """Parse final native-session messages without reading verifier artifacts."""
    parsed = NativeSessionParse(path=path)
    pending: dict[str, ToolEvent] = {}

    with path.open(encoding="utf-8", errors="replace") as lines:
        for raw_line in lines:
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                parsed.malformed_records += 1
                continue
            if not isinstance(record, dict):
                parsed.record_types[type(record).__name__] += 1
                continue

            record_type = str(record.get("type") or "missing")
            parsed.record_types[record_type] += 1
            if record_type == "session":
                parsed.session.update(
                    {
                        "id": record.get("id"),
                        "cwd": record.get("cwd"),
                        "started_at": record.get("timestamp"),
                    }
                )
                continue
            if record_type == "model_change":
                parsed.session.update(
                    {"provider": record.get("provider"), "model": record.get("modelId")}
                )
                continue
            if record_type == "thinking_level_change":
                parsed.session["thinking_level"] = record.get("thinkingLevel")
                continue
            if record_type != "message":
                continue

            message = record.get("message")
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "missing")
            parsed.roles[role] += 1
            if role == "assistant":
                parsed.assistant_turns += 1
                stop_reason = message.get("stopReason")
                if stop_reason is not None:
                    parsed.terminal_stop_reason = str(stop_reason)
                    parsed.stop_reasons[str(stop_reason)] += 1
                turn_text: list[str] = []
                content = message.get("content")
                for block in content if isinstance(content, list) else []:
                    if not isinstance(block, dict):
                        parsed.block_types[type(block).__name__] += 1
                        continue
                    block_type = str(block.get("type") or "missing")
                    parsed.block_types[block_type] += 1
                    if block_type == "thinking":
                        turn_text.append(str(block.get("thinking") or ""))
                    elif block_type == "text":
                        turn_text.append(str(block.get("text") or ""))
                    elif block_type in ("toolCall", "tool_use", "function_call"):
                        call_id = str(block.get("id") or block.get("call_id") or "")
                        name = str(block.get("name") or "unknown").lower()
                        event = ToolEvent(
                            index=len(parsed.events),
                            turn_index=parsed.assistant_turns,
                            call_id=call_id,
                            name=name,
                            arguments=block.get("arguments")
                            if block.get("arguments") is not None
                            else block.get("input", {}),
                        )
                        parsed.events.append(event)
                        parsed.tool_calls += 1
                        parsed.tool_names[name] += 1
                        if call_id:
                            pending[call_id] = event
                parsed.assistant_text_by_turn.append("\n".join(turn_text))
                continue
            if role != "toolResult":
                continue

            call_id = str(
                message.get("toolCallId") or message.get("tool_call_id") or ""
            )
            event = pending.pop(call_id, None)
            if event is None:
                parsed.orphan_tool_results += 1
                continue
            event.result_text = _content_text(message.get("content"))
            event.is_error = bool(message.get("isError"))

    parsed.unresolved_tool_calls = len(pending)
    return parsed


def normalize_tool_action(name: str, arguments: Any) -> str:
    """Return a conservative canonical key for one top-level tool action."""
    normalized = _normalize_argument_value(arguments, key=None)
    return json.dumps(
        {"name": name.strip().lower(), "arguments": normalized},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def extract_session_process_features(
    parsed: NativeSessionParse,
) -> dict[str, int | float]:
    """Extract counts and rates using only events available before verification."""
    action_counts: Counter[str] = Counter()
    read_counts: Counter[str] = Counter()
    search_counts: Counter[str] = Counter()
    successful_mutation_targets: Counter[str] = Counter()
    prior_edit_pairs: dict[str, list[tuple[str, str]]] = {}
    prior_test: dict[str, tuple[int, str, str]] = {}

    repeated_actions = 0
    repeated_reads = 0
    repeated_searches = 0
    observable_tests = 0
    repeated_tests_no_edit = 0
    repeated_unchanged_failures = 0
    failure_to_pass = 0
    pass_to_failure = 0
    mutation_calls = 0
    failed_mutation_calls = 0
    mutation_target_revisits = 0
    inverse_edits = 0
    mutation_epoch = 0
    opaque_calls = 0

    for event in parsed.events:
        action_key = normalize_tool_action(event.name, event.arguments)
        repeated_actions += int(action_counts[action_key] > 0)
        action_counts[action_key] += 1

        supported = event.name in _DIRECT_SEMANTIC_TOOLS
        opaque_calls += int(not supported)

        read_target = _read_target(event)
        if read_target is not None:
            repeated_reads += int(read_counts[read_target] > 0)
            read_counts[read_target] += 1

        search_key = _search_action_key(event)
        if search_key is not None:
            repeated_searches += int(search_counts[search_key] > 0)
            search_counts[search_key] += 1

        if event.name in _MUTATION_TOOLS:
            if event.is_error is True:
                failed_mutation_calls += 1
            elif event.is_error is False:
                mutation_calls += 1
                mutation_epoch += 1
                targets = _mutation_targets(event.arguments)
                for target in targets:
                    mutation_target_revisits += int(
                        successful_mutation_targets[target] > 0
                    )
                    successful_mutation_targets[target] += 1
                for target, old_text, new_text in _edit_replacements(event.arguments):
                    previous = prior_edit_pairs.setdefault(target, [])
                    inverse_edits += int((new_text, old_text) in previous)
                    previous.append((old_text, new_text))

        test_key = _test_action_key(event)
        if test_key is None or event.is_error is None:
            continue
        observable_tests += 1
        status = "fail" if event.is_error else "pass"
        fingerprint = _result_fingerprint(event.result_text or "")
        previous_test = prior_test.get(test_key)
        if previous_test is not None:
            previous_epoch, previous_status, previous_fingerprint = previous_test
            if previous_epoch == mutation_epoch:
                repeated_tests_no_edit += 1
                if (
                    status == "fail"
                    and previous_status == "fail"
                    and fingerprint == previous_fingerprint
                ):
                    repeated_unchanged_failures += 1
            failure_to_pass += int(previous_status == "fail" and status == "pass")
            pass_to_failure += int(previous_status == "pass" and status == "fail")
        prior_test[test_key] = (mutation_epoch, status, fingerprint)

    strategy_reset_turns = sum(
        bool(_STRATEGY_RESET_RE.search(text)) for text in parsed.assistant_text_by_turn
    )
    tool_calls = parsed.tool_calls
    return {
        "repeated_normalized_tool_actions": repeated_actions,
        "repeated_normalized_tool_action_rate": _rate(repeated_actions, tool_calls),
        "repeated_read_targets": repeated_reads,
        "repeated_read_target_rate": _rate(repeated_reads, sum(read_counts.values())),
        "repeated_search_actions": repeated_searches,
        "repeated_search_action_rate": _rate(
            repeated_searches, sum(search_counts.values())
        ),
        "observable_test_runs": observable_tests,
        "repeated_tests_without_observed_edit": repeated_tests_no_edit,
        "repeated_unchanged_test_failures": repeated_unchanged_failures,
        "test_failure_to_pass_transitions": failure_to_pass,
        "test_pass_to_failure_transitions": pass_to_failure,
        "direct_mutation_calls": mutation_calls,
        "failed_direct_mutation_calls": failed_mutation_calls,
        "direct_mutation_target_revisits": mutation_target_revisits,
        "exact_inverse_edit_pairs": inverse_edits,
        "strategy_reset_turns": strategy_reset_turns,
        "strategy_reset_turn_rate": _rate(strategy_reset_turns, parsed.assistant_turns),
        "opaque_top_level_tool_calls": opaque_calls,
        "semantic_event_coverage": _rate(tool_calls - opaque_calls, tool_calls),
    }


def terminal_session_is_truncated(parsed: NativeSessionParse) -> bool:
    """Return true only for an explicit terminal output-limit stop reason."""
    reason = (parsed.terminal_stop_reason or "").strip().lower()
    return reason in _TRUNCATION_STOP_REASONS


def _normalize_argument_value(value: Any, *, key: str | None) -> Any:
    if isinstance(value, dict):
        return {
            str(item_key): _normalize_argument_value(item_value, key=str(item_key))
            for item_key, item_value in sorted(
                value.items(), key=lambda item: str(item[0])
            )
        }
    if isinstance(value, list):
        return [_normalize_argument_value(item, key=key) for item in value]
    if isinstance(value, tuple):
        return [_normalize_argument_value(item, key=key) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if not isinstance(value, str):
        return value
    if key and key.lower() in {"path", "file", "filename", "cwd"}:
        return _normalize_path(value)
    if key and key.lower() in {"command", "cmd"}:
        return " ".join(value.split())
    return value.replace("\r\n", "\n").strip()


def _normalize_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    for prefix in ("/app/", "/workspace/"):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return posixpath.normpath(normalized)


def _read_target(event: ToolEvent) -> str | None:
    if event.name not in _READ_TOOLS or not isinstance(event.arguments, dict):
        return None
    path = event.arguments.get("path")
    return _normalize_path(path) if isinstance(path, str) else None


def _search_action_key(event: ToolEvent) -> str | None:
    if event.name in _SEARCH_TOOLS:
        return normalize_tool_action(event.name, event.arguments)
    command = _command_argument(event)
    if event.name == "bash" and command and _SEARCH_COMMAND_RE.search(command):
        return normalize_tool_action(event.name, event.arguments)
    return None


def _test_action_key(event: ToolEvent) -> str | None:
    command = _command_argument(event)
    if event.name == "bash" and command and _TEST_COMMAND_RE.search(command):
        return normalize_tool_action(event.name, event.arguments)
    return None


def _command_argument(event: ToolEvent) -> str | None:
    if not isinstance(event.arguments, dict):
        return None
    command = event.arguments.get("command", event.arguments.get("cmd"))
    return command if isinstance(command, str) else None


def _mutation_targets(arguments: Any) -> list[str]:
    targets: list[str] = []
    if isinstance(arguments, dict):
        path = arguments.get("path")
        if isinstance(path, str):
            targets.append(_normalize_path(path))
        edits = arguments.get("edits")
        if isinstance(edits, list):
            for edit in edits:
                if not isinstance(edit, dict):
                    continue
                edit_path = edit.get("path", path)
                if isinstance(edit_path, str):
                    targets.append(_normalize_path(edit_path))
    return sorted(set(targets))


def _edit_replacements(arguments: Any) -> list[tuple[str, str, str]]:
    if not isinstance(arguments, dict):
        return []
    replacements: list[tuple[str, str, str]] = []
    outer_path = arguments.get("path")
    candidates = [arguments]
    if isinstance(arguments.get("edits"), list):
        candidates = [item for item in arguments["edits"] if isinstance(item, dict)]
    for edit in candidates:
        path = edit.get("path", outer_path)
        old_text = edit.get("oldText", edit.get("old_text"))
        new_text = edit.get("newText", edit.get("new_text"))
        if all(isinstance(value, str) for value in (path, old_text, new_text)):
            replacements.append((_normalize_path(path), str(old_text), str(new_text)))
    return replacements


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "" if content is None else str(content)
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and "text" in block:
            parts.append(str(block.get("text") or ""))
        elif isinstance(block, dict):
            parts.append(json.dumps(block, ensure_ascii=False, sort_keys=True))
    return "\n".join(parts)


def _result_fingerprint(text: str) -> str:
    normalized = _ANSI_RE.sub("", text).replace("\r\n", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.strip().splitlines())
    return hashlib.sha256(normalized.encode()).hexdigest()


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 8) if denominator else 0.0
