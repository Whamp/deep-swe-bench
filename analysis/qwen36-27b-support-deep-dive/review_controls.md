# Normal Qwen 3.6 27B matched-control review

## Review

- **Correct:** The clean normal-Qwen configuration is genuinely prompt-clean: it has neither `system_preamble.md` nor `orchestration.md` and pins the requested sampling tuple (`configs/baseline-qwen36-27b/README.md:7-14`; `configs/baseline-qwen36-27b/extensions/local-vllm-qwen36-sampling.ts:5-12`).
- **Correct:** The strict same-model comparison contains **six overlapping task/rep cells**, all `rep0`. The clean root had 18 completed results (six tasks × three reps) at the analysis snapshot; the historical root has only `rep0`. No nonmatching rep was treated as paired evidence.
- **Correct:** Normal Qwen does not exhibit the ThinkingCap early non-action pathology in these data. Clean normal Qwen entered the tool loop in 18/18 completed cells, made a patch in 18/18, and used edit/write tools in 18/18. In the strict historical pairs it entered tools in 6/6; its one empty result still made 24 tool calls, so it was not a first-turn refusal (`results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-preamble-orchestration/langchain-request-coalescing/rep0/result.json:52-64`).
- **Note — high support priority:** The normal model's clearest controlled weakness is **contract completion after active implementation**, not failure to start. Across the 18 clean cells it produced no binary solve, although all 18 patched and 16 reached verifier exit 0; mean partial reward was 0.7914. This is especially strong on recursive delegation: all three clean reps have F2P=0 and P2P=1 with identical partial reward 0.815789, and the historical matched cell has exactly the same verifier outcome. Representative evidence is `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b/claude-code-by-agents-recursive-delegation/rep0/result.json:61-80` and `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-preamble-orchestration/claude-code-by-agents-recursive-delegation/rep0/result.json:44-64`.
- **Note — medium support priority:** The model is **variable on broad, multi-clause tasks**. Clean `participle` F2P was 0.967/0.154/0.154 across reps; clean `superjson` F2P was 0.750/0.812/0.250. The historical `rep0` values were 0.132 and 0.812 respectively. Thus prompt removal did not uniformly fix or break contract coverage: it yielded one excellent `participle` sample while two remained close to the historical miss, and `superjson` spanned better/equal-to-historical through substantially worse.
- **Note — medium support priority:** `langchain-request-coalescing` shows **completion/time-budget fragility**, but not early non-action. Clean normal Qwen made nonempty patches in all three reps, yet two timed out and only one was scored (partial 0.986, F2P 0.92). Its matched clean `rep0` made 53 tool calls and a 42,134-byte patch before timing out (`.../baseline-qwen36-27b/langchain-request-coalescing/rep0/result.json:61-80`). Historical `rep0` stopped with no diff after 24 tool calls (`.../baseline-preamble-orchestration/langchain-request-coalescing/rep0/result.json:44-64`). This supports a task-specific reliability concern, not a causal claim about either prompt.
- **Note:** No blocker was found in the result evidence itself. The main limitation is design: prompt, output cap, and sampling changed together, so observed deltas are not causal prompt effects.

## Scope and controls

### Strict normal-Qwen matched set

The overlap of completed `result.json` keys was:

1. `claude-code-by-agents-recursive-delegation/rep0`
2. `dateutil-rfc5545-timezone-interop/rep0`
3. `langchain-request-coalescing/rep0`
4. `obsidian-linter-link-format-conversion/rep0`
5. `participle-grammar-conflict-analysis/rep0`
6. `superjson-error-stack-serialization/rep0`

The clean root also had reps 1–2 for those six tasks. They are used only to assess within-config repeatability, not as historical pairs. `go-critic-doc-link-checker/` existed in the clean root but had no completed `result.json` at the snapshot and was excluded.

### Why this is not a causal prompt A/B

