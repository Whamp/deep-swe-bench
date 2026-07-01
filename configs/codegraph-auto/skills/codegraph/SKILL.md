---
name: codegraph
description: Local symbol-and-relationship map of the repo. Use to see who calls what (blast radius) before editing a function, class, or method. The binary is at /arm/bin/cg.
---

# codegraph

`codegraph` builds a function-level dependency graph of the whole repo
(tree-sitter) and lets you query it. In this environment the binary is at
`/arm/bin/cg` — call it by full path.

## Build once at the start

```sh
/arm/bin/cg build .
```

Creates `.codegraph/graph.db`. Takes ~1-2s for most repos. Idempotent.

## The queries that matter for safe edits

**Before changing a symbol, check its blast radius.**

| Question | Command |
|---|---|
| What symbols are in this file, and how many callers does each have? | `/arm/bin/cg brief <file>` |
| Who calls this symbol (callers / fan-in, tests excluded)? | `/arm/bin/cg where <SymbolName> -T` |
| What breaks transitively if this symbol changes? | `/arm/bin/cg fn-impact <SymbolName>` |
| Full context: source + deps + callers + tests? | `/arm/bin/cg context <SymbolName>` |
| What does this file import / what imports it? | `/arm/bin/cg deps <file>` |

`brief` is the cheap first look (one line per symbol with a caller count and a
risk tier like `[utility, 2 callers]` or `[core, 7 callers]`). `where`/`fn-impact`
give you the actual caller names when a count looks dangerous.

## Reading the risk tier

`brief` tags each symbol: `core` (heavily depended on), `utility`, `leaf`
(no callers), `dead-ffi`/`dead`. A `core` symbol with many callers is high blast
radius — changes ripple widely.

## When to use it

- Before editing a function/type/method you didn't just write: run `where` to see
  callers, or `brief` on the file for a quick scan.
- When a fix might need to touch a shared helper: run `fn-impact` first.
- You do **not** need it for files you are creating from scratch.
