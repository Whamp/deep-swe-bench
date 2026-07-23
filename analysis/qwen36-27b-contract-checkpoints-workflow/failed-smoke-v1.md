# Failed workflow smoke v1

Run: `qwen36-27b-contract-checkpoints-workflow-high-12v2-r3-w2`

The SuperJSON smoke cell completed, but the smoke contract correctly blocked batch fan-out.

## Failure

- The workflow ran only the two parallel scouts (`workflow_agent_calls=2`, expected 6).
- `seam proof` timed out after 600 seconds, so the workflow returned `ok: false` at `contract_and_seam`.
- The scouts had normal coding tools despite prose saying read-only.
- `contract ledger` wrote `/app/CONTRACT_LEDGER.md`.
- `seam proof` edited implementation files concurrently in the shared workspace.
- The fetch wrapper did not observe nested requests, so `qwen-request-guard.ndjson` was missing.

The resulting patch and score are invalid for efficacy analysis.

## Fix

- Scouts and reviewer use named workflow agent types with disposable Git worktrees and no edit/write tools.
- The synthesizer receives only `read`.
- Only writer roles receive `read,bash,edit,write`.
- The implementation writer commits before the isolated review.
- Parent request hooks remain explicit `pi-flags` entries because the harness passes `--no-extensions`.
- Child sessions inherit the same hooks through leaf `settings.json`.
- `workflow-request-audit.ts` now runs at child `before_provider_request` and records the actual nested payload.
- The wrapper emits `isolation-audit.json` and fails on forbidden read-only tool usage.
