# Qwen3.6-27B trajectory review: SuperJSON and Participle

## Review

- **Correct:** All six trajectories are substantively engaged. Each begins by reading the core implementation and test architecture, identifies most of the public API, implements a large coherent patch, writes tests, and runs both build and test commands. This is not refusal, random editing, or shallow keyword matching.
- **Blocker:** Every rep stops after its own tests pass, despite leaving an untested architectural invariant broken. SuperJSON reps break annotation/property/cause semantics; Participle rep0 omits union-specific analysis and non-adjacent shadowing, while reps1–2 do not make every graph traversal cycle-safe.
- **Note:** The dominant failure is not lack of effort. It is premature convergence on a locally plausible seam, followed by self-authored tests that encode the implementation’s assumptions rather than independently re-deriving the contract.

## Scope and evidence classes

Analyzed all currently present reps (`rep0`, `rep1`, `rep2`) for:

- `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b/superjson-error-stack-serialization/`
- `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b/participle-grammar-conflict-analysis/`

For every rep I read `result.json`, the newest `session/*.jsonl`, `artifacts/model.patch`, `verifier/run.log`, `verifier/ctrf.json`, and `verifier/reward.json`. I also read the task instructions, test patch, verifier, and oracle patch under `/home/will/evals/deep-swe/tasks/`.

Evidence is labeled as:

1. **Direct session evidence** — the model’s stated reasoning and commands.
2. **Patch/verifier evidence** — observable implementation and grader behavior.
3. **Inference** — causal interpretation supported by the first two categories.

---

# 1. `superjson-error-stack-serialization`

The task’s central constraints are explicit in `/home/will/evals/deep-swe/tasks/superjson-error-stack-serialization/instruction.md:1-27`: normalize once, preserve legacy behavior only when the option is omitted, require allowed-property opt-in, distinguish three annotations, preserve pipeline order, apply class filtering per error, keep causes as Errors after round-trip, and run processors after the whole error representation is complete.

## Aggregate result

| Rep | F2P | P2P | Partial | High-level outcome |
|---|---:|---:|---:|---|
| 0 | 60/80 (0.7500) | 113/116 (0.9741) | 0.8827 | Broad feature implementation; frames and nested Error identity are broken |
| 1 | 65/80 (0.8125) | 113/116 (0.9741) | 0.9082 | Best SuperJSON rep; remaining failures cluster around causes, class filtering, and bare-path redaction |
| 2 | 20/80 (0.2500) | 116/116 (1.0000) | 0.6939 | Preserves baseline but the enhanced Error rule is not reliably integrated |

Scores are from each rep’s `verifier/reward.json`.

## Rep 0

### Orientation

**Direct session evidence.** The model explicitly decomposes the task, then reads `src/index.ts`, `src/transformer.ts`, `src/plainer.ts`, `src/types.ts`, `src/is.ts`, registries, utilities, and existing tests before editing. See the newest session at `.../superjson-error-stack-serialization/rep0/session/2026-07-09T22-42-16-553Z_019f490b-c769-7f86-8d63-c39c9a8763f9.jsonl`, assistant events 000–024. It correctly recognizes that Error serialization and `allowedErrorProps` are the critical existing seam.

**Decision made:** implement foundational modules first, then replace the Error path in `transformer.ts`.

**Decision I would make differently:** before editing, write a five-row invariant table for the existing Error rule: annotation emitted, property opt-in, nested walker behavior, deserialization identity, and custom-class precedence. Then create one characterization test for each invariant. The session read the right files but did not freeze the behavior of the seam it was about to replace.

### Seam selection

**Direct session evidence.** It initially creates JavaScript modules, converts them to TypeScript after compiler errors, and repeatedly rewrites `transformer.ts` and `index.ts` (events 027–069). It ultimately installs a dynamic `errorStackRule` ahead of `classRule`.

**Patch evidence.** `artifacts/model.patch:1800-1825` defines `errorStackRule` and places it first in `compositeRules`. This is a high-blast-radius replacement of the core Error transformation. The oracle also changes the Error seam, so the location is reasonable, but the patch does not preserve walker annotations for nested Errors.

**Decision I would make differently:** keep the existing Error transform as the single deep module and parameterize it; do not manually pre-serialize nested causes into plain objects. Any nested Error, `AggregateError.errors` item, Set item, or Map value must remain an Error long enough for the existing walker to attach an Error annotation.

### Implementation

