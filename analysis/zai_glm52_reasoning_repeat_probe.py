#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error
from pathlib import Path

URL = "https://api.z.ai/api/coding/paas/v4/chat/completions"
OUT = Path("analysis/zai-glm52-reasoning-repeat-probe.jsonl")
PROMPT = (
    "Solve this exactly. A process starts at 17. Repeat this operation 9 times: "
    "multiply by 3, subtract 4, then divide by 5 if divisible else add 7. "
    "Show no reasoning in visible content. Return only 'ANSWER: <integer>'."
)
MESSAGES = [
    {"role":"system","content":"You are a controlled API probe. Follow output formatting exactly."},
    {"role":"user","content":PROMPT},
]
CASES = [
    ("disabled", {"thinking":{"type":"disabled"}}),
    ("enabled_no_effort_old", {"thinking":{"type":"enabled"}}),
    ("effort_high", {"thinking":{"type":"enabled"}, "reasoning_effort":"high"}),
    ("effort_max", {"thinking":{"type":"enabled"}, "reasoning_effort":"max"}),
    ("literal_low", {"thinking":{"type":"enabled"}, "reasoning_effort":"low"}),
    ("literal_xhigh", {"thinking":{"type":"enabled"}, "reasoning_effort":"xhigh"}),
    ("literal_none", {"thinking":{"type":"enabled"}, "reasoning_effort":"none"}),
]

def call(key, name, extra, rep):
    payload = {"model":"glm-5.2", "messages": MESSAGES, "max_tokens":512, "temperature":0, **extra}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", "Authorization":f"Bearer {key}"}, method="POST")
    start=time.time()
    rec={"case":name,"rep":rep,"request_payload":payload}
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data=json.loads(r.read().decode())
            rec["http_status"]=r.status
    except urllib.error.HTTPError as e:
        rec["http_status"]=e.code; rec["error_body"]=e.read().decode()[:1000]; return rec
    except Exception as e:
        rec["error"]=repr(e); return rec
    msg=(data.get("choices") or [{}])[0].get("message") or {}
    reasoning=msg.get("reasoning_content") or ""
    content=msg.get("content") or ""
    usage=data.get("usage") or {}
    rec.update({
        "elapsed_s": round(time.time()-start,3),
        "response_model": data.get("model"),
        "finish_reason": (data.get("choices") or [{}])[0].get("finish_reason"),
        "usage": usage,
        "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "reasoning_chars": len(reasoning),
        "has_reasoning_content": bool(reasoning),
        "content": content[:500],
        "reasoning_preview": reasoning[:300],
        "message_keys": sorted(msg.keys()),
    })
    return rec

def main():
    key=os.environ.get("ZAI_API_KEY")
    if not key: raise SystemExit("ZAI_API_KEY missing")
    OUT.parent.mkdir(exist_ok=True, parents=True)
    with OUT.open("w") as f:
        for rep in range(3):
            for name, extra in CASES:
                rec=call(key,name,extra,rep)
                f.write(json.dumps(rec, ensure_ascii=False)+"\n"); f.flush()
                print(json.dumps({k:rec.get(k) for k in ["case","rep","http_status","reasoning_tokens","reasoning_chars","content","error_body","error"]}, ensure_ascii=False))
    print(f"wrote {OUT}")
if __name__ == "__main__": main()
