"""Parse a benchmark cell's native Pi session into paginated trajectory turns."""

from __future__ import annotations

import json
import math
import time
from datetime import datetime
from pathlib import Path
from typing import Any

_TRAJECTORY_CACHE: dict[str, tuple[int, int, dict[str, Any]]] = {}
_TRAJECTORY_CACHE_LIMIT = 16

_CELL_RESULT_FIELDS = (
    "task",
    "config",
    "rep",
    "model",
    "thinking_level",
    "language",
    "category",
    "reward_binary",
    "reward_partial",
    "f2p",
    "f2p_passed",
    "f2p_total",
    "p2p",
    "p2p_passed",
    "p2p_total",
    "total_tokens",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cost_usd",
    "turns",
    "tool_calls",
    "agent_wall_s",
    "agent_exit",
    "agent_timed_out",
    "verifier_exit",
    "patch_bytes",
)


def build_cell_trajectory_page(
    result_path: Path,
    session_path: Path,
    *,
    offset: int | None = 0,
    limit: int = 20,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Return one turn page; a None offset selects the final page boundary."""
    parsed = _parse_session_trajectory(session_path)
    result = _load_json_object(result_path)
    cell = {field: result[field] for field in _CELL_RESULT_FIELDS if field in result}
    cell.update({"result_path": str(result_path), "cell_path": str(result_path.parent)})

    turns = parsed["turns"]
    bounded_limit = max(1, limit)
    total_turns = len(turns)
    if offset is None:
        bounded_offset = (
            ((total_turns - 1) // bounded_limit) * bounded_limit if total_turns else 0
        )
    else:
        bounded_offset = max(0, offset)
    page = turns[bounded_offset : bounded_offset + bounded_limit]
    stat = session_path.stat()
    session = {
        **parsed["session"],
        "path": str(session_path),
        "updated_at": stat.st_mtime,
        "is_live": ((now_ts if now_ts is not None else time.time()) - stat.st_mtime)
        < 180,
    }
    return {
        "found": True,
        "cell": cell,
        "session": session,
        "prompt": parsed["prompt"],
        "artifacts": _list_cell_artifacts(result_path.parent),
        "test_summary": _load_cell_test_summary(result_path.parent),
        "total_turns": total_turns,
        "offset": bounded_offset,
        "limit": bounded_limit,
        "has_previous": bounded_offset > 0,
        "has_next": bounded_offset + len(page) < total_turns,
        "turns": page,
        "metrics": parsed["metrics"],
    }


def _list_cell_artifacts(cell_path: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path in sorted(cell_path.rglob("*")):
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        relative_path = path.relative_to(cell_path).as_posix()
        artifacts.append(
            {
                "path": str(path),
                "relative_path": relative_path,
                "kind": _cell_artifact_kind(relative_path),
                "size": size,
            }
        )
    return artifacts


def _cell_artifact_kind(relative_path: str) -> str:
    if relative_path.endswith(".patch"):
        return "patch"
    if relative_path.startswith("session/"):
        return "session"
    if relative_path.startswith("verifier/") or "ctrf" in relative_path:
        return "tests"
    if relative_path.startswith("logs/") or relative_path.endswith(".log"):
        return "log"
    if relative_path == "result.json":
        return "result"
    return "other"


def _load_cell_test_summary(cell_path: Path) -> dict[str, int] | None:
    result_record = _load_json_object(cell_path / "result.json")
    verifier_summary = result_record.get("verifier_summary")
    compact_summary = (
        verifier_summary.get("tests") if isinstance(verifier_summary, dict) else None
    )
    keys = ("tests", "passed", "failed", "skipped", "pending", "other")
    if isinstance(compact_summary, dict):
        return {key: int(_number(compact_summary.get(key))) for key in keys}
    candidates = (
        cell_path / "verifier" / "ctrf.json",
        cell_path / "verifier" / "reports" / "new-ctrf.json",
    )
    for path in candidates:
        report = _load_json_object(path)
        results = report.get("results")
        summary = results.get("summary") if isinstance(results, dict) else None
        if not isinstance(summary, dict):
            continue
        return {key: int(_number(summary.get(key))) for key in keys}
    return None


def _parse_session_trajectory(path: Path) -> dict[str, Any]:
    stat = path.stat()
    cache_key = str(path)
    cached = _TRAJECTORY_CACHE.get(cache_key)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]

    session: dict[str, Any] = {}
    prompt_parts: list[str] = []
    turns: list[dict[str, Any]] = []
    pending_calls: dict[str, tuple[dict[str, Any], dict[str, Any], float | None]] = {}
    cumulative_cost = 0.0
    session_started_ms: float | None = None

    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue

            record_type = record.get("type")
            if record_type == "session":
                session.update(
                    {
                        "id": record.get("id"),
                        "cwd": record.get("cwd"),
                        "started_at": record.get("timestamp"),
                    }
                )
                session_started_ms = _timestamp_ms(record.get("timestamp"))
                continue
            if record_type == "model_change":
                session["provider"] = record.get("provider")
                session["model"] = record.get("modelId")
                continue
            if record_type == "thinking_level_change":
                session["thinking_level"] = record.get("thinkingLevel")
                continue
            if record_type != "message":
                continue

            message = record.get("message")
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            if role == "user":
                text = _content_text(message.get("content"))
                if text:
                    prompt_parts.append(text)
                continue
            if role == "assistant":
                usage = (
                    message.get("usage")
                    if isinstance(message.get("usage"), dict)
                    else {}
                )
                cost = _usage_cost(usage)
                cumulative_cost += cost
                timestamp = record.get("timestamp") or message.get("timestamp")
                started_ms = _timestamp_ms(message.get("timestamp")) or _timestamp_ms(
                    timestamp
                )
                turn: dict[str, Any] = {
                    "idx": len(turns) + 1,
                    "id": record.get("id"),
                    "timestamp": timestamp,
                    "elapsed_s": _elapsed_seconds(session_started_ms, started_ms),
                    "stop_reason": message.get("stopReason"),
                    "error": message.get("errorMessage"),
                    "usage": {
                        "input_tokens": int(_number(usage.get("input"))),
                        "output_tokens": int(_number(usage.get("output"))),
                        "cache_read_tokens": int(_number(usage.get("cacheRead"))),
                        "cache_write_tokens": int(_number(usage.get("cacheWrite"))),
                        "reasoning_tokens": int(_number(usage.get("reasoning"))),
                        "total_tokens": int(_number(usage.get("totalTokens"))),
                        "cost": round(cost, 8),
                    },
                    "cumulative_cost": round(cumulative_cost, 8),
                    "observation_chars": 0,
                    "command_time_ms": 0,
                    "blocks": [],
                }
                content = message.get("content")
                for block in content if isinstance(content, list) else []:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type")
                    if block_type == "thinking":
                        turn["blocks"].append(
                            {
                                "type": "thinking",
                                "text": str(block.get("thinking") or ""),
                            }
                        )
                    elif block_type == "text":
                        turn["blocks"].append(
                            {"type": "text", "text": str(block.get("text") or "")}
                        )
                    elif block_type in ("toolCall", "tool_use", "function_call"):
                        call_id = str(block.get("id") or block.get("call_id") or "")
                        call = {
                            "type": "tool_call",
                            "id": call_id,
                            "name": str(block.get("name") or "unknown"),
                            "arguments": block.get("arguments")
                            or block.get("input")
                            or {},
                            "result": None,
                        }
                        turn["blocks"].append(call)
                        if call_id:
                            pending_calls[call_id] = (turn, call, started_ms)
                    else:
                        turn["blocks"].append({"type": "unknown", "data": block})
                turns.append(turn)
                continue
            if role != "toolResult":
                continue

            call_id = str(
                message.get("toolCallId") or message.get("tool_call_id") or ""
            )
            result_timestamp = record.get("timestamp") or message.get("timestamp")
            result_ms = _timestamp_ms(message.get("timestamp")) or _timestamp_ms(
                result_timestamp
            )
            text = _content_text(message.get("content"))
            tool_result = {
                "timestamp": result_timestamp,
                "text": text,
                "is_error": bool(message.get("isError")),
                "details": message.get("details"),
            }
            pending = pending_calls.pop(call_id, None)
            if pending is None:
                if turns:
                    turns[-1]["blocks"].append(
                        {
                            "type": "tool_result",
                            "id": call_id,
                            "name": str(message.get("toolName") or "unknown"),
                            **tool_result,
                        }
                    )
                    turns[-1]["observation_chars"] += len(text)
                continue
            turn, call, call_started_ms = pending
            duration_ms = _duration_ms(call_started_ms, result_ms)
            call["result"] = {**tool_result, "duration_ms": duration_ms}
            turn["observation_chars"] += len(text)
            turn["command_time_ms"] = max(turn["command_time_ms"], duration_ms)

    metrics = [_trajectory_metric(turn) for turn in turns]
    parsed = {
        "session": session,
        "prompt": "\n\n".join(prompt_parts),
        "turns": turns,
        "metrics": metrics,
    }
    if len(_TRAJECTORY_CACHE) >= _TRAJECTORY_CACHE_LIMIT:
        _TRAJECTORY_CACHE.pop(next(iter(_TRAJECTORY_CACHE)))
    _TRAJECTORY_CACHE[cache_key] = (stat.st_mtime_ns, stat.st_size, parsed)
    return parsed


def _trajectory_metric(turn: dict[str, Any]) -> dict[str, Any]:
    usage = turn["usage"]
    context_tokens = usage["input_tokens"] + usage["cache_read_tokens"]
    return {
        "idx": turn["idx"],
        "timestamp": turn["timestamp"],
        "intent": _turn_intent(turn["blocks"]),
        "cumulative_cost": turn["cumulative_cost"],
        "context_tokens": context_tokens,
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["total_tokens"],
        "observation_chars": turn["observation_chars"],
        "command_time_ms": turn["command_time_ms"],
    }


def _turn_intent(blocks: list[dict[str, Any]]) -> str | None:
    for block in blocks:
        if block.get("type") not in ("thinking", "text"):
            continue
        for line in str(block.get("text") or "").splitlines():
            stripped = line.strip().lstrip("#").replace("**", "").strip()
            if stripped:
                return stripped[:160]
    return None


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


def _usage_cost(usage: dict[str, Any]) -> float:
    cost = usage.get("cost")
    if isinstance(cost, dict):
        return _number(cost.get("total"))
    return _number(cost)


def _number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


def _timestamp_ms(value: Any) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        number = float(value)
        return number if number > 10_000_000_000 else number * 1_000
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp() * 1_000
    except ValueError:
        return None


def _elapsed_seconds(start_ms: float | None, end_ms: float | None) -> float | None:
    if start_ms is None or end_ms is None or end_ms < start_ms:
        return None
    return round((end_ms - start_ms) / 1_000, 3)


def _duration_ms(start_ms: float | None, end_ms: float | None) -> int:
    if start_ms is None or end_ms is None or end_ms < start_ms:
        return 0
    return round(end_ms - start_ms)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}
