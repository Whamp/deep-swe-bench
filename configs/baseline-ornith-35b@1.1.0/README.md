# baseline-ornith-35b@1.1.0

Stock Pi baseline for `local-vllm/ornith-1.0-35b`, served by server60 at
`http://100.92.238.117:8082/v1`.

This config adds one approved `orchestration.md` instruction requiring every
`bash` call to include a command-level timeout. It has no `system_preamble.md`
or other config-authored prompt text. Its one extension pins the live server profile's
sampling settings: `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
and `repetition_penalty=1.0`.

The `high` leaf enables Ornith's reasoning mode through
`chat_template_kwargs.enable_thinking=true`. Ornith's checkpoint chat template
already carries prior `reasoning_content` across tool turns, so this config does
not add a separate thought-preservation override.

This release succeeds `baseline-ornith-35b@1.0.0`. Its version impact is
`rerun` because the orchestration instruction changes agent behavior.
