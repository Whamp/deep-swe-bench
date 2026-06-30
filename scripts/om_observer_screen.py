#!/usr/bin/env python3
"""Offline quality screen for pi-observational-memory observer workers.

The screen replays the observer task on saved session chunks:

1. extract-cases: reconstruct observer inputs from historical OM sessions.
2. run-candidates: call chat completions with the observer prompt and
   record_observations tool schema.
3. score: compute mechanical and silver-reference overlap metrics.
4. judge: optional LLM-as-judge rubric over chunk + silver + candidate output.
5. report: write a recommendation from scored outputs.

This script intentionally does not touch benchmark result records.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO / "analysis" / "om-observer-screen"
OBSERVER_PROMPT = REPO / "configs" / "observational-memory" / "extensions" / "pi-observational-memory" / "src" / "agents" / "observer" / "prompts.ts"
TWELVE_V0 = REPO / "subsets" / "12_v0.txt"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
LOCAL_VLLM_URL = os.environ.get("LOCAL_VLLM_URL", "http://100.92.238.117:30000/v1/chat/completions")
LOCAL_VLLM_PREFIX = "local-vllm/"

SOURCE_TYPES = {"message", "custom_message", "branch_summary"}
OM_OBS = "om.observations.recorded"
OM_REFL = "om.reflections.recorded"
TIMESTAMP_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$")
WORD_RE = re.compile(r"[A-Za-z0-9_./:+#-]+")

DEFAULT_CANDIDATES = [
    "deepseek-v4-flash-off=deepseek/deepseek-v4-flash:off",
    "deepseek-v4-flash-low=deepseek/deepseek-v4-flash:low",
    "gpt-5.4-mini-low=openai/gpt-5.4-mini:low",
    "gpt-5.5-low=openai/gpt-5.5:low",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def local_time(value: Any) -> str:
    if value is None:
        return "????-??-?? ??:??"
    try:
        if isinstance(value, (int, float)):
            ts = value / 1000 if value > 10_000_000_000 else value
        else:
            text = str(value).replace("Z", "+00:00")
            from datetime import datetime
            return datetime.fromisoformat(text).astimezone().strftime("%Y-%m-%d %H:%M")
        from datetime import datetime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "????-??-?? ??:??"


def text_from_content(content: Any, *, include_thinking: bool = False) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "[non-text content omitted]"
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            parts.append("[non-text content omitted]")
        elif block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif block.get("type") == "thinking":
            if include_thinking and isinstance(block.get("thinking"), str) and not block.get("redacted"):
                parts.append(f"[thinking: {block['thinking']}]")
            else:
                parts.append("[non-text content omitted]")
        elif block.get("type") == "toolCall" and isinstance(block.get("name"), str):
            parts.append(f"[{block['name']}({json.dumps(block.get('arguments') or {}, ensure_ascii=False)})]")
        else:
            parts.append("[non-text content omitted]")
    return "\n".join(parts)


def render_entry(entry: dict[str, Any]) -> str:
    typ = entry.get("type")
    if typ == "message" and isinstance(entry.get("message"), dict):
        msg = entry["message"]
        role = msg.get("role")
        ts = local_time(msg.get("timestamp", entry.get("timestamp")))
        if role == "user":
            return f"[User @ {ts}]: {text_from_content(msg.get('content'))}"
        if role == "assistant":
            body = "\n".join(x for x in text_from_content(msg.get("content"), include_thinking=True).splitlines() if x)
            return f"[Assistant @ {ts}]: {body}" if body else ""
        return f"[Tool result for {msg.get('toolName')} @ {ts}]: {text_from_content(msg.get('content'))}"
    if typ == "custom_message" or typ == "custom":
        ts = local_time(entry.get("timestamp"))
        tag = f"Custom ({entry.get('customType')})" if entry.get("customType") else "Custom"
        return f"[{tag} @ {ts}]: {text_from_content(entry.get('content'))}"
    if typ == "branch_summary" and isinstance(entry.get("summary"), str):
        return f"[Branch summary @ {local_time(entry.get('timestamp'))}]: {entry['summary']}"
    return ""


def is_source_entry(entry: dict[str, Any]) -> bool:
    return entry.get("type") in SOURCE_TYPES or entry.get("type") == "message"


def serialize_source_entries(entries: list[dict[str, Any]]) -> tuple[str, list[str]]:
    blocks, ids = [], []
    for entry in entries:
        eid = entry.get("id")
        if not eid or not is_source_entry(entry):
            continue
        rendered = render_entry(entry).strip()
        if not rendered:
            continue
        ids.append(eid)
        blocks.append(f"[Source entry id: {eid}]\n{rendered}")
    return "\n\n".join(blocks), ids


def custom_type(entry: dict[str, Any]) -> str | None:
    return entry.get("customType") or entry.get("custom_type")


def observation_line(obs: dict[str, Any]) -> str:
    return f"[{obs.get('id')}] {obs.get('timestamp')} [{obs.get('relevance')}] {obs.get('content')}"


def reflection_line(ref: dict[str, Any]) -> str:
    rid = ref.get("id", "unknown")
    content = ref.get("content") or ref.get("text") or json.dumps(ref, ensure_ascii=False)
    return f"[{rid}] {content}"


def load_observer_system() -> str:
    text = OBSERVER_PROMPT.read_text()
    m = re.search(r"export const OBSERVER_SYSTEM = `(?P<body>.*)`;", text, re.S)
    if not m:
        raise SystemExit(f"Could not parse observer prompt from {OBSERVER_PROMPT}")
    return m.group("body")


def build_user_text(case: dict[str, Any]) -> str:
    return f"""Current local time: {case['current_local_time']}

