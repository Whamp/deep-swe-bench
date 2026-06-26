# Pair sweep: medium/easy regressions

Selected from `runs/om-memory-pilot-w10/reports/paired_manifest.json` where `difficulty_bucket ∈ {medium,easy}` and `delta.partial < -0.05`, sorted by worst delta.partial.

All five rows below have `verifier_exit: 0`; these are semantic regressions, not harness failures.

| task | delta.partial | mechanical read |
|---|---:|---|
| `adaptix-name-mapping-aliases` | -0.9986 | OM collapsed to 14 shell calls and **0 test runs** (`pi.jsonl`), while baseline did 81 calls with repeated targeted pytest + a full suite sweep. OM patch also dropped the baseline’s test files (`tests/unit/morphing/facade/provider/test_aliases.py`, `tests/unit/provider/test_overlay_schema.py`), so alias support was never validated. Evidence: `runs/ponytail-full-pilot-w2/baseline/adaptix-name-mapping-aliases/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/adaptix-name-mapping-aliases/rep0/artifacts/model.patch`, `.../pi.jsonl`, `.../result.json`. |
| `cattrs-partial-structuring-recovery` | -0.8158 | OM moved the feature into a new `src/cattrs/partial.py` (655 lines) plus `tests/test_partial_structure.py`; baseline instead extended `src/cattrs/converters.py` and probed existing `gen/typeddicts.py` / `_compat.py`. OM mostly validated one new test file and import smoke checks, so edge cases stayed broken (`3/69` f2p vs `65/69` baseline). Evidence: `runs/.../cattrs-partial-structuring-recovery/rep0/artifacts/model.patch`, `runs/.../pi.jsonl`, `runs/.../result.json`. |
| `task-task-graph-export` | -0.2973 | OM explored more (56 calls, more testish commands) but missed one integration layer: baseline added `errors/errors_task.go` with `TaskGraphCycleError`/`CodeTaskfileCycle`; OM used a generic `fmt.Errorf` cycle path and the cycle smoke test (`cd /tmp && ./task --taskfile Taskfile_cycle.yml --graph a`) stack-overflowed in `computeLongestPath.func1`. Evidence: `runs/.../task-task-graph-export/rep0/artifacts/model.patch`, `runs/.../pi.jsonl`, `runs/.../result.json`. |
| `dasel-html-document-format` | -0.2945 | OM spent more time in `parsing/html` tests/builds, but skipped baseline’s `cmd/dasel/main.go` import-side registration of `parsing/html`. Local failures still showed `head: ""` vs `null` and writer render mismatches, so the feature wasn’t wired correctly at the CLI boundary. Evidence: `runs/.../dasel-html-document-format/rep0/artifacts/model.patch`, `runs/.../pi.jsonl`, `runs/.../result.json`. |
| `onedump-dump-encryption-pipeline` | -0.1705 | OM got further into the encryption package (more package-local tests) and fixed an early round-trip panic, but the trace still ends with `TestInvalidHeader` expecting an error and getting nil. Baseline also ran broader repo validation (`go test ./...`); OM stayed much narrower. Evidence: `runs/.../onedump-dump-encryption-pipeline/rep0/artifacts/model.patch`, `runs/.../pi.jsonl`, `runs/.../result.json`. |

## Common pattern

- OM usually changed the **scope** of work more than the **quality** of the final fix: either too narrow (`adaptix`, `dasel`, `onedump`) or too abstract/new-module heavy (`cattrs`).
- The recurring miss is an **adjacent integration file**: tests/overlay schema, custom error type, CLI import registration, or repo-wide validation.
- Reflection/observer artifacts were present in every run, but they mostly redirected search inside one layer; they did not force the missing cross-file smoke test.
