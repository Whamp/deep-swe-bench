# Aborted workflow smoke v2

The corrected SuperJSON smoke was manually stopped after 20 minutes because the monitor waited for a completed workflow run artifact instead of checking live child activity.

## What actually happened

- The parent called `contract_checkpoint_workflow` immediately on its first turn.
- The child workflow started.
- Child sessions made at least 70 local-Qwen provider requests.
- No completed workflow run JSON existed yet because pi-dynamic-workflows persists that artifact at workflow completion.
- The request audit mislabeled child requests as `scope: main` because separately loaded extension instances did not share the module-local workflow-scope counter.
- The two read-only scouts had timeout bounds but no turn bounds, so they continued long tool loops.
- The smoke was stopped before it produced a patch, verifier result, or `result.json`.

This attempt is quarantined under `results/_contaminated/.../qwen36-27b-contract-checkpoints-workflow-aborted-smoke-v2/` and is not benchmark evidence.

## Follow-up instrumentation

- `qwen-contract-workflow.ts` now writes `qwen-workflow-live.json` before children start.
- Process-wide `PI_QWEN_WORKFLOW_ACTIVE=1` marks nested requests reliably across extension instances.
- `workflow-request-audit.ts` removes tools after 12 turns for read-only roles and 30 turns for writer roles, forcing one final response rather than waiting for the timeout.
- Future monitoring must check the live status file and the count/timestamps of `scope: workflow` request rows within the first minute.