| Surface | Clean normal Qwen | Historical normal Qwen |
|---|---:|---:|
| Extra prompt | none | 639-byte preamble + 62-byte orchestration text |
| Model | same AWQ/BF16/INT4 leaf | same AWQ/BF16/INT4 leaf |
| Max output tokens | 81,920 (`configs/baseline-qwen36-27b/Qwen3.6-27B-AWQ-BF16-INT4/high/models.json:22`) | 16,384 (`configs/baseline-preamble-orchestration/Qwen3.6-27B-AWQ-BF16-INT4/high/models.json:18`) |
| Sampling | explicit temperature 1.0, top-p .95, top-k 20 | no equivalent sampling extension recorded in the config |
| Preserve thinking | yes | yes |

The historical text explicitly tells the model to read code, make focused edits, run tests, iterate, and commit (`configs/baseline-preamble-orchestration/system_preamble.md:1-11`). Any difference can therefore reflect prompt, sampling, output cap, date/runtime state, or stochasticity.

## Paired normal-Qwen results

### Aggregate behavior, six strict pairs

| Metric | Clean prompt-free | Historical prompt-bearing | Observed delta |
|---|---:|---:|---:|
| Tool-loop entry | 6/6 | 6/6 | none |
| Nonempty patch | 6/6 | 5/6 | +1 clean |
| Mean turns | 69.5 | 55.2 | +14.3 clean |
| Mean tool calls | 77.3 | 62.7 | +14.7 clean |
| Read calls | 102 total (17.0/cell) | 113 (18.8/cell) | slightly fewer clean |
| Edit + write calls | 110 total (18.3/cell) | 84 (14.0/cell) | more clean |
| Explicit test-runner calls | 57 total (9.5/cell) | 39 (6.5/cell) | more clean |
| Patch files | 26 total (4.33/cell) | 24 (4.00/cell) | similar/slightly broader clean |
| Added patch lines | 7,597 total (1,266/cell) | 4,926 (821/cell) | substantially broader clean |
| Deleted patch lines | 156 total | 116 | broader clean |
| Test files touched | 7 total across 5 cells | 4 across 4 cells | more clean |
| Binary solves | 0/6 | 0/6 | none |
| Mean partial reward | 0.77893 | 0.73138 | +0.04755 clean |
| Mean scored F2P | 0.6858 | 0.5218 | +0.1640 clean |
| Mean P2P | 0.99483 | 0.99483 | identical |
| Verifier disposition | 5 scored, 1 timeout | 5 scored, 1 skipped empty | different failure mode |

Patch files/lines were parsed from each `artifacts/model.patch`. Tool counts came from each `session/*.jsonl`. “Explicit test-runner” counts only shell calls invoking recognizable runners such as `pytest`, `go test`, `npm test`, `vitest`, or `jest`; it does not infer whether every composite command ultimately passed.

### Outcomes by pair

| Task | Clean partial / F2P / P2P | Historical partial / F2P / P2P | Read |
|---|---:|---:|---|
| Claude recursive delegation | .8158 / .000 / 1.000 | .8158 / .000 / 1.000 | exact tie; persistent contract miss |
| dateutil timezone interop | .9967 / .896 / 1.000 | .9914 / .731 / 1.000 | clean higher |
| langchain coalescing | 0 / n/a / n/a, timeout after patch | 0 / n/a / n/a, empty after work | tie, different failure mode |
| Obsidian link conversion | .9908 / .817 / 1.000 | .9966 / .933 / 1.000 | historical higher |
| participle conflict analysis | .9877 / .967 / 1.000 | .6762 / .132 / 1.000 | clean much higher |
| SuperJSON error stacks | .8827 / .750 / .974 | .9082 / .812 / .974 | historical higher |

The clean mean gain is driven primarily by `participle`; pairwise there are two clean wins, two historical wins, and two ties. Neither configuration solved a strict pair. It would be an overclaim to describe the prompt-free configuration as categorically better.

## Tool-loop, edits, patch breadth, and tests

The controls reject an “insufficient action” diagnosis for normal Qwen:

