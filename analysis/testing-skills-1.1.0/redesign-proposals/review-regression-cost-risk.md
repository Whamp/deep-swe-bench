# Adversarial review — regression and cost-risk axis

**Reviewer task:** `review_evidence_glm` · **Axis:** regression and cost risk (worsen successful trajectories, raise token/tool use, force unsuitable specialist techniques; require bounded safeguards).

**Grounding:** Read `full113-comparison.json`, `full113_analysis.py`, both candidate designs (`openai` inline; `glm` at `redesign-proposals/minimal-pbt-legible.md`), the three canonical skills, and 109 material paired packets plus raw sessions for the cost-critical cells. Verified directly: cache-read composition, convergence-loop cells, state-mutating validation patterns, and skill body sizes. **Observed** = read from artifacts; **inference** = labeled.

---

## Required revisions (severity order)

### S1 — The stop condition is unsafe for state-mutating validation commands  [SEVERE]

Both designs propose a stop condition of the form "re-run a command only after a change that could affect its result" (openai step 5 / `glm` B.3). The word **change** is ambiguous in two ways that, under a literal reading, truncate loops that produced solves.

**Observed.** In `dynamodb-toolbox-lazy-recursive-schemas/rep0` the treatment ran the identical `npm run test-format-fix && test-type && test-lint && vitest` chain **five times** and **solved** (+4.3M tokens, 0→1 flip). I traced the full timeline: each run was preceded by real production/test edits — but each run also **mutated state itself** (`test-format-fix` runs Prettier `--write`). The next run validates the auto-fixed tree. This is a legitimate convergence loop, not churn. In `helm-unified-manifest-stream/rep0` the pattern is sharper: `go test … -update` **regenerates golden files**, then `go test` validates them — the validation re-run exists *because* the prior command changed the working tree.

**Risk.** A model reading "no change since last run → stop" can interpret "change" as an *external* change, treating its own edits or the previous command's side-effects (Prettier `--write`, `gofmt -w`, golden `-update`) as non-changes. It would then halt after the first auto-fixing run, leaving an unvalidated or half-converged tree.

**Counterexample preserved by the design (insufficient as-is).** Both designs cite `dynamodb/rep0` and `query-persist-restored-query-state/rep2` (16 validation commands, solved) as proof the stop is safe. Those citations assume the loop was *information-gated* (failures changed each run). That is true here, but the wording does not encode the gate; it encodes "no change," which is the wrong predicate for state-mutating commands.

**Required safeguard (bounded).** Replace "a change" with an explicit, two-part trigger: a re-run is justified when (a) the agent has edited production or test code since the last run of this command, **or** (b) the previous run mutated the working tree (auto-format, lint-fix, golden/fixture regeneration, snapshot update) and the current run validates that mutation. State explicitly that a green command that itself rewrote files does not count as "evidence on the final patch." This keeps the cost benefit (no pure no-op reruns) without truncating Prettier/gofmt/golden convergence loops.

---

### S2 — Contract-inventory body inflation is an ungated, multiplicative cache-read tax on 317 cells  [HIGH]

**Observed.** Cache-read is the cost engine: of +102.2M added tokens, **+97.2M (95.1%, verified directly from `result.json`)** are cache-read, +4.5M uncached input, +0.4M output. Output per turn rose only ~1.6%; the increase is context replayed over +17.7% more turns. `testing` is read in **317/339** cells, so anything added to its body is replayed (cache-read) on every subsequent turn across nearly every session.

**Observed — both-solved overhead.** 89 both-solved cells consumed **+20.1M tokens with zero reward movement**. The 26 both-solved cells with a treatment-only test patch consumed +6.93M tokens. These cells already solve; the marginal efficacy of a contract inventory there is ~zero, but the body-replay cost is certain.

**Inference — tax estimate.** A ~150-word addition to the `testing` body (the openai "Contract ledger and owner" section is heavier than the current route table it replaces; `glm` B.2 is lighter but still net-positive) replays as roughly **+1.1–1.5M cache-read tokens** across 317 cells at ~18–25 turns each (1.3 tok/word × cells × turns). This is a *certain* cost applied to the cohort where efficacy is least likely to help, including the both-solved set.

