# baseline-qwen-agentworld-35b@1.0.0

Stock Pi baseline for `local-vllm/qwen-agentworld-35b-a3b`, served by
server60 at `http://100.92.238.117:8080/v1`.

This config adds no config-authored prompt text. Its model-specific provider
request extension:

- preserves prior thinking across multi-turn tool calls;
- pins Qwen's sampling settings: `temperature=0.6`, `top_p=0.95`, `top_k=20`,
  `min_p=0.0`, and `repetition_penalty=1.0`.

The `high` leaf enables thinking and caps model output at 65,536 tokens. Qwen's
model card recommends 32,768 output tokens for most AgentWorld requests; this
release uses the operator-approved larger ceiling for DeepSWE tasks.

Qwen-AgentWorld is trained primarily as a language world model for environment
simulation. This benchmark deliberately evaluates it as Pi's coding executor.
