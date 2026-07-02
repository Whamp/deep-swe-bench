# codegraph-auto

The **hard** codegraph config: a pi extension auto-builds the codegraph symbol
graph at session start and attaches a per-file symbol/caller map to every
`read`/`edit`/`write` result, so relationship (blast-radius) context is forced
into view instead of left for the model to request.

## Roles

- Main executor: `openai-codex/gpt-5.5`, thinking `low`.
- No secondary LLM roles. codegraph is a local tree-sitter tool, not a model.

## Files

- `orchestration.md` — system-prompt addition.
- `extensions/codegraph-auto/index.ts` — `session_start` build + `tool_result`
  injection (cached, one `codegraph brief` per file). Writes a trace to
  `/out/codegraph-trace.jsonl` (lands in the result cell).
- `skills/codegraph/SKILL.md` — deeper queries (`where`/`fn-impact`/`context`)
  the model can run on top of the auto-attached brief.
- `smoke.json` — requires `build_ok` + `inject` trace events and the injected
  block in the session. Fails the gate if the hook silently broke.
- `gpt-5.5/low/` — path-only leaf (built-in provider).

## Prerequisite: vendor the binary

The vendored codegraph binary is gitignored. Populate it before any run:

```sh
scripts/vendor_codegraph.sh
```

It prunes `@optave/codegraph` (5 grammars: ts/go/python/rust/js + linux-x64
native core) into `configs/codegraph-auto/bin/` (~124M) and hardlinks it into
all codegraph config `bin/` dirs. The smoke gate will fail loudly if `bin/` is
missing.

## Contrast

Paired with `codegraph-skill` (skill + orchestration only, no auto-attach) to
isolate whether **forced injection** beats **taught availability** for cheap-model
attention to caller relationships.