**Direct session evidence.** The model catches and fixes several real issues: missing-mode behavior, invalid `maxStackLines`, path regex behavior, and the distinction between explicit `mode=off` and omitted options (events 104–139). This shows active contract reasoning rather than rote generation.

**Patch/verifier evidence.** Important broken behaviors are:

1. **Direct/deep causes lose Error identity.** `model.patch:1668-1700` recursively builds plain `{name, message, cause}` objects. The verifier then reports three P2P failures and multiple F2P failures such as “expected … to be an instance of Error” in `rep0/verifier/ctrf.json`. A plain nested object has no Error annotation, so deserialization cannot reconstruct it.
2. **Frames are restored to `stack`, not to the requested `stackFrames` property.** `model.patch:1764-1779` joins frames into `e.stack`; it does not restore `e.stackFrames`. This maps directly to `mode=frames round-trips stackFrames array`, container Set frames, newline-in-frames, and frame redaction failures in `rep0/verifier/ctrf.json`.
3. **AggregateError restoration is not implemented.** `model.patch:1718-1720` serializes `.errors`, but `model.patch:1781-1782` only comments that restoration is “handled by walker.” The verifier reports `.errors` missing and its items not restored.
4. **Class filtering is applied using outer serialization context, not independently for each kept cause.** The verifier shows both a class-filter miss being sanitized and a cause that should miss the filter being sanitized.
5. **Normalization default is internally inconsistent.** `model.patch:115-117` and `143-145` allow `maxCauseDepth` to remain `undefined` outside deep mode. The exported-helper test requires a numeric normalized field and fails.
6. **String-path transformation corrupts internal-frame recognition.** The failing expected value `Error: x` versus actual `Error: x\ntask_queues:1:1` shows basename redaction removed the `node:internal` marker before the later string-mode strip step. The task requires the stated order, so the redactor must retain enough of a node-internal frame for the following strip predicate.

**Decision I would make differently:** represent serialization output as `{value, annotation}` only for the current Error. Leave child Error references intact for the walker, with a depth-aware per-instance policy carried through context. On deserialization, restore both `stackFrames` and reconstructed `stack`, and instantiate `AggregateError` when `.errors` is present.

### Validation

**Direct session evidence.** It runs TypeScript compilation, `npm run build`, the full existing test suite, a large new `error-stack.test.ts`, and named-export smoke checks. It fixes its own failures until green (events 096–147).

**Patch/verifier evidence.** The model added a very large test file (`model.patch:286-1038`), but its tests encode the same plain-object cause design and do not assert hidden-contract properties such as `out.cause instanceof Error`, `out.stackFrames`, or per-cause class filtering with mismatched names. The verifier exposes 23 failures despite local green.

**Decision I would make differently:** derive tests sentence-by-sentence from the instruction before implementing. In particular, add fixed tests for: direct cause `instanceof Error`; frames preserve `stackFrames`; `AggregateError.errors[i] instanceof Error`; outer TypeError plus inner Error under `classFilter`; and string mode redaction followed by internal stripping.

### Stopping

**Direct session evidence.** After build and self-authored tests pass, the model says “Everything looks good,” commits, reruns the same suite, and stops (events 144–158).

**Inference.** The stop condition is “my implementation and my tests agree,” not “all independent contract invariants have evidence.”

**Decision I would make differently:** do not stop after a single green suite that was authored during the same trajectory. Run a second, implementation-independent contract matrix and inspect the serialized `json` and `meta.values` for every mode/container combination.

## Rep 1

### Orientation

**Direct session evidence.** Rep1 performs the most systematic SuperJSON orientation: it reads the core source, registries, tests, TypeScript config, and git state, then states a module-by-module plan. See `.../rep1/session/2026-07-09T22-58-57-417Z_019f491b-0d09-7453-a42b-fbcc8a083b71.jsonl`, events 000–025.

**Decision made:** isolate error behavior in a new `error-serialization.ts`, with helper modules and a small transformer dispatch.

**Decision I would make differently:** this is the best seam choice of the three, but I would first specify that `error-serialization.ts` must never recursively flatten an Error. Its output contract should explicitly say “child Errors remain walker inputs.”

### Seam selection

**Patch evidence.** `model.patch:210-434` introduces `error-serialization.ts`; `model.patch:1396-1441` makes `transformer.ts` delegate Error handling to it. This is a comparatively deep module with a small interface and is the strongest architectural choice across the SuperJSON reps.

