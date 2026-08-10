"""Build fixed, bounded feedback candidate units from deterministic packets."""

from __future__ import annotations

import json
from typing import Any

CANDIDATE_UNIT_SCHEMA_VERSION = 1
MAX_CANDIDATE_WINDOW_BYTES = 32_768
MAX_CONTEXT_ASSISTANT_RESPONSES = 3
MAX_CONTEXT_TOOL_CALLS_PER_RESPONSE = 2
MAX_TEXT_EXCERPT_CHARS = 300
MAX_TEXT_EXCERPTS = 2
MAX_ARGUMENT_DICT_ITEMS = 12
MAX_ARGUMENT_LIST_ITEMS = 3


def bounded_candidate_text_excerpts(
    text: str,
    *,
    focus_spans: list[tuple[int, int]] | None = None,
    max_excerpts: int = MAX_TEXT_EXCERPTS,
) -> list[dict[str, Any]]:
    """Return bounded exact excerpts, prioritizing deterministic focus spans."""
    if not text or max_excerpts <= 0:
        return []
    ranges: list[tuple[int, int]] = []
    for focus_start, focus_end in focus_spans or []:
        if not (0 <= focus_start < focus_end <= len(text)):
            continue
        excerpt_start = max(0, focus_start - MAX_TEXT_EXCERPT_CHARS // 3)
        excerpt_end = min(len(text), excerpt_start + MAX_TEXT_EXCERPT_CHARS)
        excerpt_start = max(0, excerpt_end - MAX_TEXT_EXCERPT_CHARS)
        ranges.append((excerpt_start, excerpt_end))
        if len(ranges) == max_excerpts:
            break
    if not ranges:
        if len(text) <= MAX_TEXT_EXCERPT_CHARS:
            ranges = [(0, len(text))]
        else:
            ranges = [
                (0, MAX_TEXT_EXCERPT_CHARS),
                (len(text) - MAX_TEXT_EXCERPT_CHARS, len(text)),
            ][:max_excerpts]
    unique_ranges = list(dict.fromkeys(ranges))[:max_excerpts]
    return [
        {
            "text": text[start:end],
            "start_char": start,
            "end_char": end,
        }
        for start, end in unique_ranges
    ]


def compact_candidate_value(value: Any) -> Any:
    """Bound strings and containers while retaining their exact source excerpts."""
    if isinstance(value, str):
        return {
            "value_kind": "string_excerpt",
            "source_length": len(value),
            "excerpts": bounded_candidate_text_excerpts(value, max_excerpts=2),
        }
    if isinstance(value, dict):
        items = list(value.items())
        return {
            "value_kind": "object",
            "source_item_count": len(items),
            "items": {
                str(key): compact_candidate_value(child)
                for key, child in items[:MAX_ARGUMENT_DICT_ITEMS]
            },
            "omitted_item_count": max(0, len(items) - MAX_ARGUMENT_DICT_ITEMS),
        }
    if isinstance(value, list):
        return {
            "value_kind": "array",
            "source_item_count": len(value),
            "items": [
                compact_candidate_value(child)
                for child in value[:MAX_ARGUMENT_LIST_ITEMS]
            ],
            "omitted_item_count": max(0, len(value) - MAX_ARGUMENT_LIST_ITEMS),
        }
    return value


def compact_candidate_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retain detector identity and exact spans without copying unbounded match text."""
    return [
        {
            "signal_type": signal.get("signal_type"),
            "detector_id": signal.get("detector_id"),
            "source_kind": signal.get("source_kind"),
            "start_char": signal.get("start_char"),
            "end_char": signal.get("end_char"),
            "matched_text": compact_candidate_value(signal.get("matched_text")),
        }
        for signal in signals
    ]


def tool_event_source_references(event: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    """Return exact action and optional observation source addresses."""
    action_source = {
        "session_path": event["action_session_path"],
        "jsonl_line": event["action_jsonl_line"],
        "record_id": event["action_event_id"],
        "tool_call_id": event["tool_call_id"],
    }
    observation_source = (
        {
            "session_path": event["observation_session_path"],
            "jsonl_line": event["observation_jsonl_line"],
            "record_id": event["observation_event_id"],
            "tool_call_id": event["observation_tool_call_id"],
        }
        if event.get("observation_event_id") is not None
        else None
    )
    return action_source, observation_source


def compact_tool_event(event: dict[str, Any]) -> dict[str, Any]:
    """Build one bounded tool action/result view with exact source references."""
    action_source, observation_source = tool_event_source_references(event)
    focus_spans = [
        (signal["start_char"], signal["end_char"])
        for signal in event["candidate_signals"]
        if signal.get("source_kind") == "observation_text"
        and isinstance(signal.get("start_char"), int)
        and isinstance(signal.get("end_char"), int)
    ]
    observation_text = event.get("observation_text")
    return {
        "action_event_ordinal": event["action_event_ordinal"],
        "assistant_response_ordinal": event["assistant_response_ordinal"],
        "tool_call_id": event["tool_call_id"],
        "tool_name": event["tool_name"],
        "tool_kind": event["tool_kind"],
        "is_validation_command": event["is_validation_command"],
        "action_source": action_source,
        "tool_arguments": compact_candidate_value(event.get("tool_arguments")),
        "raw_result_signature": event["raw_result_signature"],
        "raw_result_facts": event["raw_result_facts"],
        "candidate_signal_types": event["candidate_signal_types"],
        "candidate_signals": compact_candidate_signals(event["candidate_signals"]),
        "observation_source": observation_source,
        "observation_text": {
            "source_length": len(observation_text)
            if isinstance(observation_text, str)
            else None,
            "excerpts": bounded_candidate_text_excerpts(
                observation_text or "", focus_spans=focus_spans
            ),
        },
    }


def compact_assistant_response(
    response: dict[str, Any],
    event_by_call_id: dict[str, dict[str, Any]],
    *,
    include_tool_events: bool = True,
) -> dict[str, Any]:
    """Build one bounded assistant response and optional linked tool events."""
    linked_call_ids = (
        response["tool_call_ids"][:MAX_CONTEXT_TOOL_CALLS_PER_RESPONSE]
        if include_tool_events
        else []
    )
    linked_events = [event_by_call_id[call_id] for call_id in linked_call_ids]
    return {
        "assistant_response_ordinal": response["assistant_response_ordinal"],
        "assistant_event_id": response["assistant_event_id"],
        "source": {
            "session_path": response["session_path"],
            "jsonl_line": response["jsonl_line"],
            "record_id": response["assistant_event_id"],
        },
        "stop_reason": response["stop_reason"],
        "error_message": compact_candidate_value(response["error_message"]),
        "diagnostics": compact_candidate_value(response["diagnostics"]),
        "candidate_signal_types": response["candidate_signal_types"],
        "candidate_signals": compact_candidate_signals(response["candidate_signals"]),
        "text_snippets": response["text_snippets"],
        "source_tool_call_count": len(response["tool_call_ids"]),
        "tool_events": [compact_tool_event(event) for event in linked_events],
        "omitted_tool_call_count": len(response["tool_call_ids"])
        - len(linked_call_ids),
    }


def candidate_unit_id(
    packet: dict[str, Any], *, source_event_kind: str, ordinal: int
) -> str:
    """Return the stable source-derived ID for one fixed feedback candidate."""
    suffix = (
        f"assistant-response-{ordinal}"
        if source_event_kind == "assistant_response"
        else f"tool-call-{ordinal}"
    )
    return f"{packet['trajectory_id']}/{suffix}"


def build_packet_feedback_candidate_units(
    packet: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build every bounded candidate unit for one deterministic trajectory packet."""
    event_by_call_id = {event["tool_call_id"]: event for event in packet["events"]}
    response_by_event_id = {
        response["assistant_event_id"]: response
        for response in packet["assistant_responses"]
    }
    candidate_sources: list[tuple[int, int, str, dict[str, Any]]] = []
    for response in packet["assistant_responses"]:
        if response["candidate_signals"]:
            candidate_sources.append(
                (
                    response["record_order"],
                    0,
                    "assistant_response",
                    response,
                )
            )
    for event in packet["events"]:
        if event["candidate_signals"]:
            candidate_sources.append(
                (event["action_record_order"], 1, "tool_call_result", event)
            )
    candidate_sources.sort(key=lambda item: (item[0], item[1]))

    candidate_ids_by_assistant_event: dict[str, list[str]] = {}
    for _, _, source_event_kind, source in candidate_sources:
        ordinal = (
            source["assistant_response_ordinal"]
            if source_event_kind == "assistant_response"
            else source["action_event_ordinal"]
        )
        source_assistant_event_id = (
            source["assistant_event_id"]
            if source_event_kind == "assistant_response"
            else source["action_event_id"]
        )
        candidate_ids_by_assistant_event.setdefault(
            source_assistant_event_id, []
        ).append(
            candidate_unit_id(
                packet, source_event_kind=source_event_kind, ordinal=ordinal
            )
        )

    units = []
    for _, _, source_event_kind, source in candidate_sources:
        if source_event_kind == "assistant_response":
            ordinal = source["assistant_response_ordinal"]
            anchor_record_order = source["record_order"]
            source_assistant_event_id = source["assistant_event_id"]
            focal_event = compact_assistant_response(source, event_by_call_id)
        else:
            ordinal = source["action_event_ordinal"]
            anchor_record_order = (
                source.get("observation_record_order") or source["action_record_order"]
            )
            source_assistant_event_id = source["action_event_id"]
            focal_event = compact_tool_event(source)
        unit_id = candidate_unit_id(
            packet, source_event_kind=source_event_kind, ordinal=ordinal
        )
        following_responses = [
            response
            for response in packet["assistant_responses"]
            if response["record_order"] > anchor_record_order
        ][:MAX_CONTEXT_ASSISTANT_RESPONSES]
        related_ids = [
            related_id
            for related_id in candidate_ids_by_assistant_event.get(
                source_assistant_event_id, []
            )
            if related_id != unit_id
        ]
        unit = {
            "candidate_unit_schema_version": CANDIDATE_UNIT_SCHEMA_VERSION,
            "candidate_unit_id": unit_id,
            "trajectory_id": packet["trajectory_id"],
            "model_key": packet["model_key"],
            "model_role": packet["model_role"],
            "task": packet["task"],
            "rep": packet["rep"],
            "result_path": packet["result_path"],
            "result_outcome": packet["result_outcome"],
            "termination_kind": packet["termination_kind"],
            "source_event_kind": source_event_kind,
            "source_event_ordinal": ordinal,
            "related_candidate_unit_ids": related_ids,
            "focal_event": focal_event,
            "focal_assistant_response": (
                None
                if source_event_kind == "assistant_response"
                else compact_assistant_response(
                    response_by_event_id[source_assistant_event_id],
                    event_by_call_id,
                    include_tool_events=False,
                )
            ),
            "following_assistant_responses": [
                compact_assistant_response(response, event_by_call_id)
                for response in following_responses
            ],
            "context_bounds": {
                "following_assistant_response_limit": MAX_CONTEXT_ASSISTANT_RESPONSES,
                "following_assistant_responses_included": len(following_responses),
                "following_context_censored": len(
                    [
                        response
                        for response in packet["assistant_responses"]
                        if response["record_order"] > anchor_record_order
                    ]
                )
                > len(following_responses),
            },
        }
        units.append(unit)
    return units


def build_feedback_candidate_units(
    packets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the fixed bounded candidate population in packet/source order."""
    return [
        unit
        for packet in packets
        for unit in build_packet_feedback_candidate_units(packet)
    ]


def first_candidate_unit_difference(
    expected: Any, actual: Any, path: str = "candidate_units"
) -> str | None:
    """Return the first field that differs from a deterministic candidate rebuild."""
    if type(expected) is not type(actual):
        return path
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return f"{path}.keys"
        for key in expected:
            difference = first_candidate_unit_difference(
                expected[key], actual[key], f"{path}.{key}"
            )
            if difference is not None:
                return difference
        return None
    if isinstance(expected, list):
        if len(expected) != len(actual):
            return f"{path}.length"
        for index, (expected_item, actual_item) in enumerate(
            zip(expected, actual, strict=True)
        ):
            difference = first_candidate_unit_difference(
                expected_item, actual_item, f"{path}[{index}]"
            )
            if difference is not None:
                return difference
        return None
    return None if expected == actual else path


def validate_feedback_candidate_units(
    units: list[dict[str, Any]], *, packets: list[dict[str, Any]]
) -> None:
    """Fail closed unless candidate units exactly rebuild and satisfy size bounds."""
    expected_units = build_feedback_candidate_units(packets)
    difference = first_candidate_unit_difference(expected_units, units)
    if difference is not None:
        raise ValueError(
            "Feedback uptake candidates: units differ from deterministic packets at "
            + difference
        )
    candidate_ids = [unit["candidate_unit_id"] for unit in units]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Feedback uptake candidates: duplicate candidate unit IDs")
    candidate_id_set = set(candidate_ids)
    for unit in units:
        if unit["candidate_unit_schema_version"] != CANDIDATE_UNIT_SCHEMA_VERSION:
            raise ValueError(
                "Feedback uptake candidates: invalid candidate unit schema version"
            )
        serialized = json.dumps(
            unit, ensure_ascii=False, separators=(",", ":")
        ).encode()
        if len(serialized) > MAX_CANDIDATE_WINDOW_BYTES:
            raise ValueError(
                "Feedback uptake candidates: bounded window exceeds byte limit for "
                + unit["candidate_unit_id"]
            )
        if any(
            related_id not in candidate_id_set
            for related_id in unit["related_candidate_unit_ids"]
        ):
            raise ValueError(
                "Feedback uptake candidates: unknown related candidate unit ID for "
                + unit["candidate_unit_id"]
            )
