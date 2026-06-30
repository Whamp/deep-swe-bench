#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from pathlib import Path

URL = "https://api.z.ai/api/coding/paas/v4/chat/completions"
OUT = Path("analysis/zai-glm51-5v-probe.jsonl")
REASON_PROMPT = (
    "Solve this exactly. A process starts at 17. Repeat this operation 9 times: "
    "multiply by 3, subtract 4, then divide by 5 if divisible else add 7. "
    "Show no reasoning in visible content. Return only 'ANSWER: <integer>'."
)
IMAGE_URL = "https://cloudcovert-1305175928.cos.ap-guangzhou.myqcloud.com/%E5%9B%BE%E7%89%87grounding.PNG"

def text_messages(prompt: str):
    return [
        {"role":"system","content":"You are a controlled Z.ai API probe. Follow output formatting exactly."},
        {"role":"user","content":prompt},
    ]

def image_messages():
    return [{"role":"user","content":[
        {"type":"image_url","image_url":{"url":IMAGE_URL}},
        {"type":"text","text":"Answer with exactly 'IMAGE-SEEN' if an image is present. Otherwise answer 'NO-IMAGE'."},
    ]}]

CASES = [
    ("glm51_disabled", {"model":"glm-5.1", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"disabled"}}),
    ("glm51_enabled_no_effort", {"model":"glm-5.1", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"enabled"}}),
    ("glm51_effort_high_sent", {"model":"glm-5.1", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"enabled"}, "reasoning_effort":"high"}),
    ("glm51_effort_max_sent", {"model":"glm-5.1", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"enabled"}, "reasoning_effort":"max"}),
    ("glm5v_text_disabled", {"model":"glm-5v-turbo", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"disabled"}}),
    ("glm5v_text_enabled_no_effort", {"model":"glm-5v-turbo", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"enabled"}}),
    ("glm5v_text_effort_high_sent", {"model":"glm-5v-turbo", "messages": text_messages(REASON_PROMPT), "thinking":{"type":"enabled"}, "reasoning_effort":"high"}),
    ("glm5v_image_enabled_no_effort", {"model":"glm-5v-turbo", "messages": image_messages(), "thinking":{"type":"enabled"}}),
    ("glm5v_image_disabled", {"model":"glm-5v-turbo", "messages": image_messages(), "thinking":{"type":"disabled"}}),
]

def call(key: str, name: str, payload: dict):
    payload = {"max_tokens": 512, "temperature": 0, **payload}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json", "Authorization":f"Bearer {key}"}, method="POST")
    start=time.time(); rec={"case":name,"request_payload":payload}
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data=json.loads(r.read().decode()); rec["http_status"]=r.status
    except urllib.error.HTTPError as e:
        rec.update({"http_status":e.code,"elapsed_s":round(time.time()-start,3),"error_body":e.read().decode()[:2000]}); return rec
    except Exception as e:
        rec.update({"elapsed_s":round(time.time()-start,3),"error":repr(e)}); return rec
    choice=(data.get("choices") or [{}])[0]
    msg=choice.get("message") or {}
    usage=data.get("usage") or {}
    reasoning=msg.get("reasoning_content") or ""
    content=msg.get("content") or ""
    rec.update({
        "elapsed_s":round(time.time()-start,3),
        "response_model":data.get("model"),
        "finish_reason":choice.get("finish_reason"),
        "usage":usage,
        "reasoning_tokens":(usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "reasoning_chars":len(reasoning),
        "content":content[:500],
        "message_keys":sorted(msg.keys()),
        "reasoning_preview":reasoning[:300],
    })
    return rec

def main():
    key=os.environ.get("ZAI_API_KEY")
    if not key: raise SystemExit("ZAI_API_KEY missing")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for name, payload in CASES:
            rec=call(key,name,payload)
            f.write(json.dumps(rec, ensure_ascii=False)+"\n"); f.flush()
            print(json.dumps({k:rec.get(k) for k in ["case","http_status","response_model","reasoning_tokens","reasoning_chars","content","error_body","error"]}, ensure_ascii=False))
    print(f"wrote {OUT}")
if __name__ == "__main__": main()
