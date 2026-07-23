# Method review: reusable upgrades for paired trajectory analysis

## Scope and evidence standard

This review proposes **method changes only**. It does not edit `.pi/skills/paired-trajectory-analysis/SKILL.md`, and it rejects guidance that is specific to Qwen, `pi-codex-goal`, CodeGraph, observational memory, or the `12_v2` tasks.

Comparison locked for the motivating evidence:

- baseline: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b`
- treatment: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal`
- model/thinking/subset/reps: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, high, `12_v2`, reps 0–2
- 36/36 exact task/rep pairs present; `results/_contaminated` excluded
- time field: `result.json.agent_wall_s`
- timeout and `reward_binary=-1` are observed treatment outcomes unless concrete infrastructure evidence proves otherwise
- difficulty metadata uses TSV fields `pass_rate`, `language`, `slug`, `repository`, `title`

The current comparison has one treatment-only solve, no baseline solves, four timeouts per side, and a treatment mean partial delta of about −0.0066. That makes it a useful warning: solve flips alone are too sparse to expose the mechanisms that dominate a comparison.

## Recommended general additions

### 1. Verify treatment delivery before attributing outcomes

**Problem.** A config label does not prove that its mechanism reached the executor. Tool availability, prompt adapters, hooks, memory blocks, model settings, or harness branches can silently fail or vary by cell.

**Addition.** Add a treatment-mechanism audit immediately after comparison locking. Define expected observable events for each side, then verify them from raw session/config/harness artifacts for every cell.

Minimum per-cell fields:

- expected treatment surface and version/hash
- delivery evidence (prompt transform, tool registration/call, hook event, memory event, model request setting, or harness branch)
- first activation turn and activation count
- missing, duplicated, delayed, or malformed activation
- cross-side leakage check

**Completion criterion.** Every cell is classified `delivered`, `not-delivered`, `ambiguous`, or `leaked`; attribution is limited to delivered cells, while the intention-to-treat result remains primary.

**Evidence.** Delivery has three separate checks in this comparison. First, the durable JSONL contains no literal `/create-goal` command in any treatment cell because Pi expands the command before writing the user message (`treatment_initial_literal_slash_command=False`, 36/36). Second, the expanded package-owned prompt—“Turn the user task into exactly one durable pi-codex-goal objective … call the goal creation tool”—is present in 36/36 treatment first-user messages (`treatment_initial_expanded_adapter_prompt=True`). Third, exactly one `create_goal` call and goal custom events occur in every treatment session. Across baseline sessions, the expanded prompt, goal tool calls, and goal custom events are all absent (0/36 leakage). Activation timing still ranges from turn 1 to turn 23. These independent fields—not the config name—establish delivery without conflating the transformed slash input with its persisted expansion.

### 2. Audit stage completion, not just final completion claims

**Problem.** Final assistant claims and lifecycle events can overstate what was completed. A treatment may alter planning, implementation, validation, consolidation, or termination independently.

**Addition.** Derive a side-by-side stage ledger from session evidence:

1. treatment initialized
2. requirements/contract represented
3. repository seam located
4. implementation started
5. targeted validation run
6. regression validation run
7. verifier-relevant failures investigated
8. final artifact/patch present
9. completion audit performed
10. termination state (`complete`, active at timeout, budget-limited, early stop, crash)

Record the first/last turn, supporting command/event, and status (`complete`, `partial`, `absent`, `unknown`) for each stage. Treat a model's checklist as a claim; corroborate it with commands, outputs, patch state, and verifier evidence.

**Completion criterion.** Every materially changed cell has a stage ledger, and the proposed mechanism identifies the earliest stage where the paired trajectories diverged.

**Evidence.** Treatment sessions commonly call `update_goal` after tests, but one treatment cell is `budgetLimited` after six turns following goal creation and three treatment cells remain active at timeout. `completion_contexts.md` also shows polished completion assertions even when benchmark reward remains below 1. Lifecycle completion is therefore useful behavioral evidence, not ground truth for task completion.

### 3. Expand packet selection beyond binary solve flips

**Problem.** The existing process centers solve flips. Here, baseline has zero solves, so it would inspect one gain and miss large partial regressions, timeout discordances, and near-solve movement.

**Addition.** Build packets for a union of predeclared triggers:

- binary solve discordance
- timeout/reward-negative discordance
- material absolute partial delta (threshold declared before reading trajectories)
- f2p or p2p status/rate discordance
- large resource delta or abnormal termination
- verifier anomaly

Keep all binary flips regardless of magnitude. For partial-only selection, report the threshold and include a ranked tail rather than calling every tiny difference a mechanism.

**Completion criterion.** The report includes every solve flip and timeout discordance plus all cells selected by the declared materiality rule; selection is reproducible from `result.json` without reviewer judgment.

