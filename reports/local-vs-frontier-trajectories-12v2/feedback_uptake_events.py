"""Build auditable raw event packets for feedback-uptake annotation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build_analysis import compact_result
from feedback_uptake_candidate_signals import (
    candidate_signal_types,
    detect_assistant_response_candidate_signals,
    detect_tool_result_candidate_signals,
)
from trajectory_evidence import is_validation_command

MODEL_ROLES = {
    "frontier": "frontier_reference",
    "agentworld": "local_subject",
    "thinkingcap": "local_subject",
}
MIN_SOURCE_SNIPPET_CHARS = 20
MAX_SOURCE_SNIPPET_CHARS = 300
COMMAND_EXIT_CODE_PATTERN = re.compile(
    r"(?:^|\n)Command exited with code ([0-9]+)(?:\n|$)"
)


@dataclass(frozen=True)
class OrderedSessionRecord:
    """One session JSONL record with its canonical source address and global order."""

    session_path: Path
    jsonl_line: int
    record_order: int
    record: dict[str, Any]


def load_ordered_session_records(
    cell_root: Path,
) -> tuple[list[OrderedSessionRecord], list[dict[str, str]]]:
    """Load every session record strictly in filename and JSONL line order."""
    session_paths = sorted((cell_root / "session").glob("*.jsonl"))
    if not session_paths:
        raise ValueError(f"Feedback uptake events: no session files in {cell_root}")

    ordered_records: list[OrderedSessionRecord] = []
    sessions: list[dict[str, str]] = []
    record_order = 0
    for session_path in session_paths:
        session_headers: list[dict[str, Any]] = []
        for jsonl_line, raw_line in enumerate(
            session_path.read_text(errors="replace").splitlines(), start=1
        ):
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Feedback uptake events: invalid session JSON at "
                    f"{session_path}:{jsonl_line}"
                ) from error
            if not isinstance(record, dict):
                raise TypeError(
                    "Feedback uptake events: session record is not an object at "
                    f"{session_path}:{jsonl_line}"
                )
            record_order += 1
            source_record = OrderedSessionRecord(
                session_path=session_path.resolve(),
                jsonl_line=jsonl_line,
                record_order=record_order,
                record=record,
            )
            ordered_records.append(source_record)
            if record.get("type") == "session":
                session_headers.append(record)

        if len(session_headers) != 1 or not isinstance(
            session_headers[0].get("id"), str
        ):
            raise ValueError(
                "Feedback uptake events: expected one session header with an ID in "
                f"{session_path}"
            )
        sessions.append(
            {
                "session_id": session_headers[0]["id"],
                "session_path": str(session_path.resolve()),
            }
        )
    return ordered_records, sessions


def bounded_source_snippets(
    text: str, *, focus_span: tuple[int, int] | None = None
) -> list[dict[str, Any]]:
    """Return one or two exact 20–300 character excerpts from one source string."""
    if len(text) < MIN_SOURCE_SNIPPET_CHARS:
        return []
    if len(text) <= MAX_SOURCE_SNIPPET_CHARS:
        ranges = [(0, len(text))]
    elif focus_span is not None:
        focus_start, focus_end = focus_span
        excerpt_start = max(0, focus_start - MAX_SOURCE_SNIPPET_CHARS // 3)
        excerpt_end = min(len(text), excerpt_start + MAX_SOURCE_SNIPPET_CHARS)
        excerpt_start = max(0, excerpt_end - MAX_SOURCE_SNIPPET_CHARS)
        if excerpt_end < focus_end:
            excerpt_end = focus_end
            excerpt_start = excerpt_end - MAX_SOURCE_SNIPPET_CHARS
        ranges = [(excerpt_start, excerpt_end)]
    elif len(text) <= MAX_SOURCE_SNIPPET_CHARS * 2:
        half = MAX_SOURCE_SNIPPET_CHARS // 2
        ranges = [(0, half), (len(text) - half, len(text))]
    else:
        ranges = [
            (0, MAX_SOURCE_SNIPPET_CHARS),
            (len(text) - MAX_SOURCE_SNIPPET_CHARS, len(text)),
        ]
    return [
        {"text": text[start:end], "start_char": start, "end_char": end}
        for start, end in ranges
    ]


def iter_feedback_argument_strings(
    value: Any, argument_path: tuple[str | int, ...] = ()
) -> list[tuple[tuple[str | int, ...], str]]:
    """Return every exact string leaf and address from recorded tool arguments."""
    if isinstance(value, str):
        return [(argument_path, value)]
    if isinstance(value, dict):
        strings = []
        for key, child in value.items():
            strings.extend(iter_feedback_argument_strings(child, (*argument_path, key)))
        return strings
    if isinstance(value, list):
        strings = []
        for index, child in enumerate(value):
            strings.extend(
                iter_feedback_argument_strings(child, (*argument_path, index))
            )
        return strings
    return []


def build_feedback_source_snippets(
    event: dict[str, Any],
    observation_text: str | None,
    candidate_signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build source-addressed evidence excerpts without paraphrase or semantic labels."""
    if observation_text is not None:
        focused_signal = next(
            (
                signal
                for signal in candidate_signals
                if signal.get("source_kind") == "observation_text"
                and isinstance(signal.get("start_char"), int)
                and isinstance(signal.get("end_char"), int)
            ),
            None,
        )
        focus_span = (
            (focused_signal["start_char"], focused_signal["end_char"])
            if focused_signal is not None
            else None
        )
        snippets = bounded_source_snippets(observation_text, focus_span=focus_span)
        if snippets:
            return [
                {
                    **snippet,
                    "source_kind": "observation_text",
                    "session_path": event["observation_session_path"],
                    "jsonl_line": event["observation_jsonl_line"],
                }
                for snippet in snippets
            ]

    for argument_path, argument_text in iter_feedback_argument_strings(
        event.get("tool_arguments")
    ):
        snippets = bounded_source_snippets(argument_text)
        if snippets:
            return [
                {
                    **snippet,
                    "source_kind": "tool_arguments",
                    "session_path": event["action_session_path"],
                    "jsonl_line": event["action_jsonl_line"],
                    "argument_path": list(argument_path),
                }
                for snippet in snippets[:1]
            ]
    return []


