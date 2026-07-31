# pi-check@1.2.0

Pi-check treatment for `local-vllm/ornith-1.0-35b`, served by server60 at
`http://100.92.238.117:8082/v1`.

The only treatment difference from `baseline-ornith-35b@1.1.0` is the existing
pi-check extension and its `--check` flag. The extension queues one verification
follow-up after the initial agent pass. Both configs mechanically default every
`bash` call without a numeric model-chosen timeout to 360 seconds and preserve
model-chosen timeout values.

This config has no `system_preamble.md`, no `orchestration.md`, and no other
config-authored executor prompt. It preserves the baseline's Ornith provider
behavior:

- binary thinking enabled with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns by Ornith's checkpoint chat template;
- sampling pinned to `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.1.0`. Its version impact is `rerun` because it
uses the Ornith model and adds the default Bash-timeout behavior.