**Decision I would make differently:** preserve the existing Error rule’s native nested-value traversal rather than returning fully constructed nested plain error graphs from the helper.

### Implementation

**Patch/verifier evidence.** The remaining defects are concentrated and explain the 65/80 score:

1. **Cause identity:** direct causes are serialized as plain objects (`model.patch:272-285`), so all three P2P cause tests fail `instanceof Error`.
2. **`includeCauses=none` semantics:** the patch retains legacy cause inclusion on the ordinary path (`model.patch:350-361`), although the explicit option’s default must discard causes. The verifier reports `includeCauses=none discards cause` failing.
3. **Depth normalization is limited to `deep`.** `model.patch:142-156` validates `maxCauseDepth` only when `includeCauses === 'deep'`; the contract says any present non-integer falls back to `includeCauses=none`, including direct. The corresponding direct-mode test fails.
4. **Off-by-one deep truncation:** `model.patch:272-275` recurses when `depth + 1 < maxCauseDepth`, and the verifier finds level 17 retained when the default limit is 16.
5. **Class filtering is not re-evaluated per cause.** Causes inherit the outer options, so an inner `Error` is sanitized under an outer matching `TypeError`. Both class-filter sanitization tests fail.
6. **Basename redaction only handles a narrow stack syntax.** Every hidden failure uses bare paths like `at /Users/john/...`, while the model’s local examples primarily use parenthesized paths. Five redaction tests and the processor-after-redaction test fail.

**Decision I would make differently:** make `serializeCause` return an Error reference plus remaining depth, not a plain record; validate `maxCauseDepth` independently of cause mode; and implement one path tokenizer supporting both `at /path/file:line:col` and `at fn (/path/file:line:col)`.

### Validation

**Direct session evidence.** Rep1 repeatedly runs all Vitest tests and TypeScript builds, debugs annotations through a temporary test, catches a regression caused by changing `plainer.ts`, reverts that global change, and moves to string annotations (events 098–188). This is strong iterative debugging.

**Correct:** It notices that changing walker wrapping breaks all composite annotations, and chooses a narrower fix. That is a good recovery decision.

**Gap:** Its local test suite accepts plain-object cause round-trips and misses bare path forms. The verifier’s failures are therefore not surprising edge cases; they are untested instruction examples.

**Decision I would make differently:** after reverting the walker change, add regression tests proving class annotations and all three Error annotations coexist in nested arrays/Maps/Sets. Then use literal stack strings from the instruction, not only engine-generated or parenthesized stacks.

### Stopping

**Direct session evidence.** It stops after 154 local tests pass, compilation succeeds, exports are present, and the branch is committed (events 189–233).

**Decision I would make differently:** treat “all tests pass” as insufficient when most new tests were written after the implementation. Require a checklist reconciliation against every numbered instruction paragraph, especially paragraphs 17–23.

## Rep 2

### Orientation

**Direct session evidence.** Rep2 also reads the correct core files and explicitly identifies Error transformation as the complex seam (`.../rep2/session/2026-07-09T22-58-57-420Z_019f491b-0d0c-74f8-915a-627d631d940d.jsonl`, events 000–042).

**Decision made:** replace the simple Error rule with a composite rule directly in a mostly rewritten `transformer.ts`.

**Decision I would make differently:** avoid a full-file rewrite. Introduce one enhanced Error rule beside the existing rule, prove dispatch with three metadata microtests, and only then remove the old path.

### Seam selection and implementation

**Patch/verifier evidence.** The patch is internally substantial but fails at the dispatch/contract boundary:

1. `model.patch:1600-1746` defines a composite Error rule, while `model.patch:1746` orders `classRule` before `errorRule`. The verifier shows string and frames modes frequently still produce the legacy `Error` annotation or no `stackFrames`, proving the intended rule is not consistently owning Error values.
2. Active string/frames processing adds stack data without checking the required allowed property (`model.patch:1626-1631`). Conversely, explicit off/default handling still copies `stack` from `allowedErrorProps` in some paths (`model.patch:1635-1641`). This maps to failures for mode off, missing mode, and mode-specific annotations.
3. `includeCauses=none` explicitly preserves the legacy cause (`model.patch:1645-1649`), contradicting the task and producing the cause failures.
4. Frames deserialization joins frames into `e.stack` (`model.patch:1705-1711`) but does not restore `e.stackFrames`, matching every frames round-trip/container failure.
5. Basename redaction only matches text inside parentheses (`model.patch:1095-1098`), matching the bare-path failures.
6. The local test itself states the wrong requirement: `model.patch:721-729` says `includeCauses=none includes cause via walker (original behavior)`. This is direct evidence that the implementation and its tests converged on a misread contract.

