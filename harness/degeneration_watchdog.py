"""Bound pathological coding-agent trajectories without storing RPC content."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_CODING_AGENT_EARLY_GATE_PROFILE = "coding-agent-early-gate-v1"
_CODING_AGENT_RESPONSE_GATE_PROFILE = "coding-agent-response-gate-v1"
_POLICY_FIELDS = frozenset(
    {
        "profile",
        "max_assistant_chars_per_turn",
        "max_assistant_output_tokens_per_turn",
        "max_tool_calls_per_turn",
        "max_identical_tool_calls_per_turn",
        "max_tool_calls_without_progress",
        "progress_tool_names",
    }
)


@dataclass(frozen=True, slots=True)
class DegenerationWatchdogPolicy:
    """Plan-identity thresholds for one opt-in RPC trajectory watchdog."""

    profile: str
    max_assistant_chars_per_turn: int
    max_assistant_output_tokens_per_turn: int
    max_tool_calls_per_turn: int
    max_identical_tool_calls_per_turn: int
    max_tool_calls_without_progress: int | None
    progress_tool_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DegenerationViolation:
    """Compact evidence explaining why the watchdog stopped a subject."""

    reason: str
    observed: int
    limit: int
    turn_index: int
    tool_name: str | None = None
    tool_signature_sha256: str | None = None

    def to_dict(self) -> dict[str, int | str | None]:
        """Return JSON-safe evidence without prompt text or tool arguments."""
        return {
            "limit": self.limit,
            "observed": self.observed,
            "reason": self.reason,
            "tool_name": self.tool_name,
            "tool_signature_sha256": self.tool_signature_sha256,
            "turn_index": self.turn_index,
        }


def coding_agent_early_gate_watchdog() -> DegenerationWatchdogPolicy:
    """Return the evidence-calibrated policy for early coding-agent gates."""
    return DegenerationWatchdogPolicy(
        profile=_CODING_AGENT_EARLY_GATE_PROFILE,
        max_assistant_chars_per_turn=180_000,
        max_assistant_output_tokens_per_turn=50_000,
        max_tool_calls_per_turn=24,
        max_identical_tool_calls_per_turn=4,
        max_tool_calls_without_progress=48,
        progress_tool_names=("edit", "write"),
    )


def coding_agent_response_gate_watchdog() -> DegenerationWatchdogPolicy:
    """Bound pathological single responses without guessing cross-turn progress."""
    return DegenerationWatchdogPolicy(
        profile=_CODING_AGENT_RESPONSE_GATE_PROFILE,
        max_assistant_chars_per_turn=180_000,
        max_assistant_output_tokens_per_turn=50_000,
        max_tool_calls_per_turn=24,
        max_identical_tool_calls_per_turn=4,
        max_tool_calls_without_progress=None,
        progress_tool_names=(),
    )


def degeneration_watchdog_policy_for_profile(
    profile: str | None,
) -> DegenerationWatchdogPolicy | None:
    """Resolve a named CLI profile without accepting hidden custom thresholds."""
    if profile is None:
        return None
    if profile == _CODING_AGENT_EARLY_GATE_PROFILE:
        return coding_agent_early_gate_watchdog()
    if profile == _CODING_AGENT_RESPONSE_GATE_PROFILE:
        return coding_agent_response_gate_watchdog()
    raise ValueError(f"Unknown degeneration watchdog profile: {profile!r}")


def validate_degeneration_watchdog_policy(
    policy: DegenerationWatchdogPolicy,
) -> None:
    """Reject malformed or drifted watchdog policies before plan compilation."""
    if policy.profile not in {
        _CODING_AGENT_EARLY_GATE_PROFILE,
        _CODING_AGENT_RESPONSE_GATE_PROFILE,
    }:
        raise ValueError(
            "Degeneration watchdog policy invalid: unsupported profile "
            f"{policy.profile!r}"
        )
    limits = {
        "max assistant chars per turn": policy.max_assistant_chars_per_turn,
        "max assistant output tokens per turn": (
            policy.max_assistant_output_tokens_per_turn
        ),
        "max tool calls per turn": policy.max_tool_calls_per_turn,
        "max identical tool calls per turn": (policy.max_identical_tool_calls_per_turn),
    }
    for name, value in limits.items():
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(
                "Degeneration watchdog policy invalid: expected a positive "
                f"integer for {name}; got {value!r}"
            )
    no_progress_limit = policy.max_tool_calls_without_progress
    names = policy.progress_tool_names
    if no_progress_limit is None:
        if names:
            raise ValueError(
                "Degeneration watchdog policy invalid: progress tool names require "
                "a no-progress limit"
            )
    else:
        if (
            isinstance(no_progress_limit, bool)
            or not isinstance(no_progress_limit, int)
            or no_progress_limit <= 0
        ):
            raise ValueError(
                "Degeneration watchdog policy invalid: expected a positive integer "
                "or null for max tool calls without progress"
            )
        if (
            not names
            or len(set(names)) != len(names)
            or any(not isinstance(name, str) or not name for name in names)
        ):
            raise ValueError(
                "Degeneration watchdog policy invalid: progress tool names must be "
                "unique nonempty strings"
            )


def validate_named_degeneration_watchdog_policy(
    policy: DegenerationWatchdogPolicy,
) -> None:
    """Require a named launch profile to retain its reviewed thresholds."""
    validate_degeneration_watchdog_policy(policy)
    expected = degeneration_watchdog_policy_for_profile(policy.profile)
    if expected is None or policy != expected:
        raise ValueError(
            f"Degeneration watchdog policy invalid: {policy.profile} thresholds drifted"
        )


def validate_coding_agent_early_gate_watchdog(
    policy: DegenerationWatchdogPolicy,
) -> None:
    """Preserve validation for historical early-gate launch plans."""
    if policy.profile != _CODING_AGENT_EARLY_GATE_PROFILE:
        raise ValueError(
            "Degeneration watchdog policy invalid: expected "
            f"{_CODING_AGENT_EARLY_GATE_PROFILE!r}; got {policy.profile!r}"
        )
    validate_named_degeneration_watchdog_policy(policy)


def degeneration_watchdog_policy_from_mapping(
    value: Mapping[str, object] | None,
) -> DegenerationWatchdogPolicy | None:
    """Decode the exact policy embedded in a confirmed launch request."""
    if value is None:
        return None
    if set(value) != _POLICY_FIELDS:
        raise ValueError(
            "Degeneration watchdog policy invalid: expected exact fields "
            f"{sorted(_POLICY_FIELDS)!r}"
        )
    profile = value.get("profile")
    progress_tool_names = value.get("progress_tool_names")
    if not isinstance(profile, str):
        raise TypeError(
            "Degeneration watchdog policy invalid: profile must be a string"
        )
    if not isinstance(progress_tool_names, list | tuple) or not all(
        isinstance(name, str) for name in progress_tool_names
    ):
        raise TypeError(
            "Degeneration watchdog policy invalid: progress_tool_names must be strings"
        )
    policy = DegenerationWatchdogPolicy(
        profile=profile,
        max_assistant_chars_per_turn=_integer_policy_value(
            value.get("max_assistant_chars_per_turn")
        ),
        max_assistant_output_tokens_per_turn=_integer_policy_value(
            value.get("max_assistant_output_tokens_per_turn")
        ),
        max_tool_calls_per_turn=_integer_policy_value(
            value.get("max_tool_calls_per_turn")
        ),
        max_identical_tool_calls_per_turn=_integer_policy_value(
            value.get("max_identical_tool_calls_per_turn")
        ),
        max_tool_calls_without_progress=_optional_integer_policy_value(
            value.get("max_tool_calls_without_progress")
        ),
        progress_tool_names=tuple(progress_tool_names),
    )
    validate_named_degeneration_watchdog_policy(policy)
    return policy


def _optional_integer_policy_value(value: object) -> int | None:
    if value is None:
        return None
    return _integer_policy_value(value)


def _integer_policy_value(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "Degeneration watchdog policy invalid: thresholds must be integers"
        )
    return value


class DegenerationWatchdog:
    """Classify one live Pi RPC event stream against a confirmed policy."""

    def __init__(self, policy: DegenerationWatchdogPolicy) -> None:
        validate_degeneration_watchdog_policy(policy)
        self.policy = policy
        self.turn_index = 0
        self.assistant_chars_this_turn = 0
        self.tool_calls_this_turn = 0
        self.tool_calls_without_progress = 0
        self.tool_signatures_this_turn: Counter[str] = Counter()
        self.violation: DegenerationViolation | None = None

    def observe(self, event: Mapping[str, Any]) -> DegenerationViolation | None:
        """Consume one decoded RPC event and return the first violation."""
        if self.violation is not None:
            return self.violation
        event_type = event.get("type")
        if event_type == "turn_start":
            self.turn_index += 1
            self.assistant_chars_this_turn = 0
            self.tool_calls_this_turn = 0
            self.tool_signatures_this_turn.clear()
            return None
        handler = {
            "message_update": self._observe_message_update,
            "message_end": self._observe_message_end,
            "tool_execution_start": self._observe_tool_start,
            "tool_execution_end": self._observe_tool_end,
        }.get(event_type)
        return handler(event) if handler is not None else None

    def _observe_message_update(
        self,
        event: Mapping[str, Any],
    ) -> DegenerationViolation | None:
        update = event.get("assistantMessageEvent")
        if not isinstance(update, Mapping) or update.get("type") not in {
            "text_delta",
            "thinking_delta",
        }:
            return None
        delta = update.get("delta")
        if not isinstance(delta, str):
            return None
        self.assistant_chars_this_turn += len(delta)
        if self.assistant_chars_this_turn > self.policy.max_assistant_chars_per_turn:
            return self._record_violation(
                "assistant_chars_per_turn",
                self.assistant_chars_this_turn,
                self.policy.max_assistant_chars_per_turn,
            )
        return None

    def _observe_message_end(
        self,
        event: Mapping[str, Any],
    ) -> DegenerationViolation | None:
        message = event.get("message")
        if not isinstance(message, Mapping) or message.get("role") != "assistant":
            return None
        usage = message.get("usage")
        output_tokens = usage.get("output") if isinstance(usage, Mapping) else None
        if (
            not isinstance(output_tokens, bool)
            and isinstance(output_tokens, int | float)
            and output_tokens > self.policy.max_assistant_output_tokens_per_turn
        ):
            return self._record_violation(
                "assistant_output_tokens_per_turn",
                int(output_tokens),
                self.policy.max_assistant_output_tokens_per_turn,
            )
        return None

    def _observe_tool_start(
        self,
        event: Mapping[str, Any],
    ) -> DegenerationViolation | None:
        tool_name = str(event.get("toolName") or "unknown")
        self.tool_calls_this_turn += 1
        if self.tool_calls_this_turn > self.policy.max_tool_calls_per_turn:
            return self._record_violation(
                "tool_calls_per_turn",
                self.tool_calls_this_turn,
                self.policy.max_tool_calls_per_turn,
                tool_name=tool_name,
            )

        signature = _tool_signature(tool_name, event.get("args"))
        self.tool_signatures_this_turn[signature] += 1
        identical_count = self.tool_signatures_this_turn[signature]
        if identical_count > self.policy.max_identical_tool_calls_per_turn:
            return self._record_violation(
                "identical_tool_calls_per_turn",
                identical_count,
                self.policy.max_identical_tool_calls_per_turn,
                tool_name=tool_name,
                tool_signature_sha256=signature,
            )

        no_progress_limit = self.policy.max_tool_calls_without_progress
        if (
            no_progress_limit is not None
            and tool_name not in self.policy.progress_tool_names
        ):
            self.tool_calls_without_progress += 1
            if self.tool_calls_without_progress > no_progress_limit:
                return self._record_violation(
                    "tool_calls_without_progress",
                    self.tool_calls_without_progress,
                    no_progress_limit,
                    tool_name=tool_name,
                )
        return None

    def _observe_tool_end(
        self,
        event: Mapping[str, Any],
    ) -> DegenerationViolation | None:
        tool_name = event.get("toolName")
        if (
            tool_name in self.policy.progress_tool_names
            and event.get("isError") is False
        ):
            self.tool_calls_without_progress = 0
        return None

    def _record_violation(
        self,
        reason: str,
        observed: int,
        limit: int,
        *,
        tool_name: str | None = None,
        tool_signature_sha256: str | None = None,
    ) -> DegenerationViolation:
        self.violation = DegenerationViolation(
            reason=reason,
            observed=observed,
            limit=limit,
            turn_index=max(1, self.turn_index),
            tool_name=tool_name,
            tool_signature_sha256=tool_signature_sha256,
        )
        return self.violation


def _tool_signature(tool_name: str, args: object) -> str:
    payload = json.dumps(
        {"args": args, "toolName": tool_name},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
