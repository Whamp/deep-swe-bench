# pi-check@1.3.0

Pi-check config for `local-vllm/qwen-agentworld-35b-a3b`, served by server60 at
`http://100.92.238.117:8080/v1`.

The only behavior difference from `baseline-qwen-agentworld-35b@1.0.0` is the
existing pi-check extension and its `--check` flag. The extension queues one
verification follow-up after the initial agent pass. This config adds no system
preamble, orchestration text, or other config-authored executor prompt.

It preserves the baseline provider behavior:

- high thinking with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- a 65,536-token output ceiling; and
- sampling pinned to `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.2.0`. Its version impact is `rerun` because it
changes the executor model and provider request hook. It does not carry forward
the Ornith-only default Bash timeout from `pi-check@1.2.0`.
