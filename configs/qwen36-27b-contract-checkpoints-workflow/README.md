# qwen36-27b-contract-checkpoints-workflow

A fixed pi-dynamic-workflows treatment for
`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, served by server60 at
`http://100.92.238.117:30000/v1`.

## Treatment

The config encodes the approved contract-checkpoint process as executable
workflow structure rather than appending the seven instructions to the main
agent prompt. It has no `system_preamble.md` or `orchestration.md`.

`extensions/qwen-contract-workflow.ts` registers one executor-facing tool,
`contract_checkpoint_workflow`. The extension captures the original task text,
forces the main agent to call that tool once, and runs the fixed script in
`extensions/contract-checkpoint.workflow.mjs` with `background: false`.
The main agent cannot use the normal coding tools directly.

The fixed task-agnostic workflow has four phases and six subagent calls:

1. **Contract and Seam** — two parallel read-only scouts independently build a
   contract ledger and prove the owning public seam; a third read-only agent
   reconciles them into one checkpoint.
2. **Thin Slice** — one writer makes a single contract row pass end-to-end before
   expanding, while applying graph/lifecycle/shared-state invariants and bounded
   churn rules.
3. **Adversarial Review** — one read-only reviewer maps the actual diff back to
   every contract row and rejects self-confirming evidence.
4. **Close and Commit** — one sequential writer repairs unresolved rows, runs
   unfiltered regression and independent adversarial checks, commits, and emits
   the completion receipt.

Only the two writer calls can change the implementation workspace. Scouts and
the reviewer run in disposable Git worktrees with no edit/write tools; the
synthesizer has only the read tool. The thin-slice writer commits before review,
so the isolated reviewer sees the exact implementation state. The workflow
contains no DeepSWE task names, repositories, languages, expected patches,
verifier tests, hidden-answer hints, or task-derived examples.

## Model isolation

Every LLM role uses exactly
`local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4:high`:

| role | model | thinking | timeout | concurrency |
| --- | --- | --- | ---: | --- |
| main Pi tool dispatcher | local Qwen3.6-27B | high | parent cell budget | 1 |
| contract ledger scout | local Qwen3.6-27B | high | 10 min | up to 2 scouts |
| seam proof scout | local Qwen3.6-27B | high | 10 min | up to 2 scouts |
| checkpoint synthesizer | local Qwen3.6-27B | high | 10 min | 1 |
| thin-slice implementer | local Qwen3.6-27B | high | 25 min | 1 |
| contract adversary | local Qwen3.6-27B | high | 20 min | 1 |
| closure/receipt writer | local Qwen3.6-27B | high | 25 min | 1 |

The two scouts share the first 10-minute window. The maximum child-stage critical
path is therefore 90 minutes. Normal stages usually finish below their caps, but
the parent cell budget must be at least 90 minutes.

The script names the exact model on every `agent()` call. All small/medium/big
fallback tiers are pinned to the same exact model as defense in depth. No API
credential is needed.

Nested Pi sessions load extensions from the config leaf's `settings.json`.
That file registers the same preserve-thinking and sampling extensions used by
the parent, plus `workflow-request-audit.ts`. The audit extension runs at the
actual child `before_provider_request` seam, enforces `enable_thinking=true`,
`preserve_thinking=true`, `temperature=1.0`, `top_p=0.95`, `top_k=20`,
`min_p=0.0`, `presence_penalty=0.0`, and `repetition_penalty=1.0`, and records
nested calls with `scope: "workflow"` under
`pi-agent/workflows/qwen-request-guard.ndjson`.

## Usage accounting

The harness copies `/root/.pi/workflows` to `pi-agent/workflows` in each result
cell. `harness/parse_usage.py` reads persisted workflow run `tokenUsage` into
`workflow_*` and `combined_*` result fields. The smoke contract requires one
completed workflow, zero failed workflows, exactly six subagent calls,
non-zero workflow tokens, all phase/agent markers, the exact local model, and a
nested guarded request.

## Validation and launch

A capture-only probe may validate the main request without executing the model.
A paid preflight is still required before batch fan-out because nested worker
behavior and usage accounting cannot be proven without running the workflow.
Any launch must show the main and nested role table and receive explicit user
confirmation.
