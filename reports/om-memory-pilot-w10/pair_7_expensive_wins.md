# Pair 7 expensive wins

Filtered from `runs/om-memory-pilot-w10/reports/paired_manifest.json` to the top 7 positive-partial rows by token delta.

Evidence paths use the paired layout:
- baseline: `runs/ponytail-full-pilot-w2/baseline/<task>/rep0/{result.json,artifacts/model.patch,pi.jsonl}`
- OM: `runs/om-memory-pilot-w10/pi-observational-memory/<task>/rep0/{result.json,artifacts/model.patch,pi.jsonl,pi-agent/observational-memory/debug/*.ndjson}`

All selected OM rows ended with `verifier_exit: 0`; two baselines were already stalled (`skipped_empty_patch` on oxvg, `timeout` on kombu).

- `koota-pair-relation-tracking` — `+0.148` partial for `+35.5M` tokens / `+3207s`. OM broadened from query-only edits into entity/trait/world wiring (`entity-methods-patch.ts`, `check-query-tracking-with-relations.ts`, `world.ts`) and added `query-modifiers.test.ts`; the trace shows `145` bash calls but no test loop, so the spend was mostly exploratory/integration churn.

- `fastapi-implicit-head-options` — `+0.997` partial for `+20.6M` tokens / `+2056s`. OM rewired the shared plumbing instead of staying local: `applications.py`, `routing.py`, `openapi/utils.py`, `middleware/methods.py`, and `middleware/__init__.py`; the patch adds `ImplicitMethodTrackingMiddleware`, ordered methods, `Allow`, and implicit HEAD/OPTIONS generation. Trace: `13` pytest runs.

- `yaegi-go-embed-directives` — `+0.719` partial for `+17.6M` tokens / `+1739s`. OM expanded from interpreter-only edits into `_test/embed*.go`, `_test/testdata/*.txt`, and `interp/embed_test.go`, implementing `//go:embed` parsing, a virtual `fs.FS`, and fixture-backed tests; trace shows `22` `go test` runs.

- `koota-query-predicates` — `+0.163` partial for `+17.6M` tokens / `+1338s`. OM turned the query engine into a first-class predicate pipeline (`predicate.ts`, `evaluate-predicate.ts`, `check-query.ts`, `query-result.ts`, `world/types.ts`, `predicate.test.ts`), but the trace is still exploration-heavy (`48` bash calls, no visible test loop).

- `oxvg-structural-selector-preservation` — `+0.912` partial for `+11.45M` tokens / `+1297s`. Baseline was `skipped_empty_patch`; OM rescued the task by adding selector-implication tracking in `visitor.rs`, `collapse_groups.rs`, and `move_elems_attrs_to_group.rs` plus four snapshot files under `jobs/snapshots/`; trace shows `18` `cargo test` runs.

- `helm-unified-manifest-stream` — `+0.286` partial for `+11.36M` tokens / `+1212s`. OM moved the fix into `pkg/release/v1/util/unified_manifest.go` and then spent most of the patch budget updating `pkg/cmd/testdata/output/*.txt` goldens; trace shows `41` `go test` runs.

- `kombu-single-active-consumer-priority` — `+0.993` partial for `+10.51M` tokens / `+263s`. Baseline timed out; OM concentrated the fix in the virtual transport choke point (`kombu/transport/virtual/__init__.py`, `base.py`) to add consumer-priority/SAC bookkeeping instead of broad transport edits. Trace shows `10` pytest runs.

## Pattern

- OM helped most when the bug crossed layers or needed fixture/golden regeneration (fastapi, yaegi, oxvg, helm, kombu).
- OM hurt efficiency most on the Koota rows: lots of search/edit churn, no visible test loop, and only modest partial movement.
- The OM debug streams were active on every row (observer/reflection cycles ranged from `8/14` to `17/25`), so the memory pipeline was actually consolidating work; it seems to have mattered most when the patch could reuse remembered structure to find the shared wiring layer.
