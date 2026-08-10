# pi-check@1.4.0

Pi-check config for `local-vllm/thinkingcap-qwen3.6-27b-awq-int4`, served by
server60 at `http://100.92.238.117:8081/v1`.

The behavior differences from `baseline-thinkingcap-qwen36@1.1.0` are:

- the existing pi-check extension and its `--check` flag, which queue one
  verification follow-up after the initial agent pass; and
- a 360-second default for Bash calls that omit a numeric timeout, while every
  model-chosen timeout is preserved.

The Bash policy prevents one unbounded tool call from consuming the full agent
allowance. This config adds no system preamble, orchestration text, or other
config-authored executor prompt. The verification wording is the unchanged
extension-owned pi-check prompt.

It preserves the baseline provider behavior:

- high thinking with `chat_template_kwargs.enable_thinking=true`;
- prior reasoning carried across tool turns with
  `chat_template_kwargs.preserve_thinking=true`;
- a 98,304-token output ceiling with no separate hard thinking-token budget;
- text-only input through `openai-completions`; and
- sampling pinned to `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
  and `repetition_penalty=1.0`.

This release succeeds `pi-check@1.3.0`. Its version impact is `rerun` because it
changes the executor model, provider request hook, and Bash timeout audit. The
ThinkingCap-specific audit marker records whether each Bash timeout was defaulted
or preserved.
