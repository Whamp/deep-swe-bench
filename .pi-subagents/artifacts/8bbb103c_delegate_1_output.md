All green: 15/15 tests pass, the module imports both ways (script-style `import results_address` as run.py uses it, and `import harness.results_address` as tests use it), and nothing is staged.

## Summary of the design (pole: **maximize flexibility**)

Full version in `docs/design/results-address-flex/design.md`; runnable interface in `harness/results_address.py`; tests in `tests/test_results_address.py`.

**1. Interface** — Two frozen dataclasses, `Tree(leaf, thinking, root)` and `Cell(tree, config, task, rep)`. No `agent` field (orthogonal to address). Split surface:
- *Canonical (invariant-protected):* `Tree.of(model, thinking)` (the single leaf derivation, executor-only), `Tree.results_jsonl`, `Cell.result`, `Cell.transient_error`, `Cell.log_file` (the flat `{task}__{config}__rep{rep}.log`), `Cell.subdir(name)` + `CANONICAL_SUBDIRS`.
- *Open composition:* `Tree.join/.glob/.cells/.has_any_results/.has_result`, `Cell.join/.glob/.subdir`.

Invariants: (1) `Cell.result` is the *same* Path the writer creates and the reader existence-checks; (2) `Tree.of` replaces the **three** existing leaf derivations (`lib.model_leaf`, `run_batch.model_leaf_of`, analyze.py's inline split) with one; (3) executor-only — `of()` never accepts an advisor model. Ordering: `cells()` yields `(config, task, rep)` sorted, skipping `_`-reserved and file siblings. Errors: `_join_safe` raises `ValueError` on absolute/empty/`..` segments (incl. inside `"a/../../x"`).

**2. Usage** — doc shows a single-cell writer (mkdir + canonical subdirs + `cell.result.write_text` + append `tree.results_jsonl`, open artifacts via `cell.join("tool-usage.jsonl")`) and a cross-cell reader (`for cell in tree.cells()` / `tree.has_result(...)` / `tree.glob("*/*/rep*/result.json")`). Plus the constraint demo: a caller adds `cell.join("flamegraph.json")`, `cell.subdir("provenance")`, `tree.join("comparisons","c1","manifest.json")` — and reads them back via the same `glob` — **with no module edit**.

**3. Seam** — hides the leaf derivation + executor-only rule, the `result.json`/flat-log strings (ADR-0001's incident), the grammar depth + reserved-name + sorting rules, path containment, and the repo-root convention. Deliberately does *not* hide writing.

**4. Dependencies** — Cat 1 (pure derivation) + Cat 2 (existence/iteration, FS in prod, `tmp_path` in tests). **No ports**: the Cat-1↔2 seam is one realistic backend; the "adapter" is the `root=` parameter, not an injected interface. A `PathBackend` port = single adapter = hypothetical seam → rejected (deletion test: delete it, pass `root=`, nothing breaks).

**5. Trade-offs** — `join`/`of`/`result` pass the deletion test (complexity re-scatters across N callers / invariants re-open if removed). Per-artifact sugar (`cell.patch()`) and an artifact *registry* **fail** the deletion test (pure pass-through / adds indirection, no leverage) → rejected, which is exactly the pole. Honest costs: non-canonical names aren't typo-checked; `.dir` is exposed for writes so canonical-drift can't be forbidden, only discouraged; canonical path is the obvious/safe one.

I deliberately did **not** wire the module into `run.py`/`run_omp.py`/`run_batch.py`/`analyze.py` — that refactor is the integration step the parent picks after comparing the four designs, and doing it now would widen scope.