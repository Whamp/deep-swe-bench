"""Parse pi token/cost/turn usage from the native session and advisor stream.

pi writes its native session to ``session/*.jsonl`` (``--session-dir``). Each
assistant message record (``type:"message"``, ``message.role == "assistant"``)
carries its final ``message.usage`` exactly once, so summing every assistant
message's usage gives the executor totals with no streaming-dedup logic.

Advisor LLM calls go through the extension's own provider path, not pi's
session machinery, so their usage is absent from the native session. It is
captured at run time by filtering pi's ``--mode json`` stdout down to
``tool-usage.jsonl`` (only ``tool_execution_end`` events with
``toolName == "advisor"``). ``parse_advisor_stream`` reads that filtered file.

``parse(session_dir=..., advisor_path=...)`` combines both and returns the full
usage dict that ``run.py`` spreads into ``result_record`` via ``**usage``.

A missing/empty/unreadable source RAISES rather than returning zeros — the
silent-zero path is the corruption vector if the stream-capture removal and the
session-read switch ever land out of sync.
"""
from __future__ import annotations

import json
from pathlib import Path


def _new_acc() -> dict:
    return {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_tokens": 0, "cache_write_tokens": 0,
        "cost_usd": 0.0, "turns": 0, "tool_calls": 0,
        "completions": 0,
        "advisor_calls": 0, "advisor_input_tokens": 0,
        "advisor_output_tokens": 0, "advisor_cache_read_tokens": 0,
        "advisor_cache_write_tokens": 0, "advisor_reported_total_tokens": 0,
        "advisor_cost_usd": 0.0,
        "advisor_provider": None, "advisor_model": None,
    }


def _add_message_usage(acc: dict, u: dict) -> None:
    acc["input_tokens"] += int(u.get("input") or 0)
    acc["output_tokens"] += int(u.get("output") or 0)
    acc["cache_read_tokens"] += int(u.get("cacheRead") or 0)
    acc["cache_write_tokens"] += int(u.get("cacheWrite") or 0)
    c = u.get("cost") or {}
    acc["cost_usd"] += float(c.get("total") or 0.0)
    acc["completions"] += 1


def _iter_jsonl(raw: str):
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _finalize(acc: dict) -> None:
    acc["total_tokens"] = (acc["input_tokens"] + acc["output_tokens"]
                           + acc["cache_read_tokens"] + acc["cache_write_tokens"])
    component_advisor_total = (acc["advisor_input_tokens"] + acc["advisor_output_tokens"]
                               + acc["advisor_cache_read_tokens"]
                               + acc["advisor_cache_write_tokens"])
    acc["advisor_total_tokens"] = (acc["advisor_reported_total_tokens"]
                                   or component_advisor_total)
    acc["combined_total_tokens"] = acc["total_tokens"] + acc["advisor_total_tokens"]
    acc["cost_usd"] = round(acc["cost_usd"], 6)
    acc["advisor_cost_usd"] = round(acc["advisor_cost_usd"], 6)
    acc["combined_cost_usd"] = round(acc["cost_usd"] + acc["advisor_cost_usd"], 6)


