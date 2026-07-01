You have access to codegraph: a local tool that builds a symbol-and-relationship
map of this repository (who calls what, what depends on what).

For this config, codegraph context is **attached automatically**: every source
file you `read` or `edit` comes back with a `[codegraph: symbol & caller map]`
block listing that file's symbols, each with its caller count and risk tier, e.g.

    Command.runLinter [utility, 2 callers]

That count is the blast radius of that symbol — how many other places break if
you change it. Treat a high caller count or a HIGH RISK tier as a signal to
check those callers before editing.

You also have a `codegraph` skill describing the deeper queries (`where`,
`context`, `fn-impact`). When you need the actual **names** of the callers of a
specific symbol you are about to change, run them directly. Otherwise work
normally as a competent engineer — do not change your approach just because the
map is present.


Observational memory is enabled for this run (observer = gpt-5.4-mini, thinking low). Work normally as a competent engineer; do not change your behavior just because memory is present.
