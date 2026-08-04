# pi-check@1.5.0

ThinkingCap config for testing pi-check preflight and final verification on
`local-vllm/thinkingcap-qwen3.6-27b-awq-int4`, served by server60 at
`http://100.92.238.117:8081/v1`.

The behavior differences from `pi-check@1.4.0` are:

- `--check-preflight` blocks the first detected file mutation before execution
  and steers the same model through the extension-owned architecture checkpoint;
- `--check local-vllm/thinkingcap-qwen3.6-27b-awq-int4:high` queues one final
  verification pass in the same Pi session; and
- the vendored pi-check package is pinned to upstream commit
  `57d50132b210dae10bc8da220fb89ca9d119f470`.

The preflight and final verification are independent one-shots. Preflight does
not start a second session or call a second model. The final verification uses
the same ThinkingCap model and high thinking level as the original task.
Native `session/*.jsonl` usage therefore accounts for all provider requests.

The 360-second default for Bash calls remains unchanged. Every model-chosen
numeric timeout is preserved.

This config adds no system preamble, orchestration text, or config-authored
executor prompt. Both checkpoint prompts belong to the vendored pi-check
extension.

The provider behavior remains unchanged:

- high thinking with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- a 98,304-token output ceiling with no separate hard thinking-token budget;
- text-only input through `openai-completions`; and
- sampling pinned to `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.4.0`. Its version impact is `rerun` because it
adds the preflight checkpoint and replaces bare same-model final verification
with the upstream extension's exact model selection.
