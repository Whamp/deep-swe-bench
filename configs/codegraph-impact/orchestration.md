You have access to codegraph: a local tool that builds a symbol-and-relationship
map of this repository (who calls what).

For this config, caller context is **attached automatically**: every source file
you `read` or `edit` comes back with a `[codegraph: non-test callers]` block
listing, for each symbol in the file, the **names** of the functions that call
it (test callers excluded), e.g.

    NewLinter [core] ← Command.runLinter
    ParseConfig [core] ← Command.runLinter, loadRepoConfig

Those are the call sites that break if you change the symbol. Before editing a
symbol, glance at its callers — if a caller is in a code path you don't
understand, check it.

You also have a `codegraph` skill for the deeper queries (`where`, `fn-impact`,
`context`) when you need transitive callers, callees, or type dependencies the
auto-attached block doesn't show. Otherwise work normally as a competent
engineer — do not change your approach just because the map is present.

Note: codegraph only indexes this repo's own sources. Cross-package, shared-type,
or `node_modules` callers are not visible — a real limitation, not a bug.
