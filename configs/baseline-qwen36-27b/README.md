# baseline-qwen36-27b

Clean stock-Pi baseline for
`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, served from server60 at
`http://100.92.238.117:30000/v1`.

This config has no `system_preamble.md` and no `orchestration.md`. Its two
extensions are provider infrastructure only:

- preserve Qwen reasoning across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- apply the requested sampling tuple:
  `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  `presence_penalty=0.0`, and `repetition_penalty=1.0`.

Pi's `qwen-chat-template` compatibility sets
`chat_template_kwargs.enable_thinking=true` for thinking level `high`. This
config does not add a hard `thinking_token_budget`.

Intended run:

```bash
PYTHONPATH=. python3 harness/run_batch.py \
  --configs baseline-qwen36-27b \
  --subset 12_v2 \
  --runs 3 \
  --workers 2 \
  --model local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4 \
  --thinking high \
  --run-id qwen36-27b-high-clean-12v2-r3-w2 \
  --progress-interval 15
```
