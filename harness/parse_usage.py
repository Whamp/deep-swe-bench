"""Parse pi's --mode json NDJSON stream into summed token/cost/turn stats.

pi emits one JSON object per line. Each assistant completion carries a `usage`
block on its final `message_end` / `turn_end` / `agent_end` event. We sum every
assistant completion's usage exactly once by keying on the message's last seen
usage. `totalTokens` already folds reasoning tokens into output for reasoning
models like deepseek-v4-flash; we also expose the components.

Usage:
  from parse_usage import parse_stream
  stats = parse_stream(Path("pi.jsonl"))   # or parse_stream(text=str)
"""
from __future__ import annotations

import json
from pathlib import Path


def _add(acc: dict, u: dict) -> None:
    acc["input_tokens"] += int(u.get("input") or 0)
    acc["output_tokens"] += int(u.get("output") or 0)
    acc["cache_read_tokens"] += int(u.get("cacheRead") or 0)
    acc["cache_write_tokens"] += int(u.get("cacheWrite") or 0)
    c = u.get("cost") or {}
    acc["cost_usd"] += float(c.get("total") or 0.0)
    acc["completions"] += 1


def parse_stream(*, path: Path | None = None, text: str | None = None) -> dict:
    raw = ""
    if path is not None:
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            raw = ""
    elif text is not None:
        raw = text

    acc = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0,
           "cache_write_tokens": 0, "cost_usd": 0.0, "completions": 0,
           "turns": 0, "tool_calls": 0,
           "advisor_calls": 0, "advisor_input_tokens": 0,
           "advisor_output_tokens": 0, "advisor_cache_read_tokens": 0,
           "advisor_cache_write_tokens": 0, "advisor_reported_total_tokens": 0,
           "advisor_cost_usd": 0.0,
           "advisor_provider": None, "advisor_model": None}

    # Each assistant message appears in several events with growing content; its
    # usage is final on the LAST event that mentions it (message_end/turn_end).
    # We sum the usage attached to each `turn_end` assistant message (one per
    # completed turn = one completion) and fall back to message_end.
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "tool_execution_end" and ev.get("toolName") == "advisor":
            details = ((ev.get("result") or {}).get("details") or {})
            usage = details.get("usage") or {}
            acc["advisor_calls"] += 1
            acc["advisor_input_tokens"] += int(usage.get("inputTokens") or 0)
            acc["advisor_output_tokens"] += int(usage.get("outputTokens") or 0)
            cache_read = int(usage.get("cacheReadTokens") or 0)
            cache_write = int(usage.get("cacheWriteTokens") or 0)
            component_total = int(usage.get("inputTokens") or 0) + int(usage.get("outputTokens") or 0) + cache_read + cache_write
            acc["advisor_cache_read_tokens"] += cache_read
            acc["advisor_cache_write_tokens"] += cache_write
            acc["advisor_reported_total_tokens"] += int(usage.get("totalTokens") or component_total)
            acc["advisor_cost_usd"] += float((usage.get("cost") or {}).get("total") or 0.0)
            acc["advisor_provider"] = usage.get("provider") or acc["advisor_provider"]
            acc["advisor_model"] = usage.get("model") or acc["advisor_model"]
        if t == "turn_start":
            acc["turns"] += 1
        msg = ev.get("message") or {}
        # Only final turn_end/message_end events count as real tool calls;
        # message_update/toolcall_delta events contain streaming partial args.
        if t in ("turn_end", "message_end") and msg.get("role") == "assistant":
            for blk in msg.get("content") or []:
                if isinstance(blk, dict) and blk.get("type") == "toolCall":
                    acc["tool_calls"] += 1
            u = msg.get("usage")
            if u:
                _add(acc, u)

    # turn_end and message_end both fire for the same message -> dedupe by only
    # counting turn_end when both exist. Recompute from turn_end alone if present.
    te_hits = sum(1 for line in raw.splitlines() if '"type":"turn_end"' in line)
    me_only = 0
    if te_hits:
        # turn_end present: trust turn_end counts (rebuild from those lines only)
        acc2 = {k: (0 if isinstance(v, int) else 0.0) for k, v in acc.items()}
        acc2["turns"] = acc["turns"]; acc2["tool_calls"] = 0
        acc2["advisor_calls"] = acc["advisor_calls"]
        acc2["advisor_input_tokens"] = acc["advisor_input_tokens"]
        acc2["advisor_output_tokens"] = acc["advisor_output_tokens"]
        acc2["advisor_cache_read_tokens"] = acc["advisor_cache_read_tokens"]
        acc2["advisor_cache_write_tokens"] = acc["advisor_cache_write_tokens"]
        acc2["advisor_reported_total_tokens"] = acc["advisor_reported_total_tokens"]
        acc2["advisor_cost_usd"] = acc["advisor_cost_usd"]
        acc2["advisor_provider"] = acc["advisor_provider"]
        acc2["advisor_model"] = acc["advisor_model"]
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "turn_end" and (ev.get("message") or {}).get("role") == "assistant":
                msg = ev["message"]
                for blk in msg.get("content") or []:
                    if isinstance(blk, dict) and blk.get("type") == "toolCall":
                        acc2["tool_calls"] += 1
                u = msg.get("usage")
                if u:
                    _add(acc2, u)
        acc = acc2

    acc["total_tokens"] = (acc["input_tokens"] + acc["output_tokens"]
                           + acc["cache_read_tokens"] + acc["cache_write_tokens"])
    component_advisor_total = (acc["advisor_input_tokens"] + acc["advisor_output_tokens"]
                               + acc["advisor_cache_read_tokens"] + acc["advisor_cache_write_tokens"])
    acc["advisor_total_tokens"] = acc["advisor_reported_total_tokens"] or component_advisor_total
    acc["combined_total_tokens"] = acc["total_tokens"] + acc["advisor_total_tokens"]
    acc["cost_usd"] = round(acc["cost_usd"], 6)
    acc["advisor_cost_usd"] = round(acc["advisor_cost_usd"], 6)
    acc["combined_cost_usd"] = round(acc["cost_usd"] + acc["advisor_cost_usd"], 6)
    return acc


if __name__ == "__main__":
    import sys
    p = Path(sys.argv[1])
    s = parse_stream(path=p)
    s.pop("completions", None)
    print(json.dumps(s, indent=2))
