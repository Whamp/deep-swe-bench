# observational-memory-gpt54-off

Observational-memory config for the GPT-5.5-low executor observer-model grid.

- Main executor: `openai-codex/gpt-5.5`, thinking `low` (selected by `harness/run_batch.py --model/--thinking`).
- Observational-memory observer/reflector/dropper worker: `openai-codex/gpt-5.4`, thinking `off`.
- Extension tracing: `extensions/om-worker-usage-trace.ts` records compact worker usage metadata only.
- API validation: see `docs/openai-codex-thinking.md` plus `analysis/openai-codex-thinking-request-probe.jsonl` and `analysis/openai-codex-thinking-live-probe.jsonl`.

The smoke contract requires Codex docs/probe artifacts, executor session markers, OM observation records, worker usage trace records for `openai-codex/gpt-5.4` at `off`, and forbids OpenRouter/ZAI worker traces.

## Explicit `none` enforcement

This off config must force OM worker `openai-codex/gpt-5.4` requests to explicit OpenAI `reasoning: {effort: "none", summary: "auto"}`. `pi-observational-memory` worker calls run through nested `agentLoop` paths, so the effective mutation/audit lives in the vendored OM worker request path (`extensions/pi-observational-memory/src/agents/*/agent.ts`) rather than relying only on a normal config-level provider hook. The worker writes a compact runtime audit record to `pi-agent/observational-memory/codex-thinking/requests.ndjson`. The smoke contract requires that copied result artifact, so smoke proves the config is exercising explicit provider `none`, not just Pi's generic `off` label. The main executor is not affected because it runs with explicit thinking `low`.