def extract_tool_result_text(message: dict[str, Any]) -> str:
    """Join exact text blocks from one tool result in recorded block order."""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(block.get("text", ""))
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def classify_feedback_tool_kind(tool_name: str, tool_arguments: Any) -> str:
    """Classify the mechanical tool surface without assigning action purpose."""
    if tool_name == "bash":
        command = (
            str(tool_arguments.get("command", ""))
            if isinstance(tool_arguments, dict)
            else ""
        )
        return (
            "validation_command" if is_validation_command(command) else "shell_command"
        )
    if tool_name == "read":
        return "repository_read"
    if tool_name in {"edit", "write"}:
        return "repository_mutation"
    return "other_tool"


def classify_feedback_result_kind(tool_name: str, has_result: bool) -> str:
    """Classify only the result's mechanical surface, not its semantic outcome."""
    if not has_result:
        return "missing_result"
    return {
        "bash": "command_result",
        "read": "read_result",
        "edit": "edit_result",
        "write": "write_result",
    }.get(tool_name, "other_result")


def parse_explicit_command_exit_code(tool_name: str, result_text: str) -> int | None:
    """Parse an exit code only from an explicit recorded shell-result marker."""
    if tool_name != "bash":
        return None
    match = COMMAND_EXIT_CODE_PATTERN.search(result_text)
    return int(match.group(1)) if match else None


def classify_raw_result_signature(
    *, has_result: bool, reported_is_error: Any, explicit_exit_code: int | None
) -> str:
    """Describe only recorded result state without interpreting its meaning."""
    if not has_result:
        return "observation_missing"
    if explicit_exit_code is not None and explicit_exit_code != 0:
        return "explicit_nonzero_exit"
    return "reported_error" if reported_is_error is True else "reported_success"


