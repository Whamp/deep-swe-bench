# observational-memory-qwen36-off

Observational-memory config for testing a GPT-5.5-low executor with a local Qwen observer.

- Main executor: `openai-codex/gpt-5.5`, thinking `low` selected by `harness/run_batch.py --model/--thinking`.
- Observational-memory observer/reflector/dropper worker: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, thinking `off`.
- Local endpoint: `http://100.92.238.117:30000/v1` on server60.
- Extension tracing: `extensions/om-worker-usage-trace.ts` records compact worker usage metadata only.
- API validation:
  - `docs/openai-codex-thinking.md`
  - `docs/local-vllm-qwen36-thinking.md`
  - `analysis/local-vllm-qwen-thinking-request-probe.jsonl`
  - `analysis/local-vllm-qwen-off-live-probe.jsonl`

The smoke contract requires Codex executor session markers, local-Qwen model leaf metadata, OM observation records, worker usage trace records for `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4` at `off`, and forbids OpenRouter/ZAI worker traces.