**Counterexample the design preserves.** `aiomonitor-task-snapshots-diff` reached 51/53 across reps with only one durable test; the inventory escape hatch ("treat several clauses as one row only when you can state the covering invariant") is meant to admit this. But the escape hatch is discretionary, and the both-solved evidence shows agents already over-invest where reward is fixed.

**Required safeguards (bounded).**
1. Make the **single inline row the explicit default** and the table form strictly conditional on "more than one independently observable clause." The openai draft inverts this by leading with the table; lead with the one-row form.
2. Declare a **body-size budget** for the `testing` change (e.g., net ≤ +60 words vs. current route section) and measure it at ship time, since cache-read is the dominant cost lever.
3. Add the **non-inferiority guardrail** the proposals already name — per-cell token delta and solve/preservation on the both-solved cohort — as a *blocking* gate, not a passive metric.

---

### S3 — The exclusive handoff fires on a step-1 commitment, before any property is written  [HIGH]

**Observed.** `prometheus-typed-label-sorting/rep1` read property-based-testing, wrote a finite antisymmetry loop, but missed one ordering category and flipped **solved → 16/17 (1→0)**. This is a partial, shallow specialist "accept" — an artifact existed, but the property work did not actually discriminate the risk.

**Risk.** Both designs transfer ownership from `testing` to the specialist when the specialist "writes its leverage sentence or campaign contract" (openai) / "accepts the surface — it writes its leverage sentence" (glm B.1). A leverage sentence is **step 1**, written before any property is implemented. Firing the exclusive handoff there stops `testing`'s discrimination loop — the one mechanism with evidence of net gain — at the moment the specialist is least proven. `prometheus/rep1` is exactly the failure mode this creates: a commitment that is not ownership.

**Counterexample preserved.** `arktype-json-schema-refs-dependencies/rep0` and `cliffy-config-file-parsing/rep2` read a specialist, declined in practice to explicit examples, and won. The decline path is safe. The accept path is the risk.

**Required safeguard (bounded).** Transfer ownership only when the specialist has produced **executable, discriminating evidence** for that row (a property proven red-then-green on the named counterfeit, or a real campaign with recorded command/elapsed/replay) — not when it has committed in prose. Until then, `testing` retains the discrimination loop; the specialist runs *alongside* it, not *instead* of it. A leverage sentence is a routing decision, not a handoff.

---

### S4 — The outer-surface journey mandate is unbounded; it adds certain cost to both-solved cells  [MEDIUM]

**Observed — justification.** `textual-richlog-follow-state/rep0–2` is the only 3/3 repeated loss: focused widget checks passed in every rep while the exact named example journey failed identically; baseline solved all three. The outer-surface rule targets this correctly.

**Observed — cost risk.** The rule "exercise every outermost changed surface … run at least one journey through that surface" applies to *all* changed-surface cells, including the 89 both-solved. `narwhals-rolling-window-suite/rep2` touched 12 files and its +1.62M-token cost came from **production scope expansion** (188→503 lines), not from missing surface journeys — mandating more journeys there adds cost against no reward movement.

**Required safeguard (bounded).** Bound journeys to **surfaces the request names as a deliverable or acceptance surface** (the textual defect was one named example), not to every changed path. Cap broad-surface coverage at the request's named entry points; the rule should not generate N journeys for N incidental file changes. The "required broad suite once on the final patch" is correctly bounded already; extend the same bound to the journey requirement.

---

### S5 — PBT body inlining is a bounded but *certain* cost against an *unverified* benefit; plus a factual error  [MEDIUM]

**Observed.** Property-based-testing was read in 53/339 cells and produced **0/53** detector-recognized property tests and 0/53 reference loads (`property` report; `full113-comparison.json` `property_test_cells: 0`). The `glm` change set A inlines ~250 words of oracle/generator technique into the body.

**Inference — cost.** ~250 added words, read in 53 cells, replayed ~18–25 turns → roughly **+310K–430K cache-read tokens**, certain. This is small relative to the 102.2M added total and is the right disclosure move (inline what every branch needs; the references were reached 0 times). The risk is that the benefit — converting 0/53 — is an *assumption*, not evidence; the cost is guaranteed.