- Clean normal Qwen started with tools in all 18 completed cells; none had one turn, zero tools, or an empty patch.
- The strict clean cells did **more**, not less, than historical cells: +26 edit/write calls, +18 test-runner calls, and +2,671 added lines in aggregate.
- This extra activity did not yield a binary solve. Support that merely says “inspect the repo,” “write tests,” “keep working,” or “use tools” duplicates behavior already present.
- Reads were not absent (17/cell clean versus 18.8 historical), but clean shifted relatively more effort into implementation. That is compatible with a need for better requirement-to-test mapping, though it does not by itself prove deficient reading caused misses.
- P2P remained essentially perfect while F2P lagged. The patches generally preserved existing behavior but did not satisfy all new requirements. That is the strongest verifier-level signature for targeted contract checking.

## ThinkingCap contrast: early non-action is not normal Qwen's weakness

ThinkingCap is used only as a failure-shape contrast because it changes the model and sampling lineage.

| Root | Completed cells | Never entered tools | Empty patches | Any edit/write | Binary solves |
|---|---:|---:|---:|---:|---:|
| Normal Qwen clean | 18 | 0 (0%) | 0 (0%) | 18 | 0 |
| ThinkingCap baseline | 35 | 9 (25.7%) | 13 (37.1%) | 22 | 1 |
| ThinkingCap temp=.6 | 36 | 17 (47.2%) | 19 (52.8%) | 17 | 1 |

A representative ThinkingCap first-turn stop has one turn, zero tools, zero patch bytes, and a skipped verifier (`results/ThinkingCap-Qwen3.6-27B/high/baseline-thinkingcap-qwen36/adaptix-name-mapping-aliases/rep1/result.json:71-90`); the temp=.6 counterpart has the same shape (`results/ThinkingCap-Qwen3.6-27B/high/baseline-thinkingcap-qwen36-temp06/adaptix-name-mapping-aliases/rep1/result.json:71-90`). Some other ThinkingCap empty cells performed orientation first, so “empty” and “never entered tools” are deliberately reported separately.

The lower temperature did not remove early non-action in this snapshot; its no-tool and empty counts were higher. This is descriptive only: the two ThinkingCap roots are not evidence about normal Qwen's causal response to temperature.

## Support hypotheses that survive the controls

1. **High confidence — provide a requirement-to-verifier coverage scaffold, not generic orchestration.** Ask the executor to turn each requested behavior into a checklist and map each item to implementation plus a focused test before declaring completion. Evidence: active tool use, many tests, near-perfect P2P, but no clean solves and persistent F2P gaps. Recursive delegation is the strongest controlled example because the exact F2P=0/P2P=1 outcome survives the prompt/config change and all three clean reps.
2. **High confidence — add an adversarial contract review near the end.** Review for omitted branches, error paths, limits, and cross-module integration rather than merely rerunning the broad suite. The normal model already averaged 9.9 explicit test-runner calls across all 18 clean cells and touched test files frequently; additional generic test exhortation is unlikely to target the missing clauses.
3. **Medium confidence — use bounded milestone checks on long, multi-clause work.** Require a compact scope/coverage checkpoint before large edits and a time-aware final verification checkpoint. This is supported by two clean `langchain` timeouts and high variation on `participle`/`superjson`, but the historical and clean configurations fail differently, so the data do not identify a single causal mechanism.
4. **Medium confidence — encourage narrower patches when each added surface has an explicit contract purpose.** Clean paired patches added about 54% more lines (1,266 versus 821/cell) and used more edits/tests without producing solves. This supports checking whether each new module/API/test is necessary; it does **not** establish that patch size itself caused failure.
5. **Rejected for normal Qwen — tool-loop bootstrap reminders.** They target ThinkingCap's 1-turn/no-tool failure mode, which is absent in 18/18 completed normal-Qwen cells and absent in all six strict historical pairs.
6. **Rejected as unsupported — restore or remove the historical preamble to fix efficacy.** The matched evidence is mixed (2 wins, 2 losses, 2 ties), no side solved a pair, and prompt is confounded with sampling and output cap.
7. **Rejected as unsupported — simply lower temperature.** The only temperature contrast supplied is on ThinkingCap, where observed early non-action was more frequent at temp=.6. It is a different model lineage and cannot establish a normal-Qwen policy.

