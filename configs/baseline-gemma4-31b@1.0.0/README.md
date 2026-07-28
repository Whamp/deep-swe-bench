# baseline-gemma4-31b@1.0.0

Stock Pi baseline for `local-vllm/gemma-4-31b`, served by server60 at
`http://100.92.238.117:8034/v1`.

This config has no `system_preamble.md`, no `orchestration.md`, and no other
config-authored prompt text. Its one extension supplies provider infrastructure:

- preserve Gemma 4 reasoning during multi-step tool calls with
  `chat_template_kwargs.preserve_thinking=true`;
- apply the live server profile's sampling settings: `temperature=1.0`,
  `top_p=0.95`, `top_k=64`, `min_p=0.0`, and `repetition_penalty=1.0`.

The `high` leaf enables Gemma 4's binary thinking mode through
`chat_template_kwargs.enable_thinking=true`.
