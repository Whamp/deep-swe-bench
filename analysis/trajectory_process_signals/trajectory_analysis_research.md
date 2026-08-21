# Research note: sequence-aware coding-agent trajectory analysis

**Question:** Which trajectory-analysis techniques should guide the next stock-Pi analysis, especially for exploration before the first source change, `edit` versus `write`, and testing behavior?

**Scope:** Primary papers and released project material available on 2026-08-14. Several of the most directly relevant works are recent preprints; their methods are useful, but their empirical claims should not be treated as settled consensus.

## Bottom line

The first stock-Pi analysis used totals and repeated-action counts. Recent trajectory work consistently argues that this loses the most useful information: **what phase the agent is in, when it first commits to code, whether it validates after changing code, and whether it moves forward or cycles backward**.

The next analysis should therefore add three distinct feature families:

1. **Opening behavior:** exploration and tests before the first source-code mutation.
2. **Mutation style:** `edit` versus `write`, target type, mutation streaks, revisits, and tool switches.
3. **Phase flow:** exploration → implementation → validation ordering, backtracks, edit-test cycles, and post-pass corruption.

These families should be evaluated separately before combining them. A large undifferentiated feature set would make the result difficult to interpret and increase overfitting risk on 990 attempts.

## What the strongest applicable studies do

### 1. Measure the opening steps and first edit directly

Mehtiyev and Assunção analyze 9,374 coding-agent trajectories over 500 SWE-bench Verified tasks. Their 13-symbol representation distinguishes broad reads, targeted reads, searches, clean edits, re-edits, passing tests, failing tests, runtime errors, reproduction scripts, environment setup, and other actions. Their controlled analysis reports three structural dimensions:

- **context gathering:** step of the first edit;
- **opening patch intensity:** share of the first ten steps spent patching;
- **validation effort:** share of the trajectory spent validating.

Across their agent-level comparison, later first edits correlate with higher resolution (`ρ=+0.68`), heavier patching in the first ten steps correlates with lower resolution (`ρ=-0.78`), and validation effort correlates with higher resolution (`ρ=+0.50`). More importantly for this project, they show that the usual length/failure relationship reverses when task difficulty is controlled: within the same task, resolved trajectories are longer on 63% of contested tasks. Their conclusion is that ordering and phase allocation are more informative than raw length.

**Direct use here:** measure first-source-mutation position, opening-ten action shares, and pre-mutation reads/searches/tests. Repeat both held-out-task prediction and within-task outcome contrasts.

