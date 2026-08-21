# Minimal redesign — make property-based testing legible and executable

**Phase:** Design · **Label:** `design_glm`
**Control:** `baseline@1.1.0` vs `testing-skills@1.1.0`, GPT-5.6 Sol low, 113 tasks × 3 reps, 339 matched pairs.
**Result under test:** +18 net solves (53 gains / 35 losses), McNemar p=0.069, bootstrap 95% CI [0.0, 0.106] (touches zero), at +51.4% tokens / +33.8% cost / +16.2% wall.

This is an *alternative* design proposal. It does not edit the canonical skills;
it proposes exact wording for approval and a follow-up A/B.

---

## Synthesized diagnosis

The evidence reports converge on one story, confirmed by direct read of the skill
sources and the comparison artifact:

1. **The active ingredient is `testing`'s step-4 discrimination loop** (diversity
   report §6). Net gain is concentrated in cells where the treatment added a
   test-bearing patch (cells with a treatment test-path: +19 net; without: −1 net;
   `cost` report). Preserve it.
2. **The specialists pay full context cost for ~zero delivered technique.**
   PBT: read in 53/339, loaded **0/53** disclosed references, wrote **0/53**
   leverage sentences, contracts, oracles, or counterfeits, yet changed tests in
   ≥44 of them (`property` report; `full113-comparison.json` delivery). The model
   reads the body, then proceeds with ordinary examples anyway.
3. **PBT's executable technique is entirely behind disclosed references.** Steps
   3 and 4 of the current body say "Load [reference]" for oracle design
   (`designing-properties.md`, 856 words) and generator/shrink design
   (`generators-and-shrinking.md`, 756 words). **Both were reached 0 times.** The
   body that stays loaded is a *router description*, not an executable process —
   so a model that does not naturally reach for PBT never sees what a property
   actually *is*.
4. **The first completion criterion is not behaviorally binding.** "Complete when:
   all three blanks are concrete" can be satisfied mentally; nothing observable is
   committed, and implementation displacement takes over (writing-for-agents:
   premature completion under a fuzzy bound with visible post-completion steps).
5. **Fuzzing converts better (7/49, 2 genuine solve gains) but over-routes** —
   48/49 reads fire within the first five tool calls, before a seam, oracle, and
   engine are confirmed (`fuzzing` report).
6. **`testing` competes with the specialists after the handoff.** Keeping it
   loaded replays its 1,202-word body for no added discrimination; 97.2% of the
   +102.2M added tokens were cache-read (`cost` report).

