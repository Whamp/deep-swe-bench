# OM regression failure modes

Scope: the 18 largest losses from `runs/om-memory-pilot-w10/reports/pair_1_top_losses.md`, checked against the task artifacts under `runs/om-memory-pilot-w10/pi-observational-memory/*/rep0/`.

| bucket | n | share | representative tasks | read on why |
|---|---:|---:|---|---|
| API / extension errors | 3 | 16.7% | `adaptix-name-mapping-aliases`, `cattrs-partial-structuring-recovery`, `igel-persist-feature-schema` | Public seam broke: adaptix hit `NameError: VarTuple` in `src/adaptix/_internal/morphing/model/loader_gen.py`; cattrs added `BaseConverter.partial_structure` but hidden tests still needed `cattrs.partial_structure`; igel broke the `Igel.results_path` contract in hidden tests. |
| Missed integration | 3 | 16.7% | `task-task-graph-export`, `go-git-worktree-merge-conflicts`, `happy-dom-deterministic-intersectionobserver` | Baseline also touched companion files / shared symbols (`errors/errors_task.go`, `worktree.go` + `worktree_merge_test.go`, `packages/happy-dom/src/PropertySymbol.ts`) that OM skipped. |
| Memory distraction / over-expansion | 6 | 33.3% | `dasel-html-document-format`, `optique-conditional-option-dependencies`, `ink-grid-box-layout`, `bandit-interprocedural-taint-checks`, `termenv-preserve-ansi-resets`, `ytt-jsonpath-query-api` | Patch scope widened into extra plumbing/tests/examples (`go.mod`, `src/dom.ts`, examples, token/truncate internals, `jsonpath_impl.go`) instead of staying on the seam that mattered. |
| Normal model variance | 4 | 22.2% | `etree-xml-diff-patch`, `abs-stepped-slices`, `kcp-go-multiplexed-kcp-streams`, `onedump-dump-encryption-pipeline` | Same surface, but hidden edge cases still failed; `etree` is the clearest pure logic miss (`ApplyPatch` panicked in `etree.go:830` via `diff.go:1096`). |
| Too much context / stalled exploration | 1 | 5.6% | `opa-rego-rule-profiling` | `patch_bytes=0`, `verifier_exit=skipped_empty_patch`; the session spent context on build-tag / profiling-hook exploration and never emitted a patch. |
| Tooling / env (not OM reasoning) | 1 | 5.6% | `quill-shared-toolbar-focus` | Browser validation hit `xvfb-run: xauth command not found` in-trace, so I would not count this as a model failure. |

## Named-task spot checks

- `adaptix-name-mapping-aliases`: `runs/om-memory-pilot-w10/pi-observational-memory/adaptix-name-mapping-aliases/rep0/logs/verifier.stdout.txt` fails with `NameError: name 'VarTuple' is not defined`; the patch spans `src/adaptix/_internal/morphing/facade/provider.py`, `src/adaptix/_internal/morphing/model/crown_definitions.py`, and `src/adaptix/_internal/morphing/model/loader_gen.py`.
- `cattrs-partial-structuring-recovery`: `runs/om-memory-pilot-w10/pi-observational-memory/cattrs-partial-structuring-recovery/rep0/logs/verifier.stdout.txt` fails on `AttributeError: module 'cattrs' has no attribute 'partial_structure'`; the patch added `src/cattrs/partial.py` and `BaseConverter.partial_structure` in `src/cattrs/converters.py`, but missed the top-level API.
- `igel-persist-feature-schema`: `runs/om-memory-pilot-w10/pi-observational-memory/igel-persist-feature-schema/rep0/logs/verifier.stdout.txt` fails on `AttributeError: <class 'igel.igel.Igel'> has no attribute 'results_path'`; the patch changed `igel/igel.py`, `igel/configs.py`, `igel/constants.py`, and added `igel/feature_schema.py`.
- `opa-rego-rule-profiling`: `runs/om-memory-pilot-w10/pi-observational-memory/opa-rego-rule-profiling/rep0/result.json` has `patch_bytes: 0` and `verifier_exit: "skipped_empty_patch"`.
- `etree-xml-diff-patch`: `runs/om-memory-pilot-w10/pi-observational-memory/etree-xml-diff-patch/rep0/logs/verifier.stdout.txt` shows a nil deref in `Element.InsertChildAt` (`etree.go:830`) called from `ApplyPatch` (`diff.go:1096`).

Bottom line: 12/18 losses are wiring/breadth issues (API + integration + over-expansion), 4/18 are pure hidden-edge logic misses, 1/18 is a stall/empty patch, and 1/18 is tooling/env.
