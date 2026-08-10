"""Detect deterministic feedback candidates without assigning semantic labels."""

from __future__ import annotations

import re
from typing import Any

FAILURE_TEXT_DETECTORS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "go_test_failure",
        re.compile(r"(?:^--- FAIL: .+$|^FAIL(?:\t[^\n]+| +\S.*|$))", re.MULTILINE),
    ),
    (
        "pytest_failure",
        re.compile(
            r"(?:^FAILED\s+\S.*$|^ERROR\s+\S.*$|"
            r"^=+ [^\n]*(?:\d+\s+failed|\d+\s+errors?)[^\n]* =+$|"
            r"^\d+\s+(?:failed|errors?)(?:, [^\n]+)? in \d+(?:\.\d+)?s$)",
            re.MULTILINE,
        ),
    ),
    (
        "javascript_test_failure",
        re.compile(
            r"(?:^Test Suites:\s+[^\n]*\bfailed\b[^\n]*$|"
            r"^Tests:\s+[^\n]*\bfailed\b[^\n]*$)",
            re.MULTILINE | re.IGNORECASE,
        ),
    ),
    (
        "test_failure_glyph",
        re.compile(r"^\s*(?:✕|✖|×)\s+.+$", re.MULTILINE),
    ),
    (
        "rust_test_failure",
        re.compile(r"^test result: FAILED\.[^\n]*$", re.MULTILINE),
    ),
    (
        "go_compiler_diagnostic",
        re.compile(
            r"^[^\n:]+:\d+:\d+:\s+[^\n]*(?:"
            r"imported and not used|undefined:|cannot use|syntax error|"
            r"no required module provides package)[^\n]*$",
            re.MULTILINE,
        ),
    ),
    (
        "typescript_compiler_diagnostic",
        re.compile(
            r"^(?:[^\n]*\(\d+,\d+\):\s*)?error TS\d+:[^\n]*$",
            re.MULTILINE | re.IGNORECASE,
        ),
    ),
    (
        "fatal_command_diagnostic",
        re.compile(r"^fatal:\s+[^\n]+$", re.MULTILINE | re.IGNORECASE),
    ),
    (
        "python_traceback",
        re.compile(
            r"^(?:Traceback \(most recent call last\):|"
            r"(?:AssertionError|ModuleNotFoundError|ImportError):[^\n]*)$",
            re.MULTILINE,
        ),
    ),
    (
        "build_error_summary",
        re.compile(
            r"^(?:npm ERR!|error Command failed|make(?:\[\d+\])?: \*\*\*)[^\n]*$",
            re.MULTILINE | re.IGNORECASE,
        ),
    ),
)


def candidate_signal_types(signals: list[dict[str, Any]]) -> list[str]:
    """Return unique candidate signal types in first-observed order."""
    return list(dict.fromkeys(str(signal["signal_type"]) for signal in signals))


def text_candidate_signal(
    *, signal_type: str, detector_id: str, match: re.Match[str]
) -> dict[str, Any]:
    """Build one exact source span for a deterministic text candidate."""
    return {
        "signal_type": signal_type,
        "detector_id": detector_id,
        "source_kind": "observation_text",
        "start_char": match.start(),
        "end_char": match.end(),
        "matched_text": match.group(0),
    }


def metadata_candidate_signal(
    *, signal_type: str, detector_id: str, source_kind: str
) -> dict[str, Any]:
    """Build one deterministic metadata candidate without inventing source text."""
    return {
        "signal_type": signal_type,
        "detector_id": detector_id,
        "source_kind": source_kind,
        "start_char": None,
        "end_char": None,
        "matched_text": None,
    }


def detect_tool_result_candidate_signals(
    *,
    tool_name: str,
    result_text: str,
    reported_is_error: Any,
    has_result: bool,
    explicit_exit_code: int | None,
) -> list[dict[str, Any]]:
    """Flag tool-result records that merit semantic review, with no outcome claim."""
    signals: list[dict[str, Any]] = []
    lowered = result_text.lower()
    if not has_result:
        return [
            metadata_candidate_signal(
                signal_type="missing_observation",
                detector_id="tool_call_without_result",
                source_kind="tool_call_metadata",
            )
        ]

    if explicit_exit_code is not None and explicit_exit_code != 0:
        signals.append(
            metadata_candidate_signal(
                signal_type="explicit_nonzero_exit",
                detector_id="explicit_command_exit_code",
                source_kind="observation_metadata",
            )
        )
    if tool_name == "bash" and "command timed out after" in lowered:
        signals.append(
            metadata_candidate_signal(
                signal_type="command_timeout",
                detector_id="command_timeout_text",
                source_kind="observation_text",
            )
        )
    if reported_is_error is True:
        signals.append(
            metadata_candidate_signal(
                signal_type="reported_tool_error",
                detector_id="tool_result_is_error",
                source_kind="observation_metadata",
            )
        )
    if tool_name == "edit" and 'validation failed for tool "edit"' in lowered:
        signals.append(
            metadata_candidate_signal(
                signal_type="edit_argument_schema_error",
                detector_id="edit_tool_schema_validation",
                source_kind="observation_text",
            )
        )
    if tool_name == "edit" and any(
        signature in lowered
        for signature in (
            "could not find the exact text",
            "oldtext must",
            "old text must",
            "must be unique",
            "found 2 occurrences",
            "did not match",
            "merge them into one edit or target disjoint regions",
            "replacement produced identical content",
        )
    ):
        signals.append(
            metadata_candidate_signal(
                signal_type="edit_application_rejection",
                detector_id="edit_tool_application_rejection",
                source_kind="observation_text",
            )
        )
    if tool_name == "read" and reported_is_error is True:
        signals.append(
            metadata_candidate_signal(
                signal_type="read_error",
                detector_id="read_tool_is_error",
                source_kind="observation_metadata",
            )
        )

    if (
        tool_name == "bash"
        and reported_is_error is False
        and explicit_exit_code
        in {
            None,
            0,
        }
    ):
        for detector_id, pattern in FAILURE_TEXT_DETECTORS:
            match = pattern.search(result_text)
            if match is not None:
                signals.append(
                    text_candidate_signal(
                        signal_type="failure_text_with_zero_status",
                        detector_id=detector_id,
                        match=match,
                    )
                )
    return signals


def detect_assistant_response_candidate_signals(
    *, stop_reason: Any, error_message: Any, diagnostics: list[Any]
) -> list[dict[str, Any]]:
    """Flag assistant/provider response records that merit semantic review."""
    signals: list[dict[str, Any]] = []
    if stop_reason == "error" or error_message not in {None, ""}:
        signals.append(
            metadata_candidate_signal(
                signal_type="assistant_response_error",
                detector_id="assistant_error_metadata",
                source_kind="assistant_message_metadata",
            )
        )
    for diagnostic in diagnostics:
        if not isinstance(diagnostic, dict):
            continue
        diagnostic_type = diagnostic.get("type")
        if not isinstance(diagnostic_type, str) or not diagnostic_type:
            continue
        signals.append(
            metadata_candidate_signal(
                signal_type=diagnostic_type,
                detector_id="assistant_diagnostic_type",
                source_kind="assistant_message_diagnostics",
            )
        )
    return signals