**Structural fact that makes this cheap:** a skill's `description` is
always-loaded (present in `system_prompt.txt` in all 339 cells); the **body loads
only on read**. So inlining the executable minimum into the PBT body costs tokens
in ~53 cells, while it replaces ~1,612 words of references reached **0 times**.
Inlining is the correct disclosure move (writing-for-agents: "inline what every
branch needs; disclose what only some branches reach") and nearly free at the
margin.

---

## Design principles (the levers)

- **P0 — make PBT executable in-file.** Inline the minimum a model needs to write
  its first property: the commit-or-decline gate, one quantified contract shape,
  the compressed oracle menu, and generator/shrink basics. Keep framework
  adapters and stateful/advanced material disclosed (genuinely branch-specific).
- **Protect ordinary example tests.** Decline is a peer outcome of reading PBT,
  not a failure. Most behavior (≈296/339 cells) is better served by examples.
- **No forced specialist use.** The gate is `property` OR `decline`, both
  completing the step. Specialists stay model-invoked (the router needs to reach
  them; they netted +6 in their read cohort, post-selection).
- **Preserve `testing`'s discrimination loop.** Touch only the framing and the
  validation step; add the three highest-evidence, smallest-interface bars.
- **Bound the loop.** Add a stop condition so the discrimination loop stops
  leaking spend on non-flips (the #1 cost lever) without a hard call cap.
- **Make the handoff exclusive.** When a specialist accepts the surface, `testing`
  stops competing; when it declines, control returns to examples.

---

## Change set A — `property-based-testing` (the priority)

> Replaces the current body (description + "Choose the branch" + Process §1–6 +
> Product seams) in full. Lines carrying the never-loaded oracle/generator
> technique now live in-file; framework adapters, stateful, advanced, review, and
> triage references stay disclosed.

### A.1 Frontmatter (description) — front-load the decision, collapse synonyms

**Current**
```yaml
description: Property-based testing for implementation and test work with broad structured behavior. Use when a feature or bug spans input combinations, round trips, encoding and decoding, serialization, normalization or idempotence, ordering or pagination, schema variants, stateful operation sequences, distributed or concurrent schedules, parsers or codecs with semantic invariants, or differential models; also use when designing or reviewing generators, shrinkers, properties, and counterexample handling.
```

**Proposed**
```yaml
description: Generated-domain search for implementation and test work. Reach when a broad domain and a compact, independent oracle create search leverage that explicit examples cannot — round trips, encode/decode, normalization or idempotence, ordering or tie-breaks, schema variants, stateful operation sequences, or differential models. Decline to the testing skill's examples when the meaningful cases are a small table or the only oracle would duplicate the implementation.
```

*Rationale:* leads with the leverage concept (priming the decision), keeps the
shape-list as recall, names the decline path in the pointer itself so the model
sees both outcomes before reading.

### A.2 Body — commit-or-decline gate + inlined executable core

```markdown
# Property-based testing

A property test searches a quantified domain for a counterexample and shrinks
failures to a replayable case. A green run is evidence over the searched cases,
not proof over every value. Most behavior is better served by the `testing`
skill's explicit examples; reach property testing only when a broad domain and a
compact oracle create search leverage that examples cannot.

## 1. Commit or decline

Decide before writing production code. Both outcomes complete this step.

- **Property** — write the leverage sentence, with every blank concrete:
  > Generate **[domain]** to challenge **[risk]**, checked by **[oracle]**.
  Continue to step 2.
- **Decline** — return to the `testing` skill's example process. Name one reason:
  the meaningful cases are a small explicit table; the only oracle would
  duplicate the implementation's decisive logic; effects cannot be isolated
  within the test budget; or no property-testing dependency is available and
  adding one is not authorized.

**Complete when:** the trajectory contains either the concrete leverage sentence
or one named decline reason. A mental decision that writes neither is incomplete.

## 2. State the property

Write the quantified contract before its test code:

> For every `x` in domain `D` satisfying precondition `P`, observing the system
> produces relation `R` under equivalence `≈`.

Ground `D`, `P`, `R`, and `≈` in specifications, public documentation, types,
callers, and established tests. Separate supported inputs from invalid inputs
when their contracts differ, including the required error or rejection.

**Complete when:** every term has a source, and `≈` is defined (structural,
semantic, multiset, normalized-key, or numeric tolerance). An undefined
equivalence turns round trips and differential tests into ambiguous bug reports.

## 3. Choose an oracle

An oracle is an observation that can fail. For each property, name one
counterfeit implementation it must reject.

- **Postcondition or verifier** — check the result against a cheap invariant:
  sorted output is ordered and preserves the multiset; a solver's witness meets
  every constraint; a parsed tree has valid spans.
- **Differential or model** — agree with an independent reference (a language
  builtin, an alternate algorithm, a specification interpreter):
  `optimized(x) ≈ reference(x)`. A copied algorithm or shared decisive helper can
  preserve the same bug on both sides, so independence matters more than size.
- **Round trip** — `decode(encode(x)) ≈ x`. Generate both directions when both
  matter; encoder output often covers only a canonical subset of what the decoder
  accepts.
- **Metamorphic** — relate observations under a controlled transformation
  (permutation, translation, decompose-then-recombine):
  `observe(f(transform(x))) ≈ transform_observation(observe(f(x)))`.
- **Preservation** — an operation keeps something invariant while changing
  something else. Pair it with an observation of the intended change, or a
  constant function can pass.
- **Algebraic law** — associativity, idempotence, commutativity, identity, only
  when the actual type and equivalence promise them. Floating point, ordering,
  and side effects often break textbook laws.
- **Invalid-input** — search the complement of the valid domain and assert the
  required error, rollback, or absence of partial mutation.

"No crash" is a complete oracle only when availability over arbitrary untrusted
input is the whole contract; otherwise pair it with the stronger postcondition.

**Complete when:** every property has a grounded relation, an observable oracle,
and a named counterfeit it rejects.

Load [designing properties](references/designing-properties.md) for the full
oracle catalog, equivalence guidance, and the counterfeit checklist.

## 4. Generate the domain

Generate from the supported contract, not from production-looking samples. Keep
every supported value reachable; add size bounds only for the contract or
measured cost.

- Separate generators for materially different contracts: supported values,
  invalid values to reject, legacy representations.
- Generate dependencies jointly — `(lower, upper)` with `lower <= upper`, a key
  known present, a legal next command — rather than independent values you hope
  connect. Joint generation raises valid-case density and exposes collisions that
  independent wide ranges make vanishingly rare.
- Preserve small values: they diagnose and find boundary defects.
- Use the framework's native combinators so generation and shrinking stay
  coupled; filtering, mapping, flat-mapping, and mutable inputs shrink
  differently across frameworks.

For a stateful contract where correctness depends on operation history, load
[stateful and concurrent testing](references/stateful-and-concurrent-testing.md)
and model commands, preconditions, transitions, and postconditions.

**Complete when:** the claimed domain is reachable, dependencies are generated
jointly, a planted failing predicate shrinks to a stable intelligible case, and
measured runtime fits the test loop.

## 5. Write it in the framework

Load the adapter for the repository's installed framework for exact syntax and
shrinking semantics:

- Python/Hypothesis — [Hypothesis adapter](references/frameworks/hypothesis.md)
- JavaScript or TypeScript/fast-check — [fast-check adapter](references/frameworks/fast-check.md)
- Rust/proptest — [proptest adapter](references/frameworks/proptest.md)
- Go/rapid — [rapid adapter](references/frameworks/rapid.md)
- Java/jqwik — [jqwik adapter](references/frameworks/jqwik.md)
- Another ecosystem — [other frameworks](references/frameworks/other-frameworks.md)

Reuse the existing dependency and project test conventions. When no
property-testing dependency exists, follow the repository's dependency policy and
present the leverage sentence before changing the manifest. For a tractable
finite domain, exhaustive enumeration is honest evidence — label it as
enumeration, not property-based testing.

## 6. Prove discrimination

Run the property against the pre-fix defect or a temporary plausible mutant. A
green property against its named counterfeit has not earned confidence. Keep
mutations local and out of the final change.

Inspect the shrunk counterexample: it should explain the violated relation, not
merely be small. Keep a durable explicit example when a minimized case
communicates a named boundary better than replay metadata.

**Complete when:** the property goes red on the target defect and on every
counterfeit that can be safely simulated, or the unproven counterfeit is recorded.

## 7. Operate

Run the repository's normal test command with the project's existing settings
first; adjust search effort only from measured runtime and observed reach.
Preserve replay data for failures and use
[triaging counterexamples](references/triaging-counterexamples.md) before changing
production code.

**Complete when:** the corrected implementation is green, the search fits the
suite budget, the failure is replayable, and the ordinary example-based tests
still pass.
```

**Dropped:** the standalone "Product seams" footer (router report: it duplicates
`testing`'s example-preservation guidance, redundant once `testing` is loaded).
Its single load-bearing line — properties add domain search rather than replacing
useful examples — now lives in the opening paragraph.

### A.3 Evidence and counterexamples for change set A

| Change | Evidence (paired cells) | Counterexample preserved |
| --- | --- | --- |
| Commit-or-decline gate as step 1, observable artifact required | All 53 PBT reads wrote **0** leverage sentences/contracts/oracles/counterfeits and proceeded to examples (`property` report). `returns-validated-error-accumulation/rep1` read PBT, used repo-native law checks, solved — but recorded no counterfeit/replay. | `effect-sse-httpapi-streaming/rep1` and `expr-try-catch-errors/rep0`: real boundaries / no independent model where decline is correct. Decline stays a peer outcome. |
| Inline oracle menu (was `designing-properties.md`, 0 reads) | `prometheus-typed-label-sorting/rep0–1` modeled a single-unit quantity and missed compound/global ordering; rep2 solved after explicitly covering the compound grammar. `arktype-json-schema-refs-dependencies/rep0` framed recursive caching + deep structural comparison and closed 25/25. | `psd-tools-blend-range-api/rep2` read the same skills and reversed 45→37; `sql-formatter-bigquery-pipe-formatting/rep1` read all three and produced no patch. Inlining raises reach, not correctness. |
| Inline generator/shrink basics (was `generators-and-shrinking.md`, 0 reads) | `csstree-shorthand-expansion-compression/rep2` added a 256-case nested round-trip loop with no generator/shrinker; `tomlkit-toml-table-converters/rep1` added fixed round trips, no generator. | `fd-deterministic-multi-key-sorting/rep1` had no proptest dependency and still solved with explicit cases; enumeration is named as honest weaker evidence, not forbidden. |
| Keep adapters/stateful/advanced/review/triage disclosed | Framework syntax is genuinely language-conditional; stateful cases are a minority branch. | `returns…/rep1` reused existing Hypothesis infra without an adapter read; `geo-shapeindex-serialization/rep0` built a valid Go target without the Go adapter. Adapters must stay optional, not gates. |

---

## Change set B — `testing` (preserve the loop; add three small bars + bound it)

> Edits the framing and the validation step only. Steps 2–4 (Choose surface,
> Build independent test, Prove discrimination) are untouched — they are the
> active ingredient.

### B.1 `Route before choosing examples` — exclusive, auditable handoff

**Current (opening)**
> Reading this skill starts test selection; it does not imply that explicit examples are the right surface. Inspect the requested contract and relevant code enough to choose every matching branch. Load each matching specialist before framing the evidence; language references supplement that choice.

**Proposed**
> Reading this skill starts test selection; it does not imply that explicit examples are the right surface. Inspect the requested contract and relevant code enough to choose every matching branch. Load each matching specialist before framing the evidence; language references supplement that choice.
>
> When a specialist **accepts** the surface — it writes its leverage sentence (`property-based-testing`) or campaign contract (`fuzzing`) — stop this skill's generic example sequence for that risk; the specialist owns the test surface. When a specialist **declines** — it names why examples are narrower — return to this process. Keeping both loaded after the handoff replays context for no added discrimination.

### B.2 Step 1 — add a contract inventory before framing (new leading demand)

**Current step 1** is "Frame the evidence" with a single `Behavior/Risk/Seam/Oracle/Counterfeit` block.

**Proposed** (split into an inventory lead, then the frame with a preservation line)
```markdown
## 1. Inventory and frame

List every behavior, boundary, interaction, and non-code deliverable the request
names before choosing examples — one row per independently observable clause. A
request with several observable clauses is not discharged by one representative
test. Treat several clauses as one row only when you can state the invariant
that lets a single observation cover them.

Then write the test claim before writing test code, one block per row:

```text
Behavior: <observable contract>
Risk: <plausible failure this test should expose>
Seam: <public input and observation point>
Oracle: <independent source of the expected result>
Counterfeit: <wrong implementation or defect that must make the test fail>
Preservation: <existing behavior that shares this changed boundary>
```

Ground the contract in specifications, public documentation, types, callers,
accepted behavior, and existing tests. Treat names and comments as search leads,
not proof. If selecting the seam would change scope or expose a new production
interface, confirm that decision before writing the test.

**Complete when:** every requested clause has a row (including preservation of
existing behavior on a shared boundary), every field is concrete, and the
counterfeit could plausibly survive without this test.
```

### B.3 Step 5 — outer-surface evidence, final patch-relative ordering, stop condition

**Current step 5** is "Validate and operate."

**Proposed**
```markdown
## 5. Validate and operate

Run the narrow test while iterating. For every new or renamed test, use runner
collection, listing, or focused execution output to confirm the intended command
selects it. Account for focus, skip, todo, tag, feature, and exclusion markers;
a green suite does not prove an unseen test ran.

Exercise every outermost changed surface. For each user-facing entry point,
runnable artifact, serialized boundary, or downstream package the request
changes, run at least one journey through that surface. Narrower unit tests
localize faults; they do not replace evidence through the outer surface the
request names.

Then run the repository's required type checks, linters, and full test suite
once the change is complete. When order, concurrency, retry, or shared state
matters, also repeat the test under the relevant seed, order, worker count, or
scheduler.

**Final-evidence rule.** After the last production mutation, run the target test
and the nearest regression suite on the final patch. A failed, timed-out,
skipped, or zero-test command leaves the behavior unverified. Do not replace a
broad failed result with a narrower green command; continue, roll back, or report
the limitation. A commit, lint, or formatting command is operational, not
validation.

**Stop testing when** the discriminating test is green for the named reason, the
affected-scope suite is green, and the required broad suite has run once on the
final patch. Re-run a command only after a change that could affect its result.

Use coverage to locate unexercised risk, not as a target by itself. Use mutation
testing on changed or risk-bearing code when the tool exists and survivors can
become concrete test goals.

**Complete when:** new and renamed tests are collected, every outer changed
surface has journey evidence, the final patch's target and regression commands
are green, relevant nondeterminism has been stressed, and failures leave enough
context to reproduce.
```

### B.4 Evidence and counterexamples for change set B

| Change | Evidence (paired cells) | Counterexample preserved |
| --- | --- | --- |
| Contract inventory (B.2) | `losses` pattern 1: `adaptix/rep2`, `anko/rep1`, `ink/rep2`, `task/rep0`, `tengo/rep1`, `ts-pattern/rep0` — full local suites green, one explicit clause absent each. `nonflips` finding 1: `participle/rep0–1` ran suites repeatedly yet feature coverage fell to 14/91. | `aiomonitor-task-snapshots-diff` reached 51/53 across reps with only one durable test — the inventory must accept existing/transient evidence, not force a new test file per clause (escape hatch: the covering invariant). |
| Outer-surface evidence (B.3) | `textual-richlog-follow-state/rep0–2`: the only 3/3 repeated loss; widget checks green, the exact example journey failed identically every rep; baseline solved all three. `vulture/rep1`, `kgateway/rep2`, `helm/rep0`: narrow tests green, the changed outer command/regression wrong. | `query-persist-restored-query-state/rep2` and `psd-tools-blend-range-api/rep0` solved *by* crossing the persistence/compositing surfaces — the rule demands the journey, which is exactly what helped them. |
| Final patch-relative ordering (B.3) | `losses` pattern 6: `numba/rep1` (final one-line unrelated patch, 0/29), `sql-formatter/rep1` and `opa/rep0` (empty patch, no grading), `helm/rep0` + `kgateway/rep2` (broad fail → narrower green → success claim). | `prometheus/rep2` ended with its changed package green and solved; commit-author failures in many solved cells are operational. The rule classifies (operational vs validation), it does not blanket-fail. |
| Stop condition (B.3) | `diversity` §6.2 / `cost` finding 3: the discrimination loop has no budget bound; ~$63 of non-flip spend leaks via repeated green suites. `helm-array-merge-strategies/rep0` 30→61 calls, 0.48M→2.20M tokens, regressed. | `query-persist/rep2` (16 validation commands, solved) and `dynamodb-toolbox-lazy-recursive-schemas/rep0` (16, solved): failures changed and closed. No hard call cap; the gate is "no change since last run." |
| Preservation line (B.2) | `gains` pattern 3: 9 cells flipped incomplete→complete preservation, 0 the reverse. `pebble-durability-wait-apis/rep2` 44/44 vs 38/44 on identical production surface. | `query-persist/rep1` (41/42 vs 42/42), `vulture/rep1–2` (collection drift despite validation): the line makes preservation explicit, it does not guarantee it. |
| Exclusive handoff (B.1) | `router` finding 1; `cost`: 97.2% of added tokens were cache-read — keeping `testing` loaded after the specialist handoff is pure replay cost. | `arktype/rep0` and `cliffy-config-file-parsing/rep2` won without specialist artifacts — control returns to examples on decline, so the example path is untouched. |

---

## Change set C — `fuzzing` (admission ordering, decline-as-peer, bounded local completion)

> Fuzzing converts better than PBT (7/49, 2 solve gains) so the body needs less
> surgery. Three targeted edits.

### C.1 Frontmatter — bake the ordering into the pointer

**Current**
```yaml
description: Coverage-guided fuzzing for implementation and test work on input-processing and memory-safety boundaries. Use when a feature or bug touches parsers, lexers, decoders, deserializers, codecs, file formats, protocol handlers, malformed, chunked, or adversarial input, unsafe or FFI code, or crash, hang, and resource-exhaustion risks; also use when designing or running fuzz targets, engines, oracles, seeds and corpora, coverage campaigns, crash minimization, and regression conversion.
```

**Proposed**
```yaml
description: Coverage-guided search for implementation and test work at a production input boundary. Reach after inspecting the code when a direct deterministic seam, a crash/hang/resource or compact-semantic risk, an oracle that detects it, and a supported engine are all concrete. Decline when the meaningful cases are a small explicit table, when property-based testing is the better search, or when the only oracle is "does not panic" while the contract is semantic.
```

### C.2 Step 1 — inspect first, then commit or decline

**Current step 1** opens "Write the campaign contract before the harness" with the six-field block.

**Proposed** (lead with ordering, add the decline branch)
```markdown
## 1. Frame the campaign

Inspect the production input boundary before committing to a campaign. Then write
the contract:

```text
Target: <narrow production entry point, reached directly>
Risk: <crash, undefined behavior, hang, resource exhaustion, or semantic defect>
Input model: <bytes, structured value, or operation sequence>
Oracle: <observable failure condition that detects the risk>
Engine: <existing project tool or justified choice>
Budget: <local smoke, bounded campaign, or continuous service>
```

**Decline** when any field stays abstract: the meaningful cases are a small
explicit table (use the `testing` skill); broad structured values or operation
sequences make property-based testing the better search; the only oracle is "does
not panic" while the dominant contract is semantic; or the harness would require
unrelated system startup, network, durable state, dependency additions, or
toolchain upgrades. A named decline is a complete outcome.

Good targets include parsers, decoders, protocol and file-format handlers,
compression or serialization code, unsafe memory operations, and FFI boundaries.
Choose by search mechanism and oracle fit, not category labels.

**Complete when:** every field is concrete and the target owns enough behavior to
expose the risk without booting an unrelated system, or one decline reason is named.
```

### C.3 Step 5 — a local smoke is a complete outcome

**Current step 5** leads to a bounded local or CI campaign; step 7 ("Operate continuously") is always visible.

**Proposed** (add a local-smoke finish line; keep continuous disclosed/optional)
```markdown
## 5. Run and record the campaign

Run ordinary regression tests first; seed replay should already be green. Start
with a single-worker smoke within the declared wall budget. A clean smoke —
representative seeds replay deterministically, the oracle detects the named risk,
and ordinary tests pass — is a complete local outcome. Stop after it unless the
target is security-sensitive or heavily exposed.

For a bounded local or CI campaign, use the engine's documented worker model
rather than ad hoc copies; do not inherit unconstrained worker defaults. Record
the source revision, engine and compiler versions, sanitizer or instrumentation
mode, target, corpus, dictionary, worker count, maximum input size, timeout, and
replay command where available.

[existing coverage paragraph unchanged]

**Complete when:** for a local smoke, a single-worker run stays within the
declared wall budget with its command and elapsed time recorded, representative
seeds replay deterministically, the oracle detects the named risk, and ordinary
tests pass. For a bounded campaign, another developer can reproduce the
configuration and replay its corpus without the active fuzzer.
```

Move "Operate continuously" to a disclosed reference or gate it behind
"security-sensitive or heavily exposed targets" so it stops competing with the
local-smoke finish line in every read.

### C.4 Evidence and counterexamples for change set C

| Change | Evidence (paired cells) | Counterexample preserved |
| --- | --- | --- |
| Inspect-first ordering (C.1, C.2) | `fuzzing` report: 48/49 reads fired within the first five tool calls, 36 within the first two, before production-code inspection. | `wazero-multi-module-snapshots/rep2` read fuzzing *after* inspection, declined a costly target, and solved — late routing is still a useful audit. Admission gates the *campaign*, not the read. |
| Decline-as-peer (C.2) | `dasel-html-document-format/rep0–2`: panic-only campaigns (~104k–229k execs) found nothing, all 146 feature checks unsatisfied. `onedump/rep2` fuzzed authenticated decode but discarded the `io.ReadAll` error — passed while 11 checks failed. `termenv/rep0` had a real width invariant but the target missed wrapper/default-option semantics. | `geo-shapeindex-serialization/rep0–1`: narrow safety-oracle decode fuzzing alongside complete implementation + explicit tests produced the 2 solve gains. A narrow safety oracle is not useless; it is insufficient when the dominant contract is semantic. The decline names that condition. |
| Bounded local completion (C.3) | The 16-worker default produced an ambiguous OOM in one cell (`fuzzing` report). Continuous operation is visible even for local-smoke branches, offering no finish line. | All six active Go campaigns passed without resource flags; one 5s campaign took 9.57s and was fine. The rule records command+elapsed and stops after a clean smoke — it does not ban multi-worker campaigns that justify them. |

---

## Deliberately not changed

- **`testing` steps 2–4** (Choose surface, Build independent test, Prove
  discrimination). The discrimination loop is the confirmed active ingredient
  (diversity §6.1). Touching it risks the only mechanism with evidence of net
  gain.
- **Specialist model-invocation status.** They must stay auto-discoverable so the
  router can reach them; making them user-invoked removes the only auto path and
  the read cohort netted +6 solves (post-selection, but non-negative).
- **Framework adapters, stateful/advanced/review/triage references.** Genuinely
  branch-specific (per language / stateful minority / review-or-triage path).
  Correct disclosure per the branching test.
- **The `testing` review checklist.** The router report flags it as the likeliest
  low-value duplication, but pruning it is independent of the efficacy levers and
  carries its own risk; defer to a separate cleanup pass so its effect stays
  isolated.

---

## Risks and how the next A/B measures them

1. **PBT body length adds cache-read cost in ~53 read cells.** It replaces
   ~1,612 words of references reached 0 times; conversion (currently 0/53) is the
   goal. *Measure:* reference-read telemetry + direct/indirect property detection
   (the analyzer's `PROPERTY_TEST_PATTERN` undercounts — `returns…/rep1`
   activated a Hypothesis law runner it missed).
2. **Contract inventory could inflate effort on simple single-clause tasks.**
   Escape hatch: "treat several clauses as one row only when you can state the
   covering invariant." *Guardrail:* non-inferiority on solves + preservation;
   watch per-cell token delta on the both-solved cohort.
3. **Stop condition could truncate a converging loop.** No hard call cap; the
   gate is "no change since last run." *Counterexample preserved in design:*
   `query-persist/rep2`, `dynamodb/rep0` (16 commands, solved because failures
   changed).
4. **Exclusive handoff could drop `testing` framing too early.** Handoff fires
   only on specialist *accept* (leverage sentence/contract written); decline
   returns to examples. *Guardrail:* track cells where a specialist was read but
   no accept/decline artifact appears.

**Recommended one-mechanism-per-release sequence on fresh held-out work:**

1. PBT commit-or-decline + inlined executable core (change set A — the priority).
2. `testing` contract inventory + final-evidence rule + stop condition (B.2, B.3).
3. `fuzzing` admission/decline + bounded local completion (change set C).

Optimize: cache-read tokens, cost, repeated no-information validations, and
**PBT read→commit conversion** with reference-read telemetry. Do **not** optimize
test-modifying-cell count downward — the net gain is concentrated there.
