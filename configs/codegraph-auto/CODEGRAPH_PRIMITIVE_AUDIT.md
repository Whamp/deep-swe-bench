# codegraph primitive audit — why `brief` is the wrong injection

Status: evidence note. Written after running every blast-radius-relevant
codegraph command against a live graph (codegraph 3.15.0, native engine) on
`pi-observational-memory` (932 nodes, 2049 edges, 53 TS files, 0 cycles, graph
quality 89/100, caller coverage 77.1%). The goal is to upgrade
`extensions/codegraph-auto/index.ts` off its current `codegraph brief`
primitive.

## TL;DR

- `brief` (what this extension injects today) returns a **flat per-file symbol
  list with caller _counts_ and a risk tier**. It does not return _which_
  callers, the call chain, or the transitive blast radius. It is the shallowest
  of codegraph's relationship primitives.
- `fn-impact <symbol>` returns the **transitive caller tree by level**
  (`{"1":[…],"2":[…]}`, with `--depth` and `-T`), as clean JSON. This is the
  primitive actually built for "what breaks if I change this."
- `batch fn-impact <targets…>` runs the above over many symbols in **one
  process**, always JSON. This is the real implementation seam for a hook that
  wants to inject blast radius without spawning N subprocesses or relying on
  the agent to call a tool.
- `diff-impact` — the one command purpose-built for "blast radius of the
  in-flight change" — **appears broken in 3.15.0** for uncommitted/staged
  edits. Reproduced below. Do not build on it until fixed; fall back to
  `git diff` → changed files → `batch fn-impact`.
- codegraph is **repo-scoped**. External types (`node_modules`, peer-dep
  interfaces like `ExtensionAPI`) resolve to nothing. Cross-package / shared-
  type blast radius is structurally invisible. State this as a ceiling, don't
  paper over it.

## What each command actually returns (grounded)

Run on `pi-observational-memory`. Lines/counts quoted from real output.

### `brief <file>` — current injection primitive

```
src/hooks/consolidation-trigger.ts [HIGH RISK]
  Symbols: … sourceEntriesAfter [utility, 5 callers], appendEntry [core, 7 callers],
           mergeReflections [core, 5 callers], anyStageDue [utility, 6 callers],
           makeModelResolver [utility, 6 callers], runConsolidationPipeline [utility, 6 callers] …
  Imports: src/agents/dropper/agent.ts, …
  Imported by: tests/consolidation-trigger.test.ts, src/index.ts
```

Shape: per file → list of symbols, each with `[role, N callers]`, plus the
file's imports / imported-by. **No caller names. No chain. No transitive
depth.** "7 callers" tells the model a symbol is load-bearing; it does not tell
the model _which 7_ or what they do. For a blast-radius task that is the part
that matters.

Risk tier (`[HIGH RISK]`) is a useful 1-bit signal; the symbol list is not.

### `fn-impact <symbol>` — the sharp primitive

```
Function impact: f resolveStageModel -- src/config.ts:169
  -- Level 1 (2 functions):
      ^ f makeModelResolver  src/hooks/consolidation-trigger.ts:84
      ^ # tests/config.test.ts  tests/config.test.ts:0
  ---- Level 2 (1 functions):
        ^ f runConsolidationPipeline  src/hooks/consolidation-trigger.ts:164
  ------ Level 3 (1 functions):
          ^ f maybeLaunchConsolidation  src/hooks/consolidation-trigger.ts:135
  …
  Total: 6 functions transitively depend on resolveStageModel
```

JSON (`-j`) is clean and parseable:

```json
{
  "name": "resolveStageModel",
  "results": [{
    "name": "resolveStageModel", "kind": "function",
    "file": "src/config.ts", "line": 169, "endLine": 171, "role": "utility",
    "levels": {
      "1": [{"name":"makeModelResolver","kind":"function","file":"src/hooks/consolidation-trigger.ts","line":84},
            {"name":"tests/config.test.ts","kind":"file","file":"tests/config.test.ts","line":0}],
      "2": [{"name":"runConsolidationPipeline", …}],
      "3": [{"name":"maybeLaunchConsolidation", …}]
    }
  }]
}
```

