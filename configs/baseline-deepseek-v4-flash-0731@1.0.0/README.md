# baseline-deepseek-v4-flash-0731@1.0.0

Stock Pi baseline for `local-llamacpp/deepseek-v4-flash-0731`, served by
server60 at `http://100.92.238.117:8200/v1`.

This config has no `system_preamble.md`, no `orchestration.md`, and no other
config-authored prompt text. Its one extension pins the live server profile's
sampling settings: `temperature=1.0`, `top_p=0.95`, `top_k=0`, `min_p=0.0`, and
`repeat_penalty=1.0`.

The single `max` leaf enables thinking through
`chat_template_kwargs.thinking=true` and maps Pi's `max` level to the custom
chat template's `reasoning_effort=max`. The server has one inference slot, so
this release declares executor concurrency 1.