CURRENT REFLECTIONS:
{chr(10).join(case['prior_reflections']) if case['prior_reflections'] else '(none yet)'}

CURRENT OBSERVATIONS:
{chr(10).join(case['prior_observations']) if case['prior_observations'] else '(none yet)'}

Compress the following new conversation chunk into observations by calling record_observations one or more times. Do not restate facts already present in current reflections or current observations. Prefer inline conversation timestamps when assigning times; fall back to the current local time above only if no message timestamp applies. Stop calling the tool and reply with a short plain-text confirmation once the chunk is fully covered.

NEW CONVERSATION CHUNK:
{case['chunk']}"""


def extract_cases(args: argparse.Namespace) -> None:
    tasks = [x.strip() for x in TWELVE_V0.read_text().splitlines() if x.strip()]
    rows: list[dict[str, Any]] = []
    for task in tasks:
        found = None
        for root in args.roots:
            root_path = REPO / root
            for result in sorted(root_path.glob(f"{task}/rep*/result.json")):
                session_files = sorted((result.parent / "session").glob("*.jsonl"))
                if not session_files:
                    continue
                entries = read_jsonl(session_files[-1])
                by_id = {e.get("id"): i for i, e in enumerate(entries) if e.get("id")}
                observations_so_far: list[dict[str, Any]] = []
                reflections_so_far: list[dict[str, Any]] = []
                prior_coverage_id: str | None = None
                for idx, entry in enumerate(entries):
                    ctype = custom_type(entry)
                    data = entry.get("data") if isinstance(entry.get("data"), dict) else {}
                    if ctype == OM_OBS and isinstance(data.get("observations"), list):
                        covers = data.get("coversUpToId")
                        start = by_id.get(prior_coverage_id, -1) + 1 if prior_coverage_id else 0
                        stop = by_id.get(covers, idx - 1)
                        chunk_entries = entries[start:stop + 1]
                        chunk, source_ids = serialize_source_entries(chunk_entries)
                        if chunk and source_ids:
                            found = {
                                "case_id": f"{task}__{result.parent.name}__obs{len([r for r in rows if r.get('task') == task])}",
                                "task": task,
                                "source_result": str(result.relative_to(REPO)),
                                "session_file": str(session_files[-1].relative_to(REPO)),
                                "coverage_id": covers,
                                "current_local_time": local_time(entry.get("timestamp")),
                                "prior_reflections": [reflection_line(r) for r in reflections_so_far],
                                "prior_observations": [observation_line(o) for o in observations_so_far],
                                "chunk": chunk,
                                "allowed_source_entry_ids": source_ids,
                                "silver_observations": data["observations"],
                                "chunk_source_count": len(source_ids),
                                "silver_count": len(data["observations"]),
                                "chunk_chars": len(chunk),
                            }
                            break
                        observations_so_far.extend(data.get("observations") or [])
                        prior_coverage_id = covers
                    elif ctype == OM_REFL and isinstance(data.get("reflections"), list):
                        reflections_so_far.extend(data.get("reflections") or [])
                if found:
                    break
            if found:
                rows.append(found)
                break
    if len(rows) < args.target:
        print(f"[warn] extracted {len(rows)} cases, target was {args.target}", file=sys.stderr)
    rows = rows[:args.target]
    out = args.out / "cases.jsonl"
    write_jsonl(out, rows)
    print(f"wrote {len(rows)} cases to {out.relative_to(REPO)}")


@dataclass(frozen=True)
class Candidate:
    name: str
    model: str
    thinking: str


def parse_candidate(text: str) -> Candidate:
    if "=" in text:
        name, rest = text.split("=", 1)
    else:
        rest = text
        name = rest.replace("/", "_").replace(":", "_")
    if ":" in rest:
        model, thinking = rest.rsplit(":", 1)
    else:
        model, thinking = rest, "off"
    return Candidate(name=name, model=model, thinking=thinking)


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 180) -> dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:4000]
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}") from e


def openrouter_request(payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return post_json(
        OPENROUTER_URL,
        payload,
        {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Whamp/deep-swe-bench",
            "X-Title": "deep-swe-bench OM observer screen",
        },
        timeout=timeout,
    )


def local_vllm_request(payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    return post_json(
        LOCAL_VLLM_URL,
        payload,
        {"Authorization": "Bearer not-needed", "Content-Type": "application/json"},
        timeout=timeout,
    )


def chat_completion_request(candidate: Candidate, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    if candidate.model.startswith(LOCAL_VLLM_PREFIX):
        local_payload = dict(payload)
        local_payload["model"] = candidate.model[len(LOCAL_VLLM_PREFIX):]
        enable_thinking = candidate.thinking != "off"
        local_payload["chat_template_kwargs"] = {"enable_thinking": enable_thinking, "preserve_thinking": enable_thinking}
        local_payload.pop("reasoning", None)
        return local_vllm_request(local_payload, timeout=timeout)
    return openrouter_request(payload, timeout=timeout)


def record_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": "record_observations",
            "description": "Record a batch of new observations distilled from the conversation chunk. Call this multiple times as you work through the chunk. Stop calling when coverage is complete, then emit a short plain-text confirmation to end the run.",
            "parameters": {
                "type": "object",
                "properties": {
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "timestamp": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$"},
                                "content": {"type": "string", "minLength": 1},
                                "relevance": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                                "sourceEntryIds": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
                            },
                            "required": ["timestamp", "content", "relevance", "sourceEntryIds"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["observations"],
                "additionalProperties": False,
            },
        },
    }


def normalize_source_ids(source_ids: Any, allowed: list[str]) -> list[str] | None:
    if not isinstance(source_ids, list) or not source_ids:
        return None
    allowed_order = {sid: i for i, sid in enumerate(allowed)}
    seen = set()
    for sid in source_ids:
        if not isinstance(sid, str) or sid not in allowed_order:
            return None
        seen.add(sid)
    if not seen:
        return None
    return sorted(seen, key=lambda sid: allowed_order[sid])


def run_observer_case(case: dict[str, Any], candidate: Candidate, max_turns: int) -> dict[str, Any]:
    system_prompt = load_observer_system()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": build_user_text(case)},
    ]
    accumulated: dict[str, dict[str, Any]] = {}
    invalid_source_ids = 0
    malformed = 0
    duplicates = 0
    tool_calls_seen = 0
    usage = Counter()
    started = time.time()
    final_text = ""
    error = None
    for turn in range(max_turns):
        payload: dict[str, Any] = {
            "model": candidate.model,
            "messages": messages,
            "tools": [record_schema()],
            "tool_choice": "auto",
            "temperature": 0,
            "max_tokens": 32000,
        }
        if candidate.thinking != "off":
            payload["reasoning"] = {"effort": candidate.thinking}
        try:
            response = chat_completion_request(candidate, payload)
        except Exception as exc:
            error = str(exc)
            break
        for key, value in (response.get("usage") or {}).items():
            if isinstance(value, (int, float)):
                usage[key] += value
        choice = (response.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        tool_calls = msg.get("tool_calls") or []
        content = msg.get("content") or ""
        if content:
            final_text = content
        messages.append({k: v for k, v in msg.items() if k in {"role", "content", "tool_calls"}} or {"role": "assistant", "content": content})
        if not tool_calls:
            break
        for call in tool_calls:
            tool_calls_seen += 1
            args_text = ((call.get("function") or {}).get("arguments") or "{}")
            try:
                params = json.loads(args_text)
                obs_list = params.get("observations")
                if not isinstance(obs_list, list):
                    malformed += 1
                    obs_list = []
            except Exception:
                malformed += 1
                obs_list = []
            added = 0
            rejected = 0
            dup = 0
            for obs in obs_list:
                if not isinstance(obs, dict):
                    malformed += 1
                    continue
                source_ids = normalize_source_ids(obs.get("sourceEntryIds"), case["allowed_source_entry_ids"])
                if not source_ids:
                    invalid_source_ids += 1
                    rejected += 1
                    continue
                content = str(obs.get("content") or "").strip().replace("\n", " ")
                ts = str(obs.get("timestamp") or "")
                rel = str(obs.get("relevance") or "medium")
                if not content or not TIMESTAMP_PATTERN.match(ts) or rel not in {"low", "medium", "high", "critical"}:
                    malformed += 1
                    continue
                oid = str(abs(hash(content)))
                if oid in accumulated:
                    duplicates += 1
                    dup += 1
                    continue
                accumulated[oid] = {"content": content, "timestamp": ts, "relevance": rel, "sourceEntryIds": source_ids}
                added += 1
            ack = f"Recorded {added} new observations ({dup} duplicates skipped). {rejected} rejected for invalid source ids. Total so far this run: {len(accumulated)}. Continue if the chunk still has uncovered content; otherwise stop calling the tool and emit a short plain-text confirmation."
            messages.append({"role": "tool", "tool_call_id": call.get("id", f"call-{tool_calls_seen}"), "name": "record_observations", "content": ack})
    return {
        "case_id": case["case_id"],
        "task": case["task"],
        "candidate": candidate.name,
        "model": candidate.model,
        "thinking": candidate.thinking,
        "observations": list(accumulated.values()),
        "observation_count": len(accumulated),
        "tool_calls": tool_calls_seen,
        "invalid_source_ids": invalid_source_ids,
        "malformed": malformed,
        "duplicates": duplicates,
        "usage": dict(usage),
        "wall_s": round(time.time() - started, 2),
        "final_text": final_text[:1000],
        "error": error,
    }


def run_candidates(args: argparse.Namespace) -> None:
    cases = read_jsonl(args.out / "cases.jsonl")
    candidates = [parse_candidate(c) for c in (args.candidate or DEFAULT_CANDIDATES)]
    output = args.out / "candidate_outputs.jsonl"
    seen = set()
    if output.exists() and not args.force:
        for row in read_jsonl(output):
            seen.add((row.get("case_id"), row.get("candidate")))
    for cand in candidates:
        for case in cases:
            key = (case["case_id"], cand.name)
            if key in seen:
                print(f"[skip] {cand.name} {case['case_id']}", flush=True)
                continue
            print(f"[run] {cand.name} {case['case_id']}", flush=True)
            row = run_observer_case(case, cand, args.max_turns)
            append_jsonl(output, row)
            if row.get("error"):
                print(f"[error] {cand.name} {case['case_id']}: {row['error'][:300]}", file=sys.stderr, flush=True)
            time.sleep(args.sleep)
    print(f"wrote outputs to {output.relative_to(REPO)}")


def tokens(text: str) -> set[str]:
    return {t.lower() for t in WORD_RE.findall(text) if len(t) > 2}


def f1(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    if inter == 0:
        return 0.0
    p, r = inter / len(tb), inter / len(ta)
    return 2 * p * r / (p + r)


def load_pricing() -> dict[str, tuple[float, float]]:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return {}
    req = urllib.request.Request(OPENROUTER_MODELS_URL, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception:
        return {}
    pricing = {}
    for model in data.get("data", []):
        p = model.get("pricing") or {}
        try:
            pricing[model["id"]] = (float(p.get("prompt") or 0), float(p.get("completion") or 0))
        except Exception:
            pass
    return pricing


def score_outputs(args: argparse.Namespace) -> None:
    cases = {c["case_id"]: c for c in read_jsonl(args.out / "cases.jsonl")}
    outputs = read_jsonl(args.out / "candidate_outputs.jsonl")
    pricing = load_pricing()
    rows = []
    for out in outputs:
        case = cases[out["case_id"]]
        silver = [o.get("content", "") for o in case.get("silver_observations", [])]
        cand = [o.get("content", "") for o in out.get("observations", [])]
        silver_best = [max([f1(s, c) for c in cand] or [0]) for s in silver]
        cand_best = [max([f1(s, c) for s in silver] or [0]) for c in cand]
        usage = out.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        pp, cp = pricing.get(out.get("model"), (0, 0))
        est_cost = prompt_tokens * pp + completion_tokens * cp
        rows.append({
            "case_id": out["case_id"],
            "task": out["task"],
            "candidate": out["candidate"],
            "model": out["model"],
            "thinking": out["thinking"],
            "error": out.get("error") or "",
            "silver_count": len(silver),
            "observation_count": len(cand),
            "tool_calls": out.get("tool_calls", 0),
            "invalid_source_ids": out.get("invalid_source_ids", 0),
            "malformed": out.get("malformed", 0),
            "duplicates": out.get("duplicates", 0),
            "silver_recall_f1_mean": round(sum(silver_best) / len(silver_best), 4) if silver_best else 0,
            "silver_recall_ge_035": round(sum(x >= 0.35 for x in silver_best) / len(silver_best), 4) if silver_best else 0,
            "candidate_precision_f1_mean": round(sum(cand_best) / len(cand_best), 4) if cand_best else 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": round(est_cost, 6),
            "wall_s": out.get("wall_s", 0),
        })
    path = args.out / "mechanical_scores.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader(); writer.writerows(rows)
    print(f"wrote {len(rows)} score rows to {path.relative_to(REPO)}")


JUDGE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "observer_judgment",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "recall": {"type": "number", "minimum": 1, "maximum": 5},
                "faithfulness": {"type": "number", "minimum": 1, "maximum": 5},
                "specificity": {"type": "number", "minimum": 1, "maximum": 5},
                "salience": {"type": "number", "minimum": 1, "maximum": 5},
                "relevance_calibration": {"type": "number", "minimum": 1, "maximum": 5},
                "hallucination_count": {"type": "integer", "minimum": 0},
                "missing_important_count": {"type": "integer", "minimum": 0},
                "notes": {"type": "string"},
            },
            "required": ["recall", "faithfulness", "specificity", "salience", "relevance_calibration", "hallucination_count", "missing_important_count", "notes"],
            "additionalProperties": False,
        },
    },
}


def judge_prompt(case: dict[str, Any], out: dict[str, Any]) -> str:
    return f"""Evaluate an observational-memory observer output.

