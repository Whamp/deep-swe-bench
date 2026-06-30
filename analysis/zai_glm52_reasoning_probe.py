#!/usr/bin/env python3
"""Probe Z.ai GLM-5.2 thinking/reasoning controls without logging secrets.

This sends small, controlled non-streaming requests to the Z.ai chat completion
API and records: request payload (minus auth), status, usage, whether
reasoning_content is returned, and short content snippets.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.z.ai/api/paas/v4/chat/completions"
OUT = Path("analysis/zai-glm52-reasoning-probe.jsonl")

BASE_MESSAGES = [
    {
        "role": "system",
        "content": "You are a precise API behavior probe. Follow the user instruction exactly.",
    },
    {
        "role": "user",
        "content": "Return exactly this visible text and nothing else: OK",
    },
]

CASES: list[dict[str, Any]] = [
    {
        "name": "old_off_disabled_no_effort",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "disabled"},
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "old_enabled_no_effort_current_low_high_xhigh_collapse",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "proposed_low_maps_high",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "proposed_high",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "high",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "proposed_xhigh_maps_max",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "max",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "doc_xhigh_literal",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "xhigh",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "doc_low_literal",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "low",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
    {
        "name": "doc_none_literal",
        "payload": {
            "model": "glm-5.2",
            "messages": BASE_MESSAGES,
            "thinking": {"type": "enabled"},
            "reasoning_effort": "none",
            "max_tokens": 128,
            "temperature": 0,
        },
    },
]


def request_case(api_key: str, case: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(case["payload"]).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    started = time.time()
    record: dict[str, Any] = {
        "case": case["name"],
        "request_payload": case["payload"],
    }
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            record["http_status"] = resp.status
            record["elapsed_s"] = round(time.time() - started, 3)
            data = json.loads(text)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        record.update({
            "http_status": e.code,
            "elapsed_s": round(time.time() - started, 3),
            "error_body": text[:2000],
        })
        return record
    except Exception as e:
        record.update({
            "elapsed_s": round(time.time() - started, 3),
            "error": repr(e),
        })
        return record

    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    reasoning = msg.get("reasoning_content") or ""
    content = msg.get("content") or ""
    record.update({
        "response_id": data.get("id"),
        "response_model": data.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage"),
        "has_reasoning_content": bool(reasoning),
        "reasoning_chars": len(reasoning),
        "content_chars": len(content),
        "reasoning_preview": reasoning[:300],
        "content_preview": content[:300],
        "raw_top_level_keys": sorted(data.keys()),
        "message_keys": sorted(msg.keys()),
    })
    return record


def main() -> int:
    api_key = os.environ.get("ZAI_API_KEY")
    if not api_key:
        print("ZAI_API_KEY is not set", file=sys.stderr)
        return 2
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for case in CASES:
            rec = request_case(api_key, case)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(json.dumps({
                "case": rec.get("case"),
                "status": rec.get("http_status"),
                "reasoning_chars": rec.get("reasoning_chars"),
                "usage": rec.get("usage"),
                "content": rec.get("content_preview"),
                "error": rec.get("error") or rec.get("error_body"),
            }, ensure_ascii=False))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