## Residual risks

- This is a snapshot of 18 completed clean cells, not a completed 12-task × 3-rep set. A clean `go-critic` directory existed without a result; later results can change aggregate rates.
- Strict same-model inference is only six pairs because historical data has one rep per task.
- The historical config differs in prompt, sampling specification, output cap, and run date. No causal prompt coefficient is identifiable.
- Test-runner counts are command-pattern counts. Verifier fields, patch presence, tool names, turns, and patch diff stats are direct artifact observations.
- Existing unstaged/untracked repository work predated this review. `git diff --cached --name-only` returned empty; this review staged nothing.

## Validation

- Enumerated result keys in all four roots and intersected `(task, rep)` keys.
- Parsed all completed `result.json`, `session/*.jsonl`, and `artifacts/model.patch` artifacts used above.
- Recomputed strict paired and all-clean aggregates in Python.
- Checked config prompt, model-cap, and sampling files directly.
- Checked staged state with `git diff --cached --name-only`: no staged files.
- No benchmark or project test suite was run; this was a read-only artifact analysis.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete severity-tagged findings cite config and result paths/lines; six strict same-model pairs and 18 completed clean cells were parsed from result.json, session JSONL, verifier fields, and model.patch artifacts."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/ed8ad123/analysis/qwen36-27b-support-deep-dive/review_controls.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "find/ls over the four requested result roots",
      "result": "passed",
      "summary": "Found 18 clean normal-Qwen results, 113 historical results, 35 ThinkingCap baseline results, and 36 ThinkingCap temp=.6 results at the snapshot."
    },
    {
      "command": "Python parser over result.json, session/*.jsonl, and artifacts/model.patch",
      "result": "passed",
      "summary": "Computed the six-key strict overlap, tool/read/edit/write/test counts, patch breadth, early-action rates, and verifier aggregates."
    },
    {
      "command": "grep/read config and representative result fields",
      "result": "passed",
      "summary": "Verified prompt surfaces, explicit clean sampling, output-token caps, and cited verifier/tool fields."
    },
    {
      "command": "git diff --cached --name-only",
      "result": "passed",
      "summary": "Returned no staged paths."
    }
  ],
  "validationOutput": [
    "Strict overlap: 6 completed task/rep pairs, all rep0.",
    "Clean strict pairs: 6/6 tool entry, 6/6 patches, 0 solves, 5 scored plus 1 timeout.",
    "Historical strict pairs: 6/6 tool entry, 5/6 patches, 0 solves, 5 scored plus 1 skipped-empty.",
    "ThinkingCap baseline: 9/35 zero-tool and 13/35 empty; temp=.6: 17/36 zero-tool and 19/36 empty; normal clean: 0/18 for both.",
    "No project tests were run or modified; analysis validation only."
  ],
  "residualRisks": [
    "Clean root was incomplete at 18 results; later cells can change aggregate rates.",
    "Only six strict same-model pairs are available.",
    "Prompt/config causality is confounded by sampling, max output tokens, run date, and stochasticity.",
    "Explicit test-runner invocation counts use a documented command regex."
  ],
  "noStagedFiles": true,
  "diffSummary": "No source/config/result files were edited; only the required review artifact was written.",
  "reviewFindings": [
    "no blockers",
    "high: normal Qwen's controlled weakness is contract completion after active implementation, not tool-loop entry",
    "high: requirement-to-test coverage and adversarial final review survive the controls as support hypotheses",
    "medium: long-task milestone checks and purpose-bounded patching are supported but not causally proven",
    "note: ThinkingCap early non-action must not be generalized to normal Qwen"
  ],
  "manualNotes": "The repository already contained unstaged and untracked work before this read-only review; none was staged or modified by the analysis."
}
```