The observer's job is to compress the chunk into source-grounded memories useful to a future coding assistant. Score 1-5:
- recall: captures the important future-useful facts from the chunk
- faithfulness: no unsupported, distorted, or overclaimed facts
- specificity: preserves concrete paths, names, errors, commands, counts, and decisions
- salience: skips routine noise and keeps useful facts
- relevance_calibration: low/medium/high/critical ratings are reasonable

Use the historical observations as a silver reference, not perfect truth. Judge against the chunk.

CHUNK:
{case['chunk'][:24000]}

SILVER OBSERVATIONS:
{json.dumps(case.get('silver_observations', []), ensure_ascii=False)[:12000]}

CANDIDATE OBSERVATIONS:
{json.dumps(out.get('observations', []), ensure_ascii=False)[:12000]}
"""


def judge_outputs(args: argparse.Namespace) -> None:
    cases = {c["case_id"]: c for c in read_jsonl(args.out / "cases.jsonl")}
    outputs = read_jsonl(args.out / "candidate_outputs.jsonl")
    path = args.out / "judge_scores.jsonl"
    seen = set()
    if path.exists() and not args.force:
        for row in read_jsonl(path):
            seen.add((row.get("case_id"), row.get("candidate")))
    for out in outputs:
        key = (out["case_id"], out["candidate"])
        if key in seen:
            continue
        print(f"[judge] {out['candidate']} {out['case_id']}", flush=True)
        payload = {
            "model": args.judge_model,
            "messages": [
                {"role": "system", "content": "You are a strict evaluator of memory extraction quality. Return only valid JSON matching the schema."},
                {"role": "user", "content": judge_prompt(cases[out["case_id"]], out)},
            ],
            "temperature": 0,
            "max_tokens": 2000,
            "response_format": JUDGE_SCHEMA,
        }
        try:
            response = openrouter_request(payload, timeout=180)
            content = ((response.get("choices") or [{}])[0].get("message") or {}).get("content") or "{}"
            judgment = json.loads(content)
            row = {"case_id": out["case_id"], "task": out["task"], "candidate": out["candidate"], "judge_model": args.judge_model, **judgment, "usage": response.get("usage") or {}}
        except Exception as exc:
            row = {"case_id": out["case_id"], "task": out["task"], "candidate": out["candidate"], "judge_model": args.judge_model, "error": str(exc)}
        append_jsonl(path, row)
        time.sleep(args.sleep)
    print(f"wrote judge rows to {path.relative_to(REPO)}")


def aggregate_csv(path: Path) -> dict[str, dict[str, float]]:
    agg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts = Counter()
    if not path.exists():
        return {}
    with path.open() as f:
        for row in csv.DictReader(f):
            c = row["candidate"]
            counts[c] += 1
            for k, v in row.items():
                if k in {"candidate", "case_id", "task", "model", "thinking", "error"}:
                    continue
                try:
                    agg[c][k] += float(v or 0)
                except ValueError:
                    pass
    return {c: {k: v / counts[c] for k, v in vals.items()} | {"cases": counts[c]} for c, vals in agg.items()}


def aggregate_judge(path: Path) -> dict[str, dict[str, float]]:
    agg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts = Counter()
    if not path.exists():
        return {}
    for row in read_jsonl(path):
        if row.get("error"):
            continue
        c = row["candidate"]
        counts[c] += 1
        for k in ["recall", "faithfulness", "specificity", "salience", "relevance_calibration", "hallucination_count", "missing_important_count"]:
            agg[c][k] += float(row.get(k) or 0)
    return {c: {k: v / counts[c] for k, v in vals.items()} | {"judge_cases": counts[c]} for c, vals in agg.items()}


def write_review_packet(args: argparse.Namespace) -> None:
    cases = {c["case_id"]: c for c in read_jsonl(args.out / "cases.jsonl")}
    outputs = read_jsonl(args.out / "candidate_outputs.jsonl") if (args.out / "candidate_outputs.jsonl").exists() else []
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outputs:
        by_case[row["case_id"]].append(row)
    lines = [
        "# Human review packet: OM observer screen",
        "",
        "Use this packet to spot-check whether candidate observer outputs preserve important, source-grounded memories without hallucinating. Historical OM observations are silver references, not ground truth.",
        "",
    ]
    for case_id, case in cases.items():
        lines += [
            f"## {case_id}",
            "",
            f"Source result: `{case['source_result']}`",
            f"Chunk sources: {case['chunk_source_count']} · Chunk chars: {case['chunk_chars']} · Silver observations: {case['silver_count']}",
            "",
            "### Chunk preview",
            "",
            "```text",
            case["chunk"][:2500].replace("```", "` ` `") + ("\n...[truncated]" if len(case["chunk"]) > 2500 else ""),
            "```",
            "",
            "### Silver observations",
            "",
        ]
        for obs in case.get("silver_observations", []):
            lines.append(f"- [{obs.get('relevance')}] {obs.get('content')}")
        for out in sorted(by_case.get(case_id, []), key=lambda row: row["candidate"]):
            lines += [
                "",
                f"### Candidate: {out['candidate']}",
                "",
                f"model={out['model']} thinking={out['thinking']} observations={len(out.get('observations', []))} invalid_source_ids={out.get('invalid_source_ids')} malformed={out.get('malformed')} error={out.get('error')}",
                "",
            ]
            for obs in out.get("observations", []):
                src = ",".join(obs.get("sourceEntryIds") or [])
                lines.append(f"- [{obs.get('relevance')}] ({src}) {obs.get('content')}")
        lines.append("")
    path = args.out / "HUMAN_REVIEW_PACKET.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    print(f"wrote {path.relative_to(REPO)}")


def write_report(args: argparse.Namespace) -> None:
    mechanical = aggregate_csv(args.out / "mechanical_scores.csv")
    judge = aggregate_judge(args.out / "judge_scores.jsonl")
    candidates = sorted(set(mechanical) | set(judge))
    rows = []
    for c in candidates:
        m, j = mechanical.get(c, {}), judge.get(c, {})
        composite = (
            j.get("recall", 0) * 0.30 +
            j.get("faithfulness", 0) * 0.30 +
            j.get("specificity", 0) * 0.15 +
            j.get("salience", 0) * 0.15 +
            j.get("relevance_calibration", 0) * 0.10 -
            j.get("hallucination_count", 0) * 0.50
        ) if j else (m.get("silver_recall_ge_035", 0) * 5 + m.get("candidate_precision_f1_mean", 0) * 2)
        rows.append({"candidate": c, "composite": composite, **m, **j})
    best = max([r["composite"] for r in rows] or [0])
    viable = [r for r in rows if r["composite"] >= best * 0.95 and r.get("faithfulness", 5) >= 4 and r.get("hallucination_count", 0) <= 0.25]
    if not viable:
        viable = rows
    recommendation = min(viable, key=lambda r: r.get("estimated_cost_usd", math.inf) if r.get("estimated_cost_usd", 0) > 0 else math.inf, default=None)
    if recommendation is None and rows:
        recommendation = max(rows, key=lambda r: r["composite"])

    lines = [
        "# Offline OM observer-quality screen",
        "",
        "This report screens observer worker model/thinking settings on reconstructed observational-memory observer chunks. It isolates the observer task from downstream DeepSWE reward noise.",
        "",
        "## Methodology",
        "",
        "- Extracted one observer replay case for each task in `subsets/12_v0.txt` from historical DeepSeek observational-memory sessions.",
        "- Replayed the observer task with the vendored observer system prompt, the same `record_observations` tool schema, source-entry validation, timestamp/relevance validation, and a 16-turn cap.",
        f"- Compared {len(candidates)} completed candidate settings: {', '.join(candidates)}.",
        "- Scored outputs mechanically against historical observations as a silver reference, then judged recall, faithfulness, specificity, salience, relevance calibration, hallucinations, and missed important facts with an LLM judge.",
        "- Produced `HUMAN_REVIEW_PACKET.md` so a human can spot-check source chunks, silver observations, and every candidate output.",
        "",
        "## Recommendation",
        "",
    ]
    if recommendation:
        lines.append(f"Recommended setting: **{recommendation['candidate']}**.")
        lines.append("")
        lines.append("Selection rule: choose the lowest estimated-cost candidate within 95% of the best composite judge score, with average faithfulness >= 4 and hallucination count <= 0.25 per case. If no judge scores exist, use mechanical silver-reference overlap as a fallback.")
    else:
        lines.append("No recommendation: no scored candidate outputs were available.")
    lines += ["", "## Aggregate scores", "", "| candidate | composite | judge recall | faithfulness | hallucinations/case | silver recall >=0.35 | est cost/case | cases |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in sorted(rows, key=lambda x: x["composite"], reverse=True):
        lines.append(f"| {r['candidate']} | {r['composite']:.3f} | {r.get('recall', 0):.2f} | {r.get('faithfulness', 0):.2f} | {r.get('hallucination_count', 0):.2f} | {r.get('silver_recall_ge_035', 0):.3f} | ${r.get('estimated_cost_usd', 0):.5f} | {int(r.get('cases', r.get('judge_cases', 0)))} |")
    aa_path = args.out / "artificial_analysis_comparison.csv"
    if aa_path.exists():
        lines += [
            "",
            "## Artificial Analysis comparison",
            "",
            "The provided Artificial Analysis key had free-tier API access, which did not expose Pro per-benchmark fields. As a point of comparison, the public AA-Omniscience page was scraped into `analysis/om-observer-screen/artificial_analysis_comparison.csv`. Coverage is partial because the public page exposes selected chart rows rather than a full API dump.",
            "",
            "| AA label | Omniscience Index ↑ | Accuracy ↑ | Hallucination Rate ↓ | Notes |",
            "|---|---:|---:|---:|---|",
        ]
        with aa_path.open() as f:
            for row in csv.DictReader(f):
                def fmt(key: str, *, pct: bool = False) -> str:
                    value = row.get(key) or ""
                    if value == "":
                        return "—"
                    number = float(value)
                    return f"{number * 100:.1f}%" if pct else f"{number:.2f}"
                label = row.get("label", "")
                if "DeepSeek V4 Flash" in label:
                    note = "Tested here as DeepSeek V4 Flash off/low; AA public row is Max."
                elif "GPT-5.4 mini" in label:
                    note = "Tested here at low; AA public row is xhigh."
                elif "GPT-5.5" in label:
                    note = "Tested here at low; AA public row is xhigh and shows high hallucination rate despite high accuracy."
                elif "GLM-5.2" in label:
                    note = "Tested here at xhigh/high/low/off; AA public row is max."
                elif "Gemini" in label:
                    note = "Used as judge model family comparison, not observer candidate in this screen."
                else:
                    note = ""
                lines.append(f"| {label} | {fmt('omniscienceIndex')} | {fmt('omniscienceAccuracy', pct=True)} | {fmt('omniscienceHallucinationRate', pct=True)} | {note} |")
        lines += [
            "",
            "Interpretation: AA-Omniscience is useful prior information about knowledge reliability, but it did not overturn the direct observer replay result. In our actual observer task, GLM settings had the highest judged composite scores, while DeepSeek V4 Flash low remained the recommendation under the cost-aware rule because it was within 95% of the best composite score and much cheaper.",
        ]

    skipped_qwen = args.out / "partial_local_qwen_outputs_skipped.jsonl"
    if skipped_qwen.exists():
        skipped_rows = read_jsonl(skipped_qwen)
        skipped_errors = sum(1 for row in skipped_rows if row.get("error"))
        lines += [
            "",
            "## Skipped local Qwen run",
            "",
            f"Local Qwen was skipped after timeout problems. Preserved partial rows: {len(skipped_rows)} in `{skipped_qwen.relative_to(REPO)}`, with {skipped_errors} timeout/error rows. These rows are excluded from aggregate scoring and recommendation.",
        ]

    lines += [
        "",
        "## Artifacts",
        "",
        f"- Cases: `{(args.out / 'cases.jsonl').relative_to(REPO)}`",
        f"- Candidate outputs: `{(args.out / 'candidate_outputs.jsonl').relative_to(REPO)}`",
        f"- Mechanical scores: `{(args.out / 'mechanical_scores.csv').relative_to(REPO)}`",
        f"- Judge scores: `{(args.out / 'judge_scores.jsonl').relative_to(REPO)}`",
        f"- Human review packet: `{(args.out / 'HUMAN_REVIEW_PACKET.md').relative_to(REPO)}`",
        f"- Artificial Analysis comparison: `{(args.out / 'artificial_analysis_comparison.csv').relative_to(REPO)}`",
        "",
        "## Caveats",
        "",
        "- Historical observations are a silver reference, not ground truth.",
        "- OpenRouter accepts requested reasoning effort, but API acceptance alone does not prove a provider implements distinct internal thinking levels.",
        "- Current pi-observational-memory uses one configured worker model/thinking setting for observer, reflector, and dropper.",
    ]
    path = args.out / "REPORT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    print(f"wrote {path.relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("extract-cases")
    p.add_argument("--target", type=int, default=12)
    p.add_argument("--roots", nargs="+", default=["results/deepseek-v4-flash/high/observational-memory"])
    p.set_defaults(func=extract_cases)

    p = sub.add_parser("run-candidates")
    p.add_argument("--candidate", action="append", help="name=model:thinking; may be repeated")
    p.add_argument("--max-turns", type=int, default=16)
    p.add_argument("--sleep", type=float, default=0.5)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=run_candidates)

    p = sub.add_parser("score")
    p.set_defaults(func=score_outputs)

    p = sub.add_parser("judge")
    p.add_argument("--judge-model", default="google/gemini-2.5-flash")
    p.add_argument("--sleep", type=float, default=0.5)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=judge_outputs)

    p = sub.add_parser("review-packet")
    p.set_defaults(func=write_review_packet)

    p = sub.add_parser("report")
    p.set_defaults(func=write_report)

    args = ap.parse_args()
    args.out = args.out if args.out.is_absolute() else REPO / args.out
    args.func(args)


if __name__ == "__main__":
    main()
