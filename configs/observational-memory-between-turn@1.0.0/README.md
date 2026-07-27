# observational-memory-between-turn@1.0.0

DeepSWE config for testing whether replacing older raw context with recorded
observations helps `openai-codex/gpt-5.6-sol` at thinking `low`.

## Behavior

The config loads `pi-observational-memory` with its between-turn continuation
policy. After a tool-bearing turn crosses 25,000 raw source tokens, the
extension aborts the pending next request, waits for Pi to settle, compacts,
and resumes the interrupted work through its hidden continuation message.
Pi retains approximately the newest 15,000 tokens.

The approved settings are:

| Setting | Value |
| --- | ---: |
| Observation cadence | 10,000 tokens |
| Reflection cadence | 20,000 tokens |
| Compaction trigger | 25,000 tokens |
| Pi retained tail | 15,000 tokens |
| Observation pool maximum | 20,000 tokens |
| Observation pool target | 10,000 tokens |
| Worker model | `openai-codex/gpt-5.6-sol` |
| Worker thinking | `low` |
| Worker maximum turns per invocation | 16 |

Both the executor and the observational-memory workers use Codex OAuth
subscription quota. Worker calls are serial, with a declared ceiling of 64
invocations per rep. Historical OM cells peaked at 14. Compact usage records are
written to `pi-agent/observational-memory/worker-usage/usage.ndjson`.

## Known limitation

This deliberately preserves the established 20,000/10,000 observation-pool
settings. DeepSWE trajectories are too short to reach the 20,000-token full-fold
threshold. The expected intervention is therefore **compaction with
observations**. Reflections may be recorded and are accounted for when present,
but the first normal fold excludes them; the dropper is not expected to run.

The leaf smoke contract requires `details.fullFold: false`, zero dropper calls,
observational-memory ownership of the prune boundary, a persisted compaction,
and the package-owned hidden continuation record. A live process or worker
trace alone cannot pass preflight.

## No executor prompt

The config has no `system_preamble.md`, `orchestration.md`, or appended system
prompt. The only continuation instruction is emitted by the extension under
test.

## Vendored source

The package under `extensions/pi-observational-memory/` comes from:

- repository: <https://github.com/elpapi42/pi-observational-memory>
- commit: `e5d54824c44402ee12c8fcd924a146cee8f2caf1`
- package version: `3.0.3`

The vendored source adds one typed usage-forwarding helper and calls it from the
observer, reflector, and dropper event-drain loops. Those calls forward nested
worker events to the config-owned compact usage tracer; they do not alter worker
prompts, model requests, tools, or structured outcomes. The vendored copy also
removes one trailing blank line from `src/tokens.ts`.

## Calibration and preflight

`analysis/observational-memory-between-turn-1.0.0-calibration.json` records the
model-free threshold calibration against 108 historical GPT-5.5 trajectories.
It is exposure evidence, not an efficacy prediction for GPT-5.6 SOL.

The confirmed preflight must use a task that naturally crosses 25,000 tokens.
Historical GPT-5.6 SOL baseline evidence makes
`yjs-map-conflict-detection` rep 0 an evidence-backed candidate, but only the
atomic preflight can prove the new config. Put that task first when compiling a
comparison because preflight task selection follows requested task order.

Do not run a model call directly. Compile with `python -m harness.run_batch plan`,
review the receipt and exact plan identity, then execute only after explicit
confirmation.