def derive_feedback_termination_kind(
    result: dict[str, Any], *, has_final_assistant_text: bool
) -> str:
    """Derive termination from saved result fields and observable final text."""
    agent_exit = result.get("agent_exit")
    if result.get("agent_timed_out") is True or agent_exit == "timeout":
        return "agent_timeout"
    if isinstance(agent_exit, int) and not isinstance(agent_exit, bool):
        if agent_exit != 0:
            return "agent_nonzero"
        return "normal_final" if has_final_assistant_text else "normal_no_final_text"
    return "unknown"


def build_feedback_uptake_packet(
    *, model_key: str, task: str, rep: int, cell_root: Path
) -> dict[str, Any]:
    """Build one compact trajectory packet with exact call/result evidence links."""
    if model_key not in MODEL_ROLES:
        raise ValueError(f"Feedback uptake events: unknown model key {model_key!r}")

    records, sessions = load_ordered_session_records(cell_root)
    result_path = (cell_root / "result.json").resolve()
    result = json.loads(result_path.read_text())
    if result.get("task") != task or result.get("rep") != rep:
        raise ValueError(
            f"Feedback uptake events: result identity mismatch at {result_path}"
        )

    tool_results: dict[str, OrderedSessionRecord] = {}
    assistant_turn = 0
    events: list[dict[str, Any]] = []
    event_source_orders: dict[str, int] = {}
    group_call_ids: dict[str, list[str]] = {}
    assistant_actions: list[dict[str, Any]] = []
    assistant_responses: list[dict[str, Any]] = []
    final_text_action: dict[str, Any] | None = None

    for source_record in records:
        record = source_record.record
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role == "toolResult":
            tool_call_id = message.get("toolCallId")
            if not isinstance(tool_call_id, str) or not tool_call_id:
                raise ValueError(
                    "Feedback uptake events: tool result without toolCallId at "
                    f"{source_record.session_path}:{source_record.jsonl_line}"
                )
            if tool_call_id in tool_results:
                raise ValueError(
                    f"Feedback uptake events: duplicate result for {tool_call_id}"
                )
            tool_results[tool_call_id] = source_record
            continue
        if role != "assistant":
            continue

        assistant_turn += 1
        event_id = record.get("id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError(
                "Feedback uptake events: assistant message without record ID at "
                f"{source_record.session_path}:{source_record.jsonl_line}"
            )
        content = message.get("content")
        blocks = content if isinstance(content, list) else []
        assistant_text = "\n".join(
            str(block.get("text", ""))
            for block in blocks
            if isinstance(block, dict)
            and block.get("type") == "text"
            and block.get("text")
        )
        message_tool_calls: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "toolCall":
                continue
            tool_call_id = block.get("id")
            tool_name = block.get("name")
            if not isinstance(tool_call_id, str) or not tool_call_id:
                raise ValueError(
                    "Feedback uptake events: tool call without ID at "
                    f"{source_record.session_path}:{source_record.jsonl_line}"
                )
            if tool_call_id in event_source_orders:
                raise ValueError(
                    f"Feedback uptake events: duplicate tool call ID {tool_call_id}"
                )
            if not isinstance(tool_name, str) or not tool_name:
                raise ValueError(
                    f"Feedback uptake events: tool call {tool_call_id} has no name"
                )
            tool_arguments = block.get("arguments")
            action_event_ordinal = len(events) + 1
            command = (
                str(tool_arguments.get("command", ""))
                if tool_name == "bash" and isinstance(tool_arguments, dict)
                else None
            )
            event = {
                "action_event_ordinal": action_event_ordinal,
                "assistant_response_ordinal": assistant_turn,
                "assistant_turn": assistant_turn,
                "parallel_group_id": event_id,
                "action_event_id": event_id,
                "action_session_path": str(source_record.session_path),
                "action_jsonl_line": source_record.jsonl_line,
                "action_record_order": source_record.record_order,
                "action_timestamp": record.get("timestamp"),
                "tool_call_id": tool_call_id,
                "tool_name": tool_name,
                "tool_arguments": tool_arguments,
                "tool_kind": classify_feedback_tool_kind(tool_name, tool_arguments),
                "is_validation_command": bool(
                    tool_name == "bash" and command and is_validation_command(command)
                ),
                "command": command,
            }
            events.append(event)
            event_source_orders[tool_call_id] = source_record.record_order
            message_tool_calls.append(
                {
                    "action_event_ordinal": action_event_ordinal,
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                }
            )

        diagnostics_value = message.get("diagnostics")
        diagnostics = diagnostics_value if isinstance(diagnostics_value, list) else []
        response_candidate_signals = detect_assistant_response_candidate_signals(
            stop_reason=message.get("stopReason"),
            error_message=message.get("errorMessage"),
            diagnostics=diagnostics,
        )
        assistant_responses.append(
            {
                "assistant_response_ordinal": assistant_turn,
                "assistant_event_id": event_id,
                "session_path": str(source_record.session_path),
                "jsonl_line": source_record.jsonl_line,
                "record_order": source_record.record_order,
                "timestamp": record.get("timestamp"),
                "stop_reason": message.get("stopReason"),
                "error_message": message.get("errorMessage"),
                "diagnostics": diagnostics,
                "tool_call_ids": [
                    tool_call["tool_call_id"] for tool_call in message_tool_calls
                ],
                "text_snippets": bounded_source_snippets(assistant_text),
                "candidate_signals": response_candidate_signals,
                "candidate_signal_types": candidate_signal_types(
                    response_candidate_signals
                ),
            }
        )
        if message_tool_calls:
            group_call_ids[event_id] = [
                tool_call["tool_call_id"] for tool_call in message_tool_calls
            ]
            assistant_actions.append(
                {
                    "record_order": source_record.record_order,
                    "assistant_event_id": event_id,
                    "assistant_turn": assistant_turn,
                    "session_path": str(source_record.session_path),
                    "jsonl_line": source_record.jsonl_line,
                    "timestamp": record.get("timestamp"),
                    "kind": "tool_calls",
                    "tool_calls": message_tool_calls,
                }
            )
            final_text_action = None
        elif assistant_text:
            final_text_action = {
                "record_order": source_record.record_order,
                "assistant_event_id": event_id,
                "assistant_turn": assistant_turn,
                "session_path": str(source_record.session_path),
                "jsonl_line": source_record.jsonl_line,
                "timestamp": record.get("timestamp"),
                "kind": "final_text",
                "tool_calls": [],
                "text_snippets": bounded_source_snippets(assistant_text),
            }
        else:
            final_text_action = None

    if final_text_action is not None:
        assistant_actions.append(final_text_action)

    call_ids = set(event_source_orders)
    orphan_result_ids = sorted(set(tool_results) - call_ids)
    if orphan_result_ids:
        raise ValueError(
            "Feedback uptake events: results reference unknown tool calls: "
            + ", ".join(orphan_result_ids)
        )

    for event in events:
        tool_call_id = event["tool_call_id"]
        result_source = tool_results.get(tool_call_id)
        if result_source is None:
            candidate_signals = detect_tool_result_candidate_signals(
                tool_name=event["tool_name"],
                result_text="",
                reported_is_error=None,
                has_result=False,
                explicit_exit_code=None,
            )
            event.update(
                {
                    "result_kind": classify_feedback_result_kind(
                        event["tool_name"], False
                    ),
                    "raw_result_signature": classify_raw_result_signature(
                        has_result=False,
                        reported_is_error=None,
                        explicit_exit_code=None,
                    ),
                    "raw_result_facts": {
                        "has_result": False,
                        "reported_is_error": None,
                        "explicit_exit_code": None,
                    },
                    "candidate_signals": candidate_signals,
                    "candidate_signal_types": candidate_signal_types(candidate_signals),
                    "raw_exit_code": None,
                    "observation_event_id": None,
                    "observation_tool_call_id": None,
                    "observation_session_path": None,
                    "observation_jsonl_line": None,
                    "observation_record_order": None,
                    "observation_timestamp": None,
                    "observation_tool_name": None,
                    "observation_is_error": None,
                    "observation_text": None,
                }
            )
            event["source_snippets"] = build_feedback_source_snippets(
                event, None, candidate_signals
            )
            continue
        if result_source.record_order <= event_source_orders[tool_call_id]:
            raise ValueError(
                f"Feedback uptake events: result precedes tool call {tool_call_id}"
            )
        result_record = result_source.record
        result_message = result_record["message"]
        observation_text = extract_tool_result_text(result_message)
        explicit_exit_code = parse_explicit_command_exit_code(
            event["tool_name"], observation_text
        )
        reported_is_error = result_message.get("isError")
        candidate_signals = detect_tool_result_candidate_signals(
            tool_name=event["tool_name"],
            result_text=observation_text,
            reported_is_error=reported_is_error,
            has_result=True,
            explicit_exit_code=explicit_exit_code,
        )
        event.update(
            {
                "result_kind": classify_feedback_result_kind(event["tool_name"], True),
                "raw_result_signature": classify_raw_result_signature(
                    has_result=True,
                    reported_is_error=reported_is_error,
                    explicit_exit_code=explicit_exit_code,
                ),
                "raw_result_facts": {
                    "has_result": True,
                    "reported_is_error": reported_is_error,
                    "explicit_exit_code": explicit_exit_code,
                },
                "candidate_signals": candidate_signals,
                "candidate_signal_types": candidate_signal_types(candidate_signals),
                "raw_exit_code": explicit_exit_code,
                "observation_event_id": result_record.get("id"),
                "observation_tool_call_id": result_message.get("toolCallId"),
                "observation_session_path": str(result_source.session_path),
                "observation_jsonl_line": result_source.jsonl_line,
                "observation_record_order": result_source.record_order,
                "observation_timestamp": result_record.get("timestamp"),
                "observation_tool_name": result_message.get("toolName"),
                "observation_is_error": result_message.get("isError"),
                "observation_text": observation_text,
            }
        )
        event["source_snippets"] = build_feedback_source_snippets(
            event, observation_text, candidate_signals
        )

    actions_by_order = sorted(
        assistant_actions, key=lambda action: action["record_order"]
    )
    for event in events:
        group_ids = group_call_ids[event["parallel_group_id"]]
        group_results = [tool_results.get(call_id) for call_id in group_ids]
        if any(result_source is None for result_source in group_results):
            event["next_action"] = None
            continue
        observation_boundary = max(
            result_source.record_order
            for result_source in group_results
            if result_source is not None
        )
        next_action = next(
            (
                action
                for action in actions_by_order
                if action["record_order"] > observation_boundary
            ),
            None,
        )
        if next_action is None:
            event["next_action"] = None
        else:
            event["next_action"] = {
                **{
                    key: value
                    for key, value in next_action.items()
                    if key != "record_order"
                },
                "assistant_record_order": next_action["record_order"],
                "assistant_turn_distance": next_action["assistant_turn"]
                - event["assistant_turn"],
            }

    termination_kind = derive_feedback_termination_kind(
        result, has_final_assistant_text=final_text_action is not None
    )
    return {
        "schema_version": 3,
        "trajectory_id": f"{model_key}/{task}/rep{rep}",
        "model_key": model_key,
        "model_role": MODEL_ROLES[model_key],
        "task": task,
        "rep": rep,
        "result_path": str(result_path),
        "session_id": sessions[0]["session_id"] if len(sessions) == 1 else None,
        "session_paths": [session["session_path"] for session in sessions],
        "sessions": sessions,
        "result_outcome": compact_result(result),
        "termination_kind": termination_kind,
        "assistant_turns": assistant_turn,
        "assistant_response_count": len(assistant_responses),
        "assistant_error_count": sum(
            bool(response["candidate_signal_types"]) for response in assistant_responses
        ),
        "assistant_responses": assistant_responses,
        "tool_call_count": len(events),
        "missing_result_count": sum(
            event["observation_event_id"] is None for event in events
        ),
        "events": events,
    }