**Decision I would make differently:** when explicit `errorStack` exists, make its policy authoritative: off suppresses stack, none suppresses cause, string requires `stack` opt-in, frames requires `stackFrames` opt-in. Never blend “legacy omitted-option behavior” with “explicit option default behavior.”

### Validation

**Direct session evidence.** It runs build and baseline tests, fixes custom-class precedence and generated deserialization stacks, writes a broad test file, and reports 154 tests passing (events 085–151).

**Patch/verifier evidence.** The grader passes all 116 P2P tests but only 20/80 F2P. This means rep2 protected the old product well but validated the new behavior against incorrect local expectations. The local test comment for `includeCauses=none` is the clearest example.

**Decision I would make differently:** pause after baseline preservation and run only minimal contract tests for the new behavior. A single assertion for each annotation plus explicit opt-in would have shown the enhanced rule was not correctly integrated.

### Stopping

**Direct session evidence.** It stops immediately after its local 154-test suite passes and a CommonJS smoke test sees the named exports.

**Inference.** This rep is the strongest example of “green-suite anchoring”: the model mistakes breadth of self-authored tests for independence of evidence.

**Decision I would make differently:** inspect actual `serialize()` output for six canonical cases before committing: omitted, off+allowed stack, string without/with allowed stack, frames without/with allowed stack. Compare both `json` and `meta.values` to an explicit table.

---

# 2. `participle-grammar-conflict-analysis`

The critical constraints appear in `/home/will/evals/deep-swe/tasks/participle-grammar-conflict-analysis/instruction.md:1-49`: analyze-tag-only API, untagged `StrictMode`, FIRST/FOLLOW propagation through embeddings, union handling, lookahead suppression, negation exclusion, and three conflict classifications with locations and actionable fields.

## Aggregate result

| Rep | F2P | P2P | Partial | High-level outcome |
|---|---:|---:|---:|---|
| 0 | 88/91 (0.9670) | 153/153 (1.0000) | 0.9877 | Nearly complete; misses union analysis and non-adjacent unreachable detection |
| 1 | 14/91 (0.1538) | 153/153 (1.0000) | 0.6844 | New suite aborts on recursive grammar stack overflow |
| 2 | 14/91 (0.1538) | 153/153 (1.0000) | 0.6844 | Same suite-abort pattern through a different unguarded traversal |

## Rep 0

### Orientation

**Direct session evidence.** Rep0 reads parser nodes, options, EBNF generation, struct construction, validation, grammar/context traversal, lexer types, and tests before editing. See `.../participle-grammar-conflict-analysis/rep0/session/2026-07-09T23-42-32-712Z_019f4942-f508-75ed-b60f-dc6ef635368f.jsonl`, events 000–025.

**Decision made:** implement the entire tagged analyzer in a single `analyze.go`, with a small untagged strict-mode hook and stub.

**Decision I would make differently:** the monolithic file is acceptable for a first pass, but I would first enumerate every recursive node edge (`strct.expr`, `union.disjunction`, sequence `next`) and every conflict-producing container (`disjunction`, `union`) before writing traversal code.

### Seam selection

**Patch evidence.** `model.patch:255-282` starts analysis from `p.typeNodes[p.rootType]`; `model.patch:301-370` provides one cycle-aware walk; `model.patch:423-507` provides a separately cycle-aware FIRST computation. This is a sound seam and explains the high score.

**Correct:** Unlike reps1–2, it has explicit `visited` and `seenTypes` guards (`model.patch:286-314`), so recursive grammars terminate.

**Decision I would make differently:** model union as a conflict-owning node, not merely a traversal wrapper. The oracle has a dedicated `checkUnionConflicts` call (oracle patch around lines 433 and 560), whereas rep0 only descends into union members.

### Implementation

**Patch/verifier evidence.** Exactly three tests fail:

1. `TestAnalyzeUnionMembersWithSameFirstToken`
2. `TestAnalyzeConflictLocationWithUnion`
3. `TestAnalyzeMixedConflictsSeverities`

