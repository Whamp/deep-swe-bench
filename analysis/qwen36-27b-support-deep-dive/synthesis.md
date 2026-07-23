# What support does normal Qwen3.6-27B need?

## Full-run answer

The completed run contains 36 cells: 12 DeepSWE tasks with three repetitions
each. Normal Qwen entered the tool loop and produced a nonempty patch in every
cell. It solved none.

The model does not need help starting. It needs help selecting the public seam,
turning prose into falsifiable contract rows, proving stateful invariants, and
knowing when its evidence is incomplete.

## Run health and outcome

- 36/36 nonempty patches
- 0/36 full solves
- 32 scored verifier results
- 4 reward `-1` cells
- 3 agent timeouts
- 4 verifier timeouts
- mean DeepSWE partial reward: 0.8021
- median 5.69 million tokens, 85 turns, and 91 tool calls

DeepSWE partial reward hides part of the problem. Across the 32 scored cells,
feature tests passed at 954/1,419 (67.23%), while existing tests passed at
37,268/37,280 (99.968%). Twenty-six of 32 scored patches preserved every old
test. No patch passed every feature test.

This is a contract-completion failure, not a broad regression problem.

## What the second half added

The first 18 cells identified wrong seams, missing invariants, self-confirming
tests, and poor stopping decisions. The last 18 cells strengthened and broadened
that diagnosis.

### Go doc links: semantic classification before implementation

All three reps passed 2/3 feature tests and 15/16 old tests. Each implemented a
different checker, but all failed the package/type/member boundary. The patches
misclassified unimported packages, promoted methods, ambiguous embedded members,
or file-local import context.

The missing decision was a reference-shape matrix before coding: parser fields,
import state, receiver kind, selector outcome, and exact diagnostic.

### GoReleaser: trace durable output, not internal state

Feature performance ranged from 2/29 to 27/29 under identical settings. The two
weak reps stored audit attempts in a new context side channel instead of the
artifact metadata that `artifacts.json` serializes. The strong rep found the
right artifact boundary but still lost attempts on cancellation and left its
sorting collector disconnected from production output.

The missing decision was to trace one attempt from retry loop to decoded public
metadata before implementing the whole retry system.

### Mobly: participant-local state before barriers

Two reps timed out in verification; one also timed out during agent work. The
scored rep passed 58/79 feature tests and regressed 3/808 existing tests. All
three patches stored participant and phase state on a shared test instance while
running participants concurrently.

The missing decision was to prove participant-local identity and result
attribution before building barriers. Barrier keys cannot be correct when the
context that supplies group, participant, and phase is shared mutable state.

### Tengo: object graphs need ownership and identity rules

The three reps passed 20/23, 12/23, and 17/23 feature tests while preserving all
122 existing tests. Each built a different binding mechanism. All missed part of
the callable graph: closure cells, recursion, imports, callback round trips,
nested composites, clone isolation, or runtime frames.

The missing decision was a memoized graph-rebinding design that states which
identities remain shared, which are copied, and which runtime owner replaces the
source.

### Adaptix and SQL Formatter: tests passed the implementation's interpretation

All six patches preserved every old test. Adaptix repeatedly missed public error
translation, non-mapping input guards, overlay precedence, or trail ownership.
SQL Formatter repeatedly encoded the wrong nested `GROUP BY` depth and omitted
standalone pipe `AS` from the parser. Some authored snapshots reproduced the
wrong output, so broad local green confirmed the patch rather than the task.

The missing decision was a literal contract matrix and one public parse/load
probe per row.

## Cross-run diagnosis

The complete data supports six failure mechanisms:

1. **Unproved public seam.** Claude delegation stayed at 0/7 feature tests in all
   reps. GoReleaser and SQL contained locally correct helpers disconnected from
   public output or grammar.
2. **Free-form requirements instead of contract rows.** Exact negative cases,
   precedence rules, error phases, and interactions repeatedly disappeared.
3. **Stateful systems without stated invariants.** Participle, LangChain, Mobly,
   and Tengo failed on cycles, ownership, wakeup, cleanup, isolation, or reuse.
4. **Self-confirming validation.** The model ran many tests, but authored tests
   often matched its own design and command output was frequently filtered.
5. **Missing finalization paths.** Cancellation, serialization, metadata sorting,
   and runtime-error propagation failed after the main operation worked.
6. **Poor stopping calibration.** Thirty-two agents stopped with incomplete
   scored patches; three agents and four verifiers timed out on large stateful
   implementations.

More tools, turns, tests, or patch size did not predict feature completion. The
model needs better decisions, not more generic effort.

## Audit of the seven-line v1 prompt

Every concept remains relevant, but the complete run exposes vague words that
Qwen can satisfy superficially:

1. Keep the contract ledger, but define its fields and status.
2. Keep seam proof, but allow an executable public-flow probe and require it to
   reach the changed symbol.
3. Keep the thin slice, but define success as one contract row passing end to
   end.
4. Expand recursion/concurrency to shared-state graphs and name cycle,
   ownership, wakeup, cleanup, and isolation invariants.
5. Require unfiltered existing-test exits and adversarial cases derived from the
   ledger, not the implementation.
6. Replace subjective churn with observable triggers: a second design or three
   cycles without fewer failures.
7. Define the completion receipt: exact commands/exits, changed public symbols,
   resolved and unresolved rows, and stop reason.

The proposed exact replacement is in `proposed_orchestration_v2.md`. It has not
been applied to a config.

## Recommended experiment

Preserve the current seven-line config as v1 if we want to measure whether the
short wording helps. Otherwise, approve the exact v2 text and replace v1 before
its first paid run; no v1 treatment data exists yet.

For the primary prompt-only comparison, hold model, high thinking, sampling,
timeout, tools, and verifier protocol fixed. Run all 12 tasks × 3 reps. Measure:

- binary solves;
- feature-test pass rate, both micro and macro;
- old-test regressions;
- reward `-1`, agent timeout, and verifier timeout rates;
- whether a ledger appears before the first production edit;
- whether a public seam probe runs before broad implementation;
- whether lifecycle tasks use bounded failure probes;
- whether the final receipt reports unresolved rows and unfiltered exits.

Measure compliance separately from efficacy. A better process with unchanged
feature reward means the prompt changed behavior but did not improve the task.

Do not add CodeGraph, verifier feedback, controller hooks, sampling changes, or a
longer timeout to this comparison. Those are separate treatments. After the
prompt-only result, test deterministic hooks at the exact failure points that
remain.

## Reproducible artifacts

- `analyze_full36.py`
- `full36_metrics.json`
- `full36_cells.csv`
- `proposed_orchestration_v2.md`
- five first-half trajectory reviews in this directory

The full-run metrics come from persisted result and patch artifacts. No model
calls or benchmark reruns were used.
