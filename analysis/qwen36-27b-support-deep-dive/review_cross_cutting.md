# Cross-cutting decision-quality audit: normal Qwen3.6-27B, high thinking

## Executive answer

**What this model needs from the harness is not more general advice or more thinking. It needs a small, enforced outer loop that (1) makes it commit to the repository seam and contract before editing, (2) selects tests by changed-symbol impact rather than by tests the model just wrote, (3) interrupts oversized or recursive implementations for a scope/architecture check, (4) gives one compact verifier-feedback repair turn, and (5) forces a bounded stop decision.**

The strongest proven pattern is “plausible, large implementation that preserves the old suite but misses the evaluator's contract.” At the inspected snapshot, 18 cells were complete (six tasks × three reps): 16 produced verifier results and two LangChain cells timed out. Fourteen of 16 verified patches passed **all** P2P tests, but **none** passed all F2P tests. This is not primarily an inability to edit or keep repositories building. It is a seam-selection, contract-coverage, and stopping problem.

A short system prompt alone is unlikely to move this. High thinking already produced lengthy checklists, repeated self-review, and 0.88M–6.95M cumulative input tokens per cell. The missing control is external and stateful.

## Inherited decisions and audit boundary

- Active config/model path: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b`.
- Run: `results/_runs/qwen36-27b-high-clean-12v2-r3-w2`, launched as baseline config, `high` thinking, three reps, two workers over `subsets/12_v2.txt`.
- Snapshot inspected: 18 completed cells covering SuperJSON, Obsidian Linter, Participle, dateutil, LangChain, and Claude Code by Agents. `go-critic-doc-link-checker` was still running and later tasks were pending; incomplete cells are not used as outcome evidence.
- This is a harness-support diagnosis, not a recommendation to contaminate the baseline. Any support should be a separately named config/comparison.
- Project files were not edited. The active worktree already contained unrelated unstaged files; `git diff --cached --name-only` was empty.

## Proven facts

1. **Old behavior is usually preserved.** Fourteen of 16 verified cells had P2P=1.0. Only SuperJSON rep0 and rep1 lost three of 116 P2P tests each (`.../superjson-error-stack-serialization/rep{0,1}/verifier/reward.json`).
2. **Feature-contract completion is systematically imperfect.** No verified cell reached F2P=1.0. Results ranged from 0.0 (all Claude delegation reps) to 0.9833 (Obsidian reps 1–2).
3. **The model writes very large patches.** Completed patches add roughly 939–2,347 lines, commonly across only 3–8 files. Examples: LangChain rep1 +2,347 lines; SuperJSON rep0 +1,583; Participle rep1 +1,585; Claude rep0 +1,224.
4. **Self-authored tests are not reliable acceptance evidence.** Claude rep0 ended claiming “All delegation tests pass,” but all seven evaluator feature tests failed. Participle reps1–2 ended claiming tagged and untagged suites passed, but the verifier hit a stack overflow in `TestAnalyzeRecursiveStructure`. SuperJSON reps reported full local success while 15–60 F2P checks failed.
5. **Stopping fails on difficult concurrency work.** LangChain reps0 and 2 hit the 5,400-second agent timeout and never reached verifier execution (`.../langchain-request-coalescing/rep{0,2}/result.json`). Rep2 ran only import/ad-hoc smoke checks and no pytest test; rep0 explicitly began another full stream redesign near the end.
6. **A good trajectory is possible with the same model/settings.** LangChain rep1 reached F2P=.92; Participle rep0 .967; Obsidian reps1–2 .983. Therefore wholesale model replacement is not supported by this sample.

## Phase-by-phase weakness model

| Phase | Proven behavior | Diagnosis | Harness implication |
|---|---|---|---|
| Task framing | The model restates nearly every requirement as a checklist. | Comprehension at noun/feature level is adequate, but it does not convert requirements into falsifiable repository-specific obligations. | Require a contract ledger whose rows name the existing seam and an observable test, not free-form planning. |
| Repository search | It reads relevant central files and searches method/class names before editing. | Search volume is high, but search is breadth-first and not impact-oriented. It often misses the exact integration path exercised by evaluator tests. | Provide callers/implementers/nearest-tests context for candidate symbols; do not add more generic grep advice. |
| Seam selection | Claude reps implemented bespoke delegation in `backend/handlers/{chat,multiAgentChat,delegation}.ts`; all evaluator tests in `tests/handlers/recursiveDelegation.test.ts` failed. LangChain rep1 created `RunnableCoalesced` that was not an instance of `Runnable`. | The model commits to a plausible local seam without proving compatibility with framework identity, mocks, factories, and existing test entry points. This is the highest-severity decision defect. | Gate first edit on a seam checkpoint and inheritance/interface proof. |
| Plan commitment | The model announces comprehensive plans, then implements most of the task in one large write. First edits commonly occur around session lines 19–55, followed by 900–2,300 added lines. | Plans are expansive rather than staged; there is no smallest vertical slice or abort condition. | Enforce one thin end-to-end slice before bulk implementation. |
| Editing | Large bespoke modules and tests are created; existing tests are sometimes changed (dateutil removes an xfail). | The model can code, but large surface area compounds hidden assumptions and makes recovery expensive. | Scope guard should interrupt—not blindly reject—large/contract-sensitive diffs and modifications to existing tests. |
| Test choice | It heavily reruns self-authored feature tests and broad old suites; many commands truncate output with `head`/`tail`/`grep`. | The chosen tests confirm its own design and regression safety but under-sample framework conformance, recursion, exact edge semantics, and evaluator entry paths. | Use changed-symbol test selection plus mandatory untruncated targeted output. |
| Error recovery | It can repair local failures repeatedly (Obsidian rep1; LangChain rep1), but also edits tests to fit behavior and repeatedly redesigns concurrency code. | Recovery is effective when feedback is close to the actual contract; otherwise it overfits or churns. | Give one compact verifier-feedback loop and prevent changing existing acceptance tests during that repair. |
| Stopping | It commits after local green checks even when relying on filtered output; two cells never stop. Final summaries overstate compliance. | Self-assessed completion is poorly calibrated. | Add explicit stop controller and machine-generated completion receipt. |

## Severity findings

### Critical — seam selection is not validated before large edits

- `.../claude-code-by-agents-recursive-delegation/rep{0,1,2}/artifacts/model.patch`: three distinct 939–1,224-line implementations; all seven F2P tests in `.../verifier/ctrf.json` fail in every rep. The failures include the basic delegate execution, recursive A→B→C, circular handling, error continuation, unknown agent, empty instructions, and no-text behavior. This uniform failure despite different patches strongly indicates the evaluator's exercised seam was never connected.
- `.../langchain-request-coalescing/rep1/verifier/ctrf.json`: `RunnableCoalesced` is not a `Runnable`, fails graph composition, and `CoalesceBackend` lacks runtime-checkable protocol behavior. The implementation satisfied its own operational tests while violating framework type/composition seams.

### High — testing is self-confirming rather than contract-seeking

- `.../participle-grammar-conflict-analysis/rep{1,2}/verifier/run.log`: hidden recursive structure causes fatal stack overflow; local test selection repeatedly focused names matching `Test(First|Unreachable|Suppress|Strict|Analysis|Conflict)` and did not expose the recursive graph defect.
- `.../superjson-error-stack-serialization/rep{0,1,2}/verifier/ctrf.json`: failures cluster around exact annotations, object rehydration, cause-depth semantics, class filters, frame processing order, and path redaction. These are explicit contract dimensions, yet locally created tests accepted divergent semantics.
- `.../dateutil-rfc5545-timezone-interop/rep{0,1,2}/verifier/ctrf.json`: failures repeatedly expose unstable TZID identity (`EDT` versus `America/New_York`), VTIMEZONE priority, UTC rendering, and aware/naive round trips. Ad-hoc scripts asserted weaker properties such as “contains TZID” or equal local dates.

### High — no bounded stop/recovery policy

- `.../langchain-request-coalescing/rep0/session/*.jsonl`: no test suite was run; late reasoning says the global stream-holder design is problematic and starts a rewrite. Timeout at 5,400 seconds.
- `.../langchain-request-coalescing/rep2/session/*.jsonl`: no pytest test was run; only import and sequential invoke smoke checks. Timeout at 5,400 seconds.

### Medium — patch size and existing-test modification obscure confidence

- All completed patches are large; several add >1,500 lines.
- Dateutil reps modify `tests/test_rrule.py` to remove an xfail while feature semantics remain incomplete. A benchmark harness should treat changes to pre-existing tests as a high-signal checkpoint event.

## Ranked harness supports

Each support below is enforceable and minimal. “Trajectories altered” names observed cells, not speculative task classes.

### 1. Pre-edit seam + contract checkpoint (highest priority)

**Form:** workflow/checkpoint; optionally backed by a repository-context tool.

**Trigger:** before the first `write`/`edit`, or after more than eight exploratory tool calls without selecting a seam.

**Action:** require a compact structured record:

- contract row;
- existing symbol/entry point that owns it;
- callers or implementers proving the seam;
- nearest existing test that exercises that entry point;
- one smallest vertical-slice test;
- explicit “framework identity” checks (inheritance/protocol/export/graph/build-tag boundary) where applicable.

The harness rejects the first edit until every must-have contract family has a repository seam or is marked unknown. Unknowns require one more targeted search, not prose.

**Completion criterion:** at least one existing (not newly authored) test reaches the proposed seam, and the model can name the changed symbol visible from that test. For wrapper/framework tasks, a smoke assertion such as `isinstance(wrapper, BaseType)` or composition through the public factory must pass before bulk editing.

**Observed trajectories altered:**

- Claude delegation reps0 and 1: would force proof that `tests/handlers/recursiveDelegation.test.ts` reaches the chosen handler/provider path before creating 900+ lines.
- LangChain rep1: would catch that `RunnableCoalesced` is not a `Runnable` and cannot be composed before +2,347 lines are committed.
- Participle reps1–2: would require mapping recursion/cycle semantics to the grammar node graph before recursive traversal implementation.

**Fact vs hypothesis:** the wrong-seam outcomes are proven; that this gate would correct them is a high-confidence hypothesis requiring an A/B config.

### 2. Changed-symbol test-selection helper

**Form:** test-selection helper, not prompt advice.

**Trigger:** after the first production diff and after each material change to public API, inheritance, parser traversal, concurrency state, or serialization annotations.

**Action:** inspect the diff and return a short ordered list:

1. nearest pre-existing tests importing/calling each changed public symbol;
2. tests for callers/implementers of changed base types;
3. one recursive/concurrent/round-trip test when those risk tags are detected;
4. the narrowest full package suite.

The helper should run selected tests without `head`, `tail`, or success-only `grep`, and retain the actual exit code/output. Model-authored tests may supplement but never satisfy the pre-existing-test slot.

**Completion criterion:** all selected existing tests pass; untruncated output and exit code are recorded; every changed public symbol has at least one exercised path.

**Observed trajectories altered:**

- Participle reps1–2: risk tag “recursive graph traversal” would select/add a cycle/recursive-structure probe instead of only name-filtered feature tests, exposing the stack overflow locally.
- Claude reps0–2: would prioritize the existing recursive delegation integration file rather than only newly added `backend/tests/handlers/delegation.test.ts` and `multiAgentChat.test.ts`.
- SuperJSON reps0–2: round-trip and annotation risk tags would require exact meta annotation and rehydrated `Error` identity checks.
- Dateutil reps0–2: round-trip helper would compare canonical TZID and aware datetime identity, not merely presence of a timezone.

**Fact vs hypothesis:** the mismatch between local test choice and verifier failures is proven. The helper's ranking quality is unproven and should be logged for manual audit.

### 3. Diff-risk / patch-scope guard

**Form:** patch-scope guard with a checkpoint, not a hard universal LOC cap.

**Trigger:** any of:

- >600 added production lines before an existing feature-path test passes;
- a new bespoke subsystem >300 lines around a single public method;
- modification/deletion/xfail change in a pre-existing test;
- implementation of the same contract in multiple handlers/entry points;
- second complete rewrite of the same file.

**Action:** pause editing and display machine-generated diff facts: files, added/deleted lines, existing tests changed, duplicate entry points, and uncovered public symbols. Require the model to choose one: shrink to a vertical slice, justify each surface with a contract row, or revert the latest expansion. Existing tests become read-only during the checkpoint unless the task explicitly requires changing them.

**Completion criterion:** every retained production file maps to a contract row and selected existing test; no pre-existing test weakening remains; at least one thin slice is green.

**Observed trajectories altered:**

- Dateutil reps0–2: would stop wholesale changes to `src/dateutil/rrule.py` plus xfail removal until canonical TZID round-trip worked.
- SuperJSON reps0–2: would force annotation/rehydration vertical slice before 1,272–1,598-line multi-module expansion.
- LangChain rep0: would interrupt the second stream redesign and global-holder approach before timeout.
- Claude rep0: would challenge parallel implementation in both `chat.ts` and `multiAgentChat.ts` before either evaluator seam was proven.

**Fact vs hypothesis:** patch sizes and test modifications are proven. The 600/300 thresholds are hypotheses; log-only pilot first, then enforce after measuring false positives.

### 4. One compact verifier-feedback repair turn

**Form:** verifier feedback loop. This changes the evaluation protocol and must be isolated as an explicit support config.

**Trigger:** after the model's completion receipt passes local gates but the first verifier attempt is non-perfect.

**Action:** return only compact, non-solution feedback: failing test names, assertion/error class, first relevant trace, and failing contract family. Do not expose expected patch or hidden source. Allow one bounded repair phase; pre-existing tests are immutable.

**Completion criterion:** rerun only failed verifier cases plus P2P; stop after one repair turn or 20 minutes; record first-pass and repaired scores separately.

**Observed trajectories altered:**

- Obsidian rep1 (`escaped >`) and rep2 (unbracketed spaces): each had one isolated F2P failure and is an ideal low-cost repair.
- Participle rep0: three union/location failures could be repaired from focused feedback.
- LangChain rep1: four framework conformance failures (`Runnable` identity, graph, runtime protocol, stats) are localized.
- Claude reps0–2: seven uniform integration failures would reveal wrong seam early; the bounded turn prevents another full rewrite.

**Fact vs hypothesis:** verifier failures are proven. Score gain is unproven, but this is the support most directly matched to the model's demonstrated ability to repair concrete local failures.

### 5. Progress/stopping controller with completion receipt

**Form:** workflow controller.

**Trigger:** any of:

- 15 minutes without a new passing targeted test or reduced failing-test count;
- three consecutive edit/test cycles with no progress;
- second architectural rewrite;
- 75 minutes total;
- final response attempted without recorded untruncated targeted and regression exits.

**Action:** inject a machine state card: elapsed time, diff size, last three test exits, unresolved contract rows, and remaining budget. Require exactly one decision: repair one failing row, revert to last green checkpoint, or finalize current patch. At 75 minutes, disable broad exploration and new subsystem creation.

**Completion criterion:** final receipt contains diff summary, selected existing tests with exits, unresolved rows, and explicit stop reason. A prose claim like “all tests pass” is not accepted without receipts.

**Observed trajectories altered:**

- LangChain reps0 and 2: both would stop or checkpoint well before the 5,400-second timeout.
- LangChain rep1: would preserve the high-scoring implementation while surfacing four unresolved conformance rows rather than claiming complete integration.
- Participle reps1–2 and SuperJSON reps: would prevent filtered local-green output from becoming an unqualified completion claim.

**Fact vs hypothesis:** the two timeouts and inaccurate completion claims are proven; exact time thresholds are hypotheses.

## Explicit option assessment

| Option | Verdict | Reason |
|---|---|---|
| Short system prompt | **Low priority; not sufficient alone.** | The model already produces long plans/checklists. Generic “inspect tests,” “keep scope small,” or “verify thoroughly” wording would duplicate behavior without enforcement. Also, project rules prohibit inventing config prompt text without Will's exact approval. If tested, approve exact wording separately and keep it to one checkpoint instruction. |
| Workflow/checkpoint | **Yes; primary support.** | Directly addresses premature seam commitment and uncalibrated stopping. |
| Test-selection helper | **Yes; primary support.** | Existing test choice is the clearest cross-task gap. |
| Patch-scope guard | **Yes, initially log/warn then enforce.** | Large patches correlate with assumption accumulation, but complex tasks genuinely need sizable changes. |
| Verifier feedback loop | **Yes, strongest likely efficacy; protocol-changing.** | Concrete feedback is where this model demonstrably recovers. Must be a separate comparison because it uses evaluator feedback. |
| Tool schema change | **Only a narrow repository-context tool.** | Add a tool returning definition, callers/implementers, public exports, and nearest existing tests for named symbols. Do not add a broad planner tool or verbose tool descriptions. Search quantity is not the bottleneck. |
| Different thinking/sampling | **Do not lead with it.** | `high` already yields extreme deliberation and still misses seams; more thinking is unsupported. A lower-thinking or lower-variance pilot may reduce timeouts, but could reduce contract coverage. First hold sampling constant and test the outer-loop supports. Then compare `medium` versus `high` with the same scaffold. Temperature effects are unverified from inspected artifacts. |

## Recommended next move

Run a small, separately named support comparison on tasks with diagnostic diversity, holding model and sampling constant:

1. Claude delegation (wrong-seam, 0/7 across all reps),
2. LangChain coalescing (timeouts plus one .92 trajectory),
3. Participle (cycle catastrophe versus .967 trajectory),
4. Obsidian (near-perfect, tests whether scaffolding harms efficient work).

First config: supports 1, 2, 3, and 5 only. Second config, only after that: add the single verifier repair turn. Primary measures should be F2P, timeout rate, first-pass versus repaired F2P, added production LOC, time to first existing feature-path test, and whether the chosen seam is reached by an existing test before bulk editing.

Do **not** combine prompt changes, sampling changes, and feedback-loop changes in one config; that would make the decision uninterpretable.

## Drift / contradiction check

- Adding a verbose orchestration preamble would drift from both the evidence and the repository's “do not invent config prompt text” rule.
- Treating P2P≈1 as success would contradict the task objective: the model preserves old behavior while missing feature semantics.
- Increasing the timeout would reward the exact non-stopping behavior seen in LangChain reps0/2 and is not support.
- A universal hard LOC cap would overcorrect; the best cells are also large. Use a checkpoint keyed to coverage, not size alone.
- Using live verifier feedback inside the baseline would invalidate baseline comparability. It belongs in an explicit feedback-support config with first-pass scores retained.

## Risks and unresolved hypotheses

- The snapshot covers only the first six completed tasks; later subset tasks may add different failure modes.
- F2P tests are evaluator-authored and hidden during execution. A test-selection helper cannot select hidden tests; it must infer risk from public symbols and existing tests.
- Compact verifier feedback may produce large gains but changes the assistance budget and benchmark interpretation.
- Thresholds (eight exploratory calls, 600/300 LOC, 15/75 minutes) are starting hypotheses, not proven optima.
- A repository-context tool could over-anchor the model to existing seams when the task truly requires a new subsystem; require evidence, not forced reuse.

## Need from main agent

No blocking decision is needed for this read-only audit. Before implementation, the main agent should decide whether the next comparison is (a) pure workflow scaffolding or (b) verifier-assisted repair; they must not be conflated.

## Suggested execution prompt

No executor handoff is warranted from this audit. Any config implementation would require Will's approval of scope and, if a system prompt is used, the exact prompt text.

## Acceptance report

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete severity findings cite result, session, patch, and verifier paths under results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b; five supports include trigger, action, completion criterion, and at least two observed trajectories."
    }
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "inventory result/run trees and read subset, status, manifest, sessions, patches, rewards, CTRF, and verifier logs",
      "result": "passed",
      "summary": "Audited all 18 completed cells at the snapshot and deep-read representative trajectories across all six completed tasks."
    },
    {
      "command": "Python summaries of rewards, patch files/line counts, tool/test histories, first-edit points, and verifier failures",
      "result": "passed",
      "summary": "Confirmed 16 verified cells, two timeouts, 14/16 perfect P2P, 0/16 perfect F2P, and cross-task failure clusters."
    },
    {
      "command": "git status --short && git diff --cached --name-only",
      "result": "passed",
      "summary": "Found pre-existing unrelated unstaged worktree changes and no staged files."
    }
  ],
  "validationOutput": [
    "Snapshot state: 17 done + 1 skipped (18 completed), 2 running, 16 pending.",
    "Verifier aggregate: 16 verified, 2 timed out; 14/16 P2P=1.0; 0/16 F2P=1.0.",
    "No project tests were run because the task was read-only; validation used persisted verifier evidence."
  ],
  "residualRisks": [
    "Later tasks in the active 12-task comparison were incomplete and not included as outcome evidence.",
    "Recommended thresholds and causal effects of supports remain hypotheses requiring a separately named comparison.",
    "Verifier feedback is protocol-changing and must not be mixed into the baseline."
  ],
  "noStagedFiles": true,
  "diffSummary": "No project diff created; only this requested review artifact was written.",
  "reviewFindings": [
    "critical: claude-code-by-agents-recursive-delegation/rep{0,1,2} - all seven F2P integration tests fail despite large locally-tested implementations, indicating an unvalidated seam",
    "high: langchain-request-coalescing/rep{0,2} - both hit 5,400-second timeouts without an adequate test/stop loop",
    "high: participle-grammar-conflict-analysis/rep{1,2}/verifier/run.log - recursive structure causes fatal stack overflow missed by local selection",
    "high: superjson/dateutil verifier clusters - self-authored tests accept semantics that diverge from exact annotation, rehydration, cause, and TZID contracts",
    "medium: completed patches routinely add 900-2,300 lines; existing-test changes and filtered outputs weaken completion confidence"
  ],
  "manualNotes": "Read-only audit. Active-run snapshot boundary is explicit; incomplete go-critic and later tasks were excluded from outcome claims."
}
```
