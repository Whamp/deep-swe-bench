# baseline-laguna-s21

Clean stock-Pi baseline for
`local-vllm/poolside/Laguna-S-2.1-INT4`, served from server60 at
`http://100.92.238.117:30000/v1`.

This config intentionally has no `system_preamble.md` and no
`orchestration.md`. Its extensions are provider infrastructure only:

- preserve Laguna's thinking across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- apply Poolside's recommended sampling tuple: `temperature=0.7` and
  `top_p=0.95`.

The requested batch is **12_v2, 3 reps**, but it has not been launched.

Intended command:

```bash
PYTHONPATH=. python3 harness/run_batch.py \
  --configs baseline-laguna-s21 \
  --subset 12_v2 \
  --runs 3 \
  --workers 2 \
  --model local-vllm/poolside/Laguna-S-2.1-INT4 \
  --thinking high \
  --run-id laguna-s21-high-12v2-r3-w2 \
  --progress-interval 15
```