Source: [Beyond Resolution Rates: Behavioral Drivers of Coding Agent Success and Failure](https://arxiv.org/html/2604.02547v1), especially Sections 3.2–3.4 and 4.2.

### 2. Normalize actions, label observable effects, and use milestones

TraceProbe maps heterogeneous logs to nine canonical action types: file read, file write, search, command, sub-agent spawn, plan, navigate, fetch, and reason. It assigns deterministic effect labels such as survived, reverted, failed, and justified, then defines explicit anti-patterns and milestones. Its milestones include first relevant-file read, first relevant-file write, all relevant files written, first passing validation, and first justified action. It reports both raw step timing and timing normalized by trajectory length.

TraceProbe also warns that aggregate anti-pattern counts are often difficulty signals rather than per-run failure explanations. Its stronger design choices are same-task comparisons, same-model/scaffold controls, frozen detector definitions, threshold sensitivity checks, and explicit separation of oracle-free signals from reference-patch-grounded signals.

**Direct use here:** preserve deterministic event rules; add first-mutation and first-validation milestones in raw and normalized form; distinguish an edit that survives from an edit later reversed where observable; report task-controlled effects rather than only pooled means.

Source: [What Resolve Rate Hides: Trajectory Structure Diagnostics for Coding Agents](https://arxiv.org/html/2607.06184), Sections III–VI.

### 3. Treat failure and recovery as temporal processes

Zhao et al. annotate 1,794 CLI-agent trajectories with three retrospective timestamps: decisive error, empirical lock-in, and first observable error. They find that failed runs often make the decisive error early, while observable evidence arrives later. Their recovery analysis finds that 71% of successful trajectories recover from at least one error and that successful recovery is shorter than failed recovery. They also distinguish whether the agent responds to an observed error signal rather than merely receiving one.

This semantic annotation cannot be reproduced automatically from Pi logs without human labels. The useful transferable idea is to measure **response windows** around observable failures: what the agent reads, changes, or retests after a failed test, and how long it takes to obtain a passing result or abandon the approach.

**Direct use here:** derive deterministic failure-response windows and manually label a small sample before claiming that they represent true recovery or lock-in.

Source: [Failure as a Process: An Anatomy of CLI Coding Agent Trajectories](https://arxiv.org/html/2607.09510v1), Sections II-E–II-H and III-A–III-C.

### 4. Separate search, read, and edit—and preserve intermediate edit history

TrajEval decomposes trajectories into search, read, and edit stages, comparing files and functions touched against the reference patch. Its large-scale analysis identifies “coherence collapse”: agents reach the correct code and then overwrite or thrash earlier progress. Five trajectories contained an intermediate patch equivalent to the gold patch and subsequently destroyed it; the intermediate patches passed the benchmark harness when replayed.

TrajEval also parses shell actions for reads and writes in bash-only agents (`cat`, `head`, `sed`, redirects, patch commands). This matters because defining the first mutation only from structured `edit` and `write` calls can be wrong when a shell command changes the workspace.

**Direct use here:** retain an ordered mutation ledger; distinguish `edit` from whole-file `write`; identify writes followed by edits to the same path; detect exact and partial overwrites where structured arguments permit; conservatively flag possible shell mutations before the first structured mutation. Do not claim full workspace history unless shell mutations can be reconstructed.

Source: [TrajEval / Coherence Collapse: Diagnosing Why Code Agents Fail After Reaching the Right Code](https://arxiv.org/html/2603.24631), Sections 2, 4.2–4.3, and Appendices A.10–A.24.

### 5. Use context-sensitive phases and temporal profiles

AgentLens labels actions as Exploration, Implementation, Verification, or Orchestration. The label depends on history, not tool name alone: reading before a patch is exploration; reading edited code can be verification; terminal tests are verification; source edits are implementation. It scores forward phase progress, backtracks, blind retries, and phase distributions in early/middle/late thirds. It also compares trajectories against multiple successful paths rather than assuming one ideal sequence.

AgentLens finds that no single signal separates outcomes well; a combination of structural alignment, coverage, phase coherence, and temporal profile works better. Its ablations assign the largest contribution to temporal profile and phase coherence. It also finds “lucky passes,” showing why process quality should not be equated with final success.

**Direct use here:** create deterministic phase labels and compressed phase sequences; measure forward transitions and backtracks; compare early/middle/late phase shares. Do not impose one rigid ideal path, and do not call a passing but unusual trajectory bad solely because it differs from common behavior.

Source: [AgentLens: Revealing the Lucky Pass Problem in SWE-Agent Evaluation](https://arxiv.org/html/2605.12925v1), Sections 3–6 and Appendices B–D.

### 6. Analyze phase flows and loops, not just event totals

Graphectory represents actions as a graph with temporal edges and code-structure edges. Its compact “Langutory” representation compresses trajectories into Localization, Patching, and Validation phases. The work measures loop count, average loop length, structural breadth, phase transitions, shortcuts, and backtracks. It explicitly treats the same command differently depending on context: tests before patching can help reproduce/localize a bug, while tests after patching validate it; writes to test files can be localization or validation rather than source implementation.

Its reported anti-patterns include repeated views, overlapping scrolls, unresolved retries, edit reversion, missing edit targets, no-effect edits, and ambiguous string replacements. It also warns that stronger models can perform more exploration and testing, so higher complexity is not automatically waste.

**Direct use here:** split test activity into pre-source-mutation diagnosis and post-source-mutation validation; distinguish writes to test/reproduction files from writes to source files; measure phase run lengths and backtracks; avoid interpreting exploration volume without task and model controls.

Source: [Process-Centric Analysis of Agentic Software Systems](https://arxiv.org/html/2512.02393), Sections 2–3.5.

## Proposed stock-Pi event model

### Mutation boundaries

Use two separate milestones:

1. **First workspace mutation:** first successful structured `edit` or `write` call.
2. **First source mutation:** first successful structured mutation to a source-like path, excluding conservatively classified test, reproduction, documentation, and generated-artifact targets.

The second milestone better represents commitment to a fix. A `write` that creates `repro.py` before touching source code is diagnostic work, not implementation.

For each milestone, record whether it exists. The three baseline attempts with no successful structured mutation must have an explicit `no_mutation` indicator, not zero-valued timing.

Flag a milestone as uncertain when a preceding bash command looks mutating (for example, `sed -i`, output redirection, `tee`, `patch`, `git apply`, `cp`, or `mv`). Start with conservative patterns and report the uncertain denominator separately.

### Opening-behavior features

Primary, predeclared features:

- tool calls before first source mutation;
- assistant turns before first source mutation;
- read calls before first source mutation;
- unique paths read before first source mutation;
- search calls before first source mutation;
- tests before first source mutation;
- failed tests before first source mutation;
- first-source-mutation position divided by total tool calls;
- read/search/test shares among the first ten tool calls;
- source-mutation share among the first ten tool calls.

Secondary descriptions:

- first test position;
- whether any test ran before source mutation;
- whether the first test passed or failed;
- number of different test commands before source mutation;
- read-window revisits before source mutation.

### `edit` versus `write`

Treat the tools as different behaviors rather than combining them immediately:

- successful and failed `edit` counts;
- successful and failed `write` counts;
- first workspace-mutation tool;
- first source-mutation tool;
- `write` share of successful mutations;
- mutation-tool switches (`edit→write`, `write→edit`);
- `write` followed by `edit` on the same path;
- repeated full-file writes to the same path;
- exact inverse `edit` pairs;
- mutation target revisits by tool type;
- content bytes supplied to `write` and replacement bytes supplied to `edit` as descriptive scale measures.

Target context is essential:

- source-like target;
- test-like target;
- reproduction-script-like target;
- documentation/config/other target;
- unknown target.

Do not interpret `write` as worse by default. It may create a focused regression test or reproduction script, while `edit` may repeatedly thrash one source file.

### Test and feedback-loop features

- tests before first source mutation;
- tool calls from first source mutation to first post-mutation test;
- mutations before first post-mutation test;
- number of source-mutation → test cycles;
- longest source-mutation streak without a test;
- tests after the final source mutation;
- whether a passing test follows the final source mutation;
- source mutations after an observed passing test;
- pass → mutation → fail patterns;
- failed test → source mutation response distance;
- failed test → passing retest recovery distance;
- fraction of failed tests followed by a mutation before the next test;
- distinct versus repeated test commands after mutation.

A passing top-level test result means only that the command exited successfully. It is not proof that the relevant feature test passed. Keep this boundary explicit.

### Phase-flow features

Map each event to one of four deterministic phases:

- **Exploration:** reads, searches, directory inspection, and non-test read-only shell commands.
- **Diagnosis:** tests and reproduction commands before the first source mutation; writes to clear test/reproduction targets before source mutation.
- **Implementation:** source mutations.
- **Validation:** tests after a source mutation and inspection of already-mutated targets.

Keep ambiguous and other actions separate rather than forcing a phase.

Derived features:

- compressed phase sequence;
- count and duration of phase runs;
- forward transitions (`Exploration/Diagnosis → Implementation → Validation`);
- backtracks (`Implementation → Exploration`, `Validation → Exploration`, `Validation → Implementation`);
- repeated implementation-validation cycles;
- terminal phase;
- early/middle/late phase shares;
- longest single-phase stagnation.

## Evaluation design

### Predictor comparisons

Use the same 990 stock-Pi baseline attempts and the same task-disjoint folds. Compare these predeclared models:

1. length + model/thinking/config controls;
2. length + existing aggregate process counts;
3. length + opening behavior;
4. length + mutation style;
5. length + test/phase flow;
6. length + all sequence-aware families.

This group-wise comparison reveals which idea helps. It is more interpretable than adding every new feature at once.

### Descriptive controls

In addition to held-out-task prediction:

- report per-task success-minus-failure differences on contested tasks;
- report results within GPT-5.5, GPT-5.6 Sol, and GPT-5.6 Luna where support permits;
- report each baseline release separately;
- report raw, within-task-normalized, and total-length-normalized milestone timing;
- report missing and shell-mutation-uncertain denominators;
- bootstrap uncertainty by task;
- freeze thresholds and feature definitions before viewing outcome results.

### Manual validation before strong claims

Hand-label a task-balanced sample for:

- first real source mutation;
- reproduction/test writes versus implementation writes;
- shell mutations;
- useful versus redundant pre-edit reads;
- genuine recovery after a failed test;
- post-pass corruption or unnecessary refinement.

Report agreement between two reviewers or one reviewer plus adjudication. Deterministic metrics can be run immediately, but claims such as “analysis paralysis,” “coherence collapse,” or “recovery” require label validation.

## What not to adopt yet

- **Gold-patch file/function precision as a predictor:** useful for diagnosis, but it leaks privileged solution information and cannot enter the failure-prediction matrix. It can be a separate retrospective analysis.
- **A single ideal phase order:** valid solutions can use diagnosis before exploration, add tests before source changes, or revisit exploration after a failed validation.
- **LLM-judged trajectory quality at full scale:** recent work uses it, but it reduces determinism and requires a human-validated calibration set.
- **Large learned sequence models:** 990 attempts are too few for a high-capacity sequence model without stronger regularization, more tasks, or external training data.
- **Unqualified “waste” labels:** longer and more exploratory successful runs are common. Waste needs same-task references, explicit rules, or manual evidence.

## Recommended next implementation

Implement the opening, `edit`/`write`, test-loop, and phase-flow feature families in the existing read-only extractor. Add synthetic ordering tests first, including:

1. reproduction-file `write` before source `edit`;
2. source `write` as the first source mutation;
3. test before mutation versus the same test after mutation;
4. `edit→test fail→read→edit→test pass` recovery;
5. passing test followed by a destructive edit and failing retest;
6. possible bash mutation before a structured mutation;
7. no-mutation trajectory.

Then regenerate the 990-row baseline dataset and compare the six model specifications above. Keep the existing aggregate result as a separate baseline rather than silently replacing it.
