# baseline-thinkingcap-qwen36@1.1.0

Stock Pi baseline for
`local-vllm/thinkingcap-qwen3.6-27b-awq-int4`, served by server60 at
`http://100.92.238.117:8081/v1`.

This config adds no config-authored prompt text. Its model-specific provider
request extension:

- preserves prior reasoning across multi-turn tool calls;
- pins ThinkingCap's sampling settings: `temperature=1.0`, `top_p=0.95`,
  `top_k=20`, `min_p=0.0`, and `repetition_penalty=1.0`.

The `high` leaf enables thinking and caps the complete model output at 98,304
tokens. It deliberately sends no hard `thinking_token_budget`; reasoning and
final output share the same generation envelope, avoiding a budget boundary
inside tool-call arguments.

This release succeeds `baseline-thinkingcap-qwen36@1.0.0`. Its version impact is
`rerun` because the endpoint, served model identity, output ceiling, and
thinking-budget behavior changed.
