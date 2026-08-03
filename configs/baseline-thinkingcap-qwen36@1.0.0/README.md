# baseline-thinkingcap-qwen36@1.0.0

Stock Pi baseline for
`local-vllm/bottlecapai/ThinkingCap-Qwen3.6-27B`, served by server60 at
`http://100.92.238.117:30000/v1`.

Tool-calling requirements, residual risks, and the pre-run validation checklist
are recorded in
[`docs/thinkingcap-qwen36-tool-calling.md`](../../docs/thinkingcap-qwen36-tool-calling.md).

This config adds no `system_preamble.md`, `orchestration.md`, or other
config-authored prompt text. Its provider-request extension supplies only the
model-specific local-vLLM infrastructure:

- preserve Qwen3.6 reasoning across multi-turn tool calls;
- cap the `high` thinking level at 32,768 tokens;
- apply BottleCapAI's sampling settings: `temperature=1.0`, `top_p=0.95`,
  `top_k=20`, and `min_p=0.0`.

This release succeeds the unversioned legacy config
`baseline-thinkingcap-qwen36`. Its version impact is `rerun`: confirmed runs
require the versioned lock and must not claim compatibility with legacy result
provenance.

Prepare the requested `12_v2` run with three reps without executing it:

```bash
export DEEP_SWE_BENCH_STATE_ROOT=/home/will/evals/deep-swe-bench/results/_runs
python3 -m harness.run_batch plan \
  --subject pi \
  --configs baseline-thinkingcap-qwen36@1.0.0 \
  --baseline-config baseline-thinkingcap-qwen36@1.0.0 \
  --model local-vllm/bottlecapai/ThinkingCap-Qwen3.6-27B \
  --thinking high \
  --subset 12_v2 \
  --reps 3 \
  --workers 4 \
  --run-id thinkingcap-qwen36-high-baseline-12v2-r3-w4 \
  --preflight required \
  --state-root "$DEEP_SWE_BENCH_STATE_ROOT" \
  --plan-out runs/launch-plans/thinkingcap-qwen36-high-baseline-12v2-r3-w4.json \
  --receipt-out runs/launch-plans/thinkingcap-qwen36-high-baseline-12v2-r3-w4.txt
```

Planning is model-free. Do not execute the resulting plan until the GPU is free
and its receipt and exact plan identity have been reviewed.
