# Pair 4 hard bucket wins

Selected hard rows with `delta.partial > 0.05`, sorted by delta.

| task | partial (baseline → OM) | turns (baseline → OM) | mechanical read |
|---|---:|---:|---|
| `mashumaro-flattened-dataclass-fields` | `0.000 → 0.9997` | `41 → 110` | OM kept the flatten/collision hypothesis alive long enough to add a dedicated flatten test file and stricter code paths. |
| `fastapi-implicit-head-options` | `0.0003 → 0.9972` | `25 → 221` | OM widened from route-only probing to app/router/OpenAPI wiring and validated the actual OPTIONS payload. |
| `kombu-single-active-consumer-priority` | `0.000 → 0.9927` | `57 → 126` | OM finished the cross-transport consumer model and the missing export path. |
| `anko-default-function-arguments` | `0.000 → 0.9917` | `71 → 110` | OM rescued an empty baseline by carrying parser defaults through parser/VM/tests. |

## Notes

- `mashumaro-flattened-dataclass-fields`
  - Baseline patch was only `3` files (`builder.py`, `helper.py`, `tests/test_helper.py`); OM expanded to `4` files and added `tests/test_flatten.py`.
  - Evidence: `runs/ponytail-full-pilot-w2/baseline/mashumaro-flattened-dataclass-fields/rep0/result.json`, `runs/ponytail-full-pilot-w2/baseline/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/result.json`, `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/pi.jsonl`, `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/pi-agent/observational-memory/debug/019f00ea-32d7-7194-929f-bc845d7b0f43.ndjson`.
  - OM validation in trace: `python -m pytest tests/test_flatten.py -v` then a broader suite including `tests/test_code_generation_options.py`.

- `fastapi-implicit-head-options`
  - Baseline stayed mostly in `fastapi/routing.py`/`fastapi/middleware/methods.py`; OM added `fastapi/applications.py` and `fastapi/openapi/utils.py` too.
  - OM trace shows a real behavior check: `TestClient().options("/users/123")` returned `200`, JSON with `path`, `methods`, `operations`, and `Allow: GET`.
  - Evidence: `runs/ponytail-full-pilot-w2/baseline/fastapi-implicit-head-options/rep0/result.json`, `runs/ponytail-full-pilot-w2/baseline/fastapi-implicit-head-options/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/result.json`, `runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/pi.jsonl`, `runs/om-memory-pilot-w10/pi-observational-memory/fastapi-implicit-head-options/rep0/pi-agent/observational-memory/debug/019f00c9-16ad-7272-8366-3df3ad36ebc2.ndjson`.

- `kombu-single-active-consumer-priority`
  - OM kept the transport state coherent across `kombu/entity.py`, `kombu/messaging.py`, `kombu/transport/virtual/base.py`, and added the missing `kombu/transport/virtual/__init__.py` export.
  - OM validated with `pytest t/unit/transport/virtual/test_base.py t/unit/transport/test_memory.py t/unit/test_messaging.py t/unit/test_entity.py`.
  - Evidence: `runs/ponytail-full-pilot-w2/baseline/kombu-single-active-consumer-priority/rep0/result.json`, `runs/ponytail-full-pilot-w2/baseline/kombu-single-active-consumer-priority/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/kombu-single-active-consumer-priority/rep0/result.json`, `runs/om-memory-pilot-w10/pi-observational-memory/kombu-single-active-consumer-priority/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/kombu-single-active-consumer-priority/rep0/pi.jsonl`, `runs/om-memory-pilot-w10/pi-observational-memory/kombu-single-active-consumer-priority/rep0/pi-agent/observational-memory/debug/019f00df-c589-75d9-a59f-70a8e3416bcf.ndjson`.

- `anko-default-function-arguments`
  - Baseline `model.patch` was empty (`0` bytes); OM produced a 6-file patch spanning `ast/expr.go`, `parser/parser.go`, `parser/parser.go.y`, `parser/validate.go`, `vm/vmExprFunction.go`, `vm/vmFunctions_test.go`.
  - OM trace ends with `go build ./... && go test ./...`.
  - Evidence: `runs/ponytail-full-pilot-w2/baseline/anko-default-function-arguments/rep0/result.json`, `runs/ponytail-full-pilot-w2/baseline/anko-default-function-arguments/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/result.json`, `runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/artifacts/model.patch`, `runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/pi.jsonl`, `runs/om-memory-pilot-w10/pi-observational-memory/anko-default-function-arguments/rep0/pi-agent/observational-memory/debug/019f0069-0fe2-7675-aa1a-44e48f7ea950.ndjson`.

## Pattern

OM mostly helped by preserving the same hypothesis across more turns/tool calls, so the agent reached the right cross-file wiring and test coverage. It usually cost more turns/tool calls, but it turned partial/empty attempts into complete, verified fixes.
