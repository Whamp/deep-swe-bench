# qwen36-27b-contract-checkpoints

Prompt-only treatment for
`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, served from server60 at
`http://100.92.238.117:30000/v1`.

This config is an infrastructure clone of `baseline-qwen36-27b`. The only
intended treatment difference is the seven approved v2 instructions in
`orchestration.md`. They were promoted after the full 36-cell baseline audit and
interactive diff review. It has no `system_preamble.md`, skills, behavioral
extensions, worker models, or additional tools.

The instructions use `orchestration.md` because the harness appends that file to
Pi's system prompt without modifying the task repository. A config-local
`AGENTS.md` would not be discovered from Pi's `/app` working directory; copying
one into `/app` would contaminate the task workspace and submission patch.

The unchanged provider infrastructure:

- preserves Qwen reasoning across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- applies `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  `presence_penalty=0.0`, and `repetition_penalty=1.0`;
- uses high thinking without a hard `thinking_token_budget`.

Intended paired measurement after the baseline completes:

```bash
PYTHONPATH=. python3 harness/run_batch.py \
  --configs baseline-qwen36-27b,qwen36-27b-contract-checkpoints \
  --subset 12_v2 \
  --runs 3 \
  --workers 2 \
  --model local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4 \
  --thinking high \
  --run-id qwen36-27b-contract-checkpoints-high-12v2-r3-w2 \
  --progress-interval 15
```

Existing baseline cells are skipped by `result.json`, so this command runs the
new treatment while preserving a paired comparison against the same task/rep
slots.
