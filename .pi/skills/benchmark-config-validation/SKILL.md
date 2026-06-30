---
name: benchmark-config-validation
description: Use before adding or changing a deep-swe-bench config, model leaf, provider/model API path, usage parser, smoke contract, or extension/subagent worker usage accounting.
---

# Benchmark Config Validation

A **config** is not ready until every LLM role is measurable and one smoke cell proves it.

## Process

1. **Validate the provider path.**
   - Before using a new provider/model/API path, create or update `docs/<model>-thinking.md`.
   - Include: official docs URLs, endpoint/API family, thinking/reasoning/tool-streaming/token-limit fields, Pi/custom-model metadata, request-shape probe, live/provider-response probe, usage shape, config rules, stale patterns to avoid, and `analysis/` artifact paths.
   - Completion: the note and probe artifacts exist; any smoke contract that depends on them uses `requireRepoFiles`/`requireRepoText`.

2. **Account for every LLM role.**
   - Main executor usage comes from native `session/*.jsonl` assistant `message.usage` records.
   - Do not persist raw `--mode json` streams; they repeat growing chunks and previously filled the repo.
   - Advisor usage comes only from filtered `tool_execution_end` events in `tool-usage.jsonl`.
   - Observational-memory worker usage comes from `pi-agent/observational-memory/worker-usage/usage.ndjson` when `extensions/om-worker-usage-trace.ts` is loaded.
   - The OM debug `tokens` field is context coverage, not billed API usage.
   - Completion: `result.json` contains non-zero fields for every expected role, such as `advisor_*` or `om_worker_*`.

3. **Respect nested workers.**
   - Do not assume config-level Pi extension hooks see extension-internal worker calls.
   - `pi-observational-memory` observer/reflector/dropper calls go through direct `agentLoop` calls.
   - Put worker request mutation/audit logic in that worker path, or prove the hook fires there.
   - Completion: the proof is copied into the result cell, not just inferred from source code.

4. **Write smoke contracts in config space.**
   - Keep `harness/run_batch.py` generic: normal cell, `agent_exit == 0`, no timeout, non-zero usage, native session file.
   - Put feature-specific checks in `configs/<config>/smoke.json` or `configs/<config>/<model-leaf>/<thinking>/smoke.json`.
   - Contract paths are relative to the result cell after `harness/run.py` copies artifacts out of the container.
   - For OM worker audits, prefer `pi-agent/observational-memory/...`; files elsewhere under `/root/.pi/agent` are invisible unless `run.py` copies them.
   - Completion: the config-authored `smoke.json` names every required result field, file, required text, forbidden text, and repo-level validation artifact.

5. **Smoke before fan-out.**
   - For any config with no results for the selected executor model/thinking leaf, let `harness/run_batch.py` run one rep0 smoke cell from `12_v0` unless separate evidence justifies `--no-smoke-new-configs`.
   - Inspect the smoke `result.json` before a full comparison.
   - Completion: the smoke gate passes and leaves evidence in the result tree.

A usage gap found after a full comparison is data you do not have and will not re-collect.