The first two map directly to `model.patch:359-362`: the union case loops over `nd.disjunction.nodes` but never calls `checkDisjunction` on the union disjunction. Thus no first/first conflict exists to carry a union location.

The mixed-severity failure maps to `model.patch:549-564`: unreachable detection compares only alternative `i` with `i-1`. In the test pattern `A`, `B`, `A`, the third alternative is shadowed by the first, not the immediately preceding second, so only the warning is produced and the expected error partition is missing.

**Decision I would make differently:** call the same pairwise disjunction analysis for unions, with location derived from the union member type; and compare each later alternative against all earlier alternatives for identical FIRST+EBNF shadowing.

### Validation

**Direct session evidence.** The model initially discovers infinite recursion in its own analyzer, rewrites with visited sets, fixes strict-mode global leakage by moving the flag into `parserOptions`, and runs tests with and without the tag plus compile probes for API absence (events 083–121). This is strong validation behavior.

**Gap:** Its own tests did not include a registered union with overlapping FIRST sets or a non-adjacent repeated alternative. Those are structural coverage holes, not implementation complexity surprises.

**Decision I would make differently:** build a node-kind × rule matrix. Each conflict rule should have tests at root disjunction, nested struct, embedded struct, and union. Add a three-alternative `A|B|A` case specifically for unreachable detection.

### Stopping

**Direct session evidence.** It stops after its comprehensive local tests and both tagged/untagged suites pass (events 121–138).

**Decision I would make differently:** before stopping, compare analyzer switch cases to the full node type list in `nodes.go`; for every wrapper node, answer both “do I descend?” and “does this node itself own a conflict rule?” That check would expose the union omission.

## Rep 1

### Orientation

**Direct session evidence.** Rep1 performs extensive architecture reading and plans separate files for types, report methods, engine, parser API, and strict mode. See `.../rep1/session/2026-07-09T23-56-07-084Z_019f494f-622c-7e1d-91a4-cb60ac925283.jsonl`, events 000–054.

**Decision made:** use a multi-pass analyzer, beginning with a pass that marks all nodes beneath lookahead groups.

**Decision I would make differently:** any pass over a grammar graph must be designed as a graph traversal from the first line, with a visited set parameter. Do not write a tree walk and retrofit cycle handling later.

### Seam selection and implementation

**Patch evidence.** `model.patch:44-50` calls `markLookaheadNodes(root)` before other analysis. But `model.patch:55-89` recursively follows disjunctions, sequences, groups, captures, structs, and unions without a visited guard.

**Verifier evidence.** `rep1/verifier/run.log:683-687` starts `TestAnalyzeRecursiveStructure` and terminates with “goroutine stack exceeds 1000000000-byte limit” / “fatal error: stack overflow.” The stack repeatedly names `(*analyzer).markLookaheadNodes` at `analyze_engine.go:49-77` (`run.log:698-712`). Because the Go test process aborts, 77 F2P IDs are missing from the report; the low 14/91 score is primarily suite truncation, not 77 independent semantic defects.

**Decision I would make differently:** add `visited map[node]struct{}` to `markLookaheadNodes` and `markNodeLookahead`, marking before recursion. Better, consolidate all graph walks behind one cycle-safe visitor rather than maintaining separate recursive functions with inconsistent guards.

### Validation

**Direct session evidence.** It runs both tagged and untagged suites repeatedly, writes many analysis tests, and validates API absence and strict-mode behavior. However, its local suite lacks a recursive grammar. It therefore reports all tests passing and commits (events 157–213).

**Decision I would make differently:** the first analyzer smoke test should be a self-recursive grammar under a short timeout. Then run it after every new traversal pass is added. Recursive grammar is a fundamental Participle shape, not an obscure edge case.

### Stopping

**Direct session evidence.** It stops after local green and a final verbose suite.

**Inference.** File decomposition gave an impression of architectural completeness, but each recursive helper was not audited as a graph algorithm.

**Decision I would make differently:** use a mechanical stop gate: grep/list every function accepting `node`; for each recursive one, prove a visited guard or prove it only traverses an acyclic chain.

## Rep 2

### Orientation

**Direct session evidence.** Rep2 reads essentially the same architecture and creates separate FIRST, FOLLOW, detection, report, parser, and strict files (`.../rep2/session/2026-07-10T00-00-48-371Z_019f4953-acf3-7a76-abd0-97f02bb75c4b.jsonl`, events 000–075).

**Decision made:** implement multiple recursive helpers, including `firstSet` and location-finding traversals, then validate with broad self-authored tests.