Supports `--depth <n>` (default 3) and `-T`/`--no-tests`. This is the right
unit for "the executor just changed symbol X; here is what is downstream of
it." File-grain equivalent: `impact <file>` (transitive file dependents by
level).

### `batch fn-impact <targets…>` — the implementation seam

```
codegraph batch fn-impact resolveStageModel foldLedger -j
→ { "command":"fn-impact", "total":2, "succeeded":2, … "results":[ …per-target fn-impact JSON… ] }
```

One process, many targets, always JSON. Also takes `--from-file <path>` /
`--stdin` (JSON array or newline-delimited) and `--depth`. Valid batch
subcommands: `fn-impact, context, explain, where, query, impact, deps,
exports, flow, dataflow, complexity`.

**This is how a hook should inject blast radius**: collect the symbols touched
in the chunk/diff, call `batch fn-impact` once, render a digest. No per-file
subprocess, no reliance on the agent choosing to query.

### `explain` / `audit <target>` — composite report

Per-function: health (cognitive/cyclomatic/nesting/MI/Halstead/LOC), impact
(transitive dependents by level), direct callers, related tests. Rich; ideal
for a reflector-style "how risky is this change" judgment, overkill for a
per-file injection.

### `context <name>`

Source + children + complexity + direct deps + direct callers + related tests.
Good "everything about this one symbol" report.

### `dataflow <name> --impact`

Data-dependency consumers (return-value users), a _different_ edge type from
calls. Sparse in practice: this repo got only 25 inter-procedural dataflow
edges total, and `appendEntry --impact` returned "0 data-dependent consumers."
Useful when present; don't depend on it.

### `roles` — cheap blast-tier signal

Classifies every node: `dead-leaf, core, utility, entry, leaf, test-only,
dead-unresolved, …`. On this repo: `dead-leaf: 429, core: 176, utility: 71,
dead-unresolved: 63, entry: 58`. This is a one-shot, whole-graph signal that a
symbol is a hub (`core`) or has no callers (`dead-leaf`) — a cheaper blast
tier than walking `fn-impact` for every symbol.

### `interfaces <type>` / `implementations <iface>` — and their ceiling

Only resolve **local** types. `interfaces Runtime` worked (local class);
`implementations ExtensionAPI` → "No symbol matching" because `ExtensionAPI`
comes from a peer-dependency package (`node_modules`), which codegraph does
not index. See the ceiling section.

### Other relevant commands (verified present, not deeply exercised)

`where`, `children`, `deps`, `exports`, `query`, `path <from> <to>`,
`flow`, `cfg`, `sequence`, `triage`, `complexity`, `cycles`, `structure`,
`communities`, `co-change`, `owners`, `branch-compare`, `map`, `stats`,
`embed`/`search` (semantic; requires `codegraph embed .`, not built here),
`export -f mermaid|json|graphml|neo4j`, `snapshot`, `watch`, `mcp`.

## BUG: `diff-impact` does not detect uncommitted/staged changes in 3.15.0

`diff-impact` is documented as "Show impact of git changes (unstaged, staged,
or vs a ref)" — i.e. exactly the "blast radius of the in-flight executor edit"
signal a hook wants at consolidation time. It does not work on this version.

Reproduction (on `pi-observational-memory`, graph freshly built):

1. Make a real, `git diff`-visible edit _inside_ a function body:

   ```python
   # inserted "const _probe = 42;" on the line after the signature of
   # resolveStageModel (src/config.ts:169)
   ```
   `git diff --stat` confirms: `1 file changed, 1 insertion(+)`.

2. `codegraph diff-impact`           → `No changes detected.`
3. `codegraph diff-impact HEAD`      → `No changes detected.`
4. `git add` then `codegraph diff-impact --staged` → `No changes detected.`
5. `codegraph -v diff-impact` (verbose) → still `No changes detected.`, **no
   debug output at all**.

A trailing-EOF comment also yields nothing, but that is expected (outside any
symbol region). The in-body edit is the real case and it is invisible to
`diff-impact`. `diff-impact master` against a clean tree also returns "No
changes detected," which is correct but does not exercise the bug.

