# observational-memory-gpt55-xhigh

Observational-memory config for the GPT-5.5-low executor observer-model grid.

- Main executor: `openai-codex/gpt-5.5`, thinking `low` (selected by `harness/run_batch.py --model/--thinking`).
- Observational-memory observer/reflector/dropper worker: `openai-codex/gpt-5.5`, thinking `xhigh`.
- Extension tracing: `extensions/om-worker-usage-trace.ts` records compact worker usage metadata only.
- API validation: see `docs/openai-codex-thinking.md` plus `analysis/openai-codex-thinking-request-probe.jsonl` and `analysis/openai-codex-thinking-live-probe.jsonl`.

The smoke contract requires Codex docs/probe artifacts, executor session markers, OM observation records, worker usage trace records for `openai-codex/gpt-5.5` at `xhigh`, and forbids OpenRouter/ZAI worker traces.