def parse_session(*, path: Path | None = None, text: str | None = None,
                  session_dir: Path | None = None) -> dict:
    """Read executor usage from native session file(s).

    ``session_dir`` reads every ``*.jsonl`` segment in the dir (a resumed cell
    can split across several) and sums them. ``path`` reads one file; ``text``
    reads a passed string. One of the three is required.
    """
    if session_dir is not None:
        files = sorted(Path(session_dir).glob("*.jsonl"),
                       key=lambda p: (p.stat().st_mtime, p.name))
        if not files:
            raise FileNotFoundError(
                f"no session/*.jsonl under {session_dir} — cannot read usage")
        # run.py invokes pi once per cell with no --resume, so each pi run writes
        # ONE fresh segment (every segment begins with a `type:"session"` record).
        # A cell that failed (transient error / timeout) and was re-run by
        # run_batch leaves its FAILED attempts as earlier segments; pi.jsonl was
        # truncated (open "w") each run so it only ever held the last run. Usage
        # must therefore come from the NEWEST segment alone (the run that wrote
        # result.json) — summing all segments would recount failed-attempt tokens.
        raw = files[-1].read_text(encoding="utf-8", errors="ignore")
    elif path is not None:
        raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    elif text is not None:
        raw = text
    else:
        raise ValueError("parse_session requires path=, text=, or session_dir=")

    acc = _new_acc()
    for r in _iter_jsonl(raw):
        if r.get("type") != "message":
            continue
        msg = r.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        # One assistant message == one agent turn == one completion.
        acc["turns"] += 1
        for blk in msg.get("content") or []:
            if isinstance(blk, dict) and blk.get("type") == "toolCall":
                acc["tool_calls"] += 1
        u = msg.get("usage")
        if u:
            _add_message_usage(acc, u)
    _finalize(acc)
    return acc


def parse_advisor_stream(*, path: Path | None = None, text: str | None = None) -> dict:
    """Read advisor usage from a filtered ``tool-usage.jsonl``.

    The file contains only ``tool_execution_end`` events with
    ``toolName == "advisor"`` (produced by filtering pi's ``--mode json``
    stdout at run time). Returns an acc dict with only the advisor_* fields set.
    """
    if path is not None:
        raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    elif text is not None:
        raw = text
    else:
        raise ValueError("parse_advisor_stream requires path= or text=")

    acc = _new_acc()
    for ev in _iter_jsonl(raw):
        if ev.get("type") != "tool_execution_end" or ev.get("toolName") != "advisor":
            continue
        details = ((ev.get("result") or {}).get("details") or {})
        usage = details.get("usage") or {}
        acc["advisor_calls"] += 1
        acc["advisor_input_tokens"] += int(usage.get("inputTokens") or 0)
        acc["advisor_output_tokens"] += int(usage.get("outputTokens") or 0)
        cache_read = int(usage.get("cacheReadTokens") or 0)
        cache_write = int(usage.get("cacheWriteTokens") or 0)
        component_total = (int(usage.get("inputTokens") or 0)
                           + int(usage.get("outputTokens") or 0)
                           + cache_read + cache_write)
        acc["advisor_cache_read_tokens"] += cache_read
        acc["advisor_cache_write_tokens"] += cache_write
        acc["advisor_reported_total_tokens"] += int(
            usage.get("totalTokens") or component_total)
        acc["advisor_cost_usd"] += float((usage.get("cost") or {}).get("total") or 0.0)
        acc["advisor_provider"] = usage.get("provider") or acc["advisor_provider"]
        acc["advisor_model"] = usage.get("model") or acc["advisor_model"]
    _finalize(acc)
    return acc


def parse(*, session_dir: Path | None = None, session_path: Path | None = None,
          advisor_path: Path | None = None) -> dict:
    """Combined entry point: executor usage from native session + (optional)
    advisor usage from the filtered tool-usage.jsonl. This is what run.py calls.
    """
    exec_usage = parse_session(session_dir=session_dir, path=session_path)
    if advisor_path is None or not Path(advisor_path).exists():
        return exec_usage
    adv_usage = parse_advisor_stream(path=advisor_path)
    merged = exec_usage
    for k in ("advisor_calls", "advisor_input_tokens", "advisor_output_tokens",
              "advisor_cache_read_tokens", "advisor_cache_write_tokens",
              "advisor_reported_total_tokens", "advisor_cost_usd",
              "advisor_provider", "advisor_model", "advisor_total_tokens",
              "combined_total_tokens", "combined_cost_usd"):
        merged[k] = adv_usage[k]
    _finalize(merged)
    return merged


if __name__ == "__main__":
    import sys
    # parity/inspection helper: parse a native session dir (and optional advisor file)
    sd = Path(sys.argv[1])
    adv = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    s = parse(session_dir=sd, advisor_path=adv)
    s.pop("completions", None)
    print(json.dumps(s, indent=2))