**Evidence.** The packet extractor selects nine cells using the declared union. It includes every solve flip, the four largest deltas in each direction, and all termination-path discordances involving timeout or reward −1. `mobly-grouped-test-barriers/rep1` is retained despite zero partial delta because baseline reached verifier timeout after agent completion while treatment hit the agent timeout. The CodeGraph retrospective likewise found that a nominal solve gain was a verifier/OOM artifact only after packet review.

### 4. Separate f2p and p2p before assigning a driver

**Problem.** Partial reward can hide whether the treatment improved requested functionality, preserved existing behavior, or merely changed grading availability.

**Addition.** Make the first outcome classification a two-axis decomposition:

- f2p: requested behavior
- p2p: preservation/regression
- grading availability: both graded, one missing, neither graded

Use counts and denominators, not only rates. Distinguish at least: feature gain, feature loss, regression introduced, regression repaired, mixed tradeoff, timeout/ungraded, and verifier artifact. Only then assign a trajectory driver such as wrong seam or validation gap.

**Completion criterion.** Every reviewed cell states f2p and p2p passed/total on both sides, names any denominator change, and maps the concrete failed tests separately for each axis.

**Evidence.** In this comparison, treatment's cell-mean f2p is slightly higher while its aggregate weighted f2p is lower (917/1390 vs 954/1419), and treatment p2p is slightly higher (36699/36704 vs 37268/37280). Without denominator-aware separation, the same result can be described misleadingly as either an f2p gain or loss. CodeGraph packets also caught an impossible all-pass f2p result caused by verifier/OOM behavior.

### 5. Add a timeout/resource sensitivity panel without relabeling outcomes

**Problem.** Timeouts are both outcomes and censoring events. Dropping them inflates efficacy; treating all of them identically can hide whether conclusions are driven by one-sided censoring.

**Addition.** Keep intention-to-treat as primary, counting timeout and negative reward exactly as observed. Add bounded sensitivity views:

- graded-only pairs (descriptive, explicitly selected)
- remove both-timeout pairs
- pessimistic/optimistic bounds for one-sided timeout pairs
- fixed-budget comparison using `agent_wall_s`
- timeout incidence and paired timeout discordance
- distance-to-budget and last completed stage

Do not impute a solve from an unfinished patch. A hypothetical rerun is a sensitivity scenario, not a corrected outcome.

**Completion criterion.** The headline result is unchanged from observed outcomes; the report says whether sign/rank/mechanism conclusions survive each declared sensitivity view.

**Evidence.** This comparison contains four reward-negative outcomes per side but not the same termination pattern. There are two treatment-only **agent** timeouts (`mobly` reps 1 and 2), one baseline-only agent timeout (`langchain` rep2), two shared agent timeouts, and one baseline verifier timeout at `mobly` rep1. Only `mobly` rep2 is treatment-only by reward-negative outcome because baseline `mobly` rep1 is also reward −1. The treatment also has a budget-limited early stop at 203.6 seconds. Aggregate equality therefore does not imply equal censoring.

### 6. Use an evidence ladder for infrastructure-vs-treatment diagnosis

**Problem.** It is easy to excuse bad treatment outcomes as infrastructure failures or, conversely, blame treatment for verifier/harness corruption.

**Addition.** Require concrete evidence and a directional diagnosis:

1. **Observed outcome:** timeout, crash, malformed verifier artifact, missing result, etc.
2. **Infrastructure signature:** host/container/provider/harness/verifier evidence independent of model behavior.
3. **Treatment linkage:** whether treatment behavior caused, amplified, or merely coincided with the failure.
4. **Counterfactual support:** paired-side logs, same-task reps, neighboring cells, or reproducible probe.
5. **Disposition:** treatment outcome, infrastructure exclusion, verifier artifact, mixed/ambiguous.

Default ambiguous cases to treatment outcomes in efficacy results; optionally report an audited exclusion sensitivity. Never exclude solely because the result is unfavorable or `reward=-1`.

**Completion criterion.** Every proposed exclusion cites a concrete artifact and explains why the causal path is external to treatment. Mixed cases remain in the primary analysis.

**Evidence.** The CodeGraph churn review found a treatment patch that triggered an infinite re-invocation and heap OOM, followed by a degenerate all-pass JUnit. That is a verifier artifact for solve attribution but still treatment-linked behavior, not a generic infrastructure outage. The OM prototype separately documents provider rate limiting and drops only unmatched failed cases from its matched prototype analysis with an explicit caveat. These are distinct dispositions and should not share a generic `infrastructure` bucket.

### 7. Permit semantic embeddings only as exploratory triage

**Problem.** Embeddings can suggest families of prompts or trajectories but cannot establish why a treatment changed an outcome. Outcome text embedded with the prompt can also leak labels into apparent clustering.

**Addition.** If embeddings are used:

- predeclare the embedded fields
- keep prompt-only and trajectory/outcome-only embeddings separate
- exclude same-task reps from nearest-neighbor evaluation
- report model, dimensions, preprocessing, truncation, and distance metric
- use neighbors to prioritize packet review or generate hypotheses
- require patch/session/verifier evidence for any mechanism claim
- validate clusters out of sample before converting them into stratification or guidance

