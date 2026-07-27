# 0007 — Separate smoke validation from config behavior

## Context

ADR-0006 included `smoke.json` in each config lock. That made any smoke-contract
correction change the lock identity, even when the prompt, settings, extensions,
models, and every other agent input stayed identical. A failed assertion caused
by an incorrect expected label could therefore force another model run despite
the saved cell containing all required evidence.

Removing smoke contracts from locks without another safeguard would create a
different problem: an approved launch could evaluate a contract edited after
confirmation.

## Decision

Root- and leaf-level smoke contracts are validation inputs, not config behavior
inputs.

- New config locks exclude `smoke.json`.
- Existing schema-1 locks remain valid. Their historical `smoke-contract`
  entries still contribute to the stored lock document's identity, but lock
  verification and launch planning ignore those entries as behavior.
- Launch planning validates the current smoke contract and stores the complete
  assertions in the immutable launch plan.
- Confirmed execution evaluates the assertions stored in the plan. It does not
  reread the live contract for its verdict.
- A corrected contract may re-evaluate an exact saved result without another
  subject or model call when the behavior lock and recorded result evidence are
  unchanged. Explicit result reuse must name any other provenance difference.
- Revalidation fails when behavior changed, result identity cannot be proven, or
  the saved cell lacks evidence required by the corrected contract.

The successful seal still identifies the behavior lock, launch plan, exact
result bytes, model, and thinking level.

## Consequences

Smoke-contract fixes no longer consume model quota merely to reproduce evidence
that already exists. Config behavior remains immutable after sealing, and each
validation verdict remains tied to the exact assertions approved in its launch
plan.

Historical lock files need no rewrite or fabricated migration. Their full
identity remains verifiable while planning presents only true behavior inputs.