**Decision I would make differently:** define a shared cycle-safe visitor and memoized FIRST function before any conflict logic. FIRST on a recursive grammar is a fixed-point computation, not ordinary unbounded recursion.

### Seam selection and implementation

**Patch/verifier evidence.** Two unsafe paths are visible:

1. `model.patch:237-315` implements `firstSet(n)` with direct recursion through `strct`, union, groups, captures, and sequences but no visited or memoization argument.
2. The verifier’s actual first crash is location traversal: `rep2/verifier/run.log:683-687` reports stack overflow in `TestAnalyzeRecursiveStructure`; `run.log:700-712` repeatedly shows the repo `visit()` helper and `(*Parser).findContainingStruct` at `analysis_parser.go:291`. The patch invokes a generic tree visitor on a cyclic grammar graph without a guard.

As with rep1, most F2P tests are “missing from report” because the process dies, explaining the identical 14/91 score.

**Decision I would make differently:** do not use the generic `visit()` helper for recursive grammar graphs unless it supports visited nodes. Build a map from node identity to containing struct during the initial guarded traversal, and memoize FIRST with three states (`unseen`, `visiting`, `done`) to break cycles while allowing fixed-point propagation.

### Validation

**Direct session evidence.** It compiles with and without tags, probes symbol availability, runs all local tests, and even runs `go vet` (events 120–151). The local suite still omits the hidden recursive-structure case.

**Decision I would make differently:** add the exact minimal recursive type before broader report-method tests. Validation order matters: termination, then sound FIRST/FOLLOW, then report ergonomics.

### Stopping

**Direct session evidence.** It stops after both tagged and untagged local suites pass and the git status is clean (events 152–161).

**Decision I would make differently:** require a timeout-bounded recursive test and a union test as mandatory stop gates for any grammar-analysis patch.

---

# Why “normal Qwen” is engaged but does not fully solve

## Direct evidence

Across all six sessions, the model:

- reads the relevant architecture before editing;
- states an implementation plan;
- reacts to compiler and test feedback;
- catches several nontrivial regressions itself;
- writes substantial tests;
- validates tagged/untagged behavior or ESM exports;
- commits only after local green.

The sessions therefore show sustained task engagement and useful debugging ability.

## Patch/verifier evidence

The misses cluster at architectural invariants:

- **SuperJSON:** annotations and nested walker ownership, explicit-option versus omitted-option semantics, preserving Error identity, per-error class filtering, and path syntax coverage.
- **Participle:** treating the grammar as a cyclic graph, ensuring every traversal is guarded, and treating union as a conflict-bearing construct.

The highest-scoring reps demonstrate that the model can implement most surface behavior: SuperJSON rep1 reaches 65/80 F2P; Participle rep0 reaches 88/91. The failures are narrow but decisive.

## Inference

The recurring cognitive pattern is:

1. Correctly orient to the codebase.
2. Choose a plausible seam.
3. Expand implementation rapidly.
4. Author tests around the implementation.
5. Repair until those tests pass.
6. Treat local green as proof of contract completion.

The model is especially vulnerable when the underlying structure is not a tree:

- nested serialization is a walker/annotation graph, not just recursive object construction;
- grammar ASTs contain cycles, not just recursive syntax trees.

It also tends to preserve an intuitive notion of backward compatibility too broadly. In SuperJSON reps1–2, “omitting `errorStack` preserves existing behavior” is generalized into “explicit `includeCauses=none` should preserve existing causes,” directly contradicting the task.

---

# Three checkable support mechanisms tailored to this model

## 1. Contract-to-invariant ledger required before edits

Have the model produce a small machine-checkable table before implementation, then make the stop gate verify every row has an independent test.

For these tasks the required rows should include:

- SuperJSON: omitted vs explicit off; allowed-property gate; exact annotation; restored property; nested Error identity; per-cause class filter; both stack path syntaxes.
- Participle: root disjunction; union; nested struct; recursive struct; adjacent and non-adjacent shadowing; lookahead; negation.

**Check:** reject completion when any instruction sentence lacks a named test ID. This directly counters the observed tendency to let implementation assumptions define the tests.

## 2. Mandatory seam microprobes before broad implementation

Require tiny executable probes at the selected architecture seam:

