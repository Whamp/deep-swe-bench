# pi-check@1.6.0

Qwen-AgentWorld config for pi-check PreFlight and final verification on
`local-vllm/qwen-agentworld-35b-a3b`, served by server60 at
`http://100.92.238.117:8080/v1`.

This release combines the Qwen-AgentWorld behavior from `pi-check@1.3.0` with
the pi-check package introduced by `pi-check@1.5.0`:

- `--check-preflight` blocks the first detected file mutation before execution
  and steers the same model through the extension-owned architecture checkpoint;
- `--check local-vllm/qwen-agentworld-35b-a3b:high` queues one final
  verification pass in the same Pi session;
- Bash calls without a numeric timeout default to 360 seconds, while explicit
  numeric timeouts are preserved; and
- the vendored pi-check package is pinned to upstream commit
  `57d50132b210dae10bc8da220fb89ca9d119f470`.

PreFlight and final verification are independent one-shots. They use the same
Qwen-AgentWorld model, high thinking level, and Pi session as the original task.
Native `session/*.jsonl` usage therefore accounts for every provider request.

This config adds no system preamble, orchestration text, or config-authored
executor prompt. Both checkpoint prompts belong to the vendored pi-check
extension.

The provider behavior remains unchanged from `pi-check@1.3.0`:

- high thinking with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- a 65,536-token output ceiling;
- text-only input through `openai-completions`; and
- sampling pinned to `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.5.0`. Its version impact is `rerun` because it
changes the executor model and provider hook and applies PreFlight to
Qwen-AgentWorld for the first time.
