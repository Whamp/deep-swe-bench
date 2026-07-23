# baseline-thinkingcap-qwen36-temp06

Clean stock-Pi baseline for `local-vllm/bottlecapai/ThinkingCap-Qwen3.6-27B`
served from server60 at `http://100.92.238.117:30000/v1`.

This config intentionally has no `system_preamble.md` and no `orchestration.md`.
The only extensions are local-vLLM infrastructure: one preserves Qwen thinking and
sets a per-request `thinking_token_budget`; the other appends the required
ThinkingCap sampling parameters (`temperature=0.6`, `top_p=0.95`, `top_k=20`,
`min_p=0.0`, `presence_penalty=0.0`, `repetition_penalty=1.0`) to the provider payload.

Intended first run:

```bash
PYTHONPATH=. python3 harness/run_batch.py \
  --configs baseline-thinkingcap-qwen36-temp06 \
  --subset 12_v2 \
  --runs 3 \
  --workers 2 \
  --model local-vllm/bottlecapai/ThinkingCap-Qwen3.6-27B \
  --thinking high \
  --run-id thinkingcap-qwen36-temp06-high-12v2-r3-w2 \
  --progress-interval 15
```