- SuperJSON probe prints `json` and `meta.values` for the six canonical mode/opt-in cases, plus `out.cause instanceof Error` and `Array.isArray(out.stackFrames)` inside a Set.
- Participle probe runs one self-recursive grammar and one union grammar under a 2-second timeout before report methods are implemented.

**Check:** store probe output and require exact expected values before allowing the large patch. This is tailored to Qwen’s observed tendency to perform well once feedback is concrete but to choose a subtly wrong recursive representation initially.

## 3. Independent adversarial stop suite, not authored from the current patch

After local tests pass, run a fixed support suite generated from the task contract but maintained outside the worktree patch. It should emphasize representation changes:

- SuperJSON: bare and parenthesized paths, outer/inner errors with different names, direct/deep identity, frames property restoration, AggregateError item identity.
- Participle: every node-recursive helper exercised by a cyclic grammar; union conflicts; `A|B|A` unreachable classification.

**Check:** completion requires this second suite’s raw output, not only the model-authored suite. A static audit should also list every recursive `node` function and its visited/memoization strategy. This directly addresses the exact stopping failure in all six reps.

---

# Residual risks

- This is trajectory analysis, not a replay of the model patches in fresh containers. Verifier artifacts are authoritative for the observed outcomes.
- In SuperJSON rep2, the verifier proves annotation dispatch is wrong, while multiple interacting transformer changes make the single lowest-level dispatch cause less isolated than the other findings. The report therefore ties failures to observable rule ordering, opt-in behavior, and deserialization behavior without claiming one unverified single-line fix.
- No repository source files or result artifacts were edited. The only written file is this required review output.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete severity-tagged findings cite task instructions, all six model.patch files, verifier CTRF/reward data, and exact verifier run.log lines for both Participle stack overflows."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/ed8ad123/analysis/qwen36-27b-support-deep-dive/review_superjson_participle.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "find/ls over both result task directories and /home/will/evals/deep-swe/tasks",
      "result": "passed",
      "summary": "Located three completed reps per task and all required result, session, patch, verifier, instruction, test, and oracle artifacts."
    },
    {
      "command": "jq over result.json, reward.json, and ctrf.json for all six reps",
      "result": "passed",
      "summary": "Extracted exact F2P/P2P counts and all failing test names/messages."
    },
    {
      "command": "Python JSONL extraction over newest session files",
      "result": "passed",
      "summary": "Reconstructed assistant reasoning, tool chronology, validation, commit, and stopping decisions for every rep."
    },
    {
      "command": "grep/nl/sed over model.patch, verifier/run.log, task instructions, tests, and oracle patches",
      "result": "passed",
      "summary": "Mapped failures to exact patch behavior, including union omission, adjacent-only shadowing, plain-object causes, frames restoration, and unguarded recursive traversals."
    }
  ],
  "validationOutput": [
    "SuperJSON: rep0 60/80 F2P and 113/116 P2P; rep1 65/80 and 113/116; rep2 20/80 and 116/116.",
    "Participle: rep0 88/91 F2P and 153/153 P2P; reps1 and 2 each 14/91 and 153/153.",
    "Participle rep1 verifier run.log records fatal stack overflow in markLookaheadNodes; rep2 records fatal stack overflow through visit/findContainingStruct.",
    "Participle rep0 has exactly three F2P failures: two union cases and mixed-severity/non-adjacent shadowing."
  ],
  "residualRisks": [
    "Analysis used existing verifier artifacts rather than replaying patches in fresh containers.",
    "SuperJSON rep2 has interacting transformer-dispatch defects, so no unsupported single-line root-cause claim is made."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added only the required Markdown trajectory-review artifact; no project source, tests, results, or staged files were modified.",
  "reviewFindings": [
    "blocker: SuperJSON all reps - local green suites do not cover nested Error identity, exact annotation/property behavior, or per-cause filtering.",
    "blocker: Participle rep1 model.patch:55-89 - markLookaheadNodes recursively traverses a cyclic graph without a visited guard.",
    "blocker: Participle rep2 model.patch:237-315 and verifier run.log:683-712 - recursive FIRST/location traversal is not cycle-safe.",
    "note: Participle rep0 model.patch:359-362 and 549-564 - union conflicts are not checked and unreachable detection only compares adjacent alternatives.",
    "note: SuperJSON rep1 is the strongest SuperJSON attempt but still flattens causes and supports too narrow a basename path syntax."
  ],
  "manualNotes": "Read-only review of all currently present reps. The required output artifact is the only file written."
}
```
