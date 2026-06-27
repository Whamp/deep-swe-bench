# AGENTS.md

This is the agent-facing project memory for `deep-swe-bench`. Read it before
configuring a new config or touching the harness.

## Vocabulary

Canonical nouns and retired/avoided terms live in [`CONTEXT.md`](./CONTEXT.md).
Use them. The big ones: **config** (not arm/treatment), **comparison** (not
study/run-as-noun), **subset** (not subsample). "run" is a verb only.

## Usage capture — read the native session by default

> **Status caveat:** this section describes the *target* state implemented by
> RENAME-PLAN Phase 3 (§14) and ADR-0002. As of this writing the harness has
> NOT yet been edited: `parse_usage.parse_stream` still reads the per-cell
> `pi.jsonl` `--mode json` stream (`run.py:350`), and `run.py` still writes it
> (`run.py:286`). The native-session switch is part of the rename and lands in
> §5d of `EXECUTION-PLAN-DRAFT.md`. Treat the rules below as the spec the
> rename implements, not current behavior.

Token/cost accounting for a config is read from the agent's native
`session/*.jsonl` that pi writes into every cell (`--session-dir`). This is the
same compact, final-state file pi writes globally. **Do not** capture the
`--mode json` stream to disk — it is a streaming protocol that re-carries the
growing message on every token-chunk (one file reached 2.5GB; the repo hit
235GB from it). The native session carries main-agent usage cleanly on each
assistant `message.usage`.

### The "fancy extensions" complication

The native session is a conversation transcript. Some configs make **additional
LLM calls out-of-band** whose usage is *not* in the session file:

- **advisor** — the advisor LLM (e.g. glm-5.2) runs through the extension's own
  provider path. Its usage appears only in the `--mode json` stream's
  `tool_execution_end` events (not in any session file). For this config the
  parser captures only those events into a tiny filtered file.
- **observational-memory** — observer/reflector/dropper workers make LLM calls
  whose usage is **not currently recorded anywhere** (not session, not stream,
  not the extension debug file). Worker token cost is a known, unmeasured gap.
  Note: the OM extension's debug `.ndjson` does carry a `tokens` field on some
  events (e.g. `observer.start`), but that is **context-window coverage, not
  API usage** — it has no `inputTokens`/`outputTokens`/`cost`. Do not mistake
  it for recoverable usage data.

### When setting up a new config

Before running a real comparison, verify usage capture:

1. Default: read usage from `session/*.jsonl`. Confirm the config's usage is
   present there (it is for plain pi, skills, and prompt-only configs).
2. If the thing under test makes its own LLM calls (an extension with worker
   models, an advisor, a sub-agent), check where — if anywhere — that usage is
   emitted. Adjust the parser per config to include it.
3. Smoke-test one cell and inspect `result.json` before committing to a full
   run. A gap discovered after a full run is data you don't have and won't
   re-collect (see the OM gap).

This is per-config by design, not a harness-level invariant.

## Verification

Going forward I'll verify before claiming.
