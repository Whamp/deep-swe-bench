"""Validate complete feedback-uptake event packet populations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from build_analysis import RESULT_ROOTS
from feedback_uptake_candidate_signals import (
    candidate_signal_types,
    detect_assistant_response_candidate_signals,
    detect_tool_result_candidate_signals,
)
from feedback_uptake_events import (
    MAX_SOURCE_SNIPPET_CHARS,
    MIN_SOURCE_SNIPPET_CHARS,
    MODEL_ROLES,
    build_feedback_uptake_packet,
    classify_feedback_tool_kind,
    classify_raw_result_signature,
)
from trajectory_evidence import is_validation_command


def resolve_feedback_argument_string(
    tool_arguments: Any, argument_path: list[str | int]
) -> str | None:
    """Resolve one source-snippet path into the exact recorded argument string."""
    value = tool_arguments
    for key in argument_path:
        if isinstance(key, str):
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
            continue
        if (
            isinstance(key, int)
            and not isinstance(key, bool)
            and isinstance(value, list)
            and 0 <= key < len(value)
        ):
            value = value[key]
            continue
        return None
    return value if isinstance(value, str) else None


def first_feedback_source_difference(
    expected: Any, actual: Any, path: str = "packet"
) -> str | None:
    """Return the first deterministic packet field that differs from raw sources."""
    if type(expected) is not type(actual):
        return path
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            differing_key = min(str(key) for key in set(expected) ^ set(actual))
            return f"{path}.{differing_key}"
        for key in expected:
            difference = first_feedback_source_difference(
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
            difference = first_feedback_source_difference(
                expected_item, actual_item, f"{path}[{index}]"
            )
            if difference is not None:
                return difference
        return None
    return None if expected == actual else path


def validate_feedback_packet_against_sources(packet: dict[str, Any]) -> None:
    """Rebuild one packet from cited result/session files and require exact equality."""
    trajectory_id = packet.get("trajectory_id")
    result_path_value = packet.get("result_path")
    if not isinstance(result_path_value, str):
        raise TypeError(
            f"Feedback uptake validation: invalid source result path for {trajectory_id}"
        )
    result_path = Path(result_path_value)
    if result_path.name != "result.json" or not result_path.is_file():
        raise ValueError(
            f"Feedback uptake validation: unreadable source result for {trajectory_id}"
        )
    try:
        source_packet = build_feedback_uptake_packet(
            model_key=packet["model_key"],
            task=packet["task"],
            rep=packet["rep"],
            cell_root=result_path.parent,
        )
    except (KeyError, OSError, TypeError, ValueError) as error:
        raise ValueError(
            f"Feedback uptake validation: cannot rebuild source records for {trajectory_id}"
        ) from error
    difference = first_feedback_source_difference(source_packet, packet)
    if difference is not None:
        raise ValueError(
            "Feedback uptake validation: packet differs from source records at "
            f"{difference} for {trajectory_id}"
        )


def validate_feedback_uptake_packets(
    packets: list[dict[str, Any]], *, expected_tasks: list[str]
) -> None:
    """Fail closed unless packets form the exact auditable 108-trajectory population."""
    expected_model_keys = tuple(RESULT_ROOTS)
    expected_reps = range(3)
    if len(expected_tasks) != 12 or len(set(expected_tasks)) != 12:
        raise ValueError(
            "Feedback uptake validation: expected exactly 12 unique task names"
        )
    expected_addresses = {
        (model_key, task, rep)
        for model_key in expected_model_keys
        for task in expected_tasks
        for rep in expected_reps
    }
    if len(packets) != 108:
        raise ValueError(
            "Feedback uptake validation: expected exactly 108 packets, "
            f"found {len(packets)}"
        )

    addresses: list[tuple[str, str, int]] = []
    trajectory_ids: list[str] = []
    result_paths: list[str] = []
    for packet in packets:
        model_key = packet.get("model_key")
        task = packet.get("task")
        rep = packet.get("rep")
        if (
            not isinstance(model_key, str)
            or not isinstance(task, str)
            or not isinstance(rep, int)
        ):
            raise TypeError("Feedback uptake validation: invalid trajectory address")
        address = (model_key, task, rep)
        addresses.append(address)
        expected_trajectory_id = f"{model_key}/{task}/rep{rep}"
        if packet.get("trajectory_id") != expected_trajectory_id:
            raise ValueError(
                "Feedback uptake validation: trajectory ID does not match address "
                f"{address}"
            )
        trajectory_ids.append(expected_trajectory_id)
        if packet.get("model_role") != MODEL_ROLES.get(model_key):
            raise ValueError(
                f"Feedback uptake validation: invalid model role for {expected_trajectory_id}"
            )

        if packet.get("schema_version") != 3:
            raise ValueError(
                f"Feedback uptake validation: expected schema version 3 for {expected_trajectory_id}"
            )

        result_path = packet.get("result_path")
        if not isinstance(result_path, str) or not Path(result_path).is_absolute():
            raise ValueError(
                f"Feedback uptake validation: result path is not absolute for {expected_trajectory_id}"
            )
        result_paths.append(result_path)
        sessions = packet.get("sessions")
        if not isinstance(sessions, list) or not sessions:
            raise ValueError(
                f"Feedback uptake validation: no sessions for {expected_trajectory_id}"
            )
        session_paths = {
            session.get("session_path")
            for session in sessions
            if isinstance(session, dict)
            and isinstance(session.get("session_path"), str)
            and Path(session["session_path"]).is_absolute()
            and isinstance(session.get("session_id"), str)
            and session.get("session_id")
        }
        if len(session_paths) != len(sessions):
            raise ValueError(
                f"Feedback uptake validation: invalid session address for {expected_trajectory_id}"
            )
        if packet.get("session_paths") != [
            session["session_path"] for session in sessions
        ]:
            raise ValueError(
                f"Feedback uptake validation: session path list mismatch for {expected_trajectory_id}"
            )
        expected_session_id = sessions[0]["session_id"] if len(sessions) == 1 else None
        if packet.get("session_id") != expected_session_id:
            raise ValueError(
                f"Feedback uptake validation: session ID mismatch for {expected_trajectory_id}"
            )

        events = packet.get("events")
        if not isinstance(events, list) or packet.get("tool_call_count") != len(events):
            raise ValueError(
                f"Feedback uptake validation: tool-call count mismatch for {expected_trajectory_id}"
            )
        expected_ordinals = list(range(1, len(events) + 1))
        if [event.get("action_event_ordinal") for event in events] != expected_ordinals:
            raise ValueError(
                f"Feedback uptake validation: event order is not contiguous for {expected_trajectory_id}"
            )
        call_ids = [event.get("tool_call_id") for event in events]
        if any(not isinstance(call_id, str) or not call_id for call_id in call_ids):
            raise ValueError(
                f"Feedback uptake validation: invalid tool call ID for {expected_trajectory_id}"
            )
        if len(call_ids) != len(set(call_ids)):
            raise ValueError(
                f"Feedback uptake validation: duplicate tool call ID for {expected_trajectory_id}"
            )
        event_by_call_id: dict[str, dict[str, Any]] = {
            event["tool_call_id"]: event for event in events
        }
        assistant_responses = packet.get("assistant_responses")
        if not isinstance(assistant_responses, list) or packet.get(
            "assistant_response_count"
        ) != len(assistant_responses):
            raise ValueError(
                f"Feedback uptake validation: assistant-response count mismatch for {expected_trajectory_id}"
            )
        expected_response_ordinals = list(range(1, len(assistant_responses) + 1))
        if [
            response.get("assistant_response_ordinal")
            for response in assistant_responses
        ] != expected_response_ordinals:
            raise ValueError(
                f"Feedback uptake validation: assistant-response order is not contiguous for {expected_trajectory_id}"
            )
        response_by_event_id: dict[str, dict[str, Any]] = {}
        assistant_error_count = 0
        for response in assistant_responses:
            assistant_event_id = response.get("assistant_event_id")
            if not isinstance(assistant_event_id, str) or not assistant_event_id:
                raise ValueError(
                    f"Feedback uptake validation: invalid assistant response ID for {expected_trajectory_id}"
                )
            if assistant_event_id in response_by_event_id:
                raise ValueError(
                    f"Feedback uptake validation: duplicate assistant response ID for {expected_trajectory_id}"
                )
            response_by_event_id[assistant_event_id] = response
            if response.get("session_path") not in session_paths:
                raise ValueError(
                    f"Feedback uptake validation: unknown assistant response source for {expected_trajectory_id}/{assistant_event_id}"
                )
            diagnostics = response.get("diagnostics")
            if not isinstance(diagnostics, list):
                raise TypeError(
                    f"Feedback uptake validation: invalid assistant diagnostics for {expected_trajectory_id}/{assistant_event_id}"
                )
            expected_signals = detect_assistant_response_candidate_signals(
                stop_reason=response.get("stop_reason"),
                error_message=response.get("error_message"),
                diagnostics=diagnostics,
            )
            if response.get("candidate_signals") != expected_signals or response.get(
                "candidate_signal_types"
            ) != candidate_signal_types(expected_signals):
                raise ValueError(
                    f"Feedback uptake validation: assistant candidate signals mismatch for {expected_trajectory_id}/{assistant_event_id}"
                )
            if expected_signals:
                assistant_error_count += 1
            response_call_ids = response.get("tool_call_ids")
            if not isinstance(response_call_ids, list) or any(
                call_id not in event_by_call_id for call_id in response_call_ids
            ):
                raise ValueError(
                    f"Feedback uptake validation: invalid assistant tool-call links for {expected_trajectory_id}/{assistant_event_id}"
                )
            for call_id in response_call_ids:
                if (
                    event_by_call_id[call_id].get("action_event_id")
                    != assistant_event_id
                ):
                    raise ValueError(
                        f"Feedback uptake validation: assistant/tool-call source mismatch for {expected_trajectory_id}/{assistant_event_id}"
                    )
        if packet.get("assistant_error_count") != assistant_error_count:
            raise ValueError(
                f"Feedback uptake validation: assistant-error count mismatch for {expected_trajectory_id}"
            )

        missing_result_count = 0
        observation_event_ids: list[str] = []
        for event in events:
            call_id = event["tool_call_id"]
            if event.get("parallel_group_id") != event.get("action_event_id"):
                raise ValueError(
                    "Feedback uptake validation: parallel group/action ID mismatch for "
                    f"{expected_trajectory_id}/{call_id}"
                )
            response = response_by_event_id.get(event.get("action_event_id"))
            if (
                response is None
                or event.get("assistant_response_ordinal")
                != response.get("assistant_response_ordinal")
                or call_id not in response.get("tool_call_ids", [])
            ):
                raise ValueError(
                    f"Feedback uptake validation: invalid assistant response link for {expected_trajectory_id}/{call_id}"
                )
            if event.get("action_session_path") not in session_paths:
                raise ValueError(
                    f"Feedback uptake validation: unknown action source for {expected_trajectory_id}/{call_id}"
                )
            if event.get("tool_kind") != classify_feedback_tool_kind(
                event.get("tool_name"), event.get("tool_arguments")
            ):
                raise ValueError(
                    f"Feedback uptake validation: tool kind mismatch for {expected_trajectory_id}/{call_id}"
                )
            command = event.get("command")
            expected_validation = bool(
                event.get("tool_name") == "bash"
                and isinstance(command, str)
                and is_validation_command(command)
            )
            if event.get("is_validation_command") is not expected_validation:
                raise ValueError(
                    f"Feedback uptake validation: validation-command mismatch for {expected_trajectory_id}/{call_id}"
                )

            observation_event_id = event.get("observation_event_id")
            if observation_event_id is None:
                missing_result_count += 1
                if event.get("observation_tool_call_id") is not None:
                    raise ValueError(
                        "Feedback uptake validation: missing observation has a result link for "
                        f"{expected_trajectory_id}/{call_id}"
                    )
                if event.get("result_kind") != "missing_result":
                    raise ValueError(
                        f"Feedback uptake validation: invalid missing-result kind for {expected_trajectory_id}/{call_id}"
                    )
            else:
                if (
                    not isinstance(observation_event_id, str)
                    or not observation_event_id
                ):
                    raise ValueError(
                        f"Feedback uptake validation: invalid observation ID for {expected_trajectory_id}/{call_id}"
                    )
                observation_event_ids.append(observation_event_id)
                if event.get("observation_tool_call_id") != call_id:
                    raise ValueError(
                        "Feedback uptake validation: call/result link mismatch for "
                        f"{expected_trajectory_id}/{call_id}"
                    )
                if event.get("observation_tool_name") != event.get("tool_name"):
                    raise ValueError(
                        "Feedback uptake validation: tool/result name mismatch for "
                        f"{expected_trajectory_id}/{call_id}"
                    )
                if event.get("observation_session_path") not in session_paths:
                    raise ValueError(
                        f"Feedback uptake validation: unknown observation source for {expected_trajectory_id}/{call_id}"
                    )
                action_order = event.get("action_record_order")
                observation_order = event.get("observation_record_order")
                if (
                    not isinstance(action_order, int)
                    or not isinstance(observation_order, int)
                    or observation_order <= action_order
                ):
                    raise ValueError(
                        f"Feedback uptake validation: invalid call/result order for {expected_trajectory_id}/{call_id}"
                    )
                observation_text = event.get("observation_text")
                if not isinstance(observation_text, str):
                    raise ValueError(
                        f"Feedback uptake validation: invalid observation text for {expected_trajectory_id}/{call_id}"
                    )
            explicit_exit_code = event.get("raw_exit_code")
            expected_raw_facts = {
                "has_result": observation_event_id is not None,
                "reported_is_error": event.get("observation_is_error"),
                "explicit_exit_code": explicit_exit_code,
            }
            if event.get("raw_result_facts") != expected_raw_facts:
                raise ValueError(
                    f"Feedback uptake validation: raw result facts mismatch for {expected_trajectory_id}/{call_id}"
                )
            expected_raw_signature = classify_raw_result_signature(
                has_result=expected_raw_facts["has_result"],
                reported_is_error=expected_raw_facts["reported_is_error"],
                explicit_exit_code=expected_raw_facts["explicit_exit_code"],
            )
            if event.get("raw_result_signature") != expected_raw_signature:
                raise ValueError(
                    f"Feedback uptake validation: raw result signature mismatch for {expected_trajectory_id}/{call_id}"
                )
            expected_candidate_signals = detect_tool_result_candidate_signals(
                tool_name=event.get("tool_name"),
                result_text=event.get("observation_text") or "",
                reported_is_error=event.get("observation_is_error"),
                has_result=observation_event_id is not None,
                explicit_exit_code=explicit_exit_code,
            )
            if event.get(
                "candidate_signals"
            ) != expected_candidate_signals or event.get(
                "candidate_signal_types"
            ) != candidate_signal_types(expected_candidate_signals):
                raise ValueError(
                    f"Feedback uptake validation: tool-result candidate signals mismatch for {expected_trajectory_id}/{call_id}"
                )

            source_snippets = event.get("source_snippets")
            if not isinstance(source_snippets, list) or len(source_snippets) > 3:
                raise ValueError(
                    f"Feedback uptake validation: invalid source snippets for {expected_trajectory_id}/{call_id}"
                )
            for snippet in source_snippets:
                if not isinstance(snippet, dict):
                    raise TypeError(
                        f"Feedback uptake validation: invalid source snippet for {expected_trajectory_id}/{call_id}"
                    )
                snippet_text = snippet.get("text")
                start_char = snippet.get("start_char")
                end_char = snippet.get("end_char")
                source_kind = snippet.get("source_kind")
                source_text: str | None = None
                expected_source_path: Any = None
                expected_jsonl_line: Any = None
                if source_kind == "observation_text":
                    source_text = event.get("observation_text")
                    expected_source_path = event.get("observation_session_path")
                    expected_jsonl_line = event.get("observation_jsonl_line")
                elif source_kind == "tool_arguments":
                    argument_path = snippet.get("argument_path")
                    if isinstance(argument_path, list):
                        source_text = resolve_feedback_argument_string(
                            event.get("tool_arguments"), argument_path
                        )
                    expected_source_path = event.get("action_session_path")
                    expected_jsonl_line = event.get("action_jsonl_line")
                if (
                    not isinstance(snippet_text, str)
                    or not (
                        MIN_SOURCE_SNIPPET_CHARS
                        <= len(snippet_text)
                        <= MAX_SOURCE_SNIPPET_CHARS
                    )
                    or not isinstance(start_char, int)
                    or isinstance(start_char, bool)
                    or not isinstance(end_char, int)
                    or isinstance(end_char, bool)
                    or not isinstance(source_text, str)
                    or start_char < 0
                    or end_char <= start_char
                    or source_text[start_char:end_char] != snippet_text
                    or snippet.get("session_path") != expected_source_path
                    or snippet.get("jsonl_line") != expected_jsonl_line
                ):
                    raise ValueError(
                        f"Feedback uptake validation: invalid source snippet for {expected_trajectory_id}/{call_id}"
                    )

            next_action = event.get("next_action")
            if next_action is None:
                continue
            if not isinstance(next_action, dict) or next_action.get(
                "assistant_turn", 0
            ) <= event.get("assistant_turn", 0):
                raise ValueError(
                    f"Feedback uptake validation: invalid next action for {expected_trajectory_id}/{call_id}"
                )
            for linked_call in next_action.get("tool_calls", []):
                linked_call_id = linked_call.get("tool_call_id")
                linked_event = event_by_call_id.get(linked_call_id)
                if not isinstance(linked_event, dict):
                    raise TypeError(
                        f"Feedback uptake validation: invalid next-action link for {expected_trajectory_id}/{call_id}"
                    )
                linked_ordinal = linked_event.get("action_event_ordinal")
                if linked_ordinal != linked_call.get(
                    "action_event_ordinal"
                ) or linked_ordinal <= event.get("action_event_ordinal"):
                    raise ValueError(
                        f"Feedback uptake validation: invalid next-action link for {expected_trajectory_id}/{call_id}"
                    )

        if len(observation_event_ids) != len(set(observation_event_ids)):
            raise ValueError(
                f"Feedback uptake validation: duplicate observation ID for {expected_trajectory_id}"
            )
        if packet.get("missing_result_count") != missing_result_count:
            raise ValueError(
                f"Feedback uptake validation: missing-result count mismatch for {expected_trajectory_id}"
            )
        validate_feedback_packet_against_sources(packet)

    if len(addresses) != len(set(addresses)):
        raise ValueError("Feedback uptake validation: duplicate trajectory addresses")
    if set(addresses) != expected_addresses:
        missing = sorted(expected_addresses - set(addresses))
        unexpected = sorted(set(addresses) - expected_addresses)
        raise ValueError(
            "Feedback uptake validation: population address mismatch; "
            f"missing={missing}, unexpected={unexpected}"
        )
    if len(trajectory_ids) != len(set(trajectory_ids)):
        raise ValueError("Feedback uptake validation: duplicate trajectory IDs")
    if len(result_paths) != len(set(result_paths)):
        raise ValueError("Feedback uptake validation: duplicate result paths")
