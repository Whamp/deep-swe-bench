# Pair sweep: OM vs baseline

Source: `runs/om-memory-pilot-w10/reports/paired_manifest.json`.

## Summary

- Selected binary wins: **8** rows where `baseline.reward_binary != 1` and `om.reward_binary == 1`.
- Additional near-solves reviewed: **31** rows where `om.reward_partial >= 0.99` and the row was not already a binary win.
- Near-solves mostly improved: **25** up, **3** down, **3** flat.
- OM usually spent more exploration on near-solves: median **+27 turns** and median **+3.5k patch bytes**.

## Why OM helped

- **Cross-file invariants stayed coherent.** `eicrud-keyset-pagination-cursor` went from 0.945 to 1.0 by wiring cursor / nextCursor plumbing across auth, read service, and options. The OM patch touches `core/crud/crud.authorization.service.ts`, `core/crud/crud.service.ts`, and `core/crud/model/CrudOptions.ts` (`runs/om-memory-pilot-w10/pi-observational-memory/eicrud-keyset-pagination-cursor/rep0/artifacts/model.patch`; debug `runs/om-memory-pilot-w10/pi-observational-memory/eicrud-keyset-pagination-cursor/rep0/pi-agent/observational-memory/debug/019f00bd-c384-735a-8f04-8c7aea9e06a4.ndjson`).

- **Hook / manifest ordering got unified across the command surface.** `helm-unified-manifest-stream` went from 0.714 to 1.0 by changing `get_manifest`, `status`, and `template` together plus testdata, rather than patching one output path in isolation. OM debug shows 11 observer cycles and 8 reflections (`runs/om-memory-pilot-w10/pi-observational-memory/helm-unified-manifest-stream/rep0/artifacts/model.patch`; debug `runs/om-memory-pilot-w10/pi-observational-memory/helm-unified-manifest-stream/rep0/pi-agent/observational-memory/debug/019f00d3-b3b8-71ff-82cb-83d02d811cd4.ndjson`).

- **State propagation was finished, not just stubbed.** `textual-richlog-follow-state` went from 0.923 to 1.0 by adding follow-state gating, scroll watchers, and a resize re-render path in `src/textual/widgets/_log.py` and `src/textual/widgets/_rich_log.py`, plus a live example (`runs/om-memory-pilot-w10/pi-observational-memory/textual-richlog-follow-state/rep0/artifacts/model.patch`; debug `runs/om-memory-pilot-w10/pi-observational-memory/textual-richlog-follow-state/rep0/pi-agent/observational-memory/debug/019f0115-87d0-78a4-8ea7-20a04cf854d8.ndjson`).

- **Small API completions stayed focused.** `true-myth-iterable-collection-combinators` went from 0.9985 to 1.0 with `Symbol.iterator`, `sequence`, `traverse`, `zip`, and `zipWith`; it also cut turns from 98 to 34 (`runs/om-memory-pilot-w10/pi-observational-memory/true-myth-iterable-collection-combinators/rep0/artifacts/model.patch`; debug `runs/om-memory-pilot-w10/pi-observational-memory/true-myth-iterable-collection-combinators/rep0/pi-agent/observational-memory/debug/019f0117-6a33-7da0-8da7-99741f5cb0e8.ndjson`).

- **Other wins in the selected set:** `fd-deterministic-multi-key-sorting` (6-file CLI/config/main patch), `narwhals-rolling-window-suite` (15 files), `returns-validated-error-accumulation` (7 files), and `sql-formatter-bigquery-pipe-formatting` (7 files).

## Where OM hurt or stalled

- **A hard feature nearly landed but missed one schema edge.** `fastapi-implicit-head-options` reached 0.9972 partial, but binary stayed 0 after 221 turns / 15 reflection cycles. The trace ends in `tests/test_additional_responses_custom_model_in_callback.py::test_openapi_schema`, so OM got the HEAD/OPTIONS surface broad enough but left one callback/OpenAPI assertion mismatched (`runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/artifacts/model.patch`; trace `runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/pi.jsonl`).

- **A codegen fix got almost all the way there.** `mashumaro-flattened-dataclass-fields` climbed from 0 to 0.9997 partial with a 4-file codegen/test patch, but the binary stayed 0. The run spent 15 reflection cycles and still missed one last edge in flattened-field handling (`runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch`; trace `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/pi.jsonl`).

- **OM rescued a dead baseline, but not the final verifier.** `anko-default-function-arguments` went from a 0-byte baseline patch to a 105k-byte parser / AST / VM rewrite and 0.9917 partial, so memory clearly got the run unstuck, but the exact completion never landed (`runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/artifacts/model.patch`; trace `runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/pi.jsonl`).

- **One near-win regressed.** `tomlkit-toml-table-converters` dropped from 0.9971 to 0.9932. The trace shows two concrete misses: `TestToStandardTable::test_nested_path` and `TestToSuperTable::test_returns_doc`, so the nested-path / super-table rewrite stayed incomplete (`runs/om-memory-pilot-w10/pi-observational-memory/tomlkit-toml-table-converters/rep0/artifacts/model.patch`; trace `runs/om-memory-pilot-w10/pi-observational-memory/tomlkit-toml-table-converters/rep0/pi.jsonl`).

## Takeaway

OM helps most when one remembered constraint has to stay consistent across several files or revisits: cursor plumbing, manifest ordering, widget follow-state, iterator/combinator API completion. It hurts when the extra reflection budget widens search or test generation but leaves one exact verifier edge unclosed.