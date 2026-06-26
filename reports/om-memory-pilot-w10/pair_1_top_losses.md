# Pair 1 top losses — OM vs baseline

OM lost in two ways:
- **Narrower patches** that skipped a required integration seam or generated artifact.
- **Broader patches** that spread into extra plumbing/tests/examples without fixing the core contract.

Across these 18 losses, OM was narrower in 9, broader in 8, and the same breadth in 3. `verifier_exit` is 0 for every non-empty patch; the only explicit non-success is `opa-rego-rule-profiling` returning `skipped_empty_patch`.

OM memory did run, but it mostly increased iteration count rather than selecting the right seam: `adaptix-name-mapping-aliases` has 8 `observer.start` / 9 `reflector.result` events in `.../debug/019f0069-102d-74db-959d-08f99d47d4ad.ndjson`, while `opa-rego-rule-profiling` only reaches 2 `observer.start` before the empty patch.

| task | Δpartial | why OM hurt | evidence |
|---|---:|---|---|
| adaptix-name-mapping-aliases | -0.999 | Narrower; alias/schema wiring stayed out of the diff. OM skipped `loader_provider.py`, `overlay_schema.py`, and the baseline tests. | `src/adaptix/_internal/morphing/model/loader_provider.py`, `src/adaptix/_internal/provider/overlay_schema.py` |
| cattrs-partial-structuring-recovery | -0.816 | Broader but miswired; OM moved logic into `src/cattrs/partial.py` yet dropped the `src/cattr/converters.py` compat/export path. | `src/cattr/converters.py`, `src/cattrs/partial.py`, `tests/test_partial_structure.py` |
| opa-rego-rule-profiling | -0.581 | No-op; OM returned an empty patch. | `runs/om-memory-pilot-w10/pi-observational-memory/opa-rego-rule-profiling/rep0/artifacts/model.patch` |
| etree-xml-diff-patch | -0.537 | Same surface (`diff.go`, `etree.go`, `diff_test.go`), but hidden cases still failed; this reads like a logic bug, not breadth loss. | `diff.go`, `etree.go`, `diff_test.go` |
| igel-persist-feature-schema | -0.500 | Narrower; baseline persisted generated artifacts, OM instead edited `.gitignore`, configs/constants, and code. | `model_results/description.json`, `model_results/model.joblib`, `model_results/feature_schema.joblib` |
| task-task-graph-export | -0.297 | Narrower; baseline also changed `errors/errors_task.go`, OM did not. | `errors/errors_task.go`, `cmd/task/task.go`, `executor.go`, `graph.go`, `internal/flags/flags.go` |
| dasel-html-document-format | -0.294 | Broader, but aimed at HTML internals/go.mod instead of the CLI entrypoint the baseline touched. | `cmd/dasel/main.go`, `parsing/html/reader.go`, `parsing/html/writer.go`, `go.mod` |
| abs-stepped-slices | -0.250 | Same surface, but OM swapped broader eval coverage for a new narrow test file and still missed parser/evaluator edges. | `evaluator/evaluator_test.go`, `evaluator/stepped_slice_test.go`, `parser/parser_test.go` |
| go-git-worktree-merge-conflicts | -0.211 | Narrower; baseline also changed `worktree.go` and `worktree_merge_test.go`, OM skipped both. | `worktree_commit.go`, `worktree_merge.go`, `worktree_status.go` |
| kcp-go-multiplexed-kcp-streams | -0.190 | Same surface (`mux.go`, `mux_test.go`, `snmp.go`); extra search/test churn did not recover the hidden edge case. | `mux.go`, `mux_test.go`, `snmp.go` |
| onedump-dump-encryption-pipeline | -0.170 | Same 12-file surface; more tests didn’t close the encryption/header gap. | `encryption/encryption.go`, `fileutil/fileutil_test.go`, `handler/jobhandler_test.go`, `storage/*` |
| optique-conditional-option-dependencies | -0.150 | Broader; baseline’s one-file fix was enough, OM expanded into dependency plumbing. | `packages/core/src/conditional-dependency.ts`, `constructs.ts`, `primitives.ts`, `usage.ts` |
| ink-grid-box-layout | -0.135 | Broader; OM added `src/dom.ts` plumbing on top of the layout fix. | `src/dom.ts`, `src/grid-layout.ts`, `src/render-to-string.ts`, `test/grid.tsx` |
| bandit-interprocedural-taint-checks | -0.111 | Broader; OM spread into five example files + functional tests instead of staying on the core taint path. | `bandit/core/issue.py`, `bandit/plugins/injection_taint.py`, `tests/functional/test_functional.py` |
| happy-dom-deterministic-intersectionobserver | -0.087 | Narrower; baseline also changed `packages/happy-dom/src/PropertySymbol.ts`, OM dropped that shared symbol wiring. | `packages/happy-dom/src/intersection-observer/IntersectionObserver.ts`, `packages/happy-dom/src/PropertySymbol.ts` |
| termenv-preserve-ansi-resets | -0.066 | Broader, but shifted into token/truncate internals instead of the reset path baseline fixed. | `ansi/ansi.go`, `ansi/token.go`, `ansi/truncate.go`, `termenv.go` |
| ytt-jsonpath-query-api | -0.058 | Broader; OM split into `jsonpath_impl.go` but still lost hidden JSONPath edge cases. | `pkg/orderedmap/jsonpath.go`, `pkg/orderedmap/jsonpath_impl.go`, `pkg/yttlibrary/jsonpath.go` |
| quill-shared-toolbar-focus | -0.057 | Broader; OM added `core/quill.ts` and `ui/picker.ts`, but browser validation hit `xvfb-run: xauth command not found` in-trace. | `packages/quill/src/core/quill.ts`, `packages/quill/src/ui/picker.ts`, `packages/quill/test/unit/modules/toolbarShared.spec.ts` |

Net: OM’s memory loop didn’t fail uniformly; it alternated between **missing the seam** and **over-scoping the fix**. The worst regressions are usually one of: skipped integration files, missing generated artifacts, or extra test/example churn that never reached the hidden contract.
