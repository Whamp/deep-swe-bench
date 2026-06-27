# 0002 — Retire pi.jsonl (stream capture); read usage from the native session

## Context

`run.py` captured pi's `--mode json` stream to a per-cell `pi.jsonl` so
`parse_usage` could recover token/cost/turn stats. `--mode json` is a *streaming*
protocol: it emits a `message_update` event for every token-chunk, each re-carrying
the growing partial message. The final usage lives in `message_end`/`turn_end`,
which `parse_usage` reads; the 99% of the file that is streaming intermediates is
read by nothing. One cell reached 2.5GB; the repo grew to 235GB, 233GB of it
`pi.jsonl` — all for ~12 bytes of usage per cell.

pi already writes a compact native session (`--session-dir`) into every cell:
final-state `message` records, ~84KB median, each carrying the final
`message.usage`. That is the same session file pi writes globally.

## Decision

Stop capturing `--mode json` to disk. Read usage from the native `session/*.jsonl`
that pi already writes. `parse_usage` is **rewritten** to parse `message.usage`
from `type:"message"` records instead of streaming `*_end` events — this is a
logic change, not a path change. Pointing the current `parse_stream` at a
session file returns all-zeros (verified: it keys on `turn_end`/`message_end`/
`tool_execution_end`, none of which appear in the native session, which uses
`type:"message"`). The rewrite also removes the `except Exception: raw=""`
silent-zero fallback so a missing or unreadable source fails loud instead of
corrupting `cost_usd`/`total_tokens` to zero.

## Considered options

- **Pipe the stream into `parse_usage` live, never touch disk.** Rejected: adds
  stdout/backpressure complexity; the native session already has the data with no
  plumbing.
- **Filter the stream to `*_end` events only.** Rejected: still redundant with
  the native session for everything except out-of-band extension calls.

## Consequences

- Per-cell disk goes from ~421MB to ~0.6MB. A full comparison drops from tens of
  GB to ~MB.
- **Out-of-band extension calls are not in the native session.** Per-config
  exceptions, documented in `AGENTS.md` "Usage capture":
  - **advisor**: usage is only in the stream's `tool_execution_end` events;
    capture only those (tiny) for advisor cells. Post-migration the parser reads
    this filtered `tool-usage.jsonl` as a *second* source alongside the session.
  - **observational-memory**: worker usage is recorded nowhere (session, stream,
    or extension debug file). The OM debug `.ndjson`'s `tokens` field is context
    coverage, not API usage. Worker token cost is a known, unmeasured gap for
    existing OM runs and is not being re-collected.
- Historical 233GB of `pi.jsonl` is discarded on migration (not moved into the
  new tree); old `runs/` is purged manually once the migration is verified.
- This is the motivation behind the AGENTS.md "verify usage capture when setting
  up a new config" rule: any future config that makes its own LLM calls must be
  checked, case by case, before a full run.