**Completion criterion.** Embedding findings are labeled exploratory, no causal claim rests on cosine similarity, and any promoted hypothesis is independently verified in trajectories.

**Evidence.** The current 36-document analysis correctly excludes same-task neighbors and reports 58.3% nearest-neighbor structural-label agreement, but it embeds `instruction.md` together with a summary that explicitly states outcome/status. Treatment-timeout cells are mutually similar, yet this may reflect task semantics, shared summary labels, or both. This is useful triage, not causal evidence. The CodeGraph retrospective names semantic search as a different, untested value proposition rather than treating embeddings as proof.

### 8. Separate facts, interpretation, and proposed guidance

**Problem.** Review artifacts can slide from observed command/patch/test facts to mechanism attribution and then to universal skill advice.

**Addition.** Use three ledgers in every packet and synthesis:

- direct session/harness evidence
- patch/source/verifier evidence
- interpretation and confidence

A proposed process change must state trigger, action, completion criterion, observed cells it could have changed, and known counterexamples. Require recurrence across wins and losses, or label it a single-case hypothesis.

**Completion criterion.** Readers can identify which statements are directly observed, inferred, or proposed without reconstructing the analysis.

**Evidence.** The CodeGraph review found one skill-aligned win but also larger patches in three of six meaningful flips and no Pareto improvement. The durable result was the packet method, not a benchmark-specific rule such as “always use CodeGraph” or “always make the patch smaller.” OM findings similarly distinguish memory-signal capture from downstream solve efficacy.

## Minimal proposed diff to the skill

The smallest useful change is to add six checks without rewriting the existing eight-step process:

```diff
 1. **Lock the comparison.** ...
+   Then verify treatment delivery per cell from session/config/harness evidence;
+   classify delivered, missing, ambiguous, and leaked treatment surfaces.

 2. **Split net from churn.** ...
+   Select packets not only for solve flips but also timeout/reward-negative
+   discordance and a predeclared material partial/f2p/p2p change threshold.
+   Keep observed outcomes primary and add an explicit timeout sensitivity panel.

 3. **Build a trajectory packet for each flip.** ...
+   Add a stage-completion ledger from initialization through validation,
+   completion audit, and termination; corroborate model claims with artifacts.

 4. **Map verifier failure to patch delta.** ...
+   Decompose f2p and p2p counts/denominators first, including missing grading,
+   before assigning a driver.
+   Use an evidence ladder before labeling an outcome infrastructure-caused;
+   ambiguous and treatment-linked failures remain treatment outcomes.

 6. **Compare winning and losing patterns.** ...
+   Semantic embeddings may prioritize review only: separate prompt-only from
+   outcome/trajectory embeddings, exclude same-task reps, and require direct
+   trajectory evidence before promoting a mechanism.

 8. **Publish as an evidence-first report.** ...
+   Separate direct session/harness evidence, patch/verifier evidence, and
+   interpretation/confidence.
```

A corresponding small packet-schema change would add `treatment_delivery`, `stage_ledger`, `grading_availability`, `timeout_sensitivity`, and `evidence_ledger` fields. No new driver buckets are required.

## Rejected overfitting

Do **not** add any of the following to the general skill:

- require `/create-goal`, `get_goal`, or `update_goal`
- prescribe a turn by which a goal must be created
- require CodeGraph, OM, workflow, or any named tool
- treat `budgetLimited`, timeout, or `reward=-1` as infrastructure by default
- use a fixed `|Δpartial|` threshold learned from this 12-task subset
- infer that smaller patches are generally better
- infer benefit or harm from one Qwen solve gain
- turn the current embedding neighbors or task families into benchmark strata
- encode the current 90-minute timeout or local-vLLM token scale

The reusable abstraction is **mechanism delivery → stage divergence → f2p/p2p outcome → resource/termination state → infrastructure audit → evidence-calibrated interpretation**. The regenerated `trajectory_packets.json` applies it with per-side stage ledgers and explicit earliest-divergence fields for all nine selected packets. Tool-, prompt-, memory-, harness-, and model-specific details belong in each comparison's treatment contract, not in the core skill.

## Evidence consulted

- `.pi/skills/paired-trajectory-analysis/SKILL.md`
- `.pi/skills/paired-trajectory-analysis/references/packet-schema.md`
- `analysis/qwen36-27b-pi-codex-goal-12v2/{quantitative.json,efficiency.json,goal_mechanics_cells.tsv,completion_contexts.md,trajectory_packets.json,embedding_rows.json,build_embedding_analysis.py,extract_packets.py}`
- `analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/classification.json`
- `analysis/codegraph-retrospective/index.html`
- `analysis/CODEGRAPH_OM_STACKING_FINDINGS.md`
- `analysis/om-impact/FINDINGS.md`

CodeGraph was used only to orient the repository's analysis-artifact structure; all claims above come from direct source/artifact reads, not from graph inference.