**Factual error to correct.** The `glm` proposal states "97.2% of the +102.2M added tokens were cache-read." Verified value: **95.1%** (97.2M is the absolute cache-read delta; 97.2M / 102.2M = 95.1%). The `cost` evidence report stated it correctly as "97.2M (95.1%)"; the proposal conflated the absolute number with the percentage. Correct before this number propagates into the A/B guardrails.

**Required safeguard (bounded).** Ship change set A **alone** in the first A/B (both proposals recommend this) with reference-read telemetry *and* indirect property detection — the analyzer's `PROPERTY_TEST_PATTERN` is Go/Python-syntax-specific and already undercounted one Hypothesis law activation (`returns-validated-error-accumulation/rep1`). Without indirect detection, a real conversion could still read as zero.

---

### S6 — Specialist commit-gate adds a small, certain ceremony cost (acceptable)  [LOW]

**Observed.** 78 specialist-read cells. Requiring a written `Commit`/`Return` verdict on each is a few hundred tokens of certain overhead. This is well-bounded and the decline-as-peer design (next section) prevents the forcing risk. No revision required beyond carrying the non-inferiority guardrail.

---

## Retained strengths (do not weaken)

1. **Decline-as-peer is correctly scoped and does not suppress the two real specialist solve gains.** `geo-shapeindex-serialization/rep0–1` (the only fuzz-target solve flips) used a **semantic** round-trip + malformed-input rejection oracle alongside a safety decode target. The proposed fuzzing decline trigger — "the *only* oracle is 'does not panic' while the contract is semantic" — would **not** fire there, because those targets had a semantic oracle. The decline correctly targets `dasel-html-document-format/rep0–2` (panic-only campaigns, 0/146 unchanged) and `onedump/rep2` (discarded `io.ReadAll` error). Keep the "only" qualifier; it is load-bearing.
2. **"Do not optimize test-modifying-cell count downward" is correct and load-bearing.** Verified: cells with a treatment test-path modification contributed +19 net solves; cells without contributed −1 net (`cost` report). Both designs preserve this. Any cost control that suppresses test-writing attacks the mechanism.
3. **The discrimination loop (`testing` steps 2–4) is untouched in both.** It is the only mechanism with evidence of net gain (diversity §6.1). Correct to leave it alone.
4. **The one-mechanism-per-release A/B sequence on fresh held-out work, with non-inferiority guardrails on solves and preservation, is the right experimental design.** It is the only way to separate S2/S3 cost from S1/S4 correctness.

---

## Unresolved disagreements

1. **Does the contract inventory's completeness benefit outweigh its body-inflation tax on 317 cells?** The *losses* evidence (≥6 cells: full local suites green, one named clause absent — `adaptix/rep2`, `anko/rep1`, `ink/rep2`, `task/rep0`, `tengo/rep1`, `ts-pattern/rep0`) supports the inventory's existence. The *both-solved* overhead (+20.1M tokens, zero reward change) argues for gating it as tightly as possible. These pull in opposite directions; only the A/B's non-inferiority gate on the both-solved cohort resolves it. The openai draft (heavier, table-first) and the `glm` draft (lighter, row-first) are testable alternatives — they should not be merged before one is measured.
2. **Stop signal: "no change since last run" vs. "information-gated ladder."** The `cost` report proposes an information-gated validation ladder (rerun only after a change in the *result*, classified into product/runner/unrelated/expected-red). Both candidate designs instead propose "no change since last run." S1 shows the latter is unsafe for state-mutating commands; the former is more robust but harder to specify compactly. Which stop predicate to ship is unsettled.
3. **Is the PBT conversion failure a reachability defect or a disposition defect?** The `glm` thesis (inline it) assumes reachability: agents read the skill, engaged, then had no executable template. The rival reading is consistent with the same evidence: agents read PBT, judged it unsuitable for the task, and declined without articulating the decline — a disposition that inlining does not fix. The shared fact (0/53 artifacts, 0/53 references, ≥44/53 still changed tests) does not distinguish these. Only the A/B with reference-read telemetry and indirect property detection does.
