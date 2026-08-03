# pi-check@1.3.0

Pi-check config for `local-vllm/qwen-agentworld-35b-a3b`, served by server60 at
`http://100.92.238.117:8080/v1`.

The behavior differences from `baseline-qwen-agentworld-35b@1.0.0` are:

- the existing pi-check extension and its `--check` flag, which queue one
  verification follow-up after the initial agent pass; and
- a 360-second default for Bash calls that omit a numeric timeout, while every
  model-chosen timeout is preserved.

The Bash policy prevents one unbounded tool call from consuming the full agent
allowance. Baseline LangChain reps 1 and 2 both ended on such calls after roughly
51 minutes without a tool result. This config adds no system preamble,
orchestration text, or other config-authored executor prompt.

It preserves the baseline provider behavior:

- high thinking with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- a 65,536-token output ceiling; and
- sampling pinned to `temperature=0.6`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.2.0`. Its version impact is `rerun` because it
changes the executor model, provider request hook, and Bash timeout policy. The
Qwen-specific audit marker records whether each Bash timeout was defaulted or
preserved.
