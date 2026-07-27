# Observational-memory between-turn 1.0.0 validation

Validation note for `observational-memory-between-turn@1.0.0` on
`openai-codex/gpt-5.6-sol` at thinking `low`.

## Status

The release is a locked candidate for a confirmed atomic preflight. No model or
paid call was made while creating it. It is not working evidence until the
versioned smoke contract passes and the central seal registry records that
preflight.

## Approved intervention

The config tests compaction with observations during one DeepSWE task:

```json
{
  "observeAfterTokens": 10000,
  "reflectAfterTokens": 20000,
  "compactAfterTokens": 25000,
  "compactionTrigger": "betweenTurns",
  "observationsPoolMaxTokens": 20000,
  "observationsPoolTargetTokens": 10000
}
```

Pi retains 15,000 recent tokens. Both the executor and all observational-memory
worker stages use `openai-codex/gpt-5.6-sol` at thinking `low`. The config adds
no executor system or orchestration prompt.

The preserved 20,000-token full-fold threshold is intentionally unreachable in
normal DeepSWE cells. Reflections are excluded from the expected normal
projection and are accounted for if produced. The dropper is expected to remain
inactive. This known limitation avoids changing the memory policy merely to
force the full pipeline into a short benchmark.

Calibration evidence:

```text
analysis/observational-memory-between-turn-1.0.0-calibration.json
```

## Package path

The vendored extension is package version `3.0.3` from commit:

```text
e5d54824c44402ee12c8fcd924a146cee8f2caf1
```

That commit adds the opt-in `betweenTurns` policy. At a due tool-bearing turn it
aborts the pending next request, compacts only after Pi reports the executor
settled, proves that the new compaction entry persisted, and sends a hidden
`om.compaction.continue` message to resume the interrupted work.

A typed config-local helper forwards the existing nested worker event streams
to `extensions/om-worker-usage-trace.ts`. Its only callers are the event-drain
loops in:

- `src/agents/observer/agent.ts`
- `src/agents/reflector/agent.ts`
- `src/agents/dropper/agent.ts`

The helper does not modify prompts, tools, request options, or structured worker
outcomes. Config-level Pi hooks cannot otherwise observe these nested
`agentLoop` calls. The vendored copy also removes one trailing blank line from
`src/tokens.ts`; no executable token-estimation code changed.

## Model and API path

The executor and workers resolve to:

```text
provider: openai-codex
model: gpt-5.6-sol
api: openai-codex-responses
thinking: low
credential route: OPENAI_CODEX_OAUTH
billing: subscription quota
```

Pi `0.81.1` model metadata, explicit low-effort request shape, and a tiny live
subscription response are already recorded in:

- `docs/openai-codex-gpt56-sol-low.md`
- `analysis/openai-codex-gpt56-sol-model-registry.json`
- `analysis/openai-codex-gpt56-sol-low-request-probe.jsonl`
- `analysis/openai-codex-gpt56-sol-low-live-probe.jsonl`

Those artifacts prove the provider path directly. The nested worker boundary is
not inferred from them: preflight must additionally produce compact worker
records with provider `openai-codex`, model `gpt-5.6-sol`, API
`openai-codex-responses`, and thinking `low`.

## Durable preflight contract

The leaf-local `smoke.json` requires all of the following:

- exact executor and worker settings in `result.json`;
- positive native executor, compact worker, and observer usage;
- zero dropper calls;
- an observation record in the native session;
- a compaction entry with `fromHook: true`, `details.type: "om.folded"`, and
  `details.fullFold: false`;
- a debug authority decision with owner `memory` and reason `covered`;
- a hidden `om.compaction.continue` session entry;
- explicit low effort in captured executor provider requests;
- exact low-thinking worker usage records at the nested boundary.

These checks distinguish the intended behavior from four false positives: a
worker that merely ran, Pi fallback compaction, end-of-run compaction with no
continuation, and a full-fold/dropper policy that was not approved.

## Preflight selection

The task must cross the 25,000-token threshold naturally. Historical GPT-5.6
SOL baseline evidence recorded 41,796 estimated tokens at the last tool boundary
for `yjs-map-conflict-detection` rep 0, making it the preferred candidate. This
is not current proof. Put it first in the requested task order when compiling
the launch plan, then inspect the exact preflight cell in the receipt.

Any launch includes a secondary model role even though it shares the executor
model. Stop for explicit confirmation of the immutable plan identity before
executing it.
