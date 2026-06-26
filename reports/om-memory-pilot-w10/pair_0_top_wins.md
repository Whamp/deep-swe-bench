# pair 0 top wins

Source: `runs/om-memory-pilot-w10/reports/paired_manifest.json` plus paired `result.json`, `artifacts/model.patch`, `verifier/run.log`, and OM debug ndjson under `runs/om-memory-pilot-w10/pi-observational-memory/.../pi-agent/observational-memory/debug/`.

## What changed
- All 18 selected rows improved `reward_partial`; OM verifier_exit was `0` for every row.
- Baseline was often missing the fix entirely: 10/18 baseline rewards were `0.0`, 3/18 baseline patches were empty, and 1/18 baselines timed out (`verifier/run.log`).
- OM patches were broader: median changed files 5.5 vs 3.5 baseline, and OM touched tests/snapshots in 14/18 rows (baseline 7/18). Generated/snapshot artifacts showed up only in OM (2/18; baseline 0/18).
- Memory likely helped by preserving intermediate findings. Debug logs show 4–13 `observer.start` batches and 3–15 `reflector.agent_start` cycles; the top win (`mashumaro...`) had 10 observer batches, 15 reflection batches, and 13 `dropper.waiting_for_reflection` events (`.../pi-agent/observational-memory/debug/019f00ea-32d7-7194-929f-bc845d7b0f43.ndjson`).

## Representative mechanics
- `mashumaro-flattened-dataclass-fields`: baseline patch in `runs/ponytail-full-pilot-w2/baseline/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch` left `builder.py` syntactically broken; `runs/ponytail-full-pilot-w2/baseline/mashumaro-flattened-dataclass-fields/rep0/verifier/run.log` shows `base pytest rc=4` with an unmatched `)` at `builder.py:1495`. OM fixed the feature in `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch` and passed via `mashumaro/core/meta/code/builder.py`, `mashumaro/helper.py`, `tests/test_helper.py`, `tests/test_flatten.py`.
- `kgateway-consistent-hash-policy`: baseline had an empty patch; OM's `runs/om-memory-pilot-w10/pi-observational-memory/kgateway-consistent-hash-policy/rep0/artifacts/model.patch` added `api/v1alpha1/kgateway/traffic_policy_types.go`, `pkg/kgateway/extensions2/plugins/trafficpolicy/consistent_hash.go`, `zz_generated.deepcopy.go`, Helm CRD YAML, and tests.
- `ts-pattern-match-each`: baseline only partially implemented the feature; OM's `runs/om-memory-pilot-w10/pi-observational-memory/ts-pattern-match-each/rep0/artifacts/model.patch` normalized the file layout to `src/match-each.ts`, completed clause/tap semantics, and improved reward while using fewer turns/tool calls (58→52, 73→71).
- `pebble-durability-wait-apis`: OM's `runs/om-memory-pilot-w10/pi-observational-memory/pebble-durability-wait-apis/rep0/artifacts/model.patch` compressed search (134→108 turns, 153→130 tool calls) while filling durability/batch/event/metrics wiring.
- `helm-unified-manifest-stream`: OM's `runs/om-memory-pilot-w10/pi-observational-memory/helm-unified-manifest-stream/rep0/artifacts/model.patch` expanded to 23 files, including CLI test outputs under `pkg/cmd/testdata/output/`, and closed a 0.714286→1.0 partial gap.

## Selected rows
| # | task | Δpartial | baseline → OM reward_partial |
|---:|---|---:|---:|
| 1 | `mashumaro-flattened-dataclass-fields` | `0.999668` | `0.000000 → 0.999668` |
| 2 | `fastapi-implicit-head-options` | `0.996852` | `0.000315 → 0.997167` |
| 3 | `kombu-single-active-consumer-priority` | `0.992696` | `0.000000 → 0.992696` |
| 4 | `anko-default-function-arguments` | `0.991736` | `0.000000 → 0.991736` |
| 5 | `kgateway-consistent-hash-policy` | `0.990741` | `0.000000 → 0.990741` |
| 6 | `sqlite-utils-safe-import-checkpoints` | `0.970856` | `0.000000 → 0.970856` |
| 7 | `ts-pattern-match-each` | `0.923077` | `0.065934 → 0.989011` |
| 8 | `oxvg-structural-selector-preservation` | `0.911765` | `0.000000 → 0.911765` |
| 9 | `go-critic-doc-link-checker` | `0.894737` | `0.000000 → 0.894737` |
| 10 | `helm-array-merge-strategies` | `0.762712` | `0.000000 → 0.762712` |
| 11 | `yaegi-go-embed-directives` | `0.718750` | `0.000000 → 0.718750` |
| 12 | `pwntools-tube-multiplexing` | `0.567568` | `0.351351 → 0.918919` |
| 13 | `tengo-destructuring-bindings` | `0.461883` | `0.000000 → 0.461883` |
| 14 | `opa-template-string-reconstruction` | `0.444444` | `0.444444 → 0.888889` |
| 15 | `pebble-durability-wait-apis` | `0.359223` | `0.572816 → 0.932039` |
| 16 | `koota-composite-trait-aspects` | `0.349776` | `0.556054 → 0.905830` |
| 17 | `obsidian-linter-auto-table-of-contents` | `0.331058` | `0.633959 → 0.965017` |
| 18 | `helm-unified-manifest-stream` | `0.285714` | `0.714286 → 1.000000` |

## Open questions
- Memory vs. budget is still confounded: OM often used more turns/tokens, so the causal lift from memory alone is not isolated.
- `verifier_exit` is not perfectly comparable across rows (`skipped_empty_patch`, `timeout`, `0`).
- A few near-solved tasks improved while using fewer turns; an ablation without OM would be needed to prove the compression came from memory rather than sampling variance.