**Implication for this extension:** do not build the consolidation-time blast
signal on `diff-impact`. Fall back to `git diff --name-only` → changed files →
map file→symbols → `batch fn-impact`. Worth filing upstream; do not silently
work around it without a note.

## CEILING: codegraph is repo-scoped (cross-package blast radius is invisible)

- The graph is built from the repo's own sources. Peer-dependency and
  `node_modules` types are **not** indexed.
- `implementations ExtensionAPI` → "No symbol matching" (ExtensionAPI is a
  peer-dep interface).
- 63 nodes classified `dead-unresolved` here — the bulk of these are external
  symbols the graph can see being used but cannot resolve.
- Stale graph: `build` runs once at `session_start` on the base commit. Symbols
  the executor _adds_ during the session are not in the graph until a rebuild.
  The blast radius you care about (pre-existing callers you might break) is
  mostly intact; brand-new symbols are blind.

This matters for the eval failure mode this extension is trying to fix. The
DeepSWE OM analysis (`analysis/om-reflector-dropper-workflow/SYNTHESIS.md` and
the regression pattern in
`docs/deepswe-eval-implications-for-observational-memory.md`) names the
recurring loss shape as **"missed boring integration seam failures (export/
compat path, CLI registration, overlay schema/test seam, shared type/error
path)."** Shared-type / cross-package seams are exactly what codegraph cannot
see. So codegraph injection should help with _internal_ caller-chain breaks
but will not catch the cross-dependency seam failures. State this as a known
ceiling; do not let the smoke contract or any writeup imply otherwise.

## Recommendation for the rewrite of `extensions/codegraph-auto/index.ts`

Ordered by expected value; each is a small diff on the current extension.

1. **Switch the per-file injection from `brief` to a `fn-impact`-derived
   digest.** For each symbol in the file, inject the level-1 caller names (not
   just the count), capped to N symbols and M chars. `brief`'s risk tier can
   stay as the header. This is the single highest-value change: it turns "7
   callers" into "called by makeModelResolver, runConsolidationPipeline, …".
2. **Use `batch fn-impact` (one process) instead of one `brief` per file.**
   The current extension already caches per file; batch lets it resolve the
   whole touched-file set in one call and keeps the cache for rendering.
3. **Add a consolidation-time / `tool_result`-on-edit path that computes
   blast radius of the _change_, not the file.** Intended primitive:
   `diff-impact`; **currently broken** (see BUG). Use `git diff --name-only` →
   `batch fn-impact` until `diff-impact` is fixed upstream. Gate behind the
   same `built` flag and trace counter the extension already has.
4. **Tag each injected symbol with its `role`** (`core`/`utility`/`dead-leaf`).
   `roles` is a one-shot whole-graph signal and gives a cheap "is this a hub"
   bit that `brief` already half-encodes in the risk tier but does not expose
   per-symbol in a machine-readable way.
5. **Document the externality ceiling in `README.md` and `orchestration.md`.**
   The extension cannot see cross-package / shared-type blast radius. Say so
   explicitly so eval readers don't attribute seam-failure regressions to a
   tool that was structurally blind to them.
6. **Do not add a second agent-facing tool.** The whole premise of this
   "hard" config (vs the `codegraph-skill` "soft" control) is that a cheap
   executor will not call a tool on its own. Keep injection deterministic and
   in the hook.

## What was NOT exercised here (do not assume)

- Semantic `search` / `embed` (requires `codegraph embed .`; not built in this
  repo). If blast-radius-by-meaning turns out to matter, this is the upgrade
  path, but it is a heavier build.
- `flow`, `cfg`, `sequence`, `co-change`, `owners`, `branch-compare`,
  `communities`, `plot`, `export` — verified present, not run. None are
  obviously blast-radius primitives; revisit only if a specific need appears.
- Behaviour on the eval's non-TS languages (go/py/rs). The current extension's
  `ALLOWED_EXTS` already covers them; `fn-impact`/`batch` should work
  language-agnostically but this was only validated on TypeScript.
