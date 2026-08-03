# Local-model analysis

Use this frame whenever a comparison includes a local model. The purpose is to
learn the model's capability shape and identify support that could improve it.
Do not treat a local model's expected deficit to a frontier model as the main
finding.

## Comparison roles

State each model's role before interpreting results:

- **Frontier reference:** a current state-of-the-art model used as a capability
  ceiling or positive control. It is not an expected peer for a much smaller
  local model.
- **Local subject:** the model whose reliable abilities, limits, and support
  opportunities are under investigation.
- **Local contrast:** another local model used to expose different strengths,
  failure modes, or execution styles.
- **Config control:** the same model under a different config, used to estimate
  the effect of one harness, tool, skill, prompt, or serving change.

A local-versus-frontier comparison is a **gap analysis**, not a horse race. A
local-versus-local comparison is a **capability-shape contrast**, not merely a
ranking. A controlled same-model config comparison may support an intervention
claim when delivery and paired evidence are sound.

If no frontier result exists for the matched cells, say so. Do not infer the
frontier gap from reputation or unrelated benchmark results.

## Analysis order

### 1. Prove the execution substrate

Before judging capability, verify the intended model and config reached every
cell. Check provider requests, reasoning preservation, tool calls, truncation,
context or output limits, timeouts, verifier completion, and required traces.

Report substrate failures separately. A parser failure, dropped reasoning field,
or verifier timeout is not evidence that the model could not solve the task.
Conversely, reliable delivery does not prove the model understood the task.

### 2. Map reliable capabilities

Start with what the local model can do repeatedly:

- tool and reasoning protocol reliability
- repository navigation and relevant seam discovery
- patch production and scope control
- feature-test coverage
- preservation of existing behavior
- validation discipline
- completion and termination behavior
- language, task-family, and difficulty patterns

Use strict solves and feature tests as primary capability evidence. Keep
preservation tests visible, but do not let a large preservation-test denominator
make high partial reward look like complete feature implementation.

### 3. Locate the frontier gap

On matched cells, select cases where the frontier reference succeeds and the
local subject fails or materially underperforms. Name the earliest supported
trajectory divergence:

1. task or contract representation
2. repository seam selection
3. implementation plan
4. feature completeness
5. invariant or edge-case handling
6. targeted validation
7. regression validation
8. completion audit
9. termination or resource exhaustion

Describe what the frontier trajectory did that the local trajectory did not.
Do not reduce this section to an aggregate score difference.

### 4. Attribute each important failure

Use the narrowest supported layer:

| Layer | Typical evidence | Analytical treatment |
| --- | --- | --- |
| Serving or config | malformed calls, missing reasoning, truncation, wrong model or sampling fields | Fix delivery before drawing capability conclusions. |
| Harness or grading | verifier crash or timeout, missing artifact, orchestration defect | Preserve the observed outcome, but separate benchmark validity from model behavior. |
| Execution control | premature completion, unproductive loops, no validation, failure to react to test output | Candidate for a skill, tool, hook, or progress controller. |
| Repository understanding | wrong seam, missed dependency, excessive scope, cross-scope regression | Candidate for repository maps, impact tools, or architecture guidance. |
| Core model capability | incorrect abstraction or incomplete reasoning despite sound delivery, sufficient feedback, and adequate execution opportunity | Treat as a likely model limit on this task; scaffolding claims require counterevidence. |
| Variance or unknown | paired trajectories do not support a stable mechanism | Keep the cause unresolved and propose the smallest discriminating rerun. |

Do not label every failure scaffoldable. A scaffoldable claim needs a mechanism:
the intervention must expose information, enforce a useful process, or redirect a
specific failure state that the baseline trajectory actually exhibited.

### 5. Build a scaffoldability ledger

For each recurring or high-value weakness, record:

| Field | Required content |
| --- | --- |
| Observed weakness | Exact cells, stage, failed tests or invariant, and trajectory evidence. |
| Failure layer | One layer from the attribution table, with uncertainty if needed. |
| Candidate support | The smallest tool, skill, hook, extension, or harness change that targets it. |
| Expected mechanism | What new information or control changes the trajectory. |
| Non-targets | Similar-looking failures the intervention should not be expected to fix. |
| Risk | Token, latency, leakage, benchmark-integrity, or overfitting cost. |
| Minimal experiment | A same-model paired A/B that changes only the proposed support where practical. |
| Success criterion | The strict, feature, preservation, reliability, and efficiency movement that would count. |

Prefer interventions such as requirement-coverage checks, targeted validation
feedback, progress-aware timeout handling, repository seam maps, or completion
gates only when trajectories show the corresponding deficiency.

Negative evidence should stop unhelpful work. For example:

- Do not raise the output ceiling when no completion approached it and no length
  stop occurred.
- Do not change the tool parser when calls were well formed and replay succeeded.
- Do not grant blanket extra time when long trajectories already looped without
  progress.
- Do not add generic exhortations such as “try harder” when the failure was a
  missing abstraction or unknown invariant.

### 6. Turn hypotheses into controlled experiments

Test scaffold changes against the same local model and serving contract whenever
possible. Change one mechanism at a time. Predeclare the targeted failure class,
matched cells, packet-selection rule, and success criterion.

Support must not reveal the reference patch, hidden tests, grader output that the
normal agent cannot observe, or task-specific solution knowledge. Repository
maps and guidance may derive only from information available inside the task
environment unless the comparison explicitly studies a different information
surface.

Use the frontier reference to show the missing behavior and to estimate the
remaining capability gap. Do not use it as the control for a local-model scaffold
change when an untreated run of the same local model is available.

## Report contract

A local-model report should answer these questions in order:

1. **What works reliably?** Name demonstrated capabilities and their evidence.
2. **Where does the model break?** Show strict, feature, preservation, validity,
   and trajectory evidence.
3. **How does that differ from the frontier reference?** Identify matched stage
   divergences, not just score deltas.
4. **Which failures appear recoverable?** Present the scaffoldability ledger.
5. **Which failures look model-limited or unresolved?** Keep uncertainty explicit.
6. **What should we test next?** Give minimal paired experiments and stop
   conditions.
7. **What should we not change?** Use negative evidence to rule out unsupported
   interventions.

Frame the hero and conclusion around the capability profile and intervention
opportunity. Avoid “winner” or product-selection language unless the user asks
for a ranking or deployment decision.

Keep aggregate score tables, efficiency metrics, and local-to-local rankings as
supporting evidence. Include confidence limits and sample-size caveats, but do
not let statistical uncertainty erase consistent qualitative trajectory
failures.

## Relationship to paired trajectory analysis

Use the `paired-trajectory-analysis` skill for matched-cell evidence, churn,
trajectory packets, stage ledgers, and driver classification. This document sets
the interpretation: frontier results define a reference behavior; local results
are inspected for capability limits and scaffoldable failure modes.
