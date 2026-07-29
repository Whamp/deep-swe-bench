# pi-check@1.1.0

Pi-check treatment for `local-vllm/gemma-4-31b`, served by server60 at
`http://100.92.238.117:8034/v1`.

The only treatment difference from `baseline-gemma4-31b@1.0.0` is the existing
pi-check extension and its `--check` flag. The extension queues one verification
follow-up after the initial agent pass.

This config has no `system_preamble.md`, no `orchestration.md`, and no other
config-authored executor prompt. It preserves the baseline's Gemma provider
behavior:

- binary thinking enabled with `chat_template_kwargs.enable_thinking=true`;
- reasoning preserved during tool calls with
  `chat_template_kwargs.preserve_thinking=true`;
- sampling pinned to `temperature=1.0`, `top_p=0.95`, `top_k=64`, `min_p=0.0`,
  and `repetition_penalty=1.0`.
